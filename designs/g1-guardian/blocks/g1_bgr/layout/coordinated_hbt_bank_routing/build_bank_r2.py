#!/usr/bin/env python3
"""Two frozen r1 substitutions, with source/route/geometry delta audit."""
import argparse
import collections
import contextlib
import hashlib
import io
import json
from pathlib import Path
import pya

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[5]
OLD=ROOT/'build/scratch/bgr-hbt-fullbank-20260922-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def reg(cell,li):
    r=pya.Region(cell.begin_shapes_rec(li));r.flatten();return r

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    original=HERE/'build_bank.py'
    assert sha(original)=='3030cb0fa264d6c077040a7343879bcf70d58fa6318a668e8eeee0b5f80e9a39'
    assert sha(OLD/'bank.gds')=='78ce18af3cd2dfbc36a1abc6319ef9a62e85381217efe115cc5bd3aaf1859dfc'
    assert a.output.is_dir() and not (a.output/'bank.gds').exists()
    proof=io.StringIO()
    with contextlib.redirect_stdout(proof):
        path=HERE/'verify_dummy_seed.py'
        exec(compile(path.read_text(),str(path),'exec'),{'__file__':str(path),'__name__':'native_seed_proof'})
    evidence=json.loads(proof.getvalue());assert evidence['status'].startswith('passed')
    dump(a.output/'dummy_seed_proof.json',evidence)
    text=original.read_text()
    substitutions=[('py=136+1.2*i;tx=trunk[role]','py=136+.6*i;tx=trunk[role]'),
       ("('B',nodes[1],'M1',x+.6,y-1.5,GUARD if dummy else nodes[1]),",
        "('B',nodes[1],'M1',x if dummy else x+.6,y-1.14 if dummy else y-1.5,GUARD if dummy else nodes[1]),")]
    for before,after in substitutions:
        assert text.count(before)==1,before;text=text.replace(before,after)
    (a.output/'derived_builder.py').write_text(text)
    scope={'__file__':str(Path(__file__).resolve()),'__name__':'derived_r2'}
    exec(compile(text,str(original),'exec'),scope)
    status=scope['Bank'](a.output).run()
    previous=json.loads((OLD/'route_ledger.json').read_text())
    current=json.loads((a.output/'route_ledger.json').read_text())
    def delta(key):
        aa=collections.Counter(json.dumps(r,sort_keys=True) for r in previous[key])
        bb=collections.Counter(json.dumps(r,sort_keys=True) for r in current[key])
        return dict(removed=[json.loads(s) for s,n in (aa-bb).items() for _ in range(n)],
                    added=[json.loads(s) for s,n in (bb-aa).items() for _ in range(n)])
    routes=delta('routes');vias=delta('vias')
    assert all(len(routes[k])==24 and len(vias[k])==12 for k in ('removed','added'))
    for side in ('removed','added'):
        assert all(v['layer']=='Via2' and not v['interface'] for v in vias[side])
        assert all(r['role'] in scope['SIGNALS'] and r['layer'] in ('M2','M3') and
                   r['purpose'] in ('source_trunk','port_escape','via_landing') for r in routes[side])
    assert previous['star_interfaces']==current['star_interfaces']
    changed=[]
    for old,new in zip(previous['probes'],current['probes']):
        if old==new:continue
        assert {k:v for k,v in old.items() if k!='point_dbu'}=={k:v for k,v in new.items() if k!='point_dbu'}
        assert (old['role']==scope['GUARD'] and old['terminal']=='B') or old['instance']=='port'
        changed.append(dict(before=old,after=new))
    assert len(changed)==15 and sum(x['before']['instance']=='port' for x in changed)==6
    assert (OLD/'bank.cdl').read_bytes()==(a.output/'bank.cdl').read_bytes()
    aa,bb=pya.Layout(),pya.Layout();aa.read(str(OLD/'bank.gds'));bb.read(str(a.output/'bank.gds'))
    allowed=pya.Region(pya.Box(190400,135800,200800,143500));xors=[];text_changes=[]
    infos={(i.layer,i.datatype) for i in aa.layer_infos()+bb.layer_infos()}
    for pair in sorted(infos):
        parts=[];texts=[]
        for ly in (aa,bb):
            li=ly.layer(*pair);top=ly.top_cell();parts.append(reg(top,li))
            it=top.begin_shapes_rec(li);found=[]
            while not it.at_end():
                if it.shape().is_text():found.append(str(it.shape().text.transformed(it.trans())))
                it.next()
            texts.append(collections.Counter(found))
        difference=parts[0]^parts[1]
        if not difference.is_empty():
            assert pair in ((10,0),(29,0),(30,0),(30,2)) and (difference-allowed).is_empty(),pair
            xors.append(dict(layer=pair,xor_area_dbu2=difference.area()))
        if texts[0]!=texts[1]:
            assert pair==(30,25)
            removed=list((texts[0]-texts[1]).elements());added=list((texts[1]-texts[0]).elements())
            assert len(removed)==len(added)==6
            text_changes.append(dict(layer=pair,removed=removed,added=added))
    assert len(text_changes)==1
    audit=dict(status='passed exact two-change delta',parent_GDS_sha256=sha(OLD/'bank.gds'),
               candidate_GDS_sha256=sha(a.output/'bank.gds'),unchanged_CDL_sha256=sha(a.output/'bank.cdl'),
               substitutions=substitutions,derived_builder_sha256=sha(a.output/'derived_builder.py'),
               route_delta=routes,via_delta=vias,probe_changes=changed,serialized_layer_XOR=xors,
               source_port_text_changes=text_changes,star_interfaces_unchanged=True,
               native_and_all_other_geometry_unchanged=True,r1_short_and_missing_probes='failed retained')
    dump(a.output/'revision_audit.json',audit)
    prep=json.loads((a.output/'preparation.json').read_text())
    prep['revision_audit_sha256']=sha(a.output/'revision_audit.json');dump(a.output/'preparation.json',prep)
    print(json.dumps({k:audit[k] for k in ['status','candidate_GDS_sha256','unchanged_CDL_sha256']},indent=2))
    return status

if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as e:
        out=Path(__import__('sys').argv[__import__('sys').argv.index('--output')+1])
        dump(out/'revision_exception.json',dict(status='failed',exception=type(e).__name__,message=str(e)));raise
