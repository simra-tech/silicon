#!/usr/bin/env python3
"""Populate diagnostic r4 core with unchanged macros and all4662 native decaps."""
import argparse
import collections
import hashlib
import json
import os
from pathlib import Path
import pya
from place_closed_analog import region, text_records

HERE = Path(__file__).resolve().parent
DESIGN = HERE.parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bbox_um(box, dbu):
    return [v*dbu for v in (box.left, box.bottom, box.right, box.top)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--analog-placement', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists() and len(os.sched_getaffinity(0)) == 1 and pya.__version__ == '0.30.9'
    parent_analysis = json.loads((args.analog_placement/'analysis.json').read_text())
    parent_gds = args.analog_placement/'closed_analog_placement.gds'
    assert parent_analysis['status']=='passed scoped placement' and sha(parent_gds)==parent_analysis['GDS_sha256']
    assert all(len(b['external_ports'])==9 for b in parent_analysis['blocks'])
    baseline = DESIGN/'blocks/g1_padring/layout/g1_chip_top.gds'
    assert sha(baseline)=='38c1d6d13bbfee4ed0e3c01477742c3d2d28317d9215d9e5bd9a35551285ae59'
    pack_path = HERE/'coordinated-bbox-pack-20260922-r4.json'
    pack = json.loads(pack_path.read_text())
    assert sha(pack_path)==parent_analysis['pack_sha256'] and pack['placed_decap_count']==4662
    targets = {r['name']:r for r in pack['macros']}
    source = pya.Layout()
    source.read(str(baseline))
    oldtop = source.cell('g1_chip_top')
    layout = pya.Layout()
    layout.read(str(parent_gds))
    assert source.dbu==layout.dbu==.001
    dbu = layout.dbu
    top = layout.top_cell()
    top.name = 'placed_core_NOT_CONNECTED_FULLCHIP'
    args.output.mkdir(parents=True)
    copies = {}
    def copy_cell(cell):
        if cell.cell_index() not in copies:
            new = layout.create_cell('retained_'+cell.name)
            new.copy_tree(cell)
            assert text_records(source,cell)==text_records(layout,new)
            for info in source.layer_infos():
                assert (region(source,cell,info)^region(layout,new,info)).is_empty()
            copies[cell.cell_index()] = new
        return copies[cell.cell_index()]
    macros = []
    shifts = {'g1_dut_macro':'g1_dut','g1_dose_macro':'g1_dose'}
    level_shifter_index = 0
    original_decaps = []
    for inst in oldtop.each_inst():
        name = inst.cell.name
        if name.startswith('sg13g2_decap'):
            original_decaps.append(inst)
        if not name.startswith('g1_') or name in ('g1_bgr','g1_sense'):
            continue
        target_name = shifts.get(name,name)
        if name=='g1_ls_up':
            target_name='g1_ls_'+str(level_shifter_index)
            level_shifter_index+=1
        target = targets[target_name]
        x,y,right,upper = target['bbox_um']
        box = inst.bbox()
        rotation = target['orientation']=='R90'
        expected = (box.height()*dbu,box.width()*dbu) if rotation else (box.width()*dbu,box.height()*dbu)
        assert abs(expected[0]-(right-x))<1e-8 and abs(expected[1]-(upper-y))<1e-8
        shift = pya.Trans(pya.Trans.R90 if rotation else pya.Trans.R0,
                          round(x/dbu)+(box.height() if rotation else 0),round(y/dbu))
        transform = shift * pya.Trans(-box.left,-box.bottom) * inst.trans
        copied = copy_cell(inst.cell)
        placed = top.insert(pya.CellInstArray(copied.cell_index(),transform))
        assert all(abs(a-b)<1e-8 for a,b in zip(bbox_um(placed.bbox(),dbu),target['bbox_um']))
        macros.append(dict(name=target_name,source_cell=name,original_transform=str(inst.trans),
                           placed_transform=str(transform),bbox_um=bbox_um(placed.bbox(),dbu)))
    assert len(macros)==10 and level_shifter_index==3
    assert len(original_decaps)==len(pack['decap_placements'])==4662
    decaps=[]
    counts=collections.Counter()
    for i,(inst,row) in enumerate(zip(original_decaps,pack['decap_placements'])):
        assert row['original_inventory_index']==i and inst.cell.name==row['cell']
        assert all(abs(a-b)<1e-8 for a,b in zip(bbox_um(inst.bbox(),dbu),row['original_bbox_um']))
        x,y,right,upper=row['bbox_um']
        assert abs(upper-y-3.78)<1e-8
        mirrored=row['orientation']=='MX'
        assert row['orientation']==('MX' if row['row']%2 else 'R0')
        transform=pya.Trans(pya.Trans.M0 if mirrored else pya.Trans.R0,
                            round(x/dbu),round((upper if mirrored else y)/dbu))
        # LEF origin, not expanded native bbox: abutment intentionally overlaps native well enclosures.
        copied=copy_cell(inst.cell)
        top.insert(pya.CellInstArray(copied.cell_index(),transform))
        pin_points={}
        for shape in inst.cell.shapes(source.layer(8,25)).each():
            if shape.is_text() and shape.text.string in ('VDD','VSS'):
                displacement=shape.text.trans.disp
                local=pya.Point(displacement.x,displacement.y)
                moved=transform*local
                pin_points[shape.text.string]=dict(local_dbu=[local.x,local.y],
                    original_dbu=[(inst.trans*local).x,(inst.trans*local).y],placed_dbu=[moved.x,moved.y])
        assert set(pin_points)=={'VDD','VSS'}
        counts[row['cell']]+=1
        decaps.append(dict(index=i,cell=row['cell'],row=row['row'],site=row['site'],
                           orientation=row['orientation'],transform=str(transform),pins=pin_points,
                           intended_LEF_bbox_um=row['bbox_um']))
    assert counts=={'sg13g2_decap_8':4645,'sg13g2_decap_4':17}
    # Check adjacent row rails share like labels, independent of bbox overlap.
    heights=collections.defaultdict(set)
    for row in decaps:
        for name,pin in row['pins'].items():
            heights[pin['placed_dbu'][1]].add(name)
    assert all(len(names)==1 for names in heights.values())
    output=args.output/'placed_core.gds'
    layout.write(str(output))
    saved=pya.Layout()
    saved.read(str(output))
    assert len(saved.top_cells())==1
    assert text_records(layout,top)==text_records(saved,saved.top_cell())
    for info in layout.layer_infos():
        assert (region(layout,top,info)^region(saved,saved.top_cell(),info)).is_empty()
    result=dict(status='passed source-preserving core placement',GDS_sha256=sha(output),
                baseline_sha256=sha(baseline),parent_GDS_sha256=sha(parent_gds),pack_sha256=sha(pack_path),
                script_sha256=sha(Path(__file__)),KLayout=pya.__version__,macros=macros,decaps=decaps,
                replacement_macros=parent_analysis['blocks'],retained_decap_counts=dict(counts),
                native_geometry_text_copy_and_saved_roundtrip='passed',adjacent_row_rail_polarity='passed',
                not_run=['decap original power-domain reconstruction','physical no-short and stockDRC',
                         'signal/power/row-feed routing','complete ring/vias/pads/sealring',
                         'antenna/density/fill/currentIR','complete LVS/PEX/integrated electrical'],
                not_applicable=['connected fullchip qualification from placement-only GDS'])
    (args.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('macros','decaps','replacement_macros')},indent=2))


if __name__=='__main__':
    main()
