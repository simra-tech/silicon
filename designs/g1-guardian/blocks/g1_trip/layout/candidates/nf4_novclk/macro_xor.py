# r4 candidate nf4_novclk: XOR of the candidate macro against the r3 TRIP macro cut, per layer (hierarchy flattened,
# fill cells included), with the bounding box of every difference; and the set of sub-cells / their content.
#   klayout -b -r macro_xor.py -rd a=<r3 cut gds> -rd b=<candidate gds>
import pya
la = pya.Layout(); la.read(a); lb = pya.Layout(); lb.read(b)
ta, tb = la.cell('g1_trip'), lb.cell('g1_trip')
tot = pya.Region()
n = 0
for li in la.layer_indexes():
    info = la.get_info(li); lj = lb.find_layer(info)
    ra = pya.Region(ta.begin_shapes_rec(li)); rb = pya.Region(tb.begin_shapes_rec(lj)) if lj is not None else pya.Region()
    x = ra ^ rb
    if not x.is_empty():
        n += 1; tot += x
        print('differs %-7s area %8.3f um2 bbox %s' % (info, x.area() * 1e-6, x.bbox().to_dtype(0.001)))
for lj in lb.layer_indexes():
    info = lb.get_info(lj)
    if la.find_layer(info) is None:
        rb = pya.Region(tb.begin_shapes_rec(lj))
        if not rb.is_empty():
            n += 1; tot += rb; print('only in candidate', info, rb.bbox().to_dtype(0.001))
print('layers differing:', n, ' union bbox of all differences:', tot.bbox().to_dtype(0.001))
# sub-cells other than fill: identical content?
for c in la.each_cell():
    if c.name in ('g1_trip',) or 'FILL' in c.name: continue
    cb = lb.cell(c.name)
    same = cb is not None and all((pya.Region(c.begin_shapes_rec(li)) ^ pya.Region(cb.begin_shapes_rec(lb.find_layer(la.get_info(li))))).is_empty() for li in la.layer_indexes() if lb.find_layer(la.get_info(li)) is not None)
    same = same and all(la.find_layer(lb.get_info(lj)) is not None or cb.bbox_per_layer(lj).empty() for lj in lb.layer_indexes())
    print('sub-cell', c.name, 'identical' if same else 'DIFFERS')
print('bbox a', ta.dbbox(), 'bbox b', tb.dbbox())
