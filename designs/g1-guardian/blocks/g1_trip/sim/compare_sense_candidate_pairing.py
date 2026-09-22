#!/usr/bin/env python3
"""Compare observed unchanged-subcircuit draws, not cross-geometry sample identity."""
import argparse
import hashlib
import json
from pathlib import Path

SIM = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pair', nargs=2, action='append', required=True,
                        metavar=('BASELINE_RUN', 'CANDIDATE_RUN'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    cases = []
    main_prefix = '@n.xs.xota.xm1.nsg13_hv_pmos['
    for baseline_name, candidate_name in args.pair:
        baseline, candidate = [SIM / 'qualification' / name for name in (baseline_name, candidate_name)]
        old, new = [json.loads((path / 'summary.json').read_text())[0] for path in (baseline, candidate)]
        old_prov, new_prov = [json.loads((path / 'provenance.json').read_text()) for path in (baseline, candidate)]
        before, after = dict(old['fingerprints']), dict(new['fingerprints'])
        unchanged = [key for key in before if not key.startswith(main_prefix)]
        checks = {'both_numerically_complete': old['solver_status'] == new['solver_status'] == 'passed',
                  'same_seed': old_prov['seed'] == new_prov['seed'],
                  'same27_observed_parameter_keys': len(before) == len(after) == 27 and before.keys() == after.keys(),
                  'unchanged23_observed_parameters_exact': len(unchanged) == 23 and all(before[key] == after.get(key) for key in unchanged),
                  'unchanged_BRG_TRIP_source_bytes_exact': all(sha(baseline / name) == sha(candidate / name) for name in ['bgr.spice', 'trip.spice']),
                  'same_runtime_models': all(old_prov[key] == new_prov[key] for key in
                                             ['image_id_observed_by_host', 'pdk_commit', 'ngspice_version', 'model_sha256']),
                  'sense_geometry_source_is_distinct': sha(baseline / 'sense.spice') != sha(candidate / 'sense.spice')}
        changes = [{'parameter': key, 'baseline': value, 'candidate': after.get(key)}
                   for key, value in before.items() if value != after.get(key)]
        cases.append({'seed': old_prov['seed'], 'baseline_run': baseline_name, 'candidate_run': candidate_name,
                      'checks': checks, 'observed_parameter_changes': changes,
                      'baseline_summary_sha256': sha(baseline / 'summary.json'),
                      'candidate_summary_sha256': sha(candidate / 'summary.json')})
    result = {'status': 'passed observed unchanged-subcircuit pairing' if all(all(case['checks'].values()) for case in cases) else 'failed pairing checks',
              'scope': 'Only27observed model parameters. Exact23unchanged-subcircuit observations support paired mechanism comparison; the SENSE geometry differs, so the full circuits are NOT the same physical sample. Does not establish electrical acceptance, equivalence of unobserved parameters, or candidate yield.',
              'cases': cases, 'comparator_sha256': sha(Path(__file__))}
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(result['status'])
    return 0 if all(all(case['checks'].values()) for case in cases) else 1


if __name__ == '__main__':
    raise SystemExit(main())
