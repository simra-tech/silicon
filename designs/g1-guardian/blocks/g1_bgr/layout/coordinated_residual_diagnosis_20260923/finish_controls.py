#!/usr/bin/env python3
"""Sequential saved-data and independently prepared source-only controls."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p/'flow/run.sh').is_file())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert set(os.sched_getaffinity(0)) == {48}
    bulk = Path(os.environ['G1_RESULTS_ROOT'])
    out = bulk/'bgr-via-and-io-source-controls-20260923-r1'
    assert not out.exists()
    audits = ROOT/'designs/g1-guardian/review/audits'
    commands = [
        ('saved_BRG_OP', [HERE/'analyze_saved.py']),
        ('current_digital_reference', [audits/'fullchip_reference_closure/current_digital_reference/prepare.py',
            '--output', bulk/'fullchip-current-digital-reference-20260923-r1']),
        ('native_tap_dimensions', [audits/'io_tap_closure/physical_source/audit_dimensions.py',
            '--output', bulk/'io-tap-physical-dimensions-20260923-r1']),
    ]
    inputs = {str(p):sha(p) for p in [Path(__file__).resolve()]+[cmd[0] for _,cmd in commands]}
    out.mkdir()
    (out/'source.py').write_bytes(Path(__file__).read_bytes())
    result = dict(status='running independent sequential controls', inputs=inputs, stages=[], new_simulation='not run')
    try:
        for name,args in commands:
            command = [sys.executable]+[str(x) for x in args]
            start = time.monotonic()
            with (out/(name+'.log')).open('x') as log:
                child = subprocess.run(['timeout','-k','5','90']+command, stdout=log, stderr=subprocess.STDOUT)
            result['stages'].append(dict(name=name, command=command, returncode=child.returncode,
                wall_s=time.monotonic()-start, watchdog_s=90,
                status='passed' if child.returncode == 0 else 'failed'))
            (out/'summary.json').write_text(json.dumps(result, indent=2)+'\n')
        assert all(sha(Path(p)) == h for p,h in inputs.items())
        result['status'] = 'passed independent sequential controls' if all(r['returncode'] == 0 for r in result['stages']) else 'failed one or more independent controls'
    finally:
        (out/'summary.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['status'].startswith('passed') else 1)


if __name__ == '__main__':
    main()
