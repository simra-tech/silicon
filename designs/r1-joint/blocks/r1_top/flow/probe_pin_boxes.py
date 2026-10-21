# SPDX-License-Identifier: Apache-2.0
"""Print the Metal3 shape under every Metal3 label of a macro top cell (track T8, try e).
  python3 probe_pin_boxes.py <gds> [<gds> ...]
"""
import sys
import klayout.db as db
for g in sys.argv[1:]:
    ly = db.Layout(); ly.read(g); tc = ly.top_cell()
    lt = ly.find_layer(30, 25)
    reg = db.Region(tc.begin_shapes_rec(ly.find_layer(30, 0))).merged()
    regp = db.Region(tc.begin_shapes_rec(ly.find_layer(30, 2))).merged() if ly.find_layer(30, 2) is not None else db.Region()
    print("==", g.split("/")[-1], tc.dbbox())
    for s in tc.shapes(lt).each():
        if not s.is_text():
            continue
        p = db.Point(s.text.x, s.text.y)
        best = None
        for r in (regp, reg):
            for poly in r.each():
                if poly.bbox().contains(p):
                    b = poly.bbox().to_dtype(ly.dbu)
                    if best is None or b.area() < best.area():
                        best = b
            if best is not None:
                break
        print("  %-12s label (%.3f, %.3f) box %s" % (s.text_string, s.text.x * ly.dbu, s.text.y * ly.dbu, best))
