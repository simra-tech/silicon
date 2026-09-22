#!/usr/bin/env python3
"""Exactly one r2 preparation invocation; no stock rules or retries."""
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
    ap=argparse.ArgumentParser();ap.add_argument('--resource-gate',type=Path,required=True);a=ap.parse_args()
    gate=json.loads(a.resource_gate.read_text())
    stamp=datetime.datetime.strptime(gate['utc'].replace('+00:00',''),'%Y-%m-%dT%H:%M:%S.%f').replace(tzinfo=datetime.timezone.utc)
    assert gate['status']=='passed' and 0<=(datetime.datetime.now(datetime.timezone.utc)-stamp).total_seconds()<1800 and gate['expected_growth_gib']>=.1
    out=ROOT/'build/scratch/bgr-hbt-worstrows-20260922-r2';out.mkdir(exist_ok=False)
    for n in ['build_pilot.py','build_pilot_r2.py','REVISION_R2_CONTRACT_20260922.md']:(out/n).write_bytes((HERE/n).read_bytes())
    cmd=['flow/run.sh','timeout','180','python3',str((HERE/'build_pilot_r2.py').relative_to(ROOT)),'--output',str(out.relative_to(ROOT))]
    env=dict(os.environ,G1_CPUS='1',G1_CPUSET='0',G1_MEMORY='4g');env.pop('G1_RESULTS_ROOT',None)
    r=dict(status='running',command=cmd,watchdog_s=180,resource_gate_sha256=sha(a.resource_gate),
           contract_sha256=sha(HERE/'REVISION_R2_CONTRACT_20260922.md'),script_sha256=sha(HERE/'build_pilot_r2.py'),
           started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    (out/'run.json').write_text(json.dumps(r,indent=2)+'\n');start=time.monotonic()
    with (out/'prepare.log').open('x') as log:p=subprocess.run(cmd,cwd=str(ROOT),env=env,stdout=log,stderr=subprocess.STDOUT,timeout=210)
    r.update(status='passed' if p.returncode==0 else 'failed',returncode=p.returncode,wall_s=time.monotonic()-start,
             finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),output_bytes=sum(p.stat().st_size for p in out.rglob('*') if p.is_file()))
    if r['output_bytes']>.1*2**30:r['status']='failed output bound'
    (out/'run.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2));return 0 if r['status']=='passed' else 1
if __name__=='__main__':raise SystemExit(main())
