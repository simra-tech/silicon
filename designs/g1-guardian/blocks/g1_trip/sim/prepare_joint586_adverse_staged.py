#!/usr/bin/env python3
"""Freeze additive scheduling-only adverse contract; no simulation or criteria change."""
import argparse
import difflib
import json
from pathlib import Path
from run_joint586_adverse_staged import SIM,ROOT,sha


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--campaign-id',required=True)
    a=p.parse_args();assert '/' not in a.campaign_id
    old=SIM/'qualification/joint586-adverse30-contract-20260923-a/contract.json'
    assert sha(old)=='b57a8b37eb9f6f045e3c07a96936e3659cf2a16b982fe0b8d18afff082063312'
    contract=json.loads(old.read_text());assert all(sha(ROOT/n)==v for n,v in contract['live_bindings_sha256'].items())
    out=SIM/'qualification'/a.campaign_id;out.mkdir()
    source=SIM/'run_joint586_adverse_staged.py'
    original=SIM/'run_joint586_adverse_calibration.py'
    diff=''.join(difflib.unified_diff(original.read_text().splitlines(True),source.read_text().splitlines(True),
                                   fromfile='frozenSerialAdverseRunner',tofile='stagedIndependentHeldoutRunner'))
    (out/'declared_scheduling_difference.diff').write_text(diff)
    paths=[old,Path(__file__).absolute(),source,SIM/'audit_joint586_adverse_staged.py',SIM/'audit_joint586_adverse_calibration.py',
           SIM/'test_joint586_adverse_staged.py',SIM/'test_joint586_adverse_sample_gate.py']
    contract['live_bindings_sha256'].update({str(q.relative_to(ROOT)):sha(q) for q in paths})
    contract['prior_serial_contract_sha256']=sha(old)
    contract['staged_execution']=dict(runner_sha256=sha(source),auditor_sha256=sha(SIM/'audit_joint586_adverse_staged.py'),
        scheduling_difference_sha256=sha(out/'declared_scheduling_difference.diff'),
        rule='Original sequential binary endpoints/midpoints freeze full11512 vector and codes. Exact original ordered40guard+20residual inputs prehashed once. Independent processes claim distinct leaf directories, never mutate parent/vector. Every attempt retained; sole assembler requires all60 receipts in original order. Resource/cpu leases remain host gated per launch; no analog parity rerun needed for byte-identical inputs.',
        numerical_contract='Unchanged1200s per leaf; original full11512/27,18or19vectors,actual/legacy decisions, endpoint and solver-error checks.',
        qualification='120 generated decks across bothcorners byte-identical to frozen serial generator. Shared analysis/watchdog function calls AST-identical; missing/mutated/duplicate/out-of-order/failedleaf controls tested. No analog result from these software tests.')
    (out/'contract.json').write_text(json.dumps(contract,indent=2)+'\n')
    print(str((out/'contract.json').relative_to(ROOT)),sha(out/'contract.json'))


if __name__=='__main__':main()
