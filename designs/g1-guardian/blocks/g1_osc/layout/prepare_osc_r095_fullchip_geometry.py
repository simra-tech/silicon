#!/usr/bin/env python3
"""Prepare an isolated full-chip R0.95 candidate; never adopt production geometry.

Pinned KLayout: -b -r this.py -rd chip=<current.gds> -rd baseline=<macro.gds>
  -rd candidate=<new-bare-macro.gds> -rd out=<new.gds> -rd report=<new.json>
The existing full-chip pure-fill cells and removal of internal OSC labels are
preserved. Full-chip DRC, density, antenna, LVS and electrical checks are still
required after this structural preparation.
"""
import hashlib
import json
import re
from pathlib import Path

import pya

CHIP_SHA = '3e3634389aff5126d0f55f6814466ad179f6d1280e9152c62a07ab5ea3d105bf'
BASE_SHA = '3f188401c91405d7d9538f976fa29bc0a6d34ca04dfd245eb260e72ac4f34e3b'
NEW_SHA = '411d52f74d0515895b4616b37af466f65481419ff0137ddc16970107851c6827'
TARGET = '__rz_port_text_032_retained_g1_osc'
FILL = {(50, 22), (67, 22)}
CHILD_FILL = {(1, 22), (5, 22), (8, 22), (10, 22), (30, 22)}
INTERNAL = {'va', 'vb', 'vbn', 'vth'}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path, digest, name):
    assert sha(path) == digest, 'Unexpected input geometry'
    layout = pya.Layout()
    layout.read(str(path))
    assert layout.dbu == .001
    cell = layout.cell(name)
    assert cell is not None, 'Missing macro'
    assert not any(s.has_prop_id() for i in layout.layer_indexes()
                   for s in cell.shapes(i).each()), 'Unexpected macro shape properties'
    return layout, cell


def instances(cell):
    # GDS cell indexes may be reassigned on read; child names and transforms
    # are the stable identity. No instance is created, deleted or moved.
    return sorted(re.sub(r'^cell_index=\d+', 'child=' + i.cell.name, str(i))
                  for i in cell.each_inst())


def check_fill_children(layout, cell, allowed):
    children = {}
    for instance in cell.each_inst():
        assert not instance.has_prop_id(), 'Unexpected instance properties'
        child = instance.cell
        assert not list(child.each_inst()), 'Unexpected nested fill hierarchy'
        assert not child.properties(), 'Unexpected fill cell properties'
        populated = set()
        for layer, index in layers(layout).items():
            for shape in child.shapes(index).each():
                assert layer in allowed and not shape.has_prop_id()
                assert shape.is_box() or shape.is_polygon(), 'Unexpected fill shape'
                populated.add(layer)
        assert populated, 'Empty fill child'
        children[child.name] = sorted(populated)
    return children


def layers(layout):
    return {(layout.get_info(i).layer, layout.get_info(i).datatype): i
            for i in layout.layer_indexes()}


def ignored_text(shape, layer):
    return layer == (50, 25) and shape.is_text() and shape.text.string in INTERNAL


def signature(layout, cell):
    rows = []
    for layer, index in sorted(layers(layout).items()):
        shapes = sorted(str(s) for s in cell.shapes(index).each())
        if shapes:
            rows.append((layer, shapes))
    value = [rows, instances(cell)]
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def normalized_matches(left_layout, left, right_layout, right, normalize_left, exact_types=False):
    a, b = layers(left_layout), layers(right_layout)
    removed = []
    for layer in sorted(set(a) | set(b)):
        aa = list(left.shapes(a[layer]).each()) if layer in a else []
        bb = list(right.shapes(b[layer]).each()) if layer in b else []
        if normalize_left:
            removed.extend(s.text.string for s in aa if ignored_text(s, layer))
            aa = [] if layer in FILL else [s for s in aa if not ignored_text(s, layer)]
        ra, rb = pya.Region(), pya.Region()
        for shapes, region in ((aa, ra), (bb, rb)):
            for shape in shapes:
                if not shape.is_text():
                    assert shape.is_box() or shape.is_polygon() or shape.is_path()
                    region.insert(shape.polygon)
        assert (ra ^ rb).is_empty(), ('Unexpected nontext geometry', layer)
        assert sorted(str(s.text) for s in aa if s.is_text()) == sorted(
            str(s.text) for s in bb if s.is_text()), ('Unexpected labels', layer)
        if exact_types:
            assert sorted(str(s) for s in aa) == sorted(str(s) for s in bb), (
                'Unexpected shape type, count or payload', layer)
    if normalize_left:
        assert sorted(removed) == sorted(INTERNAL), 'Expected exactly four removed internal labels'


def prepare(chip, baseline, candidate, out, report):
    paths = [Path(p).resolve() for p in (chip, baseline, candidate, out, report)]
    assert len(set(paths)) == 5 and not paths[3].exists() and not paths[4].exists()
    whole, target = read(chip, CHIP_SHA, TARGET)
    old_layout, old = read(baseline, BASE_SHA, 'g1_osc')
    new_layout, new = read(candidate, NEW_SHA, 'g1_osc')
    assert not list(new.each_inst()), 'Candidate must contain only direct shapes'
    retained_fill = check_fill_children(whole, target, CHILD_FILL)
    check_fill_children(old_layout, old, CHILD_FILL | FILL)
    assert len(retained_fill) == 8
    target_instances = instances(target)
    normalized_matches(old_layout, old, whole, target, True, exact_types=True)
    assert old.bbox() == new.bbox() == target.bbox()
    before = {c.name: signature(whole, c) for c in whole.each_cell() if c.name != TARGET}
    top_before = sorted((c.name, str(c.bbox())) for c in whole.top_cells())
    target_layers, new_layers = layers(whole), layers(new_layout)
    assert set(new_layers) <= set(target_layers), 'Unexpected new layer'
    for index in target_layers.values():
        target.shapes(index).clear()
    for layer, index in new_layers.items():
        if layer in FILL:
            continue
        dest = target.shapes(target_layers[layer])
        for shape in new.shapes(index).each():
            if ignored_text(shape, layer):
                continue
            if shape.is_text():
                dest.insert(shape.text)
            elif shape.is_box():
                dest.insert(shape.box)
            elif shape.is_path():
                dest.insert(shape.path)
            elif shape.is_simple_polygon():
                dest.insert(shape.simple_polygon)
            else:
                assert shape.is_polygon()
                dest.insert(shape.polygon)
    normalized_matches(new_layout, new, whole, target, True, exact_types=True)
    assert instances(target) == target_instances
    assert before == {c.name: signature(whole, c) for c in whole.each_cell() if c.name != TARGET}
    assert top_before == sorted((c.name, str(c.bbox())) for c in whole.top_cells())
    whole.write(str(out))
    # Re-read the emitted artifact instead of relying only on in-memory checks.
    emitted = pya.Layout()
    emitted.read(str(out))
    assert emitted.dbu == whole.dbu
    normalized_matches(new_layout, new, emitted, emitted.cell(TARGET), True, exact_types=True)
    assert instances(emitted.cell(TARGET)) == target_instances
    assert check_fill_children(emitted, emitted.cell(TARGET), CHILD_FILL) == retained_fill
    assert before == {c.name: signature(emitted, c) for c in emitted.each_cell() if c.name != TARGET}
    assert top_before == sorted((c.name, str(c.bbox())) for c in emitted.top_cells())
    assert sha(chip) == CHIP_SHA and sha(baseline) == BASE_SHA and sha(candidate) == NEW_SHA
    result = dict(status='prepared isolated geometry; full-chip physical/electrical checks not run',
                  chip_sha256=CHIP_SHA, baseline_macro_sha256=BASE_SHA,
                  candidate_macro_sha256=NEW_SHA, output_sha256=sha(out),
                  generator_sha256=sha(__file__), target_cell=TARGET,
                  unchanged_other_cells=len(before), unchanged_top_bboxes=top_before,
                  unchanged_target_fill_instances=len(target_instances),
                  retained_fill_children=retained_fill,
                  scope='Only normalized OSC macro geometry replaced; other cells and text/fill cleanup preserved',
                  fullchip_drc='not run', density='not run', antenna='not run',
                  fullchip_lvs='not run', electrical='not run', production_adoption='not run')
    with Path(report).open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    prepare(*(globals()[name] for name in ('chip', 'baseline', 'candidate', 'out', 'report')))
