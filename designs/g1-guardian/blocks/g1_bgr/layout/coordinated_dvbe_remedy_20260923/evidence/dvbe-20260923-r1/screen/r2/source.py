#!/usr/bin/env python3
"""One revised stepped DVBE shape, avoiding the measured upper fanout."""
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
    a=ap.parse_args();assert not a.output.exists() and set(os.sched_getaffinity(0))=={1}
    bulk=Path(os.environ['G1_RESULTS_ROOT'])
    gds=bulk/'bgr-assembly-signalbypass-20260922-r1/bank.gds'
    route=bulk/'bgr-assembly-20260922-r5/routing.json'
    prior=bulk/'bgr-dvbe-screen-20260923-r1/analysis.json'
    assert sha(gds)=='6d86b9d40333958cb8186d486d29db1532a816e302871e11d07e0f1d999cfc04'
    prior_report=json.loads(prior.read_text())
    assert [r['passed'] for r in prior_report['candidates']]==[True,False,False,False]
    inputs={str(q):sha(q) for q in (gds,route,prior,Path(__file__),HERE.parent/'coordinated_full_closure/build_assembly.py')}
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
    own={k:ltn.shapes_of_net(nets['dvbe'],layers[k],True) for k in ('M5','Via4')}
    other={k:region(top,ly.layer(*PAIRS[k]))-own[k] for k in own}
    rows=[]
    for box in ([201000,18670,205000,128000],[202700,127700,203300,137050]):
        shape=pya.Region(pya.Box(*box));mc=shape.sized(250)&other['M5'];vc=shape&other['Via4']
        def boxes(r):return [[p.bbox().left,p.bbox().bottom,p.bbox().right,p.bbox().top] for p in r.each()]
        attached=not(shape&own['M5']).is_empty()
        rows.append(dict(layer='M5',net='dvbe',bbox_dbu=box,role='stepped_dvbe_parallel_metal',
                         passed=mc.is_empty() and vc.is_empty() and attached,
                         foreign_M5_clearance_nm=250,foreign_M5_conflicts=boxes(mc),
                         foreign_Via4_capture=boxes(vc),same_net_attachment=attached))
    assert all(sha(Path(p))==h for p,h in inputs.items())
    result=dict(status='passed geometric screen' if all(r['passed'] for r in rows) else 'failed geometric screen',
                inputs=inputs,ledger=rows,checks=rows,mutual_foreign_clearance=[],
                source_nets=55,wall_s=time.monotonic()-start,candidate_GDS='not run',
                stock_DRC_LVS='not run',positive_mesh_OP='not run',adoption='not run')
    dump(a.output/'analysis.json',result);print(json.dumps(result,indent=2))


if __name__=='__main__':main()
