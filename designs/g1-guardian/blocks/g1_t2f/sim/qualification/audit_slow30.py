#!/usr/bin/env python3
"""Audit the exact30 completed slow-corner samples and unchanged calibration."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
from reciprocal_calibration import fit_calibration, infer_temperature
from run_adverse_calibration import nominal_lut

HERE = Path(__file__).resolve().parent
NAMES = ['t2f_adverse_slow_transient_pilot_20260922_01', 't2f-slow-adverse-s51902-20260922-a',
         't2f-slow-adverse-s51903-20260922-a']+['t2f-slow-adverse30-b%d-20260922-a' % i for i in [1, 2, 3]]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    samples, reference, distinct = [], None, set()
    for name in NAMES:
        parent = HERE/'runs'/name
        manifest = json.loads((parent/'manifest.json').read_text())
        assert manifest['corner'] == 'slow' and not manifest['op_only']
        assert [s['seed'] for s in manifest['cases']] == manifest['expected_seeds']
        for sample in manifest['cases']:
            assert sample['status'] == sample['frozen_parameter_status'] == 'passed'
            assert [c['label'] for c in sample['children']] == ['cal', 'low', 'high']
            vector, leaves, frequencies = None, [], {}
            for child in sample['children']:
                run = HERE/'runs'/child['run_id']
                cm = json.loads((run/'manifest.json').read_text())
                assert cm['cases'] == child['cases'] and cm['seed'] == sample['seed'] and cm['mismatch'] and not cm['op_only']
                identity = {k: cm[k] for k in ['image_id', 'pdk_commit', 'ngspice', 'input_sha256', 'realized_netlist_sha256', 'models_sha256', 'fingerprint_parameters']}
                if reference is None:
                    reference = identity
                assert identity == reference and len(cm['fingerprint_parameters']) == 580
                assert cm['pdk_commit'] == '84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
                assert cm['image_id'] == 'sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0'
                assert all(sha(run/k) == v for k, v in cm['realized_netlist_sha256'].items())
                temperatures = [25, 100] if child['label'] == 'cal' else [-40, 125]
                rails = {'cal': (3.3, 1.2), 'low': (3.0, 1.08), 'high': (3.6, 1.32)}[child['label']]
                assert [c['temperature_C'] for c in cm['cases']] == temperatures
                for case in cm['cases']:
                    assert case['status'] == 'passed' and not case['timed_out'] and case['solver_exit'] == 0
                    assert (case['vdd'], case['vdd12']) == rails
                    assert [case[k] for k in ['hbt', 'mos', 'res', 'cap']] == ['wcs', 'ss', 'wcs', 'wcs']
                    log = (run/(case['name']+'.log')).read_text()
                    fp = re.findall(r'@[^\s]+\s*=\s*([-+0-9.eE]+)', log)
                    assert fp == case['fingerprints'] and len(fp) == 1160 and fp[:580] == fp[580:]
                    if vector is None:
                        vector = fp[:580]
                    assert fp[:580] == vector
                    deck = run/(case['name']+'.cir')
                    assert sha(deck) == case['deck_sha256']
                    wave = run/(case['name']+'.dat')
                    lines = wave.read_text().splitlines()
                    assert len(lines[0].split()) == 13
                    data = [list(map(float, line.split())) for line in lines[1:] if line.strip()]
                    assert data and all(len(r) == 13 and all(math.isfinite(v) for v in r) for r in data)
                    assert abs(data[-1][0]-32e-6) < 1e-12
                    vce = max(abs(r[i]-r[j]) for r in data for i, j in [(7, 8), (9, 8), (10, 11), (12, 11)])
                    assert vce == case['t2f_hbt_vce_max_V'] and (vce <= 1.6) == (case['hbt_vce_status'] == 'passed')
                    frequencies[child['label'], case['temperature_C']] = case['measurements']['freq']
                    leaves.append({'run': run.name, 'case': case['name'], 'wall_s': case['wall_seconds'], 'deck_sha256': sha(deck),
                                   'wave_sha256': sha(wave), 'wave_rows': len(data), 'manifest_sha256': sha(run/'manifest.json'),
                                   'log_sha256': sha(run/(case['name']+'.log')), 'hbt_vce_status': case['hbt_vce_status']})
            assert len(leaves) == 6
            distinct.add(tuple(vector))
            f25, f100 = frequencies['cal', 25], frequencies['cal', 100]
            aa, bb = fit_calibration(f25, f100)
            assert len(sample['independent_points']) == 4
            for point in sample['independent_points']:
                temp = point['temperature_C']
                frequency = frequencies[point['label'], temp]
                linear = 25+(frequency-f25)/((f100-f25)/75)
                errors = {'linear': linear-temp, 'nominal_lut': nominal_lut(linear)-temp,
                          'reciprocal': infer_temperature(frequency, aa, bb)-temp}
                assert point['frequency_Hz'] == frequency
                for method, error in errors.items():
                    assert error == point[method+'_error_C']
                    assert (abs(error) <= 2) == (point[method+'_status'] == 'passed')
            samples.append({'seed': sample['seed'], 'parent': name, 'manifest_sha256': sha(parent/'manifest.json'),
                            'leaves': leaves, 'independent_points': sample['independent_points'],
                            'parameter_vector_sha256': hashlib.sha256(json.dumps(vector).encode()).hexdigest()})
    assert sorted(s['seed'] for s in samples) == list(range(51901, 51931)) and len(distinct) == 30
    methods = {method: {'failed_samples': sum(any(p[method+'_status'] == 'failed' for p in s['independent_points']) for s in samples),
                        'failed_points': sum(p[method+'_status'] == 'failed' for s in samples for p in s['independent_points']),
                        'maximum_abs_error_C': max(abs(p[method+'_error_C']) for s in samples for p in s['independent_points'])}
               for method in ['linear', 'nominal_lut', 'reciprocal']}
    result = {'numerical_parameter_source_runtime_wave_status': 'passed', 'attempted_samples': 30, 'completed_samples': 30,
              'completed_transients': 180, 'distinct_580_parameter_vectors': 30, 'calibration_methods': methods,
              'total_core_seconds': sum(leaf['wall_s'] for s in samples for leaf in s['leaves']),
              'source_runtime_identity': reference, 'samples': samples,
              'scope': 'Fixed slow ss/wcs process population, original BGR/T2F sources (NOT586). Per-seed25/100C nominal-rail calibration frozen at low/high rails and-40/125C. Original linear2C criterion unchanged; LUT/reciprocal candidates unadopted. No packaged/physical qualification or yield claim. Original numerical/model/roundoff failures outside this cohort remain retained.'}
    with a.output.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ['samples', 'source_runtime_identity']}, indent=2))


if __name__ == '__main__':
    main()
