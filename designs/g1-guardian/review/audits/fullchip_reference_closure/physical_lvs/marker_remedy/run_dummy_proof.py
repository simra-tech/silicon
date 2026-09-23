#!/usr/bin/env python3
"""Bounded receipt for the independent source/native dummy control."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[6]
sys.path.insert(0,str(ROOT/'designs/g1-guardian/blocks/g1_top/sim'))
from run_bounded import run_bounded


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('gate','output'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--resistor-candidate',type=Path)
    a=p.parse_args();assert not a.output.exists()
    g=json.loads(a.gate.read_text())
    age=(datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(g['utc'])).total_seconds()
    assert g['status']=='passed' and g['project_cpu_budget']>=44 and 0<=age<1800
    assert set(os.sched_getaffinity(0))=={1}
    a.output.mkdir(parents=True)
    worker=HERE/('audit_resistor_graph.py' if a.resistor_candidate else 'prove_leveldown_dummies.py')
    (a.output/'worker_snapshot.py').write_bytes(worker.read_bytes())
    (a.output/'runner_snapshot.py').write_bytes(Path(__file__).read_bytes())
    command=['python3',str(worker),'--gate',str(a.gate),'--bulk',os.environ['G1_RESULTS_ROOT'],'--output',str(a.output/'proof')]
    if a.resistor_candidate:
        command=['python3',str(worker),'--candidate',str(a.resistor_candidate),'--output',str(a.output/'proof')]
    with (a.output/'console.log').open('x') as log:
        run=run_bounded(command,log,a.output/'run.json',120,cwd=ROOT,interval_s=2)
    result=dict(status='passed proof' if run['status']=='completed' and run['returncode']==0 else 'failed proof',
        run=run,resource_gate_sha256=hashlib.sha256(a.gate.read_bytes()).hexdigest(),memory_reservation_GiB=4,
        memory_enforced=False,source_derivative='not run')
    (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['status']=='passed proof' else 1)


if __name__=='__main__':main()
