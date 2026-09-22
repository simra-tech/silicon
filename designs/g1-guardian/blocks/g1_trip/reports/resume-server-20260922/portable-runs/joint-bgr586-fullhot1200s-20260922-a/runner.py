#!/usr/bin/env python3
"""One fresh1200s fullhot diagnostic, gated by exact saved200ns prefix parity."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys
from run_nominal_clock_probe import analyze_wave, validate_saved_nodes, run_bounded
from run_bias_observation_probe import quiet_values
from run_bgr_substitution_draw_audit import read_group
from wave_archive import archive_new_wave, open_wave, wave_sha
from bgr_prefix_parity import select_prefix, compare_prefix_waves
from prepare_bgr_prefix_probe import require_measurements_inside_prefix

SIM = Path(__file__).resolve().parent
ROOT = SIM.parents[4]
BLOCKS = r'^echo (NON_BGR|BGR)_(BEFORE|AFTER)_BEGIN\n(.*?)^echo \1_\2_END\n'
LOG_BLOCKS = r'^(NON_BGR|BGR)_(BEFORE|AFTER)_BEGIN\n(.*?)^\1_\2_END\n'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parameter_audit(log, prep, inventory, baseline_values):
    groups = {}
    for when in ['BEFORE', 'AFTER']:
        for label, queries in [('NON_BGR', inventory['queries']), ('BGR', prep['candidate2842_queries'])]:
            groups[label + '_' + when] = read_group(log, label + '_' + when, queries)
    clean, count = re.subn(LOG_BLOCKS, '', log, flags=re.M | re.S)
    assert count == 4
    legacy = [list(pair) for pair in re.findall(r'^(@\S+)\s*=\s*(\S+)', clean, re.M)]
    assert len(legacy) == 27 and len(dict(legacy)) == 27
    original = dict(prep['original27_observations'])
    assert [key for key, value in legacy] == list(original)
    checks = {'nonBGR_before_equals_temperature_matched8670baseline': groups['NON_BGR_BEFORE'] == baseline_values,
              'nonBGR_after_equals_temperature_matched8670baseline': groups['NON_BGR_AFTER'] == baseline_values,
              'newBGR_before_all2842nominal_exact': [v for k, v in groups['BGR_BEFORE']] == prep['candidate2842_nominal_expected'],
              'newBGR_after_all2842nominal_exact': [v for k, v in groups['BGR_AFTER']] == prep['candidate2842_nominal_expected'],
              'original24legacy_nonBGR_exact': all(dict(legacy)[k] == v for k, v in prep['non_bgr24_expected'].items())}
    bgr_change = [{'parameter': k, 'original': original[k], 'candidate': v, 'unchanged': original[k] == v}
                  for k, v in legacy if '.xbgr.' in k]
    assert len(bgr_change) == 3
    return {'checks': checks, 'ordered_parameter_groups': groups, 'legacy27_observations': legacy,
            'original_three_BGR_changes': bgr_change}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--image-id', required=True)
    parser.add_argument('--timeout-s', type=float, default=1200)
    args = parser.parse_args()
    assert args.run_id == 'joint-bgr586-fullhot1200s-20260922-a' and 0 < args.timeout_s <= 1200
    out = SIM / 'qualification' / args.run_id
    prep = json.loads((out / 'preparation.json').read_text())
    assert prep['status'] == 'prepared only; simulator not run' and prep['run'] == args.run_id
    assert prep['seed'] == 71002 and prep['temperature_C'] == 125
    assert prep['planning']['watchdog_s'] == 1200
    assert sha(Path(__file__)) == prep['prepared_runner_sha256']
    assert prep['fixed_soft_hard_codes'] == [136, 154] and prep['shunt_V'] == .0245
    assert not (out / 'summary.json').exists() and not (out / 'run.log').exists()
    reference = SIM / 'qualification' / prep['reference_run']
    baseline = SIM / 'qualification' / prep['required_baseline_op_run']
    baseline_result, = json.loads((baseline / 'summary.json').read_text())
    assert baseline_result['op_inventory_qualification_status'] == 'passed'
    assert baseline_result['kind'] == 'baseline' and baseline_result['temperature_C'] == prep['temperature_C']
    baseline_values = baseline_result['ordered_parameter_groups']['NON_BGR_ALL']
    inventory = json.loads((out / 'non_bgr_inventory.json').read_text())
    assert len(baseline_values) == 8670 and [k for k, v in baseline_values] == inventory['queries']
    bindings = json.loads((out / 'prelaunch_reference_bindings.json').read_text())
    mandatory = [str((baseline / name).relative_to(ROOT)) for name in ['summary.json', 'provenance.json', 'preparation.json', 'non_bgr_inventory.json']]
    assert set(mandatory).issubset(bindings['sha256'])
    assert bindings['sha256'][prep['candidate_nominal_reference']] == prep['candidate_nominal_reference_sha256']
    deck = out / (prep['case'] + '.cir')
    deck_text = deck.read_text()
    full_reference = SIM / 'qualification' / prep['fullhot_reference_run']
    assert deck_text.replace(out.name, full_reference.name) == (full_reference / deck.name).read_text()
    assert len(require_measurements_inside_prefix(deck_text, endpoint_s=1.02e-6)) == 8
    prefix_reference = SIM / 'qualification' / prep['prefix_reference_run']
    observation_path = ROOT / prep['prefix_observation_audit']
    assert sha(observation_path) == prep['prefix_observation_audit_sha256']
    observation = json.loads(observation_path.read_text())
    assert observation['original_fixture_status'] == 'failed; unchanged'
    assert observation['limited_observation_status'].startswith('passed finite saved219ns')
    assert observation['summary_sha256'] == sha(prefix_reference / 'summary.json')
    assert observation['decoded_wave_sha256'] == wave_sha(prefix_reference / 'hard_+0mV.dat')
    with open_wave(prefix_reference / 'hard_+0mV.dat', 'rb') as stream:
        prepared_prefix = select_prefix(stream.read())
    assert all(prepared_prefix[key] == prep['strict_prefix_contract'][key] for key in ['sha256', 'byte_count', 'row_count', 'last_included_time_s'])
    clean, count = re.subn(BLOCKS, '', deck_text, flags=re.M | re.S)
    assert count == 4 and clean.replace(out.name, '@RUN@') == (reference / (prep['case'] + '.cir')).read_text().replace(reference.name, '@RUN@')
    for block in re.finditer(BLOCKS, deck_text, re.M | re.S):
        expected = inventory['queries'] if block[1] == 'NON_BGR' else prep['candidate2842_queries']
        assert block[3].splitlines() == ['print ' + key for key in expected]
    validate_saved_nodes(deck_text, (out / 'trip.spice').read_text())
    pdk = Path('/foss/pdks/ihp-sg13g2')
    runtime = {'image_id_observed_by_host': args.image_id, 'pdk_commit': (pdk / 'COMMIT').read_text().strip(),
               'ngspice_version': subprocess.check_output(['ngspice', '--version'], text=True),
               'model_sha256': {str(p.relative_to(pdk)): sha(p) for p in (pdk / 'libs.tech/ngspice/models').rglob('*') if p.is_file()},
               'solver': 'sparse'}
    baseline_prov = json.loads((baseline / 'provenance.json').read_text())
    checks = {'prepared_deck_exact': sha(deck) == prep['prepared_deck_sha256'],
              'source_exact': all(sha(out / name) == value for name, value in prep['source_hashes'].items()),
              'same_nonBGR_sources_as_temperature_matchedOP': all(sha(out / name) == sha(baseline / name) for name in ['sense.spice', 'trip.spice']),
              'candidate_nominal_source586_exact': sha(out / 'bgr.spice') == '586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b',
              'runtime_exact': runtime == prep['expected_runtime_identity'] == baseline_prov['runtime_identity'],
              'original_reference_exact': all(sha(reference / name) == value for name, value in prep['reference_hashes'].items()),
              'live_bindings_exact': all(sha(ROOT / relative) == value for relative, value in bindings['sha256'].items()),
              'query_inventory_exact': sha(out / 'non_bgr_inventory.json') == prep['non_bgr_inventory_sha256']}
    provenance = {'runner_arguments': sys.argv[1:], 'source_hashes': prep['source_hashes'], 'runtime_identity': runtime,
                  'input_checks': checks, 'prelaunch_reference_bindings': bindings,
                  'preparation_sha256': sha(out / 'preparation.json'), 'runner_sha256': sha(Path(__file__)),
                  'same_temperature_baseline_op': baseline.name,
                  'inherited_physical_fidelity_gate': 'Not qualified: independentphysicalreview reportsfourngmismatches ineachSENSEbuffer andsharedinputdiffusionAS/PS mismatch againstmodeldefaults. This iscontrolledexistingmodel-level comparison, notnewphysicalqualification.',
                  'inherited_physical_fidelity_evidence': {
                      'report': 'designs/g1-guardian/blocks/g1_sense/layout/coordinated_gm4/README.md',
                      'inherited-fidelity-20260922-r2.json': '9df9a9742e1d4309839de4905ccfa6dfb76de6ea092241472934d4fc1c723a75',
                      'junction-defaults-20260922-r1.json': '596c406af6ded2475c326b473ac79f353c9f22bd2cd52d22358a0f170517dbb3',
                      'terminal-nets-20260922-r1.json': '1d9de2a4d502d559548aab72d1ee9256981ae3bbe1adfac99926df6bcb79a07c'},
                  'strict_prefix_contract': prep['strict_prefix_contract'], 'fresh_fullhot_scope': prep['scope'],
                  'scope': 'Freshfullhot diagnostic; exact200ns prefix parity required. Original600stimeout andprefixmeasurementfailure preserved; no physicalqualification.'}
    (out / 'provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
    (out / 'runner.py').write_text(Path(__file__).read_text())
    assert all(checks.values()), 'Source/reference/input preflight failed; no simulator launch'
    with (out / 'run.log').open('x') as stream:
        state = run_bounded(['ngspice', '-b', str(deck.relative_to(SIM))], stream, out / 'run.json', args.timeout_s,
                            cwd=SIM, metadata={'seed': 71002, 'temperature_C': prep['temperature_C'], 'deck_sha256': sha(deck)}, interval_s=1)
    log = (out / 'run.log').read_text()
    warnings = [line for line in log.splitlines() if 'warning' in line.lower() or 'nan' in line.lower()]
    errors = [line for line in log.splitlines() if re.search(r'(?i)(^error|timestep too small|doAnalyses:|no such vector|no such parameter|not available|cannot parse)', line)]
    wave = out / (prep['case'] + '.dat')
    complete = state['status'] == 'completed' and state['returncode'] == 0 and not errors and 'QUALIFICATION_END' in log and wave.exists()
    params, analysis, quiet = {'checks': {}}, {'sampling_status': 'not run'}, {}
    prefix_parity = {'status': 'not run'}
    if complete:
        try:
            params = parameter_audit(log, prep, inventory, baseline_values)
            lines = wave.read_text().splitlines()
            assert len(lines[0].split()) == 18
            data = [list(map(float, line.split())) for line in lines[1:] if line.strip()]
            assert all(len(row) == 18 and all(math.isfinite(v) for v in row) for row in data)
            analysis = analyze_wave([row[:13] for row in data], prep['prospective_sampling'])
            quiet = quiet_values(log)
            prefix_parity = compare_prefix_waves(prefix_reference / 'hard_+0mV.dat', wave)
        except (AssertionError, ValueError, KeyError, IndexError) as error:
            errors.append('Strict substitution comparison failed: ' + str(error))
    valid = complete and not errors and bool(params['checks']) and all(params['checks'].values()) and analysis['sampling_status'] == 'passed' and bool(quiet) and prefix_parity['status'].startswith('passed')
    decisions = {key: value['measured_edge_decision'] for key, value in analysis.get('comparators', {}).items()}
    low = all(value is False for value in decisions.values()) if valid else None
    result = {'seed': 71002, 'temperature_C': prep['temperature_C'], 'case': prep['case'], 'shunt_V': .0245,
              'fixed_soft_hard_codes': [136, 154], 'solver_status': 'passed' if complete else 'failed',
              'watchdog_status': state['status'], 'returncode': state['returncode'], 'wall_s': state['wall_s'],
              'errors': errors, 'warning_lines': warnings, 'quiet_op_V': quiet, 'parameter_audit': params,
              'wave_analysis': analysis, 'strict_200ns_prefix_parity': prefix_parity, 'controlled_substitution_status': 'passed comparison contract' if valid else 'failed comparison contract',
              'selected_lower_point_both_LOW': low,
              'inherited_physical_fidelity_gate': provenance['inherited_physical_fidelity_gate'],
              'scope': 'One freshfullhot diagnostic,1200s cap; original600stimeout/prefixmeasurementfailure preserved. Original late3decisions plus exact200ns decoded/numeric prefix parity required. DifferentBGRnominallevel; no recalibration/population/physicaladoption/originalfailure waiver.'}
    (out / 'summary.json').write_text(json.dumps([result], indent=2) + '\n')
    if wave.exists():
        archive_new_wave(wave)
    print(json.dumps({key: result[key] for key in ['solver_status', 'wall_s', 'controlled_substitution_status', 'selected_lower_point_both_LOW', 'errors']}, indent=2))
    raise SystemExit(0 if valid else 1)


if __name__ == '__main__':
    main()
