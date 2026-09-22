#!/usr/bin/env python3
"""Audit a declared standalone screen without dropping failed physical samples."""
import argparse
import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('campaigns', type=Path, nargs='+')
    parser.add_argument('--analysis', type=Path, required=True)
    parser.add_argument('--start-seed', type=int, required=True)
    parser.add_argument('--samples', type=int, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[5]
    analysis = json.loads(args.analysis.read_text())
    identities, samples, manifests = [], [], []
    for directory in args.campaigns:
        provenance = json.loads((directory / 'provenance.json').read_text())
        rows = json.loads((directory / 'summary.json').read_text())
        identities.append({key: provenance[key] for key in
                           ['image_id_observed_by_host', 'pdk_commit', 'ngspice_version',
                            'model_hashes', 'main_input_pair_area_scale',
                            'main_compensation_capacitance_area_scale',
                            'main_matching_linear_scale', 'matching_group']})
        identities[-1]['candidate_source_sha256'] = sha(directory / 'sense_substrate_tied.spice')
        for row in rows:
            saved = row.get('rows', {})
            samples.append({'seed': row['seed'], 'numerical_status': row['status'],
                            'valid_rows': row['valid_rows'],
                            'frozen51_parameters_four_phases': row.get('frozen_sample') is True
                            and row.get('expected_fingerprint_parameter_count') == 51
                            and row.get('fingerprint_count') == 4
                            and len(set(row.get('fingerprint_sha256', []))) == 1,
                            'returned_25C_printed_rows_exact': bool(saved)
                            and all(saved[k] == saved.get(k.replace('t0_', 't3_'))
                                    for k in saved if k.startswith('t0_'))})
        logical = directory if directory.is_absolute() else root / directory
        manifests.append({'run': str(logical.relative_to(root)),
                          'summary_sha256': sha(directory / 'summary.json'),
                          'provenance_sha256': sha(directory / 'provenance.json'),
                          'candidate_source_sha256': identities[-1]['candidate_source_sha256']})
    seeds = [sample['seed'] for sample in samples]
    checks = {'exact_declared_unique_seed_set': len(seeds) == args.samples
              and sorted(seeds) == list(range(args.start_seed, args.start_seed + args.samples)),
              'source_models_runtime_candidate_exact': all(item == identities[0] for item in identities),
              'all_numerical_complete_36_rows': all(item['numerical_status'] == 'passed'
                                                   and item['valid_rows'] == 36 for item in samples),
              'all_frozen51_parameters_four_phases': all(item['frozen51_parameters_four_phases'] for item in samples),
              'all_returned25C_printed_rows_exact': all(item['returned_25C_printed_rows_exact'] for item in samples),
              'analysis_matches_sample_set': sorted(item['seed'] for item in analysis['sample_results']) == sorted(seeds),
              'supported_CM_residual_screen': analysis.get('supported_common_mode_offset_target_failures') == 0,
              'all_diagnostic_residual_screen': analysis.get('offset_target_failures') == 0,
              'gain_screen': analysis.get('gain_target_failures') == 0}
    report = {'status': 'passed declared standalone screen' if all(checks.values()) else 'failed screen/audit',
              'checks': checks, 'identity': identities[0], 'source_runs': manifests,
              'analysis_sha256': sha(args.analysis), 'samples': samples,
              'scope': 'Standalone ideal VREF/PTAT, frozen continuous room-temperature correction. No joint-chain digital calibration/yield, physical source adoption, or full PVT claim. Failures remain in every input run.',
              'auditor_sha256': sha(Path(__file__))}
    with args.output.open('x') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    print(json.dumps({'status': report['status'], 'checks': checks}, indent=2))
    return 0 if all(checks.values()) else 1


if __name__ == '__main__':
    raise SystemExit(main())
