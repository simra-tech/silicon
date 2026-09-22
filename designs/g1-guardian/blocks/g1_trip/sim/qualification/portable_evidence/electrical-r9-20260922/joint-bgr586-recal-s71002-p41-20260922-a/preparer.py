#!/usr/bin/env python3
"""Prepare a declared seed71002 nominal586 calibration stimulus from qualified fullhot."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import re
from result_directory import allocate_run

SIM = Path(__file__).resolve().parent
ROOT = SIM.parents[4]
REFERENCE = 'joint-bgr586-fullhot1200s-20260922-a'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized_stimulus(deck):
    return re.sub(r'^(\.temp|Vsh shp 0 dc|V[sh][0-7] [sh][0-7] 0 dc) .+$', r'\1 @SWEEP@', deck, flags=re.M)


def transform(deck, old_id, new_id, soft, hard, shunt, temperature):
    assert all(isinstance(code, int) and 0 <= code <= 255 for code in [soft, hard])
    assert 0 <= shunt <= .05 and temperature in [25., -40., 125.]
    result = deck.replace(old_id, new_id)
    for pattern, value in [(r'^\.temp .+$', '.temp '+str(float(temperature))),
                           (r'^Vsh shp 0 dc .+$', 'Vsh shp 0 dc '+format(shunt, '.17g'))]:
        result, count = re.subn(pattern, value, result, flags=re.M)
        assert count == 1
    for letter, code in [('s', soft), ('h', hard)]:
        for bit in range(8):
            result, count = re.subn(r'^V%s%d %s%d 0 dc .+$' % (letter, bit, letter, bit),
                                   'V%s%d %s%d 0 dc %s' % (letter, bit, letter, bit, '1.2' if code & (1 << bit) else '0'), result, flags=re.M)
            assert count == 1
    assert normalized_stimulus(result.replace(new_id, old_id)) == normalized_stimulus(deck)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--soft-code', type=int, required=True)
    parser.add_argument('--hard-code', type=int, required=True)
    parser.add_argument('--shunt-V', type=float, default=.025)
    parser.add_argument('--temperature-C', type=float, default=25)
    args = parser.parse_args()
    original = SIM / 'qualification' / REFERENCE
    result, = json.loads((original / 'summary.json').read_text())
    assert result['controlled_substitution_status'] == 'passed comparison contract'
    assert result['strict_200ns_prefix_parity']['status'].startswith('passed')
    prep = json.loads((original / 'preparation.json').read_text())
    old = (original / 'hard_+0mV.cir').read_text()
    new = transform(old, original.name, args.run_id, args.soft_code, args.hard_code, args.shunt_V, args.temperature_C)
    out = allocate_run(SIM, args.run_id)
    for name in ['sense.spice', 'trip.spice', 'bgr.spice', 'non_bgr_inventory.json']:
        (out / name).write_bytes((original / name).read_bytes())
    (out / 'hard_+0mV.cir').write_text(new)
    prep.update(run=args.run_id, calibration_template_run=original.name, prepared_deck_sha256=sha(out / 'hard_+0mV.cir'),
                fixed_soft_hard_codes=[args.soft_code, args.hard_code], shunt_V=args.shunt_V, temperature_C=args.temperature_C,
                full_nonBGR_baseline_run='joint-bgr586-drawaudit-baseline-room-20260922-a')
    prep['scope'] = 'Seed71002 fixedfullnonBGRrealization, nominal586 reference; only declaredDACcode/shunt/temperature sweep. Same5MHz/full1.02us/late3actual+legacy sampling. No physicaladoption or BGRmismatchpopulation claim.'
    prep['parameter_contract'] = 'All8670nonBGR beforeafter exact vsqualifiedseed71002 room/hotOP, temperature-independentparameters explicitlyqueried atactualleaf temperature; all2842nominalBGR exact,24legacy exact. No omitted/changedqueries.'
    prep['planning'] = {'watchdog_s': 1200, 'maximum_leaf_output_GiB': .05}
    prep['sweep_difference_sha256'] = None
    diff = ''.join(difflib.unified_diff(old.replace(original.name, '@RUN@').splitlines(True),
                   new.replace(args.run_id, '@RUN@').splitlines(True), fromfile='qualifiedFullHot71002', tofile='declaredCalibrationStimulus'))
    (out / 'declared_calibration_difference.diff').write_text(diff)
    prep['sweep_difference_sha256'] = sha(out / 'declared_calibration_difference.diff')
    bindings = {'sha256': {}}
    for source_run, names in [(original, ['summary.json', 'provenance.json', 'preparation.json', 'hard_+0mV.cir', 'sense.spice', 'trip.spice', 'bgr.spice']),
                              (SIM / 'qualification' / prep['full_nonBGR_baseline_run'], ['summary.json', 'provenance.json', 'non_bgr_inventory.json'])]:
        for name in names:
            bindings['sha256'][str((source_run / name).relative_to(ROOT))] = sha(source_run / name)
    bindings['sha256'][prep['candidate_nominal_reference']] = prep['candidate_nominal_reference_sha256']
    for name in ['prepare_bgr_calibration_probe.py', 'run_bgr_calibration_probe.py']:
        bindings['sha256'][str((SIM / name).relative_to(ROOT))] = sha(SIM / name)
    (out / 'prelaunch_reference_bindings.json').write_text(json.dumps(bindings, indent=2)+'\n')
    (out / 'preparation.json').write_text(json.dumps(prep, indent=2)+'\n')
    (out / 'preparer.py').write_text(Path(__file__).read_text())
    print(json.dumps({'prepared_run': args.run_id, 'deck_sha256': prep['prepared_deck_sha256'], 'source_hashes': prep['source_hashes']}))


if __name__ == '__main__':
    main()
