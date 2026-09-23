#!/usr/bin/env python3
"""Staged owncorner sample; independent held-out leaves, unchanged serial inputs."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys
from audit_bgr_calibration_tree import replay
from prepare_bgr_calibration_probe import transform
from result_directory import allocate_run
from run_joint586_transients import phase_parameters
from run_bgr_substitution_draw_audit import read_group
from run_nominal_clock_probe import analyze_wave, validate_saved_nodes, run_bounded
from analyze_bgr_substitution_outcomes import warning_inventory
from wave_archive import archive_new_wave
from prepare_joint586_adverse import CONDITIONS, transform_fixture
from prepare_joint586_adverse_transients import append_shn

SIM = Path(__file__).resolve().parent
ROOT = SIM.parents[4]
REFERENCE = 'joint586-mm-tranqual-20260922-a-enabled'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def calibration_deck(original, old_id, new_id, seed, codes, shunt, temp):
    result = transform(original, old_id, new_id, *codes, shunt, temp)
    assert result.count('setseed 73001\n') == 1
    return result.replace('setseed 73001\n', 'setseed %d\n' % seed)


def check_pause(path):
    if path is not None and path.exists():
        raise InterruptedError('Explicit pause before next leaf')


def adverse_deck(original, old_id, new_id, seed, codes, shunt, condition, corner):
    label, temp, vdda, vdd, cm = condition
    deck = calibration_deck(original, old_id, new_id, seed, codes, shunt, temp)
    deck, changes = transform_fixture(deck, corner, vdda, vdd, cm, shunt)
    return append_shn(deck) if cm is not None else deck


def qualification(trans_path, fixture_path, corner):
    trans = json.loads(trans_path.read_text())
    assert trans['status'] == 'passed strict owncorner TRANS qualification' and trans['corner'] == corner
    assert all(trans['checks'].values()) and not trans['audit_errors']
    fixture = json.loads(fixture_path.read_text())
    assert fixture['status'] == 'passed six required owncorner fixture controls' and fixture['corner'] == corner
    assert fixture['transient_audit_sha256'] == sha(trans_path)
    for row in fixture['records']:
        run = SIM/'qualification'/row['run']
        assert row['status'] == 'passed required fixture control'
        assert all(sha(run/n) == v for n,v in row['receipts_sha256'].items())
    assert len(fixture['records']) == 6
    for label,receipts in trans['receipts_sha256'].items():
        run = SIM/'qualification'/('joint586-'+corner+'-transqual-shn-20260923-b-'+label)
        assert all(sha(run/n) == v for n,v in receipts.items())
    return trans, fixture


def heldout_plan(tree, first_index):
    guards = [(.027, {'soft': False, 'hard': False}), (.033, {'soft': True, 'hard': False}),
              (.9*204*1.04/5300, {'soft': True, 'hard': False}), (1.1*204*1.04/5300, {'soft': True, 'hard': True})]
    residuals = [(.0245, {'soft': False, 'hard': False}), (.0255, {'soft': True, 'hard': True})]
    rows = []
    for kind, key, values in [('guard', 'corrected_codes', guards), ('residual', 'fixed_residual_codes', residuals)]:
        codes = [tree[key][k] for k in ['soft', 'hard']]
        for condition in CONDITIONS:
            for shunt, expected in values:
                rows.append(dict(index=first_index+len(rows), codes=codes[:], shunt_V=shunt,
                                 condition=list(condition), kind=kind, expected_decisions=expected.copy()))
    assert len(rows) == 60 and len({r['index'] for r in rows}) == 60
    return rows


def freeze_plan(out, result, original, reference):
    assert result['bracket_status'] == 'passed selected probes'
    rows = heldout_plan(result['calibration'], len(result['probes']))
    for row in rows:
        deck = adverse_deck(original, reference, out.name, result['seed'], row['codes'],
                            row['shunt_V'], row['condition'], result['corner'])
        deck = deck.replace('qualification/'+out.name+'/phase0.dat',
                            'qualification/'+out.name+'/p%02d/phase0.dat' % row['index'])
        row['deck_sha256'] = hashlib.sha256(deck.encode()).hexdigest()
    packet = dict(seed=result['seed'], corner=result['corner'], rows=rows,
                  vector=result['parameters_before_first_probe'],
                  calibration_summary_sha256=sha(out/'summary.json'),
                  provenance_sha256=sha(out/'provenance.json'),
                  runner_sha256=sha(Path(__file__)))
    with (out/'heldout_plan.json').open('x') as stream:
        json.dump(packet, stream, indent=2); stream.write('\n')
    with (out/'heldout_plan.sha256').open('x') as stream:
        stream.write(sha(out/'heldout_plan.json')+'\n')
    return packet


def load_plan(out, result):
    assert sha(out/'heldout_plan.json') == (out/'heldout_plan.sha256').read_text().strip()
    plan = json.loads((out/'heldout_plan.json').read_text())
    assert plan['runner_sha256'] == sha(Path(__file__)) == sha(out/'runner.py')
    assert plan['provenance_sha256'] == sha(out/'provenance.json')
    assert plan['calibration_summary_sha256'] == sha(out/'summary.json')
    assert plan['vector'] == result['parameters_before_first_probe'] and len(plan['vector']) == 11512
    assert (plan['seed'], plan['corner']) == (result['seed'], result['corner'])
    expected = heldout_plan(result['calibration'], len(result['probes']))
    assert [{k:v for k,v in row.items() if k != 'deck_sha256'} for row in plan['rows']] == expected
    return plan


def collect_entries(out, plan):
    entries = []
    for row in plan['rows']:
        leaf = out/('p%02d' % row['index'])
        entry = json.loads((leaf/'entry.json').read_text())
        assert entry['run'] == out.name+'/'+leaf.name
        assert sha(leaf/'summary.json') == entry['summary_sha256']
        assert sha(leaf/'probe.cir') == row['deck_sha256'] == entry['deck_sha256']
        assert all(entry[k] == row[k] for k in ['codes','shunt_V','condition','kind','expected_decisions'])
        entries.append(entry)
    return entries


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run-id', required=True)
    p.add_argument('--image-id', required=True)
    p.add_argument('--seed', type=int, required=True)
    p.add_argument('--qualification-audit', type=Path, required=True)
    p.add_argument('--fixture-audit', type=Path, required=True)
    p.add_argument('--corner', choices=['slow','fast'], required=True)
    p.add_argument('--campaign-contract', type=Path, required=True)
    p.add_argument('--stop-file', type=Path)
    p.add_argument('--stage', choices=['calibrate','leaf','assemble'], required=True)
    p.add_argument('--leaf-index', type=int)
    a = p.parse_args()
    assert (a.stage == 'leaf') == (a.leaf_index is not None)
    first = {'slow':77101,'fast':78101}[a.corner]
    assert first <= a.seed < first+30
    contract=json.loads(a.campaign_contract.read_text())
    assert contract['staged_execution']['runner_sha256'] == sha(Path(__file__))
    assert contract['population_seeds'][a.corner]==list(range(first,first+30))
    assert contract['conditions']==[list(c) for c in CONDITIONS]
    assert contract['sample_count_per_corner']==30 and contract['watchdog_per_leaf_s']==1200
    assert all(sha(ROOT/n)==v for n,v in contract['live_bindings_sha256'].items())
    audit, fixture_audit = qualification(a.qualification_audit, a.fixture_audit, a.corner)
    ref = SIM/'qualification'/REFERENCE
    prep = json.loads((ref/'preparation.json').read_text())
    original = (ref/'population_transient.cir').read_text()
    assert prep['fixed_codes'] == [135, 151] and prep['shunt_V'] == .025 and prep['mismatch_enabled']
    pd = Path('/foss/pdks/ihp-sg13g2')
    runtime = {'image_id_observed_by_host': a.image_id, 'pdk_commit': (pd/'COMMIT').read_text().strip(),
               'ngspice_version': subprocess.check_output(['ngspice', '--version'], universal_newlines=True),
               'model_sha256': {str(f.relative_to(pd)): sha(f) for f in (pd/'libs.tech/ngspice/models').rglob('*') if f.is_file()}, 'solver': 'sparse'}
    assert runtime == prep['expected_runtime_identity']
    assert all(sha(ref/name) == digest for name, digest in prep['source_hashes'].items())
    assert sha(ref/'population_inventory.json') == prep['inventory_sha256']
    out = allocate_run(SIM, a.run_id) if a.stage == 'calibrate' else SIM/'qualification'/a.run_id
    if a.stage == 'calibrate':
        for name in ['sense.spice', 'trip.spice', 'bgr.spice', 'population_inventory.json']:
            shutil.copyfile(str(ref/name), str(out/name))
        shutil.copyfile(str(Path(__file__)), str(out/'runner.py'))
    else:
        assert all(sha(out/n) == v for n,v in prep['source_hashes'].items())
        assert sha(out/'population_inventory.json') == prep['inventory_sha256']
        assert sha(out/'runner.py') == sha(Path(__file__))
    qualification_path = a.qualification_audit if a.qualification_audit.is_absolute() else Path.cwd()/a.qualification_audit
    provenance = {'arguments': sys.argv[1:], 'runner_sha256': sha(Path(__file__)), 'runtime_identity': runtime,
                  'source_hashes': prep['source_hashes'], 'inventory_sha256': prep['inventory_sha256'],
                  'qualified_transient_run': REFERENCE, 'qualified_audit': str(qualification_path.relative_to(ROOT)),
                  'qualified_audit_sha256': sha(a.qualification_audit), 'qualified_preparation_sha256': sha(ref/'preparation.json'),
                  'fixture_audit_sha256': sha(a.fixture_audit), 'corner':a.corner, 'conditions':CONDITIONS,
                  'campaign_contract_sha256':sha(a.campaign_contract),
                  'execution_schedule': 'Sequential binary calibration; immutable indexed60 heldout leaves; parent-only ordered assembly. Each leaf is an independent one-thread ngspice process with original1200s bound.',
                  'qualified_deck_sha256': sha(ref/'population_transient.cir'),
                  'original_binary_algorithm_sha256': sha(SIM/'run_joint_calibration.py'),
                  'decision_replay_sha256': sha(SIM/'audit_bgr_calibration_tree.py'),
                  'physical_scope': prep['physical_scope'],
                  'scope': 'One independent owncorner full11512 draw, fixed30 denominator. Samecorner25C nominalrail SHN0 originalbinary calibration; frozen signedcorrection/rounding/clipping/hard204. Ten declared temp/rail/trueCM conditions each four originalguards plus two halfmV residuals; no heldout recalibration. Clock/codeHIGH tracks VDD, original0.6V/20ns actual+legacy rules,1.02us/1200s. ActualSHN19 append only at trueCM conditions; legacy18 otherwise. No physicalCC/siliconyield qualification.'}
    if a.stage == 'calibrate':
        (out/'provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
    else:
        saved = json.loads((out/'provenance.json').read_text())
        assert all(saved[k] == v for k,v in provenance.items() if k != 'arguments')
    result = {'seed': a.seed, 'corner':a.corner, 'status': 'running', 'bracket_status': 'not run', 'guards_status': 'not run',
              'residual_half_mV_status': 'not run', 'probes': [], 'source_hashes': prep['source_hashes'],
              'scope': provenance['scope'], 'parameters_before_first_probe': None}

    def persist():
        (out/'summary.json').write_text(json.dumps([result], indent=2)+'\n')

    if a.stage == 'calibrate':
        persist()
        vector = None
        plan = None
    else:
        result, = json.loads((out/'summary.json').read_text())
        plan = load_plan(out, result)
        vector = plan['vector']

    def probe(codes, shunt=.025, condition=CONDITIONS[0], kind='calibration', explicit_index=None):
        nonlocal vector
        check_pause(a.stop_file)
        index = len(result['probes']) if explicit_index is None else explicit_index
        leaf = out/('p%02d' % index)
        leaf.mkdir()
        # Sources stay at the parent logical path; only wave output moves below it.
        label,temp,vdda,vdd,cm = condition
        deck = adverse_deck(original, ref.name, out.name, a.seed, codes, shunt, condition, a.corner)
        oldwave = 'qualification/'+out.name+'/phase0.dat'
        newwave = 'qualification/'+out.name+'/'+leaf.name+'/phase0.dat'
        assert deck.count(oldwave) == 1
        deck = deck.replace(oldwave, newwave)
        if explicit_index is not None:
            declared, = [r for r in plan['rows'] if r['index'] == explicit_index]
            assert hashlib.sha256(deck.encode()).hexdigest() == declared['deck_sha256']
        validate_saved_nodes(deck, (out/'trip.spice').read_text())
        (leaf/'probe.cir').write_text(deck)
        with (leaf/'run.log').open('x') as logstream:
            state = run_bounded(['ngspice', '-b', str((leaf/'probe.cir').relative_to(SIM))], logstream, leaf/'run.json', 1200, cwd=SIM, interval_s=1)
        log = (leaf/'run.log').read_text()
        errors = [line for line in log.splitlines() if re.search(r'(?im)^Error|Timestep too small|analysis aborted|doAnalyses:|no such vector|no such parameter|not available|cannot parse', line)]
        entry = {'run': out.name+'/'+leaf.name, 'kind': kind, 'codes': codes, 'shunt_V': shunt, 'temperature_C': temp,
                 'condition':list(condition),'corner':a.corner,'wave_columns':19 if cm is not None else 18,
                 'status': 'failed', 'wall_s': state['wall_s'], 'watchdog_status': state['status'], 'returncode': state['returncode'],
                 'errors': errors, 'deck_sha256': sha(leaf/'probe.cir'), 'decisions': {}}
        full = {'warnings': warning_inventory(log)}
        try:
            assert state['status'] == 'completed' and state['returncode'] == 0 and not errors and 'JOINT_POPULATION_TRAN_END' in log
            section, = re.findall(r'^PHASE0_BEGIN\n(.*?)^PHASE0_END$', log, re.M | re.S)
            before = read_group(section, 'NON_BGR_BEFORE', prep['groups']['NON_BGR'])+read_group(section, 'BGR_BEFORE', prep['groups']['BGR'])
            expected = vector if vector is not None else before
            params = phase_parameters(section, prep['groups'], expected)
            if vector is None:
                assert a.stage == 'calibrate'
                vector = before
                result['parameters_before_first_probe'] = before
            data = [list(map(float, line.split())) for line in (leaf/'phase0.dat').read_text().splitlines()[1:] if line.strip()]
            assert data and all(len(row) == entry['wave_columns'] and all(math.isfinite(v) for v in row) for row in data)
            assert abs(data[-1][0]-1.02e-6) < 1e-18
            if cm is not None:
                mean=[(r[17]+r[18])/2 for r in data];diff=[r[17]-r[18] for r in data]
                assert max(abs(v-cm) for v in mean)<1e-12 and max(abs(v-shunt) for v in diff)<1e-12
                full['actual_input_observation']=dict(mean_common_mode_minmax_V=[min(mean),max(mean)],
                    differential_minmax_V=[min(diff),max(diff)],shn_minmax_V=[min(r[18] for r in data),max(r[18] for r in data)])
            analysis = analyze_wave([row[:13] for row in data], prep['prospective_sampling'])
            assert analysis['sampling_status'] == 'passed'
            decisions = {key: row['measured_edge_decision'] for key, row in analysis['comparators'].items()}
            assert set(decisions) == {'soft', 'hard'} and all(type(v) is bool for v in decisions.values())
            full.update(parameter_audit=params, wave_analysis=analysis)
            entry.update(status='passed', decisions=decisions, decoded_wave_sha256=sha(leaf/'phase0.dat'), wave_rows=len(data))
        except (AssertionError, ValueError, OSError, KeyError, IndexError) as error:
            entry['analysis_error'] = repr(error)
        (leaf/'summary.json').write_text(json.dumps(dict(entry, **full), indent=2)+'\n')
        entry['summary_sha256'] = sha(leaf/'summary.json')
        if explicit_index is None:
            result['probes'].append(entry)
            persist()
        if (leaf/'phase0.dat').exists():
            archive_new_wave(leaf/'phase0.dat')
        return entry

    if a.stage == 'leaf':
        row, = [r for r in plan['rows'] if r['index'] == a.leaf_index]
        entry = probe(row['codes'], row['shunt_V'], row['condition'], row['kind'], row['index'])
        entry['expected_decisions'] = row['expected_decisions']
        leaf = out/('p%02d' % row['index'])
        with (leaf/'entry.json').open('x') as stream:
            json.dump(entry, stream, indent=2); stream.write('\n')
        print(json.dumps(entry, indent=2))
        return

    if a.stage == 'assemble':
        entries = collect_entries(out, plan)
        result['probes'] += entries
        for kind, key in [('guard','guards_status'),('residual','residual_half_mV_status')]:
            rows = [r for r in entries if r['kind'] == kind]
            result[key] = 'passed' if all(r['status']=='passed' and r['decisions']==r['expected_decisions'] for r in rows) else 'failed'
        result['status'] = 'passed fullcalibration guard residual' if result['guards_status'] == result['residual_half_mV_status'] == 'passed' else 'failed electrical or numerical check'
        result['total_core_seconds'] = sum(p['wall_s'] for p in result['probes'])
        # Preserve the immutable calibration checkpoint used by all independent leaves.
        shutil.copyfile(str(out/'summary.json'), str(out/'calibration_checkpoint.json'))
        persist()
        print(json.dumps(dict(status=result['status'], heldout_count=len(entries)), indent=2))
        return

    try:
        # Exact original endpoints and midpoint decisions; no speculative cache.
        probe([0, 0])
        probe([255, 255])
        while True:
            tree = replay([r for r in result['probes'] if r['kind'] == 'calibration'])
            tree['scope'] = 'Original binary rule and code-pair policy at samecorner25C nominalrails originalSHN0; no recalibration at heldout conditions.'
            result['calibration'] = tree
            persist()
            if 'next_required_codes' not in tree or tree['bracket_status'].startswith('failed'):
                break
            probe(tree['next_required_codes'])
        result['bracket_status'] = tree['bracket_status']
        if tree['bracket_status'] != 'passed selected probes':
            result['status'] = 'failed calibration'
        else:
            result['status'] = 'calibration frozen; independent heldout leaves not run'
            persist()
            freeze_plan(out, result, original, ref.name)
            return
    except InterruptedError as error:
        result['status'] = 'paused before next leaf'
        result['pause_reason'] = str(error)
    result['total_core_seconds'] = sum(p['wall_s'] for p in result['probes'])
    persist()
    print(json.dumps({k: v for k, v in result.items() if k not in ['probes', 'parameters_before_first_probe', 'calibration']}, indent=2))


if __name__ == '__main__':
    main()
