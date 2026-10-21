#!/usr/bin/env python3
"""Extract the signal pin x coordinates (Metal3 pin text 30/25) of the r1_safe GDS into safe_pinx.json (um)."""
import json, sys
import klayout.db as db
ly = db.Layout(); ly.read(sys.argv[1]); top = ly.top_cell()
li = ly.find_layer(30, 25); out = {}
it = top.begin_shapes_rec(li)
while not it.at_end():
    s = it.shape()
    if s.is_text():
        t = s.text.transformed(it.trans())
        n = t.string
        if (n[:3] in ("oa_", "na_", "ob_", "nb_") or n in ("oc_a", "neg_a", "oc_b", "neg_b")):
            out[n] = round(t.x / 1000.0, 3)
    it.next()
json.dump(out, open(sys.argv[2], "w"), indent=0, sort_keys=True)
print(len(out), "pins")
