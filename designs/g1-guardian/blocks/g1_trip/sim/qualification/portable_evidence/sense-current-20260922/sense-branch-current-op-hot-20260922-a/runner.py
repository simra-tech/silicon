#!/usr/bin/env python3
"""Run one explicit current-only SENSE OP/transient control with full draw audit."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import numpy as np
from prepare_sense_branch_current import instrument_source, instrument_deck
from run_bgr_substitution_draw_audit import read_group
from run_joint586_transients import phase_parameters
from run_nominal_clock_probe import analyze_wave, run_bounded
from wave_archive import archive_new_wave, open_wave
from analyze_bgr_substitution_outcomes import warning_inventory

SIM = Path(__file__).resolve().parent
ROOT = SIM.parents[4]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def statistics(data):
    times, current = data[:, 0], data[:, 1:]
    result = {}
    for name, start in [('complete', 0), ('last_200ns', .82e-6)]:
        selected = current[times >= start]
        tx = times[times >= start]
        if not len(tx):
            continue
        duration = float(tx[-1]-tx[0])
        integral = lambda array: np.sum((array[1:]+array[:-1])*.5*np.diff(tx)[:, None], axis=0)
        mean = integral(selected)/duration if duration else selected[0]
        rms = np.sqrt(integral(selected*selected)/duration) if duration else np.abs(selected[0])
        result[name] = {key: {'mean_A': float(mean[i]), 'rms_A': float(rms[i]), 'sampled_min_A': float(selected[:, i].min()),
                               'sampled_max_A': float(selected[:, i].max()), 'sampled_abs_peak_A': float(np.abs(selected[:, i]).max()),
                               'window_first_s': float(tx[0]), 'window_last_s': float(tx[-1])}
                       for i, key in enumerate(['sense_total', 'xota', 'xbuf', 'xref'])}
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run-id', required=True)
    p.add_argument('--image-id', required=True)
    a = p.parse_args()
    out = SIM/'qualification'/a.run_id
    prep = json.loads((out/'preparation.json').read_text())
    assert not (out/'run.log').exists() and not (out/'summary.json').exists()
    ref = SIM/'qualification'/prep['reference_run']
    expected_source, changes = instrument_source((ref/'sense.spice').read_text())
    assert (out/'sense.spice').read_text() == expected_source and changes == prep['source_changes']
    assert (out/'probe.cir').read_text() == instrument_deck((ref/'population_transient.cir').read_text(), ref.name, out.name, prep['mode'], prep['temperature_C'], prep['groups'])
    pd = Path('/foss/pdks/ihp-sg13g2')
    runtime = {'image_id_observed_by_host': a.image_id, 'pdk_commit': (pd/'COMMIT').read_text().strip(),
               'ngspice_version': subprocess.check_output(['ngspice', '--version'], universal_newlines=True),
               'model_sha256': {str(f.relative_to(pd)): sha(f) for f in (pd/'libs.tech/ngspice/models').rglob('*') if f.is_file()}, 'solver': 'sparse'}
    checks = {'runtime_exact': runtime == prep['expected_runtime_identity'],
              'sources_exact': all(sha(out/name) == value for name, value in prep['instrumented_source_hashes'].items()),
              'canonical_sources_exact': all(sha(ref/name) == value for name, value in prep['canonical_source_hashes'].items()),
              'deck_exact': sha(out/'probe.cir') == prep['deck_sha256'],
              'bindings_exact': all(sha(ROOT/name) == value for name, value in prep['live_bindings_sha256'].items())}
    (out/'runner.py').write_text(Path(__file__).read_text())
    provenance = {'arguments': sys.argv[1:], 'runner_sha256': sha(Path(__file__)), 'input_checks': checks,
                  'runtime_identity': runtime, 'source_hashes': prep['instrumented_source_hashes'], 'scope': prep['scope']}
    (out/'provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
    assert all(checks.values()), 'Input failure; simulator not launched'
    opref, = json.loads((SIM/'qualification'/prep['reference_op_run']/'summary.json').read_text())
    expected = opref['phases'][prep['reference_op_phase']]['parameters_before']
    with (out/'run.log').open('x') as logstream:
        state = run_bounded(['ngspice', '-b', str((out/'probe.cir').relative_to(SIM))], logstream, out/'run.json', prep['watchdog_s'], cwd=SIM, interval_s=1)
    log = (out/'run.log').read_text()
    errors = [line for line in log.splitlines() if re.search(r'(?im)^Error|Timestep too small|analysis aborted|doAnalyses:|no such vector|no such parameter|not available|cannot parse', line)]
    result = {'current_measurement_contract_status': 'failed', 'mode': prep['mode'], 'temperature_C': prep['temperature_C'],
              'seed': 73001, 'wall_s': state['wall_s'], 'watchdog_status': state['status'], 'returncode': state['returncode'],
              'errors': errors, 'warnings': warning_inventory(log), 'scope': prep['scope']}
    try:
        assert state['status'] == 'completed' and state['returncode'] == 0 and not errors
        if prep['mode'] == 'op':
            observed = {tag+'_'+when: read_group(log, 'P0_'+tag+'_'+when, queries) for tag, queries in prep['groups'].items() for when in ['BEFORE', 'AFTER']}
            before = observed['NON_BGR_BEFORE']+observed['BGR_BEFORE']
            after = observed['NON_BGR_AFTER']+observed['BGR_AFTER']
            assert before == after == expected and len(before) == 11512
            assert all(observed['LEGACY27_'+when] == [[k, dict(before)[k]] for k in prep['groups']['LEGACY27']] for when in ['BEFORE', 'AFTER'])
            result['parameter_audit'] = {'parameters_before': before, 'parameters_after': after, 'legacy27': observed['LEGACY27_BEFORE']}
            baseline = SIM/'qualification'/prep['reference_op_run']/('op%d.dat' % prep['reference_op_phase'])
            original_raw = baseline.read_bytes()
            raw = (out/'op0.dat').read_bytes()
            olddata = np.loadtxt(str(baseline), skiprows=1, ndmin=2)
            newdata = np.loadtxt(str(out/'op0.dat'), skiprows=1, ndmin=2)
            assert olddata.shape == newdata.shape == (1, 10) and np.isfinite(newdata).all()
            result['original_voltage_comparison'] = {'decoded_bytes_exact': raw == original_raw, 'numeric_rows_exact': bool(np.array_equal(newdata, olddata)),
                                                     'maximum_abs_node_delta_V': float(np.max(np.abs(newdata[:, 1:]-olddata[:, 1:]))) }
        else:
            section, = re.findall(r'^PHASE0_BEGIN\n(.*?)^PHASE0_END$', log, re.M | re.S)
            result['parameter_audit'] = phase_parameters(section, prep['groups'], expected)
            data = np.loadtxt(str(out/'phase0.dat'), skiprows=1)
            assert data.ndim == 2 and data.shape[1] == 18 and np.isfinite(data).all() and abs(data[-1, 0]-1.02e-6) < 1e-18
            result['wave_analysis'] = analyze_wave(data[:, :13].tolist(), prep['prospective_sampling'])
            with open_wave(ref/'phase0.dat', 'rb') as stream:
                oldraw = stream.read()
            original = np.array([list(map(float, line.split())) for line in oldraw.decode().splitlines()[1:] if line.strip()])
            same_grid = data.shape == original.shape and np.array_equal(data[:, 0], original[:, 0])
            interpolated = np.array([np.interp(data[:, 0], original[:, 0], original[:, i]) for i in range(1, 18)]).T
            result['original_voltage_comparison'] = {'decoded_bytes_exact': (out/'phase0.dat').read_bytes() == oldraw,
                                                     'numeric_rows_exact': bool(np.array_equal(data, original)), 'time_grid_exact': bool(same_grid),
                                                     'maximum_abs_node_delta_V_on_interpolated_reference_grid': float(np.max(np.abs(data[:, 1:]-interpolated))),
                                                     'interpolation_scope': 'Reference linearly interpolated onto instrumented times; not exactwave parity or acceptance waiver.'}
        currents = np.loadtxt(str(out/'currents.dat'), skiprows=1, ndmin=2)
        assert currents.shape[1] == 5 and np.isfinite(currents).all()
        if prep['mode'] == 'op':
            assert currents.shape[0] == 1
        else:
            assert np.array_equal(currents[:, 0], data[:, 0])
        residual = currents[:, 1]-np.sum(currents[:, 2:], axis=1)
        result['kcl_maximum_abs_residual_A'] = float(np.max(np.abs(residual)))
        assert result['kcl_maximum_abs_residual_A'] <= prep['kcl_maximum_abs_residual_A']
        result['current_windows'] = statistics(currents)
        result['current_measurement_contract_status'] = 'passed'
        result['strict_original_voltage_equality_status'] = 'passed' if result['original_voltage_comparison']['decoded_bytes_exact'] else 'failed exactcomparison; not silently replaced by numericaldifference/decisions'
    except (AssertionError, ValueError, OSError, KeyError, IndexError) as error:
        result['analysis_error'] = repr(error)
    (out/'summary.json').write_text(json.dumps([result], indent=2)+'\n')
    for wave in out.glob('*.dat'):
        archive_new_wave(wave)
    print(json.dumps({k: v for k, v in result.items() if k not in ['parameter_audit', 'warnings', 'wave_analysis']}, indent=2))
    raise SystemExit(0 if result['current_measurement_contract_status'] == 'passed' else 1)


if __name__ == '__main__':
    main()
