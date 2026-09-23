#!/usr/bin/env python3
"""Source-bound five-micrometre outward pad movement, no circuit changes."""
import argparse
import collections
import copy
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import pya

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from place_closed_analog import region, sha, text_records

PARENT_SHA = '4d3907c50f07946ef27a6d53402cf319264499a21379d2de80e9c4f1adbae299'
TSV_SHA = '43be000677b631983ae7f159d988cc6d1654679caa436e6ab3da62b1df2452fd'
DEF_SHA = '7e00861c04e17d36c0f00f9ce88e152fbee04cb88ebc0c07e07a38045dc84697'
TOP = 'placed_core_NOT_CONNECTED_FULLCHIP'
PAD = 'retained_fullchip_bondpad_70x70_tm1'


def box_values(box):
    return [box.left, box.bottom, box.right, box.top]


def signature(layout):
    """Exact local shapes and instance transforms, including non-polygon objects."""
    result = {}
    for cell in layout.each_cell():
        shapes = [(str(layout.get_info(k)), sorted(str(s) for s in cell.shapes(k).each()))
                  for k in layout.layer_indexes() if not cell.shapes(k).is_empty()]
        # Cell indexes may change on serialization; compare named instance geometry.
        instances = sorted((i.cell.name, str(i.cplx_trans), str(i.a), str(i.b), i.na, i.nb)
                           for i in cell.each_inst())
        value = json.dumps([sorted(shapes), instances], separators=(',', ':'))
        result[cell.name] = hashlib.sha256(value.encode()).hexdigest()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('parent', 'roundtrip', 'prepared', 'output'):
        parser.add_argument('--' + key, type=Path, required=True)
    a = parser.parse_args()
    assert not a.output.exists() and pya.__version__ == '0.30.9'
    assert len(os.sched_getaffinity(0)) == 1
    assert sha(a.parent) == PARENT_SHA and sha(a.roundtrip) == TSV_SHA
    old_def = a.prepared / 'g1_chip_top_unrouted.def'
    assert sha(old_def) == DEF_SHA
    a.output.mkdir(parents=True)
    (a.output / 'source.py').write_bytes(Path(__file__).read_bytes())
    rows = [s.split('\t') for s in a.roundtrip.read_text().splitlines()]
    source_pads = {tuple(map(int, r[4:8])): r for r in rows
                   if r[0] == 'INST' and r[1].startswith('IO_BOND_')}
    source_nets = {r[2]: r[1] for r in rows if r[0] == 'CONN' and r[2].startswith('IO_BOND_')}
    assert len(source_pads) == len(source_nets) == 24 and len(set(source_nets.values())) == 22
    ly = pya.Layout(); ly.read(str(a.parent)); top = ly.top_cell()
    assert top.name == TOP and ly.dbu == .001 and top.bbox() == pya.Box(0, 0, 1414000, 1414000)
    original_signature = signature(ly)
    original_texts = text_records(ly, top)
    pad = ly.cell(PAD)
    assert pad and not list(pad.each_inst())
    used = {(ly.get_info(k).layer, ly.get_info(k).datatype) for k in ly.layer_indexes()
            if not pad.shapes(k).is_empty()}
    assert used == {(126, 0), (134, 0), (133, 0), (9, 0), (41, 0)}
    assert all(not s.is_text() for k in ly.layer_indexes() for s in pad.shapes(k).each())
    before = {layer: region(ly, top, pya.LayerInfo(layer, 0)) for layer, _ in used}
    old_pad = {layer: pya.Region() for layer, _ in used}
    new_pad = {layer: pya.Region() for layer, _ in used}
    overlay = ly.create_cell('bondpad_outward_5um_retained_metal')
    moves = []; moved_instances = []
    for inst in list(top.each_inst()):
        if inst.cell.name != PAD:
            continue
        old_box = box_values(inst.bbox()); record = source_pads[tuple(old_box)]
        x, y = inst.bbox().center().x, inst.bbox().center().y
        dx, dy = (-5000, 0) if x < 200000 else (5000, 0) if x > 1200000 else (0, -5000) if y < 200000 else (0, 5000)
        assert x < 200000 or x > 1200000 or y < 200000 or y > 1200000
        shift = pya.ICplxTrans(1, 0, False, dx, dy)
        old_transform = inst.cplx_trans
        for layer, _ in sorted(used):
            r = region(ly, pad, pya.LayerInfo(layer, 0)).transformed(old_transform)
            old_pad[layer].insert(r); new_pad[layer].insert(r.transformed(shift))
            if layer in (126, 134):
                # Retain exact native frame, NOT its filled bounding rectangle.
                overlay.shapes(ly.layer(layer, 0)).insert(r)
        inst.cplx_trans = shift * old_transform
        moved_instances.append((inst, old_transform))
        moves.append(dict(instance=record[1], logical_net=source_nets[record[1]],
                          orientation=record[3], old_bbox_dbu=old_box,
                          new_bbox_dbu=box_values(inst.bbox()), shift_dbu=[dx, dy],
                          old_opening_center_um=[x / 1000, y / 1000],
                          new_opening_center_um=[(x + dx) / 1000, (y + dy) / 1000]))
    assert len(moves) == 24
    bridge_instance = top.insert(pya.CellInstArray(overlay.cell_index(), pya.Trans()))
    deltas = {}
    for layer, _ in sorted(used):
        actual = region(ly, top, pya.LayerInfo(layer, 0))
        expected = before[layer] | new_pad[layer] if layer in (126, 134) else (before[layer] - old_pad[layer]) | new_pad[layer]
        assert (actual ^ expected).is_empty(), layer
        added, removed = actual - before[layer], before[layer] - actual
        if layer in (126, 134):
            assert removed.is_empty()
        assert (new_pad[layer] - pya.Region(pya.Box(0, 0, 1414000, 1414000))).is_empty()
        deltas[str(layer) + '/0'] = dict(added_area_um2=added.area() * 1e-6,
                                        removed_area_um2=removed.area() * 1e-6,
                                        new_pad_area_um2=new_pad[layer].area() * 1e-6)
    after_sig = signature(ly)
    assert all(after_sig[name] == value for name, value in original_signature.items() if name != TOP)
    assert top.bbox() == pya.Box(0, 0, 1414000, 1414000)
    assert text_records(ly, top) == original_texts
    overlay_geometry = {layer: region(ly, overlay, pya.LayerInfo(layer, 0)) for layer in (126, 134)}
    gds = a.output / 'pad_outward_native.gds'; ly.write(str(gds))
    # Exact inverse of declared movement and bridge addition, not a comparison
    # against a separately regenerated approximation.
    for inst, old_transform in moved_instances:
        inst.cplx_trans = old_transform
    bridge_instance.delete(); ly.delete_cell(overlay.cell_index())
    assert signature(ly) == original_signature
    reread = pya.Layout(); reread.read(str(gds))
    serialized_signature = signature(reread)
    storage_differences = [name for name in after_sig if serialized_signature.get(name) != after_sig[name]]
    assert set(serialized_signature) == set(after_sig)
    # GDS serializes Region holes as cutline polygons. This exception applies
    # only to the newly inserted bridge cell, never to any native cell.
    assert set(storage_differences) <= {'bondpad_outward_5um_retained_metal'}, storage_differences
    for layer in (126, 134):
        assert (region(reread, reread.cell('bondpad_outward_5um_retained_metal'), pya.LayerInfo(layer, 0)) ^ overlay_geometry[layer]).is_empty()
    by_instance = {m['instance']: m for m in moves}
    by_center = {tuple(round(x * 1000) for x in m['old_opening_center_um']): m for m in moves}
    original_def = old_def.read_text(); new_def = original_def
    replacements = []
    for name, m in sorted(by_instance.items()):
        pat = r'(^\s*- ' + re.escape(name) + r' bondpad_70x70_tm1 \+ FIXED \( )(\d+) (\d+)( \) \S+ ;$)'
        matches = list(re.finditer(pat, new_def, re.M)); assert len(matches) == 1
        match = matches[0]; dx, dy = m['shift_dbu']
        old, new = match[0], match[1] + str(int(match[2]) + dx) + ' ' + str(int(match[3]) + dy) + match[4]
        replacements.append((old, new)); new_def = new_def.replace(old, new, 1)
    pinblock, = re.findall(r'^PINS 22 ;\n(.*?)^END PINS$', new_def, re.M | re.S)
    count = [0]
    def shift_port(match):
        xy = (int(match[1]), int(match[2])); m = by_center[xy]; count[0] += 1
        return '+ FIXED ( %d %d ) N' % (xy[0] + m['shift_dbu'][0], xy[1] + m['shift_dbu'][1])
    new_pinblock = re.sub(r'\+ FIXED \( (\d+) (\d+) \) N', shift_port, pinblock)
    assert count[0] == 24
    new_def = new_def.replace(pinblock, new_pinblock, 1)
    reverse = new_def.replace(new_pinblock, pinblock, 1)
    for old, new in replacements:
        assert reverse.count(new) == 1
        reverse = reverse.replace(new, old, 1)
    assert reverse.encode() == old_def.read_bytes()
    prepared = a.output / 'placement_projection'; prepared.mkdir()
    new_def_path = prepared / old_def.name; new_def_path.write_text(new_def)
    old_meta = json.loads((a.prepared / 'analysis.json').read_text()); meta = copy.deepcopy(old_meta)
    for change in meta['changes']:
        if change['instance'] in by_instance:
            m = by_instance[change['instance']]
            change['new'][0] += m['shift_dbu'][0]; change['new'][1] += m['shift_dbu'][1]
    meta.update(DEF_sha256=sha(new_def_path), pad_parent_DEF_sha256=DEF_SHA,
                pad_scope='Derived unrouted placement/interface projection only; not final routed ODB or new signal RC',
                pad_movement=moves, original_preparation_metadata_sha256=sha(a.prepared / 'analysis.json'))
    (prepared / 'analysis.json').write_text(json.dumps(meta, indent=2) + '\n')
    with (a.output / 'bondmap_delta.csv').open('x', newline='') as f:
        writer = csv.writer(f); writer.writerow(['instance', 'logical_pin', 'old_x_um', 'old_y_um', 'new_x_um', 'new_y_um', 'dx_um', 'dy_um'])
        for m in sorted(moves, key=lambda r: r['instance']):
            writer.writerow([m['instance'], m['logical_net'], *m['old_opening_center_um'], *m['new_opening_center_um'], *[v / 1000 for v in m['shift_dbu']]])
    result = dict(status='passed exact outward pad geometry and placement delta', GDS_sha256=sha(gds),
                  parent_GDS_sha256=PARENT_SHA, source_roundtrip_sha256=TSV_SHA,
                  script_sha256=sha(Path(__file__)), original_DEF_sha256=DEF_SHA,
                  derived_DEF_sha256=sha(new_def_path), KLayout=pya.__version__, DBU_um=ly.dbu,
                  die_bbox_dbu=[0, 0, 1414000, 1414000], pad_moves=sorted(moves, key=lambda r: r['instance']),
                  physical_pad_count=24, logical_pin_count=22, layer_delta=deltas,
                  serialized_bridge_storage_differences=storage_differences,
                  checks=dict(exact_inverse_all_cell_signatures='passed', unchanged_all_other_cells='passed',
                              all_texts_unchanged='passed', serialized_candidate_exact='passed',
                              exact_def_inverse='passed', native_metal_removal_zero='passed',
                              all_moved_shapes_within_die='passed'),
                  not_run=['actual whole-chip connectivity', 'stock main/maximal/antenna/density',
                           'final routed ODB pad placement update', 'shifted pad RC', 'bonding/measured continuity'],
                  not_applicable=['model/rule/source-device changes', 'IO marker/dummy remedy adoption'])
    (a.output / 'analysis.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
