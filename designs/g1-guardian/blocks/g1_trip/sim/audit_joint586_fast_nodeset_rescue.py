#!/usr/bin/env python3
"""Independent fixed-nodeset14 evidence; cross-original exact failures separate."""
import argparse
import json
from pathlib import Path
from prepare_joint586_fast_nodeset_rescue import SIM,ROOT,sha,transform
from run_joint586_fast_nodeset_rescue import numerical_gate,phase_audit
from run_joint586_adverse_transient import compare18
from audit_joint586_population_op import variation


def own_checks(phases,waves):
    vector=lambda label,index=0:phases[label][index]['parameters_before']
    changed=variation(vector('enabled'),vector('changed'))
    checks=dict(enabled_repeat_vector=vector('enabled')==vector('repeat'),
        enabled_repeat_wave=waves['enabled'][0]==waves['repeat'][0],
        all3500_changed=sum(r['primitive_count'] for r in changed.values())==3500 and
            all(r['primitive_count']==r['primitives_with_changed_values'] for r in changed.values()),
        disabled_changed_vector=vector('disabled')==vector('disabledchanged'),
        disabled_changed_wave=waves['disabled'][0]==waves['disabledchanged'][0],
        return_all_vectors=all(vector('return',i)==vector('enabled') for i in range(4)),
        return_initial_wave=waves['return'][0]==waves['enabled'][0],
        return_final_wave=waves['return'][0]==waves['return'][3],
        return_decisions=phases['return'][0]['decisions']==phases['return'][3]['decisions'],
        SHN_pair_vector=vector('cm0_old18')==vector('cm0_shn19')==vector('enabled'))
    try:
        projection=compare18(waves['cm0_old18'][0].splitlines(keepends=True),waves['cm0_shn19'][0].splitlines(keepends=True))
        checks['SHN_original18_projection_exact']=True
    except (AssertionError,ValueError) as error:
        projection=dict(status='failed exact18 projection',error=repr(error));checks['SHN_original18_projection_exact']=False
    return checks,changed,projection


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--contract',type=Path,required=True)
    p.add_argument('--contract-sha256',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists() and sha(a.contract)==a.contract_sha256
    packet=json.loads(a.contract.read_text());assert all(sha(ROOT/n)==v for n,v in packet['bindings_sha256'].items())
    records=[];phases={};waves={};errors=[]
    for case in packet['cases']:
        out=SIM/'qualification'/case['run'];record=dict(kind=case['kind'],label=case['label'],run=case['run'],status='not run')
        records.append(record)
        if not (out/'summary.json').exists():continue
        try:
            row,=json.loads((out/'summary.json').read_text());state=json.loads((out/'run.json').read_text())
            record['original_summary_status']=row.get('status')
            assert state==row['runtime'] and state['timeout_s']==case['watchdog_s']
            log=(out/'run.log').read_text();numerical_gate(state,log)
            original=SIM/'qualification'/case['original_run']
            expected,audit=transform((original/'population_transient.cir').read_text(),case['original_run'],case['run'],packet['fixed_guesses'])
            assert (out/'population_transient.cir').read_text()==expected and sha(out/'population_transient.cir')==case['deck_sha256']
            assert audit==case['transform']
            assert all(sha(out/n)==sha(original/n)==v for n,v in case['source_hashes'].items())
            assert sha(out/'population_inventory.json')==case['inventory_sha256']
            provenance=json.loads((out/'provenance.json').read_text())
            assert provenance['runtime_identity']==case['runtime_identity'] and all(provenance['input_checks'].values())
            if case['reuse_receipts_sha256']:
                assert all(sha(out/n)==v for n,v in case['reuse_receipts_sha256'].items())
            else:
                assert provenance['contract_sha256']==a.contract_sha256
                assert sha(out/'runner.py')==sha(SIM/'run_joint586_fast_nodeset_rescue.py')==provenance['runner_sha256']
                assert json.loads((out/'preparation.json').read_text())==case
            found,blob=phase_audit(case,log,out)
            if not case['reuse_receipts_sha256']:assert found==row['phases']
            sampling=all(r['wave_analysis']['sampling_status']=='passed' for r in found)
            record.update(status='passed finite fullparameter evidence',sampling_status='passed' if sampling else 'failed',
                phases=[{k:v for k,v in r.items() if k not in ['parameters_before','parameters_after','legacy27','wave_analysis']} for r in found],
                receipts_sha256={n:sha(out/n) for n in ['summary.json','run.json','run.log','provenance.json','population_transient.cir']})
            if case['kind']=='own':phases[case['label']]=found;waves[case['label']]=blob
        except (AssertionError,ValueError,KeyError,OSError,IndexError) as error:
            record.update(status='failed finite/fullparameter evidence',analysis_error=repr(error));errors.append(case['kind']+'/'+case['label'])
    checks={};changed='not run';projection='not run'
    if len(phases)==8:
        checks,changed,projection=own_checks(phases,waves)
    complete=len(records)==14 and all(r['status']=='passed finite fullparameter evidence' and r['sampling_status']=='passed' for r in records)
    status='passed fixed-nodeset own6/SHN/sixfixture consistency qualification' if complete and checks and all(checks.values()) else 'failed or incomplete fixed-nodeset consistency qualification'
    result=dict(status=status,contract_sha256=a.contract_sha256,records=records,own_checks=checks,
        changed_seed_variation=changed,SHN_projection=projection,audit_errors=errors,
        cross_original_exact_comparisons='Per-phase booleans in records; false remains exactcomparisonFAIL and is not used as a numerical-tolerance substitute.',
        population_release='not run; separate reviewed disposition required',auditor_sha256=sha(Path(__file__)),scope=packet['scope'])
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(a.output,sha(a.output))
    raise SystemExit(0 if status.startswith('passed') else 1)


if __name__=='__main__':main()
