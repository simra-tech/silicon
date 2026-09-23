#!/usr/bin/env python3
"""Saved-evidence arithmetic only; never a physical noise acceptance gate."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
INPUTS = {
    'blocks/g1_t2f/INTERFACE.md': '2515a041f181b0fc52bd4eff1e5515890eb7078626ca292dfac477b0508f182d',
    'blocks/g1_ctrl/rtl/g1_digital_top.v': '42430b79ddf649d832993aca1cf3c8a548afc97383c59a793cf70b972c8256ac',
    'specification/G1_TOP_LEVEL_SPECIFICATION.md': '35fe6175d12d970ee792c92ad879a2f98797961cd610e5d0055b59a69b9522e1',
    'blocks/g1_sense/reports/loaded-noise-evidence-20260923-r2/r3/summary.json': '12da9cf4086e7bebc247e241c855d7d5018979396cec422aa3c76e3108c34656',
    'blocks/g1_sense/reports/rz100-partial-field-evidence-20260923-r1/sense-rz100-followthrough-20260923-r1/nominal/noise/summary.json.gz': 'd834d21a0302e5b29d58371b6b474afad2b5086585c58b0329c99cab495655d1',
    'blocks/g1_bgr/sim/qualification/portable_evidence/required-ac-pvt-20260922/bgr586-required-ac-noise-nominal-20260922-a/summary.json': 'faeee5f0f79691ae7e0090d04022ef246b1ba6646e3ec4d7989f1c6628d65c0d',
    'blocks/g1_t2f/sim/qualification/runs/t2f_synthetic_jitter_20260922_01/analysis.json': '75e874aa1cbe220834038fab9a23490a8ec25a713815846873cd29c5a22834ce',
    'blocks/g1_osc/sim/qualification/runs/osc_synthetic_save0_20260922_r1/analysis.json': '5dff0650cc69bac51c5f45ee0cfede76a91917394c261b8c735b260db941c194',
    'blocks/g1_osc/sim/qualification/runs/osc_synthetic_save15_20260922_r1/analysis.json': 'dca55df5856a2072563c73b4ee1ff223d32c0d6d7cff4d6209461dc0a69da829',
}


def positive(value):
    if not math.isfinite(value) or value <= 0:
        raise ValueError('positive finite value required')
    return value


def one_count_temperature_step(duration_s, slope_Hz_per_C):
    return 1.0 / (positive(duration_s) * positive(slope_Hz_per_C))


def band_upper(row):
    values = [row[k] for k in ['upper_Hz', 'requested_upper_Hz'] if k in row]
    if not values or any(v != values[0] for v in values):
        raise ValueError('missing or conflicting band endpoint')
    return positive(values[0])


def same_plane_pair_rms(a, b, correlation, disjoint_sources):
    """Illustrative covariance algebra, NOT applied to incompatible fixtures."""
    if not disjoint_sources:
        raise ValueError('overlapping sources cannot be counted twice')
    if not math.isfinite(correlation) or abs(correlation) > 1:
        raise ValueError('invalid correlation')
    positive(a); positive(b)
    return math.sqrt(max(0.0, a*a + b*b + 2*correlation*a*b))


def self_test():
    assert band_upper({'upper_Hz': 2e6}) == band_upper({'requested_upper_Hz': 2e6})
    try:
        band_upper({'upper_Hz': 2e6, 'requested_upper_Hz': 1e7})
    except ValueError:
        pass
    else:
        raise AssertionError('conflicting endpoints accepted')
    assert math.isclose(one_count_temperature_step(10e-6, 5200), 19.23076923076923)
    assert math.isclose(one_count_temperature_step(1/(2*5200), 5200), 2)
    assert math.isclose(same_plane_pair_rms(3, 4, 0, True), 5)
    assert same_plane_pair_rms(3, 4, 1, True) == 7
    assert same_plane_pair_rms(3, 4, -1, True) == 1
    for args in [(3, 4, 0, False), (3, 4, 1.1, True), (float('nan'), 4, 0, True)]:
        try:
            same_plane_pair_rms(*args)
        except ValueError:
            pass
        else:
            raise AssertionError('invalid budget input accepted')
    for duration in [0, -1, float('nan')]:
        try:
            one_count_temperature_step(duration, 5200)
        except ValueError:
            pass
        else:
            raise AssertionError('invalid window accepted')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--test-only', action='store_true')
    args = parser.parse_args()
    self_test()
    if args.test_only:
        print('PASS arithmetic, correlation, duplicate-source and invalid-input controls')
        return
    loaded = {}
    for name, expected in INPUTS.items():
        raw = (BASE/name).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == expected, name
        if name.endswith('.json.gz'):
            raw = gzip.decompress(raw)
        if '.json' in name:
            loaded[name] = json.loads(raw)
    senses = []
    for name, data in loaded.items():
        if 'g1_sense' not in name:
            continue
        bands = [b for b in data['bands'] if b['assumed_boxcar_s'] == 0 and band_upper(b) in (2e6, 1e7)]
        assert len(bands) == 2
        senses.append({'evidence': name, 'unfiltered_finite_bands': bands,
                       'summed_with_standalone_BGR': False})
        for b in bands:
            positive(b['input_stimulus_referred_rms_V'])
            positive(b['output_rms_V'])
    synthetic = {}
    for block in ['t2f', 'osc']:
        cases = [row for name, data in loaded.items() if '/g1_'+block+'/' in name for row in data['cases']]
        assert sorted(row['requested_rms_mV'] for row in cases) == [0, 1, 5]
        assert all(row['status'] == 'passed' for row in cases)
        synthetic[block] = [{'amplitude_mV': row['requested_rms_mV'], 'period_std_s': positive(row['period_std_s']),
                             'window_start_s': row['measurement_window_start_s'],
                             'window_end_s': row['measurement_window_end_s']} for row in cases]
        for row in cases:
            for window in row['finite_counter_windows'].values():
                assert math.isclose(window['one_count_frequency_step_Hz'], 1/positive(window['window_duration_s']))
    bgr = [data[0] for name, data in loaded.items() if '/g1_bgr/' in name]
    assert len(bgr) == 1 and bgr[0]['status'] == 'passed'
    print(json.dumps({
        'status': 'passed saved-evidence bindings and conditional arithmetic only',
        'physical_noise_acceptance': 'not run; allocation, correlation and sampling model unresolved',
        'inputs_sha256': INPUTS, 'sense_finite_band_evidence': senses,
        'standalone_BGR_rms_V_not_added_to_loaded_SENSE': positive(bgr[0]['noise_1Hz_10MHz_rms_V']),
        'synthetic_external_perturbation_only': synthetic,
        'nominal_slope_Hz_per_C': 5200,
        'fixed_integer_count_window_sensitivity': [
            {'window_s': w, 'one_count_step_C': one_count_temperature_step(w, 5200)} for w in [1e-6, 5e-6, 10e-6]],
        'one_count_envelope_at_most_2C_minimum_window_s': 1/(2*5200),
        'minimum_window_scope': 'ideal fixed-window count model, nominal slope only, zero allowance for other errors; not selected hardware gate time',
        'new_simulations': 'not run', 'hardware_measurements': 'not run',
    }, indent=2))


if __name__ == '__main__':
    main()
