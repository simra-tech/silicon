#!/usr/bin/env python3
"""Exactly one 180 s bank preparation, no stock run or automatic retry."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[5]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def utc():return datetime.datetime.now(datetime.timezone.utc)
def dump(p,v):p.write_text(json.dumps(v,indent=2)+'\n')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--resource-gate',type=Path,required=True);a=ap.parse_args()
    gate=json.loads(a.resource_gate.read_text())
    stamp=datetime.datetime.strptime(gate['utc'].replace('+00:00',''),'%Y-%m-%dT%H:%M:%S.%f').replace(tzinfo=datetime.timezone.utc)
    assert gate['status']=='passed' and 0<=(utc()-stamp).total_seconds()<1800 and gate['expected_growth_gib']>=.2
    assert gate['project_cpu_budget']>=1 and gate['ram_available_bytes']>=4*2**30
    out=ROOT/'build/scratch/bgr-hbt-fullbank-20260922-r1';out.mkdir(exist_ok=False)
    bindings={p:sha(p) for p in [HERE/'build_bank.py',HERE/'review_assignment.py',Path(__file__).resolve(),
                                HERE/'ROUTING_CONTRACT_20260922.md',ROOT/'flow/run.sh']}
    for p in bindings:(out/p.name).write_bytes(p.read_bytes())
    # The review does not use KLayout and is independently executable before
    # any geometry process. A failed review consumes this unique candidate ID.
    review=subprocess.run(['python3',str(HERE/'review_assignment.py')],cwd=str(ROOT),stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT,universal_newlines=True,timeout=10)
    (out/'assignment_review.json').write_text(review.stdout)
    if review.returncode:
        dump(out/'run.json',dict(status='failed arithmetic review before geometry',returncode=review.returncode));return 1
    command=['flow/run.sh','timeout','180','python3',str((HERE/'build_bank.py').relative_to(ROOT)),
             '--output',str(out.relative_to(ROOT))]
    env=dict(os.environ,G1_CPUS='1',G1_CPUSET='0',G1_MEMORY='4g',G1_EDA_IMAGE='tapeoutbench-eda:latest',G1_EDA_PLATFORM='linux/amd64')
    env.pop('G1_RESULTS_ROOT',None)
    receipt=dict(status='running',started_utc=utc().isoformat(),command=command,watchdog_s=180,cpu='0',
                 memory='4GiB reservation only',growth_bound_gib=.2,resource_gate_sha256=sha(a.resource_gate),
                 frozen_bindings={str(p.relative_to(ROOT)):h for p,h in bindings.items()})
    dump(out/'run.json',receipt);start=time.monotonic()
    try:
        with (out/'prepare.log').open('x') as log:
            run=subprocess.run(command,cwd=str(ROOT),env=env,stdout=log,stderr=subprocess.STDOUT,timeout=210)
        receipt.update(status='passed' if run.returncode==0 else 'failed',returncode=run.returncode)
    except subprocess.TimeoutExpired:receipt.update(status='failed outer watchdog',returncode=None)
    receipt.update(finished_utc=utc().isoformat(),wall_s=time.monotonic()-start,
                   output_bytes=sum(p.stat().st_size for p in out.rglob('*') if p.is_file()),
                   frozen_inputs_unchanged=all(sha(p)==h for p,h in bindings.items()))
    if receipt['output_bytes']>.2*2**30 or not receipt['frozen_inputs_unchanged']:receipt['status']='failed bound or changed input'
    if receipt['status']=='passed' and json.loads((out/'preparation.json').read_text())['status']!='passed preparation':
        receipt['status']='failed incomplete preparation'
    dump(out/'run.json',receipt);print(json.dumps(receipt,indent=2));return 0 if receipt['status']=='passed' else 1

if __name__=='__main__':raise SystemExit(main())
