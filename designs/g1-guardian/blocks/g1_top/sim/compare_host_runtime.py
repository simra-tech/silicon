#!/usr/bin/env python3
"""Strict same-image host replay: complete endpoints and every saved binary64 value.

This deliberately uses no tolerance, interpolation or partial-prefix acceptance.
A failure is evidence to investigate, not permission to change the criterion.
"""
import argparse
import hashlib
import json
from pathlib import Path
from check_campaign import read_wave
from simulation_errors import solver_failure

HERE = Path(__file__).resolve().parent

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def rtl_identity(manifest):
    if manifest.get('rtl_sha256'):
        return manifest['rtl_sha256']
    origin = HERE / 'logs' / (Path(manifest['source_deck']).stem + '.json')
    original = json.loads(origin.read_text())
    return {k: v for k, v in original['input_sha256'].items() if '/rtl/' in k}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('reference', type=Path)
    parser.add_argument('candidate', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.reference.resolve() == args.candidate.resolve():
        parser.error('reference and candidate must be independent runs')
    if args.output.exists():
        parser.error('refusing to overwrite evidence')
    manifests, assessments, waves = [], [], []
    checks, artifacts = {}, {}
    for label, directory in [('reference', args.reference), ('candidate', args.candidate)]:
        manifest = json.loads((directory / 'run.json').read_text())
        assessment = json.loads((directory / 'assessment.json').read_text())
        path = directory / 'observations.tsv'
        columns, rows = read_wave(path)
        checks[label + '_completion'] = (assessment['completion'] == 'passed'
            and manifest['status'] == 'completed' and manifest['returncode'] == 0
            and abs(rows[-1][0] - assessment['requested_end_s']) < 1e-12)
        checks[label + '_wave_hash'] = sha(path) == assessment['observation_sha256']
        checks[label + '_solver_log_valid'] = not solver_failure((directory / 'run.log').read_text())
        manifests.append(manifest)
        assessments.append(assessment)
        waves.append((columns, rows))
        artifacts[label] = {p: sha(directory / p) for p in ['run.json', 'run.log', 'assessment.json', 'observations.tsv']}
    left, right = manifests
    for key in ['image_id', 'pdk_commit', 'source_deck_sha256', 'included_sha256',
                'model_sha256', 'ngspice_version', 'init_sha256', 'byteorder']:
        checks[key + '_identical'] = bool(left.get(key)) and left.get(key) == right.get(key)
    checks['rtl_identical'] = bool(rtl_identity(left)) and rtl_identity(left) == rtl_identity(right)
    checks['threads_identical'] = left['options']['threads'] == right['options']['threads']
    checks['requested_endpoint_identical'] = assessments[0]['requested_end_s'] == assessments[1]['requested_end_s']
    lc, lr = waves[0]
    rc, rr = waves[1]
    checks['columns_identical'] = lc == rc
    checks['row_counts_identical'] = len(lr) == len(rr)
    mismatches = None
    if all(checks.values()):
        mismatches = sum(x != y for a, b in zip(lr, rr) for x, y in zip(a, b))
        checks['every_binary64_value_identical'] = mismatches == 0
    else:
        checks['every_binary64_value_identical'] = False
    result = dict(status='passed' if all(checks.values()) else 'failed', checks=checks,
                  rows=[len(lr), len(rr)], columns=len(lc), mismatched_values=mismatches,
                  artifacts=artifacts, checker_sha256=sha(Path(__file__)),
                  scope='Same-image deterministic startup replay only; MC and full electrical acceptance are separate.')
    with args.output.open('x') as output:
        output.write(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    if result['status'] != 'passed':
        raise SystemExit(1)

if __name__ == '__main__':
    main()
