#!/usr/bin/env python3
"""Run one explicitly reviewed219ns prefix; no retry or timeout extension."""
import argparse
import bisect
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys
from prepare_bgr_prefix_probe import transform
from run_bgr_substitution_transient import parameter_audit
from run_nominal_clock_probe import run_bounded, validate_saved_nodes
from analyze_bgr_substitution_outcomes import warning_inventory
from wave_archive import archive_new_wave

SIM = Path(__file__).resolve().parent
ROOT = SIM.parents[4]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def analyze_prefix(data):
    assert data and all(len(row) == 18 and all(math.isfinite(v) for v in row) for row in data)
    times = [row[0] for row in data]
    assert times[0] == 0 and all(a < b for a, b in zip(times, times[1:]))
    assert abs(times[-1] - 219e-9) < 1e-16

    def sample(t):
        i = bisect.bisect_left(times, t)
        assert 0 < i < len(times)
        lo, hi = data[i-1], data[i]
        fraction = (t-lo[0])/(hi[0]-lo[0])
        assert 0 <= fraction <= 1
        return {'time_s': t, 'bracketing_times_s': [lo[0], hi[0]], 'fraction': fraction,
                'all18_values': [a+fraction*(b-a) for a, b in zip(lo, hi)]}

    channels = {}
    for name, clock_col, q_col, dac_col, legacy_time in [('soft', 1, 5, 3, 40e-9), ('hard', 8, 6, 4, 140.2e-9)]:
        edges = [a[0]+(.6-a[clock_col])/(b[clock_col]-a[clock_col])*(b[0]-a[0])
                 for a, b in zip(data, data[1:]) if a[clock_col] < .6 <= b[clock_col]]
        assert len(edges) == 1, 'Prefix requires exactly one rising edge per channel'
        actual = sample(edges[0]+20e-9)
        legacy = sample(legacy_time)
        actual_value, legacy_value = actual['all18_values'][q_col], legacy['all18_values'][q_col]
        classify = lambda value: 'LOW' if value < .6 else 'HIGH' if value > .6 else 'AMBIGUOUS'
        channels[name] = {'actual_edge_s': edges[0], 'actual_edge_plus20ns': actual,
                          'legacy_fixed_phase': legacy, 'actual_decision': classify(actual_value),
                          'legacy_decision': classify(legacy_value),
                          'sampling_policies_agree': classify(actual_value) == classify(legacy_value) != 'AMBIGUOUS',
                          'actual_sample_differential_V': actual['all18_values'][2]-actual['all18_values'][dac_col],
                          'early_evolution': [dict(sample(edges[0]+offset*1e-9), offset_ns=offset)
                                              for offset in [-1, 0, .2, .5, 1, 20]]}
    return {'status': 'passed finite219ns trajectory and one actual edge per channel', 'rows': len(data),
            'endpoint_s': times[-1], 'channels': channels,
            'late3sample_electrical_acceptance': 'not run; first evaluation pair is not late-state qualification'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--image-id', required=True)
    parser.add_argument('--timeout-s', type=float, default=300)
    args = parser.parse_args()
    assert args.run_id == 'joint-bgr586-hot-prefix219ns-20260922-a' and 0 < args.timeout_s <= 300
    out = SIM / 'qualification' / args.run_id
    assert not (out / 'summary.json').exists() and not (out / 'run.log').exists()
    prep = json.loads((out / 'preparation.json').read_text())
    assert prep['run'] == args.run_id and prep['temperature_C'] == 125 and prep['seed'] == 71002
    assert prep['shunt_V'] == .0245 and prep['fixed_soft_hard_codes'] == [136, 154]
    reference = SIM / 'qualification' / prep['prefix_reference_run']
    baseline = SIM / 'qualification' / prep['required_baseline_op_run']
    base, = json.loads((baseline / 'summary.json').read_text())
    assert base['op_inventory_qualification_status'] == 'passed' and base['temperature_C'] == 125
    bindings = json.loads((out / 'prelaunch_reference_bindings.json').read_text())
    inventory = json.loads((out / 'non_bgr_inventory.json').read_text())
    assert len(inventory['queries']) == 8670
    deck = out / (prep['case'] + '.cir')
    assert deck.read_text() == transform((reference / deck.name).read_text(), reference.name, out.name)
    assert prep['prospective_sampling']['required_endpoint_s'] == 219e-9
    validate_saved_nodes(deck.read_text(), (out / 'trip.spice').read_text())
    pdk = Path('/foss/pdks/ihp-sg13g2')
    runtime = {'image_id_observed_by_host': args.image_id, 'pdk_commit': (pdk / 'COMMIT').read_text().strip(),
               'ngspice_version': subprocess.check_output(['ngspice', '--version'], universal_newlines=True),
               'model_sha256': {str(p.relative_to(pdk)): sha(p) for p in (pdk / 'libs.tech/ngspice/models').rglob('*') if p.is_file()}, 'solver': 'sparse'}
    inherited = json.loads((reference / 'provenance.json').read_text())
    checks = {'prepared_deck_exact': sha(deck) == prep['prepared_deck_sha256'],
              'all_source_bytes_exact': all(sha(out / name) == value for name, value in prep['source_hashes'].items()),
              'runtime_models_exact': runtime == prep['expected_runtime_identity'] == inherited['runtime_identity'],
              'live_reference_baseline_nominal_bindings_exact': all(sha(ROOT / name) == value for name, value in bindings['sha256'].items()),
              'inventory_exact': sha(out / 'non_bgr_inventory.json') == prep['non_bgr_inventory_sha256']}
    mandatory = [str((baseline / name).relative_to(ROOT)) for name in ['summary.json', 'provenance.json', 'preparation.json', 'non_bgr_inventory.json']]
    assert set(mandatory).issubset(bindings['sha256'])
    assert bindings['sha256'][prep['candidate_nominal_reference']] == prep['candidate_nominal_reference_sha256']
    provenance = {'runner_arguments': sys.argv[1:], 'runner_sha256': sha(Path(__file__)),
                  'preparation_sha256': sha(out / 'preparation.json'), 'source_hashes': prep['source_hashes'],
                  'runtime_identity': runtime, 'input_checks': checks, 'live_bindings': bindings,
                  'inherited_physical_fidelity_gate': inherited['inherited_physical_fidelity_gate'],
                  'inherited_physical_fidelity_evidence': inherited['inherited_physical_fidelity_evidence'], 'scope': prep['scope']}
    (out / 'provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
    (out / 'runner.py').write_text(Path(__file__).read_text())
    assert all(checks.values()), 'Strict preflight failed; no simulator launch'
    with (out / 'run.log').open('x') as stream:
        state = run_bounded(['ngspice', '-b', str(deck.relative_to(SIM))], stream, out / 'run.json', args.timeout_s,
                            cwd=SIM, metadata={'seed': 71002, 'temperature_C': 125, 'deck_sha256': sha(deck)}, interval_s=1)
    log = (out / 'run.log').read_text()
    errors = [line for line in log.splitlines() if re.search(r'(?i)(^error|timestep too small|doAnalyses:|no such vector|no such parameter|not available|cannot parse)', line)]
    wave = out / (prep['case'] + '.dat')
    complete = state['status'] == 'completed' and state['returncode'] == 0 and not errors and 'QUALIFICATION_END' in log and wave.exists()
    params, analysis = {'checks': {}}, {'status': 'not run'}
    if complete:
        try:
            params = parameter_audit(log, prep, inventory, base['ordered_parameter_groups']['NON_BGR_ALL'])
            lines = wave.read_text().splitlines()
            assert len(lines[0].split()) == 18
            analysis = analyze_prefix([list(map(float, line.split())) for line in lines[1:] if line.strip()])
        except (AssertionError, ValueError, KeyError, IndexError) as error:
            errors.append('Prefix completion contract failed: ' + str(error))
    valid = complete and not errors and bool(params['checks']) and all(params['checks'].values()) and analysis['status'].startswith('passed')
    result = {'seed': 71002, 'temperature_C': 125, 'watchdog_status': state['status'], 'returncode': state['returncode'],
              'wall_s': state['wall_s'], 'solver_status': 'passed' if complete else 'failed',
              'prefix_contract_status': 'passed' if valid else 'failed', 'parameter_audit': params,
              'wave_analysis': analysis, 'errors': errors, 'warnings': warning_inventory(log),
              'scope': 'First soft/hard evaluation pair numerical/trajectory diagnostic only. Late3sample acceptance not run; originalhot timeout/electricalfailures and physical-fidelity failure unchanged.'}
    (out / 'summary.json').write_text(json.dumps([result], indent=2) + '\n')
    if wave.exists():
        archive_new_wave(wave)
    print(json.dumps({key: result[key] for key in ['solver_status', 'prefix_contract_status', 'wall_s', 'errors']}, indent=2))
    raise SystemExit(0 if valid else 1)


if __name__ == '__main__':
    main()
