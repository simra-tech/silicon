import pya
# KLayout batch helper for fill_g1_t2f.sh.
#   -rd src=<gds> -rd dst=<gds>            add a temporary EdgeSeal (39/0) frame around the top cell (hole = boundary inset 1 um)
#   -rd src=<gds> -rd dst=<gds> -rd strip=1   remove every EdgeSeal shape again and report the fill placed (datatype 22)
ly = pya.Layout(); ly.read(src)
top = ly.top_cell()
es = ly.layer(39, 0)
if 'strip' in globals():
    n = top.shapes(es).size()
    top.shapes(es).clear()
    print('removed', n, 'EdgeSeal shape(s)')
    for l, name in ((1, 'Activ'), (5, 'GatPoly'), (8, 'Metal1'), (10, 'Metal2'), (30, 'Metal3'), (50, 'Metal4'), (67, 'Metal5'), (126, 'TopMetal1'), (134, 'TopMetal2')):
        li = ly.find_layer(l, 22)
        r = pya.Region(top.begin_shapes_rec(li)) if li is not None else pya.Region()
        bb = top.dbbox()
        print('%-10s fill shapes %5d  area %7.1f um2 (%4.1f %% of the macro)' % (name, r.count(), r.area() / 1e6, r.area() / 1e6 / (bb.width() * bb.height()) * 100))
else:
    b = top.bbox()
    outer = pya.Box(b.left - 2000, b.bottom - 2000, b.right + 2000, b.top + 2000)
    inner = pya.Box(b.left + 1000, b.bottom + 1000, b.right - 1000, b.top - 1000)
    ring = pya.Polygon(outer); ring.insert_hole(inner)
    top.shapes(es).insert(ring)
    print('EdgeSeal frame added, fill window', inner.to_s())
ly.write(dst)
print('wrote', dst)
