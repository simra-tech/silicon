#!/usr/bin/env python3
"""Read-only source ownership of the held supply-candidate positive network."""
import argparse
import collections
import gzip
import hashlib
import json
import math
import os
from pathlib import Path


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists() and set(os.sched_getaffinity(0)) == {2}
    bulk = Path(os.environ['G1_RESULTS_ROOT'])
    prep = bulk / 'bgr-supply-fixture-20260923-r1/kpex'
    run = bulk / 'bgr-supply-kpex-20260923-r1'
    paths = [bulk / 'bgr-metal-r-supply-kpex-20260923-r2/result/raw_network.json.gz',
             prep / 'positive_edges.json', prep / 'point_nodes.json',
             run / 'metal_node_voltages.json', run / 'conditional_analysis.json',
             Path(__file__).resolve()]
    hashes = {str(p): sha(p) for p in paths}
    raw = json.loads(gzip.decompress(paths[0].read_bytes()))
    edges, points, voltages, prior = [json.loads(p.read_text()) for p in paths[1:5]]
    assert (len(edges), len(points), len(voltages)) == (42640, 3355, 33420)
    nodes = {n['id']: n for n in raw['nodes']}
    originals = {e['id']: e for e in raw['edges'] if e['R_ohm'] > 0}
    assert set(originals) == {e['raw_edge_id'] for e in edges}
    parents = {n: n for n in voltages}

    def find(n):
        while parents[n] != n:
            parents[n] = parents[parents[n]]
            n = parents[n]
        return n

    for e in edges:
        parents[find(e['a'])] = find(e['b'])
    owners = collections.defaultdict(set)
    for pt in points:
        owners[find(pt['node'])].add(pt['source_net'])
    assert len(owners) == 55 and all(len(n) == 1 for n in owners.values())
    assert set(owners) == {find(n) for n in voltages}
    rows = collections.defaultdict(list)
    for e in edges:
        original = originals[e['raw_edge_id']]
        assert original['R_ohm'] == e['R_ohm'] > 0
        ends = [nodes[original[t]] for t in ('a', 'b')]
        dv = voltages[e['a']] - voltages[e['b']]
        net = next(iter(owners[find(e['a'])]))
        rows[net].append(dict(resistor=e['resistor'], raw_edge_id=e['raw_edge_id'],
            R_ohm=e['R_ohm'], delta_V=dv, current_A=dv/e['R_ohm'],
            power_W=dv*dv/e['R_ohm'],
            endpoint_layers=[n['layer'] for n in ends],
            endpoint_locations_um=[n['location_um'] for n in ends]))
    power = math.fsum(e['power_W'] for group in rows.values() for e in group)
    assert math.isclose(power, prior['total_metal_power_W'], rel_tol=1e-13)
    result = dict(status='passed', inputs=hashes, positive_edges=len(edges),
        nodes=len(voltages), source_nets=55, points=len(points), total_power_W=power,
        per_net={net: dict(edges=len(group), total_power_W=math.fsum(e['power_W'] for e in group),
            largest_20_edges=sorted(group, key=lambda e: abs(e['delta_V']), reverse=True)[:20])
            for net, group in rows.items()},
        limitation='Endpoint locations are not complete edge support polygons or a VREF sensitivity proof.',
        new_simulation='not run', geometry_remedy='not run', model_changes='not applicable')
    assert all(sha(Path(p)) == h for p, h in hashes.items())
    a.output.mkdir(parents=True)
    (a.output / 'source.py').write_bytes(Path(__file__).read_bytes())
    (a.output / 'analysis.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps({n: result['per_net'][n]['largest_20_edges'][:3]
                     for n in ('vdd', 'vss', 'dvbe', 'vb2', 'pbias', 'pcasc')}, indent=2))


if __name__ == '__main__':
    main()
