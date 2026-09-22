#!/usr/bin/env python3
"""One bounded pilot preparation; source geometry and failures never overwritten."""
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
def main():
    p=argparse.ArgumentParser();p.add_argument('--run-id',required=True);p.add_argument('--resource-gate',type=Path,required=True);a=p.parse_args()
    assert a.run_id.startswith('bgr-hbt-worstrows-') and all(c.isalnum() or c=='-' for c in a.run_id)
    gate=json.loads(a.resource_gate.read_text())
    timestamp=datetime.datetime.strptime(gate['utc'].replace('+00:00',''),'%Y-%m-%dT%H:%M:%S.%f').replace(tzinfo=datetime.timezone.utc)
    age=(datetime.datetime.now(datetime.timezone.utc)-timestamp).total_seconds()
    assert gate['status']=='passed' and 0<=age<1800 and gate['expected_growth_gib']>=.1
    out=ROOT/'build/scratch'/a.run_id;out.mkdir(exist_ok=False)
    for name in ['build_pilot.py','PREPARATION_CONTRACT_20260922.md']:(out/name).write_bytes((HERE/name).read_bytes())
    command=['flow/run.sh','timeout','180','python3',str((HERE/'build_pilot.py').relative_to(ROOT)),'--output',str(out.relative_to(ROOT))]
    env=dict(os.environ,G1_CPUS='1',G1_CPUSET='0',G1_MEMORY='4g');env.pop('G1_RESULTS_ROOT',None)
    receipt=dict(status='running',command=command,watchdog_s=180,cpu='0',memory='4GiB reservation only',
                 resource_gate_sha256=sha(a.resource_gate),script_sha256=sha(HERE/'build_pilot.py'),
                 contract_sha256=sha(HERE/'PREPARATION_CONTRACT_20260922.md'),started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    (out/'run.json').write_text(json.dumps(receipt,indent=2)+'\n');started=time.monotonic()
    with (out/'prepare.log').open('w') as log:result=subprocess.run(command,cwd=str(ROOT),env=env,stdout=log,stderr=subprocess.STDOUT,timeout=210)
    receipt.update(status='passed' if result.returncode==0 else 'failed',returncode=result.returncode,
                   wall_s=time.monotonic()-started,finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    receipt['output_bytes']=sum(f.stat().st_size for f in out.rglob('*') if f.is_file())
    if receipt['output_bytes']>.1*2**30:receipt['status']='failed output bound'
    (out/'run.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
    return 0 if receipt['status']=='passed' else 1
if __name__=='__main__':raise SystemExit(main())
