#!/usr/bin/env python3
"""Audit fresh completed OSC synthetic endpoints against preserved failed inputs."""
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    old = HERE/'runs/osc_synthetic_jitter_20260922_01'
    original = json.loads((old/'manifest.json').read_text())
    cases = []
    for amplitude, run_id in [(0, 'osc_synthetic_save0_20260922_r1'),
                              (1, 'osc_synthetic_save15_20260922_r1'),
                              (5, 'osc_synthetic_save15_20260922_r1')]:
        folder = HERE/'runs'/run_id
        current = json.loads((folder/'manifest.json').read_text())
        case = next(row for row in current['cases'] if row['requested_rms_mV'] == amplitude)
        stem = 'rms_%dmV'%amplitude
        checks = {key: original[key] == current[key] for key in ['image_id', 'ngspice', 'pdk_commit', 'model_sha256', 'source_sha256', 'waveform_sha256', 'synthetic_model']}
        checks['source_files_match'] = all(sha(folder/name) == digest == sha(old/name) for name, digest in current['source_sha256'].items())
        checks['normalized_PWL_exact'] = sha(old/'normalized_pwl.json') == sha(folder/'normalized_pwl.json') == current['waveform_sha256']
        before = (old/(stem+'.cir')).read_text().splitlines()
        after = (folder/(stem+'.cir')).read_text().splitlines()
        saves = [line for line in after if line.startswith('save ')]
        checks['only_save_added'] = len(saves) == 1 and before == [line for line in after if not line.startswith('save ')]
        checks['deck_hash_valid'] = sha(folder/(stem+'.cir')) == case['deck_sha256']
        count = 0
        finite = True
        with (folder/(stem+'.dat')).open() as stream:
            next(stream)
            for line in stream:
                row = list(map(float, line.split()))
                finite = finite and len(row) == 6 and all(map(math.isfinite, row))
                count += 1
        checks['numerical_endpoint'] = count > 0 and finite and abs(row[0]-20e-6) < 1e-12 and case['status'] == 'passed' and case['solver_exit'] == 0 and not case['timed_out']
        cases.append({'run_id': run_id, 'amplitude_mV': amplitude, 'checks': checks,
                      'waveform_sha256': sha(folder/(stem+'.dat')), 'saved_rows': count,
                      'period_count': case['period_count'], 'period_std_s': case['period_std_s']})
    result = {'status': 'passed' if all(all(row['checks'].values()) for row in cases) else 'failed',
              'cases': cases, 'scope': 'Completed save-policy recovery with exact historical source/PWL/models/runtime and added save statement only. No waveform parity claim against incomplete failed runs; no physical device-noise acceptance.'}
    with (HERE/'synthetic_recovery_audit_20260922_r1.json').open('x') as output:
        output.write(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
