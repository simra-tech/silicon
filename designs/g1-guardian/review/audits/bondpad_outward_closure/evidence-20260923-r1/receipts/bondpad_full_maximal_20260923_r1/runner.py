#!/usr/bin/env python3
"""One immutable receipt, fresh resource gate, and one bounded CPU-1 child."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--receipt', type=Path, required=True)
    p.add_argument('--watchdog', type=int, required=True)
    p.add_argument('--minimum-budget', type=int, default=44)
    p.add_argument('--cpu', type=int, choices=[1, 48], default=1)
    p.add_argument('command', nargs=argparse.REMAINDER)
    a = p.parse_args()
    assert not a.receipt.exists() and 1 <= a.watchdog <= 1800
    a.receipt.mkdir(parents=True)
    (a.receipt / 'runner.py').write_bytes(Path(__file__).read_bytes())
    root = Path(__file__).resolve().parents[5]
    gate = root / '<private-context>/research/verification/check_resources.py'
    external = Path(os.environ['G1_RESULTS_ROOT'])
    command = [sys.executable, str(gate), '--output', str(a.receipt / 'resources.json'),
               '--expected-growth-gib', '.05', '--external-root', str(external),
               '--external-growth-gib', '2']
    with (a.receipt / 'resources.log').open('x') as log:
        result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
    assert result.returncode == 0
    resource = json.loads((a.receipt / 'resources.json').read_text())
    assert resource['status'] == 'passed' and resource['project_cpu_budget'] >= a.minimum_budget
    assert os.environ['G1_CPUSET'] == str(a.cpu) and os.environ['G1_CPUS'] == '1'
    sys.path.insert(0, str(root / 'designs/g1-guardian/blocks/g1_top/sim'))
    from run_bounded import run_bounded
    argv = a.command[1:] if a.command[0] == '--' else a.command
    with (a.receipt / 'run.log').open('x') as log:
        state = run_bounded(argv, log, a.receipt / 'run.json', a.watchdog,
                            metadata=dict(resource_sha256=hashlib.sha256((a.receipt / 'resources.json').read_bytes()).hexdigest(),
                                          CPU=a.cpu, reservation_GiB=8, memory_enforced=False,
                                          runner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))
    print(json.dumps(state, indent=2))
    raise SystemExit(0 if state['status'] == 'completed' else 1)


if __name__ == '__main__':
    main()
