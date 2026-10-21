import klayout.db as db, sys
ly = db.Layout(); ly.read(sys.argv[1]); top = ly.top_cell()
for inst in top.each_inst():
    n = inst.cell.name
    if "IOPad" in n:
        print("IO", n, inst.dcplx_trans, inst.dbbox())
c = ly.cell("new_signal_routes")
for li in ly.layer_indexes():
    info = ly.get_info(li)
    sh = c.shapes(li)
    if sh.size() == 0: continue
    print("NSR layer", info, sh.size())
    for s in list(sh.each())[:60]:
        if s.is_text(): print("   T", s.text_string, s.dbbox().center())
        else: print("   ", s.dbbox())
# texts in top
li = ly.find_layer(134, 25)
for s in top.shapes(li).each():
    print("TOPTXT", s.text_string, s.dbbox().center())
# Top-level TopVia2 bbox clusters
li = ly.find_layer(133, 0)
reg = db.Region(top.shapes(li))
xs = {}
for p in reg.each():
    b = p.bbox().to_dtype(ly.dbu)
    k = (round(b.left/10)*10, round(b.bottom/10)*10)
for p in list(reg.each())[:400:20]:
    print("TV2", p.bbox().to_dtype(ly.dbu))
