#!/usr/bin/env python3
"""Recompute nominal endpoint candidates from retained physical-sample manifests."""
import bisect
import csv
import hashlib
import json
import math
from pathlib import Path
from reciprocal_calibration import fit_calibration, infer_temperature

HERE = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    frozen_hashes = {
        'fixed_nominal_curve.json': 'de1aa2c61bc23feef28b01b14cb4cf33cebc0bf0e8db49dc62939e229cf237a3',
        'reciprocal_calibration.py': '925d3c2fd6b89c78bb83edb7a03e04ccebd467842ced0510188689cb972e0ea0',
        'reciprocal_candidate_frozen.json': '8c06bd17ef125b9d6b265e6530f714af88faaa844bdca0b293a819937fcbe61b'}
    for name, expected in frozen_hashes.items():
        assert digest(HERE/name) == expected, name
    curve = json.loads((HERE/'fixed_nominal_curve.json').read_text())['curve_pairs_linear_reading_C_actual_temperature_C']
    linear = list(csv.DictReader((HERE/'mc300_samples.csv').open()))
    lut = {int(row['seed']): row for row in csv.DictReader((HERE/'curvature_candidate300_samples.csv').open())}
    reciprocal = {(int(row['seed']), float(row['temperature_C'])): row
                  for row in csv.DictReader((HERE/'reciprocal_candidate300_points.csv').open())}
    assert len(linear) == 300 and {int(r['seed']) for r in linear} == set(range(51001, 51301))
    counts = dict(linear=0, lut=0, reciprocal=0)
    maxima = dict(linear=0.0, lut=0.0, reciprocal=0.0)
    manifests = {}
    runtimes = {}
    for row in linear:
        seed = int(row['seed'])
        path = HERE/'runs'/row['run_id']/'manifest.json'
        manifest = json.loads(path.read_text())
        manifests[row['run_id']] = digest(path)
        cases = manifest['cases']
        assert len(cases) == 4 and all(c['status'] == 'passed' for c in cases)
        assert all(c['solver_exit'] == 0 and not c['timed_out'] for c in cases)
        fingerprints = [c['fingerprints'] for c in cases]
        assert all(len(fp) == 10 and fp[:5] == fp[5:] == fingerprints[0][:5] for fp in fingerprints)
        freq = {c['temperature_C']: c['measurements']['freq'] for c in cases}
        assert set(freq) == {-40, 25, 100, 125} and all(math.isfinite(v) and v > 0 for v in freq.values())
        slope = (freq[100]-freq[25])/75
        a, b = fit_calibration(freq[25], freq[100])
        errors = {name: [] for name in counts}
        for temp, side in [(-40, 'cold'), (125, 'hot')]:
            value = 25+(freq[temp]-freq[25])/slope
            index = max(0, min(len(curve)-2, bisect.bisect_right([p[0] for p in curve], value)-1))
            (x0, y0), (x1, y1) = curve[index:index+2]
            errors['linear'].append(value-temp)
            errors['lut'].append(y0+(value-x0)*(y1-y0)/(x1-x0)-temp)
            errors['reciprocal'].append(infer_temperature(freq[temp], a, b)-temp)
            retained = [float(row[side+'_residual_C']),
                        float(lut[seed]['candidate_'+side+'_residual_C']),
                        float(reciprocal[(seed, temp)]['residual_C'])]
            assert all(abs(errors[name][-1]-old) < 1e-11 for name, old in zip(counts, retained))
        for name in counts:
            peak = max(map(abs, errors[name]))
            counts[name] += peak > 2
            maxima[name] = max(maxima[name], peak)
        runtimes[manifest['image_id']] = runtimes.get(manifest['image_id'], 0)+1
    result = {'status': 'passed', 'completed_samples': 300, 'completed_transients': 1200,
              'frozen_source_sha256': frozen_hashes, 'manifest_sha256': manifests,
              'retained_fingerprint_rechecks': 1200, 'samples_by_image': runtimes,
              'endpoint_failed_samples': counts, 'maximum_abs_endpoint_residual_C': maxima,
              'scope': 'Recomputed saved nominal endpoint results; no new simulations or candidate adoption. Manifest solver status and retained five-parameter repeat fingerprints checked; raw waveform and full model-parameter qualification are separate evidence.',
              'remaining': ['prospective legacy repeats 51148,51296,51111',
                            'declared calibration/supply policy adoption',
                            'actual TEMP_OUT pad sensitivity',
                            'supported adverse coverage and terminal margins',
                            'packaged calibration remains not run']}
    (HERE/'calibration_evidence_audit_20260922.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'manifest_sha256'}, indent=2))


if __name__ == '__main__':
    main()
