#!/usr/bin/env python3
"""Signed native BS charge-change observation with fail-closed KCL and integral controls."""
import argparse
import hashlib
import json
import math
import re
from pathlib import Path


def raw(path):
    text=path.read_text();head,tail=text.split('Values:\n')
    n=int(re.search(r'No. Points: (\d+)',head)[1])
    fields=[r.split()[1] for r in head.split('Variables:\n')[1].splitlines() if r.strip()]
    values=[r.split() for r in tail.splitlines() if r.strip()];assert len(values)==n*len(fields)
    norm=lambda s:s[2:-1] if s.startswith(('v(@','i(@')) else s
    data={norm(name):[float(values[i*len(fields)+j][-1]) for i in range(n)] for j,name in enumerate(fields)}
    assert len(data)==len(fields) and all(math.isfinite(x) for v in data.values() for x in v)
    return data


def cumulative(y,x):
    result=[0.]
    for i in range(1,len(x)):result.append(result[-1]+(y[i]+y[i-1])*.5*(x[i]-x[i-1]))
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    contract=json.loads((a.run/'contract.json').read_text());state=json.loads((a.run/'run.json').read_text())
    result=dict(status='failed',contract=contract,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    try:
        assert state['status']=='completed' and state['returncode']==0
        log=(a.run/'run.log').read_text();assert 'CHARGE_CONTROL_COMPLETE' in log
        assert not re.search(r'^Error|no such|Timestep too small|analysis aborted',log,re.M)
        initial=raw(a.run/'initial.raw');d=raw(a.run/'transient.raw');t=d['time'];assert t[0]==0 and abs(t[-1]-1e-7)<1e-18
        assert all(t[i]>t[i-1] for i in range(1,len(t)))
        field=lambda k:'@n.xm1.nsg13_hv_pmos['+k+']'
        for k in ('w','l','delvto','factuo','ctype','sdint','lp_rjuns','lp_rg','lp_rse','lp_rde','lp_rbulk','lp_rjund','lp_rwell'):
            assert len(set(d[field(k)]))==1 and d[field(k)][0]==initial[field(k)][0],k
        assert d[field('ctype')][0]==-1 and d[field('sdint')][0]==1
        assert [d[field('lp_'+k)][0]==0 for k in ('rg','rse','rde','rbulk','rjuns','rjund','rwell')]==[False,True,True,False,False,False,False]
        def observe(data):
            bs=data['v(n.xm1.nsg13_hv_pmos#bp)'];bi=data['v(n.xm1.nsg13_hv_pmos#di)']
            resistance=data[field('lp_rjuns')];ijs=data[field('ijs')]
            current=[-64*(b-i)/r-b/1e12+j for b,i,r,j in zip(bs,bi,resistance,ijs)]
            return current,[s-b for s,b in zip(data['v(tail)'],bs)]
        i0,v0=observe(initial);current,vjun=observe(d);cap=d[field('cjs')]
        assert all(c>0 for c in cap)
        q=cumulative(current,t);cq=cumulative([-c for c in cap],vjun)
        peak=max(abs(x) for x in q);deviation=max(abs(x-y) for x,y in zip(q,cq))
        g=contract['declared_gates'];budget=max(g['charge_absolute_floor_C'],g['integral_CdV_relative']*peak)
        result.update(rows=len(t),initial_KCL_A=i0[0],max_charge_abs_C=peak,return_charge_C=q[-1],
                      independent_integral_max_delta_C=deviation,declared_charge_budget_C=budget,
                      end_bias_delta_V=vjun[-1]-vjun[0],dynamic_cjs_range_F=[min(cap),max(cap)],
                      dynamic_ijs_range_A=[min(d[field('ijs')]),max(d[field('ijs')])],
                      model_parameters={k:d[field(k)][0] for k in ('w','l','delvto','factuo')},
                      raw_sha256=hashlib.sha256((a.run/'transient.raw').read_bytes()).hexdigest())
        assert abs(i0[0])<=g['static_BS_KCL_abs_A']
        assert abs(q[-1])<=max(g['charge_absolute_floor_C'],g['return_cycle_relative']*peak)
        assert deviation<=budget
        if contract['amplitude_V']==0:assert peak<=g['zero_charge_abs_C']
        else:
            assert max(cap)>min(cap)*1.01 and max(vjun)-min(vjun)>.29
            assert max(d[field('ijs')])>min(d[field('ijs')])
        result['status']='passed single-run native DeltaQ observation gates; timestep comparison pending'
    except Exception as e:result['error']=repr(e)
    result['scope']='Signed native BS-side charge difference on one unchanged ideal-biased PMOS; no absoluteQ/shared-layout/whole-SENSE qualification'
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
    assert result['status'].startswith('passed'),result.get('error')


if __name__=='__main__':main()
