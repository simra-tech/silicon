"""Small KLayout-only negative fixtures for retained OSC fill hierarchy.

Run with the pinned image: klayout -b -r test_osc_r095_fullchip_geometry.py
No production GDS is read or written by these fixtures.
"""
import json
from pathlib import Path
import sys

import pya

sys.path.insert(0, str(Path(__file__).resolve().parent))
import prepare_osc_r095_fullchip_geometry as build


def fixture(dummy_first=False):
    layout = pya.Layout()
    layout.dbu = .001
    if dummy_first:
        layout.create_cell('unreferenced_dummy')
    top = layout.create_cell('top')
    child = layout.create_cell('fill')
    layer = layout.layer(pya.LayerInfo(1, 22))
    shape = child.shapes(layer).insert(pya.Box(0, 0, 100, 100))
    instance = top.insert(pya.CellInstArray(child.cell_index(), pya.Trans(pya.Point(250, 500))))
    return layout, top, child, shape, instance


def rejects(callback):
    try:
        callback()
    except AssertionError:
        return
    raise AssertionError('Invalid retained fill hierarchy was accepted')


def run():
    allowed = build.CHILD_FILL
    layout, top, child, shape, instance = fixture()
    assert build.check_fill_children(layout, top, allowed) == {'fill': [(1, 22)]}
    assert len(build.instances(top)) == 1

    # One forbidden nonfill shape cannot hide behind valid fill on another layer.
    layer = layout.layer(pya.LayerInfo(2, 0))
    child.shapes(layer).insert(pya.Box(0, 0, 10, 10))
    rejects(lambda: build.check_fill_children(layout, top, allowed))

    layout, top, child, shape, instance = fixture()
    layer = layout.layer(pya.LayerInfo(1, 22))
    child.shapes(layer).insert(pya.Text('NOT_FILL', pya.Trans(pya.Point(0, 0))))
    rejects(lambda: build.check_fill_children(layout, top, allowed))

    layout, top, child, shape, instance = fixture()
    shape.set_property(1, 'unexpected')
    assert shape.has_prop_id()
    rejects(lambda: build.check_fill_children(layout, top, allowed))

    layout, top, child, shape, instance = fixture()
    instance.set_property(1, 'unexpected')
    assert instance.has_prop_id()
    rejects(lambda: build.check_fill_children(layout, top, allowed))

    layout, top, child, shape, instance = fixture()
    grandchild = layout.create_cell('nested')
    child.insert(pya.CellInstArray(grandchild.cell_index(), pya.Trans()))
    rejects(lambda: build.check_fill_children(layout, top, allowed))

    # Cell indexes differ, while child name and placed transform are identical.
    first, top_first, _, _, _ = fixture(dummy_first=False)
    second, top_second, _, _, _ = fixture(dummy_first=True)
    assert first.cell('fill').cell_index() != second.cell('fill').cell_index()
    assert build.instances(top_first) == build.instances(top_second)

    # A SimplePolygon and a generic Polygon can have identical area but differ
    # in the exact GDS shape inventory; the builder must keep the source type.
    layout = pya.Layout()
    source = layout.create_cell('source')
    copied = layout.create_cell('copied')
    layer = layout.layer(pya.LayerInfo(1, 0))
    polygon = pya.SimplePolygon([pya.Point(0, 0), pya.Point(100, 0),
                                 pya.Point(100, 50), pya.Point(0, 50)])
    source_shape = source.shapes(layer).insert(polygon)
    assert source_shape.is_simple_polygon()
    copied.shapes(layer).insert(source_shape.simple_polygon)
    assert sorted(str(s) for s in source.shapes(layer).each()) == sorted(
        str(s) for s in copied.shapes(layer).each())
    print(json.dumps({'status': 'passed', 'pure_fixtures': 8,
                      'production_geometry_read': False, 'production_geometry_written': False}))


if __name__ == '__main__':
    run()
