#!/usr/bin/env python3
"""Reproduce original BGR drawing in isolation; explicitly classify fill deltas."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import pya

HERE = Path(__file__).resolve().parent
LAYOUT = HERE.parent
ROOT = HERE.parents[5]
sys.path.insert(0, str(LAYOUT.parents[1] / 'g1_top/sim'))
from run_bounded import run_bounded

EXPECTED = {'g1_bgr_layout.py': 'dee7f8fa5ab94165946e342625ed72c00e6a174592bb47a0af9f9054b8ce171e',
            'g1_bgr.gds': '4f83cc0830a97b61fda66113cc3768db54e762fc210b2f798d3dd035db30afeb',
            'g1_bgr.lef': 'e00ab99d81bce2c02388a1e933af5e819dd0188f2045f13f943209d059907246'}


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def region(layout, cell, layer):
    index = layout.find_layer(*layer)
    return pya.Region(cell.begin_shapes_rec(index)) if index is not None else pya.Region()


def texts(layout, cell, layer):
    index = layout.find_layer(*layer)
    result = []
    if index is None:
        return result
    it = cell.begin_shapes_rec(index)
    while not it.at_end():
        shape = it.shape()
        if shape.is_text():
            t = shape.text
            result.append((t.string, str(it.itrans()*t.trans)))
        it.next()
    return sorted(result)


def main():
    assert pya.__version__ == '0.30.9'
    assert Path('/foss/pdks/ihp-sg13g2/COMMIT').read_text().strip() == '84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    assert all(sha(LAYOUT/n) == v for n, v in EXPECTED.items())
    out = ROOT / 'build/scratch/bgr-original-generator-20260922-r1'
    out.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(LAYOUT / 'g1_bgr_layout.py', out / 'g1_bgr_layout.py')
    shutil.copyfile(__file__, out / Path(__file__).name)
    with (out / 'generator.log').open('x') as log:
        state = run_bounded(['python3', 'g1_bgr_layout.py'], log, out / 'generator_run.json', 180, cwd=out, interval_s=1)
    result = dict(status='failed', runtime_state=state, inputs=EXPECTED,
                  runner_sha256=sha(Path(__file__)), klayout=pya.__version__, layers=[],
                  source_device_fidelity='not run', stock_DRC_LVS='not run', candidate_geometry='not run')
    try:
        assert state['status'] == 'completed' and state['returncode'] == 0
        a, b = pya.Layout(), pya.Layout()
        a.read(str(out / 'g1_bgr.gds'))
        b.read(str(LAYOUT / 'g1_bgr.gds'))
        assert a.dbu == b.dbu == .001 and len(a.top_cells()) == len(b.top_cells()) == 1
        ac, bc = a.top_cell(), b.top_cell()
        assert ac.name == bc.name == 'g1_bgr'
        layers = sorted({(li.layer, li.datatype) for layout in [a, b] for li in layout.layer_infos()})
        for layer in layers:
            ar, br = region(a, ac, layer), region(b, bc, layer)
            delta = ar ^ br
            if layer[1] == 22:
                category = 'delivered fill addition'
                passed = ar.is_empty()
            elif layer in [(50, 23), (67, 23)]:
                category = 'declared postfill no-fill layer removal'
                passed = br.is_empty()
            else:
                category = 'required exact reproduction'
                passed = delta.is_empty()
            same_text = texts(a, ac, layer) == texts(b, bc, layer)
            result['layers'].append(dict(layer=list(layer), category=category,
                generated_area_um2=ar.area()*a.dbu*a.dbu, delivered_area_um2=br.area()*b.dbu*b.dbu,
                xor_area_um2=delta.area()*a.dbu*a.dbu, geometry_check=bool(passed), text_exact=same_text))
        result.update(generated_gds_sha256=sha(out / 'g1_bgr.gds'),
                      generated_lef_sha256=sha(out / 'g1_bgr.lef'),
                      lef_exact=sha(out / 'g1_bgr.lef') == EXPECTED['g1_bgr.lef'],
                      original_inputs_unchanged=all(sha(LAYOUT/n) == v for n, v in EXPECTED.items()))
        assert result['lef_exact'] and result['original_inputs_unchanged']
        assert all(r['geometry_check'] and r['text_exact'] for r in result['layers'])
        result['status'] = 'passed scoped original-generator reproduction'
    except (AssertionError, OSError, ValueError, RuntimeError) as exc:
        result['analysis_error'] = repr(exc)
    (out / 'comparison.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['status'].startswith('passed') else 1)


if __name__ == '__main__':
    main()
