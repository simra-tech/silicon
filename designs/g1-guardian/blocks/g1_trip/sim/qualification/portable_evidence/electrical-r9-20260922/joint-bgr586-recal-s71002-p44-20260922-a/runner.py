#!/usr/bin/env python3
"""One frozen-draw calibration probe; separate numeric/parameter/timing decisions."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys
from prepare_bgr_calibration_probe import transform
from run_bgr_substitution_transient import parameter_audit
from run_nominal_clock_probe import analyze_wave, validate_saved_nodes, run_bounded
from run_bias_observation_probe import quiet_values
from analyze_bgr_substitution_outcomes import warning_inventory
from wave_archive import archive_new_wave

SIM = Path(__file__).resolve().parent
ROOT = SIM.parents[4]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--image-id', required=True)
    parser.add_argument('--timeout-s', type=float, default=1200)
    args = parser.parse_args()
    assert '/' not in args.run_id and 0 < args.timeout_s <= 1200
    out = SIM / 'qualification' / args.run_id
    assert not (out / 'run.log').exists() and not (out / 'summary.json').exists()
    prep = json.loads((out / 'preparation.json').read_text())
    assert prep['seed'] == 71002 and prep['run'] == args.run_id
    ref = SIM / 'qualification' / prep['calibration_template_run']
    baseline = SIM / 'qualification' / prep['full_nonBGR_baseline_run']
    base, = json.loads((baseline / 'summary.json').read_text())
    assert base['op_inventory_qualification_status'] == 'passed'
    inventory = json.loads((out / 'non_bgr_inventory.json').read_text())
    assert len(inventory['queries']) == 8670
    bindings = json.loads((out / 'prelaunch_reference_bindings.json').read_text())
    deck = out / 'hard_+0mV.cir'
    expected = transform((ref / deck.name).read_text(), ref.name, out.name, *prep['fixed_soft_hard_codes'], prep['shunt_V'], prep['temperature_C'])
    assert deck.read_text() == expected
    validate_saved_nodes(expected, (out / 'trip.spice').read_text())
    pdk = Path('/foss/pdks/ihp-sg13g2')
    runtime = {'image_id_observed_by_host': args.image_id, 'pdk_commit': (pdk / 'COMMIT').read_text().strip(),
               'ngspice_version': subprocess.check_output(['ngspice', '--version'], universal_newlines=True),
               'model_sha256': {str(p.relative_to(pdk)): sha(p) for p in (pdk / 'libs.tech/ngspice/models').rglob('*') if p.is_file()}, 'solver': 'sparse'}
    refprov = json.loads((ref / 'provenance.json').read_text())
    checks = {'deck_exact': sha(deck) == prep['prepared_deck_sha256'],
              'sources_exact': all(sha(out / name) == value for name, value in prep['source_hashes'].items()),
              'runtime_exact': runtime == prep['expected_runtime_identity'] == refprov['runtime_identity'],
              'inventory_exact': sha(out / 'non_bgr_inventory.json') == prep['non_bgr_inventory_sha256'],
              'livebindings_exact': all(sha(ROOT / key) == value for key, value in bindings['sha256'].items())}
    assert len(bindings['sha256']) == 13
    provenance = {'runner_arguments': sys.argv[1:], 'runner_sha256': sha(Path(__file__)), 'source_hashes': prep['source_hashes'],
                  'runtime_identity': runtime, 'input_checks': checks, 'preparation_sha256': sha(out / 'preparation.json'),
                  'input_bindings': bindings, 'inherited_physical_fidelity_gate': refprov['inherited_physical_fidelity_gate'],
                  'scope': prep['scope']}
    (out / 'provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
    (out / 'runner.py').write_text(Path(__file__).read_text())
    assert all(checks.values()), 'Input check failed; no simulator launch'
    with (out / 'run.log').open('x') as stream:
        state = run_bounded(['ngspice', '-b', str(deck.relative_to(SIM))], stream, out / 'run.json', args.timeout_s,
                            cwd=SIM, metadata={'seed':71002,'temperature_C':prep['temperature_C'],'deck_sha256':sha(deck)}, interval_s=1)
    log = (out / 'run.log').read_text()
    errors = [line for line in log.splitlines() if re.search(r'(?i)(^error|timestep too small|doAnalyses:|no such vector|no such parameter|not available|cannot parse)', line)]
    wave = out / 'hard_+0mV.dat'
    complete = state['status'] == 'completed' and state['returncode'] == 0 and not errors and 'QUALIFICATION_END' in log and wave.exists()
    params, analysis, quiet = {'checks':{}}, {'sampling_status':'not run'}, {}
    if complete:
        try:
            params = parameter_audit(log, prep, inventory, base['ordered_parameter_groups']['NON_BGR_ALL'])
            lines = wave.read_text().splitlines()
            assert len(lines[0].split()) == 18
            rows = [list(map(float, line.split())) for line in lines[1:] if line.strip()]
            assert all(len(row) == 18 and all(math.isfinite(v) for v in row) for row in rows)
            analysis = analyze_wave([row[:13] for row in rows], prep['prospective_sampling'])
            quiet = quiet_values(log)
        except (AssertionError, ValueError, KeyError, IndexError) as error:
            errors.append('Calibration comparison failed: '+str(error))
    valid = complete and not errors and params['checks'] and all(params['checks'].values()) and analysis['sampling_status'] == 'passed' and bool(quiet)
    result = {'seed':71002,'temperature_C':prep['temperature_C'],'shunt_V':prep['shunt_V'],'codes':prep['fixed_soft_hard_codes'],
              'solver_status':'passed' if complete else 'failed','probe_contract_status':'passed' if valid else 'failed',
              'watchdog_status':state['status'],'returncode':state['returncode'],'wall_s':state['wall_s'],'errors':errors,
              'parameter_audit':params,'wave_analysis':analysis,'quiet_op_V':quiet,'warnings':warning_inventory(log),
              'decisions':{key:value['measured_edge_decision'] for key,value in analysis.get('comparators',{}).items()},
              'scope':prep['scope']}
    (out / 'summary.json').write_text(json.dumps([result],indent=2)+'\n')
    if wave.exists(): archive_new_wave(wave)
    print(json.dumps({key:result[key] for key in ['probe_contract_status','wall_s','decisions','errors']}))
    raise SystemExit(0 if valid else 1)


if __name__ == '__main__': main()
