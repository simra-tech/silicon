#!/usr/bin/env python3
"""Explicit authorized VSS body interface with independent flattened controls."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

TOP = 'PLACED_CORE_NOT_CONNECTED_FULLCHIP'
BODY = 'G1_EXPLICIT_SUBSTRATE_VSS'
SOURCE_SHA = 'f4ce6848bd7dd179d2ef4cbd8a4ea6bf9788bcfa1ff4b93fabae8bf18b6378f9'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def parse(raw):
    lines = raw.decode().splitlines(True)
    records = []
    for i, line in enumerate(lines):
        if line.lstrip().startswith('+'):
            assert records and records[-1]['indices'][-1] == i - 1
            records[-1]['tokens'].extend(line.lstrip()[1:].split())
            records[-1]['indices'].append(i)
        else:
            records.append(dict(indices=[i], tokens=line.split()))
    cells = {}; cell = None
    for rec in records:
        t = rec['tokens']
        if not t or t[0].startswith('*'): continue
        if t[0].upper() == '.SUBCKT':
            assert cell is None and t[1].upper() not in cells
            cell = dict(name=t[1], pins=t[2:], header=rec, instances=[])
            cells[t[1].upper()] = cell
        elif t[0].upper() == '.ENDS':
            cell['end']=rec; cell = None
        elif not t[0].startswith('.'):
            assert cell is not None, t
            assert t[0][0].upper() in 'XMRCDQ', t
            firstparam = next((j for j, v in enumerate(t) if '=' in v), len(t))
            mi = firstparam - 1
            nodes = [v for v in t[1:mi] if v != '/']
            substrate = [v.split('=',1)[1] for v in t if v.upper().startswith('$SUB=')]
            assert len(substrate) <= 1
            nodes.extend(substrate)
            annotation = [v[2:-1] for v in t if v.startswith('$[') and v.endswith(']')]
            assert len(annotation) <= 1
            model = annotation[0] if annotation else t[mi]
            params = [v for v in t[mi+1:] if not v.upper().startswith('$SUB=')]
            if annotation: params.append('CDL_LITERAL_VALUE=' + t[mi])
            cell['instances'].append(dict(record=rec, name=t[0], model=model,
                                          model_index=mi, nodes=nodes, params=params))
    return lines, cells


def flattened(cells):
    rows = {}; reached = set()
    top = cells[TOP]
    def walk(name, binding, path, stack):
        assert name not in stack
        c = cells[name]; reached.add(name)
        def node(n):
            n = n.upper()
            return binding[n] if n in binding else ('0' if n == '0' else path + '/' + n)
        for inst in c['instances']:
            nodes = [node(n) for n in inst['nodes']]
            child = inst['model'].upper()
            ipath = path + '/' + inst['name'].upper()
            if child in cells:
                pins = cells[child]['pins']; assert len(pins) == len(nodes), (ipath,pins,nodes)
                walk(child, dict(zip([p.upper() for p in pins],nodes)), ipath, stack+[name])
            else:
                assert ipath not in rows
                rows[ipath] = dict(model=child, nodes=nodes, params=inst['params'])
    walk(TOP, {p.upper():p.upper() for p in top['pins']}, TOP, [])
    return rows,reached


def valid(expected, observed):
    return expected == observed


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); assert not a.output.exists()
    raw=a.source.read_bytes(); assert sha(raw)==SOURCE_SHA
    assert BODY.encode() not in raw and not re.search(rb'^\s*\*?\.GLOBAL\b',raw,re.M|re.I)
    lines,cells=parse(raw); before,reached=flattened(cells)
    direct={n for n in reached if any(v.upper()=='SUB!' for i in cells[n]['instances'] for v in i['nodes'])}
    assert direct and all(n.startswith('SG13G2_') for n in direct)
    affected=set(direct)
    while True:
        new={n for n in reached if any(i['model'].upper() in affected for i in cells[n]['instances'])}
        if new <= affected: break
        affected |= new
    assert TOP in affected
    edits={}
    def change(rec, newtokens):
        # Keep unchanged records byte-identical; changed records may be folded.
        idx=rec['indices']; original=''.join(lines[k] for k in idx)
        replacement=' '.join(newtokens)+'\n'
        edits[idx[0]]=dict(indices=idx,original=original,replacement=replacement)
    for name in sorted(affected):
        c=cells[name]
        if name!=TOP:
            assert name.startswith('SG13G2_'),name
            header=list(c['header']['tokens']); header[1]='G1_VSS_DERIVATIVE__'+header[1]
            change(c['header'],header+[BODY])
        for inst in c['instances']:
            old=inst['record']['tokens']; t=list(old)
            for j in range(1,inst['model_index']):
                if t[j].upper()=='SUB!': t[j]=BODY if name!=TOP else 'VSS'
            for j in range(len(t)):
                if t[j].upper()=='$SUB=SUB!': t[j]='$SUB='+ (BODY if name!=TOP else 'VSS')
            if inst['model'].upper() in affected:
                mi=inst['model_index']; pos=mi-1 if t[mi-1]=='/' else mi
                t.insert(pos,BODY if name!=TOP else 'VSS')
                t[mi+1]='G1_VSS_DERIVATIVE__'+inst['model']
            if t!=old: change(inst['record'],t)
    # Keep the complete original library namespace byte-identical. Append
    # distinct design-local clones, and change only top calls into those clones.
    clone_blocks=[]
    for name in sorted(affected-{TOP}):
        cell=cells[name]; first=cell['header']['indices'][0]; last=cell['end']['indices'][-1]
        skipped={i for e in edits.values() for i in e['indices'][1:]}
        block=''.join(edits[i]['replacement'] if i in edits else lines[i]
                      for i in range(first,last+1) if i not in skipped)
        # Original .ENDS may name the cell explicitly.
        block=re.sub(r'(?im)^(\\.ENDS\\s+)'+re.escape(cell['name'])+r'(?=\\s|$)',
                     r'\\1G1_VSS_DERIVATIVE__'+cell['name'],block)
        clone_blocks.append(block)
    top_indices={i for inst in cells[TOP]['instances'] for i in inst['record']['indices']}
    edits={i:e for i,e in edits.items() if i in top_indices}
    clone_suffix=('\\n* BEGIN_EXPLICIT_VSS_DESIGN_LOCAL_DERIVATIVES\\n'+''.join(clone_blocks)).encode()
    removed={i for e in edits.values() for i in e['indices'][1:]}
    changed=''.join(edits[i]['replacement'] if i in edits else line
                    for i,line in enumerate(lines) if i not in removed).encode()
    changed+=clone_suffix
    # Exact inverse uses ordered original record spans, not netlist reserialization.
    spans=[]; cursor=0; output=[]
    for i,line in enumerate(lines):
        if i in removed: continue
        text=edits[i]['replacement'] if i in edits else line
        if i in edits: spans.append(dict(offset=cursor,old=edits[i]['original'],new=text))
        output.append(text); cursor+=len(text.encode())
    assert changed.endswith(clone_suffix)
    restored=changed[:-len(clone_suffix)]
    for e in reversed(spans):
        off=e['offset']; new=e['new'].encode()
        assert restored[off:off+len(new)]==new
        restored=restored[:off]+e['old'].encode()+restored[off+len(new):]
    assert restored==raw
    _,aftercells=parse(changed)
    # The pinned reader parses unused definitions too. Check the entire library,
    # not just the root-reachable circuit that the first preparation audited.
    for name,cell in aftercells.items():
        for inst in cell['instances']:
            child=inst['model'].upper()
            if child in aftercells:
                assert len(inst['nodes'])==len(aftercells[child]['pins']), (name,inst['name'],child)
    for name,cell in cells.items():
        if name==TOP: continue
        original_block=''.join(lines[cell['header']['indices'][0]:cell['end']['indices'][-1]+1]).encode()
        assert changed.count(original_block)==1, name
    after,_=flattened(aftercells)
    expected={k:dict(model=v['model'],params=v['params'],nodes=[
        'VSS' if n.endswith('/SUB!') else n for n in v['nodes']]) for k,v in before.items()}
    assert valid(expected,after)
    assert cells[TOP]['pins']==aftercells[TOP]['pins'] and len(cells[TOP]['pins'])==22
    tap=lambda rows:{k:v for k,v in rows.items() if v['model'] in ('PTAP1','NTAP1')}
    assert len(tap(before))==len(tap(after))==386
    assert all(v['nodes'][1]=='VSS' for v in tap(after).values() if v['model']=='PTAP1')
    changes=[dict(instance=k,terminal_index=j,original=n,derived=after[k]['nodes'][j])
             for k,v in before.items() for j,n in enumerate(v['nodes']) if n!=after[k]['nodes'][j]]
    assert len(changes)==941 and len({q['original'] for q in changes})==245
    tap_domains={v['nodes'][1] for v in tap(before).values() if v['model']=='PTAP1'}
    associated=[q for q in changes if q['original'] in tap_domains]
    other=[q for q in changes if q['original'] not in tap_domains]
    assert len(associated)==889 and len(tap_domains)==243
    assert len(other)==52 and len({q['original'] for q in other})==2
    assert all(before[q['instance']]['model']=='RPPD' and q['terminal_index']==2 for q in other)
    # Wrong domain, omitted primitive and altered parameters must each fail.
    first=changes[0]; wrong={k:dict(v,nodes=list(v['nodes'])) for k,v in after.items()}
    wrong[first['instance']]['nodes'][first['terminal_index']]='IOVSS'
    missing=dict(after); missing.pop(first['instance'])
    parameter={k:dict(v,params=list(v['params'])) for k,v in after.items()}
    parameter[first['instance']]['params'].append('G1_BAD_PARAMETER=1')
    controls=dict(positive=valid(expected,after),wrong_domain_rejected=not valid(expected,wrong),
                  omitted_device_rejected=not valid(expected,missing),
                  parameter_change_rejected=not valid(expected,parameter))
    assert all(controls.values())
    # Separate reader syntax view; no node/model/parameter mutation.
    prefix=[]; adapted=[]
    for line in changed.decode().splitlines(True):
        if re.match(r'^\s*X\S+\s+\S+\s+\S+\s+[pn]tap1\b',line,re.I):
            name=line.split()[0]; replacement='R_G1_TAP_SYNTAX_'+name
            prefix.append(dict(old=name,new=replacement))
            line=line.replace(name,replacement,1)
        adapted.append(line)
    adapted=''.join(adapted).encode(); reverse=adapted
    for row in prefix:
        reverse=reverse.replace((row['new']+' ').encode(),(row['old']+' ').encode())
    assert reverse==changed
    a.output.mkdir(parents=True)
    (a.output/'explicit_vss.cdl').write_bytes(changed)
    (a.output/'explicit_vss_tap_reader.cdl').write_bytes(adapted)
    (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    result=dict(status='passed authorized explicit VSS source derivative controls; LVS not run',
        source_sha256=sha(raw),explicit_sha256=sha(changed),adapter_sha256=sha(adapted),
        generator_sha256=sha(Path(__file__).read_bytes()),affected_cells=sorted(affected),
        directly_affected_cells=sorted(direct),reached_cells=len(reached),primitive_count=len(before),
        reachable_taps=386,original_body_nodes=245,ptap_associated_body_nodes=243,ptap_associated_incidences=889,resistor_only_body_nodes=2,resistor_only_incidences=52,changed_terminal_incidences=changes,
        exact_reverse_byte_restoration=True,external_pins_unchanged=cells[TOP]['pins'],
        flattened_exact_expected_partition=True,negative_controls=controls,
        original_library_definitions_byte_identical=True,all_library_call_signatures_checked=True,
        reversible_record_edits=spans,appended_clone_bytes=len(clone_suffix),appended_clone_sha256=sha(clone_suffix),
        namespaced_clones=['G1_VSS_DERIVATIVE__'+cells[n]['name'] for n in sorted(affected-{TOP})],tap_prefix_edits=prefix,
        canonical_source='unchanged',physical_LVS='not run',
        electrical_ESD_power_sequencing='not run',tap_AP_applicability='unresolved')
    (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in
        ('changed_terminal_incidences','reversible_record_edits','tap_prefix_edits')},indent=2))


if __name__=='__main__': main()


