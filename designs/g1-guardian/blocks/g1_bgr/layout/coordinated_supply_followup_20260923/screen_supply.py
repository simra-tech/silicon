#!/usr/bin/env python3
"""Finite same-layer clearance screen, without modifying native geometry."""
import argparse
import json
import os
from pathlib import Path
import sys
import time
import pya

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'coordinated_full_closure'))
from build_assembly import PAIRS,CUTS,region,sha,dump


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args();assert not a.output.exists() and set(os.sched_getaffinity(0))=={0}
    bulk=Path(os.environ['G1_RESULTS_ROOT'])
    gds=bulk/'bgr-dvbe-collector-candidate-20260923-r1/bank.gds'
    route=bulk/'bgr-assembly-20260922-r5/routing.json'
    prior=bulk/'bgr-supply-remaining-20260923-r1/analysis.json'
    assert sha(gds)=='1f32630e487f70979150943e432f9ecdb68bbd35873fa94e1c0bce2b670df524'
    assert json.loads(prior.read_text())['status']=='passed source-owned saved endpoint attribution'
    inputs={str(p):sha(p) for p in (gds,route,prior,Path(__file__),HERE.parent/'coordinated_full_closure/build_assembly.py')}
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes());start=time.monotonic()
    ly=pya.Layout();ly.read(str(gds));top=ly.top_cell()
    ltn=pya.LayoutToNetlist(pya.RecursiveShapeIterator(ly,top,[]))
    layers={k:ltn.make_layer(ly.layer(*v),k) for k,v in PAIRS.items()}
    for k in layers:ltn.connect(layers[k])
    for cut,ends in CUTS.items():
        for end in ends:ltn.connect(layers[cut],layers[end])
    ltn.extract_netlist();nets={}
    for p in json.loads(route.read_text())['source_probes']:
        n=ltn.probe_net(layers[p['layer']],pya.Point(*p['point']));assert n
        if p['net'] in nets:assert nets[p['net']].cluster_id==n.cluster_id
        nets[p['net']]=n
    assert len(nets)==55
    proposals=[('vdd','M4',[286550,146630,287450,225000]),
               ('vdd','M4',[286400,146630,287600,225000]),
               ('vdd','M4',[286100,146630,287900,225000]),
               ('vdd','M5',[287000,145630,418800,147630]),
               ('vss','M5',[417810,15060,419760,143400])]
    rows=[]
    for net,layer,box in proposals:
        cuts=[k for k,ends in CUTS.items() if layer in ends]
        own={k:ltn.shapes_of_net(nets[net],layers[k],True) for k in [layer]+cuts}
        other={k:region(top,ly.layer(*PAIRS[k]))-own[k] for k in own}
        shape=pya.Region(pya.Box(*box));mc=shape.sized(250)&other[layer]
        vc={k:shape&other[k] for k in cuts}
        def boxes(r):return [[p.bbox().left,p.bbox().bottom,p.bbox().right,p.bbox().top] for p in r.each()]
        attached=not(shape&own[layer]).is_empty()
        rows.append(dict(layer=layer,net=net,bbox_dbu=box,
            passed=mc.is_empty() and all(r.is_empty() for r in vc.values()) and attached,
            foreign_metal_clearance_nm=250,foreign_metal_conflicts=boxes(mc),
            foreign_cut_capture={k:boxes(r) for k,r in vc.items()},same_net_attachment=attached))
    assert all(sha(Path(p))==h for p,h in inputs.items())
    result=dict(status='completed finite clearance screen; individual pass/fail retained',inputs=inputs,
        candidates=rows,wall_s=time.monotonic()-start,native_GDS_changed=False,
        candidate_generation='not run',stock_DRC_LVS='not run',new_nonlinear_OP='not run',
        limitation='Same-net geometry and clearance only; seven star interfaces require candidate audit.')
    dump(a.output/'analysis.json',result);print(json.dumps(result,indent=2))


if __name__=='__main__':main()
