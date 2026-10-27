# SPDX-License-Identifier: Apache-2.0
"""r1_top try g, chip-level extraction (track T11), step 1: wiring layout, ports and top-level connectivity.

  python3 top_wire.py <run dir with r1_top.gds, r1_top_assembly.json, lvs/r1_top_g.cdl> <out dir>
        [--gds <other gds, e.g. the filled chip>] [--band NET1,NET2,... --band-um 10 [--nofill]]

Method:
  1. Wiring layout (flat cell r1_top_wire): every Metal1-TopMetal2 and Via1-TopVia2 shape of the chip except the shapes
     inside the macros (r1_ctrl_top, r1_adc, r1_afe, r1_isense, r1_osc, r1_safe, r1_bgr, r1_bias, r1_t2f, r1_gate_lv,
     r1_ls, the decap row and the tie cell): the top-level routing and the ring with its IO cells, flat. The power
     grid of r1_ctrl_top (its TopMetal1 stripes, TopVia2 and TopMetal2 straps) is kept, as flow/supply_g_rnet.py.
     The macros are black boxes: their devices and their internal metal are not in the layout, their pin shapes
     (pin purpose, datatype 2, of the macro cell itself) are added as metal. No FEOL layer is written, so the
     extraction sees no devices.
  2. Ports: every macro pin shape (named by the macro label inside it), the IO-cell pins (pad side, core side and the
     supply rails, datatype 2 of the IO cell), and the 24 bond-pad openings (ring TopMetal2 pins, named by the ring
     labels).
  3. Connectivity: KLayout LayoutToNetlist on the metal and via layers. Each net is named by the chip CDL of record
     (r1_top_g.cdl): a macro pin gives the CDL net of that pin in the instance line; an IO-cell pin gives the pad net
     (pad name), the core net (<PAD>_P2C, <PAD>_C2P, analog pad: <PAD>) or the ring supply. The check compares the
     set of macro pins of every extracted net with the CDL top level: missing nets (opens), nets with two CDL names
     (shorts), pins on the wrong net.
  4. Optional (--band): only the shapes within band-um of the listed nets are kept, and the metal fill (datatype 22)
     of the GDS is added as floating metal (the fill check).
Outputs: <out>/r1_top_wire.gds (one text label per named net, layer <metal>/25), <out>/ports.json, <out>/conn.json,
<out>/top_wire.log.
"""
import json
import os
import re
import sys
from collections import defaultdict

import klayout.db as db

RUN, OUT = sys.argv[1], sys.argv[2]
args = sys.argv[3:]
GDS = os.path.join(RUN, "r1_top.gds")
BAND, BAND_UM, FILL = None, 10.0, True
while args:
    a = args.pop(0)
    if a == "--gds":
        GDS = args.pop(0)
    elif a == "--band":
        BAND = args.pop(0).split(",")
    elif a == "--band-um":
        BAND_UM = float(args.pop(0))
    elif a == "--nofill":
        FILL = False
os.makedirs(OUT, exist_ok=True)
LOG = open(os.path.join(OUT, "top_wire.log"), "w")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    LOG.write(s + "\n")
    LOG.flush()


LAY = {"M1": (8, 0), "V1": (19, 0), "M2": (10, 0), "V2": (29, 0), "M3": (30, 0), "V3": (49, 0), "M4": (50, 0),
       "V4": (66, 0), "M5": (67, 0), "TV1": (125, 0), "TM1": (126, 0), "TV2": (133, 0), "TM2": (134, 0)}
METALS = ["M1", "M2", "M3", "M4", "M5", "TM1", "TM2"]
VIAS = {"V1": ("M1", "M2"), "V2": ("M2", "M3"), "V3": ("M3", "M4"), "V4": ("M4", "M5"), "TV1": ("M5", "TM1"),
        "TV2": ("TM1", "TM2")}
MACROS = ("r1_ctrl_top", "r1_adc", "r1_afe", "r1_isense", "r1_bias", "r1_osc", "r1_safe", "r1_bgr", "r1_t2f",
          "r1_ls", "r1_gate_lv", "sg13g2_decap_8", "sg13g2_tiehi")

asm = json.load(open(os.path.join(RUN, "r1_top_assembly.json")))
ly = db.Layout()
ly.read(GDS)
top = ly.cell("r1_top")
DBU = ly.dbu
log("gds", os.path.basename(GDS), "dbu", DBU)


# ---- CDL of record: top-level instance lines and macro pin orders
def norm(p):
    return re.sub(r"_+$", "", re.sub(r"[\[\]<>]", "_", p.lower()))


def read_cdl(path):
    sub, cur, lines = {}, None, []
    for raw in open(path):
        raw = raw.rstrip("\n")
        if raw.startswith("+") and lines:
            lines[-1] += " " + raw[1:]
        else:
            lines.append(raw)
    xlines = []
    for ln in lines:
        t = ln.split()
        if not t:
            continue
        if t[0].lower() == ".subckt":
            cur = t[1]
            sub[cur] = t[2:]
        elif t[0].lower() == ".ends":
            cur = None
        elif cur == "r1_top" and t[0][0] in "Xx":
            xlines.append(t)
    return sub, xlines


SUB, XL = read_cdl(os.path.join(RUN, "lvs", "r1_top_g.cdl"))
TOPPORTS = SUB["r1_top"]
INST = {}            # instance name -> (cell, {normalized pin: net}, [pins in order], [nets in order])
for t in XL:
    toks = [x for x in t[1:] if x != "/"]
    cell = toks[-1]
    nets = toks[:-1]
    pins = SUB[cell]
    if len(pins) != len(nets):
        raise SystemExit("CDL instance %s: %d nets, %s has %d pins" % (t[0], len(nets), cell, len(pins)))
    INST[t[0][1:]] = (cell, {norm(p): n for p, n in zip(pins, nets)}, pins, nets)
log("CDL top ports", len(TOPPORTS), "instances", len(INST))

# ---- instance names of the layout instances (placement of record; decap row in x order)
PLACE = {(r["macro"], round(r["origin_um"][0], 2), round(r["origin_um"][1], 2)): r["instance"] for r in asm["placement"]}
for r in asm.get("tie_cells", []):
    PLACE[(r["cell"], round(r["origin_um"][0], 2), round(r["origin_um"][1], 2))] = r["instance"]
minst = []           # (instance name, cell, ICplxTrans)
decaps = []
for inst in top.each_inst():
    c = inst.cell
    if c.name not in MACROS:
        continue
    for tr in inst.cell_inst.each_cplx_trans():
        t = db.ICplxTrans(inst.cplx_trans) if False else tr
        o = tr.disp
        key = (c.name, round(o.x * DBU, 2), round(o.y * DBU, 2))
        if c.name == "sg13g2_decap_8":
            decaps.append((o.x, tr))
            continue
        nm = PLACE.get(key)
        if nm is None:
            raise SystemExit("no placement record for %s at %s" % (c.name, key))
        minst.append((nm, c.name, tr))
for k, (x, tr) in enumerate(sorted(decaps, key=lambda q: q[0])):
    minst.append(("u_decap_ant_%d" % k, "sg13g2_decap_8", tr))
log("macro instances", len(minst))

# ---- 1. wiring layout
skip = [c.cell_index() for c in ly.each_cell() if c.name in MACROS]
ly2 = db.Layout()
ly2.dbu = DBU
t2 = ly2.create_cell("r1_top_wire")
GEO = {}
for k, (l, d) in LAY.items():
    li = ly.find_layer(l, d)
    reg = db.Region()
    if li is not None:
        it = top.begin_shapes_rec(li)
        it.unselect_cells(skip)
        reg = db.Region(it)
        if k in ("TM1", "TV2", "TM2"):
            for nm, cn, tr in minst:
                if cn == "r1_ctrl_top":
                    reg += db.Region(ly.cell(cn).begin_shapes_rec(li)).transformed(tr)
    GEO[k] = reg

# macro pins
PORTS = []           # dict(name, kind, inst, pin, layer, poly (Polygon, dbu))
NOPIN = {}
TXT = {k: (l, 25) for k, (l, d) in LAY.items() if k in METALS}
for nm, cn, tr in minst:
    c = ly.cell(cn)
    for k in METALS:
        l, _ = LAY[k]
        lp = ly.find_layer(l, 2)
        lt = ly.find_layer(l, 25)
        if lp is None:
            continue
        labels = []
        if lt is not None:
            labels = [(s.text_string, s.text.trans.disp) for s in c.shapes(lt).each() if s.is_text()]
        for s in c.shapes(lp).each():
            if not (s.is_box() or s.is_polygon() or s.is_path()):
                continue
            pg = s.polygon
            inside = [t for t, p in labels if pg.inside(p) or pg.bbox().enlarged(1, 1).contains(p)]
            if not inside:
                near = sorted(labels, key=lambda q: pg.bbox().center().distance(q[1]))
                inside = [near[0][0]] if near and pg.bbox().center().distance(near[0][1]) < 2000 else []
            good = [t for t in inside if norm(t) in INST.get(nm, (None, {}))[1]]
            if not good:
                # pin-purpose shape without a CDL pin label: device-level pins inside a macro (r1_bias, r1_osc
                # Metal1/GatPoly) or the r1_ctrl_top power stripes (kept as wiring); not a top-level port
                NOPIN[cn] = NOPIN.get(cn, 0) + 1
                continue
            pin = good[0]
            pt = pg.transformed(tr)
            GEO[k].insert(pt)
            PORTS.append({"name": "%s/%s" % (nm, pin), "kind": "macro", "inst": nm, "cell": cn, "pin": pin,
                          "layer": k, "poly": pt})

log("pin-purpose shapes without a CDL pin label (not ports)", NOPIN)
# IO cells of the ring and bond pads
ring_inst = [i for i in top.each_inst() if i.cell.name == "r1_padring"][0]
RT = ring_inst.cplx_trans
ring = ring_inst.cell
padlab = []
lt = ly.find_layer(134, 25)
for cc in [ring] + [i.cell for i in ring.each_inst()]:
    pass
it = ring.begin_shapes_rec(lt)
while not it.at_end():
    s = it.shape()
    if s.is_text():
        padlab.append((s.text_string, (RT * it.trans()) * s.text.trans.disp))
    it.next()
padlab = [(t, p) for t, p in padlab if t.upper() == t and not t.startswith("Device")]
log("bond-pad labels", len(padlab))
lp = ly.find_layer(134, 2)
it = ring.begin_shapes_rec(lp)
pads = []
while not it.at_end():
    s = it.shape()
    pg = s.polygon.transformed(RT * it.trans())
    lab = [t for t, p in padlab if pg.inside(p)]
    if lab:
        pads.append((lab[0], pg))
    it.next()
pcount = defaultdict(int)
for t, pg in sorted(pads, key=lambda q: (q[1].bbox().center().x, q[1].bbox().center().y)):
    pcount[t] += 1
    PORTS.append({"name": "pad/%s#%d" % (t, pcount[t]), "kind": "pad", "inst": "pad%d_%s" % (pcount[t], t), "cell": "bondpad",
                  "pin": t, "layer": "TM2", "poly": pg})
log("bond pads", len(pads))
IOS = []
for i in ring.each_inst():
    cn = i.cell.name
    if "IOPad" not in cn:
        continue
    tr = RT * i.cplx_trans
    kind = cn.replace("retained_fullchip_", "")
    c = i.cell
    entry = {"cell": kind, "pins": {}}
    for k in ("M2", "M3"):
        l, _ = LAY[k]
        lp2, lt2 = ly.find_layer(l, 2), ly.find_layer(l, 25)
        labels = [(s.text_string, s.text.trans.disp) for s in c.shapes(lt2).each() if s.is_text()]
        for s in c.shapes(lp2).each():
            pg = s.polygon
            lab = [t for t, p in labels if pg.inside(p) or pg.bbox().enlarged(1, 1).contains(p)]
            if not lab:
                continue
            pin = lab[0]
            if k == "M2" and pin in ("pad", "vdd", "vss", "iovdd", "iovss") and pg.bbox().bottom < 10 / DBU:
                pin = "pad_outer"
            if k == "M3" and pin not in ("vdd", "vss", "iovdd", "iovss"):
                continue
            if k == "M2" and pin in ("vdd", "vss", "iovdd", "iovss"):
                continue
            if pin in entry["pins"]:
                continue
            entry["pins"][pin] = (k, pg.transformed(tr))
    # pad name: the bond pad nearest to the outer pad pin
    po = entry["pins"]["pad_outer"][1].bbox().center()
    pn = sorted(pads, key=lambda q: q[1].bbox().center().distance(po))[0][0]
    entry["pad"] = pn
    entry["inst"] = "io_%s" % pn.lower()
    if sum(1 for e in IOS if e["pad"] == pn):
        entry["inst"] += "_%d" % (1 + sum(1 for e in IOS if e["pad"] == pn))
    IOS.append(entry)
    for pin, (k, pg) in entry["pins"].items():
        PORTS.append({"name": "%s/%s" % (entry["inst"], pin), "kind": "io", "inst": entry["inst"], "cell": kind,
                      "pin": pin, "layer": k, "poly": pg, "pad": pn})
log("IO cells", len(IOS), sorted((e["inst"], e["cell"]) for e in IOS))

# unique port names (a pin with two shapes, e.g. r1_afe vss: the second shape is "<inst>/<pin>#2")
_cnt = defaultdict(int)
for p in PORTS:
    _cnt[p["name"]] += 1
    if _cnt[p["name"]] > 1:
        p["name"] = "%s#%d" % (p["name"], _cnt[p["name"]])
# ---- optional band window and fill
if BAND:
    log("band mode: nets", BAND, "band", BAND_UM, "um")
for k in LAY:
    t2.shapes(ly2.layer(*LAY[k])).insert(GEO[k])

# ---- 3. connectivity
l2n = db.LayoutToNetlist(db.RecursiveShapeIterator(ly2, t2, []))
R = {k: l2n.make_layer(ly2.layer(*LAY[k]), k) for k in LAY}
for k in METALS:
    l2n.connect(R[k])
for v, (a, b) in VIAS.items():
    l2n.connect(R[v])
    l2n.connect(R[a], R[v])
    l2n.connect(R[v], R[b])
l2n.extract_netlist()


def inner_point(pg):
    c = pg.bbox().center()
    if pg.inside(c):
        return c
    for e in pg.each_edge_hull():
        m = db.Point((e.p1.x + e.p2.x) // 2, (e.p1.y + e.p2.y) // 2)
        for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2)):
            q = db.Point(m.x + dx, m.y + dy)
            if pg.inside(q):
                return q
    return c


NETS = {}            # cluster id -> list of port indices
cid_of = {}
for i, p in enumerate(PORTS):
    q = inner_point(p["poly"])
    net = l2n.probe_net(R[p["layer"]], db.DPoint(q.x * DBU, q.y * DBU))
    if net is None:
        p["net_id"] = None
        continue
    p["net_id"] = net.cluster_id
    NETS.setdefault(net.cluster_id, []).append(i)
    cid_of[net.cluster_id] = net


# CDL net of every port
def cdl_net(p):
    if p["kind"] == "macro":
        ent = INST.get(p["inst"])
        if ent is None:
            return None
        return ent[1].get(norm(p["pin"]))
    if p["kind"] == "pad":
        return p["pin"]
    pin, pad, cell = p["pin"], p["pad"], p["cell"]
    if pin in ("vdd", "vss", "iovdd", "iovss"):
        return pin.upper()
    if pin == "pad_outer":
        return pad
    if pin == "p2c":
        return pad + "_P2C"
    if pin == "c2p":
        return pad + "_C2P"
    if pin == "pad":
        return pad
    if pin == "padres":
        return pad + "_PADRES"
    return None


for p in PORTS:
    p["cdl"] = cdl_net(p)
named = {}
issues = []
for cid, idx in NETS.items():
    names = sorted(set(PORTS[i]["cdl"] for i in idx if PORTS[i]["cdl"]))
    if len(names) > 1:
        issues.append({"type": "short", "names": names, "ports": [PORTS[i]["name"] for i in idx]})
    nm = names[0] if names else "unnamed_%d" % cid
    named[cid] = nm
# CDL expectations: net -> set of macro pins
exp = defaultdict(set)
for iname, (cell, pmap, pins, nets) in INST.items():
    for pn, n in zip(pins, nets):
        exp[n].add("%s/%s" % (iname, norm(pn)))
got = defaultdict(set)
for cid, idx in NETS.items():
    for i in idx:
        p = PORTS[i]
        if p["kind"] == "macro":
            got[named[cid]].add("%s/%s" % (p["inst"], norm(p["pin"])))
nets_by_name = defaultdict(list)
for cid, nm in named.items():
    nets_by_name[nm].append(cid)
for nm, cids in nets_by_name.items():
    if len(cids) > 1 and not nm.startswith("unnamed"):
        sizes = [len(NETS[c]) for c in cids]
        issues.append({"type": "open (one CDL net in %d layout nets)" % len(cids), "names": [nm], "ports_per_piece": sizes,
                       "pieces": [[PORTS[i]["name"] for i in NETS[c]] for c in cids]})
cmp_rows = []
for n in sorted(set(exp) | set(got)):
    e, g = exp.get(n, set()), got.get(n, set())
    if e != g:
        cmp_rows.append({"net": n, "missing_in_layout": sorted(e - g), "extra_in_layout": sorted(g - e)})
log("extracted nets with ports", len(NETS), "named", sum(1 for v in named.values() if not v.startswith("unnamed")))
log("issues", len(issues), "CDL pin-set differences", len(cmp_rows))
for x in issues[:40]:
    log("ISSUE", json.dumps(x)[:600])
for x in cmp_rows[:80]:
    log("DIFF", json.dumps(x)[:600])
cdl_top_nets = set(n for t in XL for n in [x for x in t[1:] if x != "/"][:-1])
conn = {"gds": os.path.basename(GDS), "cdl_top_ports": TOPPORTS, "nets": {}, "issues": issues, "pinset_diffs": cmp_rows,
        "cdl_nets_at_macros": len(exp), "layout_nets_with_ports": len(NETS),
        "cdl_nets_missing_in_layout": sorted(n for n in exp if n not in nets_by_name),
        "io_cells": [{k: v for k, v in e.items() if k != "pins"} | {"pins": sorted(e["pins"])} for e in IOS]}
for nm, cids in sorted(nets_by_name.items()):
    conn["nets"][nm] = {"pieces": len(cids), "ports": sorted(PORTS[i]["name"] for c in cids for i in NETS[c])}
json.dump(conn, open(os.path.join(OUT, "conn.json"), "w"), indent=1)

# ---- outputs: ports.json and the wiring GDS with one label per named net
pj = []
for p in PORTS:
    q = dict(p)
    q["poly"] = [[pt.x, pt.y] for pt in p["poly"].each_point_hull()]
    q["net"] = named.get(p["net_id"]) if p["net_id"] is not None else None
    pj.append(q)
json.dump({"dbu": DBU, "ports": pj, "nets": {nm: cids for nm, cids in nets_by_name.items()}}, open(os.path.join(OUT, "ports.json"), "w"))

lab_done = set()
for p in PORTS:
    nm = named.get(p.get("net_id"))
    if nm is None or nm.startswith("unnamed") or nm in lab_done:
        continue
    q = inner_point(p["poly"])
    t2.shapes(ly2.layer(*TXT[p["layer"]])).insert(db.Text(nm, db.Trans(q)))
    lab_done.add(nm)

# one substrate tap (Activ, pSD, Cont, Metal1) inside the black-boxed r1_adc box, and PWell over the die: the PDK LVS
# deck that kpex runs drops a circuit without any device (empty LVS database, run kpex_full try 1); the tap is its
# own one-shape net (T11_SUBTAP) and carries no port
TAP = (800.0, 470.0)


def dbox(x0, y0, x1, y1):
    return db.Box(int(round(x0 / DBU)), int(round(y0 / DBU)), int(round(x1 / DBU)), int(round(y1 / DBU)))


def add_tap(cell, lay):
    x, y = TAP
    cell.shapes(lay.layer(1, 0)).insert(dbox(x - 0.5, y - 0.5, x + 0.5, y + 0.5))
    cell.shapes(lay.layer(14, 0)).insert(dbox(x - 0.7, y - 0.7, x + 0.7, y + 0.7))
    cell.shapes(lay.layer(6, 0)).insert(dbox(x - 0.08, y - 0.08, x + 0.08, y + 0.08))
    cell.shapes(lay.layer(8, 0)).insert(dbox(x - 0.25, y - 0.25, x + 0.25, y + 0.25))
    cell.shapes(lay.layer(8, 25)).insert(db.Text("T11_SUBTAP", db.Trans(db.Point(int(x / DBU), int(y / DBU)))))
    cell.shapes(lay.layer(46, 0)).insert(dbox(0, 0, 1700, 1700))


if BAND:
    keep = db.Region()
    for nm in BAND:
        for cid in nets_by_name.get(nm, []):
            net = cid_of[cid]
            for k in LAY:
                keep += l2n.shapes_of_net(net, R[k], True)
    win = keep.merged().sized(int(BAND_UM / DBU))
    log("band window area um2 %.0f" % (win.area() * DBU * DBU))
    ly3 = db.Layout()
    ly3.dbu = DBU
    t3 = ly3.create_cell("r1_top_wire")
    nfill = 0
    for k, (l, d) in LAY.items():
        r = db.Region(t2.begin_shapes_rec(ly2.layer(l, d))) & win
        if FILL and k in METALS:
            lf = ly.find_layer(l, 22)
            if lf is not None:
                it = top.begin_shapes_rec(lf)
                it.unselect_cells(skip)
                fr = db.Region(it) & win
                nfill += fr.count()
                r += fr
        t3.shapes(ly3.layer(l, d)).insert(r)
        tl = ly2.find_layer(l, 25)
        if tl is not None:
            for s in t2.shapes(tl).each():
                if win.interacting(db.Region(db.Box(s.text.trans.disp, s.text.trans.disp).enlarged(1, 1))).count():
                    t3.shapes(ly3.layer(l, 25)).insert(s.text)
    log("band layout: fill polygons", nfill)
    add_tap(t3, ly3)
    ly3.write(os.path.join(OUT, "r1_top_wire.gds"))
else:
    add_tap(t2, ly2)
    ly2.write(os.path.join(OUT, "r1_top_wire.gds"))
log("wrote", os.path.join(OUT, "r1_top_wire.gds"))
