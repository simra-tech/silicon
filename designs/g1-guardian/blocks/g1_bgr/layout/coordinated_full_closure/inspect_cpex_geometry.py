#!/usr/bin/env python3
"""Read-only representation-complexity diagnostic for saved KPEX layer views."""
import argparse
import hashlib
import json
from pathlib import Path

import pya


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    original = hashlib.sha256(args.input.read_bytes()).hexdigest()
    layout = pya.Layout()
    layout.read(str(args.input))
    top = layout.top_cell()
    rows = []
    for layer in layout.layer_indices():
        iterator = top.begin_shapes_rec(layer)
        polygons = boxes = vertices = max_vertices = 0
        while not iterator.at_end():
            shape = iterator.shape()
            if shape.is_polygon() or shape.is_simple_polygon() or shape.is_box():
                polygon = shape.polygon
                count = polygon.num_points()
                vertices += count
                max_vertices = max(max_vertices, count)
                polygons += 1
                boxes += int(shape.is_box())
            iterator.next()
        rows.append({'layer': layout.get_info(layer).to_s(), 'polygon_instances': polygons,
                     'boxes': boxes, 'total_vertices': vertices, 'largest_polygon_vertices': max_vertices})
    assert hashlib.sha256(args.input.read_bytes()).hexdigest() == original
    result = {'status': 'passed read-only complexity inventory', 'input_sha256': original, 'input': str(args.input),
              'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'topcell': top.name, 'layers': rows, 'interpretation': 'Complexity only; no parasitic values, geometry changes, or solver progress guarantee'}
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
