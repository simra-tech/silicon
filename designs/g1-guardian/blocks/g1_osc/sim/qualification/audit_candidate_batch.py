#!/usr/bin/env python3
"""Audit scoped OSC batches against their exact-source qualification manifest."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--prefix', action='append', required=True)
    parser.add_argument('--qualification', required=True)
    parser.add_argument('--first-seed', type=int, required=True)
    parser.add_argument('--samples', type=int, required=True)
    parser.add_argument('--codes', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    qpath = HERE/'runs'/args.qualification/'manifest.json'
    qualification = json.loads(qpath.read_text())
    qanalysis_path = qpath.parent/'analysis.json'
    qanalysis = json.loads(qanalysis_path.read_text())
    assert qanalysis['status'] == 'passed' and qanalysis['manifest_sha256'] == sha(qpath)
    codes = sorted(map(int, args.codes.split(',')))
    expected = list(range(args.first_seed, args.first_seed+args.samples))
    manifests, batches = {}, {}
    for prefix in args.prefix:
        path = HERE/'runs'/(prefix+'_batch.json')
        batch = json.loads(path.read_text())
        batches[prefix] = {'sha256': sha(path), 'status': batch.get('campaign_status', 'not complete')}
        for seed in batch['expected_seeds']:
            assert seed not in manifests
            folder = HERE/'runs'/(prefix+'_s'+str(seed))
            manifests[seed] = folder
    assert sorted(manifests) == expected
    samples = []
    fingerprints = []
    for seed, folder in sorted(manifests.items()):
        path = folder/'manifest.json'
        if not path.exists():
            samples.append({'seed': seed, 'status': 'not run'})
            continue
        manifest = json.loads(path.read_text())
        checks = {key: manifest[key] == qualification[key] for key in
                  ['image_id', 'ngspice', 'pdk_commit', 'source_sha256', 'model_sha256', 'fingerprint_parameters']}
        checks['source_files_match'] = all(sha(folder/name) == value for name, value in manifest['source_sha256'].items())
        rows = sorted(manifest['cases'], key=lambda row: row['code'])
        checks['expected_codes'] = [row['code'] for row in rows] == codes and manifest['expected_cases'] == ['s%d_c%d'%(seed, code) for code in codes]
        checks['numerical_completion'] = len(rows) == len(codes) and all(row['status'] == 'passed' and not row['timed_out'] and row['solver_exit'] == 0 for row in rows)
        checks['conditions'] = all((row['mos'], row['res'], row['cap'], row['vdd'], row['temperature_C']) == ('tt', 'typ', 'typ', 1.2, 27) for row in rows)
        checks['deck_hashes'] = all(sha(folder/(row['name']+'.cir')) == row['deck_sha256'] for row in rows)
        n = len(manifest['fingerprint_parameters'])
        checks['all_parameters_frozen'] = n == 269 and bool(rows) and all(len(row['fingerprints']) == 2*n and row['fingerprints'][:n] == rows[0]['fingerprints'][:n] == row['fingerprints'][n:] for row in rows)
        if checks['all_parameters_frozen']:
            fingerprints.append(tuple(rows[0]['fingerprints'][:n]))
        complete = all(checks.values())
        frequencies = [row['measurements'].get('fmhz') for row in rows]
        bracket = min(frequencies) <= 10 <= max(frequencies) if complete and 0 in codes and 15 in codes else None
        monotonic = all(a > b for a, b in zip(frequencies, frequencies[1:])) if complete and codes == list(range(16)) else None
        samples.append({'seed': seed, 'run_id': folder.name, 'status': 'passed' if complete else 'failed or incomplete',
                        'manifest_sha256': sha(path), 'checks': checks, 'frequency_MHz': frequencies,
                        'brackets_10MHz': bracket, 'strict_monotonic_all16': monotonic,
                        'nearest_measured_code_error_percent': min((100*(value/10-1) for value in frequencies), key=abs) if complete else None,
                        'waveform_sha256': {row['name']: sha(folder/(row['name']+'.dat')) for row in rows if (folder/(row['name']+'.dat')).exists()},
                        'wall_seconds': sum(row['wall_seconds'] for row in rows),
                        'numerical_failures': sum(row['status'] == 'failed' for row in rows),
                        'timeouts': sum(row['timed_out'] for row in rows)})
    result = {'qualification': args.qualification, 'qualification_manifest_sha256': sha(qpath),
              'batches': batches, 'expected_samples': args.samples, 'expected_codes': codes,
              'qualified_samples': sum(row['status'] == 'passed' for row in samples),
              'unique_full_fingerprints': len(set(fingerprints)),
              'bracket_failures': sum(row.get('brackets_10MHz') is False for row in samples),
              'monotonicity_failures': sum(row.get('strict_monotonic_all16') is False for row in samples),
              'monotonicity_evaluated_samples': sum(row.get('strict_monotonic_all16') is not None for row in samples),
              'monotonicity_not_run_samples': sum(row.get('strict_monotonic_all16') is None for row in samples),
              'samples': samples,
              'scope': 'Exact-source simulation-only R0.95 candidate, nominal27C1.2V,50fF ideal load. Endpoint bracketing is not all-code monotonicity; nearest code error is descriptive without an invented trim budget. No geometry/new PEX or silicon-yield adoption.'}
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({key: value for key, value in result.items() if key != 'samples'}, indent=2))


if __name__ == '__main__':
    main()
