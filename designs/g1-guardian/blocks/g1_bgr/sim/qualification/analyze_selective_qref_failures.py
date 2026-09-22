#!/usr/bin/env python3
"""Exact-draw Qref intervention closure over all seven observed TC failures."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from analyze_selective_fixed_draw import describe

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    original = HERE/'runs/bgr_selective_fixed_draw_20260922_r1'
    extension = HERE/'runs/bgr_selective_qref_remaining6_20260922_r1'
    files = {43047: original, **{seed: extension for seed in [43026, 43039, 43056, 43058, 43068, 43077]}}
    results, hashes = [], {}
    reference = None
    for seed, folder in sorted(files.items()):
        path = folder/'manifest.json'
        manifest = json.loads(path.read_text())
        hashes[folder.name] = sha(path)
        if reference is None:
            reference = manifest
        assert all(manifest[key] == reference[key] for key in ['image_id', 'ngspice', 'pdk_commit', 'source_sha256', 'model_sha256', 'osdi_sha256'])
        assert all(sha(folder/name) == digest for name, digest in manifest['source_sha256'].items())
        rows = {row['variant']: row for row in manifest['cases'] if row['seed'] == seed}
        waves = {}
        for variant in ['all_on', 'qref_nominal']:
            row = rows[variant]
            assert row['status'] == row['diagnostic_gate_status'] == 'passed' and all(row['checks'].values())
            assert sha(folder/(row['name']+'.cir')) == row['deck_sha256']
            wavepath = folder/(row['name']+'.dat')
            assert sha(wavepath) == row['waveform_sha256']
            waves[variant] = np.loadtxt(str(wavepath), skiprows=1)
        before, after = rows['all_on'], rows['qref_nominal']
        assert before['tc_ppm_C'] > 50
        results.append({'seed': seed, 'original_tc_ppm_C': before['tc_ppm_C'], 'qref_nominal_tc_ppm_C': after['tc_ppm_C'],
                        'original_status': 'failed', 'qref_ideal_diagnostic_tc_status': 'passed' if after['tc_ppm_C'] <= 50 else 'failed',
                        'signed_slope_before_after_ppm_C': [before['signed_endpoint_slope_ppm_C'], after['signed_endpoint_slope_ppm_C']],
                        'full_vector_delta_qref_minus_original': describe(waves['qref_nominal']-waves['all_on'])})
    result = {'diagnostic_identity_status': 'passed', 'manifest_sha256': hashes,
              'expected_original_failures': 7, 'evaluated_original_failures': len(results),
              'remaining_failures_with_ideal_qref': sum(row['qref_ideal_diagnostic_tc_status'] == 'failed' for row in results),
              'samples': results,
              'scope': 'All seven observed selective16 candidate100 TC failures, exact-draw ideal Qref-area intervention only. Not manufacturable averaging, new geometry or yield; passing control remains original43001. Every original failure is preserved.'}
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({key: value for key, value in result.items() if key != 'samples'}, indent=2))
    for row in results:
        print(json.dumps({key: value for key, value in row.items() if key != 'full_vector_delta_qref_minus_original'}))


if __name__ == '__main__':
    main()
