#!/usr/bin/env python3
"""Read-only failed leaf inventory; no recovery or missing-output inference."""
import argparse
import json
from pathlib import Path
import re
from run_joint586_calibration import SIM,REFERENCE,sha,calibration_deck
from run_bgr_substitution_draw_audit import read_group


def failed_inventory(run,entry,prep,expected):
    leaf=run/entry['run'].split('/')[-1]
    runtime=json.loads((leaf/'run.json').read_text())
    assert entry['status']=='failed' and runtime['status']=='timeout' and runtime['timeout_s']==1200
    assert not entry['errors']
    log=(leaf/'run.log').read_text()
    result=dict(run=entry['run'],status='failed original1200s watchdog; unchanged',runtime=runtime,
        receipts_sha256={n:sha(leaf/n) for n in ['probe.cir','run.log','run.json','summary.json']},
        parameters_before_status='not run to completion',parameters_after_status='not run to completion',
        legacy27_status='not run to completion',waveform_status='not run; no exported waveform',
        errors=entry['errors'])
    vectors={}
    for when in ['BEFORE','AFTER']:
        if all(tag+'_'+when+'_END' in log for tag in ['NON_BGR','BGR']):
            vector=[]
            for tag in ['NON_BGR','BGR']:
                vector+=read_group(log,tag+'_'+when,prep['groups'][tag])
            assert len(vector)==11512
            if expected is not None:assert vector==expected
            vectors[when]=vector
            result['parameters_'+when.lower()+'_status']='passed all11512; exact established sample vector' if expected is not None else 'passed all11512; no prior completed anchor'
            result['parameters_'+when.lower()]=vector
    if len(vectors)==2:assert vectors['BEFORE']==vectors['AFTER']
    if 'Initial Transient Solution' in log:
        init,positive=log.split('Initial Transient Solution',1)
        result['warnings_before_initial_transient']=len(re.findall('warning',init,re.I))
        result['warnings_after_initial_transient']=len(re.findall('warning',positive,re.I))
    assert not (leaf/'phase0.dat').exists() and not (leaf/'phase0.dat.gz').exists()
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--seed',type=int,required=True)
    p.add_argument('--probe',type=int,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    assert not a.output.exists()
    run=SIM/'qualification'/('joint586-calibration-s%d-20260922-a'%a.seed)
    parent,=json.loads((run/'summary.json').read_text())
    ref=SIM/'qualification'/REFERENCE
    prep=json.loads((ref/'preparation.json').read_text())
    entry=parent['probes'][a.probe]
    leaf=run/('p%02d'%a.probe)
    deck=calibration_deck((ref/'population_transient.cir').read_text(),ref.name,run.name,a.seed,entry['codes'],entry['shunt_V'],entry['temperature_C'])
    deck=deck.replace('qualification/'+run.name+'/phase0.dat','qualification/'+run.name+'/'+leaf.name+'/phase0.dat')
    assert deck==(leaf/'probe.cir').read_text() and sha(leaf/'probe.cir')==entry['deck_sha256']
    assert all(sha(run/name)==digest for name,digest in prep['source_hashes'].items())
    result=failed_inventory(run,entry,prep,parent['parameters_before_first_probe'])
    result.update(status='passed read-only exact-input and available inventory audit; original numerical failure retained',
        parent_status=parent['status'],parent_summary_sha256=sha(run/'summary.json'),analyzer_sha256=sha(Path(__file__)),
        interpretation='Reported simulation progress is host telemetry, not a saved waveform. Initialization warnings are separate from positive-time warnings. No deterministic deck/parameter/source discrepancy found by this audit; absence does not establish numerical root cause, model validity, physical qualification or authorize a retry.')
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['parameters_before','parameters_after']},indent=2))


if __name__=='__main__':main()
