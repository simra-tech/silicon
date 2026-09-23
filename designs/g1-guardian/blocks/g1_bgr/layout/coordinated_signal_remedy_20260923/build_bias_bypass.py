#!/usr/bin/env python3
"""Add only passed pbias/pcasc overlay; source/native/ports/TopMetal held."""
import argparse
import datetime
import json
import os
from pathlib import Path
import sys
import time
import pya

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'coordinated_full_closure'))
sys.path.insert(0,str(HERE.parent/'coordinated_return_remedy'))
from build_assembly import Assembly,PAIRS,CUTS,region,sha,dump,SOURCE
from build_viaquad import texts


def main():
    ap=argparse.ArgumentParser()
    for k in ('output','preflight','resource-gate'):ap.add_argument('--'+k,type=Path,required=True)
    a=ap.parse_args();gate=json.loads(a.resource_gate.read_text())
    age=(datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(gate['utc'])).total_seconds()
    assert gate['status']=='passed' and 0<=age<1800 and gate['project_cpu_budget']>=45
    assert set(os.sched_getaffinity(0))=={1}
    bulk=Path(os.environ['G1_RESULTS_ROOT']);base=bulk/'bgr-assembly-signalbypass-20260922-r1'
    assert sha(base/'bank.gds')=='6d86b9d40333958cb8186d486d29db1532a816e302871e11d07e0f1d999cfc04'
    pre=json.loads(a.preflight.read_text());assert pre['status']=='passed geometric screen'
    assert all(c['passed'] for c in pre['checks']) and not pre['mutual_foreign_clearance']
    assert all(sha(Path(p))==h for p,h in pre['inputs'].items())
    assert {r['net'] for r in pre['ledger']}=={'pbias','pcasc'}
    assert {r['layer'] for r in pre['ledger']}=={'M4','M5','Via4'}
    original=bulk/'bgr-assembly-20260922-r5';viaquad=bulk/'bgr-assembly-viaquad-20260922-r3'
    paths=[base/'bank.gds',base/'bank.cdl',base/'preparation.json',a.preflight,a.resource_gate,
        SOURCE,Path(__file__),HERE.parent/'coordinated_full_closure/build_assembly.py',
        HERE.parent/'coordinated_return_remedy/build_viaquad.py',original/'routing.json',viaquad/'changed_shapes.json']
    bindings={str(p):sha(p) for p in paths}
    assert sha(SOURCE)=='586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b'
    a.output.mkdir(exist_ok=False);start=time.monotonic()
    (a.output/'worker_snapshot.py').write_bytes(Path(__file__).read_bytes())
    run=dict(status='running',cpu=1,watchdog_s=180,memory_reservation_gib=4,memory_enforced=False)
    dump(a.output/'run.json',run)
    try:
        ly=pya.Layout();ly.read(str(base/'bank.gds'));top=ly.top_cell()
        before={(ly.get_info(i).layer,ly.get_info(i).datatype):region(top,i) for i in ly.layer_indices()}
        text_before=texts(top)
        hierarchy=sorted((c.name,c.child_instances()) for c in ly.each_cell())
        # Every non-top native cell is held byte-for-byte at shape/instance API level.
        def local_records(layout,top_name):
            return {c.name:dict(instances=sorted((i.cell.name,str(i.cplx_trans),str(i.a),str(i.b),i.na,i.nb,i.prop_id) for i in c.each_inst()),
                shapes=sorted((str(layout.get_info(li)),str(s)) for li in layout.layer_indices() for s in c.shapes(li).each()))
                for c in layout.each_cell() if c.name!=top_name}
        local_before=local_records(ly,top.name)
        overlay=pya.Layout();overlay.dbu=ly.dbu;ot=overlay.create_cell('g1_bgr_bias_bypass_overlay')
        added={}
        for r in pre['ledger']:
            pair=PAIRS[r['layer']];shape=pya.Box(*r['bbox_dbu'])
            top.shapes(ly.layer(*pair)).insert(shape);ot.shapes(overlay.layer(*pair)).insert(shape)
            added.setdefault(pair,pya.Region()).insert(shape)
        ly.write(str(a.output/'bank.gds'));overlay.write(str(a.output/'bias_bypass_overlay.gds'))
        (a.output/'bank.cdl').write_bytes((base/'bank.cdl').read_bytes())
        saved=pya.Layout();saved.read(str(a.output/'bank.gds'));actual=saved.top_cell()
        assert texts(actual)==text_before
        assert sorted((c.name,c.child_instances()) for c in saved.each_cell())==hierarchy
        assert local_records(saved,actual.name)==local_before
        pairs=set(before)|{(saved.get_info(i).layer,saved.get_info(i).datatype) for i in saved.layer_indices()}
        for pair in pairs:
            old=before.get(pair,pya.Region());new=region(actual,saved.layer(*pair))
            assert (new^(old+added.get(pair,pya.Region()))).is_empty(),pair
        graph=Assembly(a.output);graph.probes=json.loads((original/'routing.json').read_text())['source_probes']
        graph.star=json.loads((viaquad/'changed_shapes.json').read_text())['star_interfaces']
        full=graph.graph(actual)
        cuts=[graph.graph(actual,(role,)) for role in graph.star]
        cuts += [graph.graph(actual,tuple(graph.star)),graph.graph(actual,precision=True)]
        dump(a.output/'terminal_graph.json',full);dump(a.output/'star_cuts.json',cuts)
        assert full['status']=='passed' and len(cuts)==7 and all(c['status']=='passed' for c in cuts)
        ltn=pya.LayoutToNetlist(pya.RecursiveShapeIterator(saved,actual,[]))
        layers={k:ltn.make_layer(saved.layer(*p),k) for k,p in PAIRS.items()}
        for k in layers:ltn.connect(layers[k])
        for cut,ends in CUTS.items():
            for end in ends:ltn.connect(layers[cut],layers[end])
        ltn.extract_netlist();nets={}
        for p in graph.probes:
            node=ltn.probe_net(layers[p['layer']],pya.Point(*p['point']))
            assert node is not None
            if p['net'] in nets:assert nets[p['net']].cluster_id==node.cluster_id
            nets[p['net']]=node
        coverage=[]
        for r in pre['ledger']:
            shape=pya.Region(pya.Box(*r['bbox_dbu']))
            own=ltn.shapes_of_net(nets[r['net']],layers[r['layer']],True)
            assert (shape-own).is_empty(),r
            if r['layer'] in CUTS:
                for end in CUTS[r['layer']]:
                    own_end=ltn.shapes_of_net(nets[r['net']],layers[end],True)
                    assert (shape.sized(55)-own_end).is_empty(),r
            coverage.append(dict(r,all_area_owned_by_assigned_net=True))
        dump(a.output/'added_geometry_ownership.json',coverage)
        assert (pya.Region(actual.bbox())-pya.Region(pya.Box(0,0,420000,354000))).is_empty()
        assert all(v%5==0 for r in pre['ledger'] for v in r['bbox_dbu'])
        assert all(sha(Path(p))==h for p,h in bindings.items())
        result=dict(status='passed preparation',inputs=bindings,source_count=1036,
            source_ports=json.loads((base/'preparation.json').read_text())['source_ports'],
            source_nets=sorted(nets),additive_route_ledger=pre['ledger'],
            native_non_top_shape_instance_parity=True,all_layer_native_plus_overlay_XOR_zero=True,
            all_text_and_nine_ports_unchanged=True,TopMetal1_TopMetal2_unchanged=True,
            all55nets_seven_star_cuts=True,all_added_metal_and_cut_faces_same_net=True,
            gds_sha256=sha(a.output/'bank.gds'),cdl_sha256=sha(a.output/'bank.cdl'),
            overlay_sha256=sha(a.output/'bias_bypass_overlay.gds'),
            stock_DRC_LVS_AP='not run',conditional_R_OP='not run',adoption='not run')
        dump(a.output/'preparation.json',result);run['status']='passed'
    except Exception as e:
        run.update(status='failed',error=repr(e));raise
    finally:
        run['wall_s']=time.monotonic()-start;dump(a.output/'run.json',run);print(json.dumps(run,indent=2))


if __name__=='__main__':main()
