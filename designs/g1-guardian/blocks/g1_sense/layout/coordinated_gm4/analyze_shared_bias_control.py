#!/usr/bin/env python3
"""Analyze frozen repeated-bias and changed-body controls without charge inference."""
import argparse
import hashlib
import json
import math
import re
from pathlib import Path


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True)
    a=p.parse_args();out=a.run/'analysis.json';assert not out.exists()
    contract=json.loads((a.run/'contract.json').read_text());state=json.loads((a.run/'run.json').read_text())
    result=dict(status='failed',contract_sha256=hashlib.sha256((a.run/'contract.json').read_bytes()).hexdigest(),
                script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),cases=[])
    try:
        assert state['status']=='completed' and state['returncode']==0
        log=(a.run/'run.log').read_text()
        assert not re.search(r'^Error|no such device|no such vector|no such parameter|analysis aborted',log,re.M)
        for label in contract['cases']:
            section,=re.findall('^BIAS_BEGIN_'+label+r'\n(.*?)^BIAS_END_'+label+'$',log,re.M|re.S)
            fields={m[1]:float(m[2]) for m in re.finditer(r'^@n\.xm1\.nsg13_hv_pmos\[(\w+)\]\s*=\s*(\S+)',section,re.M)}
            assert len(fields)==21 and all(math.isfinite(v) for v in fields.values())
            raw=(a.run/(label+'.raw')).read_text();head,tail=raw.split('Values:\n')
            variables=[r.split() for r in head.split('Variables:\n')[1].splitlines() if r.strip()]
            vals=[r.split() for r in tail.splitlines() if r.strip()]
            assert len(variables)==len(vals) and 'No. Points: 1\n' in head
            v={r[1]:float(vals[i][-1]) for i,r in enumerate(variables)}
            assert all(math.isfinite(x) for x in v.values())
            rkeys=('rg','rse','rde','rbulk','rjuns','rjund','rwell')
            assert [fields['lp_'+k]==0 for k in rkeys]==[False,True,True,False,False,False,False]
            # Already controlled descriptor permutation: physical BS=raw#bp, BP=raw#si.
            prefix='v(n.xm1.nsg13_hv_pmos#'
            jbias=v['v(tail)']-v[prefix+'bp)']
            channel={'vsb':v[prefix+'si)']-v['v(tail)'],'vds':v['v(tail)']-v['v(fn)'],
                     'vgs':v['v(tail)']-v[prefix+'gp)']}
            assert fields['ctype']==-1 and fields['sdint']==1
            errors={k:abs(fields[k]-x) for k,x in channel.items()}
            assert max(errors.values())<1e-9,errors
            result['cases'].append(dict(label=label,parameters=fields,junction_bias_V=jbias,
                                        channel_identity_errors_V=errors,raw_sha256=hashlib.sha256(raw.encode()).hexdigest()))
        x,y,z=result['cases']
        assert all(x['parameters'][k]==y['parameters'][k]==z['parameters'][k] for k in ('w','l','delvto','factuo'))
        eqv=abs(x['junction_bias_V']-y['junction_bias_V'])
        eqc=abs(x['parameters']['cjs']-y['parameters']['cjs'])/abs(x['parameters']['cjs'])
        nv=abs(x['junction_bias_V']-z['junction_bias_V'])
        nc=abs(x['parameters']['cjs']-z['parameters']['cjs'])/abs(x['parameters']['cjs'])
        result.update(equal_bias_delta_V=eqv,equal_cap_relative_delta=eqc,
                      negative_bias_delta_V=nv,negative_cap_relative_delta=nc)
        assert eqv<=contract['equal_bias_gate']['junction_voltage_abs_delta_V']
        assert eqc<=contract['equal_bias_gate']['junction_capacitance_relative_delta']
        assert nv>=contract['negative_bias_gate']['junction_voltage_abs_delta_V_min']
        assert nc>=contract['negative_bias_gate']['junction_capacitance_relative_delta_min']
        result['status']='passed conditional bias-dependence and node-mapping controls; shared applicability not qualified'
    except Exception as e:result['error']=repr(e)
    result.update(charge='not exposed; not run',source_adoption='not run',
                  scope='One unchanged canonical-geometry PMOS under ideal external biases; separate random realization, not full SENSE equivalence')
    out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
    assert result['status'].startswith('passed'),result.get('error')


if __name__=='__main__':main()
