#!/usr/bin/env python3
"""Bounded independent source and physical-dimension recovery controls."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
bulk = Path(os.environ['G1_RESULTS_ROOT'])
out = bulk/'io-source-dimensions-controls-20260923-r2'
assert not out.exists() and set(os.sched_getaffinity(0)) == {48}
jobs = [('current_digital_reference', HERE/'prepare_r2.py', 'fullchip-current-digital-reference-20260923-r2'),
        ('native_tap_dimensions', HERE.parents[1]/'io_tap_closure/physical_source/audit_dimensions_r2.py', 'io-tap-physical-dimensions-20260923-r2')]
inputs = {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__).resolve()]+[r[1] for r in jobs]}
out.mkdir(); (out/'source.py').write_bytes(Path(__file__).read_bytes())
result = dict(status='running source-only controls', inputs=inputs, stages=[])
try:
    for name,script,target in jobs:
        command = ['timeout','-k','5','90',sys.executable,str(script),'--output',str(bulk/target)]
        started = time.monotonic()
        with (out/(name+'.log')).open('x') as log:
            child = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
        result['stages'].append(dict(name=name, command=command, returncode=child.returncode, wall_s=time.monotonic()-started))
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == h for p,h in inputs.items())
    result['status'] = 'passed independent source-only controls' if all(r['returncode'] == 0 for r in result['stages']) else 'failed one or more source-only controls'
finally:
    (out/'summary.json').write_text(json.dumps(result, indent=2)+'\n')
raise SystemExit(0 if result['status'].startswith('passed') else 1)
