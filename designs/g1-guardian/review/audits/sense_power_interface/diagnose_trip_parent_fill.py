#!/usr/bin/env python3
"""Read-only three-way TRIP native geometry and fill-array provenance audit."""
import argparse
import json
import os
from pathlib import Path
import pya
from build_ls_interface import region,text_records,sha


def records(r):
    return [dict(hull_dbu=[[p.x,p.y]for p in q.each_point_hull()],
                 bbox_dbu=[q.bbox().left,q.bbox().bottom,q.bbox().right,q.bbox().top],area_dbu2=q.area())for q in r.each()]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in('standalone','baseline','parent','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();assert not a.output.exists()and len(os.sched_getaffinity(0))==1 and pya.__version__=='0.30.9'
    inputs=[('standalone',a.standalone,'g1_trip','c99f3ae11b4501610939aa09b4581535a42d257f76951a25b4c84dd72a3afb90'),
            ('baseline',a.baseline,'g1_trip','38c1d6d13bbfee4ed0e3c01477742c3d2d28317d9215d9e5bd9a35551285ae59'),
            ('parent',a.parent,'retained_g1_trip','9940011f4061ec17815ff65f86c2448ad07145cf6a1d87645f4ab80bbb815669')]
    shapes={};texts={};sources=[]
    for name,path,cellname,digest in inputs:
        assert sha(path)==digest
        ly=pya.Layout();ly.read(str(path));cell=ly.cell(cellname);assert cell is not None and ly.dbu==.001
        shapes[name]={(i.layer,i.datatype):region(ly,cell,i)for i in ly.layer_infos()}
        texts[name]=text_records(ly,cell)
        arrays=[]
        for inst in cell.each_inst():
            if '_FILL_CELL'in inst.cell.name:
                child=inst.cell
                payload=[dict(layer=[i.layer,i.datatype],polygons=records(region(ly,child,i)))for i in ly.layer_infos()
                         if not child.shapes(ly.layer(i)).is_empty()]
                arrays.append(dict(child=child.name,transform=str(inst.cplx_trans),na=inst.na,nb=inst.nb,
                                   a=[inst.a.x,inst.a.y],b=[inst.b.x,inst.b.y],child_geometry=payload))
        sources.append(dict(name=name,GDS_sha256=digest,cell=cellname,direct_fill_arrays=arrays,
                            direct_nonfill_instances=[dict(child=i.cell.name,transform=str(i.cplx_trans),na=i.na,nb=i.nb,a=str(i.a),b=str(i.b))
                                for i in cell.each_inst()if '_FILL_CELL'not in i.cell.name]))
    pairs=[]
    for left,right in[('standalone','baseline'),('baseline','parent'),('standalone','parent')]:
        differences=[]
        for key in sorted(set(shapes[left])|set(shapes[right])):
            old=shapes[left].get(key,pya.Region());new=shapes[right].get(key,pya.Region())
            removed=old-new;added=new-old
            if not removed.is_empty()or not added.is_empty():
                differences.append(dict(layer=list(key),left_area_um2=old.area()*1e-6,right_area_um2=new.area()*1e-6,
                    removed_area_um2=removed.area()*1e-6,added_area_um2=added.area()*1e-6,
                    removed=records(removed),added=records(added)))
        pairs.append(dict(left=left,right=right,differences=differences,texts_exact=texts[left]==texts[right]))
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    result=dict(status='completed exact read-only three-way native audit; differences not waived',sources=sources,pairs=pairs,
                script_sha256=sha(Path(__file__)),not_run=['replacement ledger','new actual-parent stock/LVS','pruning or integration'])
    (a.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(pairs=[dict(left=r['left'],right=r['right'],texts_exact=r['texts_exact'],
        differences=[{k:v for k,v in d.items()if k not in('removed','added')}for d in r['differences']])for r in pairs]),indent=2))


if __name__=='__main__':main()
