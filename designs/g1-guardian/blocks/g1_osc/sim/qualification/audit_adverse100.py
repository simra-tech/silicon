#!/usr/bin/env python3
"""Audit preserved30 plus fresh70 fixed-source slowhot oscillator samples."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    mapping, manifests, artifacts = {}, {}, []
    ids = [('osc_mc20_slowhot_r095_20260922_01' if seed <= 62020 else 'osc_adverse30_r095_20260922_r1')+'_s'+str(seed) for seed in range(62001, 62031)]
    ids += ['osc-r095-adverse100-b%d-20260922-a' % n for n in range(1, 9)]
    reference = None
    for name in ids:
        run = HERE/'runs'/name
        m = json.loads((run/'manifest.json').read_text())
        if reference is None:
            reference = m
        checks = {key: m[key] == reference[key] for key in ['image_id', 'ngspice', 'pdk_commit', 'model_sha256', 'fingerprint_parameters']}
        checks['all_snapshots_hash_exact'] = all(sha(run/key) == value for key, value in m['source_sha256'].items())
        checks['all_circuit_snapshots_same'] = all(m['source_sha256'][key] == value for key, value in reference['source_sha256'].items() if key != 'run_mc.py')
        checks['all_expected_leaves_present'] = sorted(row['name'] for row in m['cases']) == sorted(m['expected_cases'])
        assert all(checks.values()), (name, checks)
        manifests[name] = {'sha256': sha(run/'manifest.json'), 'checks': checks,
                           'runner_sha256': m['source_sha256']['run_mc.py']}
        for row in m['cases']:
            mapping.setdefault(row['seed'], []).append((name, row))
        for file in sorted(run.iterdir()):
            if file.is_file():
                artifacts.append({'logical_path': str(file.relative_to(ROOT)), 'sha256': sha(file), 'bytes': file.stat().st_size})
    assert sorted(mapping) == list(range(62001, 62101))
    samples, fingerprints = [], set()
    for seed, pairs in sorted(mapping.items()):
        pairs.sort(key=lambda pair: pair[1]['code'])
        assert [row['code'] for _, row in pairs] == [0, 15]
        checks = {'numerical': all(row['status'] == 'passed' and row['solver_exit'] == 0 and not row['timed_out'] for _, row in pairs),
                  'conditions': all((row['mos'], row['res'], row['cap'], row['vdd'], row['temperature_C']) == ('ss', 'wcs', 'wcs', 1.08, 125) for _, row in pairs)}
        fp = pairs[0][1]['fingerprints'][:269]
        checks['full269_frozen_across_endpoints'] = all(len(row['fingerprints']) == 538 and row['fingerprints'][:269] == fp == row['fingerprints'][269:] for _, row in pairs)
        checks['deck_hashes'] = all(sha(HERE/'runs'/name/(row['name']+'.cir')) == row['deck_sha256'] for name, row in pairs)
        wave_checks = []
        for name, row in pairs:
            try:
                data = np.loadtxt(str(HERE/'runs'/name/(row['name']+'.dat')), skiprows=1)
                wave_checks.append(bool(data.shape[1] == 5 and np.isfinite(data).all() and np.all(np.diff(data[:, 0]) > 0) and abs(data[-1, 0]-6e-6) < 1e-12))
            except (OSError, ValueError, IndexError):
                wave_checks.append(False)
        checks['complete_finite_waveforms'] = all(wave_checks)
        if all(checks.values()):
            assert tuple(fp) not in fingerprints
            fingerprints.add(tuple(fp))
        frequencies = [row['measurements'].get('fmhz') for _, row in pairs]
        bracket = min(frequencies) <= 10 <= max(frequencies) if all(checks.values()) else None
        samples.append({'seed': seed, 'runs': [name for name, _ in pairs], 'checks': checks,
                        'frequency_MHz': frequencies, 'brackets_10MHz': bracket,
                        'wall_seconds': sum(row['wall_seconds'] for _, row in pairs)})
    result = {'attempted_samples': len(samples), 'attempted_leaves': 2*len(samples),
              'qualified_samples': sum(all(row['checks'].values()) for row in samples),
              'numerical_or_contract_failed_samples': sum(not all(row['checks'].values()) for row in samples),
              'bracket_failures': sum(row['brackets_10MHz'] is False for row in samples),
              'bracket_not_run': sum(row['brackets_10MHz'] is None for row in samples),
              'distinct269_parameter_vectors': len(fingerprints),
              'extension70_core_seconds': sum(row['wall_seconds'] for row in samples[30:]),
              'manifests': manifests, 'samples': samples, 'artifacts': artifacts,
              'runner_difference': 'Only external result-directory allocation imports/call changed; circuit/model bytes checked separately and exactly.',
              'scope': 'Simulated R0.95 candidate slowhot endpoints0/15 at ss/wcs/wcs1.08V125C50fF; original30 retained,70 independent new seeds. Baseline16/30 failures unchanged. Not full-code statistical monotonicity, new physical geometry/PEX, measured yield or adoption.'}
    with a.output.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps({key: value for key, value in result.items() if key not in ['manifests', 'samples', 'artifacts']}, indent=2))


if __name__ == '__main__':
    main()
