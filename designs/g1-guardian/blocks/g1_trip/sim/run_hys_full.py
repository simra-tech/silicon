#!/usr/bin/env python3
"""Freeze or run one explicitly reviewed3-us HYS mechanism leaf,900s maximum."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

SIM=Path(__file__).resolve().parent
ROOT=SIM.parents[4]
sys.path.insert(0,str(SIM.parents[1]/'g1_top/sim'))
from run_bounded import run_bounded
from check_hys_full import check

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,d):
    with p.open('x') as f:f.write(json.dumps(d,indent=2)+'\n')

def main(run_id,mode):
    out=SIM/'qualification'/run_id
    prep=json.loads((out/'preparation.json').read_text())
    ref=SIM/'qualification'/prep['reference']
    assert prep['endpoint_us']==3 and prep['watchdog_s']==900
    assert all(sha(ROOT/n)==v for n,v in prep['reference_inputs'].items())
    assert sha(out/'full.cir')==prep['deck_sha256']
    assert sha(SIM/'HYS_FULL_FEEDBACK_CONTRACT_20260922.md')==prep['contract_sha256']
    helpers=[SIM/'check_hys_full.py',Path(__file__).resolve(),SIM/'prepare_hys_full.py',
             SIM.parents[1]/'g1_top/sim/run_bounded.py',SIM.parents[1]/'g1_top/sim/simulation_errors.py']
    if mode=='freeze':
        dump(out/'launch_contract.json',dict(preparation_sha256=sha(out/'preparation.json'),
            helper_sha256={str(p.relative_to(ROOT)):sha(p) for p in helpers},
            compiled_vvp_sha256=sha(ref/'g1_hys_diagnostic.vvp'),
            digital_attestation_sha256=sha(ref/'digital_attestation.json'),
            contract_sha256=prep['contract_sha256'],watchdog_s=900,endpoint_us=3,
            resource_budget='One CPU0,4 GiB reservation only,0.15 GiB HOME forecast; fresh50% resource gate and coordinator authorization required',
            simulation_status='not run'))
        print('Launch contract frozen; simulation NOT RUN')
        return 0
    bound=json.loads((out/'launch_contract.json').read_text())
    assert not (out/'full_launch.json').exists(), 'Fresh one-shot leaf required'
    assert sha(out/'preparation.json')==bound['preparation_sha256']
    assert all(sha(ROOT/n)==v for n,v in bound['helper_sha256'].items())
    assert sha(ref/'g1_hys_diagnostic.vvp')==bound['compiled_vvp_sha256']
    assert sha(ref/'digital_attestation.json')==bound['digital_attestation_sha256']
    runtime=json.loads((ref/'runtime.json').read_text())
    pd=Path('/foss/pdks/ihp-sg13g2')
    assert (pd/'COMMIT').read_text().strip()==runtime['pdk_commit']
    assert subprocess.check_output(['ngspice','--version'],universal_newlines=True)==runtime['ngspice_version']
    assert all(sha(pd/n)==v for n,v in dict(runtime['model_sha256'],**runtime['osdi_sha256']).items())
    command=['ngspice','-b','qualification/'+run_id+'/full.cir']
    metadata=dict(command=command,watchdog_s=900,endpoint_us=3,source_bindings=prep['reference_inputs'],
        deck_sha256=sha(out/'full.cir'),launch_contract_sha256=sha(out/'launch_contract.json'),
        contract_sha256=prep['contract_sha256'],compiled_vvp_sha256=bound['compiled_vvp_sha256'],
        checker_sha256=sha(SIM/'check_hys_full.py'),parameter_contract='27 POST only; BEFORE not run',
        prefix_parity_window_s=[0,.85e-6],scope='Mechanism pilot, existing1us interface settling gate separately reported')
    dump(out/'full_launch.json',metadata)
    os.environ['LD_LIBRARY_PATH']='/foss/tools/iverilog/lib'+(':'+os.environ['LD_LIBRARY_PATH'] if os.environ.get('LD_LIBRARY_PATH') else '')
    with (out/'full.log').open('x') as log:
        state=run_bounded(command,log,out/'full_run.json',900,cwd=SIM,metadata=metadata,interval_s=1)
    result=check(out,out/'full.log',state.get('returncode'))
    result['runtime_state']=state
    result['compiled_vvp_unchanged']=sha(ref/'g1_hys_diagnostic.vvp')==bound['compiled_vvp_sha256']
    if not result['compiled_vvp_unchanged']:result['mechanism_status']='failed'
    dump(out/'full_check.json',result)
    print(json.dumps(result,indent=2))
    return 0 if result['mechanism_status']=='passed' else 1

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['freeze','run']);p.add_argument('--run-id',required=True);a=p.parse_args()
    assert re.fullmatch('[a-z0-9][a-z0-9_-]+',a.run_id)
    raise SystemExit(main(a.run_id,a.mode))
