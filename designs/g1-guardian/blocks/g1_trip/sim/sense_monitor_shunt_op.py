#!/usr/bin/env python3
"""Output-only replays of failed raw-KCL controls; independently account rshunt."""
import argparse
import difflib
import json
from pathlib import Path
import re
import subprocess
import sys
import numpy as np
from result_directory import allocate_run
from run_sense_branch_current import sha, statistics
from run_bgr_substitution_draw_audit import read_group
from run_nominal_clock_probe import run_bounded
from wave_archive import open_wave, archive_new_wave
from analyze_bgr_substitution_outcomes import warning_inventory

SIM = Path(__file__).resolve().parent
ROOT = SIM.parents[4]
NODES = ['sense_vdd_monitor', 'xs.vdd_ota_monitor', 'xs.vdd_buf_monitor', 'xs.vdd_ref_monitor']


def transform(text, old, new):
    assert text.count('.option rshunt=1e12 gmin=1e-13\n') == 1
    assert text.count('echo POPULATION_OP_END\n') == 1
    text = text.replace(old, new)
    vectors = ' '.join('v('+node+')' for node in NODES)
    text, count = re.subn(r'^(\.save .+)$', lambda m: m[1]+' '+vectors, text, flags=re.M)
    assert count == 1
    return text.replace('echo POPULATION_OP_END\n', 'wrdata qualification/'+new+'/monitor_voltages.dat '+vectors+'\necho POPULATION_OP_END\n')


def raw(path):
    with open_wave(path, 'rb') as stream:
        return stream.read()


def table(payload):
    return np.array([list(map(float, line.split())) for line in payload.decode().splitlines()[1:] if line.strip()])


def account(currents, monitors):
    assert currents.shape == monitors.shape == (1, 5)
    assert np.isfinite(currents).all() and np.isfinite(monitors).all()
    assert np.array_equal(currents[:, 0], monitors[:, 0])
    shunts = monitors[:, 1:]/1e12
    residual = currents[:, 1]-currents[:, 2:].sum(axis=1)
    corrected = residual-shunts[:, 0]
    physical = currents.copy()
    physical[:, 1] -= shunts.sum(axis=1)
    physical[:, 2:] -= shunts[:, 1:]
    return {'monitor_voltages_V': dict(zip(NODES, monitors[0, 1:].tolist())),
            'added_node_shunts_A': dict(zip(NODES, shunts[0].tolist())),
            'total_added_shunt_current_A': float(shunts.sum()),
            'raw_residual_A': float(residual[0]), 'raw_1pA_status': 'passed' if abs(residual[0]) <= 1e-12 else 'failed',
            'accounted_residual_A': float(corrected[0]),
            'accounted_1pA_status': 'passed' if abs(corrected[0]) <= 1e-12 else 'failed',
            'instrumented_current_windows': statistics(currents), 'shunt_subtracted_current_windows': statistics(physical),
            'boundary_accounting': 'Top added node shunt is inside total meter and outside all three branch meters. Each branch monitor shunt is inside its own branch meter. Subtract all four only from total; subtract corresponding one from each branch. Existing canonical node shunts remain part of the original model.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--reference')
    parser.add_argument('--image-id')
    args = parser.parse_args()
    if args.reference:
        ref = SIM/'qualification'/args.reference
        old = json.loads((ref/'preparation.json').read_text())
        result, = json.loads((ref/'summary.json').read_text())
        assert old['mode'] == 'op' and result['watchdog_status'] == 'completed' and result['returncode'] == 0 and not result['errors']
        assert len(result['parameter_audit']['parameters_before']) == 11512
        out = allocate_run(SIM, args.run_id)
        for name in ['sense.spice', 'trip.spice', 'bgr.spice', 'population_inventory.json']:
            (out/name).write_bytes((ref/name).read_bytes())
        deck = transform((ref/'probe.cir').read_text(), ref.name, out.name)
        (out/'probe.cir').write_text(deck)
        (out/'declared_monitor_output_difference.diff').write_text(''.join(difflib.unified_diff((ref/'probe.cir').read_text().replace(ref.name, '@RUN@').splitlines(True), deck.replace(out.name, '@RUN@').splitlines(True), fromfile='originalFailedRawKCL', tofile='outputOnlyMonitorObservation')))
        old.update(reference_current_op=ref.name, run=out.name, deck_sha256=sha(out/'probe.cir'),
                   output_only_runner_sha256=sha(Path(__file__)), scope='Output-only monitor voltage observation. Original raw1pA KCL and original voltage exact-comparison failures remain failures; separate accounted current characterization only.')
        old['live_bindings_sha256'].update({str(p.relative_to(ROOT)): sha(p) for p in [ref/'preparation.json', ref/'summary.json', ref/'probe.cir', Path(__file__).resolve()]})
        (out/'preparation.json').write_text(json.dumps(old, indent=2)+'\n')
        print(json.dumps({'prepared': out.name, 'deck_sha256': old['deck_sha256']}))
        return
    out = SIM/'qualification'/args.run_id
    prep = json.loads((out/'preparation.json').read_text())
    ref = SIM/'qualification'/prep['reference_current_op']
    original, = json.loads((ref/'summary.json').read_text())
    assert not (out/'run.log').exists()
    assert (out/'probe.cir').read_text() == transform((ref/'probe.cir').read_text(), ref.name, out.name)
    pd = Path('/foss/pdks/ihp-sg13g2')
    runtime = {'image_id_observed_by_host': args.image_id, 'pdk_commit': (pd/'COMMIT').read_text().strip(),
               'ngspice_version': subprocess.check_output(['ngspice', '--version'], universal_newlines=True),
               'model_sha256': {str(p.relative_to(pd)): sha(p) for p in (pd/'libs.tech/ngspice/models').rglob('*') if p.is_file()}, 'solver': 'sparse'}
    checks = {'runtime': runtime == prep['expected_runtime_identity'], 'deck': sha(out/'probe.cir') == prep['deck_sha256'],
              'sources': all(sha(out/name) == value for name, value in prep['instrumented_source_hashes'].items()),
              'bindings': all(sha(ROOT/name) == value for name, value in prep['live_bindings_sha256'].items())}
    (out/'runner.py').write_text(Path(__file__).read_text())
    (out/'provenance.json').write_text(json.dumps({'arguments': sys.argv[1:], 'input_checks': checks, 'runtime_identity': runtime, 'runner_sha256': sha(Path(__file__))}, indent=2)+'\n')
    assert all(checks.values()), 'Input check failed; simulator not launched'
    with (out/'run.log').open('x') as stream:
        state = run_bounded(['ngspice', '-b', str((out/'probe.cir').relative_to(SIM))], stream, out/'run.json', 120, cwd=SIM, interval_s=1)
    log = (out/'run.log').read_text()
    errors = [s for s in log.splitlines() if re.search(r'^Error|Timestep too small|analysis aborted|doAnalyses:|no such vector|no such parameter|not available|cannot parse', s)]
    result = dict(status='failed', runtime=state, errors=errors, warnings=warning_inventory(log), scope=prep['scope'])
    try:
        assert state['status'] == 'completed' and state['returncode'] == 0 and not errors
        values = {tag+'_'+when: read_group(log, 'P0_'+tag+'_'+when, queries) for tag, queries in prep['groups'].items() for when in ['BEFORE', 'AFTER']}
        before = values['NON_BGR_BEFORE']+values['BGR_BEFORE']
        after = values['NON_BGR_AFTER']+values['BGR_AFTER']
        assert before == after == original['parameter_audit']['parameters_before'] == original['parameter_audit']['parameters_after'] and len(before) == 11512
        assert values['LEGACY27_BEFORE'] == values['LEGACY27_AFTER'] == original['parameter_audit']['legacy27']
        result['parameter_audit'] = dict(parameters_before=before, parameters_after=after, legacy27=values['LEGACY27_BEFORE'])
        result['output_only_parity'] = {name: {'decoded_bytes_exact': raw(out/name) == raw(ref/name), 'numeric_rows_exact': bool(np.array_equal(table(raw(out/name)), table(raw(ref/name))))} for name in ['op0.dat', 'currents.dat']}
        assert all(all(check.values()) for check in result['output_only_parity'].values())
        result['current_accounting'] = account(table(raw(out/'currents.dat')), table(raw(out/'monitor_voltages.dat')))
        assert result['current_accounting']['accounted_1pA_status'] == 'passed'
        result['status'] = 'passed accounted characterization; original raw and voltage exact failures retained'
    except (AssertionError, ValueError, OSError, KeyError, IndexError) as error:
        result['analysis_error'] = repr(error)
    (out/'summary.json').write_text(json.dumps([result], indent=2)+'\n')
    for path in out.glob('*.dat'):
        archive_new_wave(path)
    print(json.dumps({k: v for k, v in result.items() if k not in ['parameter_audit', 'warnings']}, indent=2))
    raise SystemExit(0 if result['status'].startswith('passed') else 1)


if __name__ == '__main__':
    main()
