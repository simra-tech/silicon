"""Prepare one original73001p00 TMAX-only hypothesis; no method adoption."""
import difflib
import json
from pathlib import Path
from prepare_joint586_klu_replay import SIM,ROOT,ORIGINAL,sha
from result_directory import allocate_run

OLD='tran 0.2n 1.02u 0 0.2n\n'
NEW='tran 0.2n 1.02u 0 1n\n'


def transform(original,run_id):
    old='qualification/'+ORIGINAL.parent.name+'/p00/phase0.dat';new='qualification/'+run_id+'/phase0.dat'
    assert original.count(OLD)==1 and original.count(old)==1
    assert original.count('setseed 73001\n')==1 and '.options klu' not in original.lower()
    changed=original.replace(OLD,NEW).replace(old,new)
    assert changed.replace(NEW,OLD).replace(new,old)==original
    return changed


def main():
    run='joint586-s73001p00-tmax1ns-20260923-a';packet=SIM/'qualification'/(run+'.json');assert not packet.exists()
    old=json.loads((ORIGINAL/'summary.json').read_text());parent=json.loads((ORIGINAL.parent/'provenance.json').read_text())
    assert old['status']=='passed' and old['watchdog_status']=='completed' and old['returncode']==0
    assert old['parameter_audit']['parameters_before']==old['parameter_audit']['parameters_after']
    assert len(old['parameter_audit']['parameters_before'])==11512 and len(old['parameter_audit']['legacy27'])==27
    ref=SIM/'qualification'/parent['qualified_transient_run'];prep=json.loads((ref/'preparation.json').read_text())
    assert sha(ref/'preparation.json')==parent['qualified_preparation_sha256']
    original=(ORIGINAL/'probe.cir').read_text();trial=transform(original,run);out=allocate_run(SIM,run)
    (out/'probe.cir').write_text(trial)
    (out/'declared_tmax_difference.diff').write_text(''.join(difflib.unified_diff(original.splitlines(True),trial.splitlines(True),fromfile='original73001p00',tofile='TMAX1ns-only')))
    for name in ['sense.spice','trip.spice','bgr.spice','population_inventory.json']:(out/name).write_bytes((ORIGINAL.parent/name).read_bytes())
    files=[ORIGINAL/n for n in ['probe.cir','run.log','run.json','summary.json','phase0.dat.gz','phase0.dat.archive.json']]
    files += [ORIGINAL.parent/n for n in ['provenance.json','sense.spice','trip.spice','bgr.spice','population_inventory.json']]
    files += [ref/'preparation.json']+[SIM/n for n in ['prepare_joint586_tmax_probe.py','compare_joint586_tmax_probe.py','run_joint586_tmax_probe.py',
        'test_joint586_tmax_probe.py','prepare_joint586_klu_replay.py','run_joint586_transients.py','run_nominal_clock_probe.py',
        'analyze_bgr_substitution_outcomes.py','run_bgr_substitution_draw_audit.py','wave_archive.py','result_directory.py','.spiceinit']]
    result=dict(status='prepared only; no execution lease or adoption',run_id=run,original_run=str(ORIGINAL.relative_to(SIM)),
        deck_sha256=sha(out/'probe.cir'),original_deck_sha256=sha(ORIGINAL/'probe.cir'),source_hashes=parent['source_hashes'],
        inventory_sha256=parent['inventory_sha256'],groups=prep['groups'],expected_runtime_identity=parent['runtime_identity'],
        expected_parameters=old['parameter_audit']['parameters_before'],expected_legacy27=old['parameter_audit']['legacy27'],
        prospective_sampling=prep['prospective_sampling'],original_decisions=old['decisions'],watchdog_s=1200,
        bounds=dict(clock_output_event_shift_s=2e-10,event_bracket_width_s=2e-10,quiet_decision_analog_abs_V=1e-4,
            wholewave_analog_abs_V=1e-3,wholewave_other_abs_V=.05),
        rationale='Prospective single-leaf consistency screen, not population acceptance. Event0.2ns equals original maximum grid interval and1%of20ns decision delay; actual crossing brackets must remain<=0.2ns. Analog100uV at quiet/decision and1mV wholewave; othernodes50mV wholewave are explicitly engineering screens, not universal integration-error bounds. No input-accuracy bound inferred from nominalgain. All original late3/legacy decisions and their agreement remain mandatory. Strong-HIGH code0/0 pilot cannot qualify near-boundary decisions.',
        comparison='Exact bytes/numeric grid retained independently; union-grid piecewise-linear absolute errors, paired actual-edge phase observations at-10,+20,+50ns, output0.6V rise/fall events and brackets, saved-grid ceiling fractions. No rejected-step inference or linear-interpolation accuracy guarantee.',
        scope='Only fourth TRAN argument0.2ns→1ns and fresh output destination differ. Requested output interval0.2ns,1.02us endpoint,5MHz,seed73001,codes0/0,25mV,25C,SPARSE,Gear,tolerances,models,all11512+27 and18vectors unchanged. Currentbaab source only; no candidateSENSE or population transfer.',
        live_bindings_sha256={str(path.relative_to(ROOT)):sha(path) for path in files})
    (out/'preparation.json').write_text(json.dumps(result,indent=2)+'\n')
    packet.write_text(json.dumps(dict(run_id=run,preparation_sha256=sha(out/'preparation.json'),deck_sha256=sha(out/'probe.cir'),watchdog_s=1200,expected_external_growth_GiB=.05),indent=2)+'\n');print(sha(packet))


if __name__=='__main__':main()
