#!/usr/bin/env python3
"""Descriptive candidate100 parameter/slope correlation; not causal attribution."""
import hashlib
import json
import re
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent


def main():
    output = HERE/'selective_loop16_mismatch_mechanism_20260922_r1.json'
    assert not output.exists()
    samples, provenance = [], {}
    for run_id in ['bgr_selective_loop16_mc20_20260922_r1', 'bgr_selective_loop16_mc80_20260922_r1']:
        folder = HERE/'runs'/run_id
        path = folder/'manifest.json'
        manifest = json.loads(path.read_text())
        provenance[run_id] = hashlib.sha256(path.read_bytes()).hexdigest()
        for case in manifest['cases']:
            n = len(case['fingerprint_parameters'])
            assert n == 1877 and case['status'] == 'passed' and case['fingerprints'][:n] == case['fingerprints'][n:]
            parameters = dict(zip(case['fingerprint_parameters'], map(float, case['fingerprints'][:n])))
            def group(originals, parameter, expected):
                values = [value for key, value in parameters.items() if any(re.search(r'\.'+instance+r'(?:_u\d+)?\.', key) for instance in originals) and key.endswith('['+parameter+']')]
                assert len(values) == expected
                return float(np.mean(values))
            features = {'Q1_area_mean': group(['xq56'], 'area', 16),
                        'Q1B_area_mean': group(['xq67'], 'area', 16),
                        'Q2_area_mean': group(['xq'+str(i) for i in [68, 69, 70, 71, 72, 73, 74, 76]], 'area', 128),
                        'Qref_area': group(['xq60'], 'area', 1),
                        'R_PTAT_sheet_draw_mean': group(['xr16'], 'nsmm_rsh', 16),
                        'R_VREF_sheet_draw_mean': group(['xr'+str(i) for i in range(17, 23)], 'nsmm_rsh', 6),
                        'Q1_branch_pmos_vth_mean': group(['xm38', 'xm48'], 'delvto', 32),
                        'Q2_branch_pmos_vth_mean': group(['xm39', 'xm47'], 'delvto', 32),
                        'VREF_branch_pmos_vth_mean': group(['xm43', 'xm44'], 'delvto', 2)}
            features['Q2_to_Q1_log_area_ratio'] = float(np.log(features['Q2_area_mean']/features['Q1_area_mean']))
            features['Q1_minus_Q2_pmos_vth_mean'] = features['Q1_branch_pmos_vth_mean']-features['Q2_branch_pmos_vth_mean']
            data = np.loadtxt(str(folder/(case['name']+'.dat')), skiprows=1)
            v25 = float(np.interp(25, data[:, 0], data[:, 1]))
            signed = float((data[-1, 1]-data[0, 1])/v25/165*1e6)
            samples.append({'seed': case['seed'], 'tc_ppm_C': case['tc_ppm_C'], 'signed_endpoint_slope_ppm_C': signed,
                            'features': features, 'waveform_sha256': hashlib.sha256((folder/(case['name']+'.dat')).read_bytes()).hexdigest()})
    assert sorted(row['seed'] for row in samples) == list(range(43001, 43101))
    slope = [row['signed_endpoint_slope_ppm_C'] for row in samples]
    correlations = {name: float(np.corrcoef([row['features'][name] for row in samples], slope)[0, 1]) for name in samples[0]['features']}
    result = {'status': 'descriptive analysis complete', 'source_manifest_sha256': provenance,
              'correlation_with_signed_endpoint_slope': correlations,
              'failed_seeds': [row['seed'] for row in samples if row['tc_ppm_C'] > 50], 'samples': samples,
              'scope': 'Prespecified candidate100 source/sample set. Correlation is not causal proof or model/spatial qualification. No fitted correction or retuned hardware is adopted; independent physical gate and new extraction remain required.'}
    output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({key: value for key, value in result.items() if key != 'samples'}, indent=2))


if __name__ == '__main__':
    main()
