#!/usr/bin/env python3
"""Read-only available evidence for an original adverse600s leaf failure."""
import argparse
import json
from pathlib import Path
import re
from run_586_adverse_calibration_sample import HERE, ROOT, sha, reference_run, sample_deck, qualification_gate
from run_bgr_substitution_draw_audit import read_group


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run-id',required=True)
    p.add_argument('--leaf',type=int,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert not a.output.exists() and '/' not in a.run_id
    parent=HERE/'runs'/a.run_id;leaf=parent/('p%02d'%a.leaf)
    row,=json.loads((leaf/'summary.json').read_text());prov=json.loads((parent/'provenance.json').read_text())
    corner=prov['corner'];ref=reference_run(corner);prep=json.loads((ref/'preparation.json').read_text())
    assert row['status']=='failed' and row['runtime']['status']=='timeout' and row['runtime']['timeout_s']==600 and not row['errors']
    assert prov['runtime_identity']==prep['runtime']
    assert all(sha(parent/n)==sha(leaf/n)==v for n,v in prep['source_hashes'].items())
    assert sha(parent/'population_inventory.json')==prep['inventory_sha256']==prov['inventory_sha256']
    assert sha(parent/'runner.py')==prov['runner_sha256']
    assert sha(ref/'preparation.json')==prov['reference_preparation_sha256'] and sha(ref/'probe.cir')==prov['reference_deck_sha256']
    assert sha(leaf/'probe.cir')==row['deck_sha256']
    assert (leaf/'probe.cir').read_text()==sample_deck((ref/'probe.cir').read_text(),corner,prov['seed'],row['label'])
    first,=json.loads((parent/'p00/summary.json').read_text());assert first['status']=='passed'
    log=(leaf/'run.log').read_text()
    before={tag:read_group(log,'P0_'+tag+'_BEFORE',keys) for tag,keys in prep['groups'].items()}
    assert sum(map(len,before.values()))==3180 and before==first['parameters_before']==first['parameters_after']
    after_complete=all('P0_'+tag+'_AFTER_END' in log for tag in prep['groups'])
    assert not after_complete and not (leaf/'phase0.dat').exists() and not (leaf/'phase0.dat.gz').exists()
    initial,positive=log.split('Initial Transient Solution',1)
    progress=[json.loads(s) for s in (leaf/'run.progress.jsonl').read_text().splitlines()]
    milestones=[]
    for t in [0,1e-6,1.01e-6,1.5e-6,2e-6,3e-6,4e-6,4.5e-6,4.64e-6,5e-6,32e-6]:
        reached=[r for r in progress if r.get('last_reported_sim_time_s',-1)>=t]
        r=reached[0] if reached else None
        milestones.append(dict(target_simulation_s=t,status='reported reached' if r else 'not reached',
            first_reported_wall_s=r['wall_s'] if r else None,
            first_reported_simulation_s=r.get('last_reported_sim_time_s') if r else None))
    result=dict(status='passed read-only frozen-input/available-BEFORE audit; original numerical failure retained',
        run=a.run_id,leaf=leaf.name,corner=corner,seed=prov['seed'],condition=row['label'],runtime=row['runtime'],
        full3180_before_status='passed exact completed cal25 same draw',full3180_before=before,
        full3180_after_status='not run to completion',waveform_status='not run; no exported waveform',
        frequency_and_calibration_status='not run to completion; frozen25/100 fit unavailable',
        warnings_before_initial_transient=len(re.findall('warning',initial,re.I)),
        warnings_after_initial_transient=len(re.findall('warning',positive,re.I)),errors=row['errors'],
        host_reported_progress=milestones,analyzer_sha256=sha(Path(__file__)),
        receipts_sha256={n:sha(leaf/n) for n in ['summary.json','probe.cir','run.json','run.log','run.progress.jsonl']},
        parent_provenance_sha256=sha(parent/'provenance.json'),cal25_summary_sha256=sha(parent/'p00/summary.json'),
        interpretation='Positive-time progress is host telemetry, not saved accepted-step or terminal wave evidence. OP/init warnings separated. Exact source/deck/fullBEFORE audit finds no input discrepancy; this does not identify the numerical cause. Original600s failure and fixed30 denominator retained; no retry, replacement, calibration refit, tolerance change or adverse expansion authorized.')
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['full3180_before','receipts_sha256']},indent=2))


if __name__=='__main__':main()
