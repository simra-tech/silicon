#!/usr/bin/env python3
"""Independent owncorner adverse sample audit; no filtering or population launch."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import time
from run_joint586_adverse_calibration import adverse_deck, REFERENCE, sha, CONDITIONS, qualification
from audit_bgr_calibration_tree import replay
from run_joint586_transients import phase_parameters
from run_nominal_clock_probe import analyze_wave
from wave_archive import open_wave
from audit_joint586_population_op import variation

SIM = Path(__file__).resolve().parent
ROOT = SIM.parents[4]


def validate_passed_runtime(state,entry,log):
    assert state['status']=='completed' and state['returncode']==0
    assert entry['watchdog_status']==state['status'] and entry['returncode']==state['returncode']
    assert entry['wall_s']==state['wall_s'] and not entry['errors']
    assert 'JOINT_POPULATION_TRAN_END' in log
    assert not any(re.search(r'(?i)(^error|timestep too small|analysis aborted|doAnalyses:|no such vector|no such parameter|not available|cannot parse)',line) for line in log.splitlines())


def first_sample_gate(report):
    if not (report['status'].startswith('passed read-only evidence audit')
            and report['requested_samples']==report['completed_samples']==1):
        return False
    row,=report['records'];leaves=row.get('leaves',[])
    changed=row.get('qualified_control_seed_variation')
    return (row.get('evidence_status')=='passed' and row.get('complete')
        and row.get('bracket_status')=='passed selected probes'
        and sum(r['kind']=='guard' for r in leaves)==40
        and sum(r['kind']=='residual' for r in leaves)==20
        and all(r['status']=='passed' for r in leaves)
        and bool(changed) and sum(r['primitive_count'] for r in changed.values())==3500
        and all(r['primitive_count']==r['primitives_with_changed_values'] for r in changed.values()))


def replay_parent_tree(probes):
    selected = [r for r in probes if r['kind'] == 'calibration']
    # The saved contract is JSON: tuple brackets are arrays on disk. Compare
    # that same representation, not Python tuple identity or audit-only fields.
    return json.loads(json.dumps(replay(selected))) if len(selected) >= 2 else None


def inspect(run, contract_path):
    summary_bytes = (run/'summary.json').read_bytes()
    result, = json.loads(summary_bytes.decode())
    prov = json.loads((run/'provenance.json').read_text())
    ref = SIM/'qualification'/REFERENCE
    prep = json.loads((ref/'preparation.json').read_text())
    assert prov['runtime_identity'] == prep['expected_runtime_identity']
    assert prov['source_hashes'] == result['source_hashes'] == prep['source_hashes']
    assert all(sha(run/name) == value for name, value in prep['source_hashes'].items())
    assert sha(run/'population_inventory.json') == prov['inventory_sha256'] == prep['inventory_sha256']
    assert sha(run/'runner.py') == prov['runner_sha256']
    assert sha(ROOT/prov['qualified_audit']) == prov['qualified_audit_sha256']
    assert sha(ref/'preparation.json') == prov['qualified_preparation_sha256']
    assert sha(ref/'population_transient.cir') == prov['qualified_deck_sha256']
    assert sha(SIM/'run_joint_calibration.py') == prov['original_binary_algorithm_sha256']
    assert sha(SIM/'audit_bgr_calibration_tree.py') == prov['decision_replay_sha256']
    contract=json.loads(contract_path.read_text())
    assert sha(contract_path)==prov['campaign_contract_sha256']
    assert all(sha(ROOT/n)==v for n,v in contract['live_bindings_sha256'].items())
    assert result['corner']==prov['corner'] and prov['conditions']==[list(c) for c in CONDITIONS]
    trans_path=ROOT/prov['qualified_audit']
    fixture_path=SIM/'qualification'/('joint586-'+result['corner']+'-fixture-qualification-20260923.json')
    assert sha(fixture_path)==prov['fixture_audit_sha256']
    qualification(trans_path,fixture_path,result['corner'])
    vector = result['parameters_before_first_probe']
    records = []
    for i, entry in enumerate(result['probes']):
        leaf = run/('p%02d' % i)
        assert entry['run'] == run.name+'/'+leaf.name
        full = json.loads((leaf/'summary.json').read_text())
        assert sha(leaf/'summary.json') == entry['summary_sha256']
        assert all(full[k] == value for k, value in entry.items() if k not in ['summary_sha256', 'expected_decisions'])
        assert entry['corner']==result['corner'] and entry['condition'] in [list(c) for c in CONDITIONS]
        assert entry['temperature_C']==entry['condition'][1]
        deck = adverse_deck((ref/'population_transient.cir').read_text(), ref.name, run.name, result['seed'], entry['codes'], entry['shunt_V'], entry['condition'], result['corner'])
        deck = deck.replace('qualification/'+run.name+'/phase0.dat', 'qualification/'+run.name+'/'+leaf.name+'/phase0.dat')
        assert (leaf/'probe.cir').read_text() == deck and sha(leaf/'probe.cir') == entry['deck_sha256']
        record = dict(entry)
        record['log_sha256'] = sha(leaf/'run.log')
        if entry['status'] == 'passed':
            log=(leaf/'run.log').read_text()
            validate_passed_runtime(json.loads((leaf/'run.json').read_text()),entry,log)
            assert vector and len(vector) == 11512
            section, = re.findall(r'^PHASE0_BEGIN\n(.*?)^PHASE0_END$', (leaf/'run.log').read_text(), re.M | re.S)
            parameters = phase_parameters(section, prep['groups'], vector)
            assert parameters == full['parameter_audit']
            with open_wave(leaf/'phase0.dat', 'rb') as stream:
                payload = stream.read()
            assert hashlib.sha256(payload).hexdigest() == entry['decoded_wave_sha256']
            data = [list(map(float, line.split())) for line in payload.decode().splitlines()[1:] if line.strip()]
            cm=entry['condition'][4];columns=19 if cm is not None else 18
            assert entry['wave_columns']==columns
            assert len(data) == entry['wave_rows'] and all(len(row) == columns and all(math.isfinite(x) for x in row) for row in data)
            assert abs(data[-1][0]-1.02e-6) < 1e-18
            if cm is not None:
                mean=[(r[17]+r[18])/2 for r in data];diff=[r[17]-r[18] for r in data]
                assert max(abs(v-cm) for v in mean)<1e-12 and max(abs(v-entry['shunt_V']) for v in diff)<1e-12
                assert full['actual_input_observation']==dict(mean_common_mode_minmax_V=[min(mean),max(mean)],
                    differential_minmax_V=[min(diff),max(diff)],shn_minmax_V=[min(r[18] for r in data),max(r[18] for r in data)])
            analysis = analyze_wave([row[:13] for row in data], prep['prospective_sampling'])
            assert analysis == full['wave_analysis'] and analysis['sampling_status'] == 'passed'
            assert {key: value['measured_edge_decision'] for key, value in analysis['comparators'].items()} == entry['decisions']
            record['full11512_wave_and_decision_reaudit'] = 'passed'
        else:
            record['full11512_wave_and_decision_reaudit'] = 'not applicable; failed leaf retained'
        records.append(record)
    # Replay the original parent entries. Audit-only log hashes and recheck
    # labels added to records are not fields in the frozen stored tree.
    tree = replay_parent_tree(result['probes'])
    complete = result['status'] not in ['running', 'paused before next leaf']
    if complete and tree and 'calibration' in result:
        assert all(result['calibration'][k] == v for k, v in tree.items() if k != 'scope')
    guards = [r for r in records if r['kind'] == 'guard']
    residuals = [r for r in records if r['kind'] == 'residual']
    if complete and result['bracket_status'] == 'passed selected probes':
        assert tree['bracket_status'] == result['bracket_status'] and len(guards) == 40 and len(residuals) == 20
        expected_guards = [(.027, {'soft': False, 'hard': False}), (.033, {'soft': True, 'hard': False}),
                           (.9*204*1.04/5300, {'soft': True, 'hard': False}), (1.1*204*1.04/5300, {'soft': True, 'hard': True})]
        expected_residuals = [(.0245, {'soft': False, 'hard': False}), (.0255, {'soft': True, 'hard': True})]
        for rows, checks, codekey, statuskey in [(guards, expected_guards, 'corrected_codes', 'guards_status'), (residuals, expected_residuals, 'fixed_residual_codes', 'residual_half_mV_status')]:
            for entry, (condition, shunt, decisions) in zip(rows, [(c, s, d) for c in CONDITIONS for s, d in checks]):
                assert entry['condition']==list(condition) and entry['temperature_C'] == condition[1] and entry['shunt_V'] == shunt and entry['expected_decisions'] == decisions
                assert entry['codes'] == [tree[codekey][key] for key in ['soft', 'hard']]
            assert result[statuskey] == ('passed' if all(r['status'] == 'passed' and r['decisions'] == r['expected_decisions'] for r in rows) else 'failed')
    calibration_entries=[r for r in records if r['kind']=='calibration']
    assert all(r['condition']==list(CONDITIONS[0]) and r['shunt_V']==.025 for r in calibration_entries)
    changed=None
    if vector:
        control=SIM/'qualification'/('joint586-'+result['corner']+'-transqual-shn-20260923-b-enabled')
        control_row,=json.loads((control/'summary.json').read_text())
        changed=variation(control_row['phases'][0]['parameters_before'],vector)
        assert all(v['primitive_count']==v['primitives_with_changed_values'] for v in changed.values())
    return {'run': run.name, 'seed': result['seed'], 'corner':result['corner'],'status': result['status'], 'complete': complete,
            'qualified_control_seed_variation':changed,
            'summary_sha256': hashlib.sha256(summary_bytes).hexdigest(), 'provenance_sha256': sha(run/'provenance.json'),
            'parameter_vector_sha256': hashlib.sha256(json.dumps(vector, separators=(',', ':')).encode()).hexdigest() if vector else None,
            'bracket_status': result['bracket_status'], 'guards_status': result['guards_status'], 'residual_half_mV_status': result['residual_half_mV_status'],
            'leaves': records, 'tree': tree, 'total_core_seconds': sum(r['wall_s'] for r in records)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--first-seed', type=int, required=True)
    parser.add_argument('--last-seed', type=int, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--corner', choices=['slow','fast'],required=True)
    parser.add_argument('--contract',type=Path,required=True)
    args = parser.parse_args()
    first={'slow':77101,'fast':78101}[args.corner]
    assert first<=args.first_seed<=args.last_seed<first+30
    assert not args.output.exists()
    records = []
    for seed in range(args.first_seed, args.last_seed+1):
        run = SIM/'qualification'/('joint586-'+args.corner+'-calibration-s%d-20260923-a' % seed)
        if not (run/'summary.json').exists():
            records.append({'seed': seed, 'run': run.name, 'status': 'not run', 'complete': False})
        else:
            try:
                record = inspect(run,args.contract)
                assert record['seed'] == seed and record['corner']==args.corner
                record['evidence_status']='passed';records.append(record)
            except (AssertionError,OSError,ValueError,KeyError,IndexError) as error:
                records.append(dict(seed=seed,run=run.name,status='failed evidence audit',complete=False,evidence_status='failed',error=repr(error)))
    hashes = [r['parameter_vector_sha256'] for r in records if r.get('parameter_vector_sha256')]
    assert len(hashes) == len(set(hashes)), 'Independent sample vectors unexpectedly duplicated'
    result = {'status': 'failed evidence audit' if any(r.get('evidence_status')=='failed' for r in records) else 'passed read-only evidence audit; electrical failures and unfinished samples separate',
              'corner':args.corner,'campaign_contract_sha256':sha(args.contract),
              'requested_samples': len(records), 'completed_samples': sum(r['complete'] for r in records),
              'fully_passed_samples': sum(r['status'] == 'passed fullcalibration guard residual' for r in records),
              'failed_completed_samples': sum(r['complete'] and r['status'] != 'passed fullcalibration guard residual' for r in records),
              'distinct_full_parameter_vectors': len(hashes), 'total_completed_leaf_core_seconds': sum(r.get('total_core_seconds', 0) for r in records),
              'records': records, 'auditor_sha256': sha(Path(__file__)),
              'scope': 'Owncorner full11512draws, original frozen binary calibration, ten conditions and halfmV residual criteria. All attempted outcomes retained. First20 then30 fixedpopulation gates remain separate; no survivor-yield or newphysicalCC inference.'}
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ['records', 'known_first36_outcomes']}, indent=2))
    raise SystemExit(1 if result['status']=='failed evidence audit' else 0)


if __name__ == '__main__':
    main()
