import pya
a = pya.Layout(); a.read(ga); b = pya.Layout(); b.read(gb)
ta, tb = a.top_cell(), b.top_cell()
diff = 0
for li in a.layer_indexes():
    info = a.get_info(li); lj = b.find_layer(info)
    ra = pya.Region(ta.begin_shapes_rec(li)); rb = pya.Region(tb.begin_shapes_rec(lj)) if lj is not None else pya.Region()
    x = ra ^ rb
    if not x.is_empty(): print('differs', info, x.area()*1e-6); diff += 1
for lj in b.layer_indexes():
    if a.find_layer(b.get_info(lj)) is None and not pya.Region(tb.begin_shapes_rec(lj)).is_empty(): print('only in b', b.get_info(lj)); diff += 1
print('layers differing:', diff)
