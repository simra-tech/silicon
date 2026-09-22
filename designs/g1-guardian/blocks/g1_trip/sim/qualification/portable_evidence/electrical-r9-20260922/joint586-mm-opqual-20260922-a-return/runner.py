#!/usr/bin/env python3
"""Execute only a reviewed full3500-device/11512-parameter OP control."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys
from prepare_joint586_population import make_control, NODES, disabled_source
from run_bgr_substitution_draw_audit import read_group
from run_nominal_clock_probe import run_bounded
from analyze_bgr_substitution_outcomes import warning_inventory

SIM = Path(__file__).resolve().parent
ROOT = SIM.parents[4]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run-id', required=True)
    p.add_argument('--image-id', required=True)
    a = p.parse_args()
    assert '/' not in a.run_id
    out = SIM/'qualification'/a.run_id
    prep = json.loads((out/'preparation.json').read_text())
    inventory = json.loads((out/'population_inventory.json').read_text())
    groups = prep['prospective_groups']
    assert len(groups['NON_BGR']) == 8670 and len(groups['BGR']) == 2842 and len(groups['LEGACY27']) == 27
    assert groups['NON_BGR']+groups['BGR'] == inventory['all_queries']
    assert len(set(inventory['all_queries'])) == 11512
    assert not (out/'run.log').exists() and not (out/'summary.json').exists()
    reference = SIM/'qualification'/prep['reference_run']
    body = (reference/'hard_+0mV.cir').read_text().split('.control\n')[0]
    expected = body.replace(reference.name, a.run_id)+make_control(a.run_id, prep['seed'], prep['temperatures_C'], groups)
    assert (out/'population_op.cir').read_text() == expected
    for name in ['sense.spice', 'trip.spice', 'bgr.spice']:
        source = (ROOT/prep['qualified_BGR_mismatch_source']).read_text() if name == 'bgr.spice' else (reference/name).read_text()
        assert (out/name).read_text() == (source if prep['mismatch_enabled'] else disabled_source(source))
    pd = Path('/foss/pdks/ihp-sg13g2')
    runtime = {'image_id_observed_by_host': a.image_id, 'pdk_commit': (pd/'COMMIT').read_text().strip(),
               'ngspice_version': subprocess.check_output(['ngspice', '--version'], universal_newlines=True),
               'model_sha256': {str(f.relative_to(pd)): sha(f) for f in (pd/'libs.tech/ngspice/models').rglob('*') if f.is_file()}, 'solver': 'sparse'}
    checks = {'deck_exact': sha(out/'population_op.cir') == prep['deck_sha256'],
              'sources_exact': all(sha(out/name) == value for name, value in prep['source_hashes'].items()),
              'inventory_exact': sha(out/'population_inventory.json') == prep['inventory_sha256'],
              'runtime_exact': runtime == prep['expected_runtime_identity'],
              'bindings_exact': all(sha(ROOT/name) == value for name, value in prep['live_bindings_sha256'].items())}
    provenance = {'arguments': sys.argv[1:], 'runtime_identity': runtime, 'source_hashes': prep['source_hashes'],
                  'input_checks': checks, 'runner_sha256': sha(Path(__file__)), 'preparation_sha256': sha(out/'preparation.json'),
                  'population': 'NEW joint586/mm enabled population, not old71002 or nominal586 control equivalence',
                  'physical_scope': prep['physical_scope']}
    (out/'runner.py').write_text(Path(__file__).read_text())
    (out/'provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
    assert all(checks.values()), 'Preflight failure; no simulator launch'
    bound = 120 if len(prep['temperatures_C']) == 1 else 300
    assert prep['planning']['watchdog_s'] == bound
    with (out/'run.log').open('x') as stream:
        state = run_bounded(['ngspice', '-b', str((out/'population_op.cir').relative_to(SIM))], stream, out/'run.json', bound, cwd=SIM, interval_s=1)
    log = (out/'run.log').read_text()
    errors = [line for line in log.splitlines() if re.search(r'(?i)(^error|timestep too small|doAnalyses:|no such vector|no such parameter|not available|cannot parse)', line)]
    complete = state['status'] == 'completed' and state['returncode'] == 0 and not errors and 'POPULATION_OP_END' in log
    phases, query_checks = [], {}
    if complete:
        try:
            for index, temp in enumerate(prep['temperatures_C']):
                observed = {tag+'_'+when: read_group(log, 'P%d_%s_%s' % (index, tag, when), queries)
                            for tag, queries in groups.items() for when in ['BEFORE', 'AFTER']}
                before = observed['NON_BGR_BEFORE']+observed['BGR_BEFORE']
                after = observed['NON_BGR_AFTER']+observed['BGR_AFTER']
                fp = dict(before)
                assert len(before) == 11512 and before == after
                assert all(observed['LEGACY27_'+when] == [[key, fp[key]] for key in groups['LEGACY27']] for when in ['BEFORE', 'AFTER'])
                assert all(float(value) > 0 for key, value in before if key.endswith(('[w]', '[l]', '[scale]', '[area]')))
                if phases:
                    assert before == phases[0]['parameters_before'], 'Temperature changes realized random parameters'
                if not prep['mismatch_enabled']:
                    assert [v for k, v in observed['BGR_BEFORE']] == prep['disabled_BGR_nominal_expected']
                    for key, value in observed['NON_BGR_BEFORE']:
                        if key.endswith(('[delvto]', '[nsmm_rsh]', '[nsmm_w]', '[nsmm_l]')):
                            assert float(value) == 0
                        if key.endswith(('[factuo]', '[scale]')):
                            assert float(value) == 1
                data = (out/('op%d.dat' % index)).read_text().splitlines()
                values = [list(map(float, line.split())) for line in data[1:] if line.strip()]
                assert len(values) == 1 and len(values[0]) == 10 and all(math.isfinite(v) for v in values[0])
                phases.append({'temperature_C': temp, 'parameters_before': before, 'parameters_after': after,
                               'legacy27': observed['LEGACY27_BEFORE'], 'op_nodes_V': dict(zip(NODES, values[0][1:])),
                               'op_data_sha256': sha(out/('op%d.dat' % index))})
            query_checks = {'all11512_before_after_exact': True, 'all27_cross_inventory_exact': True,
                            'all_temperature_phase_parameters_exact': True,
                            'disabled_nominal_controls': True if not prep['mismatch_enabled'] else None}
        except (AssertionError, ValueError, KeyError, IndexError, OSError) as error:
            errors.append('Full population audit failed: '+str(error))
    valid = complete and not errors and len(phases) == len(prep['temperatures_C']) and bool(query_checks)
    result = {'seed': prep['seed'], 'label': prep['label'], 'mismatch_enabled': prep['mismatch_enabled'],
              'op_qualification_status': 'passed' if valid else 'failed', 'solver_status': 'passed' if complete else 'failed',
              'wall_s': state['wall_s'], 'watchdog_status': state['status'], 'returncode': state['returncode'],
              'errors': errors, 'warnings': warning_inventory(log), 'query_checks': query_checks, 'phases': phases,
              'scope': 'Individual OP control only. Cross-run repetition, changed-seed variation, disabled controls and temperature-return output equality require joint audit. Transient/calibration/population/adoption not qualified.'}
    if valid and len(phases) > 1:
        initial, final = phases[0]['op_nodes_V'], phases[-1]['op_nodes_V']
        result['return_exact_opdata_bytes'] = (out/'op0.dat').read_bytes() == (out/'op3.dat').read_bytes()
        result['return_max_abs_node_change_V'] = max(abs(initial[key]-final[key]) for key in initial)
        result['return_separate_1uV_bound'] = result['return_max_abs_node_change_V'] <= 1e-6
    (out/'summary.json').write_text(json.dumps([result], indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ['warnings', 'phases']}, indent=2))
    raise SystemExit(0 if valid else 1)


if __name__ == '__main__':
    main()
