#!/usr/bin/env python3
"""Prepare a macro GDS for the PDK filler (libs.tech/klayout/tech/scripts/filler.py), or clean its output.

The three PDK filler macros fill `EdgeSeal.holes`, i.e. only the inside of a seal ring, so a macro
without one gets no fill. Usage (KLayout batch, container):
  klayout -b -r fill_prep.py -rd mode=prep  -rd gds=<macro.gds> -rd cell=<top> -rd out=<prep.gds> [-rd inset=1.0]
      draws a temporary EdgeSeal (39/0) ring on the top cell whose inner edge lies `inset` um inside
      the cell boundary (189/4), so the fill stays that far from the macro edge
  klayout -b -r fill_prep.py -rd mode=clean -rd gds=<filled.gds> -rd cell=<top> -rd out=<final.gds>
      deletes the EdgeSeal layer again and reports the fill-cell shape counts per layer
"""
import pya
mode = globals()['mode']; gds = globals()['gds']; out = globals()['out']; cellname = globals()['cell']
inset = float(globals().get('inset', '1.0'))
ly = pya.Layout(); ly.read(gds)
top = ly.cell(cellname)
dbu = ly.dbu
if mode == 'prep':
    lb = ly.layer(189, 4)
    bb = None
    for s in top.shapes(lb).each():
        bb = s.bbox() if bb is None else bb + s.bbox()
    assert bb is not None, 'no 189/4 boundary in the top cell'
    seal = ly.layer(39, 0)
    d = int(round(inset / dbu)); w = int(round(2.0 / dbu))
    inner = pya.Box(bb.left + d, bb.bottom + d, bb.right - d, bb.top - d)
    outer = pya.Box(inner.left - w, inner.bottom - w, inner.right + w, inner.top + w)
    ring = pya.Polygon(outer); ring.insert_hole(inner)
    top.shapes(seal).insert(ring)
    ly.write(out); print('prep: EdgeSeal ring around', inner.to_dtype(dbu), '->', out)
else:
    seal = ly.find_layer(39, 0)
    if seal is not None:
        ly.delete_layer(seal)
    # remove the temporary ring's proxy cells if any; count fill shapes (datatype 22) by layer
    counts = {}
    for li in ly.layer_indexes():
        info = ly.get_info(li)
        if info.datatype == 22:
            n = 0
            for c in ly.each_cell():
                n += c.shapes(li).size()
            counts['%d/%d' % (info.layer, info.datatype)] = n
    ly.write(out); print('clean: wrote', out, 'fill shapes per layer:', counts)
    print('cells:', sorted(c.name for c in ly.each_cell()))
