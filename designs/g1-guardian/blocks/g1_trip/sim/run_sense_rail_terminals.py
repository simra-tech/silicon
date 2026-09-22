#!/usr/bin/env python3
"""Bounded rail-terminal OP/TRANS control with explicit node-current accounting."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import numpy as np
from prepare_sense_rail_terminals import instrument, transform
from run_sense_branch_current import sha, statistics
from run_sense_supply_stages import windows, compare
from sense_monitor_shunt_op import raw, table
from run_bgr_substitution_draw_audit import read_group
from run_joint586_transients import phase_parameters
from run_nominal_clock_probe import run_bounded, analyze_wave
from analyze_bgr_substitution_outcomes import warning_inventory
from wave_archive import archive_new_wave

SIM = Path(__file__).resolve().parent
ROOT = SIM.parents[4]


def account(currents, monitors, data, instances):
    count = len(instances)
    assert currents.shape[1] == monitors.shape[1] == 5 and data.shape[1] == 1+2*count
    assert all(np.isfinite(a).all() for a in [currents, monitors, data])
    assert np.array_equal(currents[:, 0], monitors[:, 0]) and np.array_equal(currents[:, 0], data[:, 0])
    times, measured, volts = data[:, 0], data[:, 1:count+1], data[:, count+1:]
    corrected = measured-volts/1e12
    columns = {'xota': 2, 'xbuf': 3, 'xref': 4}
    for i, row in enumerate(instances):
        expected = monitors[:, columns[row['macro']]] if row['rail'] == 'vdd' else np.zeros(len(times))
        assert np.max(np.abs(volts[:, i]-expected)) <= 1e-15, 'Unexpected actual monitor voltage'
    top_raw = currents[:, 1]-currents[:, 2:].sum(axis=1)
    top_accounted = top_raw-monitors[:, 1]/1e12
    macro_checks, physical = {}, currents.copy()
    added = np.zeros(len(times))
    for macro, col in columns.items():
        indices = [i for i, r in enumerate(instances) if r['macro'] == macro and r['rail'] == 'vdd']
        # At the macro VDD node, every MOS rail terminal has its own downstream
        # meter. The preexisting macro VDD-node rshunt is outside those meters.
        residual = currents[:, col]-measured[:, indices].sum(axis=1)-monitors[:, col]/1e12
        extra = volts[:, indices].sum(axis=1)/1e12
        added += extra
        physical[:, col] -= monitors[:, col]/1e12+extra
        macro_checks[macro] = dict(maximum_abs_accounted_residual_A=float(np.abs(residual).max()), status='passed' if np.abs(residual).max() <= 1e-12 else 'failed')
    physical[:, 1] -= monitors[:, 1:].sum(axis=1)/1e12+added
    records = []
    for i, row in enumerate(instances):
        records.append(dict(row, measured_current_windows=windows(times, measured[:, i]),
                            shunt_subtracted_entering_terminal_windows=windows(times, corrected[:, i]),
                            injection_into_supply_wire_windows=windows(times, -corrected[:, i]),
                            actual_monitor_voltage_range_V=[float(volts[:, i].min()), float(volts[:, i].max())],
                            actual_monitor_shunt_current_range_A=[float(volts[:, i].min()/1e12), float(volts[:, i].max()/1e12)]))
    groups = {}
    for macro in ['xbuf', 'xref']:
        for label, rail, names in [('remaining_vdd', 'vdd', ['XM20', 'XMB3', 'XMB5', 'XMB7', 'XMT']), ('vss_group_a', 'vss', ['XM3', 'XMB2', 'XMB4', 'XMB6']), ('vss_group_b', 'vss', ['XM21', 'XM4'])]:
            indices = [i for i, r in enumerate(instances) if r['macro'] == macro and r['rail'] == rail and r['device'] in names]
            assert indices
            groups[macro+'_'+label] = dict(members=[dict(device=instances[i]['device'], terminal=instances[i]['terminal']) for i in indices],
                                                   entering_terminals_windows=windows(times, corrected[:, indices].sum(axis=1)),
                                                   scope='Signed sum of listed external terminals only; distinct physical source and body islands must be checked separately using individual records.')
    return dict(raw_top_kcl_maximum_abs_A=float(np.abs(top_raw).max()), raw_top_kcl_1pA_status='passed' if np.abs(top_raw).max() <= 1e-12 else 'failed',
                accounted_top_kcl_maximum_abs_A=float(np.abs(top_accounted).max()), accounted_top_kcl_1pA_status='passed' if np.abs(top_accounted).max() <= 1e-12 else 'failed',
                macro_vdd_rail_kcl=macro_checks, terminals=records, buffer_signed_groups=groups,
                macro_shunt_subtracted_current_windows=statistics(physical),
                added_vdd_monitor_shunt_range_A=[float((monitors[:, 1:].sum(axis=1)/1e12+added).min()), float((monitors[:, 1:].sum(axis=1)/1e12+added).max())],
                boundary_accounting='Four previous VDD monitor-node shunts plus each separately saved VDD-terminal monitor shunt are subtracted from total. Each macro subtracts its own old monitor shunt and new VDD-terminal shunts. All VSS-monitor actual voltages are checked zero. Individual terminal current subtracts its own measured shunt; positive enters device, negative injects into supply wire. No VSS=VDD assumption. Source and body values remain separate; sums cannot exclude cancellation.')


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
    source, sections, instances = instrument((ref/'sense.spice').read_text())
    assert source == (out/'sense.spice').read_text() and sections == prep['source_sections'] and instances == prep['terminal_instances']
    assert (out/'probe.cir').read_text() == transform((ref/'probe.cir').read_text(), ref.name, out.name, instances)
    assert '.option rshunt=1e12 gmin=1e-13\n' in (out/'probe.cir').read_text()
    pd = Path('/foss/pdks/ihp-sg13g2')
    runtime = dict(image_id_observed_by_host=args.image_id, pdk_commit=(pd/'COMMIT').read_text().strip(),
                   ngspice_version=subprocess.check_output(['ngspice', '--version'], universal_newlines=True),
                   model_sha256={str(f.relative_to(pd)): sha(f) for f in (pd/'libs.tech/ngspice/models').rglob('*') if f.is_file()}, solver='sparse')
    checks = dict(runtime=runtime == prep['runtime_identity'], sources=all(sha(out/n) == v for n, v in prep['source_hashes'].items()),
                  deck=sha(out/'probe.cir') == prep['deck_sha256'], bindings=all(sha(ROOT/n) == v for n, v in prep['bindings_sha256'].items()))
    (out/'runner.py').write_text(Path(__file__).read_text())
    (out/'provenance.json').write_text(json.dumps(dict(arguments=sys.argv[1:], runner_sha256=sha(Path(__file__)), input_checks=checks, runtime_identity=runtime, source_hashes=prep['source_hashes'], scope=prep['scope']), indent=2)+'\n')
    assert all(checks.values()), 'Input failure; simulator not launched'
    with (out/'run.log').open('x') as stream:
        state = run_bounded(['ngspice', '-b', str((out/'probe.cir').relative_to(SIM))], stream, out/'run.json', prep['watchdog_s'], cwd=SIM, interval_s=1)
    log = (out/'run.log').read_text()
    errors = [s for s in log.splitlines() if re.search(r'^Error|Timestep too small|analysis aborted|doAnalyses:|no such vector|no such parameter|not available|cannot parse', s)]
    result = dict(terminal_current_contract_status='failed', runtime=state, errors=errors, warnings=warning_inventory(log), scope=prep['scope'])
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
        current, mon, ports = [table(raw(out/n)) for n in ['currents.dat', 'monitor_voltages.dat', 'rail_terminals.dat']]
        assert np.array_equal(current[:, 0], data[:, 0])
        result['accounting'] = account(current, mon, ports, instances)
        assert result['accounting']['accounted_top_kcl_1pA_status'] == 'passed'
        assert all(r['status'] == 'passed' for r in result['accounting']['macro_vdd_rail_kcl'].values())
        result['terminal_current_contract_status'] = 'passed'
    except (AssertionError, ValueError, OSError, KeyError, IndexError) as error:
        result['analysis_error'] = repr(error)
    (out/'summary.json').write_text(json.dumps([result], indent=2)+'\n')
    for path in out.glob('*.dat'):
        archive_new_wave(path)
    print(json.dumps({k: v for k, v in result.items() if k not in ['parameter_audit', 'warnings', 'wave_analysis', 'accounting']}, indent=2))
    raise SystemExit(0 if result['terminal_current_contract_status'] == 'passed' else 1)


if __name__ == '__main__':
    main()
