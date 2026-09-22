#!/usr/bin/env python3
"""Bound the supported API data-recovery child; retain every failure."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('pilot', 'output', 'resource-gate'):
        parser.add_argument('--' + name, required=True, type=Path)
    parser.add_argument('--audit-only', action='store_true')
    args = parser.parse_args()
    assert os.sched_getaffinity(0) == {6}
    gate = json.loads(args.resource_gate.read_text())
    age = (datetime.datetime.now(datetime.timezone.utc) - datetime.datetime.fromisoformat(gate['utc'])).total_seconds()
    assert gate['status'] == 'passed' and 0 <= age < 1800
    assert gate['external_allocation']['expected_growth_gib'] >= 1
    args.output.mkdir(parents=True, exist_ok=False)
    worker = Path(__file__).with_name('export_sense_kpex_api.py')
    for script in (Path(__file__), worker):
        (args.output / script.name).write_bytes(script.read_bytes())
    command = ['python3', str(worker), '--pilot', str(args.pilot), '--output', str(args.output / 'data')]
    if args.audit_only:
        command.append('--audit-only')
    limit = 45 if args.audit_only else 180
    result = dict(status='running', command=command, timeout_s=limit, max_output_bytes=2**30,
                  source_preserving_electrical_qualification='not run', repeated_LVS=False,
                  resource_gate_sha256=hashlib.sha256(args.resource_gate.read_bytes()).hexdigest())
    report = args.output / 'supervisor.json'
    def save():
        report.write_text(json.dumps(result, indent=2) + '\n')
    save()
    start = time.monotonic()
    interrupted = []
    previous = {sig: signal.signal(sig, lambda num, frame: interrupted.append(num)) for sig in (signal.SIGINT, signal.SIGTERM)}
    reason = None
    with (args.output / 'worker.log').open('x') as log:
        child = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            while child.poll() is None:
                size = sum(path.stat().st_size for path in args.output.rglob('*') if path.is_file())
                elapsed = time.monotonic() - start
                result.update(wall_s=elapsed, output_bytes=size)
                save()
                if interrupted or elapsed >= limit or size > 2**30:
                    reason = 'external_interrupt' if interrupted else ('timeout' if elapsed >= limit else 'output_limit')
                    os.killpg(child.pid, signal.SIGTERM)
                    try:
                        child.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        os.killpg(child.pid, signal.SIGKILL)
                        child.wait()
                    break
                try:
                    child.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    pass
        finally:
            if child.poll() is None:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait()
            for sig, handler in previous.items():
                signal.signal(sig, handler)
    result.update(status='passed bounded API child' if child.returncode == 0 and reason is None else 'failed bounded API child',
                  returncode=child.returncode, termination_reason=reason, wall_s=time.monotonic() - start,
                  output_bytes=sum(path.stat().st_size for path in args.output.rglob('*') if path.is_file()))
    save()
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['status'].startswith('passed') else 1)


if __name__ == '__main__':
    main()
