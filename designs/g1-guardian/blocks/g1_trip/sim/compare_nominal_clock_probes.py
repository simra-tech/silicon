#!/usr/bin/env python3
"""Compare exactly two prepared nominal-clock diagnostics without reclassifying originals."""
import argparse
import hashlib
import json
from pathlib import Path
from compare_hot_residual_probes import decision

SIM = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(name):
    run = SIM / 'qualification' / name
    prep = json.loads((run / 'preparation.json').read_text())
    prov = json.loads((run / 'provenance.json').read_text())
    result, = json.loads((run / 'summary.json').read_text())
    original = SIM / 'qualification' / prep['reference_run']
    old, = json.loads((original / 'summary.json').read_text())
    checks = {
        'declared_seed_shunt_codes': prep['seed'] == result['seed'] == 71002
        and prep['shunt_V'] == result['shunt_V'] == .0245
        and prep['fixed_soft_hard_codes'] == result['fixed_soft_hard_codes'] == [136, 154],
        'prepared_deck_unchanged': sha(run / (prep['case'] + '.cir')) == prep['prepared_deck_sha256'],
        'preparation_unchanged_after_launch': sha(run / 'preparation.json') == prov['preparation_sha256'],
        'all_runtime_input_checks_passed': bool(prov['input_checks']) and all(prov['input_checks'].values()),
        'original_evidence_unchanged': sha(original / 'summary.json') == prep['reference_summary_sha256']
        and sha(original / 'provenance.json') == prep['reference_provenance_sha256'],
        'same27_observed_parameters': len(result['fingerprints']) == 27
        and result['fingerprints'] == prep['expected_observed27_parameters'] == old['fingerprints']
        and result['all27_parameters_exact'],
        'numerically_complete': result['solver_status'] == 'passed',
        'actual_and_legacy_sampling_qualified': result['wave_analysis']['sampling_status'] == 'passed',
        'source_bytes_exact': all(sha(run / f) == sha(original / f) == h for f, h in prep['source_hashes'].items()),
    }
    return {
        'run': name, 'reference_run': prep['reference_run'], 'temperature_C': result['temperature_C'],
        'checks': checks, 'nominal_clock_result': result,
        'preserved_10MHz_decisions': {channel: decision(values) for channel, values in old['both_sampled_output_V'].items()},
        'summary_sha256': sha(run / 'summary.json'), 'provenance_sha256': sha(run / 'provenance.json'),
        'preparation_sha256': sha(run / 'preparation.json'),
        'declared_difference_sha256': sha(run / 'declared_clock_difference.diff'),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runs', nargs=2, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    cases = [audit(name) for name in args.runs]
    assert sorted(c['temperature_C'] for c in cases) == [25., 125.]
    qualified = all(all(c['checks'].values()) for c in cases)
    result = {
        'status': 'passed diagnostic comparison contract' if qualified else 'failed diagnostic comparison contract',
        'cases': cases,
        'original_10MHz_residual_acceptance': 'failed; retained independently and never reclassified',
        'scope': 'Simulated two selected room/hot points at nominal5MHz with fixed10MHz-calibrated codes. '
                 'These data do not establish5MHz calibration, full temperature/guard coverage, statisticalqualification, '
                 'an isolated thermal/timing cause, or a waiver of the original10MHz residual failure.',
    }
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(result['status'])
    for case in cases:
        print(case['temperature_C'], case['nominal_clock_result']['residual_lower_point_status'], case['checks'])
    raise SystemExit(0 if qualified else 1)


if __name__ == '__main__':
    main()
