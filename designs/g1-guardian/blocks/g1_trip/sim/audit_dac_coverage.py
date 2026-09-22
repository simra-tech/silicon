#!/usr/bin/env python3
"""Join explicit completed DAC leaves without aliasing failed attempts."""
import argparse
import hashlib
import json
import math
from pathlib import Path

SIM = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name):
    directory = SIM / 'qualification' / name
    rows = json.loads((directory / 'summary.json').read_text())
    assert len(rows) == 1
    return directory, rows[0], json.loads((directory / 'provenance.json').read_text())


def circuit(directory, seed):
    return (directory / ('seed%d.cir' % seed)).read_text().split('.control')[0].replace(directory.name, '@RUN@')


def code_coverage(rows, start, stop):
    codes = [row[2] for row in rows]
    return len(codes) == len(set(codes)) and sorted(codes) == list(range(start, stop))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--reference', required=True)
    p.add_argument('--reference-phase', required=True, type=int)
    p.add_argument('--runs', nargs='+', required=True)
    p.add_argument('--anchor-runs', nargs='*', default=[])
    p.add_argument('--diagnostic-failed-runs', nargs='*', default=[])
    p.add_argument('--code-start', type=int, default=0)
    p.add_argument('--code-stop', type=int, default=256)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert 0 <= a.code_start < a.code_stop <= 256
    refdir, reference, refprov = load(a.reference)
    selected = [row for row in reference['rows'] if row[0] == a.reference_phase]
    assert selected and len({row[1] for row in selected}) == 1
    temp = selected[0][1]
    seed = reference['seed']
    checks = {'reference_completed': reference['status'] == 'passed',
              'reference31_frozen_across_saved_phases': reference['frozen_fingerprints'] and
              len(reference['fingerprints']) > a.reference_phase and
              all(len(fp) == 31 and fp == reference['fingerprints'][0] for fp in reference['fingerprints']),
              'unique_run_ids': len(a.runs) == len(set(a.runs))}
    cases, accepted, anchors = [], [], []
    for name in dict.fromkeys(a.runs + a.anchor_runs):
        directory, result, provenance = load(name)
        args = provenance['arguments']
        declared = list(map(int, args[args.index('--codes')+1].split(',')))
        rows = result['rows']
        local = {'numerical_completion': result['status'] == 'passed',
                 'same_seed': result['seed'] == seed,
                 'declared_rows_complete_finite': len(rows) == len(declared) and
                 [row[2] for row in rows] == declared and all(len(row) == 8 and
                 all(math.isfinite(x) for x in row) and row[0] == 0 and row[1] == temp for row in rows),
                 'circuit_before_control_exact': circuit(directory, seed) == circuit(refdir, seed),
                 'source_bytes_exact': all(digest(directory / item) == digest(refdir / item)
                                          for item in ['sense.spice', 'trip.spice', 'bgr.spice']),
                 'model_tool_pdk_solver_exact': all(provenance[key] == refprov[key] for key in
                   ['model_hashes', 'image_id', 'ngspice', 'pdk_commit', 'solver']),
                 'all31_end_parameters_exact': bool(result['fingerprints']) and result['frozen_fingerprints'] and
                 all(len(fp) == 31 and fp == reference['fingerprints'][0] for fp in result['fingerprints'])}
        overlap = [{'code': row[2], 'printed_row_exact': row[1:] == old[1:]}
                   for row in rows for old in selected if row[1:3] == old[1:3]]
        local['all_overlapping_reference_anchors_exact'] = all(x['printed_row_exact'] for x in overlap)
        anchors.extend(overlap)
        cases.append({'run': name, 'role': 'coverage' if name in a.runs else 'anchor only',
                      'checks': local, 'codes': declared, 'wall_s': result['wall_s'],
                      'summary_sha256': digest(directory / 'summary.json'),
                      'provenance_sha256': digest(directory / 'provenance.json'),
                      'deck_sha256': digest(directory / ('seed%d.cir' % seed))})
        if name in a.runs:
            accepted.extend(rows)
    checks['every_declared_code_exactly_once'] = code_coverage(accepted, a.code_start, a.code_stop)
    checks['all_leaf_contracts'] = all(all(x['checks'].values()) for x in cases)
    checks['all_three_hot_reference_anchors_exact'] = ({x['code'] for x in anchors} == {0, 127, 255}
                                                      and all(x['printed_row_exact'] for x in anchors))
    failed = []
    for name in a.diagnostic_failed_runs:
        directory, result, provenance = load(name)
        comparisons = [{'code': row[2], 'printed_row_exact': row[1:] == old[1:]}
                       for row in accepted for old in result['rows'] if row[1:3] == old[1:3]]
        failed.append({'run': name, 'preserved_status': result['status'], 'accepted_for_coverage': False,
                       'observed_end_parameter_vectors': len(result['fingerprints']),
                       'diagnostic_overlap': comparisons,
                       'codes_without_saved_original_row': [row[2] for row in accepted
                           if not any(row[1:3] == old[1:3] for old in result['rows'])],
                       'summary_sha256': digest(directory / 'summary.json')})
        checks['excluded_attempts_are_failed'] = checks.get('excluded_attempts_are_failed', True) and result['status'] != 'passed'
        checks['saved_failed_attempt_overlap_exact'] = checks.get('saved_failed_attempt_overlap_exact', True) and all(x['printed_row_exact'] for x in comparisons)
    report = {'status': 'passed' if all(checks.values()) else 'failed', 'checks': checks,
              'reference': a.reference, 'reference_phase': a.reference_phase, 'seed': seed,
              'temperature_C': temp, 'code_range_half_open': [a.code_start, a.code_stop],
              'full256_completion': all(checks.values()) and (a.code_start, a.code_stop) == (0, 256),
              'cases': cases, 'reference_anchor_comparisons': anchors, 'excluded_failed_attempts': failed,
              'rows': sorted(accepted, key=lambda row: row[2]),
              'scope': 'Explicit fresh coverage, not a repaired original run or alias. Exact printed OP rows, circuit, source/model/tool/PDK and31 observed end parameters. No unrecorded before-code vector, full temperature return, dynamic settling or statistical-yield claim.'}
    report['transfer'] = []
    if all(checks.values()) and len(accepted) > 1:
        rows = report['rows']
        for col, threshold in [(3, 'soft'), (4, 'hard')]:
            values = [row[col] for row in rows]
            lsb = (values[-1]-values[0])/(len(values)-1)
            steps = [v-u for u,v in zip(values, values[1:])]
            report['transfer'].append({'threshold': threshold, 'minimum_step_V': min(steps),
                'endpoint_lsb_V': lsb, 'min_DNL_LSB': min(steps)/lsb-1 if lsb > 0 else None,
                'max_abs_endpoint_INL_LSB': max(abs((v-values[0])/lsb-i) for i,v in enumerate(values)) if lsb > 0 else None,
                'monotonicity_status': 'passed' if min(steps) > 0 else 'failed',
                'INL_acceptance': 'not applicable: no allocated standalone limit'})
    with a.output.open('x') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['rows','cases']}, indent=2))
    raise SystemExit(0 if report['status'] == 'passed' else 1)


if __name__ == '__main__':
    main()
