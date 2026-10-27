import pya
ly = pya.Layout(); ly.read(gds); top = ly.top_cell()
for (x0,y0,x1,y1) in [(3.5,19.5,9.5,23.12),(0,0,3,23.12),(436,0,439,23.12),(28,0,33,3)]:
  for l in [(10,0),(19,0),(30,0),(29,0),(50,0),(49,0)]:
    li = ly.find_layer(*l)
    r = pya.Region(top.begin_shapes_rec(li)) & pya.Region(pya.DBox(x0,y0,x1,y1).to_itype(0.001))
    print((x0,y0,x1,y1), l, [str(p.bbox().to_dtype(0.001)) for p in r.merged().each()][:14])
