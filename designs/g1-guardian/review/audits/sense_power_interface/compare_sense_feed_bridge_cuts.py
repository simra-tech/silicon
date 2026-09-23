#!/usr/bin/env python3
"""Compare actual bridge cuts separating all device S contacts from a port witness."""
import argparse
from bisect import bisect_left, bisect_right
import collections
import gzip
import json
import os
from pathlib import Path
from bound_sense_metal_rails import Union, sha, dump, rational
from rail_resistance_bound_math import graph_bounds

FEEDS = [('XOTA/XM14', 'vdd', 575), ('XOTA/XM11', 'vdd', 575),
         ('XOTA/XM4', 'vss', 483), ('XOTA/XM3', 'vss', 483)]


def separates_all(positions, port_index, interval):
    assert positions and positions == sorted(positions)
    lo, hi = interval
    inside = bisect_right(positions, hi)-bisect_left(positions, lo)
    return ((inside == len(positions) and not lo <= port_index <= hi)
            or (inside == 0 and lo <= port_index <= hi))


def inspect(folder):
    m = json.loads((folder/'summary.json').read_text())
    assert m['status'] == 'passed geometry-only all-contact metal-R topology'
    assert sha(folder/'topology.json') == m['topology_sha256']
    assert sha(folder/'raw_network.json.gz') == m['raw_network_sha256']
    audit = json.loads((folder/'topology.json').read_text())
    raw = json.loads(gzip.decompress((folder/'raw_network.json.gz').read_bytes()))
    positive = json.loads(gzip.decompress((folder/'positive_edges.json.gz').read_bytes()))
    index = {r['id']: i for i, r in enumerate(raw['nodes'])}; zero = Union(len(index))
    for e in raw['edges']:
        if e['R_ohm'] == 0: zero.join(index[e['a']], index[e['b']])
    roots = sorted({zero.find(i) for i in range(len(index))}); compact = {r: i for i, r in enumerate(roots)}
    reduced = {key: compact[zero.find(value)] for key, value in index.items()}
    connected = Union(len(roots)); groups = collections.defaultdict(list)
    nodes = {r['id']: r for r in raw['nodes']}; rebuilt = []
    for e in raw['edges']:
        a, b = reduced[e['a']], reduced[e['b']]
        if e['R_ohm'] == 0 or a == b: continue
        rebuilt.append(dict(a=a, b=b, R_ohm=e['R_ohm'])); connected.join(a, b)
        groups[tuple(sorted((a,b)))].append(dict(R_ohm=e['R_ohm'], endpoints=[nodes[e['a']], nodes[e['b']]]))
    assert rebuilt == positive
    results = {}
    for rail in ('vdd', 'vss'):
        obs = [r for r in audit['observations'] if r['source_net'] == rail]
        components = {connected.find(r['reduced_node']) for r in obs}; assert len(components) == 1
        component = next(iter(components))
        vertices = [n for n in range(len(roots)) if connected.find(n) == component]
        edges = [(e['a'],e['b'],e['R_ohm']) for e in positive if connected.find(e['a']) == component]
        bound = graph_bounds(vertices, edges)
        port = [r for r in obs if r.get('device') == 'PORT' and r['terminal'] == rail]; assert len(port) == 1
        port_index = bound['node_discovery'][port[0]['reduced_node']]
        for name, net, count in FEEDS:
            if net != rail: continue
            source = [r for r in obs if any(q['device'] == name and q['terminal'] == 'S' for q in r.get('owners', []))]
            assert len(source) == count
            positions = sorted(bound['node_discovery'][r['reduced_node']] for r in source)
            cuts = []
            for bridge in bound['bridges']:
                if separates_all(positions, port_index, bridge['descendant_discovery_interval']):
                    cuts.append(dict(resistance_ohm=rational(bridge['resistance']), native_edges=groups[bridge['nodes']]))
            assert cuts
            cuts.sort(key=lambda r: r['resistance_ohm']['display_ohm'], reverse=True)
            results[name] = dict(source_contact_count=count, rail=rail, separating_bridge_count=len(cuts),
                leading_actual_cuts=cuts[:8], port_scope='Existing source-owned witness only, not equipotential pin attachment')
    return dict(GDS_sha256=m['GDS_sha256'], source_sha256=m['source_sha256'],
                topology_summary_sha256=sha(folder/'summary.json'), feeds=results)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('before','after','output'): p.add_argument('--'+key, type=Path, required=True)
    a = p.parse_args(); assert not a.output.exists() and len(os.sched_getaffinity(0)) == 1
    before, after = inspect(a.before), inspect(a.after)
    assert before['source_sha256'] == after['source_sha256']
    result = dict(status='passed exact source-contact separating-cut comparison', before=before, after=after,
        script_sha256=sha(Path(__file__)), scope='Actual graph bridges only; no currents, model weights, IR or physical acceptance',
        not_run=['Complete current budget', 'External feed attachment', 'Model composition and electrical parity', 'Adoption'])
    dump(a.output, result); print(json.dumps({k:v for k,v in result.items() if k not in ('before','after')}, indent=2))


if __name__ == '__main__': main()
