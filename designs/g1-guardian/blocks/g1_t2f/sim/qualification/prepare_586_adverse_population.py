#!/usr/bin/env python3
"""Prepare separate six-control final586 populations at each required corner."""
import argparse
import difflib
import json
from pathlib import Path
from prepare_586_population import HERE, ROOT, BASE, CASES, make_deck as typ_deck, sha
from prepare_586_adverse_controls import CORNERS
from result_directory import allocate_run

TYP_PACKET = HERE/'t2f586-population-controls-20260922-a.json'
SEEDS = {'slow': (75001, 75002), 'fast': (76001, 76002)}


def make_deck(original, corner, seed, temperatures, groups):
    assert corner in SEEDS and seed in SEEDS[corner]
    old_seed = 74001+SEEDS[corner].index(seed)
    deck = typ_deck(original, old_seed, temperatures, groups)
    assert deck.count('setseed %d\n' % old_seed) == 1
    deck = deck.replace('setseed %d\n' % old_seed, 'setseed %d\n' % seed)
    hbt, mos, res, cap = CORNERS[corner]
    for old, new, count in [('hbt_typ', 'hbt_'+hbt, 1), ('mos_tt', 'mos_'+mos, 2),
                            ('res_typ', 'res_'+res, 1), ('cap_typ', 'cap_'+cap, 1)]:
        assert deck.count(' '+old+'_mismatch\n') == count
        deck = deck.replace(' '+old+'_mismatch\n', ' '+new+'_mismatch\n')
    return deck


def prepare(corner, campaign_id):
    import re
    assert re.fullmatch('[a-z0-9-]+', campaign_id)
    packet_path = HERE/(campaign_id+'.json')
    assert not packet_path.exists()
    typ = json.loads(TYP_PACKET.read_text())
    audit_path = HERE/'t2f586-population-qualification-20260922.json'
    audit = json.loads(audit_path.read_text())
    assert audit['status'] == 'passed six-control qualification' and audit['packet_sha256'] == sha(TYP_PACKET)
    nominal = HERE/'runs'/('t2f586-adverse-controls-20260922-a-'+corner+'-cal25')
    nominal_row, = json.loads((nominal/'summary.json').read_text())
    assert nominal_row['control_status'] == nominal_row['full3180_status'] == 'passed'
    original = (BASE/'ptat_T12.5.cir').read_text()
    rows = []
    for label, old_seed, enabled, temperatures in CASES:
        seed = SEEDS[corner][old_seed-74001]
        old_case, = [r for r in typ['cases'] if r['label'] == label]
        old = HERE/'runs'/old_case['run_id']
        prep = json.loads((old/'preparation.json').read_text())
        assert sha(old/'preparation.json') == old_case['preparation_sha256']
        run_id = campaign_id+'-'+label
        out = allocate_run(HERE.parent, run_id, relative_parent='qualification/runs')
        for name in ['bgr.spice', 't2f.spice', '.spiceinit', 'population_inventory.json', 'declared_population_source_difference.json']:
            (out/name).write_bytes((old/name).read_bytes())
            assert sha(out/name) == sha(old/name)
        deck = make_deck(original, corner, seed, temperatures, prep['groups'])
        (out/'probe.cir').write_text(deck)
        (out/'declared_corner_deck_difference.diff').write_text(''.join(difflib.unified_diff(
            (old/'probe.cir').read_text().splitlines(True), deck.splitlines(True),
            fromfile='qualifiedTypicalPopulation/'+label, tofile=corner+'/'+label)))
        prep.update(run_id=run_id, seed=seed, corner=corner, status='not run; corner-specific qualification prepared for review',
            nominal_reference=str(nominal.relative_to(ROOT)), nominal_parameters=nominal_row['parameters_before'],
            deck_sha256=sha(out/'probe.cir'),
            scope='Separate final586 '+corner+' full1129-primitive population qualification. Only five pinned library sections and seed differ from qualified typical population; devices, cards, timing, rails, load and tolerances unchanged. Original same-corner25/100 nominal-rail calibration and four independent rail/temperature endpoints retain linear +/-2C. Deterministic slow failure remains a failure; no correction curve, filtering, source adoption or physical PEX claim.',
            planning=dict(simulation_status='not run; six corner controls required', expected_external_growth_GiB=.20 if label=='return' else .05))
        for p in [TYP_PACKET, audit_path, nominal/'summary.json', nominal/'probe.cir', nominal/'preparation.json',
                  HERE/'prepare_586_population.py', HERE/'run_586_adverse_population_control.py', Path(__file__).resolve()]:
            prep['live_bindings_sha256'][str(p.relative_to(ROOT))] = sha(p)
        (out/'preparation.json').write_text(json.dumps(prep, indent=2)+'\n')
        rows.append(dict(label=label, seed=seed, run_id=run_id, temperatures_C=temperatures,
            preparation_sha256=sha(out/'preparation.json'), deck_sha256=sha(out/'probe.cir'),
            source_hashes=prep['source_hashes'], watchdog_s=prep['watchdog_s']))
    payload = dict(status='not run; six corner qualification controls prepared for review', corner=corner, cases=rows,
        parameter_count=3180, primitive_count=1129, new_seed_ids=SEEDS[corner],
        inventory_sha256=typ['inventory_sha256'], nominal_packet_sha256=typ['nominal_packet_sha256'],
        no_ensemble_release=True, prospective_ensemble_seeds=list(range(75101 if corner=='slow' else 75201, 75131 if corner=='slow' else 75231)),
        expected_external_growth_GiB=.45, watchdog_per_phase_s=600,
        ensemble_contract='Thirty independent samples per corner, six conditions each: nominal rails25/100C fixed linear calibration; -40/125C at3.0/1.08 and3.6/1.32V heldout +/-2C. Full3180 before/after and across conditions. No survivor-only denominator, seed replacement, silent retries, LUT or reciprocal adoption. First sample exact provenance audit before further scale. Qualification failures stop dependent scaling, not independent campaigns.')
    packet_path.write_text(json.dumps(payload, indent=2)+'\n')
    print(json.dumps(dict(packet=str(packet_path.relative_to(ROOT)), sha256=sha(packet_path), cases=rows), indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--corner', choices=sorted(CORNERS), required=True)
    parser.add_argument('--campaign-id', required=True)
    args = parser.parse_args()
    prepare(args.corner, args.campaign_id)
