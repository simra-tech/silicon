#!/usr/bin/env python3
"""One full completed JOINT73001p00 matrix-solver replay; no adoption."""
import difflib,json
from pathlib import Path
from run_joint586_transients import SIM,ROOT,sha
from result_directory import allocate_run

ORIGINAL=SIM/'qualification/joint586-calibration-s73001-20260922-a/p00'


def transform(original,run_id):
    old='qualification/'+ORIGINAL.parent.name+'/p00/phase0.dat'
    new='qualification/'+run_id+'/phase0.dat'
    assert original.count(old)==1 and original.count('\n.control\n')==1
    assert original.count('setseed 73001\n')==1 and '.options klu' not in original
    trial=original.replace(old,new).replace('\n.control\n','\n.options klu\n.control\n')
    assert trial.replace(new,old).replace('.options klu\n','')==original
    return trial


def main():
    run_id='joint586-s73001p00-klu-20260923-a';packet=SIM/'qualification'/(run_id+'.json')
    assert not packet.exists()
    old=json.loads((ORIGINAL/'summary.json').read_text());parent=json.loads((ORIGINAL.parent/'provenance.json').read_text())
    assert old['status']=='passed' and old['watchdog_status']=='completed' and old['returncode']==0
    assert old['parameter_audit']['parameters_before']==old['parameter_audit']['parameters_after']
    assert len(old['parameter_audit']['parameters_before'])==11512 and len(old['parameter_audit']['legacy27'])==27
    assert 'Using SPARSE 1.3 as Direct Linear Solver' in (ORIGINAL/'run.log').read_text()
    ref=SIM/'qualification'/parent['qualified_transient_run'];prep=json.loads((ref/'preparation.json').read_text())
    assert sha(ref/'preparation.json')==parent['qualified_preparation_sha256']
    out=allocate_run(SIM,run_id)
    original=(ORIGINAL/'probe.cir').read_text();trial=transform(original,run_id)
    (out/'probe.cir').write_text(trial)
    (out/'declared_solver_difference.diff').write_text(''.join(difflib.unified_diff(original.splitlines(True),trial.splitlines(True),fromfile='completed73001p00Sparse',tofile='separate73001p00Klu')))
    for name in ['sense.spice','trip.spice','bgr.spice','population_inventory.json']:
        (out/name).write_bytes((ORIGINAL.parent/name).read_bytes())
    result=dict(run_id=run_id,status='prepared only; not run',original_run=str(ORIGINAL.relative_to(SIM)),
        original_deck_sha256=sha(ORIGINAL/'probe.cir'),deck_sha256=sha(out/'probe.cir'),
        source_hashes=parent['source_hashes'],inventory_sha256=parent['inventory_sha256'],groups=prep['groups'],
        expected_runtime_identity=parent['runtime_identity'],expected_parameters=old['parameter_audit']['parameters_before'],
        expected_legacy27=old['parameter_audit']['legacy27'],prospective_sampling=prep['prospective_sampling'],
        original_decisions=old['decisions'],physical_scope=parent['physical_scope'],watchdog_s=1200,
        scope='One completed full73001p00 replay; sole algorithm change .options klu, output wave path changed to fresh run. Includes still bind original immutable sources, copied sources exact. Full original5MHz/1.02us/seed73001/code0,0/shunt25mV/25C/options/cards/11512+27 retained. Exact waveform/grid equality remains separate; actual/legacy decisions, all18 vectors and clock events compared. No adoption, population change, physical qualification or replacement of original evidence.',
        live_bindings_sha256={})
    files=[ORIGINAL/n for n in ['probe.cir','run.log','run.json','summary.json','phase0.dat.gz']]
    files += [ORIGINAL.parent/n for n in ['provenance.json','sense.spice','trip.spice','bgr.spice','population_inventory.json']]
    files += [ref/'preparation.json',Path(__file__).resolve(),SIM/'run_joint586_klu_replay.py',SIM/'run_joint586_transients.py',SIM/'run_nominal_clock_probe.py',SIM/'compare_hot_residual_probes.py',SIM/'run_bgr_substitution_draw_audit.py',SIM/'.spiceinit']
    result['live_bindings_sha256']={str(p.relative_to(ROOT)):sha(p) for p in files}
    (out/'preparation.json').write_text(json.dumps(result,indent=2)+'\n')
    packet.write_text(json.dumps(dict(run_id=run_id,preparation_sha256=sha(out/'preparation.json'),deck_sha256=sha(out/'probe.cir'),watchdog_s=1200,expected_external_growth_GiB=.05),indent=2)+'\n')
    print(packet.relative_to(ROOT),sha(packet))


if __name__=='__main__':main()
