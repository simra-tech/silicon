#!/usr/bin/env python3
"""Fixed ordered fast-nodeset cohort; independent staged ledger and full evidence."""
import argparse
import json
from pathlib import Path
from audit_joint586_fast_nodeset_staged import staged_inspect
from run_joint586_fast_nodeset_staged import SIM,sha


def expansion_safe(report):
    rows=report['records']
    return (report['status'].startswith('passed read-only evidence audit')
        and report['requested_samples']==report['completed_samples']==20
        and [r['seed'] for r in rows]==list(range(78101,78121))
        and all(r.get('evidence_status')=='passed' and r.get('complete') and r.get('leaves')
            and all(x['status']=='passed' for x in r['leaves']) for r in rows))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--first-seed',type=int,required=True)
    p.add_argument('--last-seed',type=int,required=True);p.add_argument('--contract',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert 78101<=a.first_seed<=a.last_seed<=78130 and not a.output.exists()
    rows=[]
    for seed in range(a.first_seed,a.last_seed+1):
        run=SIM/'qualification'/('joint586-fast-nodeset-calibration-s%d-20260923-a'%seed)
        row=dict(seed=seed,run=run.name,status='not run',complete=False,evidence_status='not run')
        if (run/'summary.json').exists():
            try:
                row=staged_inspect(run,a.contract);assert row['seed']==seed and row['corner']=='fast'
                row['evidence_status']='passed'
            except (AssertionError,OSError,ValueError,KeyError,IndexError) as error:
                row=dict(seed=seed,run=run.name,status='failed evidence audit',complete=False,evidence_status='failed',error=repr(error))
        rows.append(row)
    hashes=[r['parameter_vector_sha256'] for r in rows if r.get('parameter_vector_sha256')]
    distinct=len(hashes)==len(set(hashes))
    result=dict(status='passed read-only evidence audit; electrical failures separate' if distinct and all(r['evidence_status']=='passed' for r in rows) else 'failed or incomplete evidence audit',
        requested_samples=len(rows),completed_samples=sum(r['complete'] for r in rows),records=rows,
        fully_passed_samples=sum(r['status']=='passed fullcalibration guard residual' for r in rows),
        failed_completed_samples=sum(r['complete'] and r['status']!='passed fullcalibration guard residual' for r in rows),
        distinct_full_parameter_vectors=len(set(hashes)),distinct_vectors_check=distinct,
        campaign_contract_sha256=sha(a.contract),auditor_sha256=sha(Path(__file__)),
        staged_auditor_sha256=sha(SIM/'audit_joint586_fast_nodeset_staged.py'),
        scope='Ordered fixed78101..78130 population, fixed nodeset method explicitly separate from original failed method. No survivor filtering or criterion change; all11512+27 and60heldout ledger audited independently.')
    result['first20_expansion_safe']=expansion_safe(result)
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(a.output,sha(a.output))
    raise SystemExit(0 if result['status'].startswith('passed') else 1)


if __name__=='__main__':main()
