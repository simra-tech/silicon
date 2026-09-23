#!/usr/bin/env python3
"""Bounded read-only saved-database interface probe, never an LVS pass."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
sys.path.insert(0, str(ROOT/'designs/g1-guardian/blocks/g1_top/sim'))
from run_bounded import run_bounded


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--resource-gate', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists()
    gate = json.loads(a.resource_gate.read_text())
    age = (datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(gate['utc'])).total_seconds()
    assert gate['status'] == 'passed' and gate['project_cpu_budget'] >= 45 and 0 <= age < 1800
    assert gate['ram_available_bytes'] > 8*1024**3 and set(os.sched_getaffinity(0)) == {1}
    a.output.mkdir(parents=True)
    worker = HERE/'probe_saved_interface.py'
    hashes = {str(q):sha(q) for q in (worker, Path(__file__).resolve())}
    (a.output/'runner_snapshot.py').write_bytes(Path(__file__).read_bytes())
    command = ['python3', str(worker), '--bulk', os.environ['G1_RESULTS_ROOT'], '--output', str(a.output/'probe')]
    summary = dict(status='running', command=command, script_hashes=hashes,
                   gate_sha256=sha(a.resource_gate), watchdog_seconds=120,
                   memory_reservation_GiB=8, memory_enforced=False,
                   source_geometry_or_netlist_mutation='not applicable', strict_LVS='not run')
    (a.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    with (a.output/'console.log').open('x') as log:
        run = run_bounded(command, log, a.output/'run.json', 120, cwd=ROOT, interval_s=3)
    report_path = a.output/'probe/summary.json'
    report = json.loads(report_path.read_text()) if report_path.exists() else {}
    passed = run['status'] == 'completed' and run['returncode'] == 0 and report.get('status','').startswith('passed')
    assert hashes == {q:sha(Path(q)) for q in hashes}
    summary.update(status='passed read-only probe' if passed else 'failed read-only probe', run=run,
                   output_bytes=sum(q.stat().st_size for q in a.output.rglob('*') if q.is_file()))
    (a.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))
    raise SystemExit(0 if passed else 1)


if __name__ == '__main__':
    main()
