import pya
ly = pya.Layout(); ly.read(gds); top = ly.top_cell()
pinl = ly.find_layer(10, 2); m2 = ly.find_layer(10, 0)
r = pya.Region(top.shapes(pinl))
M2 = pya.Region(top.begin_shapes_rec(m2)).merged()
for p in sorted(r.each(), key=lambda p: (p.bbox().bottom, p.bbox().left))[:3] + sorted(r.each(), key=lambda p: (-p.bbox().top, p.bbox().left))[:3]:
    print(p.bbox().to_dtype(0.001))
# north pin at x 82.08: Metal2 shapes near
w = pya.Region(pya.DBox(80.5, 21.5, 83.5, 23.12).to_itype(0.001))
print([str(q.bbox().to_dtype(0.001)) for q in (M2 & w).each()])
