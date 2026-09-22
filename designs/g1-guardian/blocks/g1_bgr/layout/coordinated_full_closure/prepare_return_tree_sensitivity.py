#!/usr/bin/env python3
"""Wire-only multi-injection tree sensitivity, not extracted RC or an IR bound."""
import argparse
import collections
import json
import os
from pathlib import Path
import re
import klayout.db as kdb
from export_cc_api import plain, sha


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--gds', type=Path, required=True)
    ap.add_argument('--ledger', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    assert len(os.sched_getaffinity(0)) == 1 and next(iter(os.sched_getaffinity(0))) in range(4)
    assert sha(args.gds) == '0083eabb0f730b2cb27eeb0bda1ac8f173a21e03e2aa5a329b01ef5cba21b3ed'
    assert sha(args.ledger) == '99a734d096ab00af99d697279066d7383a65a24dfe5df4b4c1f52ba5170ecb02'
    lef = Path('/foss/pdks/ihp-sg13g2/libs.ref/sg13g2_stdcell/lef/sg13g2_tech.lef')
    assert sha(lef) == '054f5b7b24d72365b4b1088be1331e04c1c2e3805de9f99c37e71938ed231efc'
    sheets = {}
    for name, body in re.findall(r'^LAYER (\S+)\s*\n(.*?)^END \1\s*$', lef.read_text(), re.M | re.S):
        match = re.search(r'RESISTANCE RPERSQ (\S+)', body)
        if match and name in ('Metal2', 'Metal4'):
            sheets['M' + name[5:]] = float(match[1])
    assert sheets == {'M2': .103, 'M4': .103}
    ledger = json.loads(args.ledger.read_text())
    ly = kdb.Layout()
    ly.read(str(args.gds))
    top = ly.top_cell()
    drawn = {name: plain(kdb.Region(top.begin_shapes_rec(ly.layer(layer, 0)))) for name, layer in [('M2', 10), ('M4', 50)]}
    results = []
    for role in ('return_XQ56', 'return_XQ60', 'return_XQ62', 'return_XQ67'):
        routes = [r for r in ledger['routes'] if r['role'] == role and r['purpose'] in
                  ('return_trunk', 'functional_return_row', 'star_branch')]
        for route in routes:
            box = kdb.Box(*route['bbox_dbu'])
            assert plain(kdb.Region(box) - drawn[route['layer']]).is_empty()
        probes = sorted([p for p in ledger['probes'] if p['role'] == role and p['terminal'] == 'E'], key=lambda p: p['instance'])
        assert probes and all(p['net'] == 'vss' and p['layer'] == 'M2' for p in probes)
        for probe in probes:
            px, py = probe['point_dbu']
            wires = [r for r in ledger['routes'] if r['role'] == role and r['layer'] == 'M2' and
                     r['purpose'] == 'wire' and r['bbox_dbu'][0] <= px <= r['bbox_dbu'][2] and
                     r['bbox_dbu'][1] <= py <= r['bbox_dbu'][3]]
            assert len(wires) == 1
            wx0, wy0, wx1, wy1 = wires[0]['bbox_dbu']
            assert wx1 - wx0 == 300 and (wx0 + wx1) / 2 == px
            assert plain(kdb.Region(kdb.Box(wx0, wy0, wx1, wy1)) - drawn['M2']).is_empty()
            options = [(r['bbox_dbu'][1] + r['bbox_dbu'][3]) / 2 for r in routes
                       if r['purpose'] == 'functional_return_row' and
                       wy0 + 150 <= (r['bbox_dbu'][1] + r['bbox_dbu'][3]) / 2 <= wy1 - 150]
            assert len(options) == 1
            probe['row_point_dbu'] = [px, options[0]]
            probe['access_wire_ohm'] = sheets['M2'] * abs(options[0] - py) / 300
        trunks = [r for r in routes if r['purpose'] == 'return_trunk']
        assert len(trunks) == 1
        x0, y0, x1, y1 = trunks[0]['bbox_dbu']
        assert x1 - x0 == 800
        tx, ty = (x0 + x1) / 2, y0 + 400
        star_r = 0
        for route in routes:
            if route['purpose'] == 'star_branch':
                bx0, by0, bx1, by1 = route['bbox_dbu']
                short, long = sorted((bx1 - bx0, by1 - by0))
                assert short == 800
                star_r += sheets[route['layer']] * (long - short) / short
        assert star_r > 0
        nodes = [{'id': 'star', 'parent': None, 'edge_ohm': 0},
                 {'id': 'trunk_base', 'parent': 'star', 'edge_ohm': star_r}]
        parent = 'trunk_base'
        previous_y = ty
        row_nodes = {}
        for y in sorted({p['row_point_dbu'][1] for p in probes}):
            assert y > previous_y
            name = 'row_' + str(y)
            nodes.append(dict(id=name, parent=parent, edge_ohm=sheets['M2'] * (y - previous_y) / 800))
            parent, previous_y = name, y
            row_nodes[y] = name
        injection_nodes = {}
        for y, branch in sorted(row_nodes.items()):
            row_routes = [r for r in routes if r['purpose'] == 'functional_return_row' and
                          (r['bbox_dbu'][1] + r['bbox_dbu'][3]) / 2 == y]
            assert len(row_routes) == 1
            bx0, by0, bx1, by1 = row_routes[0]['bbox_dbu']
            assert by1 - by0 == 800 and bx0 + 400 == tx
            previous_x, parent = tx, branch
            for probe in sorted([p for p in probes if p['row_point_dbu'][1] == y], key=lambda p: p['row_point_dbu'][0]):
                x = probe['row_point_dbu'][0]
                assert previous_x < x <= bx1 - 400
                name = probe['instance'] + '_tap'
                nodes.append(dict(id=name, parent=parent, edge_ohm=sheets['M4'] * (x - previous_x) / 800))
                nodes.append(dict(id=probe['instance'], parent=name, edge_ohm=probe['access_wire_ohm']))
                injection_nodes[probe['instance']] = probe['instance']
                parent, previous_x = name, x
        assert len(injection_nodes) == len(probes)
        by_id = {n['id']: n for n in nodes}
        def path(name):
            edges = set()
            while by_id[name]['parent'] is not None:
                edges.add(name)
                name = by_id[name]['parent']
            return edges
        names = sorted(injection_nodes)
        paths = {name: path(name) for name in names}
        matrix = [[sum(by_id[e]['edge_ohm'] for e in sorted(paths[a] & paths[b])) for b in names] for a in names]
        assert all(matrix[i][j] == matrix[j][i] for i in range(len(names)) for j in range(len(names)))
        # Independent bottom-up branch currents and top-down voltages versus ZI.
        injections = {name: (index + 1) * 1e-9 for index, name in enumerate(names)}
        currents = collections.defaultdict(float, injections)
        for node in reversed(nodes[1:]):
            currents[node['parent']] += currents[node['id']]
        voltages = {'star': 0.0}
        for node in nodes[1:]:
            voltages[node['id']] = voltages[node['parent']] + currents[node['id']] * node['edge_ohm']
        error = max(abs(voltages[name] - sum(matrix[i][j] * injections[other] for j, other in enumerate(names)))
                    for i, name in enumerate(names))
        assert error < 1e-15 and abs(currents['star'] - sum(injections.values())) < 1e-18
        results.append(dict(role=role, sources=names, transfer_ohm=matrix, nodes=nodes,
                            star_branch_wire_ohm=star_r, max_self_path_wire_ohm=max(matrix[i][i] for i in range(len(names))),
                            unit_1uA_each_max_drop_uV=max(sum(row) for row in matrix),
                            artificial_vector_KCL_and_ZI_error_V=error, probes=probes))
    args.output.mkdir(exist_ok=False)
    receipt = dict(status='passed wire-only sensitivity preparation; not extracted RC or IR qualification',
                   inputs={str(p): sha(p) for p in (args.gds, args.ledger, lef, Path(__file__))},
                   roles=results, source_count=sum(len(r['sources']) for r in results),
                   actual_device_current_ledger='not run here; pending electrical owner',
                   current_convention='injection into wire equals negative external current entering device emitter port',
                   omitted=['native emitter/contact spreading', 'all via/contact resistance', 'wire bends/spreading',
                            'finite shared star/generalVSS', 'resistor precision rail', 'process/temperature variation',
                            'self-consistent voltage-dependent current redistribution'],
                   interpretation='Nominal LEF centerline model only; partial sensitivity, not full-path bound or adoption',
                   electrical_simulation='not run', adoption='not run')
    (args.output / 'worker_snapshot.py').write_bytes(Path(__file__).read_bytes())
    (args.output / 'summary.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({**receipt, 'roles': [{k: v for k, v in row.items() if k not in ('transfer_ohm', 'nodes', 'probes', 'sources')} for row in results]}, indent=2))


if __name__ == '__main__':
    main()
