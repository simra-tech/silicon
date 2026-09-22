#!/usr/bin/env python3
"""Independent saved-edge current/KCL/power audit and bottleneck ledger."""
import argparse
import collections
import gzip
import hashlib
import json
import math
from pathlib import Path
import numpy as np


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--result', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    summary = json.loads((args.result / 'summary.json').read_text())
    assert summary['status'] == 'passed conditional fixed-current metallic solve'
    raw = json.loads(gzip.decompress((args.result / 'raw_network.json.gz').read_bytes()))
    solution = json.loads((args.result / 'solution.json').read_text())
    voltage = np.load(str(args.result / 'node_voltages.npy'))
    order = {n['id']: i for i, n in enumerate(raw['nodes'])}
    nodes = {n['id']: n for n in raw['nodes']}
    parent = {n['id']: n['id'] for n in raw['nodes']}
    def find(node):
        while parent[node] != node:
            node = parent[node]
        return node
    for e in raw['edges']:
        assert math.isfinite(e['R_ohm']) and e['R_ohm'] >= 0
        if e['R_ohm'] == 0:
            parent[find(e['a'])] = find(e['b'])
    root_list = sorted({find(n) for n in nodes}, key=lambda n: order[n])
    root_index = {n: i for i, n in enumerate(root_list)}
    reduced = {n: root_index[find(n)] for n in nodes}
    assert len(voltage) == len(root_list) == solution['reduced_nodes']
    currents = collections.defaultdict(list)
    powers, edges = [], []
    for e in raw['edges']:
        a, b = reduced[e['a']], reduced[e['b']]
        delta = float(voltage[a] - voltage[b])
        if e['R_ohm'] == 0:
            assert a == b and delta == 0
            continue
        value = delta / e['R_ohm']
        currents[a].append(value)
        currents[b].append(-value)
        powers.append(delta * value)
        edges.append(dict(id=e['id'], a=e['a'], b=e['b'], resistance_ohm=e['R_ohm'],
            current_a_to_b_A=value, delta_a_to_b_V=delta, power_W=delta * value,
            layer_a=nodes[e['a']]['layer'], layer_b=nodes[e['b']]['layer'],
            location_a_um=nodes[e['a']]['location_um'], location_b_um=nodes[e['b']]['location_um']))
    injections = collections.defaultdict(list)
    source_power, reference_nodes, references = [], set(), []
    by_point = {p['id']: p for p in solution['points']}
    for point in solution['points']:
        node = raw['point_to_node'][str(point['id'])]
        r = reduced[node]
        assert r == point['reduced_node'] and node == point['extracted_node']
        assert float(voltage[r]) == point['delta_V']
        assert math.isclose(math.fsum(s['injection_A'] for s in point['sources']), point['injection_A'], rel_tol=0, abs_tol=1e-18)
        injections[r].append(point['injection_A'])
        source_power.append(point['injection_A'] * point['delta_V'])
    for ref in solution['references']:
        p = by_point[ref['reference_point']]
        reference_nodes.add(p['reduced_node'])
        assert p['delta_V'] == 0
        members = [q for q in solution['points'] if q['source_net'] == ref['source_net']]
        references.append(dict(ref, minimum_terminal_delta_V=min(q['delta_V'] for q in members),
            maximum_terminal_delta_V=max(q['delta_V'] for q in members),
            terminal_span_V=max(q['delta_V'] for q in members)-min(q['delta_V'] for q in members)))
    residual = [math.fsum(currents[i]) - math.fsum(injections[i]) for i in range(len(voltage))]
    maximum = max(abs(r) for i, r in enumerate(residual) if i not in reference_nodes)
    power, supplied = math.fsum(powers), math.fsum(source_power)
    assert maximum <= 1e-10
    assert abs(power-supplied) <= 1e-9 * max(abs(power), abs(supplied), 1e-12)
    # Independently associate every raw connected component with source nets.
    connectivity = {n: n for n in nodes}
    def component(node):
        while connectivity[node] != node:
            connectivity[node] = connectivity[connectivity[node]]
            node = connectivity[node]
        return node
    for e in raw['edges']:
        connectivity[component(e['a'])] = component(e['b'])
    owner = collections.defaultdict(set)
    for point in solution['points']:
        owner[component(point['extracted_node'])].add(point['source_net'])
    assert len(owner) == 55 and all(len(nets) == 1 for nets in owner.values())
    assert set(owner) == {component(n) for n in nodes}
    for edge in edges:
        edge['source_net'] = next(iter(owner[component(edge['a'])]))
    report = dict(status='passed independent saved-network numerical audit; physical IR not qualified',
        scenario=summary['scenario'], raw_nodes=len(nodes), raw_edges=len(raw['edges']),
        retained_zero_edges=sum(e['R_ohm'] == 0 for e in raw['edges']), represented_points=len(solution['points']),
        components=55, max_nonreference_KCL_residual_A=maximum, edge_power_W=power, source_power_W=supplied,
        power_absolute_difference_W=abs(power-supplied), net_references=references,
        largest_voltage_drop_edges=sorted(edges, key=lambda e: -abs(e['delta_a_to_b_V']))[:100],
        largest_power_edges=sorted(edges, key=lambda e: -e['power_W'])[:100],
        inputs={str(p): sha(p) for p in (args.result / 'summary.json', args.result / 'raw_network.json.gz',
                                        args.result / 'solution.json', args.result / 'node_voltages.npy', Path(__file__))},
        internal_model_substrate_electrode_planes='not qualified', source_insertion='not run', adoption='not run')
    assert not args.output.exists()
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ('net_references', 'largest_voltage_drop_edges', 'largest_power_edges', 'inputs')}, indent=2))


if __name__ == '__main__':
    main()
