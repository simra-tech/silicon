#!/usr/bin/env python3
"""Prepare exact historical six-condition adverse protocol for nominal final586."""
import argparse
import difflib
import json
from pathlib import Path
import re
from prepare_586_source_controls import HERE, ROOT, BASE, sha, transform
from prepare_586_nominal_intermediates import REFERENCE, ANALYSIS
from result_directory import allocate_run

CORNERS = {'slow': ('wcs', 'ss', 'wcs', 'wcs'), 'fast': ('bcs', 'ff', 'bcs', 'bcs')}
CONDITIONS = [('cal25', 25, 3.3, 1.2, 'calibration'), ('cal100', 100, 3.3, 1.2, 'calibration'),
              ('lowcold', -40, 3.0, 1.08, 'independent'), ('lowhot', 125, 3.0, 1.08, 'independent'),
              ('highcold', -40, 3.6, 1.32, 'independent'), ('highhot', 125, 3.6, 1.32, 'independent')]


def make_deck(corner, temperature, vdda, vdd, groups):
    assert corner in CORNERS and (temperature, vdda, vdd) in [(t, a, d) for label, t, a, d, role in CONDITIONS]
    deck = transform((BASE/'ptat_T12.5.cir').read_text(), temperature, groups)
    hbt, mos, res, cap = CORNERS[corner]
    for old, new, count in [('hbt_typ', 'hbt_'+hbt, 1), ('mos_tt', 'mos_'+mos, 2),
                            ('res_typ', 'res_'+res, 1), ('cap_typ', 'cap_'+cap, 1)]:
        assert deck.count(' '+old+'\n') == count
        deck = deck.replace(' '+old+'\n', ' '+new+'\n')
    for old, new in [('Vdd vdd 0 dc 3.3\n', 'Vdd vdd 0 dc '+str(vdda)+'\n'),
                     ('Vdd12 vdd12 0 dc 1.2\n', 'Vdd12 vdd12 0 dc '+str(vdd)+'\n'),
                     ('Ven en 0 pwl(0 0 1u 0 1.01u 3.3)\n', 'Ven en 0 pwl(0 0 1u 0 1.01u '+str(vdda)+')\n')]:
        assert deck.count(old) == 1
        deck = deck.replace(old, new)
    assert '_mismatch' not in deck and 'setseed' not in deck and '.option seed' not in deck
    return deck


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--campaign-id', required=True)
    args = parser.parse_args()
    assert re.fullmatch('[a-z0-9-]+', args.campaign_id)
    output = HERE/(args.campaign_id+'.json')
    assert not output.exists()
    nominal = json.loads(ANALYSIS.read_text())
    reference, = json.loads((REFERENCE/'summary.json').read_text())
    old = json.loads((REFERENCE/'preparation.json').read_text())
    assert nominal['status'] == reference['control_status'] == reference['full_inventory_status'] == 'passed'
    legacy = (HERE/'run_adverse_calibration.py').read_text()
    assert "[('cal',3.3,1.2,'25,100'),('low',3.0,1.08,'-40,125'),('high',3.6,1.32,'-40,125')]" in legacy
    assert "'slow':('wcs','ss','wcs','wcs'),'fast':('bcs','ff','bcs','bcs')" in legacy
    paths = [ANALYSIS, REFERENCE/'summary.json', REFERENCE/'preparation.json', REFERENCE/'probe.cir',
        BASE/'ptat_T12.5.cir', BASE/'bgr.spice', HERE/'run_adverse_calibration.py', HERE/'run_joint_adverse.py',
        HERE/'prepare_586_source_controls.py', HERE/'run_586_adverse_control.py', Path(__file__).resolve()]+[REFERENCE/n for n in ['bgr.spice', 't2f.spice', '.spiceinit']]
    bindings = {str(p.relative_to(ROOT)): sha(p) for p in paths}
    rows = []
    for corner in CORNERS:
        for label, temperature, vdda, vdd, role in CONDITIONS:
            run_id = args.campaign_id+'-'+corner+'-'+label
            out = allocate_run(HERE.parent, run_id, relative_parent='qualification/runs')
            for name in ['bgr.spice', 't2f.spice', '.spiceinit']:
                (out/name).write_bytes((REFERENCE/name).read_bytes())
            deck = make_deck(corner, temperature, vdda, vdd, old['query_groups'])
            (out/'probe.cir').write_text(deck)
            (out/'declared_fixture_difference.diff').write_text(''.join(difflib.unified_diff(
                (REFERENCE/'probe.cir').read_text().splitlines(True), deck.splitlines(True), fromfile='qualifiedTyp25', tofile=corner+'-'+label)))
            (out/'declared_bgr_source_difference.diff').write_text(''.join(difflib.unified_diff(
                (BASE/'bgr.spice').read_text().splitlines(True), (out/'bgr.spice').read_text().splitlines(True),
                fromfile='historicalOldBGR72417', tofile='finalNominalBGR586')))
            prep = dict(status='not run; exact selected-adverse preparation for review', run_id=run_id, label=label,
                corner=corner, process_sections=dict(zip(['HBT', 'MOS', 'R', 'CAP'], CORNERS[corner])),
                temperature_C=temperature, VDDA_V=vdda, VDD_V=vdd, role=role, mismatch=False,
                groups=old['query_groups'], typ_reference3180=reference['parameters_before'],
                source_hashes=old['source_hashes'], runtime=old['runtime'], live_bindings_sha256=bindings,
                deck_sha256=sha(out/'probe.cir'), nominal_analysis_sha256=sha(ANALYSIS),
                watchdog_s=600, output_wave='ptat_T12.5.dat',
                contract='Exact historicalsix-condition schedule perprocesscorner:25/100 at3.3/1.2 calibrate, fourheldout−40/125 at3.0/1.08 and3.6/1.32; original linear±2C unchanged. Full3180 beforeafterexact withinleaf; allsixsamecorner vectors mustmatch before frozen-coefficientanalysis. Cross-cornerdifferencesreported, not forbidden. Deterministicno-mm source586, not historical519xx/520xx samples or statisticalqualification.32us/50fF/idealIPTAT/timing/solver/cards unchanged exceptdeclaredcorner,rails,enableamplitude,temp. No actualpad/newphysicalCC/adoption.')
            (out/'preparation.json').write_text(json.dumps(prep, indent=2)+'\n')
            rows.append(dict(run_id=run_id, corner=corner, label=label, temperature_C=temperature, VDDA_V=vdda, VDD_V=vdd, role=role,
                             preparation_sha256=sha(out/'preparation.json'), deck_sha256=sha(out/'probe.cir')))
    packet = dict(status='not run;12deterministiccontrols preparedawaitingreview', cases=rows,
                  historical_protocol_sha256=sha(HERE/'run_adverse_calibration.py'),
                  original_calibration='Eachcorner25/100 atnominalrails, freeze forfourindependentlow/highrailendpoints;±2C',
                  mismatch=False, parameters_per_leaf=3180, expected_external_growth_GiB=.36,
                  expected_home_growth_GiB=.05, watchdog_per_leaf_s=600,
                  population_qualification='not run; no statisticalreleaseoroldsourcecohortsubstitution')
    output.write_text(json.dumps(packet, indent=2)+'\n')
    print(json.dumps(dict(packet=str(output.relative_to(ROOT)), sha256=sha(output), cases=rows), indent=2))


if __name__ == '__main__':
    main()
