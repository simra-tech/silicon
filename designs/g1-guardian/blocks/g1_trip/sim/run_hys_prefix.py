#!/usr/bin/env python3
"""One explicitly reviewed .9-us HYS prefix, fixed300-second watchdog.

Use only after coordinator authorization and a fresh resource gate. No retry,
full-run or tolerance-changing options exist.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

SIM=Path(__file__).resolve().parent
sys.path.insert(0,str(SIM.parents[1]/'g1_top/sim'))
from run_bounded import run_bounded
from check_hys_prefix import check

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main(run_id):
    out=SIM/'qualification'/run_id
    assert not (out/'prefix_launch.json').exists(), 'Fresh launch required; no retries'
    frozen=json.loads((out/'frozen_inputs.json').read_text())
    attestation=json.loads((out/'digital_attestation.json').read_text())
    runtime=json.loads((out/'runtime.json').read_text())
    assert attestation['status']=='passed' and all(attestation['checks'].values())
    assert all(sha(out/n)==v for n,v in frozen.items())
    assert all(sha(out/n)==v for n,v in attestation['prior_passed_artifacts'].items())
    assert sha(SIM/'check_hys_prefix.py')==attestation['prefix_checker_sha256']
    pd=Path('/foss/pdks/ihp-sg13g2')
    assert (pd/'COMMIT').read_text().strip()==runtime['pdk_commit']
    assert subprocess.check_output(['ngspice','--version'],universal_newlines=True)==runtime['ngspice_version']
    assert all(sha(pd/n)==v for n,v in dict(runtime['model_sha256'],**runtime['osdi_sha256']).items())
    vvp=out/'g1_hys_diagnostic.vvp'
    command=['ngspice','-b','qualification/'+run_id+'/prefix.cir']
    metadata=dict(command=command,watchdog_s=300,endpoint_us=.9,
        source_input_sha256=frozen,compiled_vvp_sha256=sha(vvp),
        digital_attestation_sha256=sha(out/'digital_attestation.json'),
        passed_control_artifacts=attestation['prior_passed_artifacts'],
        checker_sha256=sha(SIM/'check_hys_prefix.py'),launcher_sha256=sha(Path(__file__)),
        simulation_errors_sha256=sha(SIM.parents[1]/'g1_top/sim/simulation_errors.py'),
        resource_policy='One CPU0,4 GiB reservation only, fresh owner-coordinated50% resource gate required')
    with (out/'prefix_launch.json').open('x') as f:f.write(json.dumps(metadata,indent=2)+'\n')
    os.environ['LD_LIBRARY_PATH']='/foss/tools/iverilog/lib'+(':'+os.environ['LD_LIBRARY_PATH'] if os.environ.get('LD_LIBRARY_PATH') else '')
    with (out/'prefix.log').open('x') as log:
        state=run_bounded(command,log,out/'prefix_run.json',300,cwd=SIM,metadata=metadata,interval_s=1)
    result=check(out,out/'prefix.log',state.get('returncode'))
    result['runtime_state']=state
    result['compiled_vvp_unchanged']=sha(vvp)==metadata['compiled_vvp_sha256']
    if not result['compiled_vvp_unchanged']:result['status']='failed'
    with (out/'prefix_check.json').open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    return 0 if result['status']=='passed' else 1

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run-id',required=True);a=p.parse_args()
    assert re.fullmatch('[a-z0-9][a-z0-9_-]+',a.run_id)
    raise SystemExit(main(a.run_id))
