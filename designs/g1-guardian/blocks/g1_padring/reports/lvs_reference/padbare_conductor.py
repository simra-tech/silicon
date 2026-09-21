# Is the core-side 'padbare' strip of sg13g2_IOPadAnalog the same conductor as
# the die-side 'pad' stub, and different from 'padres'? KLayout LayoutToNetlist
# on the stock PDK cell, metals + vias only.
import pya
ly = pya.Layout(); ly.read("/foss/pdks/ihp-sg13g2/libs.ref/sg13g2_io/gds/sg13g2_io.gds")
cell = ly.cell("sg13g2_IOPadAnalog")
l2n = pya.LayoutToNetlist(pya.RecursiveShapeIterator(ly, cell, []))
def L(l, d): return l2n.make_layer(ly.layer(l, d), f"l{l}_{d}")
m1, m2, m3, m4, m5, tm1, tm2 = L(8,0), L(10,0), L(30,0), L(50,0), L(67,0), L(126,0), L(134,0)
v1, v2, v3, v4, tv1, tv2 = L(19,0), L(29,0), L(49,0), L(66,0), L(125,0), L(133,0)
for a in (m1, m2, m3, m4, m5, tm1, tm2): l2n.connect(a)
for lo, v, hi in ((m1,v1,m2),(m2,v2,m3),(m3,v3,m4),(m4,v4,m5),(m5,tv1,tm1),(tm1,tv2,tm2)):
    l2n.connect(lo, v); l2n.connect(v, hi)
l2n.extract_netlist()
nl = l2n.netlist(); circ = nl.circuit_by_name("sg13g2_IOPadAnalog")
def net_at(layer, x, y):
    # find the net whose shapes on `layer` contain the point (um)
    pt = pya.Point(int(x*1000), int(y*1000))
    for net in circ.each_net():
        r = l2n.shapes_of_net(net, layer, True)
        if r.count() and (r & pya.Region(pya.Box(pt, pt).enlarged(1,1))).count():
            return net
    return None
stub  = net_at(tm2, 40.0, 1.5)     # die-side 'pad' stub, TopMetal2, y 0..3
strip = net_at(m3, 38.0, 179.9)    # core-side strip, Metal3, y 179.71..180  -> 'padbare'
res   = net_at(m3, 57.6, 179.9)    # padres strip, Metal3 57.355..57.855 x 179.71..180
print("pad stub    net id:", stub.cluster_id if stub else None)
print("padbare strip net id:", strip.cluster_id if strip else None)
print("padres strip net id:", res.cluster_id if res else None)
print("pad == padbare:", stub is not None and strip is not None and stub.cluster_id == strip.cluster_id)
print("pad != padres :", stub is not None and res is not None and stub.cluster_id != res.cluster_id)
