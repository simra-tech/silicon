#!/usr/bin/env python3
"""Audit saved observations separately from the preserved failed prefix fixture."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from analyze_bgr_prefix_trajectories import initial_warning_phases
from run_bgr_substitution_transient import parameter_audit
from run_bgr_prefix_probe import analyze_prefix
from wave_archive import open_wave, wave_sha

SIM = Path(__file__).resolve().parent
EXPECTED = {'ds_pre', 'ds_kick', 'ds_sample', 'qs_sample', 'dh_pre', 'dh_kick', 'dh_sample', 'qh_sample'}


def audit_measurement_errors(errors, deck):
    parsed = [re.fullmatch(r'Error: measure\s+(\w+)\s+find\(AT\) : out of interval', line) for line in errors]
    assert len(errors) == 8 and all(parsed)
    assert {match[1] for match in parsed} == EXPECTED
    measurements = []
    for number, line in enumerate(deck.splitlines(), 1):
        if line.startswith('meas tran '):
            match = re.fullmatch(r'meas tran (\S+) find (.+) at=(\S+)', line)
            assert match and float(match[3]) > 219e-9
            measurements.append({'line': number, 'name': match[1], 'command': line, 'requested_time_s': float(match[3])})
    assert len(measurements) == 8 and {row['name'] for row in measurements} == EXPECTED
    return measurements


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run = SIM / 'qualification/joint-bgr586-hot-prefix219ns-20260922-a'
    result, = json.loads((run / 'summary.json').read_text())
    assert result['prefix_contract_status'] == 'failed' and result['watchdog_status'] == 'completed'
    state = json.loads((run / 'run.json').read_text())
    assert state['returncode'] == 0
    prep = json.loads((run / 'preparation.json').read_text())
    deck = (run / 'hard_+0mV.cir').read_text()
    measures = audit_measurement_errors(result['errors'], deck)
    log = (run / 'run.log').read_text()
    assert 'QUALIFICATION_END' in log
    baseline, = json.loads((SIM / 'qualification' / prep['required_baseline_op_run'] / 'summary.json').read_text())
    inv = json.loads((run / 'non_bgr_inventory.json').read_text())
    parameters = parameter_audit(log, prep, inv, baseline['ordered_parameter_groups']['NON_BGR_ALL'])
    assert all(parameters['checks'].values())
    with open_wave(run / 'hard_+0mV.dat') as stream:
        lines = stream.readlines()
    assert len(lines[0].split()) == 18
    wave = analyze_prefix([list(map(float, line.split())) for line in lines[1:] if line.strip()])
    markers, post_commands = [], []
    past_tran = False
    for number, line in enumerate(deck.splitlines(), 1):
        if line.startswith(('tran ', 'meas tran ', 'wrdata ', 'echo NON_BGR_', 'echo BGR_', 'echo QUALIFICATION_END')):
            markers.append({'line': number, 'command': line})
        if past_tran and line.strip() and not line.startswith('*'):
            post_commands.append(line.split()[0].lower())
        if line.startswith('tran '):
            assert not past_tran
            past_tran = True
    prohibited = {'reset', 'op', 'tran', 'alter', 'altermod', 'destroy', 'resume', 'run', 'dc', 'ac', 'noise'}
    assert not prohibited.intersection(post_commands)
    output = {'run': run.name, 'original_fixture_status': 'failed; unchanged',
              'limited_observation_status': 'passed finite saved219ns vectors and full inventories; not original fixture acceptance',
              'summary_sha256': hashlib.sha256((run / 'summary.json').read_bytes()).hexdigest(),
              'log_sha256': hashlib.sha256((run / 'run.log').read_bytes()).hexdigest(),
              'decoded_wave_sha256': wave_sha(run / 'hard_+0mV.dat'),
              'deck_sha256': hashlib.sha256(deck.encode()).hexdigest(),
              'original_errors': result['errors'], 'classified_out_of_interval_measurements': measures,
              'other_errors': [], 'ordered_command_markers': markers,
              'post_tran_command_kinds': sorted(set(post_commands)), 'post_tran_circuit_state_changing_commands': [],
              'parameter_audit': parameters, 'wave_analysis': wave, 'warning_phase_counts': initial_warning_phases(log),
              'scope': 'Read-only saved-observation audit after failed measurement fixture. No rerun, command deletion, source/settings change, late-state acceptance or physical qualification. Measurement find commands and let vectors do not alter circuit state.'}
    with args.output.open('x') as stream:
        json.dump(output, stream, indent=2)
        stream.write('\n')
    print(json.dumps({'original_fixture_status': output['original_fixture_status'], 'limited_observation_status': output['limited_observation_status'],
                      'rows': wave['rows'], 'parameter_checks': parameters['checks'], 'warning_phases': output['warning_phase_counts']}, indent=2))


if __name__ == '__main__':
    main()
