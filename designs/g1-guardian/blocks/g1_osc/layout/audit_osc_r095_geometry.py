#!/usr/bin/env python3
"""Check actual candidate resistor bodies and unchanged boundary/pin geometry.

Pinned KLayout: -r audit_osc_r095_geometry.py -rd baseline=<gds>
  -rd candidate=<gds> -rd report=<new-json>
This is not DRC, LVS, extraction, or approval to replace the full-chip macro.
"""
import hashlib
import json
from pathlib import Path

import pya


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    layout = pya.Layout()
    layout.read(str(path))
    assert layout.dbu == 0.001
    cell = layout.cell('g1_osc')
    assert cell is not None
    return layout, cell


def region(layout, cell, layer, datatype):
    index = layout.find_layer(layer, datatype)
    assert index is not None and layout.is_valid_layer(index), (layer, datatype)
    result = pya.Region(cell.begin_shapes_rec(index)).merged()
    assert not result.is_empty(), ('missing expected geometry', layer, datatype)
    return result


def audit(baseline, candidate, report):
    report = Path(report)
    assert not report.exists()
    old, a = read(baseline)
    new, b = read(candidate)
    checks = {}
    # All dimensions are integer nanometres; four bodies have width1000nm.
    old_bodies = pya.Region()
    new_bodies = pya.Region()
    for index in range(1, 5):
        x = 4500 + 1850 * index
        old_bodies.insert(pya.Box(x, 10000, x+1000, 68500))
        new_bodies.insert(pya.Box(x, 10000, x+1000, 65575))
    old_poly = region(old, a, 128, 0)
    new_poly = region(new, b, 128, 0)
    checks['baseline_four_bodies_present'] = (old_bodies-old_poly).is_empty()
    checks['candidate_four_bodies_present'] = (new_bodies-new_poly).is_empty()
    checks['only_expected_polyres_difference'] = (
        (old_poly ^ new_poly) ^ (old_bodies ^ new_bodies)).is_empty()
    for layer, datatype in [(189, 4), (30, 2)]:
        checks[f'unchanged_layer_{layer}_{datatype}'] = (
            region(old, a, layer, datatype) ^ region(new, b, layer, datatype)).is_empty()
    result = dict(status='passed scoped geometry' if all(checks.values()) else 'failed',
                  baseline_sha256=sha(baseline), candidate_sha256=sha(candidate),
                  auditor_sha256=sha(__file__), checks=checks,
                  scope='PolyRes body difference and external boundary/pin polygons only',
                  connectivity='not run', stock_drc='not run', stock_lvs='not run',
                  new_pex='not run', production_adoption='not run')
    report.write_text(json.dumps(result, indent=2)+'\n')
    if not all(checks.values()):
        raise RuntimeError('Candidate geometry checks failed')


if __name__ == '__main__':
    audit(globals()['baseline'], globals()['candidate'], globals()['report'])
