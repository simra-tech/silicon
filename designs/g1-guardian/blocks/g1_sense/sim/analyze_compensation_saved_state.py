#!/usr/bin/env python3
"""Saved-evidence comparison only: do not infer an unobserved latch state."""
import argparse
import gzip
import json
from pathlib import Path
from run_loaded_noise_audit import sha


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--original',type=Path,required=True)
    p.add_argument('--candidate',type=Path,required=True)
    p.add_argument('--original-wave',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert not a.output.exists()
    records={};bindings={}
    for label,parent in [('original',a.original),('candidate',a.candidate)]:
        for mode in ['differential','tian_voltage']:
            leaf=parent/mode;record=json.loads((leaf/'summary.json').read_text())
            assert record['runtime']['status']=='completed' and record['runtime']['returncode']==0
            name=label+'_'+mode
            records[name]=dict(status=record['status'],quiet_op_V=record['quiet_op_V'],operating_point=record['operating_point'])
            bindings[name]={n:sha(leaf/n) for n in ['summary.json','contract.json','probe.cir','run.log']}
    with gzip.open(a.original_wave,'rt') as stream:
        names=stream.readline().split();values=list(map(float,stream.readline().split()))
    assert len(names)==len(values) and names[0]=='time' and values[0]==0
    first=dict(zip(names,values))
    assert all(first[n]==v for n,v in records['original_differential']['quiet_op_V'].items())
    assert first['v(clk)']==0 and 0<first['v(cmp_soft)']<1.32
    result=dict(status='completed saved-state comparison',records=records,bindings=bindings,
        original_wave_sha256=sha(a.original_wave),original_t0=first,
        original_t0_nine_OP_exact=True,
        original_zero_probe_core_current_delta_A=records['original_tian_voltage']['operating_point']['i(vdd)']-records['original_differential']['operating_point']['i(vdd)'],
        candidate_vs_original_probe_core_current_delta_A=records['candidate_differential']['operating_point']['i(vdd)']-records['original_tian_voltage']['operating_point']['i(vdd)'],
        candidate_probe_own_core_current_delta_A=records['candidate_tian_voltage']['operating_point']['i(vdd)']-records['candidate_differential']['operating_point']['i(vdd)'],
        interpretation='Low core-current solution also occurs in the original source after the nominally DC-transparent probe insertion. Original transient t0 has a midrail soft output. This supports, but does not prove, a different comparator DC state/solution as cause. Candidate/probe comparator state vectors were not exported; exact latch-state correspondence is NOT RUN. No current-budget relief, convergence waiver or source inheritance.',
        new_simulation='not run')
    a.output.mkdir(parents=True)
    (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps({k:v for k,v in result.items() if k not in ['records','bindings','original_t0']},indent=2))


if __name__=='__main__':main()
