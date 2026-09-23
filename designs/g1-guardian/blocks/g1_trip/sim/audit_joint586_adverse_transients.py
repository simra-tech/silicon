#!/usr/bin/env python3
"""Independent ten-control owncorner TRANS audit, including actual-SHN parity."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
from prepare_joint586_adverse_transients import CASES, SIM, ROOT, sha
from audit_joint586_population_op import variation
from run_joint586_transients import phase_parameters
from run_joint586_adverse_transient import compare18
from run_nominal_clock_probe import analyze_wave
from wave_archive import open_wave


def decoded(path):
    with open_wave(path, 'rb') as stream:
        return stream.read()


def wave_check(blob, columns, sampling):
    lines = blob.splitlines(keepends=True)
    assert lines and len(lines[0].split()) == columns
    data = [list(map(float, line.split())) for line in lines[1:] if line.strip()]
    assert data and all(len(row) == columns and all(math.isfinite(v) for v in row) for row in data)
    assert abs(data[-1][0]-1.02e-6) < 1e-18
    assert all(b[0] >= a[0] for a, b in zip(data, data[1:]))
    return data, analyze_wave([row[:13] for row in data], sampling)


def cross_checks(rows, waves):
    vectors = {label: row['phases'][0]['parameters_before'] for label, row in rows.items()}
    changed = variation(vectors['enabled'], vectors['changed'])
    checks = dict(
        repeat11512=vectors['enabled'] == vectors['repeat'],
        repeat_wavebytes=waves['enabled'][0] == waves['repeat'][0],
        changed_all3500=all(r['primitive_count'] == r['primitives_with_changed_values'] for r in changed.values()),
        disabled11512=vectors['disabled'] == vectors['disabledchanged'],
        disabled_wavebytes=waves['disabled'][0] == waves['disabledchanged'][0],
        all_temperatures11512=all(p['parameters_before'] == p['parameters_after'] == vectors['enabled']
            for label in ['hot', 'cold', 'return'] for p in rows[label]['phases']),
        return_initial_wavebytes=waves['return'][0] == waves['enabled'][0],
        return_wavebytes=waves['return'][0] == waves['return'][3],
        return_decisions=rows['return']['phases'][0]['decisions'] == rows['return']['phases'][3]['decisions'],
        cm0_pair11512=vectors['cm0_old18'] == vectors['cm0_shn19'] == vectors['enabled'])
    # Exact output-only comparison is a separate gate; no numerical tolerance substitutes.
    try:
        projection = compare18(waves['cm0_old18'][0].splitlines(keepends=True),
                               waves['cm0_shn19'][0].splitlines(keepends=True))
        checks['cm0_original18_decoded_bytes_and_numeric_exact'] = True
    except (AssertionError, ValueError) as error:
        projection = dict(status='failed exact original18 projection', error=repr(error))
        checks['cm0_original18_decoded_bytes_and_numeric_exact'] = False
    return checks, changed, projection


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--packet', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists()
    packet = json.loads(a.packet.read_text())
    assert [r['label'] for r in packet['cases']] == [r[0] for r in CASES]
    rows, waves, receipts, statuses, errors = {}, {}, {}, {}, []
    for case in packet['cases']:
        label = case['label']; run = SIM/'qualification'/case['run']
        statuses[label] = dict(parameter_wave='not run', decision_sampling='not run')
        if not (run/'summary.json').exists():
            continue
        try:
            row, = json.loads((run/'summary.json').read_text())
            rows[label] = row
            statuses[label] = dict(parameter_wave=row['parameter_wave_contract_status'],
                                   decision_sampling=row['decision_sampling_status'])
            names = ['preparation.json', 'population_transient.cir', 'population_inventory.json',
                     'summary.json', 'provenance.json', 'runner.py', 'run.log', 'run.json']
            receipts[label] = {n: sha(run/n) for n in names}
            prep = json.loads((run/'preparation.json').read_text())
            prov = json.loads((run/'provenance.json').read_text())
            assert sha(run/'preparation.json') == case['preparation_sha256'] == prov['preparation_sha256']
            assert sha(run/'population_transient.cir') == case['deck_sha256'] == prep['deck_sha256']
            assert all(sha(ROOT/n) == v for n, v in prep['live_bindings_sha256'].items())
            assert all(sha(run/n) == v for n, v in prep['source_hashes'].items())
            assert prov['source_hashes'] == prep['source_hashes']
            assert sha(run/'population_inventory.json') == prep['inventory_sha256']
            assert prov['runtime_identity'] == prep['expected_runtime_identity'] and all(prov['input_checks'].values())
            assert sha(run/'runner.py') == prov['runner_sha256']
            assert (row['corner'], row['label'], row['seed']) == (packet['corner'], label, prep['seed'])
            op, = json.loads((ROOT/prep['op_reference']/'summary.json').read_text())
            assert op['op_qualification_status'] == 'passed'
            assert prep['expected_vectors'] == [op['phases'][i]['parameters_before'] for i in prep['op_phase_indices']]
            if row['parameter_wave_contract_status'] != 'passed':
                continue
            state = json.loads((run/'run.json').read_text())
            assert state == row['runtime'] and state['status'] == 'completed' and state['returncode'] == 0
            assert not row['errors'] and len(row['phases']) == len(prep['temperatures_C'])
            log = (run/'run.log').read_text()
            assert 'JOINT_POPULATION_TRAN_END' in log
            waves[label] = []
            for i, phase in enumerate(row['phases']):
                section, = re.findall(r'^PHASE%d_BEGIN\n(.*?)^PHASE%d_END$' % (i, i), log, re.M | re.S)
                params = phase_parameters(section, prep['groups'], prep['expected_vectors'][i])
                assert all(phase[k] == v for k, v in params.items())
                assert phase['temperature_C'] == prep['temperatures_C'][i]
                blob = decoded(run/('phase%d.dat' % i))
                assert hashlib.sha256(blob).hexdigest() == phase['decoded_wave_sha256']
                data, analysis = wave_check(blob, prep['columns'], prep['prospective_sampling'])
                assert len(data) == phase['wave_rows'] and analysis == phase['wave_analysis']
                assert phase['decisions'] == {k: v['measured_edge_decision'] for k, v in analysis['comparators'].items()}
                if prep['columns'] == 19:
                    mean = [(r[17]+r[18])/2 for r in data]; diff = [r[17]-r[18] for r in data]
                    observed = dict(mean_common_mode_minmax_V=[min(mean), max(mean)],
                        differential_minmax_V=[min(diff), max(diff)], shn_minmax_V=[min(r[18] for r in data), max(r[18] for r in data)])
                    assert observed == phase['actual_input_observation']
                    assert max(abs(v-prep['common_mode_V']) for v in mean) < 1e-12
                    assert max(abs(v-.025) for v in diff) < 1e-12
                waves[label].append(blob)
            actual_sampling = all(r['wave_analysis']['sampling_status'] == 'passed' for r in row['phases'])
            assert (row['decision_sampling_status'] == 'passed') == actual_sampling
        except (AssertionError, ValueError, OSError, KeyError, IndexError) as error:
            errors.append(dict(label=label, error=repr(error)))
    result = dict(status='failed or incomplete owncorner TRANS qualification', corner=packet['corner'],
        packet_sha256=sha(a.packet), contract_sha256=packet['contract_sha256'],
        op_audit_sha256=packet['op_audit_sha256'], individual_controls=statuses,
        receipts_sha256=receipts, audit_errors=errors, checks={},
        population_status='not run; qualification does not launch or qualify any calibration cohort',
        scope='All ten controls retained. Exact failures remain exact failures; no consistency-bound substitution. Model-level unchanged sources, not new physical qualification.')
    if len(rows) == 10 and not errors and all(v['parameter_wave'] == 'passed' for v in statuses.values()):
        checks, changed, projection = cross_checks(rows, waves)
        checks['all_actual_legacy_decision_sampling'] = all(v['decision_sampling'] == 'passed' for v in statuses.values())
        result.update(checks=checks, changed_seed_variation=changed, original18_projection=projection,
                      actual_input_observation=rows['cm0_shn19']['phases'][0]['actual_input_observation'],
                      independent_temperature_wave_comparisons=dict(
                          scope='Separate observed equality; not an added qualification criterion',
                          hot_exact=waves['hot'][0] == waves['return'][1],
                          cold_exact=waves['cold'][0] == waves['return'][2]))
        result['status'] = 'passed strict owncorner TRANS qualification' if all(checks.values()) else 'failed exact owncorner TRANS cross-control gate'
    with a.output.open('x') as stream:
        json.dump(result, stream, indent=2); stream.write('\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'receipts_sha256'}, indent=2))
    raise SystemExit(0 if result['status'] == 'passed strict owncorner TRANS qualification' else 1)


if __name__ == '__main__':
    main()
