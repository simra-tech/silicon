#!/usr/bin/env python3
"""Exact hierarchy proof for removing only the obsolete signal-route instance.

Unlike the separately retained timed-out flat-region implementation, this
compares every reachable cell definition, text, shape and instance transform.
No geometric approximation or omitted layer is used. Final DRC/connectivity
remain independent required checks after actual routing.
"""
import argparse
import collections
import hashlib
import json
import os
from pathlib import Path
import time
import pya
from place_closed_analog import sha

def properties(obj):
    return repr(sorted(obj.properties().items(),key=lambda pair:repr(pair[0])))


def signature(layout,cell):
    shapes=[]
    for li in layout.layer_indexes():
        info=layout.get_info(li)
        for s in cell.shapes(li).each():
            shapes.append((info.layer,info.datatype,s.to_s(),properties(s)))
    children=sorted((i.cell.name,str(i.cplx_trans),str(i.a),str(i.b),i.na,i.nb,properties(i)) for i in cell.each_inst())
    return hashlib.sha256(json.dumps([properties(cell),sorted(shapes),children],separators=(',',':')).encode()).hexdigest()


def hierarchy(layout,top):
    todo=[top];result={}
    while todo:
        cell=todo.pop()
        if cell.name in result:continue
        children=list(cell.each_inst())
        result[cell.name]=signature(layout,cell)
        todo.extend(i.cell for i in children)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('parent','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();assert not a.output.exists() and len(os.sched_getaffinity(0))==1
    meta=json.loads((a.parent/'analysis.json').read_text())
    assert meta['status']=='passed exact macro-near floating-fill pruning'
    source=a.parent/'digital_fill_pruned.gds';assert sha(source)==meta['GDS_sha256']
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes());start=time.monotonic()
    result=dict(status='running',input_GDS_sha256=sha(source),input_metadata_sha256=sha(a.parent/'analysis.json'))
    def checkpoint(stage):
        result.update(stage=stage,wall_s=time.monotonic()-start)
        (a.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
        print(stage,flush=True)
    checkpoint('read native layout')
    try:
        ly=pya.Layout();ly.read(str(source));top=ly.cell(meta['top_cell']);bbox=top.bbox()
        before=hierarchy(ly,top);checkpoint('all original reachable definitions fingerprinted')
        i,=[i for i in top.each_inst() if i.cell.name=='new_signal_routes']
        assert i.cplx_trans==pya.ICplxTrans() and i.na<=1 and i.nb<=1
        direct=sorted((li.layer,li.datatype,s.to_s()) for li in ly.layer_infos() for s in top.shapes(ly.layer(li)).each())
        instances=collections.Counter((j.cell.name,str(j.cell_inst),j.prop_id) for j in top.each_inst())
        instances.subtract([(i.cell.name,str(i.cell_inst),i.prop_id)]);instances=+instances;i.delete()
        after=hierarchy(ly,top)
        assert all(before[name]==sig for name,sig in after.items() if name!=top.name)
        assert instances==collections.Counter((j.cell.name,str(j.cell_inst),j.prop_id) for j in top.each_inst())
        assert direct==sorted((li.layer,li.datatype,s.to_s()) for li in ly.layer_infos() for s in top.shapes(ly.layer(li)).each())
        assert top.bbox()==bbox;checkpoint('only declared root route instance removed')
        clean=pya.Layout();clean.dbu=ly.dbu;ct=clean.create_cell(top.name);ct.copy_tree(top)
        assert hierarchy(clean,ct)==after and len(list(clean.top_cells()))==1
        out=a.output/'unrouted_native.gds';clean.write(str(out));checkpoint('single-top copy exact; GDS written')
        reread=pya.Layout();reread.read(str(out));rt=reread.top_cell()
        assert hierarchy(reread,rt)==after and rt.bbox()==bbox and reread.dbu==ly.dbu
        assert sha(source)==meta['GDS_sha256']
        result.update(status='passed exact old-route removal with all other native definitions held',GDS_sha256=sha(out),
            top_cell=top.name,native_root_instances=sum(instances.values()),original_definitions=before,retained_definitions=after,
            removed_instance='new_signal_routes r0 at0,0',all_other_instances_and_definitions='passed exact',
            single_top_roundtrip='passed all cell shapes/texts/instance transforms and user properties exact',
            not_run=['Routing','Connectivity','DRC antenna density','Parasitics and timing','Adoption'])
        checkpoint('passed')
    except Exception as e:
        result.update(status='failed exact hierarchy route-removal proof',error=repr(e));checkpoint('failed');raise


if __name__=='__main__':main()
