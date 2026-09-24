#!/usr/bin/env python3
"""Read-only marker and foreign-shape provenance after digital replacement."""
import argparse
import collections
import json
import os
from pathlib import Path
import re
import time
import xml.etree.ElementTree as ET
import pya
from place_closed_analog import region,sha


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('candidate','drc','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();assert not a.output.exists() and len(os.sched_getaffinity(0))==1
    meta=json.loads((a.candidate/'analysis.json').read_text())
    gds=a.candidate/'digital_replaced_native.gds';assert sha(gds)==meta['GDS_sha256']
    drc=json.loads((a.drc/'summary.json').read_text());assert drc['GDS_sha256']==sha(gds)
    report=a.drc/drc['decks'][0]['reports'][0]['path']
    assert sha(report)==drc['decks'][0]['reports'][0]['sha256']
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    start=time.monotonic();ly=pya.Layout();ly.read(str(gds));top=ly.cell(meta['top_cell'])
    target=ly.cell('retained_g1_digital');inst,=[i for i in top.each_inst() if i.cell_index==target.cell_index()]
    box=inst.bbox();window=pya.Region(box)
    markers=[]
    for item in ET.parse(report).findall('.//items/item'):
        values=[e.text for e in item.findall('./values/value')]
        points=[]
        for value in values:
            assert value.startswith('edge-pair:'),value
            nums=[float(s) for s in re.findall(r'-?\d+(?:\.\d+)?',value)]
            assert len(nums)==8
            points.extend(zip(nums[::2],nums[1::2]))
        bounds=[min(x for x,y in points),min(y for x,y in points),max(x for x,y in points),max(y for x,y in points)]
        b=pya.Box(*[round(v/ly.dbu) for v in bounds])
        markers.append(dict(category=item.findtext('category'),bbox_um=bounds,
                            in_macro_bbox=box.left<=b.left and box.bottom<=b.bottom and box.right>=b.right and box.top>=b.top,values=values))
    rows=[]
    for child in top.each_inst():
        if child.cell_index==target.cell_index() or not child.bbox().overlaps(box):continue
        parts=[]
        for info in ly.layer_infos():
            if info.layer not in (8,10,30,50,67,126,134,19,29,49,66,125,133) or info.datatype not in (0,22):continue
            shapes=region(ly,child.cell,info)
            if shapes.is_empty():continue
            area=pya.Region()
            for tr in child.cell_inst.each_cplx_trans():
                if not (tr*child.cell.bbox()).overlaps(box):continue
                area.insert(shapes.transformed(tr)&window)
            if not area.is_empty():parts.append(dict(layer=[info.layer,info.datatype],area_um2=area.merged().area()*ly.dbu**2,polygons=area.count()))
        if parts:rows.append(dict(cell=child.cell.name,transform=str(child.cplx_trans),na=child.na,nb=child.nb,parts=parts))
    direct=[]
    for info in ly.layer_infos():
        if info.layer in (8,10,30,50,67,126,134,19,29,49,66,125,133) and info.datatype in (0,22):
            r=pya.Region(top.shapes(ly.layer(info)))&window
            if not r.is_empty():direct.append(dict(layer=[info.layer,info.datatype],area_um2=r.area()*ly.dbu**2))
    result=dict(status='passed read-only context inventory; design failures not waived',GDS_sha256=sha(gds),report_sha256=sha(report),
        macro_bbox_dbu=[box.left,box.bottom,box.right,box.top],marker_counts=dict(collections.Counter(r['category'] for r in markers)),
        markers_outside_macro=sum(not r['in_macro_bbox'] for r in markers),markers=markers,
        other_root_instances_intersecting_macro=rows,direct_root_shapes_in_macro=direct,wall_s=time.monotonic()-start,
        not_run=['Fill removal','Foreign functional-route replacement','Connectivity remedy','Fresh DRC after remedy'])
    (a.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='markers'},indent=2))


if __name__=='__main__':main()
