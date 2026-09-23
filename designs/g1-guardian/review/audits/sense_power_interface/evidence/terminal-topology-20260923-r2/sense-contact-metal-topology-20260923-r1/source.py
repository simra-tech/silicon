#!/usr/bin/env python3
"""Geometry-owned metal-R topology; no compact-model attachment or currents."""
import argparse
import collections
import gzip
import json
import math
import os
from pathlib import Path
import resource
import time
import klayout.db as kdb
import pad_metal_r_controls as engine

HERE = Path(__file__).resolve().parent
GM4 = HERE.parents[2]/'blocks/g1_sense/layout/coordinated_gm4'


def materialize(cell, pair):
    result = kdb.Region()
    for polygon in kdb.Region(cell.begin_shapes_rec(cell.layout().layer(*pair))).each():
        result.insert(kdb.Polygon(polygon))
    return result.merged()


def inside_point(polygon):
    if polygon.inside(polygon.bbox().center()): return polygon.bbox().center()
    for vertex in polygon.each_point_hull():
        for dx, dy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
            point = kdb.Point(vertex.x+dx, vertex.y+dy)
            if polygon.inside(point): return point
    raise AssertionError('No strict polygon interior witness')


def native_graph(regions):
    layout = kdb.Layout(); layout.dbu = .001; top = layout.create_cell('metal_topology')
    for name, region in regions.items(): top.shapes(layout.layer(*engine.PAIRS[name])).insert(region)
    net = kdb.LayoutToNetlist(kdb.RecursiveShapeIterator(layout, top, [])); layers = {}
    for name in engine.PAIRS:
        layers[name] = net.make_layer(layout.layer(*engine.PAIRS[name]), name); net.connect(layers[name])
    for name, joined in engine.CUTS.items():
        for conductor in joined: net.connect(layers[name], layers[conductor])
    net.extract_netlist()
    return layout, net, layers


def topology(raw, observations, native_count):
    index = {r['id']: i for i, r in enumerate(raw['nodes'])}
    zero = engine.base.Union(len(index))
    for edge in raw['edges']:
        assert math.isfinite(edge['R_ohm']) and edge['R_ohm'] >= 0
        if edge['R_ohm'] == 0: zero.join(index[edge['a']], index[edge['b']])
    roots = sorted({zero.find(i) for i in range(len(index))}); compact = {r: i for i, r in enumerate(roots)}
    reduced = {key: compact[zero.find(value)] for key, value in index.items()}
    connected = engine.base.Union(len(roots)); positive = []; collapsed_positive = 0
    for edge in raw['edges']:
        a, b = reduced[edge['a']], reduced[edge['b']]
        if edge['R_ohm'] == 0: continue
        assert edge['R_ohm'] > 0
        if a == b: collapsed_positive += 1; continue
        connected.join(a, b)
        positive.append(dict(a=a, b=b, R_ohm=edge['R_ohm']))
    components = {connected.find(i) for i in range(len(roots))}
    native_to_raw = collections.defaultdict(set); raw_to_native = collections.defaultdict(set)
    for row in observations:
        assert row['id'] in raw['point_to_node'], ('Missing physical contact/witness', row['id'])
        row['raw_node'] = raw['point_to_node'][row['id']]
        row['reduced_node'] = reduced[row['raw_node']]
        row['R_component'] = connected.find(row['reduced_node'])
        native_to_raw[row['native_component']].add(row['R_component'])
        raw_to_native[row['R_component']].add(row['native_component'])
    assert len(components) == native_count == len(native_to_raw) == len(raw_to_native)
    assert components == set(raw_to_native), 'Extracted floating component lacks a native witness'
    assert all(len(v) == 1 for v in native_to_raw.values()), 'R extraction splits a native metal component'
    assert all(len(v) == 1 for v in raw_to_native.values()), 'R extraction merges distinct native metal components'
    return dict(status='passed exact native-to-R component bijection', raw_nodes=len(index),
                reduced_nodes=len(roots), raw_edges=len(raw['edges']),
                zero_edges=sum(e['R_ohm'] == 0 for e in raw['edges']), positive_edges=len(positive),
                positive_edges_collapsed_by_exact_zero_paths=collapsed_positive,
                components=len(components), observations=observations,
                minimum_positive_R_ohm=min(e['R_ohm'] for e in positive),
                maximum_positive_R_ohm=max(e['R_ohm'] for e in positive)), positive


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('footprints', 'ledger', 'controls', 'output'):
        parser.add_argument('--'+key, type=Path, required=True)
    args = parser.parse_args(); assert not args.output.exists()
    assert len(os.sched_getaffinity(0)) == 1 and kdb.__version__ == '0.30.9'
    assert Path('/foss/pdks/ihp-sg13g2/COMMIT').read_text().strip() == '84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    sha = engine.base.sha; dump = engine.base.dump
    controls = json.loads(args.controls.read_text())
    assert controls['status'] == 'passed twelve analytic native-metal via controls'
    assert controls['script_sha256'] == sha(HERE/'pad_metal_r_controls.py')
    assert controls['base_helper_sha256'] == sha(engine.BASE)
    rectangle_path = engine.BASE.parent/'evidence/metallization-20260922-r1/controls/lef/r2/result/summary.json'
    rectangle = json.loads(rectangle_path.read_text())
    assert rectangle['status'] == 'passed controls'
    assert rectangle['worker_sha256'] == sha(engine.BASE)
    assert all(row['passed'] for row in rectangle['controls'])
    assert sha(Path(rectangle['native_engine_file'])) == rectangle['native_engine_sha256']
    model = engine.scenario(); assert model == controls['scenario']
    footprints = json.loads(args.footprints.read_text()); ledger = json.loads(args.ledger.read_text())
    assert footprints['ledger_sha256'] == sha(args.ledger)
    parent = GM4/'ring-r8-evidence-20260922-r1/sense-ring-routing-20260922-r8a'
    gds = parent/'g1_sense_physical.gds'
    source = GM4.parents[1]/'reports/resume-server-20260922/gm4comp3-qualified-source.spice'
    assert sha(gds) == footprints['GDS_sha256'] == ledger['GDS_sha256']
    assert sha(source) == footprints['source_sha256'] == ledger['source_sha256']
    args.output.mkdir(parents=True)
    for name, path in [('source.py', Path(__file__)), ('topmetal_helper.py', HERE/'pad_metal_r_controls.py'),
                       ('native_R_helper.py', engine.BASE), ('footprints.json', args.footprints)]:
        (args.output/name).write_bytes(path.read_bytes())
    result = dict(status='running geometry-only metal-R topology', GDS_sha256=sha(gds),
                  source_sha256=sha(source), footprint_sha256=sha(args.footprints),
                  script_sha256=sha(Path(__file__)), controls_sha256=sha(args.controls), scenario=model,
                  rectangle_controls_sha256=sha(rectangle_path),
                  native_engine_sha256=rectangle['native_engine_sha256'],
                  no_model_weights_or_current_injection_chosen=True,
                  compact_model_composition='not run', physical_IR_EM='not run', adoption='not run')
    start = time.monotonic()
    try:
        layout = kdb.Layout(); layout.read(str(gds)); cell = layout.cell('g1_sense_physical')
        assert layout.dbu == .001
        regions = {name: materialize(cell, pair) for name, pair in engine.PAIRS.items()}
        cuts = []; invalid = []
        for name, joined in engine.CUTS.items():
            expected = round(engine.SIZE[name]*1000)
            for polygon in regions[name].each():
                box = polygon.bbox()
                if polygon.area() != expected**2 or box.width() != expected or box.height() != expected:
                    invalid.append(dict(layer=name, bbox=str(box), issue='nonstandard actual cut dimensions'))
                cuts.append(dict(layer=name, bbox_dbu=[box.left, box.bottom, box.right, box.top],
                                 area_dbu2=polygon.area(), lower=joined[0], upper=joined[1]))
            for conductor in joined:
                missing = regions[name]-regions[conductor]
                if not missing.is_empty(): invalid.append(dict(layer=name, conductor=conductor,
                                                               uncovered_cut_area_dbu2=missing.area()))
        assert (regions['TopVia1'] & materialize(cell, (36, 0))).is_empty(), 'MIM-region TopVia1 requires separate ownership'
        dump(args.output/'via_footprints.json', dict(rows=cuts, invalid=invalid))
        assert not invalid, invalid
        covered = kdb.Region()
        for row in footprints['footprints']: covered.insert(kdb.Box(*row['bbox_dbu']))
        assert (covered-regions['M1']).is_empty(), 'Catalogued physical contact lacks exact M1 coverage'
        hold = native_graph(regions); native, layers = hold[1], hold[2]
        native_count = sum(1 for c in native.netlist().each_circuit() for _ in c.each_net())
        observations = []; polygons = []; points = []; physical_names = collections.defaultdict(set)
        covered_components = set()
        def bind(row, layer, point, source_net):
            found = native.probe_net(layers[layer], point)
            assert found is not None, ('Unmapped exact native footprint/witness', row)
            row['native_component'] = found.cluster_id; observations.append(row)
            covered_components.add(found.cluster_id)
            if source_net is not None: physical_names[found.cluster_id].add(source_net)
        for footprint in footprints['footprints']:
            box = kdb.Box(*footprint['bbox_dbu']); identifier = footprint['id']
            polygons.append(dict(id=identifier, layer='M1', box_dbu=footprint['bbox_dbu']))
            bind(dict(id=identifier, kind='physical_contact_footprint', bbox_dbu=footprint['bbox_dbu'],
                      source_net=footprint['source_net'], owners=footprint['owners'],
                      model_attachment='not qualified; native PolygonPort is a node marker, not an equipotential area'),
                 'M1', box.center(), footprint['source_net'])
        metal_by_layer = {pair[0]: name for name, pair in engine.PAIRS.items() if name not in engine.CUTS}
        seen = {}
        for slot in ledger['slots']:
            for witness in slot.get('witnesses', []):
                if witness['layer'] not in metal_by_layer: continue
                point = tuple(round(v*1000) for v in witness['point_um'])
                key = (witness['layer'],)+point
                if key in seen:
                    assert seen[key] == slot['source_net']; continue
                seen[key] = slot['source_net']; name = metal_by_layer[witness['layer']]
                identifier = 'source_witness_'+str(len(points))
                points.append(dict(id=identifier, layer=name, point_dbu=list(point)))
                bind(dict(id=identifier, kind='existing source-owned metal witness', source_net=slot['source_net'],
                          device=slot['device'], terminal=slot['terminal']), name, kdb.Point(*point), slot['source_net'])
        for name in model['sheet_ohm']:
            for polygon in regions[name].each():
                point = inside_point(polygon); found = native.probe_net(layers[name], point)
                assert found is not None
                if found.cluster_id in covered_components: continue
                identifier = 'unattributed_component_'+str(found.cluster_id)
                points.append(dict(id=identifier, layer=name, point_dbu=[point.x, point.y]))
                bind(dict(id=identifier, kind='native component topology witness only', source_net=None), name, point, None)
        assert len(covered_components) == native_count
        foreign = {str(key): sorted(value) for key, value in physical_names.items() if len(value) > 1}
        assert not foreign, foreign
        logical_components = collections.defaultdict(set)
        for component, names in physical_names.items():
            for name in names: logical_components[name].add(component)
        result.update(native_metal_components=native_count, source_nets_observed=len(logical_components),
                      source_nets_with_multiple_metal_components={n: sorted(v) for n, v in logical_components.items() if len(v) > 1},
                      unattributed_components=sorted(covered_components-set(physical_names)),
                      physical_contacts=len(polygons), source_and_component_witnesses=len(points),
                      via_counts=dict(collections.Counter(r['layer'] for r in cuts)),
                      excluded_native_layers={str(pair): dict(polygons=materialize(cell, pair).count(),
                                                               area_dbu2=materialize(cell, pair).area())
                                              for pair in [(1, 0), (5, 0), (6, 0), (36, 0), (128, 0), (129, 0)]})
        dump(args.output/'preparation.json', result)
        extracted = time.monotonic()
        raw = engine.base.extract({engine.IDS[name]: region for name, region in regions.items()}, points, model, polygons)
        result['native_extraction_wall_s'] = time.monotonic()-extracted
        audited, positive = topology(raw, observations, native_count)
        (args.output/'raw_network.json.gz').write_bytes(gzip.compress(json.dumps(raw, allow_nan=False).encode(), mtime=0))
        (args.output/'positive_edges.json.gz').write_bytes(gzip.compress(json.dumps(positive, allow_nan=False).encode(), mtime=0))
        dump(args.output/'topology.json', audited)
        assert sha(source) == result['source_sha256'] and sha(gds) == result['GDS_sha256']
        result.update(status='passed geometry-only all-contact metal-R topology',
                      topology_sha256=sha(args.output/'topology.json'), raw_network_sha256=sha(args.output/'raw_network.json.gz'),
                      topology={k: v for k, v in audited.items() if k != 'observations'},
                      source_geometry_unchanged=True,
                      not_run=['Cont/Poly/Active/resistor/MIM/substrate resistance ownership',
                               '367 remaining source-slot contact ownership assignments',
                               'Compact-model terminal attachment or currents', 'ZeroR source/wave parity',
                               'Nonlinear electrical/IR/EM/field/adoption'])
    except Exception as exc:
        result.update(status='failed geometry-only metal-R topology', error=repr(exc)); raise
    finally:
        result.update(wall_s=time.monotonic()-start, peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024)
        dump(args.output/'summary.json', result); print(json.dumps(result, indent=2))


if __name__ == '__main__': main()
