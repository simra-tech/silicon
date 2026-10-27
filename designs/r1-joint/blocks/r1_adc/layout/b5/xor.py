# geometric XOR of two GDS top cells (all layers, flattened); prints differing layers
import pya
def load(p):
    ly = pya.Layout(); ly.read(p); return ly
A, B = load(a), load(b)
ta, tb = A.cell(cell), B.cell(cell)
diff = 0
keys = set((A.get_info(l).layer, A.get_info(l).datatype) for l in A.layer_indexes()) | set((B.get_info(l).layer, B.get_info(l).datatype) for l in B.layer_indexes())
for (l, d) in sorted(keys):
    la, lb = A.find_layer(l, d), B.find_layer(l, d)
    ra = pya.Region(ta.begin_shapes_rec(la)) if la is not None else pya.Region()
    rb = pya.Region(tb.begin_shapes_rec(lb)) if lb is not None else pya.Region()
    x = ra ^ rb
    if not x.is_empty():
        diff += 1; print('layer %d/%d differs: %d polygons' % (l, d, x.count()))
print('XOR layers differing:', diff)
