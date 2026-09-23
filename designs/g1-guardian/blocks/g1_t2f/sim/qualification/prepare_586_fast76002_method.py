#!/usr/bin/env python3
"""Prepare only one matched2us Gear-to-trapezoidal diagnostic; no launch."""
import difflib,json
from pathlib import Path
from prepare_586_fast76002_prefix import HERE,ROOT,ORIGINAL,make_prefix as original_prefix,sha
from result_directory import allocate_run

GEAR=HERE/'runs/t2f586-fast76002-prefix2us-20260923-a'


def make_prefix(original):
    gear=original_prefix(original)
    assert gear.count('method=gear')==1 and 'method=trap' not in gear
    trial=gear.replace('method=gear','method=trap')
    assert trial.replace('method=trap','method=gear')==gear
    return trial


def main():
    run_id='t2f586-fast76002-trap2us-20260923-a'
    packet=HERE/(run_id+'.json');assert not packet.exists()
    old,=json.loads((GEAR/'summary.json').read_text())
    assert old['control_status']=='passed waveform-only diagnostic' and old['full3180_status']=='passed'
    prep=json.loads((GEAR/'preparation.json').read_text())
    assert (GEAR/'probe.cir').read_text()==original_prefix((ORIGINAL/'probe.cir').read_text())
    out=allocate_run(HERE.parent,run_id,relative_parent='qualification/runs')
    for name in ['bgr.spice','t2f.spice','.spiceinit','population_inventory.json']:
        (out/name).write_bytes((GEAR/name).read_bytes())
    trial=make_prefix((ORIGINAL/'probe.cir').read_text());(out/'probe.cir').write_text(trial)
    (out/'declared_method_difference.diff').write_text(''.join(difflib.unified_diff((GEAR/'probe.cir').read_text().splitlines(True),
        trial.splitlines(True),fromfile='qualified2usGear76002',tofile='prospective2usTrap76002')))
    prep.update(run_id=run_id,status='not run; preparation only pending diagnostic launch authority',deck_sha256=sha(out/'probe.cir'),
        gear_prefix_reference=GEAR.name,gear_prefix_decoded_wave_sha256=old['waveform_sha256'],
        scope='ONE matched2us numerical-method diagnostic, Gear->trapezoidal only. Source/model/seed/full3180/OP/reset/rails/load/tolerances/5ns/2us/13vectors/600sunchanged. Exactwave/grid failures separatelyretained; numericaldifferences are not automaticallysourcefailure or acceptancewaiver. Compare actualfirstFOUTedges, savedaccepted-output trajectory/intervals, allvectorcommon-grid errors andHBTterminalVCE. No32usretry, numericalmethodadoption, recalibration orfast30release; originalfull600s andreturn2400sfailures remainfailed.')
    for p in [GEAR/'probe.cir',GEAR/'summary.json',GEAR/'preparation.json',GEAR/'provenance.json',GEAR/'phase0.dat.gz',
              Path(__file__).resolve(),HERE/'run_586_fast76002_method.py',HERE/'analyze_586_fast76002_method.py']:
        prep['live_bindings_sha256'][str(p.relative_to(ROOT))]=sha(p)
    (out/'preparation.json').write_text(json.dumps(prep,indent=2)+'\n')
    result=dict(status='not run; prepare-only matched numerical-method control',run_id=run_id,
        preparation_sha256=sha(out/'preparation.json'),deck_sha256=sha(out/'probe.cir'),
        original_deck_sha256=sha(ORIGINAL/'probe.cir'),gear_prefix_deck_sha256=sha(GEAR/'probe.cir'),
        watchdog_s=600,endpoint_s=2e-6,expected_external_growth_GiB=.05,no_fast30_release=True,
        prospective_comparison='Require exactfull3180/input/runtimebindings andfinite13columns/2us/HBTVCE<=1.6. Report exactdecodedbyte/grid equality separately; comparefirstactual0.6Vrising/fallingedges andcounts, savedtimeintervaldistribution, all13waveforms onunioninterpolatedtimegrid withper-vectorunits/max/RMS. No numericaltolerance canpromoteexactFAIL; no standalone diagnosticconsistencyresultreleasesfullrun/population.')
    packet.write_text(json.dumps(result,indent=2)+'\n');print(packet.relative_to(ROOT),sha(packet))


if __name__=='__main__':main()
