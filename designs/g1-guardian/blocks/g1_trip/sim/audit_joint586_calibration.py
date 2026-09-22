#!/usr/bin/env python3
"""Read-only complete/in-progress cohort audit; no sample filtering or relaunch."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
from run_joint586_calibration import calibration_deck, REFERENCE, sha
from audit_bgr_calibration_tree import replay
from run_joint586_transients import phase_parameters
from run_nominal_clock_probe import analyze_wave
from wave_archive import open_wave

SIM = Path(__file__).resolve().parent
ROOT = SIM.parents[4]


def inspect(run):
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
    vector = result['parameters_before_first_probe']
    records = []
    for i, entry in enumerate(result['probes']):
        leaf = run/('p%02d' % i)
        assert entry['run'] == run.name+'/'+leaf.name
        full = json.loads((leaf/'summary.json').read_text())
        assert sha(leaf/'summary.json') == entry['summary_sha256']
        assert all(full[k] == value for k, value in entry.items() if k not in ['summary_sha256', 'expected_decisions'])
        deck = calibration_deck((ref/'population_transient.cir').read_text(), ref.name, run.name, result['seed'], entry['codes'], entry['shunt_V'], entry['temperature_C'])
        deck = deck.replace('qualification/'+run.name+'/phase0.dat', 'qualification/'+run.name+'/'+leaf.name+'/phase0.dat')
        assert (leaf/'probe.cir').read_text() == deck and sha(leaf/'probe.cir') == entry['deck_sha256']
        record = dict(entry)
        record['log_sha256'] = sha(leaf/'run.log')
        if entry['status'] == 'passed':
            assert vector and len(vector) == 11512
            section, = re.findall(r'^PHASE0_BEGIN\n(.*?)^PHASE0_END$', (leaf/'run.log').read_text(), re.M | re.S)
            parameters = phase_parameters(section, prep['groups'], vector)
            assert parameters == full['parameter_audit']
            with open_wave(leaf/'phase0.dat', 'rb') as stream:
                payload = stream.read()
            assert hashlib.sha256(payload).hexdigest() == entry['decoded_wave_sha256']
            data = [list(map(float, line.split())) for line in payload.decode().splitlines()[1:] if line.strip()]
            assert len(data) == entry['wave_rows'] and all(len(row) == 18 and all(math.isfinite(x) for x in row) for row in data)
            assert abs(data[-1][0]-1.02e-6) < 1e-18
            analysis = analyze_wave([row[:13] for row in data], prep['prospective_sampling'])
            assert analysis == full['wave_analysis'] and analysis['sampling_status'] == 'passed'
            assert {key: value['measured_edge_decision'] for key, value in analysis['comparators'].items()} == entry['decisions']
            record['full11512_wave_and_decision_reaudit'] = 'passed'
        else:
            record['full11512_wave_and_decision_reaudit'] = 'not applicable; failed leaf retained'
        records.append(record)
    selected = [r for r in records if r['kind'] == 'calibration']
    tree = replay(selected) if len(selected) >= 2 else None
    complete = result['status'] not in ['running', 'paused before next leaf']
    if complete and tree and 'calibration' in result:
        assert all(result['calibration'][k] == v for k, v in tree.items() if k != 'scope')
    guards = [r for r in records if r['kind'] == 'guard']
    residuals = [r for r in records if r['kind'] == 'residual']
    if complete and result['bracket_status'] == 'passed selected probes':
        assert tree['bracket_status'] == result['bracket_status'] and len(guards) == 12 and len(residuals) == 6
        expected_guards = [(.027, {'soft': False, 'hard': False}), (.033, {'soft': True, 'hard': False}),
                           (.9*204*1.04/5300, {'soft': True, 'hard': False}), (1.1*204*1.04/5300, {'soft': True, 'hard': True})]
        expected_residuals = [(.0245, {'soft': False, 'hard': False}), (.0255, {'soft': True, 'hard': True})]
        for rows, checks, codekey, statuskey in [(guards, expected_guards, 'corrected_codes', 'guards_status'), (residuals, expected_residuals, 'fixed_residual_codes', 'residual_half_mV_status')]:
            for entry, (temp, shunt, decisions) in zip(rows, [(t, s, d) for t in [25, -40, 125] for s, d in checks]):
                assert entry['temperature_C'] == temp and entry['shunt_V'] == shunt and entry['expected_decisions'] == decisions
                assert entry['codes'] == [tree[codekey][key] for key in ['soft', 'hard']]
            assert result[statuskey] == ('passed' if all(r['status'] == 'passed' and r['decisions'] == r['expected_decisions'] for r in rows) else 'failed')
    return {'run': run.name, 'seed': result['seed'], 'status': result['status'], 'complete': complete,
            'summary_sha256': hashlib.sha256(summary_bytes).hexdigest(), 'provenance_sha256': sha(run/'provenance.json'),
            'parameter_vector_sha256': hashlib.sha256(json.dumps(vector, separators=(',', ':')).encode()).hexdigest() if vector else None,
            'bracket_status': result['bracket_status'], 'guards_status': result['guards_status'], 'residual_half_mV_status': result['residual_half_mV_status'],
            'leaves': records, 'tree': tree, 'total_core_seconds': sum(r['wall_s'] for r in records)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--first-seed', type=int, required=True)
    parser.add_argument('--last-seed', type=int, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    records = []
    for seed in range(args.first_seed, args.last_seed+1):
        run = SIM/'qualification'/('joint586-calibration-s%d-20260922-a' % seed)
        if not (run/'summary.json').exists():
            records.append({'seed': seed, 'run': run.name, 'status': 'not run', 'complete': False})
        else:
            record = inspect(run)
            assert record['seed'] == seed
            records.append(record)
    hashes = [r['parameter_vector_sha256'] for r in records if r.get('parameter_vector_sha256')]
    assert len(hashes) == len(set(hashes)), 'Independent sample vectors unexpectedly duplicated'
    result = {'status': 'passed read-only evidence audit; electrical failures and unfinished samples separate',
              'requested_samples': len(records), 'completed_samples': sum(r['complete'] for r in records),
              'fully_passed_samples': sum(r['status'] == 'passed fullcalibration guard residual' for r in records),
              'failed_completed_samples': sum(r['complete'] and r['status'] != 'passed fullcalibration guard residual' for r in records),
              'distinct_full_parameter_vectors': len(hashes), 'total_completed_leaf_core_seconds': sum(r.get('total_core_seconds', 0) for r in records),
              'records': records, 'scope': 'Original frozen binary calibration, guard and halfmV residual criteria. All attempted outcomes retained. New586 fullmismatch population, not nominalBGR equivalence or newphysicalCC qualification; no survivor-yield inference.'}
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'records'}, indent=2))


if __name__ == '__main__':
    main()
