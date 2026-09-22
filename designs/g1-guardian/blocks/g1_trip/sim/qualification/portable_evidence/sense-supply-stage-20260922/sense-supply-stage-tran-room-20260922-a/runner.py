#!/usr/bin/env python3
"""Bounded copied-source supply-stage OP/TRANS with measured shunt accounting."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import numpy as np
from prepare_sense_supply_stages import instrument, transform
from run_sense_branch_current import sha, statistics
from sense_monitor_shunt_op import raw, table
from run_bgr_substitution_draw_audit import read_group
from run_joint586_transients import phase_parameters
from run_nominal_clock_probe import run_bounded, analyze_wave
from analyze_bgr_substitution_outcomes import warning_inventory
from wave_archive import archive_new_wave

SIM = Path(__file__).resolve().parent
ROOT = SIM.parents[4]


def windows(times, values):
    result = {}
    for name, lower in [('complete', 0), ('last200ns', .82e-6)]:
        mask = times >= lower
        if not mask.any():
            continue
        tx, y = times[mask], values[mask]
        duration = tx[-1]-tx[0]
        avg = np.sum((y[1:]+y[:-1])*.5*np.diff(tx))/duration if duration else y[0]
        result[name] = dict(mean_A=float(avg), minimum_A=float(y.min()), maximum_A=float(y.max()),
                            sampled_abs_peak_A=float(np.abs(y).max()), first_s=float(tx[0]), last_s=float(tx[-1]))
    return result


def account(currents, monitors, stages, instances):
    assert currents.shape[1] == monitors.shape[1] == 5 and stages.shape[1] == 23
    assert np.isfinite(currents).all() and np.isfinite(monitors).all() and np.isfinite(stages).all()
    assert np.array_equal(currents[:, 0], monitors[:, 0]) and np.array_equal(currents[:, 0], stages[:, 0])
    times = currents[:, 0]
    measured, volts = stages[:, 1:12], stages[:, 12:]
    corrected = measured-volts/1e12
    macro_columns = {'xota': 2, 'xbuf': 3, 'xref': 4}
    for i, row in enumerate(instances):
        expected = monitors[:, macro_columns[row['macro']]] if row['rail'] == 'vdd' else np.zeros(len(times))
        assert np.max(np.abs(volts[:, i]-expected)) <= 1e-15, 'Monitor supply voltage differs from declared ideal rail'
    raw_kcl = currents[:, 1]-currents[:, 2:].sum(axis=1)
    accounted = raw_kcl-monitors[:, 1]/1e12
    physical_macro = currents.copy()
    extra_vdd = np.zeros(len(times))
    for macro, column in macro_columns.items():
        indices = [i for i, row in enumerate(instances) if row['macro'] == macro and row['rail'] == 'vdd']
        extra = volts[:, indices].sum(axis=1)/1e12
        extra_vdd += extra
        physical_macro[:, column] -= monitors[:, column]/1e12+extra
    physical_macro[:, 1] -= monitors[:, 1:].sum(axis=1)/1e12+extra_vdd
    records = []
    for i, row in enumerate(instances):
        records.append(dict(row, measured_current_windows=windows(times, measured[:, i]),
                            shunt_subtracted_entering_device_windows=windows(times, corrected[:, i]),
                            injection_into_supply_wire_windows=windows(times, -corrected[:, i]),
                            monitor_voltage_range_V=[float(volts[:, i].min()), float(volts[:, i].max())],
                            monitor_shunt_current_range_A=[float(volts[:, i].min()/1e12), float(volts[:, i].max()/1e12)]))
    remaining = {}
    for macro in ['xbuf', 'xref']:
        indices = [i for i, row in enumerate(instances) if row['macro'] == macro and row['rail'] == 'vdd']
        remainder = physical_macro[:, macro_columns[macro]]-corrected[:, indices].sum(axis=1)
        remaining[macro] = windows(times, remainder)
    return {'raw_kcl_maximum_abs_residual_A': float(np.abs(raw_kcl).max()), 'raw_kcl_1pA_status': 'passed' if np.abs(raw_kcl).max() <= 1e-12 else 'failed',
            'accounted_kcl_maximum_abs_residual_A': float(np.abs(accounted).max()), 'accounted_kcl_1pA_status': 'passed' if np.abs(accounted).max() <= 1e-12 else 'failed',
            'all_added_vdd_node_shunt_current_range_A': [float((monitors[:, 1:].sum(axis=1)/1e12+extra_vdd).min()), float((monitors[:, 1:].sum(axis=1)/1e12+extra_vdd).max())],
            'macro_shunt_subtracted_current_windows': statistics(physical_macro), 'stages': records, 'remaining_buffer_vdd_upper_bar_windows': remaining,
            'boundary_accounting': 'TopSENSEmonitor shunt outside3branchmeters; eachbranchmonitor plus selecteddeviceVDDmonitor shunts inside itsbranch. Subtract all12addedVDDnodes fromtotal, ownbranch+selectedownVDDnodes fromeachmacro, and ownmonitor shunt fromeachstage. ThreeaddedVSSnodes measuredzero. Positive stagecurrent entersdevice; negative is injectionintowire. Remainingbufferbar is accountedmacroVDD minus both selectedstageVDDcurrents.'}


def compare(newraw, reference):
    oldraw = raw(reference)
    new, old = table(newraw), table(oldraw)
    assert new.ndim == old.ndim == 2 and new.shape[1] == old.shape[1] and np.isfinite(new).all()
    interpolation = np.column_stack([np.interp(new[:, 0], old[:, 0], old[:, i]) for i in range(1, new.shape[1])])
    return {'decoded_bytes_exact': newraw == oldraw, 'numeric_rows_exact': bool(np.array_equal(new, old)),
            'time_grid_exact': new.shape == old.shape and bool(np.array_equal(new[:, 0], old[:, 0])),
            'maximum_abs_voltage_delta_V_reference_interpolated': float(np.max(np.abs(new[:, 1:]-interpolation))),
            'scope': 'Linear reference interpolation at new times is observational, not an exactcomparison waiver.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run-id', required=True)
    p.add_argument('--image-id', required=True)
    args = p.parse_args()
    out = SIM/'qualification'/args.run_id
    prep = json.loads((out/'preparation.json').read_text())
    ref = SIM/'qualification'/prep['reference_run']
    reference, = json.loads((ref/'summary.json').read_text())
    assert not (out/'run.log').exists()
    expected_source, changes, instances = instrument((ref/'sense.spice').read_text())
    assert expected_source == (out/'sense.spice').read_text() and changes == prep['source_changes'] and instances == prep['stage_instances']
    assert (out/'probe.cir').read_text() == transform((ref/'probe.cir').read_text(), ref.name, out.name, instances)
    assert '.option rshunt=1e12 gmin=1e-13\n' in (out/'probe.cir').read_text()
    pd = Path('/foss/pdks/ihp-sg13g2')
    runtime = {'image_id_observed_by_host': args.image_id, 'pdk_commit': (pd/'COMMIT').read_text().strip(),
               'ngspice_version': subprocess.check_output(['ngspice', '--version'], universal_newlines=True),
               'model_sha256': {str(f.relative_to(pd)): sha(f) for f in (pd/'libs.tech/ngspice/models').rglob('*') if f.is_file()}, 'solver': 'sparse'}
    checks = {'runtime': runtime == prep['runtime_identity'], 'sources': all(sha(out/n) == value for n, value in prep['source_hashes'].items()),
              'deck': sha(out/'probe.cir') == prep['deck_sha256'], 'bindings': all(sha(ROOT/n) == value for n, value in prep['bindings_sha256'].items())}
    (out/'runner.py').write_text(Path(__file__).read_text())
    (out/'provenance.json').write_text(json.dumps(dict(arguments=sys.argv[1:], runner_sha256=sha(Path(__file__)), input_checks=checks, runtime_identity=runtime, source_hashes=prep['source_hashes'], scope=prep['scope']), indent=2)+'\n')
    assert all(checks.values()), 'Input failure; simulator not launched'
    with (out/'run.log').open('x') as stream:
        state = run_bounded(['ngspice', '-b', str((out/'probe.cir').relative_to(SIM))], stream, out/'run.json', prep['watchdog_s'], cwd=SIM, interval_s=1)
    log = (out/'run.log').read_text()
    errors = [line for line in log.splitlines() if re.search(r'^Error|Timestep too small|analysis aborted|doAnalyses:|no such vector|no such parameter|not available|cannot parse', line)]
    result = dict(stage_current_contract_status='failed', runtime=state, errors=errors, warnings=warning_inventory(log), scope=prep['scope'])
    try:
        assert state['status'] == 'completed' and state['returncode'] == 0 and not errors
        expected = reference['parameter_audit']['parameters_before']
        if prep['mode'] == 'op':
            observed = {tag+'_'+when: read_group(log, 'P0_'+tag+'_'+when, queries) for tag, queries in prep['groups'].items() for when in ['BEFORE', 'AFTER']}
            before, after = [observed['NON_BGR_'+when]+observed['BGR_'+when] for when in ['BEFORE', 'AFTER']]
            assert before == after == expected and len(before) == 11512
            assert observed['LEGACY27_BEFORE'] == observed['LEGACY27_AFTER'] == [[k, dict(before)[k]] for k in prep['groups']['LEGACY27']]
            result['parameter_audit'] = dict(parameters_before=before, parameters_after=after, legacy27=observed['LEGACY27_BEFORE'])
            name = 'op0.dat'
        else:
            section, = re.findall(r'^PHASE0_BEGIN\n(.*?)^PHASE0_END$', log, re.M | re.S)
            result['parameter_audit'] = phase_parameters(section, prep['groups'], expected)
            name = 'phase0.dat'
        data = table(raw(out/name))
        assert np.isfinite(data).all()
        if prep['mode'] == 'op':
            assert data.shape == (1, 10)
        else:
            assert data.shape[1] == 18 and abs(data[-1, 0]-1.02e-6) < 1e-18
            result['wave_analysis'] = analyze_wave(data[:, :13].tolist(), prep['prospective_sampling'])
            assert result['wave_analysis']['sampling_status'] == 'passed'
        result['prior_macro_control_voltage_comparison'] = compare(raw(out/name), ref/name)
        result['canonical_fixture_voltage_comparison'] = compare(raw(out/name), SIM/'qualification'/prep['canonical_reference_run']/prep['canonical_wave_name'])
        current, mon, stage = [table(raw(out/n)) for n in ['currents.dat', 'monitor_voltages.dat', 'stages.dat']]
        assert np.array_equal(current[:, 0], data[:, 0])
        result['accounting'] = account(current, mon, stage, instances)
        assert result['accounting']['accounted_kcl_1pA_status'] == 'passed'
        result['stage_current_contract_status'] = 'passed'
    except (AssertionError, ValueError, OSError, KeyError, IndexError) as error:
        result['analysis_error'] = repr(error)
    (out/'summary.json').write_text(json.dumps([result], indent=2)+'\n')
    for path in out.glob('*.dat'):
        archive_new_wave(path)
    print(json.dumps({k: v for k, v in result.items() if k not in ['parameter_audit', 'warnings', 'wave_analysis', 'accounting']}, indent=2))
    raise SystemExit(0 if result['stage_current_contract_status'] == 'passed' else 1)


if __name__ == '__main__':
    main()
