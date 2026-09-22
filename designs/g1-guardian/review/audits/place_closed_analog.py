#!/usr/bin/env python3
"""Place exact closed analog blocks in r4; diagnostic ring preview, not fullchip."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import pya

HERE = Path(__file__).resolve().parent
DESIGN = HERE.parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def region(layout, cell, info):
    # Explicit insertion materializes lazy recursive geometry before comparison.
    result = pya.Region()
    for polygon in pya.Region(cell.begin_shapes_rec(layout.layer(info))).each():
        result.insert(polygon)
    return result.merged()


def text_records(layout, cell):
    records = []
    for index in layout.layer_indexes():
        iterator = cell.begin_shapes_rec(index)
        while not iterator.at_end():
            shape = iterator.shape()
            if shape.is_text():
                displacement = shape.text.trans.disp
                point = iterator.trans() * pya.Point(displacement.x, displacement.y)
                records.append((str(layout.get_info(index)), shape.text.string, point.x, point.y))
            iterator.next()
    return sorted(records)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists() and len(os.sched_getaffinity(0)) == 1
    assert pya.__version__ == '0.30.9'
    pack_path = HERE / 'coordinated-bbox-pack-20260922-r4.json'
    ring_path = HERE / 'fit-ring-layer-screen-20260922-r2.json'
    pack = json.loads(pack_path.read_text())
    ring = json.loads(ring_path.read_text())['actual_core_ring_conductors']
    targets = {r['name']: r for r in pack['macros']}
    assert pack['ring_proposed_die_side_um'] == 1414
    inputs = [
        ('g1_bgr_candidate', DESIGN / 'blocks/g1_bgr/layout/coordinated_full_closure/evidence/20260922-r1/r5/bank.gds',
         '0083eabb0f730b2cb27eeb0bda1ac8f173a21e03e2aa5a329b01ef5cba21b3ed', 420, 354),
        ('g1_sense_candidate', DESIGN / 'blocks/g1_sense/layout/coordinated_gm4/assembly-evidence-20260922-r1/sense-fullassembly-20260922-r5/g1_sense_physical.gds',
         '6609a77884a0009924422bf9871ea699e2393c8988412e1b000057cf3448beda', 385, 240),
    ]
    args.output.mkdir(parents=True)
    layout = pya.Layout()
    layout.dbu = .001
    top = layout.create_cell('closed_analog_placement_NOT_FULLCHIP')
    rings = {}
    for row in ring:
        x1, y1, x2, y2 = row['bbox_um']
        if row['layer'] == 126:
            y2 += 64
            if x1 > 986:
                x1 += 64
                x2 += 64
        else:
            x2 += 64
            if y1 > 986:
                y1 += 64
                y2 += 64
        box = pya.DBox(x1, y1, x2, y2).to_itype(layout.dbu)
        rings.setdefault(row['layer'], pya.Region()).insert(box)
        top.shapes(layout.layer(row['layer'], 0)).insert(box)
    records = []
    errors = []
    for name, path, expected, width, height in inputs:
        assert sha(path) == expected
        source = pya.Layout()
        source.read(str(path))
        assert source.dbu == layout.dbu
        expected_cell = 'g1_bgr' if name == 'g1_bgr_candidate' else 'g1_sense_physical'
        cell = source.cell(expected_cell)
        assert cell is not None and cell in source.top_cells()
        auxiliary_roots = [c.name for c in source.top_cells() if c.name != expected_cell]
        assert auxiliary_roots == ([] if name == 'g1_bgr_candidate' else ['resistor_bank_view'])
        target = targets[name]
        x, y, right, upper = target['bbox_um']
        rotated = target['orientation'] == 'R90'
        assert (right-x, upper-y) == ((height, width) if rotated else (width, height))
        transform = pya.Trans(pya.Trans.R90 if rotated else pya.Trans.R0,
                              round((x+height if rotated else x)/layout.dbu), round(y/layout.dbu))
        # Local reservation origin is (0,0); do not normalize away genuine .67um margins.
        copy = layout.create_cell(name)
        copy.copy_tree(cell)
        assert text_records(source, cell) == text_records(layout, copy)
        top.insert(pya.CellInstArray(copy.cell_index(), transform))
        bounds = pya.Box(0, 0, round(width/layout.dbu), round(height/layout.dbu))
        if not (pya.Region(cell.bbox()) - pya.Region(bounds)).is_empty():
            errors.append(name + ': geometry exceeds local reservation')
        layers = []
        for info in source.layer_infos():
            original = region(source, cell, info)
            copied = region(layout, copy, info)
            xor = original ^ copied
            if not xor.is_empty():
                errors.append(name + ': copy XOR ' + str(info))
            moved = original.transformed(transform)
            same_layer_ring = rings.get(info.layer, pya.Region()) if info.datatype == 0 else pya.Region()
            overlap = moved & same_layer_ring
            near = moved & same_layer_ring.sized(5000)
            if not overlap.is_empty():
                errors.append(name + ': ring overlap ' + str(info))
            layers.append(dict(layer=info.layer, datatype=info.datatype,
                               area_um2=original.area()*layout.dbu**2,
                               copy_xor_um2=xor.area()*layout.dbu**2,
                               ring_overlap_um2=overlap.area()*layout.dbu**2,
                               ring_5um_margin_overlap_um2=near.area()*layout.dbu**2))
        labels = []
        for index in cell.layout().layer_indexes():
            info = source.get_info(index)
            iterator = cell.begin_shapes_rec(index)
            while not iterator.at_end():
                shape = iterator.shape()
                if shape.is_text():
                    displacement = shape.text.trans.disp
                    # Translation acts on Point, not on Vector/Trans.disp.
                    position = transform * (iterator.trans() * pya.Point(displacement.x, displacement.y))
                    labels.append(dict(text=shape.text.string, layer=str(info),
                                       x_um=position.x*layout.dbu, y_um=position.y*layout.dbu))
                iterator.next()
        external = []
        port_layer = 30 if name == 'g1_bgr_candidate' else 50
        for shape in cell.shapes(source.layer(port_layer, 25)).each():
            if shape.is_text():
                d = shape.text.trans.disp
                local = pya.Point(d.x, d.y)
                moved = transform * local
                assert transform.inverted() * moved == local
                assert x <= moved.x*layout.dbu <= right and y <= moved.y*layout.dbu <= upper
                external.append(dict(name=shape.text.string, layer=port_layer,
                                     local_um=[d.x*layout.dbu, d.y*layout.dbu],
                                     chip_um=[moved.x*layout.dbu, moved.y*layout.dbu]))
        assert len(external) == 9 and len({r['name'] for r in external}) == 9
        records.append(dict(name=name, source_sha256=expected, source_cell=cell.name, excluded_auxiliary_roots=auxiliary_roots,
                            local_bbox_um=[v*layout.dbu for v in (cell.bbox().left, cell.bbox().bottom, cell.bbox().right, cell.bbox().top)],
                            reservation=target, transform=str(transform), layers=layers,
                            external_ports=external, transformed_labels=labels))
    output = args.output / 'closed_analog_placement.gds'
    layout.write(str(output))
    reread = pya.Layout()
    reread.read(str(output))
    assert len(reread.top_cells()) == 1
    assert text_records(layout, top) == text_records(reread, reread.top_cell())
    for info in layout.layer_infos():
        assert (region(layout, top, info) ^ region(reread, reread.top_cell(), info)).is_empty()
    result = dict(status='passed scoped placement' if not errors else 'failed scoped placement',
                  errors=errors, script_sha256=sha(Path(__file__)), pack_sha256=sha(pack_path),
                  ring_inventory_sha256=sha(ring_path), GDS_sha256=sha(output), KLayout=pya.__version__,
                  source_geometry_copy_and_saved_roundtrip='passed', blocks=records,
                  ring='Only eight extrapolated drawing rectangles, no vias/feeds; not a legal connected ring.',
                  not_run=['fullchip DRC/LVS/antenna/density', 'decap placement and connectivity',
                           'signal and power routing', 'current/IR', 'padframe and sealring', 'PEX and electrical adoption'],
                  not_applicable=['fullchip signoff from a two-block placement preview'])
    (args.output / 'analysis.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k != 'blocks'}, indent=2))
    raise SystemExit(bool(errors))


if __name__ == '__main__':
    main()
