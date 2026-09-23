#!/usr/bin/env python3
"""Exactly 301 emitter M1-to-published-M2 point-plane substitutions only."""
import argparse
import collections
import datetime
import hashlib
import json
import os
from pathlib import Path
import time
import klayout.db as kdb

PAIRS = {'M1': (8, 0), 'M2': (10, 0), 'M3': (30, 0), 'M4': (50, 0), 'M5': (67, 0),
         'Via1': (19, 0), 'Via2': (29, 0), 'Via3': (49, 0), 'Via4': (66, 0)}
CUTS = {'Via1': ('M1', 'M2'), 'Via2': ('M2', 'M3'), 'Via3': ('M3', 'M4'), 'Via4': ('M4', 'M5')}


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def dump(p, x):
    p.write_text(json.dumps(x, indent=2, allow_nan=False) + '\n')


def main():
    p = argparse.ArgumentParser()
    for key in ('baseline', 'boundary-audit', 'output', 'resource-gate'):
        p.add_argument('--' + key, type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(exist_ok=False)
    (a.output / 'worker_snapshot.py').write_bytes(Path(__file__).read_bytes())
    result = dict(status='running', source_insertion='not run', physical_IR_qualification='not run')
    started = time.monotonic()
    try:
        gate = json.loads(a.resource_gate.read_text())
        assert gate['status'] == 'passed'
        assert 0 <= (datetime.datetime.now(datetime.timezone.utc) - datetime.datetime.fromisoformat(gate['utc'])).total_seconds() < 1800
        assert os.sched_getaffinity(0) == {0}
        assert kdb.__version__ == '0.30.9'
        base = json.loads((a.baseline / 'summary.json').read_text())
        assert base['status'] == 'passed conditional metallization preparation'
        assert all(sha(a.baseline / n) == h for n, h in base['outputs'].items())
        proof = json.loads((a.boundary_audit / 'summary.json').read_text())
        assert proof['status'] == 'passed read-only geometric/model inventory; physical partition unresolved'
        assert all(sha(Path(n)) == h for n, h in proof['inputs'].items())
        records = json.loads((a.boundary_audit / 'native_terminal_planes.json').read_text())
        hbts = {r['source_id']: r for r in records if r['source_id'].startswith('XQ')}
        assert len(hbts) == 301
        points = json.loads((a.baseline / 'points.json').read_text())
        changes = []
        for point in points:
            selected = [s for s in point['sources'] if s['source_id'].startswith('XQ') and s['terminal'] == 'E']
            if selected:
                assert len(selected) == len(point['sources']) == 1
                assert point['layer'] == 'M1' and not point['reference_ports']
                source = selected[0]['source_id']
                assert hbts[source]['same_xy_within_native_M2_pin']
                assert hbts[source]['conditional_injection_layer'] == 'M1'
                changes.append(dict(point_id=point['id'], source_id=source, terminal='E', old_layer='M1', new_layer='M2',
                                    unchanged_point_dbu=point['point_dbu'], unchanged_source_net=point['source_net']))
                point['layer'] = 'M2'
        assert len(changes) == len({c['source_id'] for c in changes}) == 301
        baseline_points = json.loads((a.baseline / 'points.json').read_text())
        restored = json.loads(json.dumps(points))
        for change in changes:
            restored[change['point_id']]['layer'] = 'M1'
        assert restored == baseline_points
        layout = kdb.Layout()
        layout.read(str(a.baseline / 'metallization.gds'))
        top = layout.top_cell()
        ltn = kdb.LayoutToNetlist(kdb.RecursiveShapeIterator(layout, top, []))
        layers = {n:ltn.make_layer(layout.layer(*pair), n) for n,pair in PAIRS.items()}
        for n in layers:
            ltn.connect(layers[n])
        for cut, ends in CUTS.items():
            for end in ends:
                ltn.connect(layers[cut], layers[end])
        ltn.extract_netlist()
        owners = collections.defaultdict(set)
        for point in points:
            node = ltn.probe_net(layers[point['layer']], kdb.Point(*point['point_dbu']))
            assert node is not None
            owners[node.cluster_id].add(point['source_net'])
            # Numeric cluster IDs depend on graph construction order. Prove the
            # old and new probes share one cluster in this same graph instance.
            old = baseline_points[point['id']]
            old_node = ltn.probe_net(layers[old['layer']], kdb.Point(*old['point_dbu']))
            assert old_node is not None and node.cluster_id == old_node.cluster_id
            point['component'] = node.cluster_id
        assert len(owners) == 55 and all(len(v) == 1 for v in owners.values())
        assert len({(p['layer'], tuple(p['point_dbu'])) for p in points}) == len(points) == 3355
        for name in ('metallization.gds', 'scenarios.json', 'omitted_resistor_substrates.json'):
            (a.output / name).write_bytes((a.baseline / name).read_bytes())
            assert sha(a.output / name) == sha(a.baseline / name)
        dump(a.output / 'points.json', points)
        dump(a.output / 'point_plane_changes.json', changes)
        frozen = [a.baseline/n for n in base['outputs']] + [a.baseline/'summary.json',
                  a.boundary_audit/'summary.json', a.boundary_audit/'native_terminal_planes.json', a.resource_gate, Path(__file__)]
        result.update(status='passed conditional metallization preparation', source_devices=1036,
                      represented_terminal_incidences=3346, distinct_injection_points=3355, source_net_count=55,
                      exact_plane_substitutions=301, same_coordinates_currents_source_terms=True,
                      every_native_metal_via_byte_unchanged=True, no_positive_R_subtraction=True,
                      input_points_reconstructed_exact=True, inputs={str(q):sha(q) for q in frozen},
                      outputs={n:sha(a.output/n) for n in ('metallization.gds','points.json','scenarios.json','omitted_resistor_substrates.json')},
                      boundaries='HBT E at unchanged x/y within native published M2 pin; all other original points held',
                      unresolved='Published geometric pins are not proof of calibrated model deembedding; native spreading, R BN, substrate and historical C landing unresolved')
    except Exception as error:
        result.update(status='failed', error=repr(error))
        raise
    finally:
        result['wall_s'] = time.monotonic()-started
        dump(a.output/'summary.json', result)
        print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
