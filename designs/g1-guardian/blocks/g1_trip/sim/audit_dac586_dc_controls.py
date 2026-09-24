#!/usr/bin/env python3
"""Independent conditional method audit; exact failures remain separate fields."""
import argparse
import json
from prepare_dac586_dc_controls import ROOT,SIM,transform
from run_dac586_dc_control import analyze
from run_dac586_static_control import sha


def audit(execution,digest,phase):
    assert sha(execution)==digest;packet=json.loads(execution.read_text())
    assert packet['numerical_comparison_approved'] is True
    assert all(sha(ROOT/name)==value for name,value in packet['source_bindings_sha256'].items())
    proposal_path=ROOT/packet['proposal'];assert sha(proposal_path)==packet['proposal_sha256']
    proposal=json.loads(proposal_path.read_text());assert all(sha(ROOT/name)==value for name,value in proposal['bindings_sha256'].items())
    cases=proposal['controls'][:11] if phase=='static' else proposal['controls']
    results={};rows=[]
    for case in cases:
        out=SIM/'qualification'/case['run'];prep=json.loads((out/'preparation.json').read_text())
        assert sha(out/'preparation.json')==case['preparation_sha256']
        ref=SIM/'qualification'/prep['reference_static']
        assert (out/'dac_dc.cir').read_text()==transform((ref/'dac_static.cir').read_text(),ref.name,out.name,*prep['codes'],prep['groups'],dc=prep['method']=='dc-two-point-forward-reverse')
        assert sha(out/'dac_dc.cir')==prep['deck_sha256']
        assert all(sha(out/name)==value for name,value in prep['source_hashes'].items())
        assert sha(out/'population_inventory.json')==prep['inventory_sha256']
        assert all(sha(ROOT/name)==value for name,value in prep['bindings_sha256'].items())
        if not all((out/name).exists() for name in ['run.json','run.log','summary.json','provenance.json']):
            rows.append(dict(run=out.name,label=case['label'],status='not run'));continue
        provenance=json.loads((out/'provenance.json').read_text())
        assert provenance['execution_sha256']==digest and provenance['runtime_identity']==prep['expected_runtime_identity']
        assert provenance['runner_sha256']==packet['source_bindings_sha256'][str((SIM/'run_dac586_dc_control.py').relative_to(ROOT))]
        result=analyze(out,prep,json.loads((out/'run.json').read_text()))
        assert result==json.loads((out/'summary.json').read_text())
        results[case['label']]=result
        files=['run.json','run.log','summary.json','provenance.json','dac_dc.cir','preparation.json']+[path.name for path in out.glob('*.dat')]
        rows.append(dict(run=out.name,label=case['label'],status=result['status'],strict_static_equivalence=result['strict_static_equivalence'],
            prospective_consistency=result.get('prospective_consistency','not run'),comparisons=result['reference_comparisons'],timing=result.get('timing'),
            receipts_sha256={name:sha(out/name) for name in files}))
    def equal_data(a,b,filename):
        if a not in results or b not in results:return None
        if not all(results[label]['status'].startswith('passed conditional') for label in [a,b]):return False
        paths=[SIM/'qualification'/next(case['run'] for case in cases if case['label']==label)/filename for label in [a,b]]
        # Same output schema, but compare decoded token bytes, not padding or directory names.
        return [[line.split() for line in path.read_bytes().splitlines()] for path in paths][0]==[[line.split() for line in path.read_bytes().splitlines()] for path in paths][1]
    repeat=equal_data('output','repeat','op0.dat')
    returned=results.get('return',{}).get('same_method_return_exact')
    dc_repeat=None if phase=='static' else {name:equal_data('dc-room','dc-room-repeat',name) for name in ['op0.dat','forward.dat','reverse.dat']}
    passed=len(rows)==len(cases) and all(row['status'].startswith('passed conditional') for row in rows) and repeat is True and returned is True
    if phase!='static':passed=passed and all(value is True for value in dc_repeat.values())
    return dict(status=('passed conditional staticB11 qualification' if phase=='static' else 'passed conditional DC method controls') if passed else 'failed or incomplete conditional method controls',
        execution_sha256=digest,controls=rows,completed_controls=sum(row['status']!='not run' for row in rows),repeat_exact=repeat,return_exact=returned,dc_repeat_exact=dc_repeat,
        scope='Finite anchors and declared numerical-consistency screen only; strict exact status retained. No global solver-error proof, all-code/statistical/guard/settling or isolatedleakage acceptance.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execution',required=True);p.add_argument('--execution-sha256',required=True)
    p.add_argument('--phase',choices=['static','dc'],required=True);p.add_argument('--output',required=True);a=p.parse_args()
    result=audit(ROOT/a.execution,a.execution_sha256,a.phase);out=ROOT/a.output;assert not out.exists()
    out.write_text(json.dumps(result,indent=2)+'\n');print(result['status'])
