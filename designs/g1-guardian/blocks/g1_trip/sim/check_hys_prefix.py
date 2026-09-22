#!/usr/bin/env python3
"""Read-only .9-us HYS prefix gate. Does not launch or extend simulations."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import numpy as np

SIM=Path(__file__).resolve().parent
sys.path.insert(0,str(SIM.parents[1]/'g1_top/sim'))
from simulation_errors import solver_failure

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def check(out, log_path, returncode):
    manifest=json.loads((out/'frozen_inputs.json').read_text())
    reference=json.loads((out/'reference_summary.json').read_text())[0]
    ports=json.loads((out/'port_map.json').read_text())
    digital=json.loads((out/'digital_check.json').read_text())
    attestation=json.loads((out/'digital_attestation.json').read_text())
    log=log_path.read_text()
    checks=dict(digital_control_passed=digital['status']=='passed',
        compiled_control_attested=attestation['status']=='passed' and all(attestation['checks'].values()),
        attested_control_unchanged=all(sha(out/n)==v for n,v in attestation['prior_passed_artifacts'].items()),
        checker_matches_attested_hash=sha(Path(__file__))==attestation['prefix_checker_sha256'],
        simulator_returncode_zero=returncode==0,solver_log_clean=not solver_failure(log),
        analog_completion_marker='HYS_ANALOG_COMPLETE' in log,
        frozen_inputs_unchanged=all(sha(out/n)==v for n,v in manifest.items()))
    observed={}
    for name,start,stop in [('before','HYS_PARAMETERS_BEFORE','HYS_PARAMETERS_AFTER'),
                            ('after','HYS_PARAMETERS_AFTER','HYS_ANALOG_COMPLETE')]:
        if log.count(start)!=1 or log.count(stop)!=1:
            observed[name]=[]
        else:
            section=log.split(start,1)[1].split(stop,1)[0]
            observed[name]=[list(x) for x in re.findall(r'^(@[^=\n]+) = (\S+)',section,re.M)]
        checks['all27_parameters_exact_'+name]=observed[name]==reference['fingerprints'] and len(observed[name])==27
    detail={}
    wave=out/'prefix.dat'
    try:
        header=wave.open().readline().lower().split()
        names=ports['inputs']+ports['outputs']+['shp','vref','iptat','vref_buf','vped','isense','xt.icmp','xt.vth_soft','xt.vth_hard']
        assert header==['time']+['v('+n+')' for n in names]
        data=np.loadtxt(str(wave),skiprows=1)
        t=data[:,0]; values=dict(zip(names,data[:,1:].T))
        assert np.isfinite(data).all() and np.all(np.diff(t)>0) and abs(t[-1]-.9e-6)<1e-15
        checks['finite_exact_endpoint']=True
        bit=lambda n,at: np.interp(at,t,values[n])>.6
        code=lambda p,w,at: sum((1<<i)*int(bit(p+str(i),at)) for i in range(w))
        samples=[]
        for i in range(9):
            at=(25.1+100*i)*1e-9
            samples.append(dict(t_s=at,reset=bool(bit('rst_n',at)),clock=bool(bit('clk',at)),
                count=code('count',24,at),soft=code('s',8,at),hard=code('h',8,at),
                trip=bool(bit('trip',at)),mask=bool(bit('soft_mask',at))))
        checks['reset_release_phase']=[s['reset'] for s in samples[:4]]==[False,False,True,True]
        checks['divider_5MHz_phase']=all(s['clock']==(i%2==1) for i,s in enumerate(samples) if i>=2)
        late=[s for s in samples if s['t_s']>=.6e-6]
        checks['quiet_static_codes']=all(s['soft']==128 and s['hard']==240 for s in late)
        checks['sampled_digital_levels_valid']=all(
            (-.1 <= np.interp(s['t_s'],t,values[n]) <= .1) or
            (1.1 <= np.interp(s['t_s'],t,values[n]) <= 1.3)
            for s in samples[3:] for n in ports['outputs'])
        checks['quiet_counter_mask_trip']=all(s['count']==0 and not s['mask'] and not s['trip'] for s in late)
        checks['quiet_raw_and_synced_low']=all(not bit(n,at) for n in ['cmp_soft','cmp_hard','sync_soft','sync_hard'] for at in [.775e-6,.875e-6])
        detail=dict(rows=len(t),endpoint_s=float(t[-1]),samples=samples,
            final_nodes_V={n:float(values[n][-1]) for n in ['vref','vref_buf','isense','xt.icmp','xt.vth_soft','xt.vth_hard']},waveform_sha256=sha(wave))
    except (OSError,ValueError,AssertionError,IndexError) as exc:
        checks['finite_exact_endpoint']=False
        detail['wave_error']=type(exc).__name__+': '+str(exc)
    return dict(status='passed' if all(checks.values()) else 'failed',checks=checks,
        parameters=observed,detail=detail,analog_feedback_coverage='not run',
        full_3us_feedback='not run',two_lsb='not run',offset_carry='not run',
        adverse_pvt_and_route_skew='not run',serial_or_fast_gate_qualification='not applicable to this isolated prefix',
        interpretation='Prefix gate only; no hysteresis event occurs before .9 us. No analog convergence or full-loop qualification.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run-id',required=True);p.add_argument('--log',type=Path,required=True)
    p.add_argument('--returncode',type=int,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert re.fullmatch('[a-z0-9][a-z0-9_-]+',a.run_id)
    result=check(SIM/'qualification'/a.run_id,a.log,a.returncode)
    with a.output.open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2));raise SystemExit(0 if result['status']=='passed' else 1)
