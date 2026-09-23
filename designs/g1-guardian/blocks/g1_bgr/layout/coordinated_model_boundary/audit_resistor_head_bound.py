#!/usr/bin/env python3
"""Read-only saved nonlinear metal OP layer attribution; no network changes."""
import argparse
import collections
import gzip
import hashlib
import json
import math
from pathlib import Path


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    args.output.mkdir(exist_ok=False)
    base = Path(__file__).resolve().parent / 'evidence/external-pins-20260923-r1'
    results = {}
    for case in ('kpex', 'lef'):
        paths = [base / 'network' / case / 'result/raw_network.json.gz',
                 base / 'source_preparation' / case / 'positive_edges.json',
                 base / 'source_preparation' / case / 'point_nodes.json',
                 base / case / 'metal_node_voltages.json',
                 base / case / 'conditional_analysis.json']
        inputs = {str(p.relative_to(base)): sha(p) for p in paths}
        raw = json.loads(gzip.decompress(paths[0].read_bytes()).decode())
        edges, points, voltage, prior = [json.loads(p.read_text()) for p in paths[1:]]
        nodes = {n['id']: n for n in raw['nodes']}
        assert {n['layer'] for n in nodes.values()} <= set(range(5))
        original = {e['id']: e for e in raw['edges'] if e['R_ohm'] > 0}
        assert len(edges) == len(original) == 42615
        assert {e['raw_edge_id'] for e in edges} == set(original)
        parent = {name: name for name in voltage}

        def find(a):
            while parent[a] != a:
                parent[a] = parent[parent[a]]
                a = parent[a]
            return a

        for e in edges:
            parent[find(e['a'])] = find(e['b'])
        owners = collections.defaultdict(set)
        for p in points:
            owners[find(p['node'])].add(p['source_net'])
        assert len(owners) == 55 and all(len(v) == 1 for v in owners.values())
        assert set(owners) == {find(n) for n in voltage}
        grouped = collections.defaultdict(list)
        all_rows = []
        for e in edges:
            orig = original[e['raw_edge_id']]
            assert orig['R_ohm'] == e['R_ohm'] > 0
            a, b = nodes[orig['a']], nodes[orig['b']]
            # M1 layer index is 0. ALL M1-touching edges are conservatively
            # included, not just resistor heads. Other layers cannot be M1
            # head sheet elements. No endpoint-only spatial cut is inferred.
            bucket = 'all_M1_touching_upper_bucket' if 0 in (a['layer'], b['layer']) else 'outside_M1_heads_by_layer'
            dv = voltage[e['a']] - voltage[e['b']]
            power = dv * dv / e['R_ohm']
            assert math.isfinite(power) and power >= 0
            net = next(iter(owners[find(e['a'])]))
            row = dict(raw_edge_id=e['raw_edge_id'], source_net=net,
                       bucket=bucket, R_ohm=e['R_ohm'], delta_V=dv,
                       current_A=dv/e['R_ohm'], power_W=power,
                       endpoint_layers=[a['layer'], b['layer']],
                       endpoint_locations_um=[a['location_um'], b['location_um']])
            grouped[(net, bucket)].append(row)
            all_rows.append(row)
        total = math.fsum(r['power_W'] for r in all_rows)
        assert math.isclose(total, prior['total_metal_power_W'], rel_tol=1e-13)
        totals = {bucket: math.fsum(r['power_W'] for r in all_rows if r['bucket'] == bucket)
                  for bucket in ('all_M1_touching_upper_bucket', 'outside_M1_heads_by_layer')}
        results[case] = dict(total_power_W=total, power_by_bucket_W=totals,
            fraction_by_bucket={k: v/total for k, v in totals.items()},
            per_net_bucket=sorted([dict(source_net=n, bucket=b, edges=len(rows),
                power_W=math.fsum(r['power_W'] for r in rows),
                maximum_edge_delta_V=max(abs(r['delta_V']) for r in rows))
                for (n, b), rows in grouped.items()], key=lambda r: r['power_W'], reverse=True),
            largest_30_outside_head_edges=sorted([r for r in all_rows if r['bucket'] == 'outside_M1_heads_by_layer'],
                key=lambda r: abs(r['delta_V']), reverse=True)[:30], inputs=inputs)
        assert inputs == {str(p.relative_to(base)): sha(p) for p in paths}
    report = dict(status='passed read-only layer attribution of conditional saved nonlinear OP',
        model_ownership='failed to establish calibrated lateral M1 boundary',
        limitation='Power fraction is NOT VREF sensitivity or an upper bound on VREF error. All M1-touching edges include non-resistor routing and Via1. No support polygon inferred from endpoints.',
        new_simulation='not run', network_or_model_changes='not applicable',
        worker_sha256=sha(Path(__file__)), cases=results)
    (args.output / 'analysis.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    print(json.dumps({k: {'total_power_W': v['total_power_W'], 'fraction_by_bucket': v['fraction_by_bucket'], 'top': v['per_net_bucket'][:6]} for k,v in results.items()}, indent=2))


if __name__ == '__main__':
    main()
