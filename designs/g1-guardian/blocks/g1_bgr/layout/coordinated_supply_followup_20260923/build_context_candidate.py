#!/usr/bin/env python3
"""Isolated full-parent ten-fill exclusion plus held additive BGR metal view."""
import argparse
import json
import os
from pathlib import Path
import time
import pya
from check_full_context_flat import ROOT,sha,dump,region,texts,METALS,CUTS

PARENT_SHA='ae62bf68aa001144c08a37c58ac3553c6e5f2013a6824b340218e84962066aca'
GOLDEN_SHA='6d86b9d40333958cb8186d486d29db1532a816e302871e11d07e0f1d999cfc04'
CANDIDATE_SHA='e3ecfc6208fcae71c6b2f4223b7db3900677acfe30987b50ba6365c720297feb'

def functional(ly):
    return sorted((c.name,i.cell.name,str(i.cell_inst),i.prop_id) for c in ly.each_cell()
                  for i in c.each_inst() if '_FILL_CELL' not in i.cell.name)

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args();assert not a.output.exists() and set(os.sched_getaffinity(0))=={0}
    bulk=Path(os.environ['G1_RESULTS_ROOT'])
    parent=ROOT/'designs/g1-guardian/review/audits/fullchip_reference_closure/physical_lvs/full_marker_candidate/evidence-20260923-r1/candidate/io_marker_native.gds'
    golden=bulk/'bgr-assembly-signalbypass-20260922-r1/bank.gds'
    candidate=bulk/'bgr-supply-candidate-20260923-r1/bank.gds'
    ledger=bulk/'bgr-supply-fill-inventory-20260923-r1/analysis.json'
    assert sha(parent)==PARENT_SHA and sha(golden)==GOLDEN_SHA and sha(candidate)==CANDIDATE_SHA
    inputs={str(p):sha(p) for p in (parent,golden,candidate,ledger,Path(__file__))}
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    start=time.monotonic();result=dict(status='running',inputs=inputs)
    dump(a.output/'analysis.json',result)
    try:
        inventory=json.loads(ledger.read_text());rows=inventory['rows']
        assert inventory['status'].startswith('passed') and inventory['parent_sha256']==PARENT_SHA and len(rows)==10
        old=pya.Layout();old.read(str(parent));ot=old.top_cell()
        ly=pya.Layout();ly.read(str(parent));top=ly.top_cell()
        assert ly.dbu==old.dbu==.001 and top.bbox()==pya.Box(0,0,1414000,1414000)
        before_text=texts(top);before_functional=functional(ly)
        row=rows[0]
        assert all(r['parent_path']==[top.name] and r['parent_transform']=='r0 *1 0,0' for r in rows)
        keys=('parent_cell','child_cell','array_transform','na','nb','a','b','layer','datatype','child_shape')
        assert all(all(r[k]==row[k] for k in keys) for r in rows)
        matches=[i for i in top.each_inst() if i.cell.name==row['child_cell'] and
                 str(i.cplx_trans)==row['array_transform'] and i.na==row['na'] and i.nb==row['nb'] and
                 [i.a.x,i.a.y]==row['a'] and [i.b.x,i.b.y]==row['b']]
        assert len(matches)==1,len(matches)
        inst=matches[0];child=inst.cell
        assert child.name=='Met5_M_FILL_CELL' and not list(child.each_inst()) and inst.prop_id==0
        shapes=[(str(ly.get_info(i)),str(s)) for i in ly.layer_indices() for s in child.shapes(i).each()]
        assert shapes==[tuple(r) for r in row['child_shape']]
        polygon=next(child.shapes(ly.layer(67,22)).each()).polygon
        wanted={r['repetition_transform']:r for r in rows};assert len(wanted)==10
        keep=[];removed=pya.Region()
        for trans in inst.cell_inst.each_cplx_trans():
            if str(trans) not in wanted:keep.append(trans);continue
            poly=polygon.transformed(trans);r=wanted[str(trans)]
            assert [[p.x,p.y] for p in poly.each_point_hull()]==r['global_hull']
            removed.insert(poly)
        assert len(keep)==550 and removed.count()==10 and removed.area()==160000000
        ci=child.cell_index();inst.delete()
        for tr in keep:top.insert(pya.CellInstArray(ci,tr))
        assert functional(ly)==before_functional and texts(top)==before_text
        gl=pya.Layout();gl.read(str(golden));gt=gl.top_cell()
        cl=pya.Layout();cl.read(str(candidate));ct=cl.top_cell()
        assert texts(gt)==texts(ct)
        transform=pya.ICplxTrans(1,0,False,331000,732000)
        cells=[i for i in top.each_inst() if i.cell.name=='g1_bgr_candidate']
        assert len(cells)==1 and str(cells[0].cplx_trans)==str(transform)
        native=cells[0].cell
        pairs={(gl.get_info(i).layer,gl.get_info(i).datatype) for i in gl.layer_indices()}|{(cl.get_info(i).layer,cl.get_info(i).datatype) for i in cl.layer_indices()}
        overlay=ly.create_cell('bgr_supply_additive_context_candidate');deltas={}
        for pair in pairs:
            g=region(gt,gl.layer(*pair));c=region(ct,cl.layer(*pair))
            assert (region(native,ly.layer(*pair))^g).is_empty(),pair
            assert (g-c).is_empty(),pair
            delta=c-g
            if delta.is_empty():continue
            assert pair[1]==0 and pair[0] in METALS+tuple(CUTS),pair
            global_delta=delta.transformed(transform);deltas[pair]=global_delta
            for poly in global_delta.each():overlay.shapes(ly.layer(*pair)).insert(poly)
        assert abs(sum(r.area() for r in deltas.values())*1e-6-733.166)<1e-7
        top.insert(pya.CellInstArray(overlay.cell_index(),pya.Trans()))
        assert texts(top)==before_text
        assert functional(ly)==sorted(before_functional+[(top.name,overlay.name,str(next(i for i in top.each_inst() if i.cell.name==overlay.name).cell_inst),0)])
        pairs|={(old.get_info(i).layer,old.get_info(i).datatype) for i in old.layer_indices()}
        checks=[]
        for pair in sorted(pairs):
            orig=region(ot,old.layer(*pair));expected=orig.dup()
            if pair==(67,22):expected-=removed
            if pair in deltas:expected+=deltas[pair]
            actual=region(top,ly.layer(*pair))
            assert (expected^actual).is_empty(),pair
            # Exact reversal of the declared edits recovers the original union.
            inverse=actual.dup()
            if pair in deltas:
                assert (deltas[pair]&orig).is_empty(),('additive overlap',pair)
                inverse-=deltas[pair]
            if pair==(67,22):inverse+=removed
            assert (inverse^orig).is_empty(),('inverse',pair)
            checks.append(dict(layer=list(pair),added_area_um2=deltas.get(pair,pya.Region()).area()*1e-6,
                               removed_area_um2=160 if pair==(67,22) else 0,exact_XOR=True,inverse_XOR=True))
        gds=a.output/'supply_context_native.gds';ly.write(str(gds))
        reload=pya.Layout();reload.read(str(gds));rt=reload.top_cell()
        assert texts(rt)==before_text and rt.bbox()==ot.bbox()
        for pair in pairs:assert (region(rt,reload.layer(*pair))^region(top,ly.layer(*pair))).is_empty(),pair
        assert all(sha(Path(p))==h for p,h in inputs.items())
        result.update(status='passed isolated exact ten-fill and additive BGR geometry proof',GDS_sha256=sha(gds),
            original_parent_sha256=PARENT_SHA,source_BRG_geometry_sha256=CANDIDATE_SHA,
            removed_fills=rows,removed_fill_area_um2=160,retained_array_repetitions=550,
            layer_checks=checks,all_functional_native_geometry_text_and_ports_held=True,
            fullchip_connectivity='not run',stock_main='not run',stock_maximal='not run',
            stock_antenna='not run',stock_density='not run',strict_fullchip_LVS='not run',adoption='not run')
    except Exception as e:
        result.update(status='failed isolated context candidate',error=repr(e));raise
    finally:
        result['wall_s']=time.monotonic()-start;dump(a.output/'analysis.json',result)
        print(json.dumps({k:v for k,v in result.items() if k not in ('inputs','removed_fills','layer_checks')},indent=2))

if __name__=='__main__':main()
