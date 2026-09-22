#!/usr/bin/env python3
"""Separate prospective27-post-value gate for direct-TRAN lifecycle revision."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from check_hys_prefix import check as check_original

SIM=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def check(out,log_path,returncode):
    preparation=json.loads((out/'preparation.json').read_text())
    assert preparation.get('direct_tran') is True
    attestation=json.loads((out/'digital_attestation.json').read_text())
    result=check_original(out,log_path,returncode)
    checks=result['checks']
    checks.pop('all27_parameters_exact_before')
    checks['no_pre_transient_capture_claim']=result['parameters']['before']==[]
    checks['direct_checker_matches_attestation']=sha(Path(__file__))==attestation['direct_checker_sha256']
    checks['original_digital_waveform_parity']=attestation['checks']['original_control_waveform_byte_identical']
    checks['no_explicit_op']=not re.search(r'^op\s*$',(out/'prefix.cir').read_text(),re.M)
    result['status']='passed' if all(checks.values()) else 'failed'
    result['same_instance_pre_transient_parameters']='not run'
    result['parameter_contract']='27 exact post-transient observations vs frozen passed reference; not54 before/after'
    result['interpretation']='Single direct-transient .9-us prefix only. Internal initial OP, no explicit prior OP. No HYS-event or full-loop qualification.'
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run-id',required=True);p.add_argument('--log',type=Path,required=True)
    p.add_argument('--returncode',type=int,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert re.fullmatch('[a-z0-9][a-z0-9_-]+',a.run_id)
    result=check(SIM/'qualification'/a.run_id,a.log,a.returncode)
    with a.output.open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2));raise SystemExit(0 if result['status']=='passed' else 1)
