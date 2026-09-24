#!/usr/bin/env python3
"""Extend only legal drawn access metals on the pinned native CMIM coupon."""
import argparse
import hashlib
import json
from pathlib import Path

import klayout.db as kdb


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def region(cell, layout, layer, datatype=0):
    return kdb.Region(cell.begin_shapes_rec(layout.layer(layer, datatype)))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--coupon', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists()
    source = json.loads((a.coupon / 'manifest.json').read_text())
    source_gds = a.coupon / 'sense_mim_method_control.gds'
    source_cdl = a.coupon / 'sense_mim_method_control.cdl'
    assert sha(source_gds) == source['GDS_sha256'] == '546c3e33d3894fb4c0d54c623a0cd2ac261cbf074a44d210240921c86194fd20'
    assert sha(source_cdl) == source['CDL_sha256'] == 'bcc32a78962430e46e7269518c645681c3233e24337e87142e714c7fe85aa974'
    ly = kdb.Layout()
    ly.read(str(source_gds))
    assert ly.dbu == .001
    cell = ly.cell('sense_mim_method_control')
    assert cell is not None
    protected = {(layer, dt): region(cell, ly, layer, dt) for layer, dt in [(36, 0), (129, 0)]}
    before_metal = {layer: region(cell, ly, layer) for layer in (67, 126)}
    assert protected[(36, 0)].area() == 49_000_000
    # 2-um-wide, 10-um-long drawn metal stubs, overlapping the native
    # bottom Metal5 and top TopMetal1 landing regions at their existing edge.
    stubs = {67: kdb.Box(-5600, 7000, 4400, 9000),
             126: kdb.Box(11650, 7000, 21650, 9000)}
    for layer, box in stubs.items():
        cell.shapes(ly.layer(layer, 0)).insert(box)
        assert (region(cell, ly, layer) ^ (before_metal[layer] + kdb.Region(box))).is_empty()
    for layer in (67, 126):
        cell.shapes(ly.layer(layer, 25)).clear()
    # Pinned KPEX technology uses datatype 2 for pin polygons and datatype
    # 25 for labels; labels alone do not create R-request pin landings.
    cell.shapes(ly.layer(67, 2)).insert(kdb.Box(-5600, 7000, -3600, 9000))
    cell.shapes(ly.layer(126, 2)).insert(kdb.Box(19650, 7000, 21650, 9000))
    cell.shapes(ly.layer(67, 25)).insert(kdb.Text('bottom', kdb.Trans(kdb.Point(-4600, 8000))))
    cell.shapes(ly.layer(126, 25)).insert(kdb.Text('top', kdb.Trans(kdb.Point(20650, 8000))))
    a.output.mkdir(parents=True)
    gds = a.output / 'sense_mim_method_control.gds'
    ly.write(str(gds))
    (a.output / source_cdl.name).write_bytes(source_cdl.read_bytes())
    saved = kdb.Layout()
    saved.read(str(gds))
    restored = saved.cell('sense_mim_method_control')
    assert restored is not None
    assert all((region(restored, saved, layer, dt) ^ expected).is_empty()
               for (layer, dt), expected in protected.items())
    assert all((region(restored, saved, layer) ^
                (before_metal[layer] + kdb.Region(box))).is_empty()
               for layer, box in stubs.items())
    assert (region(restored, saved, 67, 2) ^ kdb.Region(kdb.Box(-5600, 7000, -3600, 9000))).is_empty()
    assert (region(restored, saved, 126, 2) ^ kdb.Region(kdb.Box(19650, 7000, 21650, 9000))).is_empty()
    result = dict(status='prepared native CMIM plus external access-metal diagnostic',
                  source_GDS_sha256=sha(source_gds), source_CDL_sha256=sha(source_cdl),
                  GDS_sha256=sha(gds), CDL_sha256=sha(a.output / source_cdl.name),
                  native_MIM_area_um2=49, native_MIM_and_via_XOR_um2=0,
                  stub_geometry_um=dict(bottom_Metal5=[-5.6, 7, 4.4, 9],
                                        top_TopMetal1=[11.65, 7, 21.65, 9]),
                  remote_pin_datatype=2, remote_label_datatype=25,
                  stock_DRC='not run', stock_LVS='not run',
                  external_R='not run', full_PEX='not qualified')
    (a.output / 'manifest.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
