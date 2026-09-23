#!/usr/bin/env python3
"""Independent serialized-GDS structural proof of candidate-only text changes."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import pya

TOP='placed_core_NOT_CONNECTED_FULLCHIP'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def records(ly,c,text=None):
    out=Counter()
    for li in ly.layer_indexes():
        info=ly.get_info(li)
        for s in c.shapes(li).each():
            if text is None or s.is_text()==text:
                out[(info.layer,info.datatype,s.to_s(),str(s.properties()))]+=1
    return out
def insts(c):
    return [(i.cell.name,str(i.cplx_trans),str(i.a),str(i.b),i.na,i.nb,str(i.properties())) for i in c.each_inst()]
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--reference',type=Path,required=True)
    ap.add_argument('--candidate',type=Path,required=True)
    ap.add_argument('--transformation',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    assert not a.output.exists()
    meta=json.loads(a.transformation.read_text());assert sha(a.reference)==meta['input_gds_sha256'] and sha(a.candidate)==meta['output_gds_sha256']
    old=pya.Layout();old.read(str(a.reference));new=pya.Layout();new.read(str(a.candidate))
    assert old.dbu==new.dbu==.001
    original={c.name for c in old.each_cell()};clones={r['clone']:r['source'] for r in meta['clones']}
    retained={c.name for c in new.each_cell()}&original
    assert {c.name for c in new.each_cell()}==retained|set(clones) and TOP in retained
    assert [c.name for c in old.top_cells()]==[TOP]==[c.name for c in new.top_cells()]
    ot=old.cell(TOP);nt=new.cell(TOP)
    for c in old.each_cell():
        nc=new.cell(c.name)
        if c.name!=TOP and nc is not None:
            assert records(old,c)==records(new,nc),(c.name,'shapes',len(records(old,c)),len(records(new,nc)),list((records(old,c)-records(new,nc)).items())[:1])
            assert Counter(insts(c))==Counter(insts(nc)),(c.name,'instances',len(insts(c)),len(insts(nc)),list((Counter(insts(c))-Counter(insts(nc))).items())[:2])
            assert c.properties()==nc.properties(),(c.name,'properties',c.properties(),nc.properties())
    assert records(old,ot,False)==records(new,nt,False)
    added=records(new,nt,True)-records(old,ot,True)
    removed=records(old,ot,True)-records(new,nt,True)
    assert not removed and sum(added.values())==22
    assert all(k[:2]==(134,25) for k in added)
    assert ot.properties()==nt.properties()
    deletions=Counter(r['cell'] for r in meta['text_occurrences_removed'])
    for clone,source in clones.items():
        oc=old.cell(source);nc=new.cell(clone)
        assert records(old,oc,False)==records(new,nc,False),clone
        assert not (records(new,nc,True)-records(old,oc,True)),clone
        assert sum((records(old,oc,True)-records(new,nc,True)).values())==deletions[clone],clone
        assert oc.properties()==nc.properties(),clone
        oi=Counter(insts(oc));ni=Counter((clones.get(i[0],i[0]),)+i[1:] for i in insts(nc))
        assert oi==ni,(clone,'normalized instances',list((oi-ni).items())[:2],list((ni-oi).items())[:2])
    oi=Counter(insts(ot));ni=Counter((clones.get(i[0],i[0]),)+i[1:] for i in insts(nt))
    assert oi==ni,('top normalized instances',list((oi-ni).items())[:2],list((ni-oi).items())[:2])
    assert sum(deletions.values())==86 and len(meta['root_external_labels'])==22
    result=dict(status='passed serialized exact all-layer nontext identity by recursive cell/instance induction',
                original_GDS_sha256=sha(a.reference),candidate_GDS_sha256=sha(a.candidate),transformation_sha256=sha(a.transformation),
                original_cell_definitions_unchanged=len(retained)-1,unreachable_original_cells_omitted=len(original-retained),clone_count=len(clones),
                original_nontext_shape_records_unchanged=True,clone_nontext_shape_records_exact=True,
                all_instance_transforms_arrays_properties_exact=True,root_nontext_shape_records_exact=True,
                text_occurrences_removed=86,root_134_25_text_records_added=22,
                external_label_names=sorted(meta['root_external_labels']),
                flattened_all_layer_nontext_XOR_dbu2=0,stock_LVS='not run')
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
if __name__=='__main__':main()
