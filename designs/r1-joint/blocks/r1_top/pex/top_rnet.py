# SPDX-License-Identifier: Apache-2.0
"""r1_top try g, chip-level extraction (track T11), step 2: resistance network of every top-level net.

  python3 top_rnet.py <wire dir (top_wire.py output)> <out json> [typ|max] [NET,NET,... (default: all named nets)]

Method (the RNetExtractor method of flow/supply_g_rnet.py and r1_bgr/layout/pex_build.py):
  1. Net geometry: KLayout LayoutToNetlist on r1_top_wire.gds (metal and via layers); the net is found by its ports
     (ports.json of top_wire.py).
  2. Resistance: KLayout RNetExtractor (klayout.pex, square counting). Sheet and via values: typ = sg13g2_typ.itf
     (Metal1 0.110, Metal2-5 0.088, TopMetal1 0.018, TopMetal2 0.011 Ohm/sq; Via1-4 9, TopVia1 2.2, TopVia2 1.1 Ohm
     per cut); max = process specification Rev 1.2 maxima (as flow/supply_g_rnet.py).
  3. Ports: one polygon port per port shape of the net (macro pin, IO-cell pin, bond-pad opening). For VDD and VSS
     also the 63 r1_ctrl_top grid points of flow/supply_g_rnet.py (7 TopMetal1 stripes x 9 heights).
  4. Supply nets (VDD, VSS, VDDA, IOVDD, IOVSS): Metal1 and Via1 only inside the core box 322-1378 um (KLayout
     dbPLC.cc:543 on the Metal1 IO-row ring annulus, flow/supply_g_rnet.py F3); the IO-row Metal1 is left out
     (conservative). A port that does not touch the network is joined to the nearest node (distance recorded).
Output: one JSON with, per net: nodes [name, layer, x um, y um], elements [a, b, ohm], ports {port: node}.
"""
import json
import math
import os
import sys
import time

import klayout.db as db
import klayout.pex as kp

WD, OUTF = sys.argv[1], sys.argv[2]
CORNER = sys.argv[3] if len(sys.argv) > 3 else "typ"
SEL = sys.argv[4].split(",") if len(sys.argv) > 4 and sys.argv[4] else None
LAY = {"M1": (8, 0), "V1": (19, 0), "M2": (10, 0), "V2": (29, 0), "M3": (30, 0), "V3": (49, 0), "M4": (50, 0),
       "V4": (66, 0), "M5": (67, 0), "TV1": (125, 0), "TM1": (126, 0), "TV2": (133, 0), "TM2": (134, 0)}
METALS = ["M1", "M2", "M3", "M4", "M5", "TM1", "TM2"]
VIAS = {"V1": ("M1", "M2"), "V2": ("M2", "M3"), "V3": ("M3", "M4"), "V4": ("M4", "M5"), "TV1": ("M5", "TM1"),
        "TV2": ("TM1", "TM2")}
RS = {"typ": {"M1": 0.110, "M2": 0.088, "M3": 0.088, "M4": 0.088, "M5": 0.088, "TM1": 0.018, "TM2": 0.011},
      "max": {"M1": 0.135, "M2": 0.103, "M3": 0.103, "M4": 0.103, "M5": 0.103, "TM1": 0.021, "TM2": 0.0145}}
RV = {"typ": {"V1": 9.0, "V2": 9.0, "V3": 9.0, "V4": 9.0, "TV1": 2.2, "TV2": 1.1},
      "max": {"V1": 20.0, "V2": 20.0, "V3": 20.0, "V4": 20.0, "TV1": 4.0, "TV2": 2.2}}
VSZ = {"V1": 0.19, "V2": 0.19, "V3": 0.19, "V4": 0.19, "TV1": 0.42, "TV2": 0.90}
STEP = float(os.environ.get("T11_STEP_UM", "20"))
CORE = (322.0, 322.0, 1378.0, 1378.0)
SUPPLY = ("VDD", "VSS", "VDDA", "IOVDD", "IOVSS")
LID = {k: i for i, k in enumerate(LAY)}
LOGF = open(OUTF + ".log", "w")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    LOGF.write(s + "\n")
    LOGF.flush()


PJ = json.load(open(os.path.join(WD, "ports.json")))
DBU = PJ["dbu"]
ly = db.Layout()
ly.read(os.path.join(WD, "r1_top_wire.gds"))
top = ly.cell("r1_top_wire")
l2n = db.LayoutToNetlist(db.RecursiveShapeIterator(ly, top, []))
R = {k: l2n.make_layer(ly.layer(*LAY[k]), k) for k in LAY}
for k in METALS:
    l2n.connect(R[k])
for v, (a, b) in VIAS.items():
    l2n.connect(R[v])
    l2n.connect(R[a], R[v])
    l2n.connect(R[v], R[b])
l2n.extract_netlist()

ports_by_net = {}
for p in PJ["ports"]:
    if p["net"] and not p["net"].startswith("unnamed"):
        ports_by_net.setdefault(p["net"], []).append(p)
# r1_ctrl_top grid ports (flow/supply_g_rnet.py): VSS stripes at local x 29.74 + 75.6 k, VDD at 23.54 + 75.6 k
XC, YC = 538.8, 673.3
for net, x0 in (("VSS", 29.74), ("VDD", 23.54)):
    for k in range(7):
        x = XC + x0 + 75.6 * k
        for yy in range(50, 651, 75):
            bx = [x, YC + yy - 0.5, x + 2.2, YC + yy + 0.5]
            ports_by_net.setdefault(net, []).append({"name": "ctrlgrid/%s_s%d_y%d" % (net, k, yy), "kind": "ctrlgrid",
                                                      "layer": "TM1", "box_um": bx})


def port_region(p):
    if "box_um" in p:
        b = p["box_um"]
        return db.Region(db.Box(int(round(b[0] / DBU)), int(round(b[1] / DBU)), int(round(b[2] / DBU)), int(round(b[3] / DBU))))
    return db.Region(db.Polygon([db.Point(x, y) for x, y in p["poly"]]))


def inner(reg):
    pg = sorted(reg.each(), key=lambda q: -q.area())[0]
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


def tech_for(corner, layers):
    tech = kp.RExtractorTech()
    for k in METALS:
        if k not in layers:
            continue
        c = kp.RExtractorTechConductor()
        c.layer = LID[k]
        c.resistance = RS[corner][k]
        c.algorithm = kp.Algorithm.SquareCounting
        c.triangulation_max_area = 25.0 if k in ("TM1", "TM2", "M5") else 9.0
        c.triangulation_min_b = 0.3
        tech.add_conductor(c)
    for v, (a, b) in VIAS.items():
        if v not in layers:
            continue
        t = kp.RExtractorTechVia()
        t.cut_layer = LID[v]
        t.bottom_conductor = LID[a]
        t.top_conductor = LID[b]
        t.resistance = RV[corner][v] * VSZ[v] * VSZ[v]
        t.merge_distance = 0.0
        tech.add_via(t)
    return tech


res = {"corner": CORNER, "method": __doc__.strip().splitlines()[0], "nets": {}}
nets = sorted(ports_by_net) if SEL is None else SEL
for net in nets:
    t0 = time.time()
    plist = ports_by_net[net]
    # the net: probe at the first non-grid port
    p0 = [p for p in plist if p["kind"] != "ctrlgrid"][0]
    reg0 = port_region(p0)
    q = inner(reg0)
    lnet = l2n.probe_net(R[p0["layer"]], db.DPoint(q.x * DBU, q.y * DBU))
    GEO = {k: l2n.shapes_of_net(lnet, R[k], True).merged() for k in LAY}
    layers = [k for k in LAY if not GEO[k].is_empty()]
    drop = ()
    if net in SUPPLY:
        # Metal1/Via1 of a supply net: only inside the core box (the Metal1 IO-row ring annulus stops the
        # triangulation, dbPLC.cc:543); the core part carries the Metal1 straps to the level shifters, tie and decap cells
        core = db.Region(db.Box(int(CORE[0] / DBU), int(CORE[1] / DBU), int(CORE[2] / DBU), int(CORE[3] / DBU)))
        GEO["M1"] = GEO["M1"] & core
        GEO["V1"] = GEO["V1"] & core
        layers = [k for k in LAY if not GEO[k].is_empty()]
    use = [k for k in layers if k not in drop]
    pp, pmap, far = {}, [], []
    for p in plist:
        if p["layer"] in drop:
            far.append(p)
            continue
        poly = (GEO[p["layer"]] & port_region(p)).merged()
        if poly.is_empty():
            far.append(p)
            continue
        pg = sorted(poly.each(), key=lambda z: -z.area())[0]
        pp.setdefault(LID[p["layer"]], []).append(pg)
        pmap.append((p["name"], p["layer"], len(pp[LID[p["layer"]]]) - 1))
    geo = {LID[k]: GEO[k] for k in use}
    # vertex ports every STEP um along the signal wires, so that the network keeps nodes along each wire (the
    # extractor merges a plain wire into one element; the nodes carry the distributed capacitance, step 3)
    vp = {}
    if net not in SUPPLY:
        step = STEP / DBU
        for k in use:
            if k not in METALS:
                continue
            for pg in GEO[k].each():
                for tz in pg.decompose_trapezoids():
                    b = tz.bbox()
                    horiz = b.width() >= b.height()
                    L = b.width() if horiz else b.height()
                    n = int(L // step)
                    for i in range(1, n + 1):
                        if horiz:
                            q = db.Point(int(b.left + i * L / (n + 1)), b.center().y)
                        else:
                            q = db.Point(b.center().x, int(b.bottom + i * L / (n + 1)))
                        if tz.inside(q):
                            vp.setdefault(LID[k], []).append(q)
    try:
        rn = kp.RNetExtractor(DBU).extract(tech_for(CORNER, use), geo, vp, pp)
    except RuntimeError as e:
        if "M1" in use:
            log(net, "RNetExtractor failed with Metal1 (%s); Metal1/Via1 left out" % e)
            use = [k for k in use if k not in ("M1", "V1")]
            geo = {LID[k]: GEO[k] for k in use}
            for lid in list(pp):
                if lid in (LID["M1"],):
                    del pp[lid]
            far += [p for p in plist if p["layer"] == "M1"]
            pmap = [m for m in pmap if m[1] != "M1"]
            vp.pop(LID["M1"], None)
            rn = kp.RNetExtractor(DBU).extract(tech_for(CORNER, use), geo, vp, pp)
        else:
            raise
    nodes, names, port_node = [], {}, {}
    k = 0
    for node in rn.each_node():
        lay = list(LAY)[node.layer()] if node.layer() is not None and node.layer() >= 0 else "?"
        c = node.location().center()
        nm = "%s_%d" % (net, k)
        k += 1
        names[node.object_id()] = nm
        nodes.append([nm, lay, round(c.x, 4), round(c.y, 4)])
        if node.type().to_s() == "PolygonPort":
            m = [x for x in pmap if x[1] == lay and x[2] == node.port_index()]
            if m:
                port_node[m[0][0]] = nm
    elems = []
    nopen = 0
    for e in rn.each_element():
        r = e.resistance()
        if r != r or r > 1e12:
            nopen += 1
            continue
        elems.append([names[e.a().object_id()], names[e.b().object_id()], max(r, 1e-6)])
    # ports not in the network (Metal1 of a supply net, or no overlap): nearest node
    joined = {}
    for p in far:
        b = port_region(p).bbox()
        cx, cy = b.center().x * DBU, b.center().y * DBU
        best = min(nodes, key=lambda n: (n[2] - cx) ** 2 + (n[3] - cy) ** 2) if nodes else None
        if best is None:
            continue
        d = math.hypot(best[2] - cx, best[3] - cy)
        port_node[p["name"]] = best[0]
        joined[p["name"]] = round(d, 3)
    miss = [p["name"] for p in plist if p["name"] not in port_node]
    res["nets"][net] = {"nodes": nodes, "elements": elems, "ports": port_node, "layers": use,
                        "ports_joined_to_nearest_node_um": joined, "ports_missing": miss, "open_elements": nopen}
    log("%-16s layers %-28s nodes %6d elements %6d ports %3d joined %d missing %d  %.1f s" % (
        net, ",".join(use), len(nodes), len(elems), len(port_node), len(joined), len(miss), time.time() - t0))
json.dump(res, open(OUTF, "w"))
log("wrote", OUTF, "nets", len(res["nets"]), "nodes", sum(len(v["nodes"]) for v in res["nets"].values()),
    "elements", sum(len(v["elements"]) for v in res["nets"].values()))
