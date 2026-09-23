#!/usr/bin/env python3
"""Explicit old-a controls plus corrected-return-b audit; no original failure erasure."""
import argparse
import json
from pathlib import Path
from prepare_joint586_fast_nodeset_rescue import SIM,ROOT,sha,transform
from run_joint586_fast_nodeset_rescue import numerical_gate,phase_audit
from audit_joint586_fast_nodeset_rescue import own_checks


def audit_case(case,packet,digest):
    out=SIM/'qualification'/case['run']
    row,=json.loads((out/'summary.json').read_text());state=json.loads((out/'run.json').read_text())
    assert state==row['runtime'] and state['timeout_s']==case['watchdog_s']
    log=(out/'run.log').read_text();numerical_gate(state,log)
    old=SIM/'qualification'/case['original_run']
    expected,transform_audit=transform((old/'population_transient.cir').read_text(),case['original_run'],case['run'],packet['fixed_guesses'])
    assert (out/'population_transient.cir').read_text()==expected and sha(out/'population_transient.cir')==case['deck_sha256']
    assert transform_audit==case['transform']
    assert all(sha(out/n)==sha(old/n)==v for n,v in case['source_hashes'].items())
    assert sha(out/'population_inventory.json')==case['inventory_sha256']
    provenance=json.loads((out/'provenance.json').read_text())
    assert provenance['runtime_identity']==case['runtime_identity'] and all(provenance['input_checks'].values())
    if case['reuse_receipts_sha256']:
        assert all(sha(out/n)==v for n,v in case['reuse_receipts_sha256'].items())
    else:
        assert provenance['contract_sha256']==packet['inherited_execution_contract_sha256'].get(case['run'],digest)
        assert sha(out/'runner.py')==sha(SIM/'run_joint586_fast_nodeset_rescue.py')==provenance['runner_sha256']
        assert json.loads((out/'preparation.json').read_text())==case
        if 'validation_adapter_sha256' in case:
            assert sha(out/'validation_adapter.py')==case['validation_adapter_sha256']
    phases,blobs=phase_audit(case,log,out)
    if not case['reuse_receipts_sha256']:assert phases==row['phases']
    record=dict(kind=case['kind'],label=case['label'],run=case['run'],status='passed finite fullparameter evidence',
        sampling_status='passed' if all(p['wave_analysis']['sampling_status']=='passed' for p in phases) else 'failed',
        phases=[{k:v for k,v in p.items() if k not in ['parameters_before','parameters_after','legacy27','wave_analysis']} for p in phases],
        receipts_sha256={n:sha(out/n) for n in ['summary.json','run.json','run.log','provenance.json','population_transient.cir']})
    return record,phases,blobs


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--contract',type=Path,required=True)
    p.add_argument('--contract-sha256',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists() and sha(a.contract)==a.contract_sha256
    packet=json.loads(a.contract.read_text());assert all(sha(ROOT/n)==v for n,v in packet['bindings_sha256'].items())
    records=[];phases={};waves={};errors=[]
    for case in packet['cases']:
        record=dict(kind=case['kind'],label=case['label'],run=case['run'],status='not run')
        if (SIM/'qualification'/case['run']/'summary.json').exists():
            try:
                record,found,blob=audit_case(case,packet,a.contract_sha256)
                if case['kind']=='own':phases[case['label']]=found;waves[case['label']]=blob
            except (AssertionError,ValueError,KeyError,OSError,IndexError) as error:
                record.update(status='failed finite/fullparameter evidence',analysis_error=repr(error));errors.append(case['kind']+'/'+case['label'])
        records.append(record)
    checks={};changed='not run';projection='not run'
    if len(phases)==8:checks,changed,projection=own_checks(phases,waves)
    complete=len(records)==14 and all(r['status']=='passed finite fullparameter evidence' and r['sampling_status']=='passed' for r in records)
    status='passed fixed-nodeset own6/SHN/sixfixture consistency qualification' if complete and checks and all(checks.values()) else 'failed or incomplete fixed-nodeset consistency qualification'
    result=dict(status=status,contract_sha256=a.contract_sha256,records=records,own_checks=checks,
        changed_seed_variation=changed,SHN_projection=projection,audit_errors=errors,
        preserved_preflight_failure=packet['preserved_preflight_failure'],
        cross_original_exact_comparisons='False per-phase exact booleans remain FAILED, separate from new-method consistency.',
        population_release='not run; separately reviewed disposition required',auditor_sha256=sha(Path(__file__)),scope=packet['scope'])
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(a.output,sha(a.output))
    raise SystemExit(0 if status.startswith('passed') else 1)


if __name__=='__main__':main()
