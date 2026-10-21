# Probe the R1 ring GDS: top-level shapes per layer in the core-ring band, IO cell instances, fill datatypes.
import klayout.db as db, sys, json, collections
ly = db.Layout(); ly.read(sys.argv[1]); top = ly.top_cell()
print("top", top.name, "dbu", ly.dbu, "bbox", top.dbbox())
cnt = collections.Counter()
for li in ly.layer_indexes():
    info = ly.get_info(li)
    n = top.shapes(li).size()
    if n: cnt[(info.layer, info.datatype)] = n
print("top-level shape counts", sorted(cnt.items()))
# instances
ic = collections.Counter(); 
for inst in top.each_inst():
    ic[inst.cell.name] += 1
print("instances", sorted(ic.items()))
for inst in top.each_inst():
    n = inst.cell.name
    if n.startswith("sg13g2_IOPad") or "Corner" in n or "bondpad" in n.lower():
        print("INST", n, inst.dcplx_trans, inst.dbbox())
# big shapes on TM1/TM2/vias top-level (non-fill)
for (l, d) in [(126, 0), (134, 0), (133, 0), (125, 0), (67, 0), (50, 0), (30, 0), (10, 0), (8, 0)]:
    li = ly.find_layer(l, d)
    if li is None: continue
    reg = db.Region(top.shapes(li)).merged()
    print("LAYER %d/%d top-level merged polys %d" % (l, d, reg.count()))
    for p in list(reg.each())[:40]:
        b = p.bbox().to_dtype(ly.dbu)
        if b.width() > 20 or b.height() > 20:
            print("   ", b)
