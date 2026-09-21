import pya
a=pya.Layout(); a.read("/foss/pdks/ihp-sg13g2/libs.ref/sg13g2_io/gds/sg13g2_io.gds")
b=pya.Layout(); b.read("build/sources/ihp-sg13g2-ams-chip-template/ip/sg13g2_io_custom/gds/sg13g2_io.gds")
for cell in ["sg13g2_IOPadIn","sg13g2_IOPadAnalog","sg13g2_IOPadVdd","sg13g2_Corner"]:
    ca=a.cell(cell); cb=b.cell(cell)
    if ca is None or cb is None: print(cell,"missing", ca is None, cb is None); continue
    tot=0; per=[]
    for (l,d,n) in [(1,0,"Activ"),(5,0,"GatPoly"),(6,0,"Cont"),(8,0,"M1"),(30,0,"M3"),(126,0,"TM1"),(134,0,"TM2"),(9,0,"Passiv")]:
        la=a.find_layer(l,d); lb=b.find_layer(l,d)
        ra=pya.Region(ca.begin_shapes_rec(la)) if la is not None else pya.Region()
        rb=pya.Region(cb.begin_shapes_rec(lb)) if lb is not None else pya.Region()
        x=(ra^rb).count(); tot+=x; per.append(f"{n}:{x}")
    print(cell, "XOR polys:", tot, " ".join(per))
# the gate at (41.5..42,161.4..166.7) in the template's IOPadIn?
cb=b.cell("sg13g2_IOPadIn"); lb=b.find_layer(5,0)
g=pya.Region(cb.begin_shapes_rec(lb)) & pya.Region(pya.Box(41000,161000,42500,167000))
print("template IOPadIn GatPoly in gate box:", g.count(), g.bbox().to_s())
