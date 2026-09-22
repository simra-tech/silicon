#!/usr/bin/env python3
"""Read-only native SENSE-to-chip supply corridor screen, not routing acceptance."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import pya

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from place_closed_analog import region, sha


def rect(box):
    return pya.Region(pya.DBox(*box).to_itype(.001))


def boxes(reg):
    return [[v*.001 for v in (b.left, b.bottom, b.right, b.top)]
            for b in (p.bbox() for p in reg.each())]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--native', type=Path, required=True)
    ap.add_argument('--spines', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    a = ap.parse_args()
    assert pya.__version__ == '0.30.9' and len(os.sched_getaffinity(0)) == 1
    assert not a.output.exists()
    meta = json.loads((a.native/'analysis.json').read_text())
    source = a.native/'fullchip_instances_unrouted.gds'
    assert sha(source) == meta['GDS_sha256'] == '8b66a958759478987fa9de59746a0554f9bd065307e730342f10e891082134e6'
    spines = json.loads((a.spines/'analysis.json').read_text())['spines']
    assert any(r['net'] == 'VSS' and r['lane'] == 5 and r['bbox'] == [733800,321000,739800,1093000] for r in spines)
    layout = pya.Layout(); layout.read(str(source)); top = layout.top_cell()
    assert layout.dbu == .001
    actual = {l: region(layout, top, pya.LayerInfo(l, 0)) for l in (30,50,67,126,134)}
    pins = {'VDDA': (134, [811,712,815,716]), 'VSS': (126, [803,712,807,716]),
            'pad07': (30, [1093,381.105,1093.290,405.875])}
    own = {}
    for name, (layer, box) in pins.items():
        assert (rect(box)-actual[layer]).is_empty(), name
        own[name] = actual[layer].interacting(rect(box))
    requested = [
        ('VDDA_pin_escape',134,[811.9,714,814.1,727.1],'VDDA'),
        ('VDDA_north_trunk',134,[813,724.9,1049.1,727.1],None),
        ('VDDA_east_trunk',134,[1046.9,393.9,1049.1,726],None),
        ('VDDA_M3_bridge',30,[1046.9,393.9,1093.145,396.1],'pad07'),
        ('VDDA_M4_stack',50,[1046.7,393.7,1049.3,396.3],None),
        ('VDDA_M5_stack',67,[1046.7,393.7,1049.3,396.3],None),
        ('VDDA_TM1_stack',126,[1046.7,393.7,1049.3,396.3],None),
        ('VSS_pin_escape',126,[803.9,714,806.1,724.1],'VSS'),
        ('VSS_pin_landing',126,[802.9,719.9,807.1,724.1],None),
        ('VSS_TM2_bridge',134,[734.7,719.9,807.1,724.1],None),
        ('VSS_spine_landing',126,[734.7,719.9,738.9,724.1],None),
    ]
    rows = []
    for name, layer, box, allowed in requested:
        route = rect(box)
        excluded = actual[layer] - (own[allowed] if allowed else pya.Region())
        # The overlapping proposed VSS escape and landing share their own pin.
        if name == 'VSS_pin_landing': excluded -= own['VSS']
        spacing = .4 if layer in (30,50,67) else 2 if layer == 126 else 5
        collision = route & excluded
        proximity = route & excluded.sized(round(spacing*1000))
        planned = pya.Region()
        if layer == 126:
            for spine in spines:
                if name.startswith('VSS') and spine['net'] == 'VSS': continue
                planned.insert(pya.Box(*spine['bbox']))
        future = route & planned.sized(round(spacing*1000))
        rows.append(dict(name=name,layer=layer,bbox_um=box,clearance_screen_um=spacing,
                         overlap_um2=collision.area()*1e-6,proximity_um2=proximity.area()*1e-6,
                         proximity_bboxes_um=boxes(proximity),root_spine_proximity_um2=future.area()*1e-6))
    a.output.mkdir(parents=True)
    (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    result = dict(status='completed read-only obstacle screen; feasibility not qualified',
                  source_sha256=sha(source),script_sha256=sha(Path(__file__)),spines_sha256=sha(a.spines/'analysis.json'),
                  candidates=rows,method='Materialized native drawing polygons, explicit pin-owned same-layer exclusions; conservative spacing only, no GDS write.',
                  not_run=['cut geometry','physical no-other-net graph','stock DRC','current sharing/EM','routed-signal overlay','implementation or adoption'])
    (a.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__': main()
