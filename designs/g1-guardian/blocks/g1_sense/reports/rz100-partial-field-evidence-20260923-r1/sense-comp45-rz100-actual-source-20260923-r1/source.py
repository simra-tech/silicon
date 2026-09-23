#!/usr/bin/env python3
"""Own-native R100 partial C, gated by this source's exact zero-C controls."""
import argparse,hashlib,json,math,sys
from pathlib import Path
from expose_rz100_internal_nodes import expose,SOURCE
from expose_comp45_internal_nodes import SOURCE as PARENT
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'layout/coordinated_comp45_rz62'))
from analyze_affected_field_cc import matrix,tests
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def prepare(raw,view,rows):
    text,proof=expose(raw);labels={q['pex_label']:q['source_net'] for q in view['labels']}
    assert len(labels)==134 and set(labels.values())==set(proof['node_mapping'])
    full,_=matrix(rows);assert set(full['nodes'])==set(labels)|{'VSUBS'}
    added=[];excluded=[];seen=set()
    for i,row in enumerate(rows):
        value=row['capacitance_fF'];assert math.isfinite(value) and value>=0 and float.fromhex(row['capacitance_fF_hex'])==value
        key=tuple(sorted([row['net1'],row['net2']]));assert key[0]!=key[1] and key not in seen;seen.add(key)
        if 'VSUBS' in key:
            assert all(n=='VSUBS' or n in labels for n in key)
            excluded.append(dict(raw=row,reason='Unbound VSUBS omitted explicitly; neither physical zero nor bound'));continue
        assert all(n in labels for n in key)
        source_nodes=[labels[n] for n in key];nodes=[proof['node_mapping'][n] for n in source_nodes]
        value_F=value*1e-15;printed=format(value_F,'.17g');assert float(printed)==value_F
        line=' '.join(['CPRIVATE_ACTUAL_%04d'%i]+nodes+[printed]);assert line.split()[0] not in text
        added.append(dict(raw=row,source_nodes=source_nodes,nodes=nodes,line=line,capacitance_F=value_F))
    assert len(rows)==978 and len(added)==844 and len(excluded)==134
    assert {n for r in excluded for n in (r['raw']['net1'],r['raw']['net2']) if n!='VSUBS'}==set(labels)
    addition='* Own-native incomplete R100 field; unbound VSUBS excluded explicitly.\n'+'\n'.join(r['line'] for r in added)+'\n'
    candidate=text.replace('.ends',addition+'.ends',1);assert candidate.replace(addition,'',1)==text
    return candidate,dict(status='prepared own-native R100 partial-C diagnostic',original_source_sha256=PARENT,
        canonical_candidate_sha256=SOURCE,diagnostic_source_sha256=hashlib.sha256(candidate.encode()).hexdigest(),
        private_source_proof=proof,view_manifest=view,raw_rows=rows,added=added,excluded=excluded,added_count=844,excluded_count=134,
        exact_inverse=True,all_raw_pairs_accounted=True,primitive_model_or_parameter_changes=True,
        declared_change='Only canonical main R62->100 versus b891; added partial C is distinct diagnostic hypothesis',
        full_MIM_pair_subtraction=False,delta_insertion=False,rz_length_um=100,
        own_native_capacitors=True,full_matrix_math=full,
        borrowed_field_scope=None,physical_field_acceptance='FAILED/unresolved MIM/tap/VSUBS/model attachment/fullchipfill')
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['source','view','extraction','zero-noise','zero-step','output']:p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();assert not a.output.exists();tests()
    for path,mode in [(a.zero_noise,'noise'),(a.zero_step,'step')]:
        proof=json.loads(path.read_text());assert proof['status']=='passed exact zero-C instrumentation control' and proof['mode']==mode
        assert proof['own_parameter_gate_exact'] and proof['own_OP_exact'] and proof['own_observations_exact'] and all(proof['saved_wave_exact'].values())
        contract=json.loads((path.parent/'contract.json').read_text());assert contract['source']['original_sha256']==SOURCE
    view=json.loads((a.view/'manifest.json').read_text());ex=json.loads((a.extraction/'summary.json').read_text())
    assert ex['status']=='passed raw native CC only; completefield FAILED' and ex['exact_source_node_mapping']=='passed' and ex['inputs_tools_cards_unchanged']
    assert sha(a.source)==view['source_sha256']==ex['source_sha256']==SOURCE
    assert ex['view_GDS_sha256']==view['GDS_sha256']
    caps=a.extraction/'exact_capacitances.json';assert sha(caps)==ex['capacitor_sha256']
    text,result=prepare(a.source.read_bytes(),view,json.loads(caps.read_text()))
    result.update(zero_noise_sha256=sha(a.zero_noise),zero_step_sha256=sha(a.zero_step),view_sha256=sha(a.view/'manifest.json'),
        extraction_sha256=sha(a.extraction/'summary.json'),raw_capacitors_sha256=sha(caps))
    a.output.mkdir(parents=True);(a.output/'candidate.spice').write_bytes(a.source.read_bytes());(a.output/'sense_partial_c.spice').write_text(text)
    (a.output/'source.py').write_bytes(Path(__file__).read_bytes());(a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
