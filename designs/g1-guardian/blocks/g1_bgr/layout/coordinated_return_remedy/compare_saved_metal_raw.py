#!/usr/bin/env python3
"""Read-only exact numerical-network replay comparison after zero-edge unions."""
import argparse
import collections
import gzip
import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(path):
    raw=json.loads(gzip.decompress(path.read_bytes()))
    parent={n['id']:n['id'] for n in raw['nodes']}
    def find(n):
        while parent[n]!=n:
            parent[n]=parent[parent[n]];n=parent[n]
        return n
    for e in raw['edges']:
        if e['R_ohm']==0:parent[find(e['a'])]=find(e['b'])
    groups=collections.defaultdict(list)
    for n in raw['nodes']:
        groups[find(n['id'])].append(json.dumps({k:v for k,v in n.items() if k!='id'},sort_keys=True))
    signatures={r:tuple(sorted(v)) for r,v in groups.items()}
    assert len(set(signatures.values()))==len(signatures),'Ambiguous geometric zero-component signature'
    names={r:hashlib.sha256(json.dumps(v).encode()).hexdigest() for r,v in signatures.items()}
    edges=collections.defaultdict(list)
    for e in raw['edges']:
        a,b=names[find(e['a'])],names[find(e['b'])]
        if e['R_ohm']>0:edges[tuple(sorted((a,b)))].append(e['R_ohm'])
    return dict(nodes=collections.Counter(json.dumps({k:v for k,v in n.items() if k!='id'},sort_keys=True) for n in raw['nodes']),
        groups=collections.Counter(signatures.values()),edges={k:sorted(v) for k,v in edges.items()},
        ports={k:names[find(v)] for k,v in raw['point_to_node'].items()},
        raw_nodes=len(raw['nodes']),raw_edges=len(raw['edges']),zero_edges=sum(e['R_ohm']==0 for e in raw['edges']))


def main():
    ap=argparse.ArgumentParser()
    for name in ('first','second','output'):ap.add_argument('--'+name,type=Path,required=True)
    a=ap.parse_args();assert not a.output.exists()
    report=dict(status='running',inputs={str(p):sha(p) for p in (a.first,a.second,Path(__file__))})
    try:
        x,y=canonical(a.first),canonical(a.second)
        checks=dict(node_signature_multiset_exact=x['nodes']==y['nodes'],zero_group_signatures_exact=x['groups']==y['groups'],
            positive_edge_topology_exact={k:len(v) for k,v in x['edges'].items()}=={k:len(v) for k,v in y['edges'].items()},
            positive_resistance_binary64_exact=x['edges']==y['edges'],point_mapping_exact=x['ports']==y['ports'],
            raw_counts_exact=all(x[k]==y[k] for k in ('raw_nodes','raw_edges','zero_edges')))
        differences=[]
        if checks['positive_edge_topology_exact']:
            for key,values in x['edges'].items():
                for first,second in zip(values,y['edges'][key]):
                    if first!=second:differences.append(dict(first=first,second=second,absolute_ohm=abs(first-second),
                        relative=abs(first-second)/max(abs(first),abs(second))))
        report.update(status='passed exact zero-reduced numerical-network replay' if all(checks.values()) else 'failed exact replay',
            checks=checks,resistance_differences=len(differences),maximum_absolute_resistance_difference_ohm=max((d['absolute_ohm'] for d in differences),default=0),
            maximum_relative_resistance_difference=max((d['relative'] for d in differences),default=0),
            examples=sorted(differences,key=lambda d:-d['absolute_ohm'])[:20])
    except Exception as error:
        report.update(status='failed exact replay',error=repr(error))
    a.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
