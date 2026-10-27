# where do net a and net b run close (< d um) in an lvsdb (all metal layers)?
import pya
lvs = pya.LayoutVsSchematic(); lvs.read(db)
c = lvs.netlist().top_circuit()
na, nb = c.net_by_name(a), c.net_by_name(b)
for ln in ('metal1_con', 'metal2_con', 'metal3_con', 'metal4_con', 'metal5_con', 'topmetal1_con'):
    L = lvs.layer_by_name(ln)
    if L is None: continue
    ra = lvs.shapes_of_net(na, L, True).merged(); rb = lvs.shapes_of_net(nb, L, True).merged()
    for ln2 in ('metal1_con', 'metal2_con', 'metal3_con', 'metal4_con', 'metal5_con', 'topmetal1_con'):
        L2 = lvs.layer_by_name(ln2)
        rb2 = lvs.shapes_of_net(nb, L2, True).merged()
        near = ra & rb2.sized(int(float(d) * 1000))
        if not near.is_empty():
            print(ln, ln2, 'area um2 %.2f' % (near.area() * 1e-6), [str(p.bbox().to_dtype(0.001)) for p in near.each()][:6])
