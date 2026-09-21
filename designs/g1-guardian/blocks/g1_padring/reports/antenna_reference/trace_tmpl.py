import pya
a=pya.Layout(); a.read("/foss/pdks/ihp-sg13g2/libs.ref/sg13g2_io/gds/sg13g2_io.gds")
b=pya.Layout(); b.read("build/sources/ihp-sg13g2-ams-chip-template/ip/sg13g2_io_custom/gds/sg13g2_io.gds")
ca=a.cell("sg13g2_IOPadIn"); cb=b.cell("sg13g2_IOPadIn")
print("XOR bboxes (PDK vs template) in sg13g2_IOPadIn:")
for (l,d,n) in [(1,0,"Activ"),(5,0,"GatPoly"),(6,0,"Cont"),(8,0,"M1")]:
    ra=pya.Region(ca.begin_shapes_rec(a.find_layer(l,d))); rb=pya.Region(cb.begin_shapes_rec(b.find_layer(l,d)))
    x=ra^rb
    print("  %-8s n=%d bbox=%s" % (n, x.count(), x.bbox().to_s()))
    for p in list(x.each())[:3]: print("      ", p.bbox().to_s())
def trace(ly, c, label):
    def reg(l,d):
        li=ly.find_layer(l,d); return pya.Region(c.begin_shapes_rec(li)) if li is not None else pya.Region()
    gat=reg(5,0); g=gat & pya.Region(pya.Box(41000,161000,42500,167000)); gp=gat.interacting(g)
    cont=reg(6,0).interacting(gp.sized(300)); m1=reg(8,0).interacting(cont)
    print(label, "gate bbox", gp.bbox().to_s(), "| Cont on gate:", cont.count(), "| M1 on gate: n=%d area=%.1f bbox=%s" % (m1.count(), m1.area()/1e6, m1.bbox().to_s()))
    cur=m1
    for (vl,vd,ml,md,name) in [(19,0,10,0,'M2'),(29,0,30,0,'M3'),(49,0,50,0,'M4'),(66,0,67,0,'M5'),(125,0,126,0,'TM1')]:
        v=reg(vl,vd).interacting(cur); m=reg(ml,md).interacting(v) if v.count() else pya.Region()
        print("   %s: vias=%d polys=%d area=%.1f bbox=%s" % (name, v.count(), m.count(), m.area()/1e6, m.bbox().to_s() if m.count() else '-'))
        if not m.count(): break
        cur=m
trace(a, ca, "PDK 8437402:"); trace(b, cb, "template custom:")
