#!/usr/bin/env python3
"""Bounded frozen-input metallic R controls/full launcher; no source insertion."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run-id', required=True)
    ap.add_argument('--resource-gate', type=Path, required=True)
    ap.add_argument('--mode', choices=('controls', 'full'), required=True)
    ap.add_argument('--scenario', choices=('LEF', 'KPEX'), required=True)
    ap.add_argument('--control', type=Path)
    args = ap.parse_args()
    assert re.fullmatch('bgr-metal-r-[a-z0-9-]+', args.run_id)
    assert len(os.sched_getaffinity(0)) == 1 and next(iter(os.sched_getaffinity(0))) in range(4)
    gate = json.loads(args.resource_gate.read_text())
    age = (datetime.datetime.now(datetime.timezone.utc) - datetime.datetime.fromisoformat(gate['utc'])).total_seconds()
    assert gate['status'] == 'passed' and 0 <= age < 1800
    bulk = Path(os.environ['G1_RESULTS_ROOT'])
    assert str(bulk) == gate['external_allocation']['root'] and gate['external_allocation']['expected_growth_gib'] >= 2
    prep = bulk / 'bgr-metal-network-prepare-20260922-r1'
    worker = Path(__file__).with_name('extract_metal_r.py')
    if args.mode == 'full':
        assert args.control
        control = json.loads(args.control.read_text())
        assert control['status'] == 'passed controls' and control['scenario'] == args.scenario
        assert control['worker_sha256'] == sha(worker)
    out = bulk / args.run_id
    out.mkdir(exist_ok=False)
    files = [p for p in prep.iterdir() if p.is_file()] + [worker, Path(__file__), args.resource_gate]
    if args.control:
        files.append(args.control)
    inputs = {str(p): sha(p) for p in files}
    for p in (worker, Path(__file__)):
        (out / p.name).write_bytes(p.read_bytes())
    limit = 60 if args.mode == 'controls' else 600
    command = ['python3', str(worker), '--preparation', str(prep), '--output', str(out / 'result'),
               '--mode', args.mode, '--scenario', args.scenario]
    receipt = dict(status='running', inputs=inputs, command=command, watchdog_s=limit, kill_grace_s=5,
        cpu=list(os.sched_getaffinity(0)), memory_reservation_gib=4 if args.mode == 'controls' else 16,
        memory_enforced=False, output_bound_bytes=2 * 2**30)
    save = lambda: (out / 'launch.json').write_text(json.dumps(receipt, indent=2) + '\n')
    save()
    start = time.monotonic()
    with (out / 'worker.log').open('x') as log:
        process = subprocess.run(['timeout', '--kill-after=5', str(limit)] + command, stdout=log, stderr=subprocess.STDOUT)
    receipt.update(returncode=process.returncode, wall_s=time.monotonic() - start,
        inputs_unchanged=all(sha(Path(p)) == h for p, h in inputs.items()),
        output_bytes=sum(p.stat().st_size for p in out.rglob('*') if p.is_file()))
    receipt['status'] = 'passed' if process.returncode == 0 and receipt['inputs_unchanged'] and receipt['output_bytes'] < receipt['output_bound_bytes'] else 'failed'
    save()
    print(json.dumps({k: v for k, v in receipt.items() if k != 'inputs'}, indent=2))
    return 0 if receipt['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
