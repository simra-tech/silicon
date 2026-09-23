#!/usr/bin/env python3
"""Exact completed-record projections for compact export, never new analysis."""
import argparse
import hashlib
import json
from pathlib import Path


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def derive(audit,kind,parent_sha):
    assert audit['status'].startswith('passed read-only evidence audit')
    assert len(audit['records'])==audit['requested_samples']==audit['completed_samples']
    assert all(r['complete'] for r in audit['records'])
    if kind=='t2f-fixed55':
        assert [r['seed'] for r in audit['records']]==list(range(74101,74201))
        chosen=audit['records'][45:];assert [r['seed'] for r in chosen]==list(range(74146,74201))
        counts=dict(passed_samples=sum(r['status']=='passed' for r in chosen),failed_complete_samples=sum(r['status']!='passed' for r in chosen))
    else:
        assert kind=='slow-firstsample' and audit['first_sample_gate_passed'] is True
        assert len(audit['records'])==1 and audit['records'][0]['seed']==77101 and audit['records'][0]['corner']=='slow'
        chosen=audit['records'];counts=dict(fully_passed_samples=sum(r['status']=='passed fullcalibration guard residual' for r in chosen),failed_completed_samples=sum(r['status']!='passed fullcalibration guard residual' for r in chosen))
    return dict(status='passed read-only evidence audit; exact completed-record projection for export',
        requested_samples=len(chosen),completed_samples=len(chosen),records=chosen,
        original_independent_audit_sha256=parent_sha,original_independent_auditor_sha256=audit['auditor_sha256'],
        deriver_sha256=sha(Path(__file__)),**counts,
        scope='Exact ordered records copied from the complete independently audited parent; no source/wave analysis repeated and no failed sample filtered. Original audit is authoritative; projection is for compact export only.')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--audit',type=Path,required=True)
    p.add_argument('--parent-sha256',required=True);p.add_argument('--kind',choices=['t2f-fixed55','slow-firstsample'],required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert sha(a.audit)==a.parent_sha256 and not a.output.exists()
    result=derive(json.loads(a.audit.read_text()),a.kind,a.parent_sha256)
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(a.output.name,sha(a.output))


if __name__=='__main__':main()
