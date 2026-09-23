"""Incremental terminal9 audit; exact previous13 reused, not simulated or re-audited."""
import argparse
import json
from pathlib import Path
from audit_joint586_calibration import inspect,SIM,sha
from audit_joint586_post100_milestone import passed_runtime

SEEDS=[73109,73111,73112,73113,73114,73116,73117,73118,73121]
PREVIOUS_SHA='ba87a9401bb54fd09198325b18284233e77f0fb7f6375c418ad9004fa8785e3a'


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    previous=SIM/'qualification/joint586-post100-thirteen-audit-20260923-a.json';assert sha(previous)==PREVIOUS_SHA
    prior=json.loads(previous.read_text());assert len(prior['records'])==13
    assert not set(SEEDS)&set(prior['requested_seeds']) and sorted(SEEDS+prior['requested_seeds'])==list(range(73101,73123))
    records=[]
    for seed in SEEDS:
        run=SIM/'qualification'/('joint586-calibration-s%d-20260922-a'%seed);record=inspect(run)
        assert record['complete'] and record['seed']==seed
        for entry in record['leaves']:
            leaf=SIM/'qualification'/entry['run'];runtime=json.loads((leaf/'run.json').read_text());log=(leaf/'run.log').read_text()
            if entry['status']=='passed':passed_runtime(runtime,log)
            else:assert runtime['status']==entry['watchdog_status'] and runtime['returncode']==entry['returncode']
            entry['runtime_receipt_sha256']=sha(leaf/'run.json')
        records.append(record)
    allrecords=prior['records']+records;vectors=[r['parameter_vector_sha256'] for r in allrecords];assert len(set(vectors))==22
    firstfile=SIM/'qualification/joint586-first100-audit-20260923.json';assert sha(firstfile)==prior['first100_audit_sha256']
    first=json.loads(firstfile.read_text());assert not set(vectors)&{r.get('parameter_vector_sha256') for r in first['records']}
    result=dict(status='passed incremental9 terminal evidence audit; exact previous13 retained',requested_seeds=SEEDS,new_records=records,
        cumulative_post100_seeds=list(range(73101,73123)),cumulative_post100_terminal=22,
        cumulative_fully_passed=sum(r['status']=='passed fullcalibration guard residual' for r in allrecords),
        cumulative_failed_completed=sum(r['status']!='passed fullcalibration guard residual' for r in allrecords),
        previous13_audit_sha256=PREVIOUS_SHA,first100_audit_sha256=sha(firstfile),auditor_sha256=sha(Path(__file__)),
        base_auditor_sha256=sha(SIM/'audit_joint586_calibration.py'),runtime_auditor_sha256=sha(SIM/'audit_joint586_post100_milestone.py'),
        scope='Original fixed300 denominator and all prior failures retained. No rerun or source/method adoption; other required parents continue.')
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(result['status'],result['cumulative_fully_passed'],result['cumulative_failed_completed'])


if __name__=='__main__':main()
