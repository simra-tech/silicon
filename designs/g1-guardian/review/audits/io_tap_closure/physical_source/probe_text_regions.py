#!/usr/bin/env python3
"""Literal native-label parity and independent text-region API controls."""
import argparse
import collections
import hashlib
import json
import os
from pathlib import Path
import pya


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def labels(ly,cell):
    out=[];it=cell.begin_shapes_rec(ly.layer(63,0))
    while not it.at_end():
        s=it.shape()
        if s.is_text():
            t=s.text.transformed(it.trans());out.append([t.string,t.x,t.y])
        it.next()
    return sorted(out)


def selections(ly,cell):
    dss=pya.DeepShapeStore();dss.threads=1
    return [dict(pattern=pattern,glob=glob,flat_area=pya.Region(cell.begin_shapes_rec(ly.layer(63,0)),pattern,glob,1).area(),
        deep_area=pya.Region(cell.begin_shapes_rec(ly.layer(63,0)),dss,pattern,glob,1).area())
        for pattern,glob in [('sub!',False),('SUB!',False),('*',True),('[sS][uU][bB]!',True),('{s,S}{u,U}{b,B}!',True)]]


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0))==1
    bulk=Path(os.environ['G1_RESULTS_ROOT']);actual=bulk/'io-current-native-20260923-r1/current_io_masters.gds'
    original=Path('/foss/pdks/ihp-sg13g2/libs.ref/sg13g2_io/gds/sg13g2_io.gds')
    assert sha(actual)=='e7d4af382fa9b07b4be4c1f8d59c3f668f3605cb68d68926a1c7d789d5e6d8c5'
    assert sha(original)=='4281a855377b6a1ca46356e9391258dc14e8efc3b8051a65befc0fe9db3c7825'
    ly=pya.Layout();ly.read(str(actual));ref=pya.Layout();ref.read(str(original))
    rows=[]
    for cell in ly.top_cells():
        gold=ref.cell(cell.name);assert gold
        before=labels(ref,gold);after=labels(ly,cell)
        rows.append(dict(cell=cell.name,before=before,after=after,exact=before==after,selections=selections(ly,cell)))
    toy=pya.Layout();toy.dbu=.001;t=toy.create_cell('CONTROL');layer=toy.layer(63,0)
    t.shapes(layer).insert(pya.Text('sub!',pya.Trans(100,100)));t.shapes(layer).insert(pya.Text('SUB!',pya.Trans(200,200)))
    controls=selections(toy,t)
    assert controls[0]['flat_area']==controls[1]['flat_area']==4
    assert controls[0]['deep_area']==controls[1]['deep_area']==4
    assert controls[2]['flat_area']==controls[2]['deep_area']==8
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    result=dict(status='passed literal label and API diagnostic',inputs={str(p):sha(p) for p in (actual,original,Path(__file__).resolve())},
        masters=rows,synthetic=controls,all_original_labels_exact=all(r['exact'] for r in rows),
        source_geometry_mutation='not applicable; none',tap_parameters='not run')
    (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':main()
