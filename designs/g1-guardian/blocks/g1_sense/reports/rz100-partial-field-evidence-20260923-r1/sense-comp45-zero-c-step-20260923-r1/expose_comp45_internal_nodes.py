#!/usr/bin/env python3
"""Private diagnostic port exposure; preserve primitive paths and external ports."""
import argparse,collections,hashlib,json
from pathlib import Path

SOURCE='b8912a862b61554266239634dd388ed0ffad229c0b0e48819ad129d589352e97'
PRIMITIVES={'sg13_hv_nmos':4,'sg13_hv_pmos':4,'rppd':3,'cap_cmim':2}
def sha(raw):return hashlib.sha256(raw).hexdigest()

def parse(text):
    cells={};current=None
    for line in text.splitlines():
        w=line.split()
        if not w or w[0].startswith('*'):continue
        if w[0].lower()=='.subckt':
            assert current is None and w[1] not in cells
            current=w[1];cells[current]=dict(header=line,ports=w[2:],devices=[])
        elif w[0].lower()=='.ends':assert current;current=None
        else:
            assert current and w[0].startswith('X'),line
            first=next((i for i,t in enumerate(w) if '=' in t),len(w));model=w[first-1]
            cells[current]['devices'].append(dict(line=line,name=w[0],nodes=w[1:first-1],model=model,params=w[first:]))
    assert current is None
    return cells

def flatten(cells,aliases=None):
    aliases=aliases or {};rows=[]
    def walk(name,prefix,binding):
        for d in cells[name]['devices']:
            nodes=[binding.get(n,prefix+n) for n in d['nodes']]
            if d['model'] in cells:
                ports=cells[d['model']]['ports'];assert len(nodes)==len(ports)
                walk(d['model'],prefix+d['name']+'/',dict(zip(ports,nodes)))
            else:
                assert d['model'] in PRIMITIVES and len(nodes)==PRIMITIVES[d['model']]
                rows.append(dict(path=prefix+d['name'],model=d['model'],nodes=[aliases.get(n,n) for n in nodes],params=d['params']))
    walk('g1_sense','',dict((n,n) for n in cells['g1_sense']['ports']))
    return rows

def expose(raw):
    assert sha(raw)==SOURCE
    text=raw.decode();cells=parse(text);original=flatten(cells)
    assert len(original)==159 and collections.Counter(r['model'] for r in original)=={'rppd':98,'cap_cmim':3,'sg13_hv_nmos':25,'sg13_hv_pmos':33}
    edits=[];aliases={};mapping={};internals={}
    for name in ['g1_ota','g1_ota_main_candidate']:
        c=cells[name];nodes=sorted({n for d in c['devices'] for n in d['nodes']}-set(c['ports']))
        assert len(nodes)==11 and len(set(c['ports']+nodes))==17
        internals[name]=nodes;edits.append(dict(old=c['header'],new=c['header']+' '+' '.join(nodes)))
    for d in cells['g1_sense']['devices']:
        if d['model'] not in internals:continue
        assert d['name'] in ['XOTA','XBUF','XREF']
        extra=[]
        for n in internals[d['model']]:
            node='__pex_'+d['name'].lower()+'_'+n
            assert node not in aliases;aliases[node]=d['name']+'/'+n;mapping[d['name']+'/'+n]=node;extra.append(node)
        old=d['line'];new=' '.join([d['name']]+d['nodes']+extra+[d['model']]+d['params'])
        edits.append(dict(old=old,new=new))
    assert len(edits)==5 and len(aliases)==33
    for e in edits:assert text.count(e['old'])==1;text=text.replace(e['old'],e['new'])
    modified=parse(text);projected=flatten(modified,aliases)
    assert original==projected
    assert cells['g1_sense']['ports']==modified['g1_sense']['ports'] and len(cells['g1_sense']['ports'])==9
    source_nets={n for r in original for n in r['nodes']};assert len(source_nets)==134
    for n in source_nets:mapping.setdefault(n,n)
    assert len(mapping)==len(set(mapping.values()))==134
    restored=text
    for e in reversed(edits):assert restored.count(e['new'])==1;restored=restored.replace(e['new'],e['old'])
    assert restored.encode()==raw
    return text,dict(status='passed source-only private-node exposure',original_sha256=SOURCE,
        diagnostic_sha256=sha(text.encode()),exact_inverse=True,edits=edits,node_mapping=mapping,
        primitive_inventory=original,projected_inventory=projected,primitive_count=159,
        original_paths_and_params_exact=True,external_nine_ports_unchanged=True,
        source_net_count=134,private_ports_added=33,zero_C_electrical='not run',positive_C='not run',
        complete_field_coverage='failed/unresolved; no qualification by private instrumentation')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert not a.output.exists();text,report=expose(a.source.read_bytes())
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    (a.output/'sense_private_nodes.spice').write_text(text)
    (a.output/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['edits','node_mapping','primitive_inventory','projected_inventory']},indent=2))

if __name__=='__main__':main()
