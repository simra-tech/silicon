#!/usr/bin/env python3
"""One fresh-gated CPU48 job under the successor shared 60-percent policy."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = next(p for p in Path(__file__).resolve().parents if (p/'flow/run.sh').is_file())


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--receipt', type=Path, required=True)
    ap.add_argument('--watchdog', type=int, required=True)
    ap.add_argument('--minimum-budget', type=int, default=56)
    ap.add_argument('--bulk-growth', type=float, default=.1)
    ap.add_argument('--ram-gib', type=int, choices=(8,16), default=8)
    ap.add_argument('command', nargs=argparse.REMAINDER)
    a = ap.parse_args()
    assert not a.receipt.exists() and 1 <= a.watchdog <= 1000
    assert 1 <= a.minimum_budget <= 80 and a.bulk_growth >= 0
    assert os.environ['G1_CPUSET'] == '48' and os.environ['G1_CPUS'] == '1'
    a.receipt.mkdir(parents=True)
    (a.receipt/'runner.py').write_bytes(Path(__file__).read_bytes())
    gate = a.receipt/'resources.json'
    args = [sys.executable, str(ROOT/'<private>/research/verification/check_resources_v2.py'),
            '--output', str(gate), '--expected-growth-gib', '.03',
            '--external-root', os.environ['G1_RESULTS_ROOT'], '--external-growth-gib', str(a.bulk_growth)]
    with (a.receipt/'resources.log').open('x') as log:
        rc = subprocess.run(args, stdout=log, stderr=subprocess.STDOUT).returncode
    j = json.loads(gate.read_text())
    passed = rc == 0 and j['status'] == 'passed' and j['project_cpu_budget'] >= a.minimum_budget and j['ram_available_bytes'] >= a.ram_gib*2**30
    (a.receipt/'prelaunch.json').write_text(json.dumps(dict(status='passed' if passed else 'failed',
        required_budget=a.minimum_budget, observed_budget=j['project_cpu_budget'], CPU=48,
        memory_reservation_GiB=a.ram_gib, memory_enforced=False,
        runtime_launch='permitted' if passed else 'not run'), indent=2)+'\n')
    assert passed
    sys.path.insert(0, str(ROOT/'designs/g1-guardian/blocks/g1_top/sim'))
    from run_bounded import run_bounded
    command = a.command[1:] if a.command[0] == '--' else a.command
    with (a.receipt/'run.log').open('x') as log:
        result = run_bounded(command, log, a.receipt/'run.json', a.watchdog, metadata=dict(
            CPU=48, reservation_GiB=a.ram_gib, memory_enforced=False, command=command,
            required_coordinator_budget=a.minimum_budget,
            resource_sha256=hashlib.sha256(gate.read_bytes()).hexdigest(),
            runner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))
    print(json.dumps(result, indent=2))
    assert result['status'] == 'completed' and result['returncode'] == 0


if __name__ == '__main__':
    main()
