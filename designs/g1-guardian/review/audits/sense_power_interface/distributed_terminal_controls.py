#!/usr/bin/env python3
"""Exact algebra controls and an unrun SPICE coupon for a diagnostic port adapter."""
import argparse
from fractions import Fraction as F
import hashlib
import itertools
import json
from pathlib import Path
import re


def weights(values):
    values=tuple(F(v)for v in values)
    assert values and all(v>=0 for v in values)and sum(values)==1
    return values


def adapter_voltage(voltages,allocation):
    allocation=weights(allocation);assert len(voltages)==len(allocation)
    return sum(F(v)*w for v,w in zip(voltages,allocation))


def fixed_current_bounds(transfer_rows,currents):
    """Linear positive-mesh response only; NOT a nonlinear circuit-performance bound."""
    assert len(transfer_rows)==len(currents)
    lo=hi=F(0)
    for row,current in zip(transfer_rows,currents):
        choices=[F(current)*F(z)for z in row];assert choices
        lo+=min(choices);hi+=max(choices)
    return lo,hi


def render_adapter(name,allocation):
    assert re.fullmatch('[a-z][a-z0-9_]*',name)
    allocation=weights(allocation);ports=['p'+str(i)for i in range(len(allocation))]
    coefficients=['{%d/%d}'%(w.numerator,w.denominator)for w in allocation]
    rows=['* CONDITIONAL ideal distributed adapter; syntax/runtime NOT RUN',
          '.subckt '+name+' m '+' '.join(ports),
          'Eaverage av 0 POLY('+str(len(ports))+') '+' '.join(p+' 0'for p in ports)+' 0 '+' '.join(coefficients),
          'Vmeasure av m 0']
    rows+=['Fcontact%d %s 0 Vmeasure %s'%(i,p,w)for i,(p,w)in enumerate(zip(ports,coefficients))]
    rows+=['.ends '+name]
    return '\n'.join(rows)+'\n'


def controls():
    records=[]
    for allocation in((F(1,2),F(1,2)),(F(1,3),F(2,3)),(F(1),F(0)),(F(0),F(1))):
        for voltage in((F(2),F(5)),(F(-3),F(7)),(F(11,10),F(11,10))):
            for current in(F(-2,1000),F(0),F(3,1000)):
                u=adapter_voltage(voltage,allocation)
                injections=[w*current for w in allocation]
                assert sum(injections)==current
                assert sum(v*i for v,i in zip(voltage,injections))==u*current
                if voltage[0]==voltage[1]:assert u==voltage[0]
                records.append(dict(weights=[str(w)for w in allocation],voltage=[str(v)for v in voltage],
                    current=str(current),model_voltage=str(u),signed_KCL='exact',power='exact'))
    # Positive-resistor ladder: grounded root --2ohm--a--3ohm--b.
    # Observation v(b) has transfer impedances [2,5] for injection at a/b.
    coeff=((F(2),F(5)),(F(2),F(5)));currents=(F(2),F(-1))
    bound=fixed_current_bounds(coeff,currents);assert bound==(F(-1),F(8))
    samples=[]
    for x,y in itertools.product(range(11),repeat=2):
        allocations=((F(x,10),1-F(x,10)),(F(y,10),1-F(y,10)))
        v=sum(i*sum(w*z for w,z in zip(ws,row))for i,ws,row in zip(currents,allocations,coeff))
        assert bound[0]<=v<=bound[1];samples.append(v)
    assert min(samples)==bound[0]and max(samples)==bound[1]
    # Sign inversion in F-source mapping must fail both current and power.
    w=weights((F(1,3),F(2,3)));v=(F(2),F(5));i=F(3)
    assert sum(-z*i for z in w)!=i
    assert sum(a*(-z*i)for a,z in zip(v,w))!=adapter_voltage(v,w)*i
    rejected=0
    for bad in((F(-1),F(2)),(F(1,2),F(1,3)),()):
        try:weights(bad)
        except AssertionError:rejected+=1
    assert rejected==3
    # Shared physical strip contributions add, never instantiate another MOS.
    assert F(2)*F(1,4)+F(-1)*F(1,2)==0
    return dict(status='passed exact rational algebra only',cases=records,
        fixed_current_bound=dict(lower=str(bound[0]),upper=str(bound[1]),interior_samples=len(samples)),
        negative_controls='passed wrong F sign, negative/nonunit/empty weights rejected',
        shared_strip_signed_current_superposition='passed',
        not_run=['ngspice E/F syntax','DC/AC/transient coupon','Model parameter/wave zeroR parity',
                 'Nonlinear current redistribution or performance bounds','Physical applicability'])


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists()
    result=controls();result['script_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    result['unrun_coupon']=render_adapter('g1_distributed_diagnostic',(F(1,3),F(2,3)))
    result['canonical_source_modified']=False
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items()if k!='cases'},indent=2))


if __name__=='__main__':main()
