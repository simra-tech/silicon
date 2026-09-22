#!/usr/bin/env python3
"""Qualify selected bounded DC chunks against the archived reset-sequence anchor."""
import argparse
import hashlib
import json
from pathlib import Path

SIM = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference', required=True)
    parser.add_argument('--reference-phase', type=int, default=0,
                        help='Explicit saved reference temperature phase; default0 retains initial25C')
    parser.add_argument('--candidates', required=True, nargs='+')
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    reference = SIM / 'qualification' / args.reference
    original = json.loads((reference / 'summary.json').read_text())[0]
    original_provenance = json.loads((reference / 'provenance.json').read_text())
    reference_rows = [row for row in original['rows'] if row[0] == args.reference_phase]
    assert reference_rows, 'Requested reference temperature phase does not exist'
    reference_temperatures = {row[1] for row in reference_rows}
    assert len(reference_temperatures) == 1
    seed = original['seed']
    original_circuit = (reference / ('seed'+str(seed)+'.cir')).read_text().split('.control')[0].replace(reference.name, '@RUN@')
    cases = []
    for name in args.candidates:
        directory = SIM / 'qualification' / name
        rows = json.loads((directory / 'summary.json').read_text())
        assert len(rows) == 1
        candidate = rows[0]
        provenance = json.loads((directory / 'provenance.json').read_text())
        circuit = (directory / ('seed'+str(seed)+'.cir')).read_text().split('.control')[0].replace(name, '@RUN@')
        checks = {'both_numerically_complete': original['status'] == candidate['status'] == 'passed',
                  'reference_all31_frozen_across_saved_phases': original['frozen_fingerprints']
                  and len(original['fingerprints']) > args.reference_phase
                  and all(len(fp) == 31 and fp == original['fingerprints'][0] for fp in original['fingerprints']),
                  'same_seed': candidate['seed'] == seed,
                  'selected_temperature_phase_matches': {row[1] for row in candidate['rows']} == reference_temperatures,
                  'circuit_before_control_exact': circuit == original_circuit,
                  'sources_exact': all(sha(reference / item) == sha(directory / item) for item in ['sense.spice', 'trip.spice', 'bgr.spice']),
                  'model_image_engine_pdk_solver_exact': all(provenance[key] == original_provenance[key] for key in ['model_hashes', 'image_id', 'ngspice', 'pdk_commit', 'solver']),
                  'all31_sampled_parameters_exact': candidate['frozen_fingerprints'] and len(candidate['fingerprints'][0]) == 31 and all(fp == original['fingerprints'][0] for fp in candidate['fingerprints'])}
        comparisons = []
        for row in candidate['rows']:
            matching = [old for old in reference_rows if old[1:3] == row[1:3]]
            if matching:
                comparisons.append({'temperature_C': row[1], 'code': row[2], 'printed_row_exact': row[1:] == matching[0][1:], 'difference': [x-y for x,y in zip(row[3:],matching[0][3:])]})
        checks['overlapping_anchor_rows_exact'] = bool(comparisons) and all(row['printed_row_exact'] for row in comparisons)
        cases.append({'run': name, 'checks': checks, 'anchor_comparisons': comparisons,
                      'completed_codes': [row[2] for row in candidate['rows']], 'wall_s': candidate['wall_s']})
    codes = {row['code'] for case in cases for row in case['anchor_comparisons']}
    report = {'status': 'passed' if codes == {0,127,255} and all(all(case['checks'].values()) for case in cases) else 'failed',
              'reference': args.reference, 'reference_phase': args.reference_phase,
              'temperature_C': next(iter(reference_temperatures)), 'cases': cases,
              'scope': 'Selected explicit-temperature code0/127/255 OP anchors in bounded code chunks; each completed code list is explicit. Frozen31parameter sample and source/model/solver identity. Echo precision inherited. No all256code monotonicity, full temperature-return transfer, analog dynamics or yield claim.'}
    with args.output.open('x') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report['status'] == 'passed' else 1)


if __name__ == '__main__':
    main()
