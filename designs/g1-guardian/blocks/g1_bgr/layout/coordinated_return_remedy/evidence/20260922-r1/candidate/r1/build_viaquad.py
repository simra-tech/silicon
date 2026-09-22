#!/usr/bin/env python3
"""Isolated four-cut common-return routing candidate derived from passed r5."""
import argparse
import collections
import copy
import json
import os
from pathlib import Path
import sys
import pya

HERE = Path(__file__).resolve().parent
CLOSURE = HERE.parent / 'coordinated_full_closure'
sys.path.insert(0, str(CLOSURE))
from build_assembly import Assembly, PAIRS, region, sha, dump, SOURCE, ROOT


def texts(top):
    result = []
    ly = top.layout()
    for index in ly.layer_indices():
        info = ly.get_info(index)
        iterator = top.begin_shapes_rec(index)
        while not iterator.at_end():
            if iterator.shape().is_text():
                text = iterator.shape().text
                result.append((info.layer, info.datatype, text.string, str(iterator.trans() * text.trans)))
            iterator.next()
    return sorted(result)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    assert args.output.is_dir() and not (args.output / 'bank.gds').exists()
    bulk = Path(os.environ['G1_RESULTS_ROOT'])
    base = bulk / 'bgr-assembly-20260922-r5'
    via_path = bulk / 'bgr-return-tree-vias-20260922-r1/summary.json'
    old_ledger = ROOT / 'build/scratch/bgr-hbt-fullbank-20260922-r2/route_ledger.json'
    pack_path = ROOT / 'designs/g1-guardian/review/audits/coordinated-bbox-pack-586-20260922-r1.json'
    assert sha(base / 'bank.gds') == '0083eabb0f730b2cb27eeb0bda1ac8f173a21e03e2aa5a329b01ef5cba21b3ed'
    assert sha(base / 'bank.cdl') == '7f8e6e8c606b1e04321c5c9b20e94610d34d42055c8818d03d79352b3a4710b2'
    assert sha(SOURCE) == '586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b'
    paths = [base / name for name in ('bank.gds', 'bank.cdl', 'preparation.json', 'routing.json', 'star_cuts.json')]
    paths += [via_path, old_ledger, pack_path, SOURCE, Path(__file__), CLOSURE / 'build_assembly.py']
    bindings = {str(p): sha(p) for p in paths}
    prep = json.loads((base / 'preparation.json').read_text())
    assert prep['status'] == 'passed preparation'
    via = json.loads(via_path.read_text())
    assert via['status'] == 'passed partial wire-plus-ledger-via sensitivity; not full extracted RC or IR qualification'
    old = json.loads(old_ledger.read_text())
    star = copy.deepcopy(old['star_interfaces'])
    native_boxes = pya.Region()
    pack = json.loads(pack_path.read_text())
    for device in pack['BGR_devices']:
        native_boxes.insert(pya.DBox(*device['bbox_um']).to_itype(.001))
    assert len(pack['BGR_devices']) == 1036
    ly = pya.Layout()
    ly.read(str(base / 'bank.gds'))
    top = ly.top_cell()
    before = {(ly.get_info(i).layer, ly.get_info(i).datatype): region(top, i) for i in ly.layer_indices()}
    original_texts = texts(top)
    selected = [a for a in via['arrays'] if ':trunk_base:' in a['id'] or ':row_' in a['id'] or ':star_interface:' in a['id']]
    assert len(selected) == 36
    removed = collections.defaultdict(pya.Region)
    added = collections.defaultdict(pya.Region)
    sites = set()
    changes = []
    for array in selected:
        role, layer = array['role'], array['layer']
        x, y = array['center_dbu']
        assert x == int(x) and y == int(y)
        x, y = int(x), int(y)
        sites.add((role, x, y))
        old_boxes = [old['vias'][i]['bbox_dbu'] for i in array['cut_indices']]
        assert len(old_boxes) == 2
        for box in old_boxes:
            removed[layer].insert(pya.Box(*box))
        new_boxes = [[x + dx - 95, y + dy - 95, x + dx + 95, y + dy + 95]
                     for dx in (-210, 210) for dy in (-210, 210)]
        for box in new_boxes:
            added[layer].insert(pya.Box(*box))
        landing = pya.Box(x - 360, y - 360, x + 360, y + 360)
        added['M3'].insert(landing)
        if ':star_interface:' in array['id']:
            assert star[role] == old_boxes
            star[role] = new_boxes
        changes.append(dict(array_id=array['id'], role=role, layer=layer, removed_boxes=old_boxes,
                            added_boxes=new_boxes, M3_landing=[landing.left, landing.bottom, landing.right, landing.top]))
    assert len(sites) == 20
    assert sum(len(c['removed_boxes']) for c in changes) == 72 and sum(len(c['added_boxes']) for c in changes) == 144
    for layer in ('Via2', 'Via3'):
        assert (removed[layer] - before[PAIRS[layer]]).is_empty()
    native_errors = {}
    for name in ('Via2', 'Via3', 'M3'):
        delta = added[name] + removed[name]
        overlap = delta & native_boxes
        if not overlap.is_empty():
            native_errors[name] = overlap.area()
    assert not native_errors
    top.flatten(-1, False)
    for name in ('Via2', 'Via3'):
        index = ly.layer(*PAIRS[name])
        new_region = (before[PAIRS[name]] - removed[name]) + added[name]
        top.shapes(index).clear()
        for polygon in new_region.each():
            top.shapes(index).insert(polygon)
    for polygon in added['M3'].merged().each():
        top.shapes(ly.layer(*PAIRS['M3'])).insert(polygon)
    expected = dict(before)
    for name in ('Via2', 'Via3'):
        expected[PAIRS[name]] = (before[PAIRS[name]] - removed[name]) + added[name]
    expected[PAIRS['M3']] = before[PAIRS['M3']] + added['M3']
    assert all((value ^ region(top, ly.layer(*pair))).is_empty() for pair, value in expected.items())
    assert texts(top) == original_texts
    metal = {name: region(top, ly.layer(*PAIRS[name])) for name in ('M2', 'M3', 'M4')}
    enclosure_errors = []
    for change in changes:
        ends = ('M2', 'M3') if change['layer'] == 'Via2' else ('M3', 'M4')
        for box in change['added_boxes']:
            for name in ends:
                if not (pya.Region(pya.Box(*box)).sized(55) - metal[name]).is_empty():
                    enclosure_errors.append(dict(change=change['array_id'], metal=name, via=box))
    assert not enclosure_errors
    ly.write(str(args.output / 'bank.gds'))
    (args.output / 'bank.cdl').write_bytes((base / 'bank.cdl').read_bytes())
    saved = pya.Layout()
    saved.read(str(args.output / 'bank.gds'))
    saved_top = saved.top_cell()
    assert all((value ^ region(saved_top, saved.layer(*pair))).is_empty() for pair, value in expected.items())
    assert texts(saved_top) == original_texts
    graph = Assembly(args.output)
    graph.probes = json.loads((base / 'routing.json').read_text())['source_probes']
    graph.star = star
    full = graph.graph(saved_top)
    dump(args.output / 'terminal_graph.json', full)
    cuts = [graph.graph(saved_top, (role,)) for role in star]
    cuts += [graph.graph(saved_top, tuple(star)), graph.graph(saved_top, precision=True)]
    dump(args.output / 'star_cuts.json', cuts)
    # Explicit other-role spacing for new M3 landing area outside approved star hub.
    role_violations = []
    allowed_star = pya.Region(pya.Box(13000, 14400, 17800, 16900))
    for role, x, y in sorted(sites):
        new_pad = pya.Region(pya.Box(x - 360, y - 360, x + 360, y + 360)) - allowed_star
        for route in old['routes']:
            if route['layer'] != 'M3' or route['role'] == role:
                continue
            if not (new_pad.sized(300) & pya.Region(pya.Box(*route['bbox_dbu']))).is_empty():
                role_violations.append(dict(site=[role, x, y], other_role=route['role'], bbox=route['bbox_dbu']))
    offgrid = []
    for index in saved.layer_indices():
        for polygon in region(saved_top, index).each():
            for point in polygon.each_point_hull():
                if point.x % 5 or point.y % 5:
                    offgrid.append([point.x, point.y])
    checks = dict(source1036=True, CDL_byte_identity=sha(args.output / 'bank.cdl') == sha(base / 'bank.cdl'),
                  all_native_bbox_delta_zero=not native_errors, exact_changed_shape_ledger=True, all_texts_preserved=True,
                  saved_layer_XOR=True, terminal_graph=full['status'] == 'passed',
                  seven_star_cuts=len(cuts) == 7 and all(c['status'] == 'passed' for c in cuts),
                  via_enclosures=not enclosure_errors, other_role_clearance=not role_violations, grid=not offgrid,
                  bounds=(pya.Region(saved_top.bbox()) - pya.Region(pya.Box(0, 0, 420000, 354000))).is_empty())
    dump(args.output / 'changed_shapes.json', dict(status='passed', sites=20, arrays=36, removed_cuts=72,
          added_cuts=144, native_bbox_XOR_area=0, changes=changes, star_interfaces=star))
    dump(args.output / 'preparation.json', dict(status='passed preparation' if all(checks.values()) else 'failed preparation',
          checks=checks, inputs=bindings, source_count=1036, source_ports=prep['source_ports'], source_nets=prep['source_nets'],
          source_terminal_probes=len(graph.probes), role_clearance_findings=role_violations, offgrid=offgrid,
          gds_sha256=sha(args.output / 'bank.gds'), cdl_sha256=sha(args.output / 'bank.cdl'),
          stock_PEX_electrical='not run', adoption='not run', seed='not applicable'))
    print(json.dumps(checks, indent=2))
    return 0 if all(checks.values()) else 1


if __name__ == '__main__':
    raise SystemExit(main())
