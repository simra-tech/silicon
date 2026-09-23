#!/usr/bin/env python3
"""Extract one exact moved pad plus retained frame for bounded stock screening."""
import argparse
import json
import os
from pathlib import Path
import sys
import pya
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from place_closed_analog import region, sha


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0)) == 1
    metadata = json.loads((a.candidate / 'analysis.json').read_text())
    source = a.candidate / 'pad_outward_native.gds'
    assert sha(source) == metadata['GDS_sha256'] and metadata['status'].startswith('passed')
    ly = pya.Layout(); ly.read(str(source)); top = ly.top_cell()
    move, = [m for m in metadata['pad_moves'] if m['instance'] == 'IO_BOND_pad01_vdd']
    pad, = [i for i in top.each_inst() if i.cell.name == 'retained_fullchip_bondpad_70x70_tm1'
            and [i.bbox().left, i.bbox().bottom, i.bbox().right, i.bbox().top] == move['new_bbox_dbu']]
    overlay = ly.cell('bondpad_outward_5um_retained_metal')
    oldbox = pya.Box(*move['old_bbox_dbu'])
    unit = pya.Layout(); unit.dbu = ly.dbu; cell = unit.create_cell('pad_bridge_unit')
    translate = pya.Trans(-oldbox.left, -oldbox.bottom + 5000)
    inventories = {}
    for layer in (9, 41, 126, 133, 134):
        r = region(ly, pad.cell, pya.LayerInfo(layer, 0)).transformed(pad.cplx_trans)
        if layer in (126, 134):
            r |= region(ly, overlay, pya.LayerInfo(layer, 0)) & pya.Region(oldbox)
        cell.shapes(unit.layer(layer, 0)).insert(r.transformed(translate))
        inventories[str(layer)] = dict(area_um2=r.area() * 1e-6, polygons=r.count())
    a.output.mkdir(parents=True); target = a.output / 'pad_unit.gds'; unit.write(str(target))
    result = dict(status='passed exact isolated pad and retained-frame extraction',
                  GDS_sha256=sha(target), parent_GDS_sha256=sha(source),
                  script_sha256=sha(Path(__file__)), layers=inventories,
                  not_run=['full-chip/context DRC', 'connectivity', 'electrical qualification'])
    (a.output / 'analysis.json').write_text(json.dumps(result, indent=2) + '\n')
    (a.output / 'source.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
