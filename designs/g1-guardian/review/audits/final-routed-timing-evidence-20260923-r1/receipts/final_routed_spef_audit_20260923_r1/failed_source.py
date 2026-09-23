#!/usr/bin/env python3
"""Strict audit of stock OpenRCX routed-net coverage, graph and printed values."""
import argparse
from collections import Counter, defaultdict
from decimal import Decimal
import hashlib
import json
import math
from pathlib import Path
import re


def unescape(value):
    return re.sub(r'\\([.\[\]/])',r'\1',value)


def rounding_radius(value):
    x=Decimal(value)
    assert x.is_finite()
    return Decimal(5).scaleb(x.as_tuple().exponent-1)


def parse(text):
    names={}; nets={}; ports=[]; state='header'; current=None
    units={}
    def node(value):
        m=re.fullmatch(r'\*(\d+)(?::(.+))?',value)
        assert m and m[1] in names, value
        return (names[m[1]],unescape(m[2])) if m[2] else (names[m[1]],None)
    for raw in text.splitlines():
        line=raw.strip()
        if not line:continue
        fields=line.split()
        if line=='*NAME_MAP': state='names';continue
        if line=='*PORTS':state='ports';continue
        if fields[0]=='*D_NET':
            assert current is None and len(fields)==3
            name, suffix=node(fields[1]);assert suffix is None and name not in nets
            current=dict(name=name,total=fields[2],connections=[],caps=[],res=[])
            assert Decimal(fields[2]).is_finite() and Decimal(fields[2])>=0
            nets[name]=current;state='net';continue
        if line in ('*CONN','*CAP','*RES'):
            assert current is not None;state=line[1:].lower();continue
        if line=='*END':assert current is not None;current=None;state='between';continue
        if state=='header':
            if fields[0] in ('*C_UNIT','*R_UNIT','*T_UNIT'):
                assert fields[0] not in units;units[fields[0]]=fields[1:]
            continue
        if state=='names':
            assert len(fields)==2 and re.fullmatch(r'\*\d+',fields[0])
            key=fields[0][1:];assert key not in names
            names[key]=unescape(fields[1]);continue
        if state=='ports':
            assert len(fields)==2 and fields[1] in ('I','O','B')
            ports.append((unescape(fields[0]),fields[1]));continue
        if state=='conn':
            assert len(fields)==5 and fields[0]=='*I' and fields[2] in ('I','O','B') and fields[3]=='*D'
            terminal=node(fields[1]);assert terminal not in current['connections']
            current['connections'].append(terminal);continue
        if state in ('cap','res'):
            assert fields[0].isdigit()
            assert len(fields)==4 if state=='res' else len(fields) in (3,4)
            number=Decimal(fields[-1]);assert number.is_finite() and number>=0
            if state=='res': assert number>0
            values=[node(v)for v in fields[1:-1]]
            current['res' if state=='res' else 'caps'].append((int(fields[0]),values,fields[-1]));continue
        raise AssertionError((state,line))
    assert current is None and nets
    assert units=={'*T_UNIT':['1','NS'],'*C_UNIT':['1','PF'],'*R_UNIT':['1','OHM']}
    assert len(ports)==len(set(ports))
    return nets,ports


def audit(nets,inventory):
    expected={r['net']:{tuple(v)for v in r['endpoints']}for r in inventory['nets']if r['status']=='routed'}
    assert set(nets)==set(expected)
    couplings=defaultdict(list);rows=[];graphs={}
    for name,net in nets.items():
        assert set(net['connections'])==expected[name], name
        graph=defaultdict(set)
        for key in ('caps','res'):
            ids=[r[0]for r in net[key]];assert len(ids)==len(set(ids))
        for _,(a,b),value in net['res']:
            assert a!=b;graph[a].add(b);graph[b].add(a)
        assert graph and set(net['connections'])<=set(graph)
        seen={next(iter(graph))}; todo=list(seen)
        while todo:
            for adjacent in graph[todo.pop()]-seen:seen.add(adjacent);todo.append(adjacent)
        assert seen==set(graph),'Disconnected resistance graph: '+name
        graphs[name]=set(graph)
        total=Decimal(0);radius=rounding_radius(net['total'])
        for _,nodes,value in net['caps']:
            assert nodes[0] in graph
            total+=Decimal(value);radius+=rounding_radius(value)
            if len(nodes)==2:
                assert nodes[0]!=nodes[1]
                couplings[tuple(sorted(nodes))].append((name,value))
        delta=abs(total-Decimal(net['total']))
        assert delta<=radius,('Printed total inconsistent beyond rounding intervals',name,str(delta),str(radius))
        rows.append(dict(net=name,terminals=len(net['connections']),nodes=len(graph),
                         resistance_edges=len(net['res']),capacitance_rows=len(net['caps']),
                         total_C_pF=float(net['total']),printed_C_sum_residual_pF=float(delta),
                         printed_rounding_interval_pF=float(radius),
                         sum_edge_R_ohm=sum(float(r[2])for r in net['res'])))
    for pair,records in couplings.items():
        assert len(records)==2 and records[0][0]!=records[1][0],(pair,records)
        assert Decimal(records[0][1])==Decimal(records[1][1])
        assert pair[0] in graphs[records[0][0]]|graphs[records[1][0]]
        assert pair[1] in graphs[records[0][0]]|graphs[records[1][0]]
    return dict(status='passed routed SPEF numerical/coverage/graph audit',nets=rows,
                routed_net_count=len(rows),paired_coupling_count=len(couplings),
                interpretation='Sum of positive resistor edges is not an effective terminal-to-terminal resistance',
                rounding='Each printed decimal treated with half-last-place rounding interval; no physical acceptance tolerance changed')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('spef','inventory','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();assert not a.output.exists()
    net,ports=parse(a.spef.read_text());result=audit(net,json.loads(a.inventory.read_text()))
    result.update(input_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest()for p in (a.spef,a.inventory)},
        ports=ports,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        not_run=['Independent physical RC accuracy','Macro internal/fill/native extra metal extraction','Final STA and electrical acceptance'],
        not_applicable=['Stochastic seed for deterministic extraction'])
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items()if k not in ('nets','ports')},indent=2))


if __name__=='__main__':main()
