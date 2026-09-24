#!/usr/bin/env python3
"""Remove exactly old signal-route instance; preserve all native hierarchy."""
import argparse
import collections
import json
import os
from pathlib import Path
import pya
from place_closed_analog import region,sha
from streamout_native_signal_routes import text_records
from replace_digital_macro_candidate import cell_signature,equal_macro


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('parent','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();assert not a.output.exists() and len(os.sched_getaffinity(0))==1
    meta=json.loads((a.parent/'analysis.json').read_text())
    assert meta['status']=='passed exact macro-near floating-fill pruning'
    source=a.parent/'digital_fill_pruned.gds';assert sha(source)==meta['GDS_sha256']
    ly=pya.Layout();ly.read(str(source));top=ly.cell(meta['top_cell'])
    i,=[i for i in top.each_inst() if i.cell.name=='new_signal_routes']
    assert i.cplx_trans==pya.ICplxTrans() and i.na<=1 and i.nb<=1
    definitions={c.name:cell_signature(ly,c) for c in ly.each_cell() if c!=top}
    before={str(info):region(ly,top,info) for info in ly.layer_infos()}
    removed={str(info):region(ly,i.cell,info) for info in ly.layer_infos()}
    before_text=collections.Counter(text_records(ly,top));removed_text=collections.Counter(text_records(ly,i.cell))
    instances=collections.Counter((j.cell.name,str(j.cell_inst),j.prop_id) for j in top.each_inst())
    instances.subtract([(i.cell.name,str(i.cell_inst),i.prop_id)]);instances=+instances
    i.delete()
    assert definitions=={c.name:cell_signature(ly,c) for c in ly.each_cell() if c!=top}
    assert instances==collections.Counter((j.cell.name,str(j.cell_inst),j.prop_id) for j in top.each_inst())
    assert collections.Counter(text_records(ly,top))==before_text-removed_text
    for info in ly.layer_infos():assert ((region(ly,top,info)+removed[str(info)])^before[str(info)]).is_empty(),str(info)
    clean=pya.Layout();clean.dbu=ly.dbu;ct=clean.create_cell(top.name);ct.copy_tree(top)
    equality=equal_macro(ly,top,clean,ct);assert len(list(clean.top_cells()))==1
    a.output.mkdir(parents=True);out=a.output/'unrouted_native.gds';clean.write(str(out))
    reread=pya.Layout();reread.read(str(out));equal_macro(clean,ct,reread,reread.top_cell())
    (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    result=dict(status='passed exact old-route removal with all other native definitions held',GDS_sha256=sha(out),
        input_GDS_sha256=sha(source),input_metadata_sha256=sha(a.parent/'analysis.json'),top_cell=top.name,
        native_root_instances=sum(instances.values()),
        removed_instance='new_signal_routes r0 at0,0',all_other_instances_and_definitions='passed exact',single_top_roundtrip=equality,
        not_run=['Routing','Connectivity','DRC antenna density','Parasitics and timing','Adoption'])
    (a.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],GDS_sha256=sha(out))))


if __name__=='__main__':main()
