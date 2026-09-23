#!/usr/bin/env python3
"""Read-only terminal failed fixture input/available-inventory and progress audit."""
import argparse,json,re
from pathlib import Path
from prepare_joint586_adverse_fixture_controls import SIM,ROOT,REFERENCE,fixture,sha
from run_bgr_substitution_draw_audit import read_group


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run-id',required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert '/' not in a.run_id and not a.output.exists()
    out=SIM/'qualification'/a.run_id;prep=json.loads((out/'preparation.json').read_text())
    prov=json.loads((out/'provenance.json').read_text());row,=json.loads((out/'summary.json').read_text())
    state=json.loads((out/'run.json').read_text());assert state==row['runtime'] and state['status']!='running'
    assert row['status']!='passed required fixture control'
    original=(SIM/'qualification'/REFERENCE/'population_transient.cir').read_text()
    assert (out/'population_transient.cir').read_text()==fixture(original,a.run_id,prep['corner'],prep['seed'],prep['condition'])
    assert sha(out/'preparation.json')==prov['preparation_sha256'] and sha(out/'population_transient.cir')==prep['deck_sha256']
    assert prov['runtime_identity']==prep['expected_runtime_identity'] and all(prov['input_checks'].values())
    assert all(sha(ROOT/n)==v for n,v in prep['live_bindings_sha256'].items())
    assert all(sha(out/n)==v for n,v in prep['source_hashes'].items())
    assert sha(out/'population_inventory.json')==prep['inventory_sha256']
    log=(out/'run.log').read_text()
    before=read_group(log,'NON_BGR_BEFORE',prep['groups']['NON_BGR'])+read_group(log,'BGR_BEFORE',prep['groups']['BGR'])
    assert len(before)==11512 and before==prep['expected_vector']
    has_after=all(tag+'_AFTER_END' in log for tag in ['NON_BGR','BGR'])
    parts=log.split('Initial Transient Solution',1)
    progress=[json.loads(line) for line in (out/'run.progress.jsonl').read_text().splitlines()]
    milestones=[]
    for t in [0,20e-9,20.2e-9,100e-9,120e-9,120.2e-9,120.7e-9,121e-9,200e-9,1.02e-6]:
        reached=[r for r in progress if r.get('last_reported_sim_time_s',-1)>=t]
        first=reached[0] if reached else None
        milestones.append(dict(target_s=t,status='host reported reached' if first else 'not reached',
            first_wall_s=first['wall_s'] if first else None,first_reported_s=first.get('last_reported_sim_time_s') if first else None))
    report=dict(status='passed read-only source/fullBEFORE audit; original fixture failure retained',
        run=a.run_id,condition=prep['condition'],seed=prep['seed'],corner=prep['corner'],runtime=state,
        full11512_before_status='passed exact qualified samecorner draw',full11512_before=before,
        full_after_status='available; original failed acceptance retained' if has_after else 'not run to completion',
        full27_wave_and_decision_status='not run unless explicitly completed by original failed fixture report',
        wave_export_exists=any((out/n).exists() for n in ['phase0.dat','phase0.dat.gz']),
        warnings_before_initial_transient=len(re.findall('warning',parts[0],re.I)),
        warnings_after_initial_transient=len(re.findall('warning',parts[1],re.I)) if len(parts)==2 else None,
        original_errors=row['errors'],host_reported_progress=milestones,
        receipt_sha256={n:sha(out/n) for n in ['summary.json','run.json','run.log','run.progress.jsonl','population_transient.cir','preparation.json','provenance.json']},
        analyzer_sha256=sha(Path(__file__)),
        scope='No accepted-wave/parameter-AFTER inference from host progress. Clock deck has20ns rising start and120.2ns falling start; proximity of progress to those events is temporal observation, not causal attribution. Original1200s/source/seed/solver/criteria unchanged. No retry, extension, solver adoption or fast30 release.')
    a.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['full11512_before','receipt_sha256']},indent=2))


if __name__=='__main__':main()
