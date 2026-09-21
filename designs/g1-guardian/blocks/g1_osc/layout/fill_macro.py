"""Helper for fill_macro.sh: prepare a macro GDS for the PDK filler and clean its output.

The PDK fill macros (libs.tech/klayout/tech/macros/sg13g2_filler_{ActGatP,Metal,TopMetal}.lym,
driven by libs.tech/klayout/tech/scripts/filler.py) fill the *holes of the EdgeSeal layer* (39/0),
i.e. the inside of the chip's seal ring, minus the drawn shapes with their keep-outs and minus the
no-fill shapes (<layer>/23, NoMetFiller 160/0).  A macro has no seal ring, so:

  mode=pre   klayout -b -r fill_macro.py -rd mode=pre -rd gds=<macro.gds> -rd out=<fillin.gds> [-rd inset=3.0]
             adds a temporary EdgeSeal ring around the macro whose hole is the prBoundary (189/4, or
             the cell bbox) shrunk by `inset` um: fill stays that far from the macro edge (pins, bars)
  mode=post  klayout -b -r fill_macro.py -rd mode=post -rd gds=<filled_raw.gds> -rd out=<macro.gds>
             removes the temporary EdgeSeal layer again and reports the fill shape counts per layer
"""
import pya

mode = globals().get('mode', 'pre')
gds = globals()['gds']
out = globals()['out']
inset = float(globals().get('inset', '3.0'))

ly = pya.Layout()
ly.read(gds)
top = ly.top_cell()
if mode == 'pre':
    li = ly.find_layer(189, 4)
    box = top.bbox(li) if li is not None and not top.shapes(li).is_empty() else top.bbox()
    hole = box.enlarged(-int(round(inset * 1000)), -int(round(inset * 1000)))
    outer = box.enlarged(2000, 2000)
    ring = pya.Region(outer) - pya.Region(hole)
    top.shapes(ly.layer(39, 0)).insert(ring)
    ly.write(out)
    print('fill window %s (macro %s, inset %.1f um) written to %s' % (hole.to_s(), box.to_s(), inset, out))
else:
    li = ly.find_layer(39, 0)
    if li is not None:
        for c in ly.each_cell():
            c.shapes(li).clear()
        ly.delete_layer(li)
    counts = {}
    for lidx in ly.layer_indexes():
        info = ly.get_info(lidx)
        if info.datatype == 22:
            n = 0
            for _ in top.begin_shapes_rec(lidx):
                n += 1
            counts['%d/%d' % (info.layer, info.datatype)] = n
    ly.write(out)
    print('fill shapes per layer (datatype 22):', counts)
    print('wrote', out, top.name, top.dbbox())
