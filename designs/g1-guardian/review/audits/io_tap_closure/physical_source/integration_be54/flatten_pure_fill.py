#!/usr/bin/env python3
"""Flatten only proved device-free root fill occurrences, without deleting fill."""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import sys
import pya

ROOT=next(p for p in Path(__file__).resolve().parents if (p/'flow/run.sh').is_file())
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from flatten_cut_overlay import shapes,children,physical,signature,properties

FILL={'Act_FILL_CELL','GatP_FILL_CELL','Met1_M_FILL_CELL','Met1_S_FILL_CELL',
    'Met2_M_FILL_CELL','Met2_S_FILL_CELL','Met3_M_FILL_CELL','Met3_S_FILL_CELL',
    'Met4_M_FILL_CELL','Met4_S_FILL_CELL','Met5_M_FILL_CELL','Met5_S_FILL_CELL',
    'TM1_FILL_CELL','TM2_FILL_CELL'}


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(counter):
    return hashlib.sha256(json.dumps(sorted((list(key),count) for key,count in counter.items()),
        separators=(',',':')).encode()).hexdigest()


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0))==1 and pya.__version__=='0.30.9'
    bulk=Path(os.environ['G1_RESULTS_ROOT']);source=bulk/'analog-pair-overlay-flat-20260923-r1/overlay_flattened.gds'
    audit=bulk/'analog-pair-prepurge-audit-20260923-r3/summary.json'
    cdl=bulk/'analog-pair-reference-20260923-r1/physical_taps_reader.cdl'
    expected={source:'dcca5f47f6d397e8c6811116f092ac0f9adbbe761617a87ba69cec8216417333',
        cdl:'35b4b45b11427e327bc8a2cd145c27c70c102d00dd388a0199a0d19a96695f51',
        audit:'07e02ba5ebe729a0eb80dafab5e2a5a31754067afa6258ecb41495bc9b2e567b',
        ROOT/'designs/g1-guardian/review/audits/prepare_digital_reroute_native_hierarchy.py':'0d881688d344c59705fb8a1c768d2ec37ed83f0da30227c863314f8978d0de3c',
        HERE/'flatten_cut_overlay.py':'59faadff2e1eb2ed2d8d90232cff66f5c0cd3ad3a35ce17d25de0f234df51f38'}
    assert all(sha(p)==h for p,h in expected.items())
    aj=json.loads(audit.read_text());assert aj['status'].startswith('passed pre-purge snapshot inventory')
    expected[audit]=sha(audit);expected[Path(__file__)]=sha(Path(__file__))
    byname={r['name']:r for r in aj['circuits']}
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    result=dict(status='running pure-fill representation proof',inputs={str(p):h for p,h in expected.items()})
    def save():(a.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    save();ly=pya.Layout();ly.read(str(source));top=ly.cell('placed_core_NOT_CONNECTED_FULLCHIP')
    assert ly.dbu==.001 and [c.name for c in ly.top_cells()]==[top.name]
    before={c.name:signature(ly,c) for c in ly.each_cell()};rootshapes=shapes(ly,top);rootchildren=children(top)
    rootprops=properties(top);bbox=str(top.bbox());selected=[i for i in top.each_inst() if i.cell.name in FILL]
    names={i.cell.name for i in selected};assert names and names<=FILL
    templates={};layers=set()
    for name in sorted(names):
        c=ly.cell(name);r=byname[name]
        assert r['devices']==0 and r['subcircuits']==0 and r['all_nets_passive']
        assert not list(c.each_inst()) and not c.properties()
        template=[]
        for li in ly.layer_indexes():
            pair=(ly.get_info(li).layer,ly.get_info(li).datatype)
            for s in c.shapes(li).each():
                assert not s.properties() and (s.is_box() or s.is_polygon()),(name,s.to_s())
                # Exact generated-fill datatypes, not native device masks or labels.
                assert pair[1]==22 and pair[0] in (1,5,8,10,30,50,67,126,134),(name,pair)
                template.append([pair[0],pair[1],s.to_s(),properties(s)]);layers.add(pair)
        assert template;templates[name]=template
    added=Counter();saved_instances=[];expanded=Counter();expectedchildren=rootchildren.copy()
    for inst in selected:
        assert not inst.properties()
        child=inst.cell
        saved_instances.append((child.name,inst.cell_inst.dup()))
        key=(child.name,str(inst.cplx_trans),str(inst.a),str(inst.b),inst.na,inst.nb,properties(inst))
        expectedchildren[key]-=1
        if expectedchildren[key]==0:del expectedchildren[key]
        for tr in inst.cell_inst.each_cplx_trans():
            assert tr.mag==1 and tr.angle in (0,90,180,270)
            expanded[child.name]+=1
            for pair in layers:
                li=ly.layer(*pair)
                for s in child.shapes(li).each():
                    obj=s.box.transformed(tr) if s.is_box() else s.polygon.transformed(tr)
                    inserted=top.shapes(li).insert(obj)
                    added[(pair[0],pair[1],inserted.to_s(),properties(inserted))]+=1
        inst.delete()
    assert shapes(ly,top)==rootshapes+added and children(top)==expectedchildren and properties(top)==rootprops
    assert all(signature(ly,ly.cell(n))==h for n,h in before.items() if n!=top.name)
    result.update(phase='expanded exact fill instances',templates=templates,instance_arrays=len(saved_instances),
        expanded_occurrences=dict(expanded),added_shape_count=sum(added.values()),added_multiset_sha256=digest(added));save()
    clean=pya.Layout();clean.dbu=ly.dbu;ct=clean.create_cell(top.name);ct.copy_tree(top)
    destination=a.output/'pure_fill_flattened.gds';clean.write(str(destination))
    saved=pya.Layout();saved.read(str(destination));st=saved.cell(top.name)
    after={c.name:signature(saved,c) for c in saved.each_cell()};removed=set(before)-set(after)
    assert removed<=names and not set(after)-set(before)
    assert all(after[n]==h for n,h in before.items() if n not in removed|{top.name})
    assert shapes(saved,st)==rootshapes+added and children(st)==expectedchildren and properties(st)==rootprops
    assert str(st.bbox())==bbox and saved.dbu==.001 and [c.name for c in saved.top_cells()]==[top.name]
    original=pya.Layout();original.read(str(source));ot=original.cell(top.name);xor=[]
    for pair in sorted(layers):
        delta=physical(st,saved.layer(*pair))^physical(ot,original.layer(*pair))
        assert delta.is_empty(),pair;xor.append(dict(layer=list(pair),xor_dbu2=0))
        result.update(phase='full-parent XOR',full_affected_layer_XOR=xor);save()
    # Linear multiset subtraction from the actual saved result, not a blind
    # replacement with the original root; duplicate records keep multiplicity.
    remaining=added.copy()
    for li in saved.layer_indexes():
        info=saved.get_info(li)
        for s in list(st.shapes(li).each()):
            key=(info.layer,info.datatype,s.to_s(),properties(s))
            if remaining[key]>0:remaining[key]-=1;s.delete()
    assert not any(remaining.values()) and shapes(saved,st)==rootshapes
    for name in sorted(removed):saved.create_cell(name).copy_tree(original.cell(name))
    for name,ca in saved_instances:
        ca.cell_index=saved.cell(name).cell_index();st.insert(ca)
    assert {c.name:signature(saved,c) for c in saved.each_cell()}==before
    assert all(sha(p)==h for p,h in expected.items())
    result.update(status='passed exact pure-fill hierarchy projection; native LVS not run',GDS_sha256=sha(destination),
        removed_unreachable_definitions=sorted(removed),all_other_cell_definitions_exact=True,
        all_root_functional_geometry_text_properties_held=True,all_fill_geometry_preserved=True,
        inverse_saved_projection_all_definitions_exact=True,source_bytes_exact=True,
        native_LVS='not run',purge_speed_benefit='not run',physical_geometry_change='not applicable',adoption='not run')
    save()


if __name__=='__main__':main()
