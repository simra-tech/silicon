#!/usr/bin/env python3
"""Independent owncorner six-control OP gate; failures never omitted."""
import argparse
import json
from pathlib import Path
from prepare_joint586_adverse import SIM,ROOT,sha
from audit_joint586_population_op import variation
from run_bgr_substitution_draw_audit import read_group


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--contract',type=Path,required=True)
    p.add_argument('--corner',choices=['slow','fast'],required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    assert not a.output.exists()
    packet=json.loads(a.contract.read_text());groups=packet['groups']
    rows={};runs={};receipts={};issues=[]
    for case in packet['op_controls']:
        if case['corner']!=a.corner:continue
        label=case['label'];run=(ROOT/case['deck']).parent;runs[label]=run
        if not (run/'summary.json').exists():
            rows[label]=dict(op_qualification_status='not run')
            continue
        row,=json.loads((run/'summary.json').read_text());rows[label]=row
        receipts[label]={name:sha(run/name) for name in ['summary.json','provenance.json','population_op.cir','run.json','run.log','runner.py']}
        try:
            prov=json.loads((run/'provenance.json').read_text())
            assert prov['contract_sha256']==sha(a.contract) and all(prov['input_checks'].values())
            assert prov['runtime_identity']==packet['expected_runtime_identity']
            assert sha(run/'population_op.cir')==case['deck_sha256']
            assert all(sha(run/n)==d for n,d in case['source_hashes'].items())
            if row['op_qualification_status']=='passed':
                log=(run/'run.log').read_text()
                assert len(row['phases'])==len(case['temperatures_C'])
                for i,phase in enumerate(row['phases']):
                    for when in ['BEFORE','AFTER']:
                        actual=read_group(log,'P%d_NON_BGR_%s'%(i,when),groups['NON_BGR'])+read_group(log,'P%d_BGR_%s'%(i,when),groups['BGR'])
                        assert len(actual)==11512 and actual==phase['parameters_'+when.lower()]
                        assert read_group(log,'P%d_LEGACY27_%s'%(i,when),groups['LEGACY27'])==phase['legacy27']
                    assert phase['op_data_sha256']==sha(run/('op%d.dat'%i))
        except (AssertionError,ValueError,OSError,KeyError,IndexError) as error:
            issues.append(dict(label=label,error=repr(error)))
    result=dict(status='failed or incomplete owncorner OP qualification',corner=a.corner,
        individual_controls={label:row['op_qualification_status'] for label,row in rows.items()},
        receipts_sha256=receipts,contract_sha256=sha(a.contract),audit_errors=issues,
        transient_status='not run; this OP gate is not transient qualification',checks={},
        scope='Allsix owncorner attempts retained. Exactrepeat/disabled/return is not replaced with consistencybounds. Source/model/physicaladoption unchanged.')
    if len(rows)==6 and not issues and all(r['op_qualification_status']=='passed' for r in rows.values()):
        vectors={label:row['phases'][0]['parameters_before'] for label,row in rows.items()}
        changed=variation(vectors['enabled'],vectors['changed'])
        checks=dict(enabled_repeat11512=vectors['enabled']==vectors['repeat'],
            enabled_repeat_opbytes=(runs['enabled']/'op0.dat').read_bytes()==(runs['repeat']/'op0.dat').read_bytes(),
            changed_all3500=all(v['primitive_count']==v['primitives_with_changed_values'] for v in changed.values()),
            disabled_seed11512=vectors['disabled']==vectors['disabledchanged'],
            disabled_seed_opbytes=(runs['disabled']/'op0.dat').read_bytes()==(runs['disabledchanged']/'op0.dat').read_bytes(),
            return_initial_opbytes=(runs['enabled']/'op0.dat').read_bytes()==(runs['return']/'op0.dat').read_bytes(),
            return11512=all(p['parameters_before']==p['parameters_after']==vectors['enabled'] for p in rows['return']['phases']),
            return_opbytes=(runs['return']/'op0.dat').read_bytes()==(runs['return']/'op3.dat').read_bytes())
        result.update(checks=checks,changed_seed_variation=changed,
            return_max_abs_node_change_V=rows['return']['return_max_abs_node_change_V'],
            return_separate_1uV_bound=rows['return']['return_separate_1uV_bound'])
        result['status']='passed strict owncorner OP qualification' if all(checks.values()) else 'failed exact owncorner OP cross-control gate'
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='receipts_sha256'},indent=2))
    raise SystemExit(0 if result['status']=='passed strict owncorner OP qualification' else 1)


if __name__=='__main__':main()
