# KLayout batch: geometry XOR of two GDS files, top cells compared by layer (names of the top cells may differ).
# klayout -b -r xor_vs_g1.py -rd a=<gds a> -rd b=<gds b> -rd top_a=<cell> -rd top_b=<cell>
import pya
la, lb = pya.Layout(), pya.Layout()
la.read(a); lb.read(b)
ca, cb = la.cell(top_a), lb.cell(top_b)
bad = 0
infos = {}
for i in la.layer_indices():
    infos[(la.get_info(i).layer, la.get_info(i).datatype)] = [i, None]
for i in lb.layer_indices():
    k = (lb.get_info(i).layer, lb.get_info(i).datatype)
    infos.setdefault(k, [None, None])[1] = i
for k, (ia, ib) in sorted(infos.items()):
    ra = pya.Region(ca.begin_shapes_rec(ia)) if ia is not None else pya.Region()
    rb = pya.Region(cb.begin_shapes_rec(ib)) if ib is not None else pya.Region()
    x = (ra ^ rb).area()
    if x:
        bad += 1
    print('layer %d/%d  area_a %.3f  area_b %.3f  xor_area %.6f' % (k[0], k[1], ra.area() / 1e6, rb.area() / 1e6, x / 1e6))
print('XOR RESULT:', 'identical geometry' if bad == 0 else '%d layers differ' % bad)
