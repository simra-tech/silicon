#!/usr/bin/env python3
"""Two source-only RZ remedies with borrowed, explicitly incomplete r9 C."""
import argparse,hashlib,json
from pathlib import Path
from expose_comp45_internal_nodes import SOURCE,expose,parse,flatten

OLD='XRZ out1 cz vss rppd w=1u l=62u m=1 b=0 mm_ok=1'
PARTIAL='be01749553a1780ef2fb3dd6bcfb4e8465a38fa855374996ff085b06f26ff800'
def digest(raw):return hashlib.sha256(raw).hexdigest()
def change(text,length):
    assert length in (80,100) and text.count(OLD)==1
    new=OLD.replace('l=62u',f'l={length}u');out=text.replace(OLD,new)
    assert out.replace(new,OLD)==text
    return out

def prepare(raw,partial,packet,length):
    assert digest(raw)==SOURCE and digest(partial)==PARTIAL
    assert packet['diagnostic_source_sha256']==PARTIAL and packet['exact_inverse']
    assert packet['added_count']==844 and packet['excluded_count']==134
    canonical=change(raw.decode(),length);derived=change(partial.decode(),length)
    before=flatten(parse(raw.decode()));after=flatten(parse(canonical))
    changes=[dict(before=x,after=y) for x,y in zip(before,after) if x!=y]
    assert len(before)==len(after)==159 and len(changes)==1
    x,y=changes[0]['before'],changes[0]['after']
    assert x['path']==y['path']=='XOTA/XRZ' and x['nodes']==y['nodes'] and x['model']==y['model']=='rppd'
    assert [p.replace('l=62u',f'l={length}u') for p in x['params']]==y['params']
    exposed,proof=expose(raw);exposed=change(exposed,length)
    aliases={v:k for k,v in proof['node_mapping'].items()}
    assert flatten(parse(exposed),aliases)==after
    caps=[r['line'] for r in packet['added']]
    assert len(caps)==844 and all(derived.count(c)==1 for c in caps)
    recovered=derived.replace('* Explicitly incomplete source-net-pair field sensitivity; VSUBS unbound.\n'+'\n'.join(caps)+'\n','',1)
    assert recovered==exposed
    assert parse(canonical)['g1_sense']['ports']==parse(raw.decode())['g1_sense']['ports']
    result=dict(packet)
    result.update(status='prepared isolated RZ remedy with borrowed partial-C diagnostic',
        original_source_sha256=SOURCE,canonical_candidate_sha256=digest(canonical.encode()),
        diagnostic_source_sha256=digest(derived.encode()),parent_partial_sha256=PARTIAL,
        primitive_model_or_parameter_changes=True,declared_geometry_changes=changes,rz_length_um=length,
        exact_inverse=True,borrowed_capacitors_byte_exact=True,
        borrowed_field_scope='844 r9 RZ62 net-pair capacitors unchanged; NOT RZ candidate-specific PEX; 134 VSUBS pairs omitted explicitly',
        own_source_zero_C_wave_control='not run; prior b891 adapter method control does not qualify this changed circuit',
        native_candidate='not run',population_transfer='not permitted',source_net_count=134,
        physical_field_acceptance='failed/unresolved')
    return canonical,derived,result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['source','packet','output']:p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--length',type=int,choices=[80,100],required=True);a=p.parse_args();assert not a.output.exists()
    packet=json.loads((a.packet/'summary.json').read_text())
    canonical,derived,result=prepare(a.source.read_bytes(),(a.packet/'sense_partial_c.spice').read_bytes(),packet,a.length)
    a.output.mkdir(parents=True)
    (a.output/'candidate.spice').write_text(canonical);(a.output/'sense_partial_c.spice').write_text(derived)
    (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['status','canonical_candidate_sha256','diagnostic_source_sha256','rz_length_um']},indent=2))
if __name__=='__main__':main()
