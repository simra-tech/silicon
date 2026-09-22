#!/usr/bin/env python3
"""Bind the current compiled VVP to exact replay of the passed bridge waveform."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time

SIM=Path(__file__).resolve().parent
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main(run_id, original_control=None):
    out=SIM/'qualification'/run_id
    frozen=json.loads((out/'frozen_inputs.json').read_text())
    passed=json.loads((out/'digital_check.json').read_text())
    assert passed['status']=='passed' and all(passed['checks'].values())
    assert all(sha(out/n)==v for n,v in frozen.items())
    vvp=out/'g1_hys_diagnostic.vvp'
    bound={n:sha(out/n) for n in ['g1_hys_diagnostic.vvp','digital.dat','digital.log','digital_check.json','digital_samples.json',
                                 'g1_hys_diagnostic.v','g1_trip_timer.v','g1_sync2.v','compile.log','digital.cir']}
    deck=(out/'digital.cir').read_text()
    assert deck.count('/digital.dat ')==1
    new=deck.replace('/digital.dat ','/digital_attested.dat ')
    with (out/'digital_attested.cir').open('x') as f:f.write(new)
    env=dict(os.environ)
    env['LD_LIBRARY_PATH']='/foss/tools/iverilog/lib'+(':'+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '')
    cmd=['timeout','20','ngspice','-b','qualification/'+run_id+'/digital_attested.cir']
    start=time.monotonic()
    with (out/'digital_attested.log').open('x') as f:
        p=subprocess.run(cmd,cwd=str(SIM),stdout=f,stderr=subprocess.STDOUT,env=env)
    wave=out/'digital_attested.dat'
    checks=dict(returncode_zero=p.returncode==0,passed_original_bound=all(sha(out/n)==v for n,v in bound.items()),
        inputs_unchanged=all(sha(out/n)==v for n,v in frozen.items()),
        waveform_byte_identical=wave.exists() and sha(wave)==bound['digital.dat'],
        completion_marker='HYS_DIGITAL_COMPLETE' in (out/'digital_attested.log').read_text())
    original_bound=None
    if original_control:
        previous=SIM/'qualification'/original_control
        previous_check=json.loads((previous/'digital_check.json').read_text())
        assert previous_check['status']=='passed' and all(previous_check['checks'].values())
        original_bound={n:sha(previous/n) for n in ['digital.dat','digital_check.json','digital.cir']}
        checks['original_control_waveform_byte_identical']=wave.exists() and sha(wave)==original_bound['digital.dat']
    result=dict(status='passed' if all(checks.values()) else 'failed',checks=checks,command=cmd,wall_s=time.monotonic()-start,
        prior_passed_artifacts=bound,artifacts={n:sha(out/n) for n in ['digital_attested.cir','digital_attested.log']+(['digital_attested.dat'] if wave.exists() else [])},
        prefix_checker_sha256=sha(SIM/'check_hys_prefix.py'),attester_sha256=sha(Path(__file__)),
        direct_checker_sha256=sha(SIM/'check_hys_direct_prefix.py') if original_control else None,
        original_control=original_control,original_control_artifacts=original_bound,
        meaning='Current VVP hash reproduced the exact previously passed digital waveform; original files preserved.')
    with (out/'digital_attestation.json').open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    return 0 if result['status']=='passed' else 1

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run-id',required=True);p.add_argument('--original-control');a=p.parse_args()
    assert re.fullmatch('[a-z0-9][a-z0-9_-]+',a.run_id)
    assert not a.original_control or re.fullmatch('[a-z0-9][a-z0-9_-]+',a.original_control)
    raise SystemExit(main(a.run_id,a.original_control))
