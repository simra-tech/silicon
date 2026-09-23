#!/usr/bin/env python3
"""Finite additive common-DVBE via proposal; read-only native clearance screen."""
import argparse
import json
import os
from pathlib import Path
import sys
import time
import pya

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'coordinated_full_closure'))
from build_assembly import PAIRS, CUTS, region, sha, dump


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', type=Path, required=True)
    a = ap.parse_args()
    assert not a.output.exists() and set(os.sched_getaffinity(0)) == {2}
    bulk = Path(os.environ['G1_RESULTS_ROOT'])
    gds = bulk / 'bgr-supply-candidate-20260923-r1/bank.gds'
    route = bulk / 'bgr-assembly-20260922-r5/routing.json'
    assert sha(gds) == 'e3ecfc6208fcae71c6b2f4223b7db3900677acfe30987b50ba6365c720297feb'
    inputs = {str(p): sha(p) for p in (gds, route, Path(__file__).resolve(),
                                      HERE.parent / 'coordinated_full_closure/build_assembly.py')}
    a.output.mkdir(parents=True)
    (a.output / 'source.py').write_bytes(Path(__file__).read_bytes())
    # Read-only exact installed model evidence for the separate BN applicability audit.
    pdk = Path('/foss/pdks/ihp-sg13g2')
    assert (pdk / 'COMMIT').read_text().strip() == '84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    models = {}
    for rel in ('libs.tech/verilog-a/r3_cmc/r3_cmc-patched.va',
                'libs.tech/verilog-a/r3_cmc/r3_cmc_macros.include',
                'libs.tech/ngspice/models/resistors_mod.lib'):
        path = pdk / rel
        inputs[str(path)] = sha(path)
        models[rel] = dict(sha256=sha(path), lines=path.read_text().splitlines())
    dump(a.output / 'pinned_models.json', models)
    start = time.monotonic()
    ly = pya.Layout()
    ly.read(str(gds))
    top = ly.top_cell()
    ltn = pya.LayoutToNetlist(pya.RecursiveShapeIterator(ly, top, []))
    layers = {k: ltn.make_layer(ly.layer(*v), k) for k, v in PAIRS.items()}
    for k in layers:
        ltn.connect(layers[k])
    for cut, ends in CUTS.items():
        for end in ends:
            ltn.connect(layers[cut], layers[end])
    ltn.extract_netlist()
    nets = {}
    for p in json.loads(route.read_text())['source_probes']:
        n = ltn.probe_net(layers[p['layer']], pya.Point(*p['point']))
        assert n
        if p['net'] in nets:
            assert nets[p['net']].cluster_id == n.cluster_id
        nets[p['net']] = n
    assert len(nets) == 55
    ledger = []

    def add(layer, box, role):
        assert all(v % 5 == 0 for v in box)
        assert 0 <= box[0] < box[2] <= 420000 and 0 <= box[1] < box[3] <= 354000
        ledger.append(dict(net='dvbe', layer=layer, bbox_dbu=box, role=role))

    # Upper alternative landing is above the crowded original y137.2 M3 row.
    add('M2', [192640, 140220, 193360, 141780], 'upper_M2_landing')
    add('M3', [192640, 140220, 203360, 141780], 'upper_common_bridge')
    add('M4', [202640, 140220, 203360, 141780], 'upper_M4_landing')
    add('M5', [202640, 136900, 203360, 141780], 'upper_M5_extension')
    for cut, xc in (('Via2', 193000), ('Via3', 203000), ('Via4', 203000)):
        for dx in (-210, 210):
            for dy in (-630, -210, 210, 630):
                add(cut, [xc+dx-95, 141000+dy-95, xc+dx+95, 141000+dy+95], 'upper_eight_cut')
    # Retain the lower two cuts at x203; add two columns around them.
    for layer in ('M3', 'M4', 'M5'):
        add(layer, [202430, 18100, 203570, 18820], 'lower_six_cut_landing')
    for cut in ('Via3', 'Via4'):
        for xc in (202580, 203000, 203420):
            for yc in (18250, 18670):
                add(cut, [xc-95, yc-95, xc+95, yc+95], 'lower_six_cut')
    native = {k: region(top, ly.layer(*v)) for k, v in PAIRS.items()}
    owned = {k: ltn.shapes_of_net(nets['dvbe'], layers[k], True) for k in PAIRS}
    added = {}
    for r in ledger:
        added.setdefault(r['layer'], pya.Region()).insert(pya.Box(*r['bbox_dbu']))

    def boxes(reg):
        return [[p.bbox().left, p.bbox().bottom, p.bbox().right, p.bbox().top] for p in reg.each()]

    checks = []
    for r in ledger:
        layer = r['layer']
        shape = pya.Region(pya.Box(*r['bbox_dbu']))
        spacing = shape.sized(250) & (native[layer]-owned[layer])
        captured, missing, overlap, too_close = {}, {}, [], []
        if layer in CUTS:
            for end in CUTS[layer]:
                missing[end] = boxes(shape.sized(55)-(owned[end]+added.get(end, pya.Region())))
                captured[end] = boxes(shape & (native[end]-owned[end]))
            for polygon in (native[layer]+added[layer]).merged().interacting(shape.sized(220)).each():
                old = pya.Region(polygon)
                if not (old ^ shape).is_empty():
                    overlap += boxes(old & shape)
                    too_close += boxes(old & shape.sized(219))
        else:
            for cut, ends in CUTS.items():
                if layer in ends:
                    captured[cut] = boxes(shape & (native[cut]-owned[cut]))
        checks.append(dict(r, passed=spacing.is_empty() and not any(captured.values())
            and not any(missing.values()) and not overlap and not too_close,
            foreign_spacing=boxes(spacing), foreign_capture=captured,
            missing_enclosure=missing, partial_cut_overlap=overlap, cut_spacing=too_close))
    assert all(sha(Path(p)) == h for p, h in inputs.items())
    result = dict(status='passed geometric screen' if all(c['passed'] for c in checks) else 'failed geometric screen',
        inputs=inputs, ledger=ledger, checks=checks, wall_s=time.monotonic()-start,
        physical_native_changed=False, source_nets=55, candidate_generation='not run',
        full_parent_context='not run', stock_DRC_LVS='not run', new_nonlinear_OP='not run',
        model_plane_changes='not applicable')
    dump(a.output / 'analysis.json', result)
    print(json.dumps(dict(status=result['status'], failed=[r for r in checks if not r['passed']]), indent=2))


if __name__ == '__main__':
    main()
