#!/usr/bin/env python3
"""Independent bounded cases; a sparse-pin crash remains a failed API check."""
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
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--resource-gate',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    assert not a.output.exists() and set(os.sched_getaffinity(0))=={1}
    gate=json.loads(a.resource_gate.read_text())
    age=(datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(gate['utc'])).total_seconds()
    assert gate['status']=='passed' and gate['project_cpu_budget']>=44 and 0<=age<1800
    a.output.mkdir(parents=True)
    worker=HERE/'test_pin_id_comparison.py'
    initial=hashlib.sha256(worker.read_bytes()).hexdigest()
    (a.output/'runner_snapshot.py').write_bytes(Path(__file__).read_bytes())
    results=[]
    # Each case independently starts from its declared small immutable fixture.
    for case in ('fresh','sparse','sparse_wrongwire','compact','compact_wrongwire'):
        command=['python3',str(worker),'--case',case,'--output',str(a.output/case)]
        with (a.output/(case+'.log')).open('x') as log:
            run=run_bounded(command,log,a.output/(case+'.json'),30,cwd=ROOT,interval_s=1)
        report=a.output/case/'summary.json'
        result=json.loads(report.read_text()) if report.exists() else None
        results.append(dict(case=case,run=run,result=result))
        # Only the exact sparse-pin crash under study may fail and still allow
        # the independent fresh-ID control; ordinary harness failures stop.
        if run['returncode'] != 0 and not (case.startswith('sparse') and run['returncode'] in (11,-11)):
            break
    assert hashlib.sha256(worker.read_bytes()).hexdigest()==initial
    summary=dict(status='completed API controls; inspect each outcome',cases=results,
                 worker_sha256=initial,resource_gate_sha256=hashlib.sha256(a.resource_gate.read_bytes()).hexdigest(),
                 native_LVS='not run',physical_or_source_change='not applicable')
    (a.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':
    main()
