# Dump top cell, prBoundary, layer usage and pin labels (text with the shape under it) for each macro GDS.
import klayout.db as db, sys, json
out = {}
for path in sys.argv[2:]:
    ly = db.Layout(); ly.read(path); top = ly.top_cell()
    r = {"top": top.name, "bbox": list(top.dbbox().to_s().replace(";", ",").split(",")), "layers": {}, "texts": []}
    pb = ly.find_layer(189, 4)
    if pb is not None:
        r["prBoundary"] = str(db.Region(top.begin_shapes_rec(pb)).bbox().to_dtype(ly.dbu))
    for li in ly.layer_indexes():
        info = ly.get_info(li)
        it = top.begin_shapes_rec(li)
        n = 0; bb = db.Box()
        while not it.at_end():
            sh = it.shape()
            if sh.is_text() and it.cell_index() == top.cell_index():
                t = sh.text.transformed(it.trans())
                r["texts"].append([info.layer, info.datatype, t.string, round(t.x * ly.dbu, 3), round(t.y * ly.dbu, 3)])
            elif not sh.is_text():
                n += 1
            it.next()
        if n: r["layers"]["%d/%d" % (info.layer, info.datatype)] = n
    out[path.split("/")[-1]] = r
json.dump(out, open(sys.argv[1], "w"), indent=1)
for k, v in out.items():
    print(k, v["top"], v.get("prBoundary"), v["bbox"])
    print("  layers", " ".join(sorted(v["layers"].keys())))
    print("  texts", len(v["texts"]), v["texts"][:12])
