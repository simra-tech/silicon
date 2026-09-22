#!/usr/bin/env python3
"""Fresh-gated 180s candidate build; no canonical mutation."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run-id', required=True)
    ap.add_argument('--resource-gate', type=Path, required=True)
    args = ap.parse_args()
    assert re.fullmatch('bgr-assembly-viaquad-[a-z0-9-]+', args.run_id)
    gate = json.loads(args.resource_gate.read_text())
    stamp = datetime.datetime.strptime(gate['utc'].replace('+00:00', ''), '%Y-%m-%dT%H:%M:%S.%f').replace(tzinfo=datetime.timezone.utc)
    assert gate['status'] == 'passed' and 0 <= (datetime.datetime.now(datetime.timezone.utc) - stamp).total_seconds() < 1800
    assert gate['external_allocation']['expected_growth_gib'] >= 2
    bulk = Path(os.environ['G1_RESULTS_ROOT'])
    assert str(bulk) == gate['external_allocation']['root']
    out = bulk / args.run_id
    out.mkdir(exist_ok=False)
    files = [HERE / 'build_viaquad.py', Path(__file__), ROOT / 'flow/run.sh', HERE.parent / 'coordinated_full_closure/build_assembly.py']
    bindings = {str(p): sha(p) for p in files}
    for p in files[:2]:
        (out / p.name).write_bytes(p.read_bytes())
    command = ['flow/run.sh', 'timeout', '--kill-after=5', '180', 'python3',
               str((HERE / 'build_viaquad.py').relative_to(ROOT)), '--output', str(out)]
    receipt = dict(status='running', command=command, cpu=1, watchdog_s=180, memory_reservation_gib=8,
                   memory_enforced=False, bindings=bindings, resource_gate_sha256=sha(args.resource_gate))
    save = lambda: (out / 'run.json').write_text(json.dumps(receipt, indent=2) + '\n')
    save()
    start = time.monotonic()
    with (out / 'run.log').open('x') as log:
        process = subprocess.run(command, cwd=str(ROOT), env=dict(os.environ, G1_CPUS='1', G1_CPUSET='1', G1_MEMORY='8g'),
                                 stdout=log, stderr=subprocess.STDOUT)
    receipt.update(returncode=process.returncode, wall_s=time.monotonic() - start,
                   inputs_unchanged=all(sha(Path(p)) == h for p, h in bindings.items()),
                   output_bytes=sum(p.stat().st_size for p in out.rglob('*') if p.is_file()))
    receipt['status'] = 'passed' if process.returncode == 0 and receipt['inputs_unchanged'] and receipt['output_bytes'] < 2 * 2**30 else 'failed'
    save()
    print(json.dumps(receipt, indent=2))
    return 0 if receipt['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
