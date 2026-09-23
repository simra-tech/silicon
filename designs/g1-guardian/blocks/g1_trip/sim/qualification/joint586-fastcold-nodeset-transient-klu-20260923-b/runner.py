#!/usr/bin/env python3
"""Bounded full nodeset diagnostics; completion is not fixture adoption."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
from prepare_joint586_fastcold_nodeset_transients import SIM, ROOT, ORIGINAL, sha, transform
from run_joint586_fastcold_klu import qualification
from run_joint586_transients import phase_parameters
from run_nominal_clock_probe import run_bounded, validate_saved_nodes
from audit_joint586_adverse_transients import wave_check
from analyze_bgr_substitution_outcomes import warning_inventory
from wave_archive import archive_new_wave


def numerical_gate(state, errors, log, solver):
    assert state['status'] == 'completed' and state['returncode'] == 0 and not errors
    assert 'JOINT_POPULATION_TRAN_END' in log
    banner = 'Using KLU as Direct Linear Solver' if solver == 'klu' else 'Using SPARSE 1.3 as Direct Linear Solver'
    opposite = 'Using SPARSE 1.3 as Direct Linear Solver' if solver == 'klu' else 'Using KLU as Direct Linear Solver'
    assert banner in log and opposite not in log


def validate_header(blob, deck):
    output, = [l for l in deck.splitlines() if l.startswith('wrdata ')]
    expected = ['time']+output.split()[2:]
    assert len(expected) == 19 and blob.splitlines()[0].decode().split() == expected


def error_lines(log):
    return [l for l in log.splitlines() if re.search(
        r'(?i)(^error|timestep too small|doAnalyses:|no such vector|no such parameter|not available|cannot parse)', l)]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--contract', type=Path, required=True)
    p.add_argument('--contract-sha256', required=True)
    p.add_argument('--solver', choices=['sparse', 'klu'], required=True)
    p.add_argument('--image-id', required=True)
    p.add_argument('--qualification-audit', type=Path, required=True)
    a = p.parse_args()
    assert sha(a.contract) == a.contract_sha256
    packet = json.loads(a.contract.read_text())
    case, = [c for c in packet['cases'] if c['solver'] == a.solver]
    prep = packet['original_preparation']
    out = SIM/'qualification'/case['run']
    deck = out/'population_transient.cir'
    assert not (out/'run.log').exists()
    assert all(sha(ROOT/n) == v for n, v in packet['bindings_sha256'].items())
    expected, audit = transform((ORIGINAL/'population_transient.cir').read_text(), case['run'], a.solver,
        packet['guesses_original_printed_strings'])
    assert deck.read_text() == expected and sha(deck) == case['deck_sha256']
    assert json.loads((out/'transform_audit.json').read_text()) == audit
    assert sha(out/'transform_audit.json') == case['transform_sha256']
    assert all(sha(out/n) == sha(ORIGINAL/n) == v for n, v in packet['source_hashes'].items())
    qualification(a.qualification_audit, prep)
    validate_saved_nodes(expected, (out/'trip.spice').read_text())
    pd = Path('/foss/pdks/ihp-sg13g2')
    runtime = dict(image_id_observed_by_host=a.image_id, pdk_commit=(pd/'COMMIT').read_text().strip(),
        ngspice_version=subprocess.check_output(['ngspice', '--version'], universal_newlines=True),
        model_sha256={str(f.relative_to(pd)): sha(f) for f in (pd/'libs.tech/ngspice/models').rglob('*') if f.is_file()}, solver=a.solver)
    assert runtime == dict(prep['expected_runtime_identity'], solver=a.solver)
    (out/'runner.py').write_text(Path(__file__).read_text())
    (out/'provenance.json').write_text(json.dumps(dict(arguments=sys.argv[1:], runtime_identity=runtime,
        contract_sha256=sha(a.contract), qualified_audit_sha256=sha(a.qualification_audit),
        source_hashes=packet['source_hashes'], runner_sha256=sha(Path(__file__)),
        input_checks=dict(deck=True, bindings=True, sources=True, runtime=True, original_own_TRANS=True)), indent=2)+'\n')
    with (out/'run.log').open('x') as stream:
        state = run_bounded(['ngspice', '-b', str(deck.relative_to(SIM))], stream, out/'run.json', 1200, cwd=SIM, interval_s=1)
    log = (out/'run.log').read_text()
    errors = error_lines(log)
    result = dict(status='failed full nodeset diagnostic', numerical_completion='failed',
        parameter_wave_status='not run', decision_sampling_status='not run', runtime=state, errors=errors,
        warnings=warning_inventory(log), scope=packet['scope'], solver=a.solver,
        original_fullwave_comparison='not run: original failed fixture has no completed full wave',
        pair_wave_comparison='not run: independent pair analysis requires both terminal outputs')
    try:
        numerical_gate(state, errors, log, a.solver)
        result['numerical_completion'] = 'passed'
        section, = re.findall(r'^PHASE0_BEGIN\n(.*?)^PHASE0_END$', log, re.M|re.S)
        params = phase_parameters(section, prep['groups'], prep['expected_vector'])
        blob = (out/'phase0.dat').read_bytes()
        validate_header(blob, expected)
        data, analysis = wave_check(blob, 19, prep['prospective_sampling'])
        cm = prep['condition'][4]
        mean = [(r[17]+r[18])/2 for r in data]
        differential = [r[17]-r[18] for r in data]
        assert max(abs(v-cm) for v in mean) < 1e-12
        assert max(abs(v-.025) for v in differential) < 1e-12
        result.update(parameter_wave_status='passed', parameters=params, wave_analysis=analysis,
            decoded_wave_sha256=sha(out/'phase0.dat'), wave_rows=len(data),
            actual_input_observation=dict(mean_common_mode_minmax_V=[min(mean), max(mean)],
                differential_minmax_V=[min(differential), max(differential)]),
            decision_sampling_status=analysis['sampling_status'],
            decisions={k: v['measured_edge_decision'] for k, v in analysis['comparators'].items()},
            status='passed finite fullparameter nodeset diagnostic; decisions and exact comparisons separate')
    except (AssertionError, ValueError, KeyError, OSError, IndexError) as error:
        result.update(status='failed full nodeset diagnostic', analysis_error=repr(error))
    (out/'summary.json').write_text(json.dumps([result], indent=2)+'\n')
    if (out/'phase0.dat').exists():
        archive_new_wave(out/'phase0.dat')
    print(json.dumps({k:v for k,v in result.items() if k not in ['warnings', 'parameters', 'wave_analysis']}, indent=2))
    raise SystemExit(0 if result['status'].startswith('passed finite') else 1)


if __name__ == '__main__':
    main()
