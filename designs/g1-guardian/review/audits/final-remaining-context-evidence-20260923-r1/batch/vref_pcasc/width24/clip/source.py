#!/usr/bin/env python3
"""Source-bound final-route metal/fill clip, with exact saved polygon checks."""
import argparse
import json
import os
from pathlib import Path
import pya
from route_inventory import sha
from audit_geometry import NUMBERS


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('inventory', 'geometry', 'candidate', 'output'):
        p.add_argument('--'+key, type=Path, required=True)
    p.add_argument('--victim', required=True)
    p.add_argument('--neighbor', required=True)
    p.add_argument('--victim-segment', type=int, required=True)
    p.add_argument('--neighbor-segment', type=int, required=True)
    p.add_argument('--context-um', type=int, choices=[12, 24, 48], required=True)
    a = p.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0)) == 1 and pya.__version__ == '0.30.9'
    inventory = json.loads(a.inventory.read_text()); geometry = json.loads(a.geometry.read_text())
    assert inventory['status'].startswith('passed') and geometry['status'].startswith('passed')
    assert geometry['inventory_sha256'] == sha(a.inventory)
    source = a.candidate/'filled_native.gds'
    assert sha(source) == geometry['GDS_sha256'] == '4d3907c50f07946ef27a6d53402cf319264499a21379d2de80e9c4f1adbae299'
    pairs = [r for r in inventory['parallel_candidates'] if
             (r['victim'], r['neighbor'], r['victim_segment'], r['neighbor_segment']) ==
             (a.victim, a.neighbor, a.victim_segment, a.neighbor_segment)]
    pair, = pairs
    assert pair['victim_layer'] == pair['neighbor_layer'] and pair['overlap_um'] > 20
    low, high = pair['shared_interval_dbu']; longitudinal = (low+high)//2
    assert low < longitudinal-10000 < longitudinal+10000 < high
    first, second = pair['victim_transverse_dbu'], pair['neighbor_transverse_dbu']
    transverse = (first+second)//2; half = a.context_um*500
    assert transverse-half < min(first, second) < max(first, second) < transverse+half
    vertical = pair['longitudinal_axis'] == 'y'
    box = pya.Box(transverse-half, longitudinal-10000, transverse+half, longitudinal+10000) if vertical else pya.Box(longitudinal-10000, transverse-half, longitudinal+10000, transverse+half)
    points = {label: pya.Point(value, longitudinal) if vertical else pya.Point(longitudinal, value)
              for label, value in [('P', first), ('N', second)]}
    ly = pya.Layout(); ly.read(str(source)); top = ly.top_cell()
    assert ly.dbu == .001 and top.name == 'placed_core_NOT_CONNECTED_FULLCHIP'
    window = pya.Region(box); metals = list(NUMBERS.values()); vias = [19, 29, 49, 66, 125, 133]
    regions = {(layer, dt): (pya.Region(top.begin_shapes_rec(ly.layer(layer, dt)))&window).merged()
               for layer in metals+vias for dt in ([0, 22] if layer in metals else [0])}
    target_layer = NUMBERS[pair['victim_layer']]; labels = []
    for (layer, dt), region in regions.items():
        if layer not in metals:
            continue
        for index, polygon in enumerate(region.each()):
            matched = [label for label, point in points.items() if layer == target_layer and dt == 0 and polygon.inside(point)]
            assert len(matched) <= 1, 'Targets joined in clipped geometry'
            if matched:
                label, = matched; point = points[label]
                if vertical:
                    stripe = pya.Box(point.x-1, box.bottom, point.x+1, box.top)
                else:
                    stripe = pya.Box(box.left, point.y-1, box.right, point.y+1)
                assert (pya.Region(stripe)-pya.Region(polygon)).is_empty()
            else:
                label = ('FILL' if dt == 22 else 'CTX')+'_L%d_%d' % (layer, index)
                point = polygon.bbox().center()
                if not polygon.inside(point):
                    point = list(polygon.decompose_trapezoids())[0].bbox().center()
                assert polygon.inside(point)
            labels.append(dict(name=label, source_layer=[layer, dt], point_dbu=[point.x, point.y]))
    assert sum(r['name'] == 'P' for r in labels) == sum(r['name'] == 'N' for r in labels) == 1
    a.output.mkdir(parents=True); (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    variants = []
    for variant in ('no_fill', 'actual_fill'):
        out = pya.Layout(); out.dbu = .001; cell = out.create_cell('sense_fill_clip')
        for (layer, dt), region in regions.items():
            if variant == 'actual_fill' or dt != 22:
                cell.shapes(out.layer(layer, dt)).insert(region)
        for label in labels:
            layer, dt = label['source_layer']
            if variant == 'actual_fill' or dt != 22:
                cell.shapes(out.layer(layer, 25)).insert(pya.Text(label['name'], pya.Trans(*label['point_dbu'])))
        path = a.output/(variant+'.gds'); out.write(str(path))
        saved = pya.Layout(); saved.read(str(path)); st = saved.top_cell()
        checks = []
        for (layer, dt), region in regions.items():
            expected = pya.Region() if variant == 'no_fill' and dt == 22 else region
            observed = pya.Region(st.begin_shapes_rec(saved.layer(layer, dt))).merged()
            assert (expected^observed).is_empty()
            checks.append(dict(layer=[layer, dt], polygons=observed.count(), xor_area_um2=0))
        variants.append(dict(variant=variant, sha256=sha(path), geometry=checks))
    omitted = []
    for layer in (1, 5):
        region = (pya.Region(top.begin_shapes_rec(ly.layer(layer, 22)))&window).merged()
        omitted.append(dict(layer=[layer, 22], polygons=region.count(), area_um2=region.area()*1e-6))
    assert sha(source) == geometry['GDS_sha256']
    result = dict(status='passed exact final-context paired clip export',
        source_gds_sha256=sha(source), inventory_sha256=sha(a.inventory), geometry_audit_sha256=sha(a.geometry),
        script_sha256=sha(Path(__file__)), KLayout=pya.__version__, pair=pair,
        clip_box_dbu=[box.left, box.bottom, box.right, box.top], context_um=a.context_um,
        length_um=20, labels=labels, variants=variants, omitted_nonmetal_fill=omitted,
        scope='Exact source metal/via polygons; additional text is diagnostic only. No net joining by label or outside-clip continuity assumed.',
        not_run=['stock extraction', 'full-route/context convergence', 'electrical coupling acceptance'],
        limitations=['Active/poly fill, devices and all below-M1 geometry omitted; not a full capacitance model.',
                    'Grounded/floating fill and other-context boundary conditions must be declared in subsequent reduction.',
                    'Midpoint clip cannot be scaled by full route length to claim complete coupling.'])
    (a.output/'provenance.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('labels', 'variants')}, indent=2))


if __name__ == '__main__':
    main()
