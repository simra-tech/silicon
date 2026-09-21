# SPDX-License-Identifier: Apache-2.0
"""Same-layer overlaps between the special (supply) nets of a DEF.

  klayout -b -rd gds=<chip.gds> -rd defp=<chip.def> -r pdn_net_overlap.py

Builds one region per (net, layer) from the DEF SPECIALNETS (stripe segments
with their width; via instances expanded with the geometry of the GDS `VIA_*`
cells) for VDD, VSS, VDDA, IOVDD and IOVSS, and reports every overlap between
two different nets on the same metal layer and every via cut of one net that
lands on metal of another. Such overlaps are shorts that KLayout DRC cannot
see (same-layer metal merges) and that check_power_grid does not test (it
checks one net at a time).
"""
import re
import pya

ly = pya.Layout(); ly.read(globals()["gds"])
D = open(globals()["defp"]).read()
sec = D[D.index("SPECIALNETS"):D.index("END SPECIALNETS")]
LAY = {"Metal1": 8, "Metal2": 10, "Metal3": 30, "Metal4": 50, "Metal5": 67, "TopMetal1": 126, "TopMetal2": 134,
       "Via1": 19, "Via2": 29, "Via3": 49, "Via4": 66, "TopVia1": 125, "TopVia2": 133}
VIA_STACK = {"Via1": ("Metal1", "Metal2"), "Via2": ("Metal2", "Metal3"), "Via3": ("Metal3", "Metal4"),
             "Via4": ("Metal4", "Metal5"), "TopVia1": ("Metal5", "TopMetal1"), "TopVia2": ("TopMetal1", "TopMetal2")}
SEG = re.compile(r"(?:ROUTED|NEW)\s+(\w+)\s+(\d+)\s+(?:\+\s+SHAPE\s+\w+\s+)?\(\s*(-?\d+)\s+(-?\d+)\s*\)\s*(?:\(\s*(-?\d+|\*)\s+(-?\d+|\*)\s*\)|(\w+))")
regions = {}
via_cache = {}
def via_shapes(vname):
    if vname in via_cache:
        return via_cache[vname]
    c = ly.cell("VIA_" + vname); out = []
    if c is None:
        print("WARNING: no GDS cell for via", vname)
    else:
        for lname, gl in LAY.items():
            li = ly.find_layer(gl, 0)
            if li is None: continue
            r = pya.Region(c.begin_shapes_rec(li))
            if not r.is_empty(): out.append((lname, r))
    via_cache[vname] = out
    return out
for rec in re.split(r"\n\s*-\s+", sec)[1:]:
    net = rec.split()[0]
    if net not in ("VDD", "VSS", "VDDA", "IOVDD", "IOVSS"): continue
    for m in SEG.finditer(rec):
        lay, w, x1, y1, x2, y2, vname = m.groups()
        x1, y1, w = int(x1), int(y1), int(w)
        if vname:
            for lname, r in via_shapes(vname):
                regions.setdefault((net, lname), pya.Region()).insert(r.moved(x1, y1))
        else:
            x2 = x1 if x2 == "*" else int(x2); y2 = y1 if y2 == "*" else int(y2)
            box = pya.Box(x1 - w // 2, min(y1, y2), x1 + w // 2, max(y1, y2)) if x1 == x2 else pya.Box(min(x1, x2), y1 - w // 2, max(x1, x2), y1 + w // 2)
            regions.setdefault((net, lay), pya.Region()).insert(box)
nets = sorted({k[0] for k in regions})
print("special nets:", nets)
found = 0
for i, a in enumerate(nets):
    for b in nets[i + 1:]:
        for lname in LAY:
            ra = regions.get((a, lname)); rb = regions.get((b, lname))
            if ra is not None and rb is not None:
                ov = ra & rb
                if not ov.is_empty():
                    found += 1
                    print(f"OVERLAP {a} x {b} on {lname}: {ov.count()} polygons, e.g. {[str(p.bbox()) for p in list(ov.each())[:4]]}")
        for vl, (m1, m2) in VIA_STACK.items():
            for (na, nb) in ((a, b), (b, a)):
                rv = regions.get((na, vl))
                if rv is None: continue
                for ml in (m1, m2):
                    rm = regions.get((nb, ml))
                    if rm is not None:
                        ov = rv & rm
                        if not ov.is_empty():
                            found += 1
                            print(f"VIA-SHORT {na} {vl} on {nb} {ml}: {ov.count()} cuts, e.g. {[str(p.bbox()) for p in list(ov.each())[:4]]}")
print("overlaps between different supply nets:", found)
