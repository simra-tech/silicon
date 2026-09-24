#!/usr/bin/env python3
"""Read-only BGR additive-delta check against the actual assembled parent."""
import argparse
import json
import os
from pathlib import Path
import sys
import time
import pya

HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'flow/run.sh').is_file())
sys.path.insert(0,str(HERE.parent/'coordinated_full_closure'))
from build_assembly import PAIRS,region,sha,dump
sys.path.insert(0,str(HERE.parent/'coordinated_return_remedy'))
from build_viaquad import texts
METALS=(8,10,30,50,67,126,134)
CUTS={19:(8,10),29:(10,30),49:(30,50),66:(50,67),125:(67,126),133:(126,134)}


def graph(layout,top,dummy=False):
    ltn=pya.LayoutToNetlist(pya.RecursiveShapeIterator(layout,top,[]))
    layers={(k,0):ltn.make_layer(layout.layer(k,0),'L%d'%k) for k in METALS+tuple(CUTS)}
    for r in layers.values():ltn.connect(r)
    for cut,ends in CUTS.items():
        for end in ends:ltn.connect(layers[(cut,0)],layers[(end,0)])
    if dummy:
        for k in METALS:
            layers[(k,22)]=ltn.make_layer(layout.layer(k,22),'DM%d'%k)
            ltn.connect(layers[(k,22)]);ltn.connect(layers[(k,0)],layers[(k,22)])
            for cut,ends in CUTS.items():
                if k in ends:ltn.connect(layers[(cut,0)],layers[(k,22)])
    ltn.extract_netlist()
    return ltn,layers


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args();assert not a.output.exists() and set(os.sched_getaffinity(0))=={0}
    bulk=Path(os.environ['G1_RESULTS_ROOT'])
    parent=ROOT/'designs/g1-guardian/review/audits/fullchip_reference_closure/physical_lvs/full_marker_candidate/evidence-20260923-r1/candidate/io_marker_native.gds'
    golden=bulk/'bgr-assembly-signalbypass-20260922-r1/bank.gds'
    candidate=bulk/'bgr-supply-candidate-20260923-r1/bank.gds'
    route=bulk/'bgr-assembly-20260922-r5/routing.json'
    assert sha(parent)=='ae62bf68aa001144c08a37c58ac3553c6e5f2013a6824b340218e84962066aca'
    assert sha(golden)=='6d86b9d40333958cb8186d486d29db1532a816e302871e11d07e0f1d999cfc04'
    inputs={str(p):sha(p) for p in (parent,golden,candidate,route,Path(__file__))}
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    start=time.monotonic();result=dict(status='running',inputs=inputs,fullchip_mutation='not run')
    dump(a.output/'analysis.json',result)
    try:
        pl=pya.Layout();pl.read(str(parent));pt=pl.top_cell()
        found=[]
        def walk(cell,tr,path):
            if cell.name=='g1_bgr_candidate':found.append((cell,tr,path));return
            for inst in cell.each_inst():
                for it in inst.cell_inst.each_cplx_trans():walk(inst.cell,tr*it,path+[inst.cell.name])
        walk(pt,pya.ICplxTrans(),[pt.name]);assert len(found)==1,len(found)
        cell,tr,path=found[0]
        gl=pya.Layout();gl.read(str(golden));gt=gl.top_cell()
        pairs={(gl.get_info(i).layer,gl.get_info(i).datatype) for i in gl.layer_indices()}|{(pl.get_info(i).layer,pl.get_info(i).datatype) for i in pl.layer_indices()}
        diffs=[pair for pair in pairs if not(region(cell,pl.layer(*pair))^region(gt,gl.layer(*pair))).is_empty()]
        result.update(hierarchy=path,transform=str(tr),native_layer_XOR_failures=diffs)
        assert not diffs,diffs
        assert texts(cell)==texts(gt)
        cl=pya.Layout();cl.read(str(candidate));ct=cl.top_cell()
        cg,cs=graph(cl,ct);pg,ps=graph(pl,pt,True)
        probes=json.loads(route.read_text())['source_probes'];rows=[]
        for net in ('vdd','vss','dvbe'):
            p=next(r for r in probes if r['net']==net)
            layer=PAIRS[p['layer']][0];local=pya.Point(*p['point']);at=tr*local
            cn=cg.probe_net(cs[(layer,0)],local);pn=pg.probe_net(ps[(layer,0)],at)
            assert cn is not None and pn is not None
            for k in METALS+tuple(CUTS):
                old=region(gt,gl.layer(k,0));new=region(ct,cl.layer(k,0))
                assert (old-new).is_empty(),k
                delta=(new-old)&cg.shapes_of_net(cn,cs[(k,0)],True)
                if delta.is_empty():continue
                added=delta.transformed(tr)
                own=pg.shapes_of_net(pn,ps[(k,0)],True)
                material=region(pt,pl.layer(k,0))
                floating_fill=[]
                if k in METALS:
                    dm=region(pt,pl.layer(k,22));own_dm=pg.shapes_of_net(pn,ps[(k,22)],True)
                    own+=own_dm;material+=dm
                    floating_fill=[str(p.bbox()) for p in (added&(dm-own_dm)).each()]
                foreign=material-own
                overlap=added&foreign
                near=added.sized(250)&foreign if k in METALS else pya.Region()
                cut_hits={}
                if k in METALS:
                    for cut,ends in CUTS.items():
                        if k in ends:
                            fc=region(pt,pl.layer(cut,0))-pg.shapes_of_net(pn,ps[(cut,0)],True)
                            cut_hits[str(cut)]=[str(p.bbox()) for p in (added&fc).each()]
                rows.append(dict(net=net,layer=k,added_area_um2=added.area()*1e-6,
                    same_net_parent_cluster=pn.cluster_id,
                    passed=overlap.is_empty() and near.is_empty() and not any(cut_hits.values()),
                    foreign_overlap_bbox=[str(p.bbox()) for p in overlap.each()],
                    foreign_250nm_proximity_bbox=[str(p.bbox()) for p in near.each()],
                    foreign_cut_capture=cut_hits,unowned_datatype22_capture=floating_fill))
        # Every candidate delta must be accounted for by one source-owned row.
        accounted=sum(r['added_area_um2'] for r in rows)
        expected=sum((region(ct,cl.layer(k,0))-region(gt,gl.layer(k,0))).area()*1e-6 for k in METALS+tuple(CUTS))
        assert abs(accounted-expected)<1e-8,(accounted,expected)
        assert all(sha(Path(p))==h for p,h in inputs.items())
        result.update(status='passed full-parent source-owned additive clearance' if all(r['passed'] for r in rows) else 'failed full-parent additive clearance',
            all_native_layer_XOR_zero=True,all_native_text_exact=True,checks=rows,
            complete_delta_area_um2=accounted,datatype22_policy='Conservatively included as conductive material; unowned fill is not waived.',
            new_stock_fullchip='not run',fullchip_integration='not run',new_electrical='not run')
    except Exception as e:
        result.update(status='failed context harness or gate',error=repr(e));raise
    finally:
        result['wall_s']=time.monotonic()-start;dump(a.output/'analysis.json',result)
        print(json.dumps({k:v for k,v in result.items() if k!='inputs'},indent=2))


if __name__=='__main__':main()
