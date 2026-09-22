#!/usr/bin/env python3
"""Prepare only a219ns prefix of the preserved failed hot substitution."""
import difflib
import hashlib
import json
from pathlib import Path
import re
from result_directory import allocate_run
from run_nominal_clock_probe import validate_saved_nodes

SIM = Path(__file__).resolve().parent
ROOT = SIM.parents[4]
FULL_TRAN = 'tran 0.2n 1.02u 0 0.2n\n'
PREFIX_TRAN = 'tran 0.2n 219n 0 0.2n\n'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def transform(deck, old_id, new_id):
    assert deck.count(FULL_TRAN) == 1
    transformed = deck.replace(old_id, new_id).replace(FULL_TRAN, PREFIX_TRAN)
    assert transformed.replace(new_id, old_id).replace(PREFIX_TRAN, FULL_TRAN) == deck
    return transformed


def require_measurements_inside_prefix(deck, endpoint_s=219e-9):
    measurements = re.findall(r'^meas(?:ure)?\s+tran\s+(\S+).*?\bat=(\S+)', deck, re.M | re.I)
    assert measurements, 'Expected declared transient measurements'
    outside = [(name, value) for name, value in measurements if float(value) > endpoint_s or float(value) < 0]
    assert not outside, 'Future-window measurements invalidate prefix preparation: ' + str(outside)
    return measurements


def main():
    old = SIM / 'qualification/joint-bgr586-nominal-substitution-hot-20260922-a'
    result, = json.loads((old / 'summary.json').read_text())
    assert result['watchdog_status'] == 'timeout' and result['temperature_C'] == 125
    prep = json.loads((old / 'preparation.json').read_text())
    # Guard added after the preserved219ns attempt exposed eight inherited
    # late-window measures. A future preparation must explicitly resolve them;
    # never silently remove/remap commands or rerun the failed fixture.
    require_measurements_inside_prefix((old / (prep['case'] + '.cir')).read_text())
    out = allocate_run(SIM, 'joint-bgr586-hot-prefix219ns-20260922-a')
    for name in ['sense.spice', 'trip.spice', 'bgr.spice', 'non_bgr_inventory.json']:
        (out / name).write_bytes((old / name).read_bytes())
    original = (old / (prep['case'] + '.cir')).read_text()
    deck = transform(original, old.name, out.name)
    (out / (prep['case'] + '.cir')).write_text(deck)
    saved = validate_saved_nodes(deck, (out / 'trip.spice').read_text())
    difference = ''.join(difflib.unified_diff(original.replace(old.name, '@RUN@').splitlines(True),
                        deck.replace(out.name, '@RUN@').splitlines(True), fromfile='preservedFailedHot1p02us', tofile='hotPrefix219ns'))
    (out / 'declared_prefix_difference.diff').write_text(difference)
    bindings = json.loads((old / 'prelaunch_reference_bindings.json').read_text())
    for name in ['summary.json', 'provenance.json', 'preparation.json', 'run.json', 'hard_+0mV.cir',
                 'sense.spice', 'trip.spice', 'bgr.spice', 'non_bgr_inventory.json']:
        bindings['sha256'][str((old / name).relative_to(ROOT))] = sha(old / name)
    assert all(sha(ROOT / name) == value for name, value in bindings['sha256'].items())
    (out / 'prelaunch_reference_bindings.json').write_text(json.dumps(bindings, indent=2) + '\n')
    prep.update(run=out.name, status='prepared only; simulator not run', prefix_reference_run=old.name,
                prepared_deck_sha256=sha(out / (prep['case'] + '.cir')))
    prep['baseline_op_binding_status'] = 'Completed hot originalOP prerequisite retained; complete inventory and livebindings mandatory before prefix launch.'
    prep['prospective_sampling'] = {
        'required_endpoint_s': 219e-9, 'expected_rising_crossings': {'soft': 1, 'hard': 1},
        'clock_threshold_V': .6, 'delay_after_measured_edge_s': 20e-9,
        'legacy_phase_samples_s': {'soft': 40e-9, 'hard': 140.2e-9},
        'internal_observation_offsets_ns': [-1, 0, .2, .5, 1, 20],
        'scope': 'First soft/hard evaluation pair only; not a full20-to220ns period or late steady decisions.',
        'decision_rule': 'Report single first-pair measured-edge and legacy samples separately. Agreement is a timing diagnostic, not original late3sample acceptance.'}
    prep['output_contract'] = 'Exactly18 finite columns through219ns; one actual rising edge per clock. Export all bias/internal vectors and interpolation brackets. Full8670nonBGR+2842nominal BEFORE/AFTER and24anchors mandatory. No late-steady electrical acceptance.'
    prep['unchanged'] = 'Relative to preserved failedhot nominal586 deck: only endpoint1.02us→219ns and output/include run labels change. All source/body/cards/seed/code/clock/solver/tolerances/maxstep/load/stimulus unchanged.'
    prep['scope'] = 'Preparationonly numerical/trajectory diagnostic. First soft/hard evaluation pair, not a full period; no originalhot waveform parity acrossBGR sources, physical qualification, calibration or late-state claim.'
    prep['planning'] = {'watchdog_s': 300, 'home_total_budget_GiB': .10, 'proposed_cpu': 5,
                        'observed_hot_wall_to219ns_approx_s': 226,
                        'forecast_s_including_after_queries_export': [240, 280],
                        'forecast_scope': 'Estimate from archived positive-time progress, not guarantee. No timeout extension or relaunch on failure.',
                        'maximum_new_simulations': 1, 'resource_gate': 'not run; required freshly before launch'}
    (out / 'preparation.json').write_text(json.dumps(prep, indent=2) + '\n')
    audit = {'status': 'passed exact endpoint/output-label transform', 'reference_run': old.name,
             'reference_deck_sha256': sha(old / 'hard_+0mV.cir'), 'prepared_deck_sha256': prep['prepared_deck_sha256'],
             'reverse_transform_byte_exact': transform(original, old.name, out.name) == deck,
             'source_hashes_exact': all(sha(out / name) == value for name, value in prep['source_hashes'].items()),
             'saved_node_audit': saved, 'live_bound_file_count': len(bindings['sha256']),
             'simulator': 'not run', 'runner': 'not run', 'scope': prep['scope']}
    (out / 'prefix_structure_audit.json').write_text(json.dumps(audit, indent=2) + '\n')
    (out / 'preparer.py').write_text(Path(__file__).read_text())
    print(json.dumps(audit, indent=2))


if __name__ == '__main__':
    main()
