#!/usr/bin/env python3
"""Run one immutable qualified joint586 population transient control."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys
from prepare_joint586_transients import transform
from run_bgr_substitution_draw_audit import read_group
from run_bgr_substitution_transient import LOG_BLOCKS
from run_nominal_clock_probe import analyze_wave, validate_saved_nodes, run_bounded
from run_bias_observation_probe import quiet_values
from analyze_bgr_substitution_outcomes import warning_inventory
from wave_archive import archive_new_wave

SIM = Path(__file__).resolve().parent
ROOT = SIM.parents[4]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def phase_parameters(log, groups, expected):
    observed = {tag+'_'+when: read_group(log, tag+'_'+when, groups[tag])
                for tag in ['NON_BGR', 'BGR'] for when in ['BEFORE', 'AFTER']}
    before = observed['NON_BGR_BEFORE']+observed['BGR_BEFORE']
    after = observed['NON_BGR_AFTER']+observed['BGR_AFTER']
    assert len(before) == 11512 and before == after == expected
    clean, count = re.subn(LOG_BLOCKS, '', log, flags=re.M | re.S)
    assert count == 4
    legacy = [list(pair) for pair in re.findall(r'^(@\S+)\s*=\s*(\S+)', clean, re.M)]
    assert legacy == [[key, dict(before)[key]] for key in groups['LEGACY27']]
    return {'parameters_before': before, 'parameters_after': after, 'legacy27': legacy}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run-id', required=True)
    p.add_argument('--image-id', required=True)
    a = p.parse_args()
    assert '/' not in a.run_id
    out = SIM/'qualification'/a.run_id
    prep = json.loads((out/'preparation.json').read_text())
    assert not (out/'run.log').exists() and not (out/'summary.json').exists()
    template = SIM/'qualification'/prep['template_run']
    reference = SIM/'qualification'/prep['qualified_op_run']
    baseline, = json.loads((reference/'summary.json').read_text())
    assert baseline['op_qualification_status'] == 'passed'
    deck = out/'population_transient.cir'
    expected_deck = transform((template/'hard_+0mV.cir').read_text(), template.name, out.name, prep['seed'], prep['temperatures_C'])
    assert deck.read_text() == expected_deck
    # Each phase retains the exact already-validated source hierarchy and save list.
    first = expected_deck.split('echo PHASE0_END\n')[0]+'quit 0\n.endc\n.end\n'
    validate_saved_nodes(first, (out/'trip.spice').read_text())
    pd = Path('/foss/pdks/ihp-sg13g2')
    runtime = {'image_id_observed_by_host': a.image_id, 'pdk_commit': (pd/'COMMIT').read_text().strip(),
               'ngspice_version': subprocess.check_output(['ngspice', '--version'], universal_newlines=True),
               'model_sha256': {str(f.relative_to(pd)): sha(f) for f in (pd/'libs.tech/ngspice/models').rglob('*') if f.is_file()}, 'solver': 'sparse'}
    checks = {'deck_exact': sha(deck) == prep['deck_sha256'],
              'sources_exact': all(sha(out/name) == sha(reference/name) == value for name, value in prep['source_hashes'].items()),
              'inventory_exact': sha(out/'population_inventory.json') == prep['inventory_sha256'],
              'runtime_exact': runtime == prep['expected_runtime_identity'],
              'bindings_exact': all(sha(ROOT/name) == value for name, value in prep['live_bindings_sha256'].items())}
    provenance = {'arguments': sys.argv[1:], 'source_hashes': prep['source_hashes'], 'runtime_identity': runtime,
                  'input_checks': checks, 'runner_sha256': sha(Path(__file__)), 'preparation_sha256': sha(out/'preparation.json'),
                  'physical_scope': prep['physical_scope'], 'scope': prep['scope']}
    (out/'provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
    (out/'runner.py').write_text(Path(__file__).read_text())
    assert all(checks.values()), 'Input gate failed; no simulator launch'
    bound = 1200 if len(prep['temperatures_C']) == 1 else 4800
    assert bound == prep['planning']['watchdog_s']
    with (out/'run.log').open('x') as stream:
        state = run_bounded(['ngspice', '-b', str(deck.relative_to(SIM))], stream, out/'run.json', bound, cwd=SIM, interval_s=1)
    log = (out/'run.log').read_text()
    errors = [line for line in log.splitlines() if re.search(r'(?i)(^error|timestep too small|doAnalyses:|no such vector|no such parameter|not available|cannot parse)', line)]
    complete = state['status'] == 'completed' and state['returncode'] == 0 and not errors and 'JOINT_POPULATION_TRAN_END' in log
    phases = []
    if complete:
        try:
            for index, temp in enumerate(prep['temperatures_C']):
                sections = re.findall(r'^PHASE%d_BEGIN\n(.*?)^PHASE%d_END$' % (index, index), log, re.M | re.S)
                assert len(sections) == 1
                expected = baseline['phases'][prep['qualified_op_phase_indices'][index]]['parameters_before']
                params = phase_parameters(sections[0], prep['groups'], expected)
                wave = out/('phase%d.dat' % index)
                lines = wave.read_text().splitlines()
                assert len(lines[0].split()) == 18
                data = [list(map(float, line.split())) for line in lines[1:] if line.strip()]
                assert all(len(row) == 18 and all(math.isfinite(v) for v in row) for row in data)
                analysis = analyze_wave([row[:13] for row in data], prep['prospective_sampling'])
                quiet = quiet_values(sections[0])
                phases.append(dict(params, temperature_C=temp, wave_analysis=analysis, quiet_op_V=quiet,
                                   decoded_wave_sha256=sha(wave), wave_rows=len(data),
                                   decisions={key: row['measured_edge_decision'] for key, row in analysis['comparators'].items()}))
        except (AssertionError, ValueError, KeyError, IndexError, OSError) as error:
            errors.append('Transient population audit failed: '+str(error))
    parameter_valid = complete and not errors and len(phases) == len(prep['temperatures_C'])
    sampling_valid = parameter_valid and all(row['wave_analysis']['sampling_status'] == 'passed' for row in phases)
    result = {'seed': prep['seed'], 'label': prep['label'], 'mismatch_enabled': prep['mismatch_enabled'],
              'solver_status': 'passed' if complete else 'failed', 'parameter_wave_contract_status': 'passed' if parameter_valid else 'failed',
              'decision_sampling_status': 'passed' if sampling_valid else 'failed or not run',
              'wall_s': state['wall_s'], 'watchdog_status': state['status'], 'returncode': state['returncode'],
              'errors': errors, 'warnings': warning_inventory(log), 'phases': phases, 'scope': prep['scope']}
    if parameter_valid and len(phases) == 4:
        result['return_decoded_wavebytes_exact'] = (out/'phase0.dat').read_bytes() == (out/'phase3.dat').read_bytes()
        result['return_selected_decisions_exact'] = phases[0]['decisions'] == phases[3]['decisions']
    (out/'summary.json').write_text(json.dumps([result], indent=2)+'\n')
    for wave in sorted(out.glob('phase*.dat')):
        archive_new_wave(wave)
    print(json.dumps({k: v for k, v in result.items() if k not in ['warnings', 'phases']}, indent=2))
    raise SystemExit(0 if parameter_valid and sampling_valid else 1)


if __name__ == '__main__':
    main()
