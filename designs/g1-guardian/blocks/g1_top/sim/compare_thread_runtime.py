#!/usr/bin/env python3
"""Exact deterministic thread study; the ordinary same-host gate is not relaxed."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

from check_campaign import read_wave
from compare_host_runtime import sha


def normalize_init(text, threads):
    pattern = r'^set num_threads=' + str(threads) + r'$'
    value, count = re.subn(pattern, 'set num_threads=THREAD_STUDY', text, flags=re.M)
    if count != 1 or len(re.findall(r'^set num_threads=', text, re.M)) != 1:
        raise ValueError('exactly one declared thread setting required')
    return value


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('reference', type=Path)
    ap.add_argument('candidate', type=Path)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    strict = args.output.with_name(args.output.stem + '_strict_host.json')
    if args.output.exists() or strict.exists():
        ap.error('preserve prior evidence')
    manifests = [json.loads((p / 'run.json').read_text()) for p in [args.reference, args.candidate]]
    threads = [m['options']['threads'] for m in manifests]
    if threads[0] != 2 or threads[1] not in (1, 4):
        ap.error('declared study compares two-thread reference with one/four threads')
    command = [sys.executable, str(Path(__file__).with_name('compare_host_runtime.py')),
               str(args.reference), str(args.candidate), '--output', str(strict)]
    completed = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               universal_newlines=True)
    if not strict.exists():
        ap.error('strict check could not produce evidence: ' + completed.stderr)
    original = json.loads(strict.read_text())
    allowed = {'threads_identical', 'init_sha256_identical', 'every_binary64_value_identical'}
    failed = {name for name, passed in original['checks'].items() if not passed}
    checks = {'only_declared_strict_differences': failed == allowed,
              'strict_gate_failed_as_expected': completed.returncode == 1 and original['status'] == 'failed'}
    inits = []
    for label, path, manifest, thread in zip(['reference', 'candidate'],
            [args.reference, args.candidate], manifests, threads):
        init = path / '.spiceinit'
        checks[label + '_init_hash_valid'] = sha(init) == manifest['init_sha256']
        inits.append(normalize_init(init.read_text(), thread))
    checks['init_differs_only_declared_threads'] = inits[0] == inits[1]
    left, right = [read_wave(p / 'observations.tsv') for p in [args.reference, args.candidate]]
    checks['exact_columns_and_every_binary64_value'] = left == right
    output = dict(status='passed' if all(checks.values()) else 'failed', checks=checks,
                  threads=threads, wall_s=[m['wall_s'] for m in manifests],
                  strict_host_assessment_sha256=sha(strict), checker_sha256=sha(Path(__file__)),
                  scope='Only this deterministic4us fixture. Every saved value must match exactly; no tolerance/interpolation. Ordinary same-input host parity remains separately strict. No electrical or MC qualification.')
    with args.output.open('x') as f:
        json.dump(output, f, indent=2)
        f.write('\n')
    print(json.dumps(output, indent=2))
    if output['status'] != 'passed':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
