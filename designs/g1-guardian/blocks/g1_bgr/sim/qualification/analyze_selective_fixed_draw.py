#!/usr/bin/env python3
"""Full-vector factorial counterfactual deltas, retaining nonlinear interactions."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
VECTORS = ['VREF_V', 'IPTAT_A', 'I_VDD_A', 'VBE_V', 'dVBE_V', 'PBIAS_V', 'PCASC_V', 'c2_V', 'vbe3_V', 'vd1_V', 'vd2_V']


def describe(delta):
    return {name: {'maximum_absolute': float(np.max(np.abs(delta[:, column]))),
                   'at_25C': float(delta[13, column]),
                   'values_in_5C_temperature_order': [float(value) for value in delta[:, column]]}
            for column, name in enumerate(VECTORS, 1)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('run_id')
    args = parser.parse_args()
    folder = HERE/'runs'/args.run_id
    path = folder/'manifest.json'
    manifest = json.loads(path.read_text())
    output = folder/'factorial_analysis.json'
    assert not output.exists()
    assert len(manifest['cases']) == 8 and not manifest.get('not_run_cases')
    assert all(row['status'] == row['diagnostic_gate_status'] == 'passed' and all(row['checks'].values()) for row in manifest['cases'])
    results = []
    for seed in [43047, 43001]:
        rows = {row['variant']: row for row in manifest['cases'] if row['seed'] == seed}
        waves = {}
        for variant, row in rows.items():
            wave = folder/(row['name']+'.dat')
            assert hashlib.sha256(wave.read_bytes()).hexdigest() == row['waveform_sha256']
            waves[variant] = np.loadtxt(str(wave), skiprows=1)
        base = waves['all_on']
        assert all(np.array_equal(wave[:, 0], base[:, 0]) for wave in waves.values())
        differences = {variant: describe(wave-base) for variant, wave in waves.items() if variant != 'all_on'}
        interaction = waves['both_nominal']-waves['qref_nominal']-waves['ptat_hbt_nominal']+base
        results.append({'seed': seed, 'tc_ppm_C': {variant: row['tc_ppm_C'] for variant, row in rows.items()},
                        'signed_endpoint_slope_ppm_C': {variant: row['signed_endpoint_slope_ppm_C'] for variant, row in rows.items()},
                        'full_vector_delta_from_all_on': differences,
                        'factorial_interaction_both_minus_qref_minus_ptat_plus_all_on': describe(interaction)})
    result = {'status': 'passed exact diagnostic gates', 'manifest_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
              'temperature_C': [float(value) for value in base[:, 0]], 'samples': results,
              'scope': 'Controlled causal sensitivity within these two fixed simulated samples only. Counterfactual nominal areas are not a realizable yield remedy. TC box and its normalization are nonlinear; full waveform interaction is preserved instead of assuming additive TC changes. No new geometry or adoption.'}
    output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'status': result['status'], 'samples': [{'seed': row['seed'], 'tc_ppm_C': row['tc_ppm_C'],
                      'VREF_interaction_max_V': row['factorial_interaction_both_minus_qref_minus_ptat_plus_all_on']['VREF_V']['maximum_absolute'],
                      'IPTAT_interaction_max_A': row['factorial_interaction_both_minus_qref_minus_ptat_plus_all_on']['IPTAT_A']['maximum_absolute']} for row in results]}, indent=2))


if __name__ == '__main__':
    main()
