#!/usr/bin/env python3
"""Analytical perimeter ledger also covers native non-Manhattan edges."""
import hashlib
from decimal import Decimal, localcontext
from pathlib import Path


def polygon_record(poly):
    rings = [list(poly.each_point_hull())]+[list(poly.each_point_hole(i)) for i in range(poly.holes())]
    areas, lengths, edge_squares = [], [], []
    orthogonal = True
    with localcontext() as ctx:
        ctx.prec = 80
        for points in rings:
            assert len(points) >= 3
            pairs = list(zip(points, points[1:]+points[:1]))
            orthogonal = orthogonal and all(p.x == q.x or p.y == q.y for p,q in pairs)
            areas.append(abs(sum(p.x*q.y-q.x*p.y for p,q in pairs)))
            squares = [(p.x-q.x)**2+(p.y-q.y)**2 for p,q in pairs]
            edge_squares.append(squares)
            lengths.append(sum((Decimal(s).sqrt() for s in squares), Decimal(0)))
        twice_area = areas[0]-sum(areas[1:])
        perimeter = sum(lengths, Decimal(0))
        if orthogonal:
            assert twice_area == 2*poly.area()
            assert perimeter == Decimal(poly.perimeter())
        shape = 'rectangle' if poly.is_box() else ('other Manhattan shape' if orthogonal else 'non-Manhattan shape')
        ring_widths = None
        if orthogonal and len(rings) == 2 and len(rings[0]) == len(rings[1]) == 4:
            bounds = [(min(p.x for p in ring),min(p.y for p in ring),max(p.x for p in ring),max(p.y for p in ring)) for ring in rings]
            outer, inner = bounds
            ring_widths = [inner[0]-outer[0],inner[1]-outer[1],outer[2]-inner[2],outer[3]-inner[3]]
            shape = 'uniform rectangular ring' if len(set(ring_widths)) == 1 else 'nonuniform rectangular ring'
        return dict(twice_area_dbu2=twice_area, klayout_area_dbu2=poly.area(),
            analytical_perimeter_dbu=str(perimeter), klayout_perimeter_dbu=poly.perimeter(),
            area_API_difference_dbu2=str(Decimal(poly.area())-Decimal(twice_area)/2),
            perimeter_API_difference_dbu=str(Decimal(poly.perimeter())-perimeter),
            area_um2=str(Decimal(twice_area)/Decimal(2000000)),
            perimeter_um=str(perimeter/Decimal(1000)), classification=shape,
            rectangular_ring_widths_dbu=ring_widths,
            hull_and_holes=[[[p.x,p.y] for p in ring] for ring in rings],
            edge_squared_lengths_dbu2=edge_squares, bbox_dbu=str(poly.bbox()),
            exact_Manhattan_API_parity='passed' if orthogonal else 'not applicable; irrational edge lengths recorded analytically',
            source_parameter_quantization='not run')


original = Path(__file__).resolve().with_name('audit_dimensions.py')
assert hashlib.sha256(original.read_bytes()).hexdigest() == 'c82957847dea49bf02e0b36de22e9dbe06d1c98531f42eab9324e0bc4c4f5a4c'
scope = dict(__file__=str(Path(__file__).resolve()), __name__='native_geometry_analytical_successor')
exec(compile(original.read_text(), str(original), 'exec'), scope)
scope['polygon_record'] = polygon_record
scope['main']()
