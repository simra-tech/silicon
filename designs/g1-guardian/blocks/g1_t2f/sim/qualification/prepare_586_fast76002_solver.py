#!/usr/bin/env python3
"""Prepare only one matched2us SPARSE-to-KLU diagnostic; no launch."""
import difflib,json
from pathlib import Path
from prepare_586_fast76002_prefix import HERE,ROOT,ORIGINAL,make_prefix as original_prefix,sha
from result_directory import allocate_run

GEAR=HERE/'runs/t2f586-fast76002-prefix2us-20260923-a'


def make_prefix(original):
    gear=original_prefix(original)
    assert gear.count('method=gear')==1 and 'method=trap' not in gear
    assert gear.count('\n.control\n')==1 and '.options klu' not in gear and '.option sparse' not in gear
    trial=gear.replace('\n.control\n','\n.options klu\n.control\n')
    assert trial.replace('.options klu\n','')==gear
    return trial


def main():
    run_id='t2f586-fast76002-klu2us-20260923-a'
    packet=HERE/(run_id+'.json');assert not packet.exists()
    old,=json.loads((GEAR/'summary.json').read_text())
    assert old['control_status']=='passed waveform-only diagnostic' and old['full3180_status']=='passed'
    prep=json.loads((GEAR/'preparation.json').read_text())
    assert 'Compiled with KLU Direct Linear Solver' in prep['runtime']['ngspice']
    assert 'Using SPARSE 1.3 as Direct Linear Solver' in (GEAR/'run.log').read_text()
    assert '.options klu' not in (GEAR/'.spiceinit').read_text()
    assert (GEAR/'probe.cir').read_text()==original_prefix((ORIGINAL/'probe.cir').read_text())
    out=allocate_run(HERE.parent,run_id,relative_parent='qualification/runs')
    for name in ['bgr.spice','t2f.spice','.spiceinit','population_inventory.json']:
        (out/name).write_bytes((GEAR/name).read_bytes())
    trial=make_prefix((ORIGINAL/'probe.cir').read_text());(out/'probe.cir').write_text(trial)
    (out/'declared_solver_difference.diff').write_text(''.join(difflib.unified_diff((GEAR/'probe.cir').read_text().splitlines(True),
        trial.splitlines(True),fromfile='qualified2usSparseGear76002',tofile='prospective2usKluGear76002')))
    prep.update(run_id=run_id,status='not run; preparation only pending diagnostic launch authority',deck_sha256=sha(out/'probe.cir'),
        gear_prefix_reference=GEAR.name,gear_prefix_decoded_wave_sha256=old['waveform_sha256'],
        scope='ONE matched2us matrix-solver diagnostic, SPARSE1.3->KLU selector only; Gear remainsunchanged. Source/model/seed/full3180/OP/reset/rails/load/tolerances/5ns/2us/13vectors/600sunchanged. Exactwave/grid failures separatelyretained; numericaldifferences are not automaticallysourcefailure or acceptancewaiver. Compare actualfirstFOUTedges, savedaccepted-output trajectory/intervals, allvectorcommon-grid errors andHBTterminalVCE. No32usretry, solveradoption, recalibration orfast30release; originalfull600s andreturn2400sfailures remainfailed.')
    prep['solver_selector_support']=dict(manual_url='https://ngspice.sourceforge.io/docs/ngspice-46-manual.pdf',section='11.1.1 General Options; printedpage316',selector='.options klu',runtime_build=prep['runtime']['ngspice'],baseline_banner='Using SPARSE 1.3 as Direct Linear Solver',required_trial_banner='Using KLU as Direct Linear Solver',scope='Version46 manual and pinnedbinarycompiledKLU support; no performance/parity/adoption inference.')
    for p in [GEAR/'run.log',GEAR/'probe.cir',GEAR/'summary.json',GEAR/'preparation.json',GEAR/'provenance.json',GEAR/'phase0.dat.gz',
              Path(__file__).resolve(),HERE/'run_586_fast76002_solver.py',HERE/'analyze_586_fast76002_solver.py']:
        prep['live_bindings_sha256'][str(p.relative_to(ROOT))]=sha(p)
    (out/'preparation.json').write_text(json.dumps(prep,indent=2)+'\n')
    result=dict(status='not run; prepare-only matched matrix-solver control',run_id=run_id,
        preparation_sha256=sha(out/'preparation.json'),deck_sha256=sha(out/'probe.cir'),
        original_deck_sha256=sha(ORIGINAL/'probe.cir'),gear_prefix_deck_sha256=sha(GEAR/'probe.cir'),
        watchdog_s=600,endpoint_s=2e-6,expected_external_growth_GiB=.05,no_fast30_release=True,
        prospective_comparison='Require exactfull3180/input/runtimebindings andfinite13columns/2us/HBTVCE<=1.6. Report exactdecodedbyte/grid equality separately; comparefirstactual0.6Vrising/fallingedges andcounts, savedtimeintervaldistribution, all13waveforms onunioninterpolatedtimegrid withper-vectorunits/max/RMS. No numericaltolerance canpromoteexactFAIL; no standalone diagnosticconsistencyresultreleasesfullrun/population.')
    packet.write_text(json.dumps(result,indent=2)+'\n');print(packet.relative_to(ROOT),sha(packet))


if __name__=='__main__':main()

