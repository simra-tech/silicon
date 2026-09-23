#!/usr/bin/env python3
"""Exact fixed33 subset for compact export; no simulation or audit rerun."""
import argparse,json
from pathlib import Path
from export_joint586_calibration import sha,validate_audit

def derive(audit,parent_sha):
    records=validate_audit(audit)
    assert audit['requested_samples']==100 and [r['seed'] for r in records]==list(range(73001,73101))
    chosen=[r for r in records if 73068<=r['seed']<=73100]
    assert len(chosen)==33 and [r['seed'] for r in chosen]==list(range(73068,73101))
    return dict(status='passed read-only evidence audit; exact fixed33 subset of independently audited first100',
        requested_samples=33,completed_samples=33,
        fully_passed_samples=sum(r['status']=='passed fullcalibration guard residual' for r in chosen),
        failed_completed_samples=sum(r['status']!='passed fullcalibration guard residual' for r in chosen),
        records=chosen,parent_first100_audit_sha256=parent_sha,original_independent_auditor_sha256=audit['auditor_sha256'],
        deriver_sha256=sha(Path(__file__)),scope='Contiguous73068..73100 includes every original success/failure; exact records copied from hash-bound first100 evidence audit. Earlier1..67 portable exports already retained. This is an export projection, not a new audit or filtered yield population.')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--audit',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();assert not args.output.exists()
    result=derive(json.loads(args.audit.read_text()),sha(args.audit))
    with args.output.open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k!='records'},indent=2))

if __name__=='__main__':main()
