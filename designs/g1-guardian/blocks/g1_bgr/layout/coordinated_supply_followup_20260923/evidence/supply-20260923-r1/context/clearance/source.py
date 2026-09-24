#!/usr/bin/env python3
"""Independent exact-pruned-parent graph clearance; no naming-based net joins."""
import argparse
import json
import os
from pathlib import Path
import time
import pya
from check_full_context_flat import ROOT,sha,dump,region,METALS,CUTS,graph,flatten_conductors,PAIRS,hierarchy_control

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--candidate',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    assert not a.output.exists() and set(os.sched_getaffinity(0))=={0}
    bulk=Path(os.environ['G1_RESULTS_ROOT']);gds=a.candidate/'supply_context_native.gds'
    meta=json.loads((a.candidate/'analysis.json').read_text())
    assert meta['status'].startswith('passed') and sha(gds)==meta['GDS_sha256']
    routes=bulk/'bgr-assembly-20260922-r5/routing.json';local=bulk/'bgr-supply-candidate-20260923-r1/bank.gds'
    golden=bulk/'bgr-assembly-signalbypass-20260922-r1/bank.gds'
    parent=ROOT/'designs/g1-guardian/review/audits/fullchip_reference_closure/physical_lvs/full_marker_candidate/evidence-20260923-r1/candidate/io_marker_native.gds'
    assert sha(parent)==meta['original_parent_sha256']
    control=bulk/'bgr-supply-local-control-20260923-r2/analysis.json'
    assert json.loads(control.read_text())['status']=='passed reproduction and exact-flat recovery control'
    inputs={str(p):sha(p) for p in (control,gds,a.candidate/'analysis.json',routes,local,golden,parent,Path(__file__))}
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    start=time.monotonic();result=dict(status='running',inputs=inputs);dump(a.output/'analysis.json',result)
    try:
        result['controls']=hierarchy_control()
        ly=pya.Layout();ly.read(str(gds));top=ly.top_cell()
        found=[i for i in top.each_inst() if i.cell.name=='bgr_supply_additive_context_candidate'];assert len(found)==1
        found[0].delete()  # In-memory only: graph must precede added conductors to expose captures.
        old=pya.Layout();old.read(str(parent));ot=old.top_cell()
        removed=pya.Region()
        for r in meta['removed_fills']:removed.insert(pya.Polygon([pya.Point(*p) for p in r['global_hull']]))
        for index in old.layer_indices():
            pair=(old.get_info(index).layer,old.get_info(index).datatype)
            expected=region(ot,index)
            if pair==(67,22):expected-=removed
            assert (expected^region(top,ly.layer(*pair))).is_empty(),pair
        # Original fills are separate physical islands, not a supply path or native device.
        assert (removed&region(ot,old.layer(67,0))).is_empty()
        for cut in (66,125):assert (removed&region(ot,old.layer(cut,0))).is_empty(),cut
        rest_fill=region(ot,old.layer(67,22))-removed
        assert (removed.sized(250)&rest_fill).is_empty()
        fl,ft,counts=flatten_conductors(ly,top);pg,ps=graph(fl,ft,True)
        cl=pya.Layout();cl.read(str(local));ct=cl.top_cell()
        cf,cft,local_counts=flatten_conductors(cl,ct);cg,cs=graph(cf,cft)
        result['local_exact_flat_conductor_counts']=local_counts
        gl=pya.Layout();gl.read(str(golden));gt=gl.top_cell()
        trans=pya.ICplxTrans(1,0,False,331000,732000)
        bindings={};probes=json.loads(routes.read_text())['source_probes']
        local_clusters={}
        for probe in probes:
            net=probe['net'];layer=PAIRS[probe['layer']][0];point=pya.Point(*probe['point'])
            pn=pg.probe_net(ps[(layer,0)],trans*point);cn=cg.probe_net(cs[(layer,0)],point)
            assert pn and cn,probe
            bindings.setdefault(net,set()).add(pn.cluster_id);local_clusters.setdefault(net,set()).add(cn.cluster_id)
        assert len(bindings)==55 and all(len(s)==1 for s in bindings.values())
        assert len({next(iter(s)) for s in bindings.values()})==55
        assert all(len(s)==1 for s in local_clusters.values()) and len({next(iter(s)) for s in local_clusters.values()})==55
        rows=[]
        for net in ('vdd','vss','dvbe'):
            p=next(p for p in probes if p['net']==net);layer=PAIRS[p['layer']][0];point=pya.Point(*p['point'])
            pn=pg.probe_net(ps[(layer,0)],trans*point);cn=cg.probe_net(cs[(layer,0)],point)
            for k in METALS+tuple(CUTS):
                delta=(region(ct,cl.layer(k,0))-region(gt,gl.layer(k,0)))&cg.shapes_of_net(cn,cs[(k,0)],True)
                if delta.is_empty():continue
                added=delta.transformed(trans);material=region(top,ly.layer(k,0));own=pg.shapes_of_net(pn,ps[(k,0)],True)
                if k in METALS:
                    material+=region(top,ly.layer(k,22));own+=pg.shapes_of_net(pn,ps[(k,22)],True)
                foreign=material-own;overlap=added&foreign
                proximity=added.sized(250)&foreign if k in METALS else pya.Region();cut_hits={}
                if k in METALS:
                    for cut,ends in CUTS.items():
                        if k in ends:
                            fc=region(top,ly.layer(cut,0))-pg.shapes_of_net(pn,ps[(cut,0)],True)
                            cut_hits[str(cut)]=[str(p.bbox()) for p in (added&fc).each()]
                rows.append(dict(net=net,layer=k,added_area_um2=added.area()*1e-6,
                    passed=overlap.is_empty() and proximity.is_empty() and not any(cut_hits.values()),
                    foreign_overlap=[str(p.bbox()) for p in overlap.each()],
                    foreign_250nm_proximity=[str(p.bbox()) for p in proximity.each()],foreign_cut_capture=cut_hits))
        assert abs(sum(r['added_area_um2'] for r in rows)-733.166)<1e-7
        assert all(sha(Path(p))==h for p,h in inputs.items())
        result.update(status='passed exact pruned-parent source-owned clearance' if all(r['passed'] for r in rows) else 'failed exact pruned-parent clearance',
            source_net_bindings={k:list(v)[0] for k,v in bindings.items()},source_probe_count=len(probes),
            all_55_source_nets_distinct=True,removed_fills_are_isolated=True,
            exact_parent_minus_ten_fills_XOR=True,exact_flat_conductor_counts=counts,checks=rows,
            final_all_chip_terminal_enumeration='not run',fullchip_LVS='not run',adoption='not run')
        assert all(r['passed'] for r in rows),rows
    except Exception as e:
        result.update(status='failed pruned-context gate',error=repr(e));raise
    finally:
        result['wall_s']=time.monotonic()-start;dump(a.output/'analysis.json',result)
        print(json.dumps({k:v for k,v in result.items() if k not in ('inputs','exact_flat_conductor_counts')},indent=2))

if __name__=='__main__':main()
