#!/usr/bin/env python3
"""One bounded preparation process, with immutable receipt and no retry."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def utc(): return datetime.datetime.now(datetime.timezone.utc)
def dump(path, value): path.write_text(json.dumps(value, indent=2)+'\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--resource-gate', type=Path, required=True)
    args = ap.parse_args()
    gate = json.loads(args.resource_gate.read_text())
    stamp = datetime.datetime.strptime(gate['utc'].replace('+00:00', ''), '%Y-%m-%dT%H:%M:%S.%f').replace(tzinfo=datetime.timezone.utc)
    assert gate['status'] == 'passed' and 0 <= (utc()-stamp).total_seconds() < 1800
    assert gate['expected_growth_gib'] >= .10 and gate['project_cpu_budget'] >= 1
    assert gate['ram_available_bytes'] >= 4*2**30
    out = ROOT/'build/scratch/bgr-hbt-return-controls-20260922-r2'
    out.mkdir(exist_ok=False)
    bindings = {p: sha(p) for p in [HERE/'prepare_return_controls.py', Path(__file__).resolve(),
                HERE/'PREPARATION_CONTRACT_20260922.md', ROOT/'flow/run.sh']}
    for p in bindings: (out/p.name).write_bytes(p.read_bytes())
    command = ['flow/run.sh', 'timeout', '180', 'python3',
               str((HERE/'prepare_return_controls.py').relative_to(ROOT)),
               '--output', str(out.relative_to(ROOT))]
    env = dict(os.environ, G1_CPUS='1', G1_CPUSET='0', G1_MEMORY='4g',
               G1_EDA_IMAGE='tapeoutbench-eda:latest', G1_EDA_PLATFORM='linux/amd64')
    env.pop('G1_RESULTS_ROOT', None)
    receipt = dict(status='running', started_utc=utc().isoformat(), command=command,
                   watchdog_s=180, cpu='0', memory='4 GiB reservation only', growth_bound_gib=.10,
                   resource_gate_sha256=sha(args.resource_gate),
                   frozen_bindings={str(p.relative_to(ROOT)): h for p,h in bindings.items()})
    dump(out/'run.json', receipt); started = time.monotonic()
    try:
        with (out/'prepare.log').open('x') as log:
            result = subprocess.run(command, cwd=str(ROOT), env=env,
                                    stdout=log, stderr=subprocess.STDOUT, timeout=210)
        receipt.update(returncode=result.returncode, status='passed' if result.returncode == 0 else 'failed')
    except subprocess.TimeoutExpired:
        receipt.update(status='failed outer watchdog', returncode=None)
    receipt.update(wall_s=time.monotonic()-started, finished_utc=utc().isoformat(),
                   inputs_unchanged=all(sha(p) == h for p,h in bindings.items()),
                   output_bytes=sum(p.stat().st_size for p in out.rglob('*') if p.is_file()))
    if not receipt['inputs_unchanged']: receipt['status'] = 'failed changed input'
    if receipt['output_bytes'] > .10*2**30: receipt['status'] = 'failed growth bound'
    if receipt['status'] == 'passed':
        controls = json.loads((out/'controls.json').read_text())
        if controls['status'] != 'passed two contact and source-placement controls':
            receipt['status'] = 'failed missing completed controls'
    dump(out/'run.json', receipt); print(json.dumps(receipt, indent=2))
    return 0 if receipt['status'] == 'passed' else 1


if __name__ == '__main__': raise SystemExit(main())
