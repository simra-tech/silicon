#!/usr/bin/env python3
"""Explicit PCell bootstrap and exact stretch control for the 1414-um die."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys
import pya
from place_closed_analog import region, text_records, sha, DESIGN

PDK = Path('/foss/pdks/ihp-sg13g2')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0)) == 1 and pya.__version__ == '0.30.9'
    assert (PDK/'COMMIT').read_text().strip() == '84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    a.output.mkdir(parents=True); (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    for path in (PDK/'libs.tech/klayout/python', PDK/'libs.tech/klayout/python/pycell4klayout-api/source/python'):
        sys.path.insert(0, str(path))
    import sg13g2_pycell_lib  # noqa: F401
    driver = DESIGN/'blocks/g1_padring/flow/sealring_g1.py'
    spec = importlib.util.spec_from_file_location('frozen_sealring_driver', driver)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    (a.output/'driver_snapshot.py').write_bytes(driver.read_bytes())
    library = pya.Library.library_by_name('SG13_dev', 'sg13g2')
    assert library is not None
    decl = library.layout().pcell_declaration('sealring')
    control = pya.Layout(); control.dbu = .001
    small = module.pcell_ring(control, library, decl, 900, 900)
    reference = module.pcell_ring(control, library, decl, 1000, 1000)
    module.stretch_cell(small, 100000, 100000, 475000, 475000)
    checks = []
    for info in control.layer_infos():
        expected = region(control, reference, info)
        actual = region(control, small, info)
        assert (expected^actual).is_empty(), str(info)
        checks.append(dict(layer=str(info), xor_area_dbu2=0, reference_area_dbu2=expected.area()))
    actual_texts = text_records(control, small)
    expected_texts = text_records(control, reference)
    (a.output/'control_diagnostic.json').write_text(json.dumps(dict(
        layers=checks, actual_texts=actual_texts, expected_texts=expected_texts), indent=2)+'\n')
    control.write(str(a.output/'stretch_control.gds'))
    assert actual_texts == expected_texts
    output = a.output/'sealring.gds'
    module.generate(1414, 1414, None, str(output))
    saved = pya.Layout(); saved.read(str(output)); top = saved.top_cell()
    assert top.bbox() == pya.Box(0, 0, 1414000, 1414000)
    extent = pya.Region(pya.Box(0, 0, 1414000, 1414000))
    layers = []
    for info in saved.layer_infos():
        r = region(saved, top, info)
        assert (r-extent).is_empty(), str(info)
        if not r.is_empty(): layers.append(dict(layer=str(info), area_um2=r.area()*1e-6))
    assert 1414*1414*1e-6 <= 2
    result = dict(status='passed native PCell stretch control and isolated sealring generation',
                  GDS_sha256=sha(output), driver_sha256=sha(driver), script_sha256=sha(Path(__file__)),
                  KLayout=pya.__version__, PDK_commit=(PDK/'COMMIT').read_text().strip(),
                  die_side_um=1414, die_area_mm2=1414*1414*1e-6,
                  native_900_to_1000_stretch_exact_polygon_text_control='passed', control_layers=checks,
                  layers=layers, no_shape_outside_die='passed',
                  not_run=['combined chip sealring placement/clearance', 'stock Seal rules and full DRC',
                           'density/fill/antenna', 'electrical adoption'],
                  not_applicable=['electrical qualification from isolated sealring generation'])
    (a.output/'analysis.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
