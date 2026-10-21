# SPDX-License-Identifier: Apache-2.0
"""List the core-side pin shapes of every IO cell in a ring GDS (track T8, try e).

  python3 probe_ring_pins.py <ring.gds> <out.json> <io_inner_low> <io_inner_high>

For each sg13g2_IOPad* instance: cell name, transformation, and every labelled pin shape of the IO cell whose
transformed box touches the IO-row inner edge (within 1 um). Coordinates in um, chip frame.
"""
import json
import sys
import klayout.db as db

g, out, lo, hi = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
ly = db.Layout()
ly.read(g)
top = ly.top_cell()
res = []
for inst in top.each_inst():
    c = inst.cell
    if "IOPad" not in c.name:
        continue
    t = inst.dcplx_trans
    pins = []
    for li in ly.layer_indexes():
        info = ly.get_info(li)
        if info.datatype not in (25, 2, 0) or info.layer not in (8, 10, 30, 50, 67, 126, 134):
            continue
        for s in c.shapes(li).each():
            if not s.is_text():
                continue
            p = t * db.DPoint(s.dtext.x, s.dtext.y)
            # shape under the label on the drawing layer
            dl = ly.find_layer(info.layer, 0)
            box = None
            if dl is not None:
                reg = db.Region(c.begin_shapes_rec(dl)).merged()
                q = db.Point.from_dpoint(db.DPoint(s.dtext.x, s.dtext.y) * (1.0 / ly.dbu))
                for poly in reg.each():
                    if poly.bbox().contains(q):
                        b = poly.bbox().to_dtype(ly.dbu).transformed(t)
                        if box is None or b.area() < box.area():
                            box = b
            near = box is not None and (abs(box.left - hi) < 1 or abs(box.right - lo) < 1 or
                                        abs(box.bottom - hi) < 1 or abs(box.top - lo) < 1)
            pins.append({"text": s.text_string, "layer": "%d/%d" % (info.layer, info.datatype),
                         "label_xy": [round(p.x, 3), round(p.y, 3)],
                         "box": [round(box.left, 3), round(box.bottom, 3), round(box.right, 3), round(box.top, 3)] if box else None,
                         "core_edge": near})
    bb = inst.dbbox()
    res.append({"cell": c.name, "trans": str(t), "bbox": [round(bb.left, 3), round(bb.bottom, 3), round(bb.right, 3), round(bb.top, 3)],
                "pins": [p for p in pins if p["core_edge"]]})
json.dump(res, open(out, "w"), indent=1)
for r in sorted(res, key=lambda r: (r["bbox"][0], r["bbox"][1])):
    print(r["cell"], r["bbox"], [(p["text"], p["layer"], p["box"]) for p in r["pins"]])
