#!/usr/bin/env python3
"""Prepare original-range intermediate temperatures; no simulator launch."""
import argparse
import difflib
import json
from pathlib import Path
import re
from prepare_586_source_controls import HERE, ROOT, BASE, sha, transform
from result_directory import allocate_run

REFERENCE = HERE/'runs/t2f586-source-controls-20260922-a-new-t25'
ANALYSIS = HERE/'t2f586-nominal-calibration-20260922.json'
TEMPERATURES = [('tm20', -20), ('t0', 0), ('t50', 50), ('t75', 75)]


def deck_for(temperature, groups):
    assert temperature in [t for label, t in TEMPERATURES]
    original = (BASE/'ptat_T12.5.cir').read_text()
    deck = transform(original, temperature, groups)
    assert deck.replace('.temp '+str(float(temperature))+'\n', '.temp 25.0\n') == (REFERENCE/'probe.cir').read_text()
    return deck


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--campaign-id', required=True)
    args = parser.parse_args()
    assert re.fullmatch('[a-z0-9-]+', args.campaign_id)
    output = HERE/(args.campaign_id+'.json')
    assert not output.exists()
    analysis = json.loads(ANALYSIS.read_text())
    result, = json.loads((REFERENCE/'summary.json').read_text())
    original = json.loads((REFERENCE/'preparation.json').read_text())
    assert analysis['status'] == result['control_status'] == result['full_inventory_status'] == 'passed'
    paths = [ANALYSIS, REFERENCE/'summary.json', REFERENCE/'preparation.json', REFERENCE/'probe.cir',
             BASE/'ptat_T12.5.cir', HERE/'prepare_586_source_controls.py', Path(__file__).resolve(),
             HERE/'run_586_nominal_intermediate.py']+[REFERENCE/n for n in ['bgr.spice', 't2f.spice', '.spiceinit']]
    bindings = {str(path.relative_to(ROOT)): sha(path) for path in paths}
    rows = []
    for label, temperature in TEMPERATURES:
        run_id = args.campaign_id+'-'+label
        out = allocate_run(HERE.parent, run_id, relative_parent='qualification/runs')
        for name in ['bgr.spice', 't2f.spice', '.spiceinit']:
            (out/name).write_bytes((REFERENCE/name).read_bytes())
        deck = deck_for(temperature, original['query_groups'])
        (out/'probe.cir').write_text(deck)
        (out/'declared_fixture_difference.diff').write_text(''.join(difflib.unified_diff(
            (REFERENCE/'probe.cir').read_text().splitlines(True), deck.splitlines(True), fromfile='qualifiedNominal25', tofile=label)))
        prep = dict(status='not run; preparation only', run_id=run_id, label=label, temperature_C=temperature,
            source_hashes=original['source_hashes'], runtime=original['runtime'], groups=original['query_groups'],
            expected3180=result['parameters_before'], live_bindings_sha256=bindings, deck_sha256=sha(out/'probe.cir'),
            nominal_analysis=str(ANALYSIS.relative_to(ROOT)), nominal_analysis_sha256=sha(ANALYSIS),
            watchdog_s=600, output_wave='ptat_T12.5.dat',
            contract='Only .temp differs from qualified25C full3180 nominaldeck. Frozen25/100 calibration; eachintermediate±2C isheldout, nofit/LUT. Full3180beforeafter exactreference and32us finite13vectors/HBT|VCE|≤1.6V required. Allsource/card/load/timing/solver/measurements unchanged. No mismatchpopulation/PVT/actualpad/newphysicalCC/adoption claim.')
        (out/'preparation.json').write_text(json.dumps(prep, indent=2)+'\n')
        rows.append(dict(run_id=run_id, label=label, temperature_C=temperature, preparation_sha256=sha(out/'preparation.json'), deck_sha256=sha(out/'probe.cir')))
    packet = dict(status='not run; four prepared independentnominal controls awaitingreview', cases=rows,
                  expected_external_growth_GiB=.12, expected_home_growth_GiB=.03, maximum_parallel_processes=1,
                  nominal_analysis_sha256=sha(ANALYSIS), scope='Required final-source original-range nominalintermediate coverage, not population expansion.')
    output.write_text(json.dumps(packet, indent=2)+'\n')
    print(json.dumps(dict(packet=str(output.relative_to(ROOT)), sha256=sha(output), cases=rows), indent=2))


if __name__ == '__main__':
    main()
