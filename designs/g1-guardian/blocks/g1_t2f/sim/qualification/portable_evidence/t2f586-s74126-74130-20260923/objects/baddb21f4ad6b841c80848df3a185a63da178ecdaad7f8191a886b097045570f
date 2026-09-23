#!/usr/bin/env python3
"""One final586 independent sample; original four-temperature linear criterion."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import numpy as np
from prepare_586_population import HERE, ROOT, sha
from result_directory import allocate_run
from run_586_population_control import nominal_gate, phase_text
from run_586_source_control import load_wave
from run_nominal_clock_probe import run_bounded
from run_bgr_substitution_draw_audit import read_group
from analyze_bgr_substitution_outcomes import warning_inventory
from wave_archive import archive_new_wave

REFERENCE = HERE/'runs/t2f586-population-controls-20260922-a-enabled'
TEMPERATURES = [25, 100, -40, 125]


def sample_deck(reference, seed, temperature):
    assert 74101 <= seed <= 74400 and temperature in TEMPERATURES
    substitutions = [('.temp 25\n', '.temp %d\n' % temperature),
                     ('setseed 74001\n', 'setseed %d\n' % seed),
                     ('set temp=25\n', 'set temp=%d\n' % temperature)]
    result = reference
    for old, new in substitutions:
        assert result.count(old) == 1
        result = result.replace(old, new)
    assert result.count('\nreset\n') == result.count('tran 5n 32u\n') == 1
    return result


def qualification_gate(path):
    report = json.loads(path.read_text())
    assert report['status'] == 'passed six-control qualification'
    assert len(report['control_statuses']) == 6 and set(report['control_statuses'].values()) == {'passed'}
    assert all(report['comparisons']['full3180_vectors'].values())
    assert all(all(v.values()) for v in report['comparisons']['waveforms'].values())
    assert report['variation']['status'] == 'passed' and report['variation']['changed_primitives'] == 1129
    assert report['variation']['primitive_count'] == 1129
    for run_id, receipts in report['receipts_sha256'].items():
        assert all(sha(HERE/'runs'/run_id/name) == expected for name, expected in receipts.items())
    packet = HERE/'t2f586-population-controls-20260922-a.json'
    assert sha(packet) == report['packet_sha256']
    return report


def calibrate(rows):
    assert set(rows) == set(TEMPERATURES)
    f25, f100 = rows[25], rows[100]
    assert all(math.isfinite(value) and value > 0 for value in rows.values())
    slope = (f100-f25)/75
    assert slope > 0
    points = [dict(temperature_C=t, frequency_Hz=rows[t], inferred_temperature_C=25+(rows[t]-f25)/slope,
                   residual_C=25+(rows[t]-f25)/slope-t) for t in [-40, 125]]
    worst = max(abs(row['residual_C']) for row in points)
    return dict(status='passed' if worst <= 2 else 'failed', slope_Hz_per_C=slope, points=points,
                maximum_abs_residual_C=worst, criterion='Original25/100 frozen linear calibration; held-out−40/125 both within±2C; no LUT/refit.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--seed', type=int, required=True)
    parser.add_argument('--qualification-audit', type=Path, required=True)
    parser.add_argument('--image-id', required=True)
    parser.add_argument('--stop-file', type=Path)
    args = parser.parse_args()
    assert 74101 <= args.seed <= 74400
    audit_path = args.qualification_audit if args.qualification_audit.is_absolute() else HERE/args.qualification_audit
    qualification_gate(audit_path)
    prep = json.loads((REFERENCE/'preparation.json').read_text())
    nominal_gate(ROOT/prep['required_nominal_analysis'])
    assert all(sha(ROOT/name) == value for name, value in prep['live_bindings_sha256'].items())
    assert all(sha(REFERENCE/name) == value for name, value in prep['source_hashes'].items())
    assert sha(REFERENCE/'probe.cir') == prep['deck_sha256']
    pdk = Path('/foss/pdks/ihp-sg13g2')
    runtime = dict(image_id=args.image_id, pdk_commit=(pdk/'COMMIT').read_text().strip(),
        ngspice=subprocess.check_output(['ngspice', '--version'], universal_newlines=True),
        models_sha256={str(p.relative_to(pdk)): sha(p) for p in sorted((pdk/'libs.tech/ngspice/models').glob('*.lib'))},
        osdi_sha256={str(p.relative_to(pdk)): sha(p) for p in sorted((pdk/'libs.tech/ngspice/osdi').glob('*.osdi'))})
    assert runtime == prep['runtime']
    out = allocate_run(HERE.parent, args.run_id, relative_parent='qualification/runs')
    for name in ['bgr.spice', 't2f.spice', '.spiceinit', 'population_inventory.json']:
        (out/name).write_bytes((REFERENCE/name).read_bytes())
    assert sha(out/'population_inventory.json') == prep['inventory_sha256']
    (out/'runner.py').write_text(Path(__file__).read_text())
    provenance = dict(arguments=sys.argv[1:], runner_sha256=sha(Path(__file__)), qualification_audit_sha256=sha(audit_path),
        reference_preparation_sha256=sha(REFERENCE/'preparation.json'), reference_deck_sha256=prep['deck_sha256'],
        source_hashes=prep['source_hashes'], inventory_sha256=prep['inventory_sha256'], runtime_identity=runtime,
        seed=args.seed, temperatures_C=TEMPERATURES, watchdog_per_leaf_s=600,
        scope='New final586 independent T2F population, not historical510xx or control740xx. Full3180 within/between leaves exact; original linear±2C. Independent resets at same seed per leaf, with separately qualified same-instance return control. No actualpad/physicalCC/adoption or survivor-yield claim.')
    (out/'provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
    result = dict(seed=args.seed, status='running', leaves=[], full3180_across_temperatures='not run',
                  calibration_status='not run', scope=provenance['scope'])
    first_parameters = None
    for index, temperature in enumerate(TEMPERATURES):
        if args.stop_file and args.stop_file.exists():
            result['status'] = 'paused before next leaf; remaining conditions not run'
            break
        leaf = out/('p%02d' % index)
        leaf.mkdir()
        for name in ['bgr.spice', 't2f.spice', '.spiceinit']:
            (leaf/name).write_bytes((out/name).read_bytes())
        (leaf/'probe.cir').write_text(sample_deck((REFERENCE/'probe.cir').read_text(), args.seed, temperature))
        with (leaf/'run.log').open('x') as stream:
            state = run_bounded(['ngspice', '-b', 'probe.cir'], stream, leaf/'run.json', 600, cwd=leaf, interval_s=1)
        log = (leaf/'run.log').read_text()
        errors = [s for s in log.splitlines() if re.search(r'^Error|Timestep too small|analysis aborted|doAnalyses:|no such vector|no such parameter|not available|cannot parse', s, re.I)]
        row = dict(index=index, temperature_C=temperature, status='failed', runtime=state, errors=errors,
                   full3180_status='not run', warnings=warning_inventory(log), deck_sha256=sha(leaf/'probe.cir'))
        try:
            assert state['status'] == 'completed' and state['returncode'] == 0 and not errors
            phase = phase_text(log, 0)
            before = {tag: read_group(phase, 'P0_'+tag+'_BEFORE', keys) for tag, keys in prep['groups'].items()}
            after = {tag: read_group(phase, 'P0_'+tag+'_AFTER', keys) for tag, keys in prep['groups'].items()}
            assert sum(map(len, before.values())) == 3180 and before == after
            row.update(parameters_before=before, parameters_after=after)
            if first_parameters is None:
                first_parameters = before
            assert before == first_parameters, 'Exact same-seed cross-temperature full3180 failure'
            row['full3180_status'] = 'passed'
            blob, data = load_wave(leaf/'phase0.dat')
            assert data.ndim == 2 and data.shape[1] == 13 and np.isfinite(data).all() and abs(data[-1, 0]-32e-6) < 1e-12
            values = {k: float(v) for k, v in re.findall(r'(?m)^(\w+)\s*=\s*([-+0-9.eE]+)', phase)}
            assert all(k in values and math.isfinite(values[k]) for k in ['freq', 't_a', 't_b', 't_half_a', 'fout_hi', 'fout_lo'])
            assert values['freq'] > 0 and values['t_b'] > values['t_a']
            vce = float(max(np.abs(data[:, i]-data[:, j]).max() for i, j in [(7, 8), (9, 8), (10, 11), (12, 11)]))
            row.update(waveform_sha256=hashlib.sha256(blob).hexdigest(), wave_rows=len(data), measurements=values,
                       t2f_hbt_external_vce_max_V=vce, t2f_hbt_vce_status='passed' if vce <= 1.6 else 'failed')
            assert vce <= 1.6
            row['status'] = 'passed'
        except (AssertionError, ValueError, OSError, KeyError, IndexError) as error:
            row['analysis_error'] = repr(error)
        (leaf/'summary.json').write_text(json.dumps([row], indent=2)+'\n')
        if (leaf/'phase0.dat').exists():
            archive_new_wave(leaf/'phase0.dat')
        result['leaves'].append({k: v for k, v in row.items() if k not in ['parameters_before', 'parameters_after', 'warnings']})
        result['leaves'][-1]['summary_sha256'] = sha(leaf/'summary.json')
        result['parameters_first_completed_leaf'] = first_parameters
        (out/'summary.json').write_text(json.dumps([result], indent=2)+'\n')
    else:
        result['status'] = 'failed; complete attempted four-condition coverage'
        if all(row['status'] == row['full3180_status'] == 'passed' for row in result['leaves']):
            result['full3180_across_temperatures'] = 'passed'
            try:
                result['calibration'] = calibrate({row['temperature_C']: row['measurements']['freq'] for row in result['leaves']})
                result['calibration_status'] = result['calibration']['status']
                result['status'] = 'passed' if result['calibration_status'] == 'passed' else 'failed original linear calibration'
            except (AssertionError, KeyError, ValueError) as error:
                result['calibration_analysis_error'] = repr(error)
    (out/'summary.json').write_text(json.dumps([result], indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ['parameters_first_completed_leaf', 'leaves']}, indent=2))
    raise SystemExit(0 if result['status'] == 'passed' else 1)


if __name__ == '__main__':
    main()
