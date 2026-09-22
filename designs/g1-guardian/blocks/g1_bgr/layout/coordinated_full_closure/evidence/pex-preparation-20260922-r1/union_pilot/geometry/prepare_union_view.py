#!/usr/bin/env python3
"""Exact area-union representation only, with immutable golden input."""
import argparse
import hashlib
import json
from pathlib import Path

import pya

from prepare_pex_view import texts


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def statistics(cell, layer):
    count = vertices = largest = 0
    iterator = cell.begin_shapes_rec(layer)
    while not iterator.at_end():
        shape = iterator.shape()
        if not shape.is_text():
            assert shape.prop_id == 0, 'Nonzero shape properties require separate representation review'
            polygon = shape.polygon
            n = polygon.num_points()
            count += 1
            vertices += n
            largest = max(largest, n)
        iterator.next()
    return {'polygons': count, 'vertices': vertices, 'largest_vertices': largest}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--cell', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists() and pya.__version__ == '0.30.9'
    args.output.mkdir()
    report = {'status': 'running', 'source_sha256': sha(args.input), 'script_sha256': sha(Path(__file__)),
              'semantics': 'Exact area union only; all text unchanged; no geometry filtering, rule/model change, or source edit'}
    def save():
        (args.output / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
    save()
    try:
        layout = pya.Layout()
        layout.read(str(args.input))
        top = layout.cell(args.cell)
        assert top is not None
        original_text = texts(top)
        regions = {layout.get_info(layer).to_s(): pya.Region(top.begin_shapes_rec(layer)).merged() for layer in layout.layer_indices()}
        before = {layout.get_info(layer).to_s(): statistics(top, layer) for layer in layout.layer_indices()}
        top.flatten(True)
        layout.write(str(args.output / 'flat.gds'))
        for layer in layout.layer_indices():
            for shape in list(top.shapes(layer).each()):
                if not shape.is_text():
                    shape.delete()
            for polygon in regions[layout.get_info(layer).to_s()].each():
                top.shapes(layer).insert(polygon)
        layout.write(str(args.output / 'union.gds'))
        saved = pya.Layout()
        saved.read(str(args.output / 'union.gds'))
        union = saved.cell(args.cell)
        assert texts(union) == original_text
        rows = []
        for layer in saved.layer_indices():
            name = saved.get_info(layer).to_s()
            delta = regions[name] ^ pya.Region(union.begin_shapes_rec(layer)).merged()
            rows.append({'layer': name, 'xor_polygons': delta.count(), 'xor_area_dbu2': delta.area(),
                         'before': before[name], 'after': statistics(union, layer)})
        assert all(row['xor_polygons'] == 0 for row in rows)
        assert sha(args.input) == report['source_sha256']
        report.update(status='passed exact-union preparation', layers=rows, all_text_exact=True,
                      text_count=len(original_text), flat_sha256=sha(args.output / 'flat.gds'), union_sha256=sha(args.output / 'union.gds'),
                      stock_and_capacitance_parity='not run')
        (args.output / Path(__file__).name).write_bytes(Path(__file__).read_bytes())
    except Exception as error:
        report.update(status='failed', error=repr(error))
    save()
    print(json.dumps({key: value for key, value in report.items() if key != 'layers'}, indent=2))
    return 0 if report['status'] == 'passed exact-union preparation' else 1


if __name__ == '__main__':
    raise SystemExit(main())
