#!/usr/bin/env python3
"""Check the public opening map against actual serialized pad instances."""
import argparse
import csv
import json
import os
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
import pya
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from place_closed_analog import region, sha


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('candidate', 'map', 'output'):
        p.add_argument('--' + key, type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0)) == 1
    source = a.candidate / 'pad_outward_native.gds'
    expected = 'ab02b653c6b0e29e7693bed55e097081e6e41f67e24c59102494e6fbc1724541'
    assert sha(source) == expected
    meta = json.loads((a.candidate / 'analysis.json').read_text())
    rows = list(csv.DictReader(a.map.open())); assert len(rows) == 24
    assert [int(r['pad_number']) for r in rows] == list(range(1, 25))
    assert len({r['logical_pin'] for r in rows}) == 22
    ly = pya.Layout(); ly.read(str(source)); top = ly.top_cell()
    pads = {tuple([i.bbox().left, i.bbox().bottom, i.bbox().right, i.bbox().top]): i
            for i in top.each_inst() if i.cell.name == 'retained_fullchip_bondpad_70x70_tm1'}
    details = []
    for m, row in zip(meta['pad_moves'], rows):
        assert int(re.search(r'pad(\d+)_', m['instance'])[1]) == int(row['pad_number'])
        assert row['logical_pin'] == m['logical_net'] and row['candidate_gds_sha256'] == expected
        assert row['status'] == 'candidate_not_tapeout'
        assert row['die_width_um'] == row['die_height_um'] == '1414'
        dx, dy = m['shift_dbu']; side = 'west' if dx < 0 else 'east' if dx > 0 else 'south' if dy < 0 else 'north'
        assert row['side'] == side
        inst = pads[tuple(m['new_bbox_dbu'])]
        opening = region(ly, inst.cell, pya.LayerInfo(9, 0)).transformed(inst.cplx_trans)
        assert opening.count() == 1 and opening.area() == opening.bbox().area()
        box = opening.bbox(); centre = box.center()
        assert [float(row['opening_center_x_um']), float(row['opening_center_y_um'])] == [centre.x / 1000, centre.y / 1000] == m['new_opening_center_um']
        assert float(row['opening_width_um']) == box.width() / 1000 == 65.8
        assert float(row['opening_height_um']) == box.height() / 1000 == 65.8
        details.append(dict(pad=int(row['pad_number']), logical_pin=row['logical_pin'],
                            opening_bbox_dbu=[box.left, box.bottom, box.right, box.top]))
    bulk = a.candidate.parent; checks = []
    for folder in ('bondpad-outward-main-20260923-r1', 'bondpad-outward-maximal-20260923-r2',
                   'bondpad-outward-antenna-20260923-r1', 'bondpad-outward-density-20260923-r1'):
        base = bulk / folder; summary = json.loads((base / 'summary.json').read_text())
        assert summary['status'].startswith('passed') and summary['GDS_sha256'] == expected
        assert summary['inputs_rules_unchanged']
        if 'decks' in summary:
            reports = [base / r['path'] for d in summary['decks'] for r in d['reports']]
        else:
            reports = [base / (summary['check'] + '.lyrdb')]
        assert len(reports) == 1 and len(ET.parse(reports[0]).findall('.//items/item')) == 0
        checks.append(dict(folder=folder, summary_sha256=sha(base / 'summary.json'), report_sha256=sha(reports[0]), markers=0))
    result = dict(status='passed all24 public physical opening centres and four actual zero-marker stock reports',
                  GDS_sha256=expected, map_sha256=sha(a.map), script_sha256=sha(Path(__file__)),
                  physical_pads=24, logical_pins=22, openings=details, stock=checks,
                  not_run=['bonding/package measurements', 'device-aware fullchip LVS acceptance', 'shifted-pad RC'],
                  not_applicable=['pin reassignment', 'die/circuit changes'])
    a.output.parent.mkdir(parents=True, exist_ok=True); a.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
