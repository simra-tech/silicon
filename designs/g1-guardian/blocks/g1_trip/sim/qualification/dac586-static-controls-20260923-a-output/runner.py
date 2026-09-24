#!/usr/bin/env python3
"""Run one prepared final-source DAC OP control, fail closed on every gate."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys

from prepare_dac586_static_controls import SIM, ROOT, REFERENCE, EXTRA, transform
from prepare_joint586_population import NODES
from run_bgr_substitution_draw_audit import read_group
from run_nominal_clock_probe import run_bounded
from analyze_bgr_substitution_outcomes import warning_inventory


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fatal_errors(log):
    return [line for line in log.splitlines() if re.search(
        r'(?i)(^error|^fatal|timestep too small|doAnalyses:|no such vector|no such parameter|'
        r'not available|cannot parse|analysis aborted|simulation interrupted)', line)]


def read_op(path, expected_header):
    raw = path.read_bytes().splitlines()
    assert len(raw) == 2, 'Expected exactly one OP row'
    tokens = [line.split() for line in raw]
    assert [token.decode('ascii') for token in tokens[0]] == expected_header, 'OP header/order mismatch'
    values = [float(token) for token in tokens[1]]
    assert len(values) == len(expected_header) and all(math.isfinite(v) for v in values)
    return tokens, values


def compare_columns(candidate, reference, columns):
    # Decoded token bytes include full numeric spelling, not raw padding widths.
    return {'decoded_column_token_bytes_exact': all(a[:columns] == b[:columns] for a, b in zip(candidate[0], reference[0])),
            'numeric_rows_exact': candidate[1][:columns] == reference[1][:columns]}


def analyze(out, prep, state):
    log = (out/'run.log').read_text()
    errors = fatal_errors(log)
    result = {'status': 'failed', 'solver_status': 'failed', 'seed': prep['seed'], 'codes': prep['codes'],
              'temperatures_C': prep['temperatures_C'], 'watchdog_status': state['status'],
              'returncode': state['returncode'], 'wall_s': state['wall_s'], 'errors': errors,
              'warnings': warning_inventory(log), 'phases': [], 'exact_comparisons': {},
              'scope': prep['scope'], 'physical_scope': prep['physical_scope']}
    complete = state['status'] == 'completed' and state['returncode'] == 0 and not errors and 'POPULATION_OP_END' in log
    result['solver_status'] = 'passed' if complete else 'failed'
    if not complete:
        return result
    try:
        ref = SIM/'qualification'/REFERENCE
        old_header = (ref/'op0.dat').read_text().splitlines()[0].split()
        assert old_header[1:] == ['v('+node+')' for node in NODES]
        original = read_op(ref/'op0.dat', old_header)
        expected = prep['expected_full_parameters']
        assert len(expected) == 11512 and len(dict(expected)) == 11512
        records = []
        for index, temp in enumerate(prep['temperatures_C']):
            observed = {tag+'_'+when: read_group(log, 'P%d_%s_%s' % (index, tag, when), queries)
                        for tag, queries in prep['groups'].items() for when in ['BEFORE', 'AFTER']}
            before = observed['NON_BGR_BEFORE']+observed['BGR_BEFORE']
            after = observed['NON_BGR_AFTER']+observed['BGR_AFTER']
            assert before == after == expected, 'Complete11512 realization changed'
            lookup = dict(before)
            anchors = [[key, lookup[key]] for key in prep['groups']['LEGACY27']]
            assert observed['LEGACY27_BEFORE'] == observed['LEGACY27_AFTER'] == anchors
            record = read_op(out/('op%d.dat' % index), old_header+EXTRA)
            records.append(record)
            result['phases'].append({'temperature_C': temp, 'parameters_before': before,
                'parameters_after': after, 'legacy27': anchors, 'op_data_sha256': sha(out/('op%d.dat' % index)),
                'op_scale_name': old_header[0], 'op_scale_not_physical_time': True,
                'observations': dict(zip(old_header[1:]+EXTRA, record[1][1:]))})
        if prep['label'] in ['output', 'repeat']:
            result['exact_comparisons']['original_first10'] = compare_columns(records[0], original, 10)
            assert all(result['exact_comparisons']['original_first10'].values()), 'Output-only original OP mismatch'
        if len(records) > 1:
            result['exact_comparisons']['return_full12'] = compare_columns(records[-1], records[0], 12)
            assert all(result['exact_comparisons']['return_full12'].values()), 'Exact returned OP mismatch'
        result['checks'] = {'full11512_reference_before_after': True, 'legacy27_exact': True,
                            'all_phase_named_finite_OP': True}
        result['status'] = 'passed'  # Last, after every assertion, including exact comparisons.
    except (AssertionError, ValueError, KeyError, IndexError, OSError) as error:
        result['errors'].append('Audit: '+str(error))
        result['status'] = 'failed'
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--preparation-sha256', required=True)
    parser.add_argument('--image-id', required=True)
    parser.add_argument('--implementation', required=True)
    parser.add_argument('--implementation-sha256', required=True)
    args = parser.parse_args()
    assert re.fullmatch(r'[a-z0-9-]+', args.run_id)
    out = SIM/'qualification'/args.run_id
    assert sha(out/'preparation.json') == args.preparation_sha256
    prep = json.loads((out/'preparation.json').read_text())
    implementation = ROOT/args.implementation
    assert sha(implementation) == args.implementation_sha256
    frozen = json.loads(implementation.read_text())
    assert frozen['preparations_sha256'][str((out/'preparation.json').relative_to(ROOT))] == args.preparation_sha256
    assert str(Path(__file__).resolve().relative_to(ROOT)) in frozen['source_sha256']
    assert all(sha(ROOT/name) == value for name, value in frozen['source_sha256'].items()), 'Implementation changed'
    assert prep['run'] == args.run_id and prep['seed'] == 73001 and prep['reference_run'] == REFERENCE
    assert not any((out/name).exists() for name in ['run.log', 'run.json', 'summary.json', 'provenance.json'])
    original = (SIM/'qualification'/REFERENCE/'population_op.cir').read_text()
    expected_deck = transform(original, REFERENCE, args.run_id, *prep['codes'], prep['temperatures_C'], prep['groups'])
    pd = Path('/foss/pdks/ihp-sg13g2')
    runtime = {'image_id_observed_by_host': args.image_id, 'pdk_commit': (pd/'COMMIT').read_text().strip(),
        'ngspice_version': subprocess.check_output(['ngspice', '--version'], universal_newlines=True),
        'model_sha256': {str(path.relative_to(pd)): sha(path) for path in (pd/'libs.tech/ngspice/models').rglob('*') if path.is_file()},
        'solver': 'sparse'}
    checks = {'deck_exact': sha(out/'dac_static.cir') == prep['deck_sha256'] and (out/'dac_static.cir').read_text() == expected_deck,
        'source_exact': all(sha(out/name) == value for name, value in prep['source_hashes'].items()),
        'inventory_exact': sha(out/'population_inventory.json') == prep['inventory_sha256'],
        'bindings_exact': all(sha(ROOT/name) == value for name, value in prep['bindings_sha256'].items()),
        'runtime_exact': runtime == prep['expected_runtime_identity']}
    provenance = {'arguments': sys.argv[1:], 'runtime_identity': runtime, 'preparation_sha256': args.preparation_sha256,
        'implementation_sha256': args.implementation_sha256,
        'input_checks': checks, 'runner_sha256': sha(Path(__file__)), 'source_hashes': prep['source_hashes'],
        'helper_sha256': {str(path.relative_to(ROOT)): sha(path) for path in
            [SIM/'prepare_dac586_static_controls.py', SIM/'prepare_joint586_population.py',
             SIM/'run_bgr_substitution_draw_audit.py', SIM/'run_nominal_clock_probe.py', SIM/'analyze_bgr_substitution_outcomes.py']}}
    (out/'runner.py').write_text(Path(__file__).read_text())
    (out/'provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
    assert all(checks.values()), 'Preflight failed; simulator not launched'
    bound = 300 if len(prep['temperatures_C']) == 1 else 1200
    assert prep['prospective_bound_s'] == bound
    with (out/'run.log').open('x') as stream:
        state = run_bounded(['ngspice', '-b', str((out/'dac_static.cir').relative_to(SIM))], stream,
            out/'run.json', bound, cwd=SIM, interval_s=1)
    result = analyze(out, prep, state)
    (out/'summary.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({key: value for key, value in result.items() if key not in ['phases', 'warnings']}, indent=2))
    raise SystemExit(0 if result['status'] == 'passed' else 1)


if __name__ == '__main__':
    main()
