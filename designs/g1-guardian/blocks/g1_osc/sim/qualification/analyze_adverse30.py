#!/usr/bin/env python3
"""Audit the preserved 20+10 endpoint samples independently for each geometry."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    output = HERE/'adverse30_comparison_20260922_r1.json'
    assert not output.exists()
    result = {'sample_policy': 'Independent population summaries per netlist. Equal seeds across changed resistor geometry are not paired physical samples.',
              'limitations': 'Endpoint-only codes 0/15, slowhot ss/wcs/wcs 1.08V 125C, 50fF ideal load, capacitance-only PEX. No all-code monotonicity, physical candidate layout, extracted candidate parasitics or yield adoption.',
              'variants': {}}
    for variant, old, new in [
            ('baseline', 'osc_mc20_slowhot_20260922_01', 'osc_adverse30_base_20260922_r1'),
            ('r095', 'osc_mc20_slowhot_r095_20260922_01', 'osc_adverse30_r095_20260922_r1')]:
        samples, reference = [], None
        for seed in range(62001, 62031):
            run_id = (old if seed <= 62020 else new)+'_s'+str(seed)
            folder = HERE/'runs'/run_id
            manifest = json.loads((folder/'manifest.json').read_text())
            if reference is None:
                reference = manifest
            checks = {key: manifest[key] == reference[key] for key in
                      ['image_id', 'ngspice', 'pdk_commit', 'source_sha256', 'model_sha256', 'fingerprint_parameters']}
            checks['source_files_match'] = all(sha(folder/name) == digest for name, digest in manifest['source_sha256'].items())
            rows = sorted(manifest['cases'], key=lambda row: row['code'])
            checks['expected_cases'] = manifest['expected_cases'] == ['s%d_c0'%seed, 's%d_c15'%seed]
            checks['numerical_completion'] = len(rows) == 2 and all(row['status'] == 'passed' and row['solver_exit'] == 0 and not row['timed_out'] for row in rows)
            checks['deck_identity'] = all(sha(folder/(row['name']+'.cir')) == row['deck_sha256'] for row in rows)
            checks['conditions'] = all((row['mos'], row['res'], row['cap'], row['vdd'], row['temperature_C']) == ('ss', 'wcs', 'wcs', 1.08, 125) for row in rows)
            n = len(manifest['fingerprint_parameters'])
            checks['full_fingerprint_frozen'] = n == 269 and len(rows) == 2 and all(len(row['fingerprints']) == 2*n and row['fingerprints'][:n] == rows[0]['fingerprints'][:n] == row['fingerprints'][n:] for row in rows)
            frequencies = [row['measurements'].get('fmhz') for row in rows]
            bracket = min(frequencies) <= 10 <= max(frequencies) if all(checks.values()) else None
            samples.append({'seed': seed, 'run_id': run_id, 'manifest_sha256': sha(folder/'manifest.json'),
                            'checks': checks, 'frequency_MHz': frequencies, 'brackets_10MHz': bracket,
                            'waveform_sha256': {row['name']: sha(folder/(row['name']+'.dat')) for row in rows if (folder/(row['name']+'.dat')).exists()},
                            'wall_seconds': sum(row['wall_seconds'] for row in rows)})
        result['variants'][variant] = {'samples': samples, 'expected_samples': 30,
            'qualified_samples': sum(all(row['checks'].values()) for row in samples),
            'bracket_failures': sum(row['brackets_10MHz'] is False for row in samples),
            'bracket_not_run': sum(row['brackets_10MHz'] is None for row in samples),
            'extension_bracket_failures': sum(row['brackets_10MHz'] is False for row in samples[20:]),
            'extension_wall_seconds': sum(row['wall_seconds'] for row in samples[20:])}
    output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({key: {k: v for k, v in value.items() if k != 'samples'} for key, value in result['variants'].items()}, indent=2))


if __name__ == '__main__':
    main()
