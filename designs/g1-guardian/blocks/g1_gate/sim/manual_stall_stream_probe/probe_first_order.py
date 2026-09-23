#!/usr/bin/env python3
"""Bounded integration-order diagnostic; never electrical qualification."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
from analyze_stream import read_raw

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert len(os.sched_getaffinity(0)) == 1
    assert not a.output.exists()
    parent = a.baseline / 'fixture.cir'
    contract = json.loads((a.baseline / 'contract.json').read_text())
    assert sha(parent) == contract['deck_sha256']
    assert contract['mode'] == 'raw_full'
    original = parent.read_text()
    old = '.option method=gear reltol=0.005'
    new = '.option method=gear maxord=1 reltol=0.005'
    assert original.count(old) == 1 and 'maxord' not in original
    deck = original.replace(old, new)
    assert deck.replace(new, old) == original
    includes = [Path(line.split()[1]) for line in original.splitlines()
                if line.lower().startswith(('.include ', '.incpslt ', '.lib '))]
    before = {str(q): sha(q) for q in includes}
    a.output.mkdir(parents=True)
    (a.output / 'fixture.cir').write_text(deck)
    (a.output / '.spiceinit').write_bytes((a.baseline / '.spiceinit').read_bytes())
    summary = dict(checks={'exact_inverse': 'passed',
                          'electrical_acceptance': 'not run',
                          'integration_order_convergence': 'not run',
                          'hardware': 'not run'},
                   baseline_sha256=sha(parent), deck_sha256=sha(a.output / 'fixture.cir'),
                   include_hashes=before, change=[old, new], timeout_s=120,
                   status='running numerical diagnostic')
    def save():
        (a.output / 'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    save()
    start = time.monotonic()
    with (a.output / 'ngspice.log').open('wb') as log:
        try:
            result = subprocess.run(['ngspice','-b','-r','raw.bin','fixture.cir'],
                cwd=a.output, stdout=log, stderr=subprocess.STDOUT, timeout=120,
                env=dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1'))
            summary.update(returncode=result.returncode, timed_out=False)
        except subprocess.TimeoutExpired:
            summary.update(returncode=None, timed_out=True)
    summary['wall_s'] = time.monotonic()-start
    summary['checks']['includes_unchanged'] = 'passed' if before == {str(q):sha(q) for q in includes} else 'failed'
    try:
        names, rows, trailing = read_raw(a.output / 'raw.bin')
        summary.update(complete_points=len(rows), last_s=rows[-1][0], trailing_bytes=trailing,
                       vectors=names)
        endpoint = rows[-1][0] >= 16e-6*(1-1e-12)
        summary['checks']['solver_endpoint'] = 'passed' if endpoint and summary['returncode']==0 else 'failed'
    except Exception as e:
        summary['raw_error'] = repr(e)
        summary['checks']['solver_endpoint'] = 'failed'
    summary['status'] = 'diagnostic complete; no electrical qualification'
    save()
    print(json.dumps(summary))

if __name__ == '__main__':
    main()
