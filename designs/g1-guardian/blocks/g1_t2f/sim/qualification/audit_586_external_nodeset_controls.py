#!/usr/bin/env python3
"""Independent OP diagnostic reanalysis and unwaived pair differences."""
import argparse
import json
from prepare_586_external_nodeset_controls import HERE,ROOT,REFERENCE,sha,transform
from run_586_external_nodeset_control import analyze


def pair(a,b):
    if not a or not b or a['status']!='passed OP/full3180 evidence' or b['status']!='passed OP/full3180 evidence':
        return dict(status='not run; missing or failed comparison arm')
    assert a['op_header']==b['op_header']
    return dict(status='compared; exact booleans retained independently',
        parameters_exact=a['parameters_before']==b['parameters_before'],
        numeric_values_exact=a['op_values']==b['op_values'],decoded_token_bytes_exact=a['decoded_token_rows']==b['decoded_token_rows'],
        differences={name:y-x for name,x,y in zip(a['op_header'][1:],a['op_values'][1:],b['op_values'][1:])})


def audit(implementation,digest):
    assert sha(implementation)==digest;bound=json.loads(implementation.read_text())
    assert all(sha(ROOT/name)==value for name,value in bound['bindings_sha256'].items())
    contract=ROOT/bound['contract'];assert sha(contract)==bound['contract_sha256'];packet=json.loads(contract.read_text())
    assert all(sha(ROOT/name)==value for name,value in packet['bindings_sha256'].items())
    rows={};results={}
    for case in packet['cases']:
        out=HERE/'runs'/case['run_id'];label=case['label']
        if not (out/'summary.json').exists():rows[label]=dict(status='not run');continue
        assert (out/'probe.cir').read_text()==transform((REFERENCE/'p02/probe.cir').read_text(),label,packet['guesses'])
        assert sha(out/'probe.cir')==case['deck_sha256']
        assert all(sha(out/name)==value for name,value in packet['source_hashes'].items())
        assert sha(out/'population_inventory.json')==packet['inventory_sha256']
        assert sha(out/'.spiceinit')==sha(REFERENCE/'p02/.spiceinit')
        provenance=json.loads((out/'provenance.json').read_text())
        assert provenance['implementation_sha256']==digest and provenance['runtime_identity']==packet['runtime_identity']
        assert provenance['runner_sha256']==bound['bindings_sha256'][str((HERE/'run_586_external_nodeset_control.py').relative_to(ROOT))]
        recomputed=analyze(out,packet,case,json.loads((out/'run.json').read_text()))
        assert recomputed==json.loads((out/'summary.json').read_text())
        results[label]=recomputed;rows[label]=dict(status=recomputed['status'],errors=recomputed['errors'],
            receipts_sha256={name:sha(out/name) for name in ['run.json','run.log','summary.json','probe.cir','provenance.json']})
    return dict(status='independent diagnostic audit; no method adoption',controls=rows,
        sparse_original_vs_nodeset=pair(results.get('sparse-original'),results.get('sparse-nodeset')),
        sparse_nodeset_vs_klu_nodeset=pair(results.get('sparse-nodeset'),results.get('klu-nodeset')),
        implementation_sha256=digest,scope='Failed baselines and false exact comparisons remain explicit; no transient/accuracy or population qualification.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--implementation',required=True)
    p.add_argument('--implementation-sha256',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    result=audit(ROOT/a.implementation,a.implementation_sha256);out=ROOT/a.output;assert not out.exists()
    out.write_text(json.dumps(result,indent=2)+'\n');print(result['status'])
