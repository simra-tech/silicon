import pya, sys
ly = pya.Layout(); ly.read(globals()["gds"]); top = ly.top_cell()
box = pya.Region(pya.Box(733000, 440000, 985160, 629250))
for l, name in ((1,"Activ"),(5,"GatPoly"),(8,"Metal1"),(10,"Metal2"),(30,"Metal3"),(50,"Metal4"),(67,"Metal5"),(126,"TopMetal1"),(134,"TopMetal2")):
    li = ly.find_layer(l, 22)
    if li is None: print(f"{name:10s} fill layer {l}/22 absent"); continue
    r = pya.Region(top.begin_shapes_rec(li))
    inside = (r & box).count(); total = r.count()
    print(f"{name:10s} fill shapes total {total:7d}  inside no-fill box {inside:6d}")
