#!/usr/bin/env python3
"""One upper VDD M5 bypass with explicitly checked redundant Via4 landings."""
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
    prior=bulk/'bgr-supply-screen-20260923-r1/analysis.json'
    assert sha(gds)=='1f32630e487f70979150943e432f9ecdb68bbd35873fa94e1c0bce2b670df524'
    old=json.loads(prior.read_text());assert [r['passed'] for r in old['candidates']]==[False,False,False,True,True]
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
    ledger=[dict(net=r['net'],layer=r['layer'],bbox_dbu=r['bbox_dbu']) for r in old['candidates'][3:]]
    ledger.append(dict(net='vdd',layer='M5',bbox_dbu=[286000,171660,288000,225780]))
    for yc in (172440,225000):
        ledger.append(dict(net='vdd',layer='M4',bbox_dbu=[286640,yc-780,287360,yc+780]))
        for xc in (286790,287210):
            for dy in (-630,-210,210,630):
                ledger.append(dict(net='vdd',layer='Via4',bbox_dbu=[xc-95,yc+dy-95,xc+95,yc+dy+95]))
    native={k:region(top,ly.layer(*v)) for k,v in PAIRS.items()}
    owners={(n,k):ltn.shapes_of_net(nets[n],layers[k],True) for n in ('vdd','vss') for k in PAIRS}
    added={}
    for r in ledger:added.setdefault((r['net'],r['layer']),pya.Region()).insert(pya.Box(*r['bbox_dbu']))
    def boxes(reg):return [[p.bbox().left,p.bbox().bottom,p.bbox().right,p.bbox().top] for p in reg.each()]
    checks=[]
    for r in ledger:
        net,layer=r['net'],r['layer'];shape=pya.Region(pya.Box(*r['bbox_dbu']))
        foreign=native[layer]-owners[(net,layer)]
        for (n,k),reg in added.items():
            if n!=net and k==layer:foreign+=reg
        spacing=shape.sized(250)&foreign
        captured={};missing={};cut_overlap=[]
        if layer in CUTS:
            spacing=pya.Region()
            for end in CUTS[layer]:
                full=owners[(net,end)]+added.get((net,end),pya.Region())
                missing[end]=boxes(shape.sized(55)-full)
            for p in native[layer].interacting(shape).each():
                if not(pya.Region(p)^shape).is_empty():cut_overlap+=boxes(pya.Region(p)&shape)
        else:
            for cut,ends in CUTS.items():
                if layer in ends:captured[cut]=boxes(shape&(native[cut]-owners[(net,cut)]))
        checks.append(dict(r,passed=spacing.is_empty() and not any(captured.values()) and not any(missing.values()) and not cut_overlap,
            foreign_spacing=boxes(spacing),foreign_cut_capture=captured,missing_enclosure=missing,partial_old_cut_overlap=cut_overlap))
    assert all(sha(Path(p))==h for p,h in inputs.items())
    passed=all(r['passed'] for r in checks)
    result=dict(status='passed geometric screen' if passed else 'failed geometric screen',inputs=inputs,ledger=ledger,
        checks=checks,mutual_foreign_clearance=[],wall_s=time.monotonic()-start,
        via4_cuts=16,native_GDS_changed=False,source_count=1036,source_nets=55,
        candidate_generation='not run',stock_DRC_LVS='not run',new_nonlinear_OP='not run')
    dump(a.output/'analysis.json',result);print(json.dumps(result,indent=2))


if __name__=='__main__':main()
