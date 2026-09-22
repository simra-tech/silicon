#!/usr/bin/env python3
"""Compare complete native DeltaQ traces across the two prospectively frozen steps."""
import argparse
import bisect
import hashlib
import json
from pathlib import Path
from analyze_junction_charge_control import raw,cumulative


def trace(path):
    d=raw(path/'transient.raw');bs=d['v(n.xm1.nsg13_hv_pmos#bp)'];bi=d['v(n.xm1.nsg13_hv_pmos#di)']
    key=lambda k:'@n.xm1.nsg13_hv_pmos['+k+']'
    i=[-64*(b-v)/r-b/1e12+j for b,v,r,j in zip(bs,bi,d[key('lp_rjuns')],d[key('ijs')])]
    return d['time'],cumulative(i,d['time'])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('coarse','fine','zero','output'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();assert not a.output.exists()
    summaries=[json.loads((r/'analysis_r1.json').read_text()) for r in (a.zero,a.coarse,a.fine)]
    assert all(r['status'].startswith('passed') for r in summaries)
    assert summaries[0]['model_parameters']==summaries[1]['model_parameters']==summaries[2]['model_parameters']
    assert summaries[1]['contract']['files']==summaries[2]['contract']['files']
    assert summaries[1]['contract']['maxstep_ns']==.1 and summaries[2]['contract']['maxstep_ns']==.05
    tc,qc=trace(a.coarse);tf,qf=trace(a.fine);errors=[]
    for t,q in zip(tc,qc):
        j=bisect.bisect_left(tf,t)
        if j==0:y=qf[0]
        elif j==len(tf):y=qf[-1]
        else:y=qf[j-1]+(qf[j]-qf[j-1])*(t-tf[j-1])/(tf[j]-tf[j-1])
        errors.append(abs(q-y))
    peak=max(abs(q) for q in qf);budget=max(1e-20,.001*peak)
    result=dict(status='passed' if max(errors)<=budget else 'failed',
                maximum_trace_delta_C=max(errors),fine_peak_abs_C=peak,relative_trace_delta=max(errors)/peak,
                prospective_budget_C=budget,raw_grid_equality='not claimed; fine trace linearly interpolated onto coarse times',
                source_model_parameter_binding='passed exact',zero_control_peak_C=summaries[0]['max_charge_abs_C'],
                inputs={r.name:hashlib.sha256((r/'analysis_r1.json').read_bytes()).hexdigest() for r in (a.zero,a.coarse,a.fine)},
                script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                scope='Method control only, single ideal-biased canonical PMOS; no absoluteQ/shared-layout equivalence/full-SENSE applicability')
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));assert result['status']=='passed'


if __name__=='__main__':main()
