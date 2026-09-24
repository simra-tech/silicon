#!/usr/bin/env python3
"""Read-only exact hierarchy inventory of ten supply-route fill conflicts."""
import argparse
import json
import os
from pathlib import Path
import time
import pya
from check_full_context_flat import ROOT,sha,dump

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args();assert not a.output.exists() and set(os.sched_getaffinity(0))=={0}
    parent=ROOT/'designs/g1-guardian/review/audits/fullchip_reference_closure/physical_lvs/full_marker_candidate/evidence-20260923-r1/candidate/io_marker_native.gds'
    assert sha(parent)=='ae62bf68aa001144c08a37c58ac3553c6e5f2013a6824b340218e84962066aca'
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    start=time.monotonic();ly=pya.Layout();ly.read(str(parent));top=ly.top_cell()
    target=pya.Box(617000,903660,619000,957780);rows=[]
    def walk(cell,tr,path):
        for inst in cell.each_inst():
            if not inst.bbox().transformed(tr).overlaps(target):continue
            for trans in inst.cell_inst.each_cplx_trans():
                total=tr*trans
                if not inst.cell.bbox().transformed(total).overlaps(target):continue
                child=inst.cell
                if '_FILL_CELL' in child.name:
                    for shape in child.shapes(ly.layer(67,22)).each():
                        poly=shape.polygon.transformed(total)
                        if (pya.Region(poly)&pya.Region(target)).is_empty():continue
                        shapes=[(str(ly.get_info(i)),str(s)) for i in ly.layer_indices() for s in child.shapes(i).each()]
                        assert len(shapes)==1 and not list(child.each_inst()) and inst.prop_id==0
                        rows.append(dict(parent_path=path,parent_cell=cell.name,child_cell=child.name,
                            parent_transform=str(tr),array_transform=str(inst.cplx_trans),
                            na=inst.na,nb=inst.nb,a=[inst.a.x,inst.a.y],b=[inst.b.x,inst.b.y],
                            repetition_transform=str(trans),global_transform=str(total),
                            layer=67,datatype=22,global_bbox=str(poly.bbox()),
                            global_hull=[[p.x,p.y] for p in poly.each_point_hull()],
                            area_dbu2=poly.area(),child_shape=shapes))
                else:walk(child,total,path+[child.name])
    walk(top,pya.ICplxTrans(),[top.name]);assert len(rows)==10,len(rows)
    expected=[str(pya.Box(618000,y,622000,y+4000)) for y in range(900000,954001,6000)]
    assert sorted(r['global_bbox'] for r in rows)==sorted(expected)
    assert sha(parent)=='ae62bf68aa001144c08a37c58ac3553c6e5f2013a6824b340218e84962066aca'
    result=dict(status='passed exact ten generated-fill identity inventory',parent_sha256=sha(parent),
                rows=rows,total_removed_area_um2=sum(r['area_dbu2'] for r in rows)*1e-6,
                mutation='not run',wall_s=time.monotonic()-start)
    dump(a.output/'analysis.json',result);print(json.dumps(result,indent=2))

if __name__=='__main__':main()
