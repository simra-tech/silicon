#!/usr/bin/env python3
"""Add every ledger Via2/Via3 cut to the partial return-tree sensitivity."""
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
    for name in ('gds', 'ledger', 'wire', 'output'):
        ap.add_argument('--' + name, type=Path, required=True)
    args = ap.parse_args()
    assert len(os.sched_getaffinity(0)) == 1 and next(iter(os.sched_getaffinity(0))) in range(4)
    assert sha(args.gds) == '0083eabb0f730b2cb27eeb0bda1ac8f173a21e03e2aa5a329b01ef5cba21b3ed'
    assert sha(args.ledger) == '99a734d096ab00af99d697279066d7383a65a24dfe5df4b4c1f52ba5170ecb02'
    wire = json.loads(args.wire.read_text())
    assert wire['status'] == 'passed wire-only sensitivity preparation; not extracted RC or IR qualification'
    assert wire['source_count'] == 76
    lef = Path('/foss/pdks/ihp-sg13g2/libs.ref/sg13g2_stdcell/lef/sg13g2_tech.lef')
    assert sha(lef) == '054f5b7b24d72365b4b1088be1331e04c1c2e3805de9f99c37e71938ed231efc'
    cut_r = {}
    for name, body in re.findall(r'^LAYER (\S+)\s*\n(.*?)^END \1\s*$', lef.read_text(), re.M | re.S):
        if name in ('Via2', 'Via3'):
            values = re.findall(r'^\s*RESISTANCE\s+([0-9.]+)\s*;', body, re.M)
            assert len(values) == 1
            cut_r[name] = float(values[0])
    assert cut_r == {'Via2': 20.0, 'Via3': 20.0}
    ly = kdb.Layout()
    ly.read(str(args.gds))
    top = ly.top_cell()
    drawn = {name: plain(kdb.Region(top.begin_shapes_rec(ly.layer(layer, 0)))) for name, layer in [('Via2', 29), ('Via3', 49)]}
    ledger = json.loads(args.ledger.read_text())
    assigned = set()
    arrays = []
    def array(role, layer, x, y, label, interface=None):
        hits = []
        for index, via in enumerate(ledger['vias']):
            if via['role'] != role or via['layer'] != layer or via['interface'] != interface:
                continue
            x0, y0, x1, y1 = via['bbox_dbu']
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            if (abs(cx - x) == 210 and cy == y) or (cx == x and abs(cy - y) == 210):
                assert x1 - x0 == y1 - y0 == 190
                assert index not in assigned
                assert plain(kdb.Region(kdb.Box(x0, y0, x1, y1)) - drawn[layer]).is_empty()
                hits.append(index)
        assert len(hits) == 2, (role, layer, x, y, label, hits)
        centers = [((ledger['vias'][i]['bbox_dbu'][0] + ledger['vias'][i]['bbox_dbu'][2]) / 2,
                    (ledger['vias'][i]['bbox_dbu'][1] + ledger['vias'][i]['bbox_dbu'][3]) / 2) for i in hits]
        assert sum(c[0] for c in centers) / 2 == x and sum(c[1] for c in centers) / 2 == y
        assigned.update(hits)
        identifier = role + ':' + label + ':' + layer
        arrays.append(dict(id=identifier, role=role, layer=layer, center_dbu=[x, y], cut_indices=hits,
                           cuts=2, ohm_per_cut=cut_r[layer], parallel_ohm=cut_r[layer] / 2))
        return identifier
    rows = []
    for role in wire['roles']:
        name = role['role']
        trunk = next(r for r in ledger['routes'] if r['role'] == name and r['purpose'] == 'return_trunk')
        x0, y0, x1, y1 = trunk['bbox_dbu']
        tx, ty = (x0 + x1) / 2, y0 + 400
        common = {array(name, layer, tx, ty, 'trunk_base') for layer in ('Via2', 'Via3')}
        interface = ledger['star_interfaces'][name]
        sx = sum((b[0] + b[2]) / 2 for b in interface) / len(interface)
        sy = sum((b[1] + b[3]) / 2 for b in interface) / len(interface)
        common.add(array(name, 'Via3', sx, sy, 'star_interface', name))
        paths = {}
        row_arrays = {}
        for y in sorted({p['row_point_dbu'][1] for p in role['probes']}):
            row_arrays[y] = {array(name, layer, tx, y, 'row_' + str(y)) for layer in ('Via2', 'Via3')}
        for probe in role['probes']:
            x, y = probe['row_point_dbu']
            local = {array(name, layer, x, y, probe['instance']) for layer in ('Via2', 'Via3')}
            paths[probe['instance']] = common | row_arrays[y] | local
        values = {r['id']: r['parallel_ohm'] for r in arrays}
        names = role['sources']
        extra = [[sum(values[e] for e in sorted(paths[a] & paths[b])) for b in names] for a in names]
        matrix = [[role['transfer_ohm'][i][j] + extra[i][j] for j in range(len(names))] for i in range(len(names))]
        injection = {source: (i + 1) * 1e-9 for i, source in enumerate(names)}
        branch_current = {edge: sum(injection[source] for source in names if edge in paths[source]) for edge in values}
        errors = [abs(sum(values[e] * branch_current[e] for e in paths[source]) -
                      sum(extra[i][j] * injection[other] for j, other in enumerate(names))) for i, source in enumerate(names)]
        assert max(errors) < 1e-15
        rows.append(dict(role=name, sources=names, transfer_ohm=matrix, added_via_transfer_ohm=extra,
                         via_paths={key: sorted(value) for key, value in paths.items()},
                         max_self_path_wire_plus_ledger_via_ohm=max(matrix[i][i] for i in range(len(names))),
                         artificial_1uA_each_max_drop_uV=max(sum(row) for row in matrix),
                         independent_array_current_ZI_error_V=max(errors)))
    expected = {i for i, via in enumerate(ledger['vias']) if via['role'].startswith('return_')}
    assert assigned == expected and len(assigned) == 376
    args.output.mkdir(exist_ok=False)
    report = dict(status='passed partial wire-plus-ledger-via sensitivity; not full extracted RC or IR qualification',
                  inputs={str(p): sha(p) for p in (args.gds, args.ledger, args.wire, lef, Path(__file__))},
                  source_count=76, ledger_via_cuts_covered=376, parallel_arrays=len(arrays), arrays=arrays, roles=rows,
                  omitted=['native emitter/contact and Via1 access', 'wire bends/spreading', 'finite common hub/generalVSS',
                           'precision resistor rail', 'temperature/process variation', 'self-consistent current redistribution'],
                  actual_current_voltage_error='not run here; requires independently qualified current ledger', adoption='not run')
    (args.output / 'worker_snapshot.py').write_bytes(Path(__file__).read_bytes())
    (args.output / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({**report, 'arrays': 'see full receipt', 'roles': [{k: v for k, v in r.items()
                      if k not in ('sources', 'transfer_ohm', 'added_via_transfer_ohm', 'via_paths')} for r in rows]}, indent=2))


if __name__ == '__main__':
    main()
