#!/usr/bin/env python3
"""Compare prespecified prospective tail repeats without replacing MC samples."""
import argparse
import bisect
import csv
import hashlib
import json
import math
import struct
from pathlib import Path
from reciprocal_calibration import fit_calibration, infer_temperature

HERE = Path(__file__).resolve().parent
SEEDS = [51148, 51296, 51111]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ulp(value):
    value = abs(value)
    bits = struct.unpack('>Q', struct.pack('>d', value))[0]
    return struct.unpack('>d', struct.pack('>Q', bits+1))[0]-value


def evaluate(manifest, curve):
    cases = manifest['cases']
    assert len(cases) == 4 and all(c['status'] == 'passed' and c['solver_exit'] == 0
                                   and not c['timed_out'] for c in cases)
    fingerprints = [c['fingerprints'] for c in cases]
    assert all(len(fp) == 10 and fp[:5] == fp[5:] == fingerprints[0][:5] for fp in fingerprints)
    frequencies = {c['temperature_C']: c['measurements']['freq'] for c in cases}
    assert set(frequencies) == {-40, 25, 100, 125}
    assert all(math.isfinite(f) and f > 0 for f in frequencies.values())
    slope = (frequencies[100]-frequencies[25])/75
    a, b = fit_calibration(frequencies[25], frequencies[100])
    errors = {name: {} for name in ['linear', 'lut', 'reciprocal']}
    for temp in [-40, 125]:
        value = 25+(frequencies[temp]-frequencies[25])/slope
        index = max(0, min(len(curve)-2, bisect.bisect_right([p[0] for p in curve], value)-1))
        (x0, y0), (x1, y1) = curve[index:index+2]
        errors['linear'][temp] = value-temp
        errors['lut'][temp] = y0+(value-x0)*(y1-y0)/(x1-x0)-temp
        errors['reciprocal'][temp] = infer_temperature(frequencies[temp], a, b)-temp
    return {'frequencies_Hz': frequencies, 'fingerprints': fingerprints[0][:5],
            'residuals_C': errors, 'acceptance': {name: 'passed' if max(map(abs, values.values())) <= 2 else 'failed'
                                               for name, values in errors.items()}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--legacy-prefix', required=True,
                    help='Run name prefix; each selected seed is appended without separator')
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    assert Path(args.legacy_prefix).name == args.legacy_prefix
    assert not args.output.exists()
    assert sha(HERE/'fixed_nominal_curve.json') == 'de1aa2c61bc23feef28b01b14cb4cf33cebc0bf0e8db49dc62939e229cf237a3'
    frozen = json.loads((HERE/'reciprocal_candidate_frozen.json').read_text())
    assert sha(HERE/'reciprocal_calibration.py') == frozen['equation_source_sha256']
    curve = json.loads((HERE/'fixed_nominal_curve.json').read_text())['curve_pairs_linear_reading_C_actual_temperature_C']
    native = {int(r['seed']): r['run_id'] for r in csv.DictReader((HERE/'mc300_samples.csv').open())}
    result = {'scope': 'Three prespecified prospective native samples repeated entirely on legacy runtime. '
                       'Same-runtime calibration is independently frozen for each repeat. No additional independent MC sample or global runtime adoption.',
              'selection': {51148: 'nearest prospective linear pass', 51296: 'nearest prospective linear failure',
                            51111: 'largest prospective reciprocal residual'},
              'frozen_sha256': {name: sha(HERE/name) for name in ['fixed_nominal_curve.json',
                                'reciprocal_calibration.py', 'reciprocal_candidate_frozen.json']}, 'cases': []}
    for seed in SEEDS:
        names = [native[seed], args.legacy_prefix+str(seed)]
        paths = [HERE/'runs'/name/'manifest.json' for name in names]
        row = {'seed': seed, 'native_run': names[0], 'legacy_run': names[1], 'status': 'not run'}
        if paths[1].exists():
            manifests = [json.loads(p.read_text()) for p in paths]
            try:
                values = [evaluate(m, curve) for m in manifests]
                x, y = values
                differences = [abs(float(a)-float(b))/max(ulp(float(a)), ulp(float(b)))
                               for a, b in zip(x['fingerprints'], y['fingerprints'])]
                row.update(status='completed comparison', manifest_sha256=[sha(p) for p in paths],
                           native=x, legacy=y,
                           images=[m['image_id'] for m in manifests],
                           same_pinned_pdk=all(m['pdk_commit'] == '84374023ee8b4b126bebbba67fcbada0a9c0ff0b' for m in manifests),
                           identical_models=manifests[0]['models_sha256'] == manifests[1]['models_sha256'],
                           identical_sources=manifests[0]['realized_netlist_sha256'] == manifests[1]['realized_netlist_sha256'],
                           strict_fingerprint_match='passed' if x['fingerprints'] == y['fingerprints'] else 'failed',
                           maximum_parameter_ulp_difference=max(differences),
                           separate_4ulp_diagnostic='passed' if max(differences) <= 4 else 'failed',
                           maximum_frequency_difference_ppm=max(abs(x['frequencies_Hz'][t]/y['frequencies_Hz'][t]-1)*1e6 for t in x['frequencies_Hz']),
                           maximum_residual_difference_C={name: max(abs(x['residuals_C'][name][t]-y['residuals_C'][name][t]) for t in [-40, 125]) for name in x['residuals_C']},
                           all_classifications_agree=x['acceptance'] == y['acceptance'])
            except (AssertionError, KeyError, ValueError) as exc:
                row.update(status='not run to completion', error=str(exc))
        result['cases'].append(row)
    with args.output.open('x') as output:
        output.write(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
