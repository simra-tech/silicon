"""Fixed thirteen terminal attempts; full independent source/leaf audit, no filtering."""
import argparse
import json
from pathlib import Path
import re
from audit_joint586_calibration import inspect,SIM,sha

SEEDS=list(range(73101,73109))+[73110,73115,73119,73120,73122]


def passed_runtime(state,log):
    assert state['status']=='completed' and state['returncode']==0
    assert 'JOINT_POPULATION_TRAN_END' in log
    assert not re.search(r'^Error|Timestep too small|analysis aborted|doAnalyses:|no such vector|no such parameter|not available|cannot parse',log,re.I|re.M)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
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
    vectors=[r['parameter_vector_sha256'] for r in records];assert len(vectors)==len(set(vectors))==13
    previous=SIM/'qualification/joint586-first100-audit-20260923.json';first=json.loads(previous.read_text())
    assert not set(vectors)&{r.get('parameter_vector_sha256') for r in first['records']}
    result=dict(status='passed fixed thirteen terminal evidence audit; failures retained',requested_seeds=SEEDS,requested_samples=13,completed_samples=13,
        fully_passed_samples=sum(r['status']=='passed fullcalibration guard residual' for r in records),failed_completed_samples=sum(r['status']!='passed fullcalibration guard residual' for r in records),
        records=records,first100_audit_sha256=sha(previous),distinct_vectors_from_first100=True,auditor_sha256=sha(Path(__file__)),base_auditor_sha256=sha(SIM/'audit_joint586_calibration.py'),
        scope='All thirteen original terminal attempts at the declared milestone, including73115 numerical failure. Other samples continue unchanged. No survivor yield or changed-SENSE qualification.')
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(result['status'],result['fully_passed_samples'],result['failed_completed_samples'])


if __name__=='__main__':main()
