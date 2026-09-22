#!/usr/bin/env python3
"""Run one reviewed nominal T2F/BGR source control; predecessor gates fail closed."""
import argparse
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import numpy as np
from prepare_586_source_controls import BASE, BGR, transform, sha

HERE = Path(__file__).resolve().parent
BLOCKS = HERE.parents[2]
ROOT = HERE.parents[5]
sys.path.insert(0, str(BLOCKS/'g1_trip/sim'))
from run_nominal_clock_probe import run_bounded
from run_bgr_substitution_draw_audit import read_group
from analyze_bgr_substitution_outcomes import warning_inventory
from wave_archive import archive_new_wave, open_wave


def requirements(label):
    if label == 'old-host':
        return []
    if label == 'old-inventory':
        return [('old-host', 'exact_historical_wave_status', 'passed')]
    if label == 'new-paired':
        return [('old-inventory', 'exact_historical_wave_status', 'passed'), ('old-inventory', 'full_inventory_status', 'passed')]
    assert label in ['new-t25', 'new-t100', 'new-tm40', 'new-t125']
    return [('new-paired', 'control_status', 'passed')]


def load_wave(path):
    with open_wave(path, 'rb') as stream:
        blob = stream.read()
    data = np.array([list(map(float, line.split())) for line in blob.decode().splitlines()[1:] if line.strip()])
    return blob, data


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--packet', type=Path, required=True)
    p.add_argument('--label', required=True)
    p.add_argument('--image-id', required=True)
    args = p.parse_args()
    packet_path = args.packet if args.packet.is_absolute() else HERE/args.packet
    packet = json.loads(packet_path.read_text())
    cases = {row['label']: row for row in packet['cases']}
    case = cases[args.label]
    out = HERE/'runs'/case['run_id']
    prep = json.loads((out/'preparation.json').read_text())
    assert sha(out/'preparation.json') == case['preparation_sha256']
    assert not (out/'run.log').exists()
    predecessor_results = {}
    for label, key, expected in requirements(args.label):
        parent = HERE/'runs'/cases[label]['run_id']
        result, = json.loads((parent/'summary.json').read_text())
        assert result[key] == expected, 'Predecessor gate not passed: '+label+'/'+key
        predecessor_results[label] = dict(summary_sha256=sha(parent/'summary.json'), required_key=key, result=expected)
    expected_deck = transform((BASE/'ptat_T12.5.cir').read_text(), prep['temperature_C'], prep['query_groups'], prep['label'] == 'old-host')
    assert (out/'probe.cir').read_text() == expected_deck
    pd = Path('/foss/pdks/ihp-sg13g2')
    runtime = dict(image_id=args.image_id, pdk_commit=(pd/'COMMIT').read_text().strip(),
                   ngspice=subprocess.check_output(['ngspice', '--version'], universal_newlines=True),
                   models_sha256={str(path.relative_to(pd)): sha(path) for path in sorted((pd/'libs.tech/ngspice/models').glob('*.lib'))},
                   osdi_sha256={str(path.relative_to(pd)): sha(path) for path in sorted((pd/'libs.tech/ngspice/osdi').glob('*.osdi'))})
    checks = dict(runtime=runtime == prep['runtime'], sources=all(sha(out/n) == v for n, v in prep['source_hashes'].items()),
                  deck=sha(out/'probe.cir') == prep['deck_sha256'] == case['deck_sha256'],
                  bindings=all(sha(ROOT/n) == v for n, v in prep['bindings_sha256'].items()))
    (out/'runner.py').write_text(Path(__file__).read_text())
    provenance = dict(arguments=sys.argv[1:], runner_sha256=sha(Path(__file__)), packet_sha256=sha(packet_path),
                      preparation_sha256=sha(out/'preparation.json'), runtime_identity=runtime, source_hashes=prep['source_hashes'],
                      input_checks=checks, predecessors=predecessor_results, scope=prep['scope'])
    (out/'provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
    assert all(checks.values()), 'Input failure; ngspice not launched'
    with (out/'run.log').open('x') as stream:
        state = run_bounded(['ngspice', '-b', 'probe.cir'], stream, out/'run.json', prep['watchdog_proposal_s'], cwd=out, interval_s=1)
    log = (out/'run.log').read_text()
    errors = [line for line in log.splitlines() if re.search(r'^Error|Timestep too small|analysis aborted|doAnalyses:|no such vector|no such parameter|not available|cannot parse', line, re.I)]
    result = dict(control_status='failed', runtime=state, errors=errors, warnings=warning_inventory(log), label=args.label,
                  temperature_C=prep['temperature_C'], source_kind=prep['source_kind'], scope=prep['scope'],
                  full_inventory_status='not applicable' if not prep['query_groups'] else 'not run',
                  exact_historical_wave_status='not applicable; source substitution' if prep['source_kind'] == '586' else 'not run')
    try:
        assert state['status'] == 'completed' and state['returncode'] == 0 and not errors
        if prep['query_groups']:
            before, after = {}, {}
            for tag, queries in prep['query_groups'].items():
                before[tag] = read_group(log, tag+'_BEFORE', queries)
                after[tag] = read_group(log, tag+'_AFTER', queries)
                assert before[tag] == after[tag]
            assert sum(map(len, before.values())) == prep['query_count']
            if prep['source_kind'] == '586':
                assert before['BGR'] == prep['expected_nominal_BGR2842']
                reference, = json.loads((HERE/'runs'/cases['old-inventory']['run_id']/'summary.json').read_text())
                assert before['T2F'] == reference['parameters_before']['T2F']
                result['T2F338_exact_old_control_status'] = 'passed'
                result['BGR2842_exact_retained_nominal_status'] = 'passed'
            result.update(full_inventory_status='passed', parameters_before=before, parameters_after=after)
        blob, data = load_wave(out/prep['output_wave'])
        assert data.ndim == 2 and data.shape[1] == 13 and np.isfinite(data).all() and abs(data[-1, 0]-32e-6) < 1e-12
        values = {key: float(value) for key, value in re.findall(r'(?m)^(\w+)\s*=\s*([-+0-9.eE]+)', log)}
        assert all(k in values and math.isfinite(values[k]) for k in ['freq', 't_a', 't_b', 't_half_a', 'fout_hi', 'fout_lo'])
        assert values['freq'] > 0 and values['t_b'] > values['t_a']
        vce = float(max(np.abs(data[:, i]-data[:, j]).max() for i, j in [(7, 8), (9, 8), (10, 11), (12, 11)]))
        result.update(wave_rows=len(data), waveform_sha256=sha(out/prep['output_wave']), measurements=values,
                      t2f_hbt_external_vce_max_V=vce, t2f_hbt_vce_status='passed' if vce <= 1.6 else 'failed')
        assert vce <= 1.6
        if prep['source_kind'] == 'old':
            original_blob, original_data = load_wave(BASE/prep['historical_wave'])
            exact = dict(decoded_bytes=blob == original_blob, numeric_rows=bool(np.array_equal(data, original_data)),
                         time_grid=data.shape == original_data.shape and bool(np.array_equal(data[:, 0], original_data[:, 0])))
            result['exact_historical_wave_checks'] = exact
            result['exact_historical_wave_status'] = 'passed' if all(exact.values()) else 'failed'
            result['numerical_and_declared_inventory_status'] = 'passed'
            assert all(exact.values()), 'Original exact waveform comparison failed; no implicit waiver'
        result['control_status'] = 'passed'
    except (AssertionError, ValueError, OSError, KeyError, IndexError) as error:
        result['analysis_error'] = repr(error)
    (out/'summary.json').write_text(json.dumps([result], indent=2)+'\n')
    if (out/prep['output_wave']).exists():
        archive_new_wave(out/prep['output_wave'])
    print(json.dumps({k: v for k, v in result.items() if k not in ['parameters_before', 'parameters_after', 'warnings']}, indent=2))
    raise SystemExit(0 if result['control_status'] == 'passed' else 1)


if __name__ == '__main__':
    main()
