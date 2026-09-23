#!/usr/bin/env python3
"""Prepare a COPY-only positive partial-C diagnostic after zero-C controls.

Explicit VSUBS omission is a sensitivity assumption, never a physical bound.
All978 raw entries remain in the ledger; only844 proven source-net pairs enter
this hypothesis. No full MIM pair subtraction or compact-model replacement.
"""
import argparse,hashlib,json,math
from pathlib import Path
from expose_comp45_internal_nodes import expose,parse,flatten,SOURCE

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def prepare(raw,view,rows):
    text,proof=expose(raw)
    labels={r['pex_label']:r['source_net'] for r in view['labels']}
    assert len(labels)==134 and set(labels.values())==set(proof['node_mapping'])
    added=[];excluded=[];seen=set()
    for i,r in enumerate(rows):
        value=r['capacitance_fF'];assert float.fromhex(r['capacitance_fF_hex'])==value and math.isfinite(value) and value>=0
        key=tuple(sorted([r['net1'],r['net2']]));assert key not in seen and key[0]!=key[1];seen.add(key)
        if 'VSUBS' in key:
            assert all(n=='VSUBS' or n in labels for n in key)
            excluded.append(dict(raw=r,reason='Unbound extractor substrate excluded by explicit diagnostic hypothesis; NOT zero physical coupling or a bound'))
            continue
        assert all(n in labels for n in key)
        source_nodes=[labels[n] for n in key]
        nodes=[proof['node_mapping'][n] for n in source_nodes]
        assert nodes[0]!=nodes[1]
        c_F=value*1e-15;number=format(c_F,'.17g');assert float(number)==c_F
        name='CPRIVATE_PARTIAL_%04d'%i;assert name not in text
        line=' '.join([name]+nodes+[number])
        added.append(dict(raw=r,source_nodes=source_nodes,nodes=nodes,line=line,capacitance_F=c_F))
    assert len(added)==844 and len(excluded)==134 and len(rows)==978
    addition='* Explicitly incomplete source-net-pair field sensitivity; VSUBS unbound.\n'+'\n'.join(r['line'] for r in added)+'\n'
    assert text.count('.ends')==3
    candidate=text.replace('.ends',addition+'.ends',1)
    assert candidate.replace(addition,'',1)==text
    # No primitive/card change beyond previously proven private port exposure.
    recovered=candidate.replace(addition,'',1)
    for edit in reversed(proof['edits']):recovered=recovered.replace(edit['new'],edit['old'])
    assert recovered.encode()==raw
    return candidate,dict(status='prepared incomplete partial-C diagnostic COPY only',original_source_sha256=SOURCE,
        diagnostic_source_sha256=hashlib.sha256(candidate.encode()).hexdigest(),exact_inverse=True,
        added_count=len(added),excluded_count=len(excluded),added=added,excluded=excluded,
        private_source_proof=proof,all_raw_pairs_accounted=True,delta_insertion=False,
        primitive_model_or_parameter_changes=False,full_MIM_pair_subtraction=False,
        complete_field_PM_acceptance='not qualified',finite_wire_R='not represented',
        current_injection_weights='not chosen',external_nine_ports='unchanged')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ['source','view','extraction','zero-noise','zero-step','output']:p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();assert not a.output.exists()
    for path,mode in [(a.zero_noise,'noise'),(a.zero_step,'step')]:
        q=json.loads(path.read_text());assert q['status']=='passed exact zero-C instrumentation control' and q['mode']==mode
        assert q['own_parameter_gate_exact'] and q['own_OP_exact'] and q['own_observations_exact'] and all(q['saved_wave_exact'].values())
    view=json.loads((a.view/'manifest.json').read_text());ex=json.loads((a.extraction/'summary.json').read_text())
    assert ex['status']=='passed raw native CC only; completefield FAILED' and ex['exact_source_node_mapping']=='passed'
    assert ex['source_sha256']==view['source_sha256']==sha(a.source)==SOURCE
    assert ex['view_GDS_sha256']==view['GDS_sha256'] and ex['inputs_tools_cards_unchanged']
    caps=a.extraction/'exact_capacitances.json';assert sha(caps)==ex['capacitor_sha256']
    text,proof=prepare(a.source.read_bytes(),view,json.loads(caps.read_text()))
    proof.update(view_sha256=sha(a.view/'manifest.json'),extraction_sha256=sha(a.extraction/'summary.json'),
        raw_capacitors_sha256=sha(caps),zero_noise_sha256=sha(a.zero_noise),zero_step_sha256=sha(a.zero_step))
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    (a.output/'sense_partial_c.spice').write_text(text);(a.output/'summary.json').write_text(json.dumps(proof,indent=2)+'\n')

if __name__=='__main__':main()
