#!/usr/bin/env python3
"""Small exact controls of detached fill projection and inverse reconstruction."""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import pya
from cached_fill import relocate

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'integration_be54'))
from flatten_cut_overlay import shapes,children,physical,signature,properties


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    assert not a.output.exists() and pya.__version__=='0.30.9' and len(os.sched_getaffinity(0))==1
    a.output.mkdir(parents=True);ly=pya.Layout();ly.dbu=.001;top=ly.create_cell('TOP')
    fill=ly.create_cell('Met1_M_FILL_CELL');li=ly.layer(8,22)
    fill.shapes(li).insert(pya.Box(-3,-7,19,23))
    fill.shapes(ly.layer(10,22)).insert(pya.Polygon([pya.Point(0,0),pya.Point(30,0),pya.Point(15,20)]))
    keep=ly.create_cell('NATIVE_HELD');keep.shapes(ly.layer(8,0)).insert(pya.Box(0,0,50,60))
    keep.shapes(ly.layer(8,25)).insert(pya.Text('SENSITIVE_NATIVE',pya.Trans(11,12)))
    kin=top.insert(pya.CellInstArray(keep.cell_index(),pya.Trans(700,800)));kin.set_property(12,'keep-property')
    top.set_property(11,'top-property');top.shapes(ly.layer(10,25)).insert(pya.Text('TOP_PIN',pya.Trans(9,9)))
    for i in range(64):
        top.insert(pya.CellInstArray(fill.cell_index(),pya.Trans(i%4,bool(i%2),i*200,i*90),pya.Vector(61,0),pya.Vector(0,71),3,2))
    original=a.output/'original.gds';ly.write(str(original))
    before={c.name:signature(ly,c) for c in ly.each_cell()};rs=shapes(ly,top);props=properties(top)
    reference=pya.Layout();reference.read(str(original));rt=reference.cell('TOP')
    # Deliberately simple independent unbatched path on the small control.
    for inst in list(rt.each_inst()):
        if inst.cell.name!=fill.name:continue
        child=inst.cell
        for tr in inst.cell_inst.each_cplx_trans():
            for idx in reference.layer_indexes():
                for shape in child.shapes(idx).each():
                    rt.shapes(idx).insert((shape.box if shape.is_box() else shape.polygon).transformed(tr))
        inst.delete()
    start=time.monotonic();added,arrays,expanded,expected=relocate(ly,top,{fill.name});elapsed=time.monotonic()-start
    assert shapes(ly,top)==shapes(reference,rt) and children(top)==children(rt)==expected
    assert properties(top)==props and sum(expanded.values())==384
    for idx in ly.layer_indexes():assert (physical(top,idx)^physical(rt,reference.layer(ly.get_info(idx)))).is_empty()
    candidate=a.output/'candidate.gds';ly.write(str(candidate));saved=pya.Layout();saved.read(str(candidate));st=saved.cell('TOP')
    assert shapes(saved,st)==rs+added and children(st)==expected
    remaining=added.copy()
    for idx in saved.layer_indexes():
        info=saved.get_info(idx)
        for shape in list(st.shapes(idx).each()):
            key=(info.layer,info.datatype,shape.to_s(),properties(shape))
            if remaining[key]>0:remaining[key]-=1;shape.delete()
    assert not any(remaining.values())
    for name,array in arrays:array.cell_index=saved.cell(name).cell_index();st.insert(array)
    assert {c.name:signature(saved,c) for c in saved.each_cell()}==before
    bad=Counter(added);key=next(iter(bad));bad[key]-=1
    assert rs+bad!=rs+added
    mismatch=next(k for k in expected);wrong=expected.copy();wrong[mismatch]+=1
    assert wrong!=children(top)
    result=dict(status='passed detached/batched equivalence, full layer XOR, saved inverse and negative controls',
        runtime=pya.__version__,arrays=len(arrays),expanded_occurrences=sum(expanded.values()),
        added_shapes=sum(added.values()),cached_wall_s=elapsed,
        all_native_geometry_text_properties_exact=True,missing_shape_negative=True,duplicate_native_instance_negative=True,
        original_GDS_sha256=sha(original),candidate_GDS_sha256=sha(candidate),
        sources={p.name:sha(p) for p in (Path(__file__),HERE/'cached_fill.py')},
        fullchip_prep='not run',native_LVS='not run',physical_change='not applicable')
    (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))


if __name__=='__main__':main()
