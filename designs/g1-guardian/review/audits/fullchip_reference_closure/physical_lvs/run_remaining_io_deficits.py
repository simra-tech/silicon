#!/usr/bin/env python3
"""Fresh-gated 120-second read-only residual IO audit."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import sys
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
sys.path.insert(0,str(ROOT/'designs/g1-guardian/blocks/g1_top/sim'))
from run_bounded import run_bounded


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--gate',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    assert not a.output.exists()
    gate=json.loads(a.gate.read_text())
    age=(datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(gate['utc'])).total_seconds()
    assert gate['status']=='passed' and gate['project_cpu_budget']>=43 and 0<=age<1800
    assert gate['ram_available_bytes']>8*1024**3 and set(os.sched_getaffinity(0))=={1}
    a.output.mkdir(parents=True)
    worker=HERE/'audit_remaining_io_deficits.py'
    (a.output/'runner_snapshot.py').write_bytes(Path(__file__).read_bytes())
    (a.output/'worker_snapshot.py').write_bytes(worker.read_bytes())
    digest=hashlib.sha256(worker.read_bytes()).hexdigest()
    command=['python3',str(worker),'--bulk',os.environ['G1_RESULTS_ROOT'],'--output',str(a.output/'audit')]
    with (a.output/'console.log').open('x') as log:
        run=run_bounded(command,log,a.output/'run.json',120,cwd=ROOT,interval_s=3)
    assert hashlib.sha256(worker.read_bytes()).hexdigest()==digest
    complete=run['status']=='completed' and run['returncode']==0
    result=dict(status='passed read-only audit' if complete else 'failed read-only audit',run=run,
                worker_sha256=digest,resource_gate_sha256=hashlib.sha256(a.gate.read_bytes()).hexdigest(),
                memory_reservation_GiB=8,memory_enforced=False,native_LVS='not run')
    (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if complete else 1)


if __name__=='__main__':
    main()
