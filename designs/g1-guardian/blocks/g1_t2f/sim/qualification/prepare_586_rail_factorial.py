#!/usr/bin/env python3
"""Prepare four cold rail-factorial controls, without simulation release."""
import argparse
import difflib
import json
from pathlib import Path
import re
from prepare_586_supply_decomposition import HERE, ROOT, sha
from result_directory import allocate_run

CONDITIONS = {'analoghigh': (3.6, 1.2), 'digitalhigh': (3.3, 1.32)}


def make_deck(original, label):
    assert label in CONDITIONS and original.count('.temp -40.0\n') == 1
    assert 'setseed' not in original and '_mismatch' not in original
    assert original.count('tran 5n 32u\n') == 1
    vdda, vdd = CONDITIONS[label]
    pairs = [('Vdd vdd 0 dc 3.3\n', 'Vdd vdd 0 dc '+str(vdda)+'\n'),
             ('Vdd12 vdd12 0 dc 1.2\n', 'Vdd12 vdd12 0 dc '+str(vdd)+'\n'),
             ('Ven en 0 pwl(0 0 1u 0 1.01u 3.3)\n', 'Ven en 0 pwl(0 0 1u 0 1.01u '+str(vdda)+')\n')]
    deck = original
    for old, new in pairs:
        assert deck.count(old) == 1
        deck = deck.replace(old, new)
    restored = deck
    for old, new in pairs:
        assert restored.count(new) == 1
        restored = restored.replace(new, old)
    assert restored == original
    assert deck.split('.control\n')[1] == original.split('.control\n')[1]
    return deck


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--campaign-id', required=True)
    args = parser.parse_args()
    assert re.fullmatch('[a-z0-9-]+', args.campaign_id)
    packet = HERE/(args.campaign_id+'.json')
    assert not packet.exists()
    analysis = HERE/'t2f586-supply-decomposition-analysis-20260923.json'
    assert json.loads(analysis.read_text())['status'] == 'passed conditional algebraic diagnostic; electrical failures retained'
    cases = []
    for corner in ['slow', 'fast']:
        original = HERE/'runs'/('t2f586-supply-decomposition-20260923-a-'+corner+'-nomcold')
        reference, = json.loads((original/'summary.json').read_text())
        assert reference['control_status'] == reference['full3180_status'] == 'passed'
        assert reference['parameters_before'] == reference['parameters_after']
        for label, (vdda, vdd) in CONDITIONS.items():
            prep = json.loads((original/'preparation.json').read_text())
            run_id = args.campaign_id+'-'+corner+'-'+label
            out = allocate_run(HERE.parent, run_id, relative_parent='qualification/runs')
            for name in ['bgr.spice', 't2f.spice', '.spiceinit', 'declared_bgr_source_difference.diff']:
                (out/name).write_bytes((original/name).read_bytes())
                assert sha(out/name) == sha(original/name)
            old_deck = (original/'probe.cir').read_text()
            deck = make_deck(old_deck, label)
            (out/'probe.cir').write_text(deck)
            (out/'declared_fixture_difference.diff').write_text(''.join(difflib.unified_diff(
                old_deck.splitlines(True), deck.splitlines(True), fromfile=corner+'NominalCold', tofile=corner+label)))
            prep.update(run_id=run_id, label=label, VDDA_V=vdda, VDD_V=vdd, enable_high_V=vdda,
                role='conditional cold rail factorial; not calibration', status='not run; prepared for review',
                deck_sha256=sha(out/'probe.cir'), factorial_reference=str(original.relative_to(ROOT)),
                samecorner_reference3180=reference['parameters_before'],
                contract='Four no-mismatch cold controls: each slow/fast corner independently raises VDDA+HV enable together to3.6V or VDD12 alone to1.32V. Original source/cards/temp/reset/OP/options/32us/13vectors/50fF/IPTAT load/full3180/600s unchanged. Existing nominal/all-high supply results provide other factorial vertices. Original25/100 calibration remains frozen; interaction reported, never assumedzero. No causal attribution within combined VDDA+enable, no source remedy/adoption/accuracy waiver/new statisticalpopulation.')
            for path in [analysis, original/'summary.json', original/'preparation.json', original/'probe.cir',
                         HERE/'run_586_rail_factorial.py', HERE/'test_586_rail_factorial.py', Path(__file__).resolve()]:
                prep['live_bindings_sha256'][str(path.relative_to(ROOT))] = sha(path)
            (out/'preparation.json').write_text(json.dumps(prep, indent=2)+'\n')
            cases.append(dict(run_id=run_id, corner=corner, label=label, temperature_C=-40,
                VDDA_V=vdda, VDD_V=vdd, enable_high_V=vdda,
                preparation_sha256=sha(out/'preparation.json'), deck_sha256=sha(out/'probe.cir')))
    packet.write_text(json.dumps(dict(status='not run; review required before launch', cases=cases,
        watchdog_per_leaf_s=600, expected_external_growth_GiB=.12, expected_home_growth_GiB=.03,
        source_card_calibration_acceptance_change=False,
        scope='Two-axis cold factorial, analog rail and HV enable deliberately grouped; no single-rail isolation claim for their separate effects.'), indent=2)+'\n')
    print(json.dumps(dict(packet=str(packet.relative_to(ROOT)), sha256=sha(packet), cases=cases), indent=2))


if __name__ == '__main__':
    main()
