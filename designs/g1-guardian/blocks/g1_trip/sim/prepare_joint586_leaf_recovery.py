#!/usr/bin/env python3
"""Prepare the single authorized 73034/p09 exact-input watchdog recovery."""
import argparse
import difflib
import json
from pathlib import Path
import re
from run_joint586_calibration import sha, REFERENCE
from result_directory import allocate_run
from run_bgr_substitution_draw_audit import read_group

SIM = Path(__file__).resolve().parent
ROOT = SIM.parents[4]
ORIGINAL = 'joint586-calibration-s73034-20260922-a'


def transform(original, run_id):
    old = 'qualification/'+ORIGINAL+'/p09/phase0.dat'
    new = 'qualification/'+run_id+'/phase0.dat'
    assert original.count(old) == 1
    result = original.replace(old, new)
    assert result.replace(new, old) == original
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id', required=True)
    args = parser.parse_args()
    parent = SIM/'qualification'/ORIGINAL
    leaf = parent/'p09'
    old = json.loads((leaf/'summary.json').read_text())
    state = json.loads((leaf/'run.json').read_text())
    result, = json.loads((parent/'summary.json').read_text())
    provenance = json.loads((parent/'provenance.json').read_text())
    template = json.loads((SIM/'qualification'/REFERENCE/'preparation.json').read_text())
    assert old['status'] == 'failed' and old['watchdog_status'] == 'timeout' and state['timeout_s'] == 1200
    assert old['codes'] == [130, 146] and old['temperature_C'] == 25 and old['shunt_V'] == .025
    assert result['status'] == 'failed calibration' and result['seed'] == 73034
    assert not list(leaf.glob('*.dat*')), 'Unexpected existing waveform; declare an exact prefix gate before recovery'
    text = (leaf/'run.log').read_text()
    before = read_group(text, 'NON_BGR_BEFORE', template['groups']['NON_BGR'])+read_group(text, 'BGR_BEFORE', template['groups']['BGR'])
    assert before == result['parameters_before_first_probe'] and len(before) == 11512
    # This TRANS fixture prints the standalone 27-anchor list only after TRAN.
    # The failed job never reached that command. All 27 keys are already in
    # the exact full BEFORE inventory; do not invent an independent query.
    legacy_subset = [[k, dict(before)[k]] for k in template['groups']['LEGACY27']]
    assert legacy_subset == [[k, dict(result['parameters_before_first_probe'])[k]] for k in template['groups']['LEGACY27']]
    boundary = text.index('Initial Transient Solution')
    warnings = [i for i, line in enumerate(text.splitlines()) if 'WARNING:' in line or 'temperature limiting function received NaN' in line]
    initial_line = len(text[:boundary].splitlines())
    diagnostic = dict(status='failed original 1200 s watchdog; no completed waveform or AFTER inventory',
                      original_run=ORIGINAL+'/p09', full11512_BEFORE_exact=True, legacy27_subset_in_full_BEFORE_exact=True,
                      original_independent_legacy27_query='not run; scheduled after unfinished transient',
                      warnings_before_initial_transient_solution=sum(i < initial_line for i in warnings),
                      warnings_after_initial_transient_solution=sum(i >= initial_line for i in warnings),
                      last_reported_sim_time_s=state['last_reported_sim_time_s'],
                      progress_reference_count=len(re.findall(r'Reference value\s*:', text)),
                      scope='Slow progression near the first hard-evaluation edge; temporal association is not causal attribution. Initialization warnings retained separately from positive-time behavior. Original completed-wave prefix comparison not run because no waveform was exported.')
    out = allocate_run(SIM, args.run_id)
    deck = transform((leaf/'probe.cir').read_text(), out.name)
    (out/'probe.cir').write_text(deck)
    (out/'declared_watchdog_recovery_output.diff').write_text(''.join(difflib.unified_diff((leaf/'probe.cir').read_text().splitlines(True), deck.splitlines(True), fromfile='failed1200sOriginal', tofile='fresh2400sOutputOnly')))
    (out/'original_failure_diagnosis.json').write_text(json.dumps(diagnostic, indent=2)+'\n')
    paths = [leaf/n for n in ['probe.cir', 'run.json', 'run.log', 'summary.json']]+[parent/n for n in ['summary.json', 'provenance.json', 'sense.spice', 'trip.spice', 'bgr.spice', 'population_inventory.json']]+[SIM/n for n in ['prepare_joint586_leaf_recovery.py', 'run_joint586_leaf_recovery.py', 'run_joint586_transients.py', 'run_nominal_clock_probe.py']]
    prep = dict(original_run=ORIGINAL+'/p09', runtime_identity=provenance['runtime_identity'], source_hashes=provenance['source_hashes'],
                groups=template['groups'], prospective_sampling=template['prospective_sampling'], expected11512=before,
                codes=old['codes'], seed=73034, temperature_C=25, shunt_V=.025, watchdog_s=2400,
                deck_sha256=sha(out/'probe.cir'), bindings_sha256={str(p.relative_to(ROOT)): sha(p) for p in paths},
                scope='One distinct same-input 2400 s recovery of original 1200 s failure. Only output path changes in deck; model/source/seed/codes/timing/solver/settings unchanged. Original failed sample is not overwritten, aliased, retried repeatedly, or counted complete by this diagnostic. Full 11512 and 27 before/after plus original BEFORE equality required. No original waveform exists, so original prefix-wave comparison is not run.')
    (out/'preparation.json').write_text(json.dumps(prep, indent=2)+'\n')
    print(json.dumps(dict(run=out.name, deck_sha256=prep['deck_sha256'], original_diagnosis=diagnostic), indent=2))


if __name__ == '__main__':
    main()
