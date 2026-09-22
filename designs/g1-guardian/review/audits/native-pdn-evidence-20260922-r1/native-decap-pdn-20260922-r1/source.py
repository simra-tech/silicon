#!/usr/bin/env python3
"""Construct source-bound decap supply feeders; fail closed on foreign nets."""
import argparse
import collections
import faulthandler
import json
import os
from pathlib import Path
import pya
from audit_placed_decap_domains import physical, identity, sha
from place_closed_analog import region, text_records

METALS = (8, 10, 30, 50, 67, 126, 134)
CUTS = ((19, 8, 10), (29, 10, 30), (49, 30, 50),
        (66, 50, 67), (125, 67, 126), (133, 126, 134))
ANCHORS = {'VDD': [395000, 354660], 'VSS': [507000, 334660]}


def point(polygon):
    p = next(polygon.each_point_hull())
    return [p.x, p.y]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--core', type=Path, required=True)
    p.add_argument('--placement', type=Path, required=True)
    p.add_argument('--plan', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0)) == 1
    assert pya.__version__ == '0.30.9'
    faulthandler.dump_traceback_later(60, repeat=True)
    a.output.mkdir(parents=True)
    (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    plan = json.loads(a.plan.read_text())
    placement = json.loads((a.placement/'analysis.json').read_text())
    source = a.core/'refreshed_core.gds'
    parent = json.loads((a.core/'analysis.json').read_text())
    assert parent['status'].startswith('passed') and plan['status'].startswith('passed')
    assert sha(source) == parent['GDS_sha256'] == plan['source_GDS_sha256']
    assert plan['reachable'] == plan['components'] == 464 and not plan['missing']
    ly = pya.Layout(); ly.read(str(source)); top = ly.top_cell()
    assert ly.dbu == .001
    before = {str(i): region(ly, top, i) for i in ly.layer_infos()}
    old = {layer: region(ly, top, pya.LayerInfo(layer, 0))
           for layer in METALS + tuple(c[0] for c in CUTS)}
    texts = text_records(ly, top)
    net, layers = physical(ly, top)
    allowed = {name: {identity(net, layers[134], xy)} for name, xy in ANCHORS.items()}
    probes = []
    for row in placement['decaps']:
        for name, pin in row['pins'].items():
            xy = pin['placed_dbu']; component = identity(net, layers[10], xy)
            assert component is not None
            allowed[name].add(component)
            probes.append(dict(index=row['index'], net=name, point=xy, before=list(component)))
    assert len(probes) == 9324 and not (allowed['VDD'] & allowed['VSS'])
    assert all(None not in s for s in allowed.values())
    additions = {name: {layer: pya.Region() for layer in old} for name in ANCHORS}
    arrays = []

    def box(name, layer, bounds):
        additions[name][layer].insert(pya.Box(*bounds))

    def array(name, cut, lo, hi, xy, width, pitch, lo_enc, hi_enc):
        x, y = xy
        assert pitch % 2 == width % 2 == 0 or width == 190
        half = (pitch + width)//2
        box(name, lo, (x-half-lo_enc, y-half-lo_enc, x+half+lo_enc, y+half+lo_enc))
        box(name, hi, (x-half-hi_enc, y-half-hi_enc, x+half+hi_enc, y+half+hi_enc))
        cut_boxes = []
        for dx in (-pitch//2, pitch//2):
            for dy in (-pitch//2, pitch//2):
                bounds = (x+dx-width//2, y+dy-width//2, x+dx+width//2, y+dy+width//2)
                box(name, cut, bounds); cut_boxes.append(bounds)
        arrays.append(dict(net=name, cut=cut, lower=lo, upper=hi, center=xy, cuts=cut_boxes))

    for spine in plan['spines']:
        name = spine['net']; b = pya.Box(*spine['bbox'])
        box(name, 126, spine['bbox'])
        for bottom, upper in spine['ring_crossings']:
            array(name, 133, 126, 134, [b.center().x, (bottom+upper)//2], 900, 1960, 650, 650)
    for row in plan['plans']:
        name = row['net']; route = row['best']
        assert tuple(row['component']) in allowed[name]
        assert identity(net, layers[10], route['source_point']) == tuple(row['component'])
        box(name, 10, route['M2_bbox'])
        xy = route['via_center'] if route['route_layer'] == 10 else route['source_point']
        if route['route_layer'] == 67:
            box(name, 67, route['M5_bbox'])
        else:
            assert route['route_layer'] == 10
        for cut, lo, hi in CUTS[1:4]:
            array(name, cut, lo, hi, xy, 190, 500, 55, 55)
        array(name, 125, 67, 126, route['via_center'], 420, 840, 120, 450)
    for by_layer in additions.values():
        for r in by_layer.values(): r.merge()
    errors = []; inspected = collections.Counter()

    def inspect(name, layer, polygons, why):
        for polygon in polygons.each():
            xy = point(polygon); found = identity(net, layers[layer], xy)
            inspected[why] += 1
            if found not in allowed[name]:
                errors.append(dict(net=name, layer=layer, point=xy, actual=found, reason=why))

    for name, added in additions.items():
        other = 'VSS' if name == 'VDD' else 'VDD'
        for layer in METALS:
            if not (added[layer] & additions[other][layer]).is_empty():
                errors.append(dict(net=name, layer=layer, reason='opposite added metals overlap'))
            # Whole touching polygons retain an on-metal native witness even
            # when the new metal touches only a boundary (zero overlap area).
            inspect(name, layer, old[layer].interacting(added[layer]), 'new metal touches native metal')
        for cut, lo, hi in CUTS:
            for layer, opposite in ((lo, hi), (hi, lo)):
                touched = old[cut].interacting(added[layer])
                inspect(name, opposite, old[opposite].interacting(touched), 'new metal touches existing cut')
                inspect(name, layer, old[layer].interacting(added[cut]), 'new cut touches native metal')
                if not (added[cut] & additions[other][layer]).is_empty():
                    errors.append(dict(net=name, cut=cut, layer=layer, reason='new cut touches opposite added metal'))
                if not (added[cut]-(old[layer]+added[layer])).is_empty():
                    errors.append(dict(net=name, cut=cut, layer=layer, reason='new cut not enclosed by intended metal'))
    gate = dict(status='failed' if errors else 'passed', errors=errors,
                inspected=dict(inspected), source_GDS_sha256=sha(source), plan_sha256=sha(a.plan), arrays=arrays)
    (a.output/'preflight.json').write_text(json.dumps(gate, indent=2)+'\n')
    assert not errors, errors[:10]
    print(json.dumps(dict(phase='native no-foreign-contact gate passed', inspected=dict(inspected))), flush=True)
    for layer in old:
        for name in ANCHORS:
            for polygon in additions[name][layer].each():
                top.shapes(ly.layer(layer, 0)).insert(polygon)
    newnet, newlayers = physical(ly, top)
    rings = {name: identity(newnet, newlayers[134], xy) for name, xy in ANCHORS.items()}
    assert None not in rings.values() and len(set(rings.values())) == 2
    bad = []
    for row in probes:
        for layer in (8, 10):
            found = identity(newnet, newlayers[layer], row['point'])
            if found != rings[row['net']]:
                bad.append(dict(probe=row, layer=layer, found=found))
    (a.output/'connectivity.json').write_text(json.dumps(dict(rings=rings, errors=bad), indent=2)+'\n')
    assert not bad, bad[:5]
    for info in ly.layer_infos():
        expected = before.get(str(info), pya.Region())
        if info.datatype == 0 and info.layer in old:
            expected = expected + additions['VDD'][info.layer] + additions['VSS'][info.layer]
        assert (region(ly, top, info)^expected).is_empty(), str(info)
    assert text_records(ly, top) == texts
    output = a.output/'decap_pdn_core.gds'; ly.write(str(output))
    saved = pya.Layout(); saved.read(str(output))
    assert text_records(saved, saved.top_cell()) == texts
    for info in ly.layer_infos():
        assert (region(ly, top, info)^region(saved, saved.top_cell(), info)).is_empty()
    result = dict(status='passed scoped native decap-to-ring PDN connectivity', GDS_sha256=sha(output),
                  parent_GDS_sha256=sha(source), plan_sha256=sha(a.plan), script_sha256=sha(Path(__file__)),
                  placement_sha256=sha(a.placement/'analysis.json'), KLayout=pya.__version__,
                  decaps=4662, M1_M2_pin_pairs_connected_to_correct_ring=9324,
                  original_components_connected=464, spines=len(plan['spines']), redundant_arrays=len(arrays),
                  no_foreign_native_contact='passed', exact_additive_geometry_text_saved_roundtrip='passed',
                  not_run=['stock main/maximal DRC', 'macro and pad feeds', 'global PDN current/IR/EM',
                           'fullchip LVS/PEX', 'electrical adoption'],
                  not_applicable=['complete chip qualification from decap feeder connectivity alone'])
    (a.output/'analysis.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))
    faulthandler.cancel_dump_traceback_later()


if __name__ == '__main__':
    main()
