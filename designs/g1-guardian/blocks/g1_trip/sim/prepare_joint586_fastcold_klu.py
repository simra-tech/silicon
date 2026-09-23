#!/usr/bin/env python3
"""Prepare one original failed fast lowcold full-fixture KLU diagnostic."""
import difflib,json
from pathlib import Path
from run_joint586_transients import SIM,ROOT,sha
from result_directory import allocate_run
ORIGINAL=SIM/'qualification/joint586-fast-fixture-controls-20260923-b-low_cold_cm0'


def transform(original,run_id):
    old='qualification/'+ORIGINAL.name+'/phase0.dat';new='qualification/'+run_id+'/phase0.dat'
    assert original.count(old)==1 and original.count('\n.control\n')==1 and '.options klu' not in original
    assert original.count('setseed 78001\n')==1 and original.count('tran 0.2n 1.02u')==1
    trial=original.replace(old,new).replace('\n.control\n','\n.options klu\n.control\n')
    assert trial.replace(new,old).replace('.options klu\n','')==original
    return trial


def main():
    run_id='joint586-fast-lowcold-klu-20260923-a';packet=SIM/'qualification'/(run_id+'.json');assert not packet.exists()
    old,=json.loads((ORIGINAL/'summary.json').read_text());assert old['runtime']['status']=='timeout' and old['runtime']['timeout_s']==1200
    prep=json.loads((ORIGINAL/'preparation.json').read_text());assert prep['columns']==19 and prep['condition']==['low_cold_cm0',-40,3.0,1.08,0.0]
    assert len(prep['expected_vector'])==11512
    out=allocate_run(SIM,run_id)
    for n in ['sense.spice','trip.spice','bgr.spice','population_inventory.json']:(out/n).write_bytes((ORIGINAL/n).read_bytes())
    original=(ORIGINAL/'population_transient.cir').read_text();trial=transform(original,run_id)
    (out/'population_transient.cir').write_text(trial)
    (out/'declared_solver_difference.diff').write_text(''.join(difflib.unified_diff(original.splitlines(True),trial.splitlines(True),fromfile='originalFailedFastLowcoldSparse',tofile='separateKluFastLowcold')))
    prep.update(run=run_id,deck_sha256=sha(out/'population_transient.cir'),original_failed_run=ORIGINAL.name,
        original_failure_summary_sha256=sha(ORIGINAL/'summary.json'),
        scope='ONE original failed fast78001 lowrailcold fixture replay: .options klu sole algorithm change, fresh wrdata path only other deck change. Source includes/preamble/seed/OP/reset/19vectors/SHN/rails/clock/codes/measurements/1.02us/1200s unchanged. All11512+27 expected original owncorner realization. OriginalSPARSE1200stimeout remainsFAILED, original fullwave absent so no acrosssolver waveform parity claim. No adoption, alias into sixfixture gate or fast30release; comparisons to five successfulfixtures and exactKLUrepeat remain separate future qualification.')
    for p in [ORIGINAL/n for n in ['summary.json','run.log','run.json','population_transient.cir','preparation.json','sense.spice','trip.spice','bgr.spice','population_inventory.json']]+[SIM/'.spiceinit',Path(__file__).resolve(),SIM/'run_joint586_fastcold_klu.py']:
        prep['live_bindings_sha256'][str(p.relative_to(ROOT))]=sha(p)
    (out/'preparation.json').write_text(json.dumps(prep,indent=2)+'\n')
    packet.write_text(json.dumps(dict(run_id=run_id,preparation_sha256=sha(out/'preparation.json'),deck_sha256=sha(out/'population_transient.cir'),watchdog_s=1200,no_fast30_release=True),indent=2)+'\n')
    print(packet.relative_to(ROOT),sha(packet))


if __name__=='__main__':main()
