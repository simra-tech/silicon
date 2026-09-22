#!/usr/bin/env python3
"""Native KLayout metallic R extraction and fixed-current sparse diagnostic."""
import argparse
import collections
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import time
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve
import klayout.db as kdb
import klayout.pex as klp
import klayout.pexcore as core

PAIRS = {'M1': (8, 0), 'M2': (10, 0), 'M3': (30, 0), 'M4': (50, 0), 'M5': (67, 0),
         'Via1': (19, 0), 'Via2': (29, 0), 'Via3': (49, 0), 'Via4': (66, 0)}
CUTS = {'Via1': ('M1', 'M2'), 'Via2': ('M2', 'M3'), 'Via3': ('M3', 'M4'), 'Via4': ('M4', 'M5')}
IDS = {name: i for i, name in enumerate(PAIRS)}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def technology(scenario):
    tech = klp.RExtractorTech()
    tech.skip_simplify = True
    for name, resistance in scenario['sheet_ohm'].items():
        c = klp.RExtractorTechConductor()
        c.layer = IDS[name]
        c.algorithm = klp.Algorithm.SquareCounting
        c.triangulation_min_b = .5
        c.triangulation_max_area = 50.
        c.resistance = resistance
        tech.add_conductor(c)
    for name, resistance in scenario['cut_ohm'].items():
        v = klp.RExtractorTechVia()
        v.cut_layer = IDS[name]
        v.bottom_conductor = IDS[CUTS[name][0]]
        v.top_conductor = IDS[CUTS[name][1]]
        # Actual cut dimensions were checked for every saved GDS via polygon.
        # Native API consumes ohm*um^2, equivalent to per-cut R times cut area.
        v.resistance = resistance * .19 * .19
        v.merge_distance = 0.
        tech.add_via(v)
    return tech


def extract(regions, points, scenario, polygons=None):
    vertex = collections.defaultdict(list)
    mapping = {}
    for point in points:
        layer = IDS[point['layer']]
        mapping[(layer, len(vertex[layer]))] = point['id']
        vertex[layer].append(kdb.Point(*point['point_dbu']))
    polygon_mapping, polygon_ports = {}, collections.defaultdict(list)
    for row in polygons or []:
        layer = IDS[row['layer']]
        polygon_mapping[(layer, len(polygon_ports[layer]))] = row['id']
        polygon_ports[layer].append(kdb.Polygon(kdb.Box(*row['box_dbu'])))
    network = klp.RNetExtractor(.001).extract(technology(scenario), regions, dict(vertex), dict(polygon_ports))
    nodes, terminals = [], {}
    for node in network.each_node():
        identifier = int(node.object_id())
        kind = node.type()
        loc = node.location()
        row = dict(id=identifier, layer=int(node.layer()), kind=str(kind),
                   location_um=[loc.p1.x, loc.p1.y, loc.p2.x, loc.p2.y])
        if kind == klp.RNodeType.VertexPort:
            port = mapping[(node.layer(), node.port_index())]
            assert port not in terminals
            terminals[port] = identifier
            row['point_id'] = port
        elif kind == klp.RNodeType.PolygonPort:
            port = polygon_mapping[(node.layer(), node.port_index())]
            assert port not in terminals
            terminals[port] = identifier
            row['point_id'] = port
        nodes.append(row)
    assert set(terminals) == {p['id'] for p in points + (polygons or [])}
    edges = []
    for edge in network.each_element():
        value = float(edge.resistance())
        assert math.isfinite(value) and value >= 0
        edges.append(dict(id=int(edge.object_id()), a=int(edge.a().object_id()), b=int(edge.b().object_id()), R_ohm=value))
    assert nodes and edges
    return dict(nodes=nodes, edges=edges, point_to_node=terminals)


class Union:
    def __init__(self, n):
        self.parent = list(range(n))

    def find(self, a):
        while self.parent[a] != a:
            self.parent[a] = self.parent[self.parent[a]]
            a = self.parent[a]
        return a

    def join(self, a, b):
        a, b = self.find(a), self.find(b)
        self.parent[a] = b


def solve(raw, points, expected_components):
    index = {n['id']: i for i, n in enumerate(raw['nodes'])}
    zero = Union(len(index))
    for edge in raw['edges']:
        if edge['R_ohm'] == 0:
            zero.join(index[edge['a']], index[edge['b']])
    roots = sorted({zero.find(i) for i in range(len(index))})
    compact = {r: i for i, r in enumerate(roots)}
    reduced = {identifier: compact[zero.find(i)] for identifier, i in index.items()}
    n = len(roots)
    components = Union(n)
    row, col, data, positive = [], [], [], []
    for edge in raw['edges']:
        a, b = reduced[edge['a']], reduced[edge['b']]
        if edge['R_ohm'] == 0 or a == b:
            continue
        components.join(a, b)
        g = 1 / edge['R_ohm']
        row += [a, a, b, b]
        col += [a, b, b, a]
        data += [g, -g, -g, g]
        positive.append((a, b, edge['R_ohm']))
    matrix = coo_matrix((data, (row, col)), shape=(n, n)).tocsc()
    point_nodes = {p['id']: reduced[raw['point_to_node'][p['id']]] for p in points}
    grouped = collections.defaultdict(list)
    for point in points:
        grouped[components.find(point_nodes[point['id']])].append(point)
    assert len(grouped) == expected_components
    assert set(grouped) == {components.find(i) for i in range(n)}, 'Floating extracted component without a source-bound port'
    rhs = np.zeros(n)
    for point in points:
        rhs[point_nodes[point['id']]] += point['injection_A']
    references, ownership = [], []
    for members in grouped.values():
        nets = {p['source_net'] for p in members}
        assert len(nets) == 1, nets
        ports = [p for p in members if p.get('reference_ports')]
        assert len(ports) <= 1
        reference = ports[0] if ports else min(members, key=lambda p: p['id'])
        node = point_nodes[reference['id']]
        references.append(node)
        ownership.append(dict(source_net=next(iter(nets)), point_count=len(members), reference_point=reference['id'],
            reference_kind='actual macro pin' if ports else 'arbitrary internal-net offset',
            net_injection_A=sum(p['injection_A'] for p in members)))
    free = np.array([i for i in range(n) if i not in set(references)], dtype=int)
    voltage = np.zeros(n)
    voltage[free] = spsolve(matrix[free][:, free], rhs[free])
    assert np.all(np.isfinite(voltage))
    residual = matrix @ voltage - rhs
    max_error = float(np.max(np.abs(residual[free])))
    assert max_error <= 1e-10, max_error  # numerical KCL gate, not a physical acceptance limit
    power = sum((voltage[a] - voltage[b]) ** 2 / r for a, b, r in positive)
    supplied = float(voltage @ rhs)
    assert abs(power - supplied) <= 1e-9 * max(abs(power), abs(supplied), 1e-12), dict(
        power_W=power, source_power_W=supplied, absolute_delta_W=abs(power-supplied),
        free_KCL_residual_A=max_error, nodes=n, positive_edges=len(positive))
    result_points = [dict(p, extracted_node=raw['point_to_node'][p['id']], reduced_node=point_nodes[p['id']],
                          delta_V=float(voltage[point_nodes[p['id']]])) for p in points]
    return dict(status='passed conditional fixed-current metallic solve', raw_nodes=len(index), reduced_nodes=n,
        raw_edges=len(raw['edges']), zero_edges=sum(e['R_ohm'] == 0 for e in raw['edges']),
        components=expected_components, references=ownership, points=result_points,
        max_free_node_KCL_residual_A=max_error, numerical_KCL_gate_A=1e-10,
        reference_balance_A=[float(residual[i]) for i in references], power_W=float(power), source_power_W=supplied,
        maximum_absolute_delta_V=float(np.max(np.abs(voltage)))), voltage


def controls(scenario, output):
    cases = []
    regions = {IDS['M1']: kdb.Region(kdb.Box(0, 0, 10000, 1000))}
    ports = [dict(id=0, layer='M1', box_dbu=[0, 0, 1000, 1000], injection_A=.001, source_net='coupon', reference_ports=['a']),
             dict(id=1, layer='M1', box_dbu=[9000, 0, 10000, 1000], injection_A=-.001, source_net='coupon', reference_ports=[])]
    raw = extract(regions, [], scenario, ports)
    dump(output / 'rectangle_raw.json', raw)
    result, _ = solve(raw, ports, 1)
    actual = abs(result['points'][1]['delta_V']) / .001
    expected = 8 * scenario['sheet_ohm']['M1']
    cases.append(dict(name='rectangle_8_squares_between_equipotential_end_regions', actual_ohm=actual, expected_ohm=expected,
                      passed=abs(actual - expected) <= 1e-8, raw=raw, solution=result))
    for count in (1, 2):
        pad = kdb.Box(-1000, -1000, 1000, 1000)
        regions = {IDS['M1']: kdb.Region(pad), IDS['M2']: kdb.Region(pad), IDS['Via1']: kdb.Region()}
        for dx in ([0] if count == 1 else [-210, 210]):
            regions[IDS['Via1']].insert(kdb.Box(dx - 95, -95, dx + 95, 95))
        ports = [dict(id=i, layer=layer, box_dbu=[-1000, -1000, 1000, 1000], injection_A=.001 if i == 0 else -.001,
                      source_net='coupon', reference_ports=['a'] if i == 0 else []) for i, layer in enumerate(('M1', 'M2'))]
        raw = extract(regions, [], scenario, ports)
        dump(output / ('via_' + str(count) + '_raw.json'), raw)
        result, _ = solve(raw, ports, 1)
        actual = abs(result['points'][1]['delta_V']) / .001
        expected = scenario['cut_ohm']['Via1'] / count
        cases.append(dict(name='parallel_via_' + str(count), actual_ohm=actual, expected_ohm=expected,
                          passed=abs(actual - expected) <= 1e-8, raw=raw, solution=result))
    return cases


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--preparation', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--mode', choices=('controls', 'full'), required=True)
    ap.add_argument('--scenario', choices=('LEF', 'KPEX'), required=True)
    args = ap.parse_args()
    assert len(os.sched_getaffinity(0)) == 1
    assert kdb.__version__ == '0.30.9'
    prep = json.loads((args.preparation / 'summary.json').read_text())
    assert prep['status'] == 'passed conditional metallization preparation'
    assert all(sha(args.preparation / name) == digest for name, digest in prep['outputs'].items())
    args.output.mkdir(exist_ok=False)
    scenario = json.loads((args.preparation / 'scenarios.json').read_text())[args.scenario]
    receipt = dict(status='running', mode=args.mode, scenario=args.scenario, resistance_values=scenario,
        worker_sha256=sha(Path(__file__)), preparation_sha256=sha(args.preparation / 'summary.json'),
        native_engine_file=str(core.__file__), native_engine_sha256=sha(Path(core.__file__)),
        domain='conditional actual metallization only; internal/electrode/substrate model boundaries not qualified',
        physical_IR_qualification='not run', nonlinear_redistribution='not run', adoption='not run', seed='not applicable')
    dump(args.output / 'summary.json', receipt)
    start = time.monotonic()
    try:
        if args.mode == 'controls':
            cases = controls(scenario, args.output)
            dump(args.output / 'controls.json', cases)
            receipt.update(status='passed controls' if all(c['passed'] for c in cases) else 'failed controls',
                           controls=[{k: v for k, v in c.items() if k not in ('raw', 'solution')} for c in cases])
            assert all(c['passed'] for c in cases)
        else:
            ly = kdb.Layout()
            ly.read(str(args.preparation / 'metallization.gds'))
            regions = {IDS[name]: kdb.Region(ly.top_cell().begin_shapes_rec(ly.layer(*pair))).merged() for name, pair in PAIRS.items()}
            points = json.loads((args.preparation / 'points.json').read_text())
            raw = extract(regions, points, scenario)
            receipt['extraction_wall_s'] = time.monotonic() - start
            (args.output / 'raw_network.json.gz').write_bytes(gzip.compress(json.dumps(raw, allow_nan=False).encode(), mtime=0))
            result, voltage = solve(raw, points, 55)
            dump(args.output / 'solution.json', result)
            np.save(str(args.output / 'node_voltages.npy'), voltage)
            receipt.update(status=result['status'], raw_network_sha256=sha(args.output / 'raw_network.json.gz'),
                solution_sha256=sha(args.output / 'solution.json'), nodes=result['raw_nodes'], edges=result['raw_edges'],
                maximum_absolute_delta_V=result['maximum_absolute_delta_V'], max_free_node_KCL_residual_A=result['max_free_node_KCL_residual_A'])
    except Exception as error:
        receipt.update(status='failed', error=repr(error))
        raise
    finally:
        receipt.update(wall_s=time.monotonic() - start, peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024)
        dump(args.output / 'summary.json', receipt)
        print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
