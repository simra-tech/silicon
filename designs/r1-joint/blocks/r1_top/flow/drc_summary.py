# SPDX-License-Identifier: Apache-2.0
"""Count DRC markers per rule in KLayout report databases and classify each marker by location.

  python3 drc_summary.py <r1_top_assembly.json> <out.json> <db.lyrdb> [<db.lyrdb> ...]

Class (b) "placeholder or empty region": density and fill rules (no fill is inserted yet), or the marker lies inside a placeholder outline.
Class (a) "assembled parts": every other marker. Each marker is also tagged with the instance whose outline
contains its centre ("top-level" if none, i.e. chip routing or the ring band).
"""
import json
import sys
import klayout.rdb as rdb

asm = json.load(open(sys.argv[1]))
out = sys.argv[2]
boxes = [(r["instance"], r["bbox_um"], r["macro"].endswith("_ph")) for r in asm["placement"] if r["instance"] != "u_ring"]
DENS = ("density", "M1.j", "M1.k", "Mn.j", "Mn.k", "AFil", "GFil", "TM1.c", "TM1.d", "TM2.c", "TM2.d", "LBE.d",
        "M2.j", "M2.k", "M3.j", "M3.k", "M4.j", "M4.k", "M5.j", "M5.k")
res = {"files": [], "rules": {}}
for f in sys.argv[3:]:
    db = rdb.ReportDatabase("")
    db.load(f)
    res["files"].append(f)
    for item in db.each_item():
        cat = db.category_by_id(item.category_id()).name()
        c = None
        for v in item.each_value():
            try:
                bb = v.box() if v.is_box() else (v.polygon().bbox() if v.is_polygon() else
                                                 (v.edge_pair().bbox() if v.is_edge_pair() else
                                                  (v.edge().bbox() if v.is_edge() else None)))
            except Exception:
                bb = None
            if bb is not None:
                c = bb.center()
                break
        where = "top-level"
        in_ph = False
        if c is not None:
            for name, b, ph in boxes:
                if b[0] <= c.x <= b[2] and b[1] <= c.y <= b[3]:
                    where, in_ph = name, ph
                    break
        cls = "b" if (any(cat.startswith(d) for d in DENS) or "Fil." in cat or in_ph) else "a"
        r = res["rules"].setdefault(cat, {"count": 0, "a": 0, "b": 0, "where": {}, "example": None})
        r["count"] += 1
        r[cls] += 1
        r["where"][where] = r["where"].get(where, 0) + 1
        if r["example"] is None and c is not None:
            r["example"] = [round(c.x, 3), round(c.y, 3)]
res["total"] = sum(r["count"] for r in res["rules"].values())
res["total_a"] = sum(r["a"] for r in res["rules"].values())
res["total_b"] = sum(r["b"] for r in res["rules"].values())
json.dump(res, open(out, "w"), indent=1)
print("total", res["total"], "a", res["total_a"], "b", res["total_b"])
for k, r in sorted(res["rules"].items(), key=lambda kv: -kv[1]["count"]):
    print("%-28s %6d a=%d b=%d %s ex=%s" % (k, r["count"], r["a"], r["b"], r["where"], r["example"]))
