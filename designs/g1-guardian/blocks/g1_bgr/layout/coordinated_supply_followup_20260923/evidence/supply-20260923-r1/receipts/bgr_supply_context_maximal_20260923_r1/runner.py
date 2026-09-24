#!/usr/bin/env python3
"""One fresh-gated CPU2 job with an explicit coordinator allocation floor."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=next(p for p in Path(__file__).resolve().parents if (p/'flow/run.sh').is_file())

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--receipt',type=Path,required=True)
    p.add_argument('--watchdog',type=int,required=True)
    p.add_argument('--minimum-budget',type=int,required=True)
    p.add_argument('--bulk-growth',type=float,default=.1)
    p.add_argument('--ram-gib',type=int,choices=(8,16),default=8)
    p.add_argument('command',nargs=argparse.REMAINDER)
    a=p.parse_args();assert not a.receipt.exists() and 1<=a.watchdog<=1000
    assert 1<=a.minimum_budget<=64 and a.bulk_growth>=0
    assert os.environ['G1_CPUSET']=='2' and os.environ['G1_CPUS']=='1'
    a.receipt.mkdir(parents=True);(a.receipt/'runner.py').write_bytes(Path(__file__).read_bytes())
    gate=a.receipt/'resources.json'
    argv=[sys.executable,str(ROOT/'.private'/'research/verification/check_resources.py'),
          '--output',str(gate),'--expected-growth-gib','.03','--external-root',os.environ['G1_RESULTS_ROOT'],
          '--external-growth-gib',str(a.bulk_growth)]
    with (a.receipt/'resources.log').open('x') as log:
        rc=subprocess.run(argv,stdout=log,stderr=subprocess.STDOUT).returncode
    j=json.loads(gate.read_text())
    passed=rc==0 and j['status']=='passed' and j['project_cpu_budget']>=a.minimum_budget and j['ram_available_bytes']>=a.ram_gib*1024**3
    check=dict(status='passed' if passed else 'failed',required_coordinator_budget=a.minimum_budget,
               observed_budget=j['project_cpu_budget'],RAM_reservation_GiB=a.ram_gib,
               CPU=2,memory_enforced=False,runtime_launch='permitted' if passed else 'not run')
    (a.receipt/'prelaunch.json').write_text(json.dumps(check,indent=2)+'\n')
    assert passed,check
    sys.path.insert(0,str(ROOT/'designs/g1-guardian/blocks/g1_top/sim'))
    from run_bounded import run_bounded
    argv=a.command[1:] if a.command[0]=='--' else a.command
    with (a.receipt/'run.log').open('x') as log:
        state=run_bounded(argv,log,a.receipt/'run.json',a.watchdog,metadata=dict(
            CPU=2,reservation_GiB=a.ram_gib,memory_enforced=False,command=argv,
            required_coordinator_budget=a.minimum_budget,
            resource_sha256=hashlib.sha256(gate.read_bytes()).hexdigest(),
            runner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))
    print(json.dumps(state,indent=2))
    assert state['status']=='completed' and state['returncode']==0

if __name__=='__main__':main()
