# SPDX-License-Identifier: Apache-2.0
"""r1_top try g, chip-level extraction (track T11): kpex 2.5D on tiles (fallback for the full-chip kpex run time).

  python3 kpex_tiles.py prepare <wire dir> <tiles dir> <n> <halo um>
  python3 kpex_tiles.py merge   <wire dir> <tiles dir> <n>

prepare: the wiring layout r1_top_wire.gds is cut into n x n tiles (die 0-1700 um), each with a halo; every piece of a
  named net in a tile carries a label with the net name (so a net clipped by the tile keeps its name); one LVS
  database per tile (make_lvsdb.py layer names) for kpex --lvsdb.
merge: from each tile's kpex report database only the contributions whose location lies in the tile core (without
  the halo) are kept, so every contribution is counted once. The report database prints values rounded to 0.001 fF,
  so the exact pair totals of the tile CSV are split over the contributions in proportion to the printed values
  (a value printed as 0.0 counts as 0.00025 fF), and the core share is kept. The result is written as one CSV (pair
  totals, fF) and one JSON of located contributions, which top_netlist.py reads in place of the full-chip output.
"""
import csv
import gzip
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict

MODE, WD, TD, N = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
HALO = float(sys.argv[5]) if len(sys.argv) > 5 else 20.0
DIE = 1700.0
LAY = {"M1": (8, 0), "V1": (19, 0), "M2": (10, 0), "V2": (29, 0), "M3": (30, 0), "V3": (49, 0), "M4": (50, 0),
       "V4": (66, 0), "M5": (67, 0), "TV1": (125, 0), "TM1": (126, 0), "TV2": (133, 0), "TM2": (134, 0)}
METALS = ["M1", "M2", "M3", "M4", "M5", "TM1", "TM2"]
VIAS = {"V1": ("M1", "M2"), "V2": ("M2", "M3"), "V3": ("M3", "M4"), "V4": ("M4", "M5"), "TV1": ("M5", "TM1"),
        "TV2": ("TM1", "TM2")}
os.makedirs(TD, exist_ok=True)


def tiles():
    s = DIE / N
    for i in range(N):
        for j in range(N):
            yield "t%d_%d" % (i, j), (i * s, j * s, (i + 1) * s, (j + 1) * s)


if MODE == "prepare":
    import klayout.db as db
    ly = db.Layout()
    ly.read(os.path.join(WD, "r1_top_wire.gds"))
    top = ly.cell("r1_top_wire")
    DBU = ly.dbu
    l2n = db.LayoutToNetlist(db.RecursiveShapeIterator(ly, top, []))
    R = {k: l2n.make_layer(ly.layer(*LAY[k]), k) for k in LAY}
    T = {k: l2n.make_text_layer(ly.layer(LAY[k][0], 25), k + "_t") for k in METALS}
    for k in METALS:
        l2n.connect(R[k])
        l2n.connect(R[k], T[k])
    for v, (a, b) in VIAS.items():
        l2n.connect(R[v])
        l2n.connect(R[a], R[v])
        l2n.connect(R[v], R[b])
    l2n.extract_netlist()
    c = l2n.netlist().circuit_by_name("r1_top_wire")
    named = [(n.name, n) for n in c.each_net() if n.name]
    NG = {nm: {k: l2n.shapes_of_net(n, R[k], True) for k in METALS} for nm, n in named}
    FULL = {k: db.Region(top.begin_shapes_rec(ly.layer(*LAY[k]))) for k in LAY}
    for name, (x0, y0, x1, y1) in tiles():
        box = db.Box(int((x0 - HALO) / DBU), int((y0 - HALO) / DBU), int((x1 + HALO) / DBU), int((y1 + HALO) / DBU))
        reg = db.Region(box)
        o = db.Layout()
        o.dbu = DBU
        t = o.create_cell("r1_top_wire")
        ns = 0
        for k in LAY:
            r = FULL[k] & reg
            ns += r.count()
            t.shapes(o.layer(*LAY[k])).insert(r)
        nl = 0
        for nm, geo in NG.items():
            for k in METALS:
                for pg in (geo[k] & reg).each():
                    c0 = pg.bbox().center()
                    p = c0 if pg.inside(c0) else None
                    if p is None:
                        for e in pg.each_edge():
                            m = db.Point((e.p1.x + e.p2.x) // 2, (e.p1.y + e.p2.y) // 2)
                            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                                q = db.Point(m.x + dx, m.y + dy)
                                if pg.inside(q):
                                    p = q
                                    break
                            if p is not None:
                                break
                    if p is not None:
                        t.shapes(o.layer(LAY[k][0], 25)).insert(db.Text(nm, db.Trans(p)))
                        nl += 1
        d = os.path.join(TD, name)
        os.makedirs(d, exist_ok=True)
        o.write(os.path.join(d, "r1_top_wire.gds"))
        print(name, "shapes", ns, "labels", nl)
elif MODE == "merge":
    VAL = re.compile(r"([0-9.eE+-]+) fF$")
    NUM = re.compile(r"(-?[0-9.]+),(-?[0-9.]+)")
    pair = defaultdict(float)
    contrib = []
    for name, (x0, y0, x1, y1) in tiles():
        kd = os.path.join(TD, name, "kpex")
        if not os.path.isdir(kd):
            raise SystemExit("tile %s: no kpex output" % name)
        kd = os.path.join(kd, os.listdir(kd)[0])
        rdb = [f for f in os.listdir(kd) if f.endswith("_pex_report.rdb.gz")][0]
        seen = set()
        n_in = 0
        tile_all = defaultdict(float)     # pair -> sum of weights of all contributions of the tile (core + halo)
        tile_core = []                     # (pair key, weight, x, y) of the core contributions
        for ev, el in ET.iterparse(gzip.open(os.path.join(kd, rdb)), events=("end",)):
            if el.tag != "item":
                continue
            cat = el.findtext("category") or ""
            comps = cat.strip("'").split("'.'")
            kind = comps[0]
            key = None
            if kind == "[C] Overlap" and comps[-1] == "Overlap Area":
                nets = re.split(r" (?:\u2013|\\342\\200\\223) ", comps[3])   # en dash, raw or octal-escaped in the XML
                key, val = cat, comps[4]
            elif kind.startswith("[C] Fringe") and comps[-1] == "Inside Edge":
                nets = [comps[2].split("=", 1)[1], comps[4].split("=", 1)[1]]
                key, val = cat, comps[5]
            elif kind == "[C] Sidewall":
                nets = [comps[2].split("=", 1)[1], comps[3].split("=", 1)[1]]
                key, val = cat, comps[4]
            if key is not None and key not in seen:
                seen.add(key)
                m = VAL.search(val)
                v = float(m.group(1)) if m else 0.0
                vals = el.find("values")
                g = vals.find("value").text if vals is not None and vals.find("value") is not None else ""
                xy = [(float(p), float(q)) for p, q in NUM.findall(g)]
                if xy and len(nets) == 2:
                    x = sum(p for p, q in xy) / len(xy)
                    y = sum(q for p, q in xy) / len(xy)
                    k2 = tuple(sorted(nets))
                    w = v if v > 0 else 0.00025      # a value printed as 0.0 fF is below 0.0005 fF
                    tile_all[k2] += w
                    if x0 <= x < x1 and y0 <= y < y1:
                        tile_core.append((k2, w, x, y))
                        n_in += 1
            el.clear()
        # exact pair totals of the tile (CSV), split by the weights; only the core share is kept
        csvf = [f for f in os.listdir(kd) if f.endswith("_k25d_pex_netlist.csv")][0]
        ex = defaultdict(float)
        for row in csv.reader(open(os.path.join(kd, csvf)), delimiter=";"):
            if row and row[0].startswith("C"):
                ex[tuple(sorted(row[1:3]))] += float(row[3])
        miss = sum(c for k2, c in ex.items() if tile_all.get(k2, 0) == 0)
        for k2, w, x, y in tile_core:
            f = ex.get(k2, 0.0) / tile_all[k2]
            a, b = k2
            if a.startswith("$"):
                a = "%s:%s" % (name, a)
            if b.startswith("$"):
                b = "%s:%s" % (name, b)
            a, b = sorted((a, b))
            pair[(a, b)] += w * f
            contrib.append([a, b, w * f, round(x, 3), round(y, 3)])
        print(name, "contributions in core", n_in, "CSV total %.1f fF, pairs without located contributions %.3f fF" % (
            sum(ex.values()), miss))
    with open(os.path.join(TD, "merged_k25d_pex_netlist.csv"), "w") as f:
        f.write("Device;Net1;Net2;Capacitance [fF];Resistance [Ohm]\n")
        for k, ((a, b), c) in enumerate(sorted(pair.items())):
            f.write("C%d;%s;%s;%.6g;\n" % (k + 1, a, b, c))
    json.dump(contrib, open(os.path.join(TD, "merged_contributions.json"), "w"))
    print("pairs", len(pair), "contributions", len(contrib), "total fF %.1f" % sum(pair.values()))
