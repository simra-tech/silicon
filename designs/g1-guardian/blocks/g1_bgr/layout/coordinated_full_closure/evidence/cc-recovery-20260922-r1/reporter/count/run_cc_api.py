#!/usr/bin/env python3
"""Bounded immutable-input launcher for output-only native CC diagnostics."""
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
    ap.add_argument('--full', action='store_true')
    ap.add_argument('--audit-only', action='store_true')
    ap.add_argument('--reporter', choices=('original', 'count-only'), required=True)
    ap.add_argument('--parity', type=Path)
    args = ap.parse_args()
    assert re.fullmatch('bgr-cc-api-[a-z0-9-]+', args.run_id)
    assert len(os.sched_getaffinity(0)) == 1 and next(iter(os.sched_getaffinity(0))) in range(4)
    gate = json.loads(args.resource_gate.read_text())
    age = (datetime.datetime.now(datetime.timezone.utc) - datetime.datetime.fromisoformat(gate['utc'])).total_seconds()
    assert gate['status'] == 'passed' and 0 <= age < 1800
    bulk = Path(os.environ['G1_RESULTS_ROOT'])
    assert str(bulk) == gate['external_allocation']['root'] and gate['external_allocation']['expected_growth_gib'] >= 2
    if args.full:
        database = bulk / 'bgr-pex-prepare-20260922-r3/extraction.lvsdb'
        digest = '6bc87673405b26f4cbc9f23c7ddf77d49c35b2ae12ec70dc0c0786f8d797856f'
        cell = 'g1_bgr'
        if not args.audit_only:
            assert args.reporter == 'count-only' and args.parity
            parity = json.loads(args.parity.read_text())
            assert parity['status'] == 'passed exact binary64 reporter parity' and parity['capacitor_count'] == 21
            assert parity['worker_sha256'] == sha(Path(__file__).with_name('export_cc_api.py'))
            assert all(sha(Path(p)) == h for p, h in parity['inputs'].items())
    else:
        database = bulk / 'bgr-union-pilot-check-20260922-r1/union.lvsdb'
        digest = '01742a9ad52ba2329b4f77883269ef7259452003921fbe547907d758c608990a'
        cell = 'bgr_hbt_worstrows'
    assert sha(database) == digest
    out = bulk / args.run_id
    out.mkdir(exist_ok=False)
    worker = Path(__file__).with_name('export_cc_api.py')
    files = [database, Path(__file__), worker, args.resource_gate]
    if args.parity:
        files.append(args.parity)
    inputs = {str(p): sha(p) for p in files}
    for p in (Path(__file__), worker):
        (out / p.name).write_bytes(p.read_bytes())
    limit = 180 if args.audit_only or not args.full else 900
    command = ['python3', str(worker), '--database', str(database), '--database-sha256', digest,
               '--cell', cell, '--output', str(out / 'result'), '--reporter', args.reporter]
    if args.audit_only:
        command.append('--audit-only')
    receipt = dict(status='running', inputs=inputs, command=command, watchdog_s=limit, kill_grace_s=5,
                   memory_reservation_gib=8, memory_enforced=False, cpu=list(os.sched_getaffinity(0)),
                   output_bound_bytes=2 * 2**30, scope='raw native CC, not completeness or adoption')
    def save():
        (out / 'launch.json').write_text(json.dumps(receipt, indent=2) + '\n')
    save()
    start = time.monotonic()
    with (out / 'worker.log').open('x') as log:
        result = subprocess.run(['timeout', '--kill-after=5', str(limit)] + command, stdout=log, stderr=subprocess.STDOUT)
    receipt.update(returncode=result.returncode, wall_s=time.monotonic() - start,
                   inputs_unchanged=all(sha(Path(p)) == h for p, h in inputs.items()),
                   output_bytes=sum(p.stat().st_size for p in out.rglob('*') if p.is_file()))
    receipt['status'] = 'passed' if result.returncode == 0 and receipt['inputs_unchanged'] and receipt['output_bytes'] <= receipt['output_bound_bytes'] else 'failed'
    save()
    print(json.dumps(receipt, indent=2))
    return 0 if receipt['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
