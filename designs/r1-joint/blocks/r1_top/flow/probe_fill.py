import klayout.db as db, sys, collections
ly = db.Layout(); ly.read(sys.argv[1]); top = ly.top_cell()
c = collections.Counter()
for inst in top.each_inst(): c[inst.cell.name] += 1
print(sorted(c.items()))
for li in ly.layer_indexes():
    info = ly.get_info(li); n = top.shapes(li).size()
    if n: print("top", info, n, db.Region(top.shapes(li)).bbox().to_dtype(ly.dbu) if n < 100000 else "")
# cells with many shapes
for ci in ly.each_cell():
    tot = sum(ci.shapes(li).size() for li in ly.layer_indexes())
    if tot > 5000: print("cell", ci.name, tot)
