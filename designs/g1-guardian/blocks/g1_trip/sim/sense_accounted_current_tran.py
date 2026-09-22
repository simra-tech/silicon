#!/usr/bin/env python3
"""Explicit rshunt-accounted current characterization; not original-wave parity."""
import argparse
import difflib
import json
from pathlib import Path
import re
import subprocess
import sys
import numpy as np
from result_directory import allocate_run
from prepare_sense_branch_current import instrument_source, instrument_deck
from run_sense_branch_current import sha, statistics
from sense_monitor_shunt_op import NODES, raw, table
from run_joint586_transients import phase_parameters
from run_nominal_clock_probe import run_bounded, analyze_wave
from wave_archive import archive_new_wave
from analyze_bgr_substitution_outcomes import warning_inventory

SIM = Path(__file__).resolve().parent
ROOT = SIM.parents[4]


def transform(original, old, new, temperature, groups):
    deck = instrument_deck(original, old, new, 'tran', temperature, groups)
    vectors = ' '.join('v('+node+')' for node in NODES)
    deck, count = re.subn(r'^(\.save .+)$', lambda m: m[1]+' '+vectors, deck, flags=re.M)
    assert count == 1 and deck.count('echo JOINT_POPULATION_TRAN_END\n') == 1
    return deck.replace('echo JOINT_POPULATION_TRAN_END\n', 'wrdata qualification/'+new+'/monitor_voltages.dat '+vectors+'\necho JOINT_POPULATION_TRAN_END\n')


def accounting(currents, volts):
    assert currents.shape == volts.shape and currents.shape[1] == 5
    assert np.isfinite(currents).all() and np.isfinite(volts).all()
    assert np.array_equal(currents[:, 0], volts[:, 0])
    shunts = volts[:, 1:]/1e12
    raw_residual = currents[:, 1]-currents[:, 2:].sum(axis=1)
    accounted = raw_residual-shunts[:, 0]
    physical = currents.copy()
    physical[:, 1] -= shunts.sum(axis=1)
    physical[:, 2:] -= shunts[:, 1:]
    return {'raw_maximum_abs_residual_A': float(np.abs(raw_residual).max()),
            'raw_1pA_status': 'passed' if np.abs(raw_residual).max() <= 1e-12 else 'failed',
            'accounted_maximum_abs_residual_A': float(np.abs(accounted).max()),
            'accounted_1pA_status': 'passed' if np.abs(accounted).max() <= 1e-12 else 'failed',
            'monitor_voltage_ranges_V': {name: [float(volts[:, i+1].min()), float(volts[:, i+1].max())] for i, name in enumerate(NODES)},
            'total_added_shunt_current_range_A': [float(shunts.sum(axis=1).min()), float(shunts.sum(axis=1).max())],
            'instrumented_current_windows': statistics(currents), 'shunt_subtracted_current_windows': statistics(physical)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run-id', required=True)
    p.add_argument('--qualified-current-op')
    p.add_argument('--image-id')
    args = p.parse_args()
    if args.qualified_current_op:
        op = SIM/'qualification'/args.qualified_current_op
        qualified, = json.loads((op/'summary.json').read_text())
        assert qualified['status'].startswith('passed')
        assert qualified['current_accounting']['accounted_1pA_status'] == 'passed'
        assert all(all(v.values()) for v in qualified['output_only_parity'].values())
        prep = json.loads((op/'preparation.json').read_text())
        ref = SIM/'qualification'/prep['reference_run']
        out = allocate_run(SIM, args.run_id)
        for name in ['sense.spice', 'trip.spice', 'bgr.spice', 'population_inventory.json']:
            (out/name).write_bytes((op/name).read_bytes())
        original = (ref/'population_transient.cir').read_text()
        deck = transform(original, ref.name, out.name, prep['temperature_C'], prep['groups'])
        (out/'probe.cir').write_text(deck)
        (out/'declared_accounted_current_difference.diff').write_text(''.join(difflib.unified_diff(original.replace(ref.name, '@RUN@').splitlines(True), deck.replace(out.name, '@RUN@').splitlines(True), fromfile='qualifiedOriginal', tofile='declaredCurrentCharacterization')))
        prep.update(run=out.name, mode='tran', qualified_accounted_op=op.name, deck_sha256=sha(out/'probe.cir'), watchdog_s=1200,
                    scope='Representative nominalprocess seed73001 CM0/shunt25mV/codes135151 at25/125C, original5MHz1.02us. Explicit zeroV current instrumentation plus measured added-node1Tohm shunts. Original18 voltage exactcomparison and raw1pA KCL remain separate pass/fail. Accounted1pA KCL/full11512+27 required. No worstcase, poweron-startup, VSS current, physical fidelity or canonical adoption claim.')
        prep['live_bindings_sha256'].update({str(f.relative_to(ROOT)): sha(f) for f in [op/'summary.json', op/'preparation.json', Path(__file__).resolve()]})
        (out/'preparation.json').write_text(json.dumps(prep, indent=2)+'\n')
        print(json.dumps({'prepared': out.name, 'deck_sha256': prep['deck_sha256']}))
        return
    out = SIM/'qualification'/args.run_id
    prep = json.loads((out/'preparation.json').read_text())
    ref = SIM/'qualification'/prep['reference_run']
    op, = json.loads((SIM/'qualification'/prep['qualified_accounted_op']/'summary.json').read_text())
    assert not (out/'run.log').exists()
    assert (out/'sense.spice').read_text() == instrument_source((ref/'sense.spice').read_text())[0]
    assert (out/'probe.cir').read_text() == transform((ref/'population_transient.cir').read_text(), ref.name, out.name, prep['temperature_C'], prep['groups'])
    assert '.option rshunt=1e12 gmin=1e-13\n' in (out/'probe.cir').read_text()
    pd = Path('/foss/pdks/ihp-sg13g2')
    runtime = {'image_id_observed_by_host': args.image_id, 'pdk_commit': (pd/'COMMIT').read_text().strip(),
               'ngspice_version': subprocess.check_output(['ngspice', '--version'], universal_newlines=True),
               'model_sha256': {str(f.relative_to(pd)): sha(f) for f in (pd/'libs.tech/ngspice/models').rglob('*') if f.is_file()}, 'solver': 'sparse'}
    checks = {'runtime': runtime == prep['expected_runtime_identity'], 'deck': sha(out/'probe.cir') == prep['deck_sha256'],
              'sources': all(sha(out/name) == value for name, value in prep['instrumented_source_hashes'].items()),
              'bindings': all(sha(ROOT/name) == value for name, value in prep['live_bindings_sha256'].items())}
    (out/'runner.py').write_text(Path(__file__).read_text())
    (out/'provenance.json').write_text(json.dumps({'arguments': sys.argv[1:], 'input_checks': checks, 'runtime_identity': runtime, 'runner_sha256': sha(Path(__file__)), 'scope': prep['scope']}, indent=2)+'\n')
    assert all(checks.values()), 'Input check failed; no simulator launch'
    with (out/'run.log').open('x') as stream:
        state = run_bounded(['ngspice', '-b', str((out/'probe.cir').relative_to(SIM))], stream, out/'run.json', 1200, cwd=SIM, interval_s=1)
    log = (out/'run.log').read_text()
    errors = [s for s in log.splitlines() if re.search(r'^Error|Timestep too small|analysis aborted|doAnalyses:|no such vector|no such parameter|not available|cannot parse', s)]
    result = dict(status='failed', runtime=state, errors=errors, warnings=warning_inventory(log), scope=prep['scope'])
    try:
        assert state['status'] == 'completed' and state['returncode'] == 0 and not errors
        section, = re.findall(r'^PHASE0_BEGIN\n(.*?)^PHASE0_END$', log, re.M | re.S)
        result['parameter_audit'] = phase_parameters(section, prep['groups'], op['parameter_audit']['parameters_before'])
        data, olddata = table(raw(out/'phase0.dat')), table(raw(ref/'phase0.dat'))
        assert data.ndim == 2 and data.shape[1] == 18 and np.isfinite(data).all() and abs(data[-1, 0]-1.02e-6) < 1e-18
        result['wave_analysis'] = analyze_wave(data[:, :13].tolist(), prep['prospective_sampling'])
        same_grid = data.shape == olddata.shape and np.array_equal(data[:, 0], olddata[:, 0])
        deltas = data[:, 1:]-np.column_stack([np.interp(data[:, 0], olddata[:, 0], olddata[:, i]) for i in range(1, 18)])
        result['original_voltage_comparison'] = {'decoded_bytes_exact': raw(out/'phase0.dat') == raw(ref/'phase0.dat'),
            'numeric_rows_exact': bool(np.array_equal(data, olddata)), 'time_grid_exact': bool(same_grid),
            'all_node_maximum_abs_delta_V_on_interpolated_reference': float(np.abs(deltas).max()),
            'last200ns_node_maximum_abs_delta_V_on_interpolated_reference': float(np.abs(deltas[data[:, 0] >= .82e-6]).max()),
            'per_column_maximum_abs_delta_V_on_interpolated_reference': np.abs(deltas).max(axis=0).tolist(),
            'scope': 'Linear reference interpolation onto instrumented time grid; not exact parity or acceptance waiver.'}
        result['strict_original_voltage_equality_status'] = 'passed' if result['original_voltage_comparison']['decoded_bytes_exact'] else 'failed'
        currents, volts = table(raw(out/'currents.dat')), table(raw(out/'monitor_voltages.dat'))
        assert np.array_equal(currents[:, 0], data[:, 0])
        result['current_accounting'] = accounting(currents, volts)
        assert result['current_accounting']['accounted_1pA_status'] == 'passed'
        result['status'] = 'passed accounted current characterization; exact original voltage and raw KCL statuses separate'
    except (AssertionError, ValueError, OSError, KeyError, IndexError) as error:
        result['analysis_error'] = repr(error)
    (out/'summary.json').write_text(json.dumps([result], indent=2)+'\n')
    for path in out.glob('*.dat'):
        archive_new_wave(path)
    print(json.dumps({k: v for k, v in result.items() if k not in ['parameter_audit', 'warnings', 'wave_analysis']}, indent=2))
    raise SystemExit(0 if result['status'].startswith('passed') else 1)


if __name__ == '__main__':
    main()
