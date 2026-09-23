#!/usr/bin/env python3
"""One bounded pinned-reader source-adapter control, no layout extraction."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
sys.path.insert(0, str(ROOT / 'designs/g1-guardian/blocks/g1_top/sim'))
from run_bounded import run_bounded


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--resource-gate', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    a = ap.parse_args()
    assert not a.output.exists()
    a.output.mkdir(parents=True)
    gate = json.loads(a.resource_gate.read_text())
    age = (datetime.datetime.now(datetime.timezone.utc) - datetime.datetime.fromisoformat(gate['utc'])).total_seconds()
    assert gate['status'] == 'passed' and gate['project_cpu_budget'] >= 45 and 0 <= age < 1800
    assert set(os.sched_getaffinity(0)) == {0}
    bulk = Path(os.environ['G1_RESULTS_ROOT'])
    original = bulk / 'fullchip-name-interface-20260923-r1/g1_chip_top_layout_name_only.cdl'
    adapted = bulk / 'fullchip-tap-prefix-adapter-20260923-r1/fullchip_tap_prefix_only.cdl'
    worker = HERE / 'probe_tap_adapter.rb'
    inputs = {str(p): sha(p) for p in [original, adapted, worker, Path(__file__)]}
    command = ['klayout', '-b', '-r', str(worker), '-rd', 'original=' + str(original),
               '-rd', 'adapted=' + str(adapted), '-rd', 'output_dir=' + str(a.output / 'reader')]
    (a.output / 'runner_snapshot.py').write_bytes(Path(__file__).read_bytes())
    (a.output / 'worker_snapshot.rb').write_bytes(worker.read_bytes())
    result = dict(status='running', inputs=inputs, command=command, watchdog_seconds=120,
                  memory_reservation_GiB=2, memory_enforced=False, resource_gate_sha256=sha(a.resource_gate),
                  stock_LVS='not run', electrical_simulation='not applicable')
    (a.output / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    with (a.output / 'console.log').open('x') as log:
        run = run_bounded(command, log, a.output / 'run.json', 120, cwd=ROOT, interval_s=2)
    report = a.output / 'reader/summary.json'
    parsed = json.loads(report.read_text()) if report.exists() else None
    unchanged = all(sha(Path(p)) == h for p, h in inputs.items())
    passed = run['status'] == 'completed' and run['returncode'] == 0 and parsed is not None and parsed['status'].startswith('passed') and unchanged
    result.update(status='passed' if passed else 'failed', run=run, inputs_unchanged=unchanged,
                  reader_report=parsed, output_bytes=sum(p.stat().st_size for p in a.output.rglob('*') if p.is_file()))
    (a.output / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if passed else 1)


if __name__ == '__main__':
    main()
