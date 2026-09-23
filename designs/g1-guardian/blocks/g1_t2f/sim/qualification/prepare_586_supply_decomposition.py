#!/usr/bin/env python3
"""Four no-mismatch nominal-rail endpoint controls; no calibration refit."""
import argparse
import difflib
import json
from pathlib import Path
from prepare_586_adverse_controls import HERE, ROOT, CORNERS, make_deck as adverse_deck, sha
from result_directory import allocate_run


def make_deck(corner, temperature, vdda, vdd, groups):
    assert corner in CORNERS and temperature in [-40, 125] and (vdda, vdd) == (3.3, 1.2)
    deck = adverse_deck(corner, temperature, 3.0, 1.08, groups)
    for old, new in [('Vdd vdd 0 dc 3.0\n', 'Vdd vdd 0 dc 3.3\n'),
                     ('Vdd12 vdd12 0 dc 1.08\n', 'Vdd12 vdd12 0 dc 1.2\n'),
                     ('Ven en 0 pwl(0 0 1u 0 1.01u 3.0)\n', 'Ven en 0 pwl(0 0 1u 0 1.01u 3.3)\n')]:
        assert deck.count(old) == 1
        deck = deck.replace(old, new)
    return deck


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--campaign-id', required=True)
    args = parser.parse_args()
    import re
    assert re.fullmatch('[a-z0-9-]+', args.campaign_id)
    packet = HERE/(args.campaign_id+'.json')
    assert not packet.exists()
    cases = []
    for corner in CORNERS:
        for label, temperature, original_label in [('nomcold', -40, 'lowcold'), ('nomhot', 125, 'lowhot')]:
            original = HERE/'runs'/('t2f586-adverse-controls-20260922-a-'+corner+'-'+original_label)
            reference, = json.loads((original/'summary.json').read_text())
            assert reference['control_status'] == reference['full3180_status'] == 'passed'
            prep = json.loads((original/'preparation.json').read_text())
            run_id = args.campaign_id+'-'+corner+'-'+label
            out = allocate_run(HERE.parent, run_id, relative_parent='qualification/runs')
            for name in ['bgr.spice', 't2f.spice', '.spiceinit', 'declared_bgr_source_difference.diff']:
                (out/name).write_bytes((original/name).read_bytes())
                assert sha(out/name) == sha(original/name)
            deck = make_deck(corner, temperature, 3.3, 1.2, prep['groups'])
            (out/'probe.cir').write_text(deck)
            (out/'declared_fixture_difference.diff').write_text(''.join(difflib.unified_diff(
                (original/'probe.cir').read_text().splitlines(True), deck.splitlines(True),
                fromfile=corner+'/'+original_label, tofile=corner+'/'+label)))
            prep.update(run_id=run_id, label=label, VDDA_V=3.3, VDD_V=1.2, role='independent supply decomposition',
                status='not run; four nominal-rail endpoints prepared for review', deck_sha256=sha(out/'probe.cir'),
                samecorner_reference3180=reference['parameters_before'],
                contract='No-mm final586 nominal-rail endpoint at fixed process and temperature; only VDDA/VDD12/enable amplitude differ from original lowrail endpoint. Full3180 must match completed samecorner reference before/after. Original32us/13vectors/HBTVCE1.6V/600s preserved. Evaluate originalsamecorner25/100fixedlinear: totaladverseerror=nominalrailresidual+supplyinduceddelta. No refit/thresholdchange/architectureattribution/adoption.')
            for p in [original/'summary.json', original/'probe.cir', original/'preparation.json',
                      HERE/'run_586_supply_decomposition.py', Path(__file__).resolve()]:
                prep['live_bindings_sha256'][str(p.relative_to(ROOT))] = sha(p)
            (out/'preparation.json').write_text(json.dumps(prep, indent=2)+'\n')
            cases.append(dict(run_id=run_id, corner=corner, label=label, temperature_C=temperature, VDDA_V=3.3, VDD_V=1.2,
                preparation_sha256=sha(out/'preparation.json'), deck_sha256=sha(out/'probe.cir')))
    payload = dict(status='not run; four controls prepared for review', cases=cases, watchdog_per_leaf_s=600,
        expected_external_growth_GiB=.12, expected_home_growth_GiB=.03, source_or_acceptance_change=False)
    packet.write_text(json.dumps(payload, indent=2)+'\n')
    print(json.dumps(dict(packet=str(packet.relative_to(ROOT)), sha256=sha(packet), cases=cases), indent=2))


if __name__ == '__main__':
    main()
