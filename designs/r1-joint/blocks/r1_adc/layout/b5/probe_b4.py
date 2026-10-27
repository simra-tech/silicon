# probe the B4 GDS: for each routing layer, x intervals free of metal over a y range (vertical channels), whole top cell flattened
import pya
ly = pya.Layout(); ly.read(gds)
top = ly.cell('r1_adc')
L = {'M1': (8, 0), 'M2': (10, 0), 'M3': (30, 0), 'M4': (50, 0), 'M5': (67, 0), 'TM1': (126, 0), 'TM2': (134, 0), 'MIM': (36, 0)}
y0, y1 = float(ya), float(yb)
for nm, (l, d) in L.items():
    li = ly.find_layer(l, d)
    if li is None:
        print(nm, 'absent'); continue
    r = pya.Region(top.begin_shapes_rec(li)).merged()
    band = r & pya.Region(pya.Box(0, int(y0 * 1000), 439000, int(y1 * 1000)))
    # project onto x
    occ = pya.Region()
    for p in band.each():
        b = p.bbox(); occ.insert(pya.Box(b.left, 0, b.right, 10))
    occ.merge()
    free = pya.Region(pya.Box(0, 0, 439000, 10)) - occ
    iv = sorted([(round(b.left / 1000, 2), round(b.right / 1000, 2)) for b in (p.bbox() for p in free.each()) if b.width() >= int(float(minw) * 1000)])
    print(nm, 'y %.1f-%.1f' % (y0, y1), 'free x >= %s:' % minw, iv)
