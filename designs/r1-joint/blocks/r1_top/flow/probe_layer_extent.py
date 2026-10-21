# Print the bounding box and merged-polygon boxes of selected layers in a macro GDS (recursive).
import klayout.db as db, sys
ly = db.Layout(); ly.read(sys.argv[1]); top = ly.top_cell()
for spec in sys.argv[2:]:
    l, d = map(int, spec.split("/"))
    li = ly.find_layer(l, d)
    if li is None: print(spec, "absent"); continue
    reg = db.Region(top.begin_shapes_rec(li)).merged()
    print(spec, "bbox", reg.bbox().to_dtype(ly.dbu), "polys", reg.count())
    for p in list(reg.each())[:12]: print("   ", p.bbox().to_dtype(ly.dbu))
