#!/usr/bin/env python3
"""Exact-source five-tuple/all16 candidate screen, not Cartesian PVT closure."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    ids = ['osc_r095_candidate_shard0_20260921_01', 'osc_r095_candidate_shard1_20260921_01', 'osc_r095_remaining48_20260922_r1']
    tuples = [('tt', 'typ', 'typ', 1.2, 27), ('ss', 'wcs', 'wcs', 1.08, -40),
              ('ss', 'wcs', 'wcs', 1.08, 125), ('ff', 'bcs', 'bcs', 1.32, -40), ('ff', 'bcs', 'bcs', 1.32, 125)]
    manifest_hashes, cases, reference = {}, {}, None
    for run_id in ids:
        folder = HERE/'runs'/run_id
        manifest = json.loads((folder/'manifest.json').read_text())
        manifest_hashes[run_id] = sha(folder/'manifest.json')
        if reference is None:
            reference = manifest
        assert all(reference[key] == manifest[key] for key in ['image_id', 'pdk_commit', 'ngspice', 'models_sha256', 'pex_sha256', 'source_pex_sha256'])
        assert sha(folder/'osc.spice') == manifest['pex_sha256']
        assert sha(folder/'osc_source.spice') == manifest['source_pex_sha256']
        assert manifest['candidate']['charging_resistor_length_scale'] == .95
        for row in manifest['cases']:
            key = tuple(row[field] for field in ['mos', 'res', 'cap', 'vdd', 'temp', 'code'])
            assert key not in cases
            deck = folder/(row['name']+'.cir')
            checks = {'deck_hash': sha(deck) == row['deck_sha256'],
                      'numerical': row['status'] == 'passed' and row['solver_exit'] == 0 and not row['timed_out']}
            wave = folder/(row['name']+'.dat')
            try:
                data = np.loadtxt(str(wave), skiprows=1)
                checks['complete_finite_waveform'] = bool(np.isfinite(data).all() and np.all(np.diff(data[:, 0]) > 0) and abs(data[-1, 0]-6e-6) < 1e-12)
            except (OSError, ValueError, IndexError):
                checks['complete_finite_waveform'] = False
            cases[key] = {'run_id': run_id, 'name': row['name'], 'checks': checks,
                          'status': 'passed' if all(checks.values()) else 'failed',
                          'frequency_MHz': row['measurements'].get('fmhz'),
                          'duty_percent': row['measurements'].get('duty'),
                          'waveform_sha256': sha(wave) if wave.exists() else None,
                          'wall_seconds': row['wall_seconds']}
    result = {'manifest_sha256': manifest_hashes, 'tuples': [], 'expected_leaves': 80,
              'attempted_leaves': len(cases), 'numerical_failed_leaves': sum(row['status'] != 'passed' for row in cases.values()),
              'scope': 'Five selected PVT tuples, all16codes, nominal mismatch-disabled models and50fF ideal load. Source identity preserved across retained/new runs. Not full Cartesian PVT, physical adoption, full clock tree, jitter or measured yield.'}
    for condition in tuples:
        rows = [cases.get(condition+(code,), {'status': 'not run', 'code': code}) for code in range(16)]
        complete = all(row['status'] == 'passed' for row in rows)
        frequencies = [row['frequency_MHz'] for row in rows] if complete else []
        result['tuples'].append({'condition': condition, 'cases': rows, 'numerical_status': 'passed' if complete else 'failed or not run',
                                 'strictly_decreasing_all16': all(a > b for a, b in zip(frequencies, frequencies[1:])) if complete else None,
                                 'brackets_10MHz': min(frequencies) <= 10 <= max(frequencies) if complete else None,
                                 'nearest_code_error_percent': min((100*(f/10-1) for f in frequencies), key=abs) if complete else None})
    result['status'] = 'passed' if len(cases) == 80 and all(row['numerical_status'] == 'passed' and row['strictly_decreasing_all16'] and row['brackets_10MHz'] for row in result['tuples']) else 'failed or not run'
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({key: value for key, value in result.items() if key != 'tuples'}, indent=2))
    for row in result['tuples']:
        print(json.dumps({key: value for key, value in row.items() if key != 'cases'}))


if __name__ == '__main__':
    main()
