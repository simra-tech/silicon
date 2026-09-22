#!/usr/bin/env python3
"""Compare the frozen six-point adverse runtime anchor without hiding failures."""
import argparse, hashlib, json, math
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--protocol', default='adverse_native_protocol_20260922.json')
    ap.add_argument('--output', default='adverse_native_comparison_20260922.json')
    args = ap.parse_args()
    protocol_path = HERE / args.protocol
    protocol = json.loads(protocol_path.read_text())
    manifests = [json.loads((HERE / 'runs' / protocol[k] / 'manifest.json').read_text())
                 for k in ['legacy_run', 'native_planned_run']]
    samples = [m['cases'][0] for m in manifests]
    rows = []
    differences = []
    for old, new in zip(samples[0]['children'], samples[1]['children']):
        assert old['label'] == new['label']
        assert old['fingerprint_parameters'] == new['fingerprint_parameters']
        parameters = old['fingerprint_parameters']
        for x, y in zip(old['cases'], new['cases']):
            assert x['temperature_C'] == y['temperature_C']
            name = f"{old['label']}_{x['temperature_C']:g}C"
            same_length = len(x['fingerprints']) == len(y['fingerprints']) == 2 * len(parameters)
            for i, (a, b) in enumerate(zip(x['fingerprints'], y['fingerprints'])):
                if a != b:
                    fa, fb = float(a), float(b)
                    differences.append({'point': name, 'parameter': parameters[i % len(parameters)],
                                        'phase': 'op' if i < len(parameters) else 'after_transient',
                                        'legacy': a, 'native': b, 'absolute_difference': abs(fa-fb),
                                        'ULP_difference': abs(fa-fb)/max(math.ulp(fa), math.ulp(fb))})
            rows.append({'point': name, 'both_complete': x['status'] == y['status'] == 'passed',
                         'fingerprint_length_matches': same_length,
                         'strict_fingerprint_match': same_length and x['fingerprints'] == y['fingerprints'],
                         'source_models_match': old['model_sha256'] == new['model_sha256'] and old['netlist_sha256'] == new['netlist_sha256'],
                         'deck_matches': x['deck_sha256'] == y['deck_sha256'],
                         'frequency_difference_ppm': abs(x['measurements']['freq']/y['measurements']['freq']-1)*1e6,
                         'hbt_vce_classification_match': x['hbt_vce_status'] == y['hbt_vce_status'],
                         'legacy_seconds': x['wall_seconds'], 'native_seconds': y['wall_seconds']})
    residuals = []
    for x, y in zip(samples[0]['independent_points'], samples[1]['independent_points']):
        assert (x['label'], x['temperature_C']) == (y['label'], y['temperature_C'])
        for method in ['linear', 'nominal_lut', 'reciprocal']:
            residuals.append({'label': x['label'], 'temperature_C': x['temperature_C'], 'method': method,
                              'difference_C': abs(x[method+'_error_C']-y[method+'_error_C']),
                              'classification_match': x[method+'_status'] == y[method+'_status']})
    requirements = protocol['requirements']
    checks = {'six_complete_points': len(rows) == 6 and all(r['both_complete'] for r in rows),
              'frozen_within_runtime': all(s['frozen_parameter_status'] == 'passed' for s in samples),
              'strict_fingerprints': all(r['strict_fingerprint_match'] for r in rows),
              'same_models_netlists_decks': all(r['source_models_match'] and r['deck_matches'] for r in rows),
              'frequency_limit': all(r['frequency_difference_ppm'] <= requirements['frequency_difference_ppm_max'] for r in rows),
              'residual_limit': len(residuals) == 12 and all(r['difference_C'] <= requirements['calibrated_residual_difference_C_max'] for r in residuals),
              'classifications': all(r['classification_match'] for r in residuals) and all(r['hbt_vce_classification_match'] for r in rows)}
    result = {'protocol_sha256': hashlib.sha256(protocol_path.read_bytes()).hexdigest(),
              'status': 'passed' if all(checks.values()) else 'failed', 'checks': checks,
              'points': rows, 'residuals': residuals, 'fingerprint_differences': differences,
              'separate_4ULP_diagnostic': 'passed' if all(d['ULP_difference'] <= 4 for d in differences) else 'failed',
              'limitations': protocol['limitations']}
    (HERE / args.output).write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['fingerprint_differences', 'points', 'residuals']}, indent=2))


if __name__ == '__main__':
    main()
