#!/usr/bin/env python3
"""Extraction-only three-dummy projection; original/source/native stay intact."""
import argparse
import hashlib
import json
from pathlib import Path
from prepare_r5 import parse, flattened, TOP


def sha(data): return hashlib.sha256(data).hexdigest()


def allowed(removed):
    # This independent literal parser retains X instance prefixes. The prior
    # physical proof strips them for the KLayout-expanded occurrence names.
    paths={TOP+'/X'+pad+'/XI0/MP0' for pad in ('PAD12_EN','PAD14_SCLK','PAD15_SDI')}
    return (set(removed)==paths and all(v['model']=='SG13_HV_PMOS'
        and v['nodes']==['VDD']*4 for v in removed.values()))


def main():
    p=argparse.ArgumentParser()
    for name in ('preparation','native-proof','output'): p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args(); assert not a.output.exists()
    report=json.loads((a.preparation/'summary.json').read_text())
    proof=json.loads(a.native_proof.read_text())
    assert report['original_library_definitions_byte_identical'] and report['all_library_call_signatures_checked']
    assert proof['status']=='passed independent three-dummy source/native-terminal proof'
    assert 'ae62bf68aa001144c08a37c58ac3553c6e5f2013a6824b340218e84962066aca' in proof['inputs'].values()
    assert 'target_netlist.purge_devices' in proof['unconditional_purge_rule']
    assert len(proof['source_occurrences'])==len(proof['physical_instances'])==3
    assert {v['path'] for v in proof['source_occurrences']}=={
        'PAD12_EN.I0.MP0','PAD14_SCLK.I0.MP0','PAD15_SDI.I0.MP0'}
    source=a.preparation/'explicit_vss_tap_reader.cdl'; raw=source.read_bytes()
    assert sha(raw)==report['adapter_sha256']
    lines,cells=parse(raw); before,_=flattened(cells)
    cell=cells['G1_VSS_DERIVATIVE__SG13G2_LEVELDOWN']
    inst,=[i for i in cell['instances'] if i['name'].upper()=='MP0']
    assert inst['model'].lower()=='sg13_hv_pmos' and [n.upper() for n in inst['nodes']]==['VDD']*4
    assert inst['params']==['m=1','w=4.65u','l=450.00n','ng=1']
    indices=inst['record']['indices']; assert len(indices)==1
    line=lines[indices[0]].encode(); offset=sum(len(x.encode()) for x in lines[:indices[0]])
    changed=raw[:offset]+raw[offset+len(line):]
    assert changed[:offset]+line+changed[offset:]==raw
    _,aftercells=parse(changed); after,_=flattened(aftercells)
    assert set(after)<set(before)
    removed={k:before[k] for k in set(before)-set(after)}
    assert allowed(removed) and all(after[k]==before[k] for k in after)
    # These are topology/selection negative controls, not parameter waivers.
    wrong={k:dict(v,nodes=list(v['nodes'])) for k,v in removed.items()}
    first=sorted(wrong)[0]; wrong[first]['nodes'][3]='IOVDD'
    missing=dict(removed); missing.pop(first)
    extra=dict(removed); extra['OTHER_UNAUTHORIZED_DEVICE']=removed[first]
    checks=dict(exact_three_all_VDD=allowed(removed),wrong_body_rejected=not allowed(wrong),
                missing_occurrence_rejected=not allowed(missing),extra_device_rejected=not allowed(extra))
    assert all(checks.values())
    a.output.mkdir(parents=True)
    dest=a.output/'explicit_vss_three_dummy_extraction_only.cdl'; dest.write_bytes(changed)
    result=dict(status='passed reversible three-dummy extraction-reference preparation; comparison not run',
        source_sha256=sha(raw),output_sha256=sha(changed),native_proof_sha256=sha(a.native_proof.read_bytes()),
        original_preparation_sha256=sha((a.preparation/'summary.json').read_bytes()),
        script_sha256=sha(Path(__file__).read_bytes()),parser_sha256=sha(Path(__file__).with_name('prepare_r5.py').read_bytes()),
        removed_record=line.decode(),byte_offset=offset,source_occurrences=removed,
        all_other_primitives_and_terminal_bindings_exact=True,reverse_byte_restoration=True,
        negative_controls=checks,full_original_library_definition='retained byte-identical',
        physical_devices='all retained; same four-terminal native proof',
        electrical_source='full owner-authorized explicit source retained; this is comparison-only',
        changed_models_rules_AP='not applicable; none',strict_LVS='not run in this arm',
        power_sequencing_ESD='not run')
    (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps(result,indent=2))


if __name__=='__main__': main()
