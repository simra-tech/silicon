#!/usr/bin/env python3
"""Prepare a hot baseline OP prerequisite and two nominalBGR substitutions; never run."""
import hashlib
import json
from pathlib import Path
import difflib
import re
from result_directory import allocate_run
from prepare_bgr_substitution_draw_audit import CANDIDATE, CANDIDATE_SHA, inventory_non_bgr

SIM = Path(__file__).resolve().parent
ROOT = SIM.parents[4]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def main():
    room_op = SIM / 'qualification/joint-bgr586-drawaudit-baseline-room-20260922-a'
    candidate_op = SIM / 'qualification/joint-bgr586-drawaudit-candidate-room-20260922-a'
    base_prep = json.loads((room_op / 'preparation.json').read_text())
    candidate_prep = json.loads((candidate_op / 'preparation.json').read_text())
    assert sha(CANDIDATE) == CANDIDATE_SHA
    parity = SIM / '../reports/resume-server-20260922/joint-bgr586-room-full-draw-parity.json'
    audit = json.loads(parity.read_text())
    assert all(audit['checks'].values()) and not audit['nonBGR_parameter_changes']
    hot_ref = SIM / 'qualification/joint-gm4comp3-s71002-bias-observation-hot-20260922-a'
    hot_summary, = json.loads((hot_ref / 'summary.json').read_text())
    assert hot_summary['temperature_C'] == 125 and hot_summary['output_only_qualification_status'] == 'passed'
    hot_id = 'joint-bgr586-drawaudit-baseline-hot-20260922-a'
    hot_out = allocate_run(SIM, hot_id)
    hot_old_deck = (hot_ref / 'hard_+0mV.cir').read_text()
    hot_deck = hot_old_deck.split('.control\n')[0].replace(hot_ref.name, hot_id)
    hot_deck += '.control\n' + (room_op / 'draw_audit.cir').read_text().split('.control\n')[1]
    assert '.temp 125.0\n' in hot_deck and not re.search(r'^tran\b', hot_deck, re.M)
    for name in ['sense.spice', 'trip.spice', 'bgr.spice']:
        (hot_out / name).write_bytes((hot_ref / name).read_bytes())
    (hot_out / 'draw_audit.cir').write_text(hot_deck)
    (hot_out / 'non_bgr_inventory.json').write_bytes((room_op / 'non_bgr_inventory.json').read_bytes())
    (hot_out / 'preparer.py').write_text(Path(__file__).read_text())
    hot_prep = dict(base_prep)
    hot_prep.update(run=hot_id, temperature_C=125, reference_run=hot_ref.name,
                    deck_sha256=sha(hot_out / 'draw_audit.cir'),
                    legacy27_expected=dict(hot_summary['fingerprints']),
                    non_bgr24_expected={k: v for k, v in hot_summary['fingerprints'] if '.xbgr.' not in k})
    hot_prep['stimulus_scope'] = 'Exact originalhot125C fixture prefix andinitialization; OPonlyfull8670inventory prerequisite fornewhot source substitution. NoTRAN.'
    write_json(hot_out / 'preparation.json', hot_prep)
    diff = ''.join(difflib.unified_diff(hot_old_deck.replace(hot_ref.name, '@RUN@').splitlines(True),
                hot_deck.replace(hot_id, '@RUN@').splitlines(True), fromfile='preservedHot5MHz', tofile='hotBaselineOpOnly'))
    (hot_out / 'declared_draw_audit_difference.diff').write_text(diff)
    bindings = {'scope': 'Live originalhotreference and nominalBGRmanifest bindings forOP-only prerequisite.',
                'sha256': {str((hot_ref / name).relative_to(ROOT)): sha(hot_ref / name)
                           for name in ['summary.json', 'provenance.json', 'preparation.json', 'sense.spice', 'trip.spice', 'bgr.spice', 'hard_+0mV.cir']}}
    nominal = ROOT / base_prep['candidate_nominal_reference']
    assert sha(nominal) == base_prep['candidate_nominal_reference_manifest_sha256']
    bindings['sha256'][str(nominal.relative_to(ROOT))] = sha(nominal)
    write_json(hot_out / 'prelaunch_reference_bindings.json', bindings)
    rows = [{'run': hot_id, 'kind': 'hotbaselineOPonly', 'deck_sha256': hot_prep['deck_sha256']}]
    for phase, temperature, expected_op in [('room', 25, room_op), ('hot', 125, hot_out)]:
        reference = SIM / 'qualification' / ('joint-gm4comp3-s71002-bias-observation-' + phase + '-20260922-a')
        original_prep = json.loads((reference / 'preparation.json').read_text())
        original_result, = json.loads((reference / 'summary.json').read_text())
        assert original_result['output_only_qualification_status'] == 'passed' and original_result['temperature_C'] == temperature
        run_id = 'joint-bgr586-nominal-substitution-' + phase + '-20260922-a'
        out = allocate_run(SIM, run_id)
        for name in ['sense.spice', 'trip.spice']:
            (out / name).write_bytes((reference / name).read_bytes())
        (out / 'bgr.spice').write_bytes(CANDIDATE.read_bytes())
        inventory = inventory_non_bgr((out / 'sense.spice').read_text(), (out / 'trip.spice').read_text())
        write_json(out / 'non_bgr_inventory.json', inventory)
        old = (reference / 'hard_+0mV.cir').read_text()
        deck = old.replace(reference.name, run_id)
        for phase_tag, insertion in [('BEFORE', 'tran 0.2n 1.02u 0 0.2n\n'), ('AFTER', 'let ds = v(xt.icmp)-v(xt.vth_soft)\n')]:
            assert deck.count(insertion) == 1
            observation = ''
            for group, queries in [('NON_BGR', inventory['queries']), ('BGR', candidate_prep['bgr_queries'])]:
                tag = group + '_' + phase_tag
                observation += 'echo ' + tag + '_BEGIN\n' + ''.join('print ' + key + '\n' for key in queries) + 'echo ' + tag + '_END\n'
            deck = deck.replace(insertion, observation + insertion)
        assert deck.count('tran 0.2n 1.02u 0 0.2n') == 1
        (out / 'hard_+0mV.cir').write_text(deck)
        (out / 'preparer.py').write_text(Path(__file__).read_text())
        diff = ''.join(difflib.unified_diff(old.replace(reference.name, '@RUN@').splitlines(True),
                    deck.replace(run_id, '@RUN@').splitlines(True), fromfile='preserved5MHzSamePhase', tofile='nominalBgr586Substitution'))
        (out / 'declared_substitution_difference.diff').write_text(diff)
        record = {
            'status': 'prepared only; simulator not run', 'run': run_id, 'reference_run': reference.name,
            'temperature_C': temperature, 'seed': 71002, 'shunt_V': .0245, 'fixed_soft_hard_codes': [136, 154],
            'source_hashes': {name: sha(out / name) for name in ['sense.spice', 'trip.spice', 'bgr.spice']},
            'prepared_deck_sha256': sha(out / 'hard_+0mV.cir'), 'case': 'hard_+0mV',
            'expected_runtime_identity': original_prep['expected_runtime_identity'],
            'prospective_sampling': original_prep['prospective_sampling'], 'wave_columns': original_prep['wave_columns'],
            'non_bgr24_expected': {key: value for key, value in original_result['fingerprints'] if '.xbgr.' not in key},
            'original27_observations': original_result['fingerprints'],
            'required_baseline_op_run': expected_op.name,
            'baseline_op_binding_status': 'completed8670inventory exists; bindhash live beforelaunch' if phase == 'room' else 'not run; prerequisite must complete andhashmustbind beforeanynewhottransient',
            'non_bgr_inventory_sha256': sha(out / 'non_bgr_inventory.json'),
            'candidate2842_queries': candidate_prep['bgr_queries'],
            'candidate2842_nominal_expected': candidate_prep['expected_candidate2842_nominal_values'],
            'candidate_nominal_reference': candidate_prep['candidate_nominal_reference'],
            'candidate_nominal_reference_sha256': candidate_prep['candidate_nominal_reference_manifest_sha256'],
            'reference_hashes': {name: sha(reference / name) for name in ['summary.json', 'provenance.json', 'preparation.json', 'hard_+0mV.cir', 'sense.spice', 'trip.spice', 'bgr.spice']},
            'completed_room_draw_parity_sha256': sha(parity),
            'parameter_contract': 'Full8670nonBGR keys/order/values before andafter must exactly equal same-temperature originalbaselineOP inventory, including6CMIMscales; original24anchors exact. NewBGR2842before/after must exactly equal retainednominalvalues. Original3BGRvalues are distinct andreported, never incorrectly requiredunchanged. Any mismatch invalidatesdiagnostic comparison.',
            'output_contract': 'Same18finite bias/internalwavecolumns andfullendpoint1.02us; sameactualclock0.6risingedge+20ns late3cycles andretainedlegacy decisions. Source substitution is expectedtochange waveforms; no samewaveparity claim.',
            'unchanged': 'ExactSENSE/TRIPsource/body/cards/rails/shunt/loads/codes/clock/solver/tolerances/maxstep/endpoint; onlyBGRsourcebytes substituted andbefore/afterparameterobservationsadded. No recalibration, temperaturewaiver or acceptance rewrite.',
            'planning': {'watchdog_s': 600, 'home_total_budget_GiB': .15, 'proposed_cpu': 5 if phase == 'room' else 10},
            'scope': 'Preparationonly. Does definednominalBGRsubstitution change retainedroom/hot failureunderoldcalibrationcodes? DifferentBGR andnominaloffset; notnewfullcalibration, BGRmismatchpopulation, jointMC, physicalPEX/reliability orcandidateadoption. No launchauthorized.'}
        write_json(out / 'preparation.json', record)
        rows.append({'run': run_id, 'kind': 'preparedonlynominalBGRsubstitution', 'deck_sha256': record['prepared_deck_sha256'],
                     'required_baseline_op_run': expected_op.name})
    print(json.dumps(rows, indent=2))


if __name__ == '__main__':
    main()
