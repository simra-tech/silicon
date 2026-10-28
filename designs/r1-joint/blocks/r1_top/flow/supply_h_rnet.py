# SPDX-License-Identifier: Apache-2.0
"""r1_top try h0: DC run on the extracted top-level supply network, with segment breakdown (track T8f).

  python3 supply_h_rnet.py <run dir with r1_top.gds and r1_top_assembly.json> <out dir> [typ|max] [VSS|VDD|VDDA]

Copy of supply_g_rnet.py (try g, track T8e; same geometry, ports, sheet values and solve; results equal on the same
GDS). Added in try h0 (track T8f):
  a. Segment breakdown: every node of the solved network is put in one region (south IO pad cells, south IO rail,
     other IO rows, south core rows, west/east core columns, north core rows, south feed area, ctrl grid, other core).
     For each pair of regions the script sums the element currents across the boundary (an exact cut set) and the
     current-weighted mean node voltage on both sides. Output key "breakdown".
  b. EM on the new feed shapes: the assembly JSON lists them (key "supply_h_feed", "em_items"); for each item the
     element currents across the mid line of the shape are summed (cut sum, only elements with both nodes inside the
     shape on its layer) and the gradient method of try g is applied along it. Output key "em_feed".
  c. Node list with layer and position (nodes_<tag>.json) for later checks.

Method (the RNetExtractor method of r1_isense/layout/pex/pex_build.py, applied to the chip):
  1. Geometry: every Metal1-TopMetal2 and Via1-TopVia2 shape of the chip except the shapes inside the macros, the
     decap row and the tie cell (the top-level shapes and the ring cell with its IO cells, flat), plus the power grid
     of r1_ctrl_top (its TopMetal1 stripes, TopVia2 and TopMetal2 straps). The macros are current sources at their
     supply pins; their other internal metal is not part of the network. The r1_ctrl current is spread over 63 ports
     (7 stripes x 9 heights, local y 50 ... 650) on its own TopMetal1 stripes.
  2. Net: KLayout LayoutToNetlist on these layers (metal-via-metal connections only); the VSS net is the net under the
     r1_bgr VSS tap (Metal4 trunk, chip (380, 336)). Check: the two VSS bond pads (pads 2 and 5) and every port lie on it.
  3. Resistance: KLayout RNetExtractor (klayout.pex, square counting) on the VSS net, sheet and via resistance from
     the PDK (typ: sg13g2_typ.itf values as r1_isense; max: process specification Rev 1.2 maxima, as supply_f.py).
  4. Ports: one polygon port per macro VSS hookup (the top-level shape at the macro pin), current = the block supply
     current (sum of its VDD and VDDA currents); the two pad openings (TopMetal2, 60 x 60 um) are 0 V (bond wires and
     package not modelled; both pads ideal ground). VDD: pad 1 at 0 V, VDDA: pad 7 at 0 V, every port draws its block
     current (the port voltage is minus the static drop from the pad).
  5. DC operating point with ngspice (pinned container): node voltages at every port; the isense - bgr ground offset
     with all currents, with the r1_ctrl current alone and with the isense current alone (superposition).
Outputs: <out>/vss_net.spice, vss_op.log, supply_g_rnet.json.
"""
import json
import os
import subprocess
import sys

import klayout.db as db
import klayout.pex as kp

RUN, OUT = sys.argv[1], sys.argv[2]
CORNER = sys.argv[3] if len(sys.argv) > 3 else "typ"
NET = sys.argv[4] if len(sys.argv) > 4 else "VSS"
TAG = CORNER if NET == "VSS" else "%s_%s" % (NET.lower(), CORNER)
os.makedirs(OUT, exist_ok=True)
LOG = open(os.path.join(OUT, "rnet_%s.log" % TAG), "w")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    LOG.write(s + "\n")
    LOG.flush()


asm = json.load(open(os.path.join(RUN, "r1_top_assembly.json")))
ly = db.Layout()
ly.read(os.path.join(RUN, "r1_top.gds"))
top = ly.cell("r1_top")
DBU = ly.dbu
LAY = {"M1": (8, 0), "V1": (19, 0), "M2": (10, 0), "V2": (29, 0), "M3": (30, 0), "V3": (49, 0), "M4": (50, 0),
       "V4": (66, 0), "M5": (67, 0), "TV1": (125, 0), "TM1": (126, 0), "TV2": (133, 0), "TM2": (134, 0)}
METALS = ["M1", "M2", "M3", "M4", "M5", "TM1", "TM2"]
VIAS = {"V1": ("M1", "M2"), "V2": ("M2", "M3"), "V3": ("M3", "M4"), "V4": ("M4", "M5"), "TV1": ("M5", "TM1"),
        "TV2": ("TM1", "TM2")}
# sheet (Ohm/sq) and via (Ohm per cut, cut size um): typ = sg13g2_typ.itf / process spec typ; max = process spec max
RS = {"typ": {"M1": 0.110, "M2": 0.088, "M3": 0.088, "M4": 0.088, "M5": 0.088, "TM1": 0.018, "TM2": 0.011},
      "max": {"M1": 0.135, "M2": 0.103, "M3": 0.103, "M4": 0.103, "M5": 0.103, "TM1": 0.021, "TM2": 0.0145}}
RV = {"typ": {"V1": 9.0, "V2": 9.0, "V3": 9.0, "V4": 9.0, "TV1": 2.2, "TV2": 1.1},
      "max": {"V1": 20.0, "V2": 20.0, "V3": 20.0, "V4": 20.0, "TV1": 4.0, "TV2": 2.2}}
VSZ = {"V1": 0.19, "V2": 0.19, "V3": 0.19, "V4": 0.19, "TV1": 0.42, "TV2": 0.90}

# ---- 1. flat geometry without the macros
skip = set()
for c in ly.each_cell():
    if c.name in ("r1_ctrl_top", "r1_adc", "r1_afe", "r1_isense", "r1_bias", "r1_osc", "r1_safe", "r1_bgr", "r1_t2f",
                  "r1_ls", "r1_gate_lv", "sg13g2_decap_8", "sg13g2_tiehi"):
        skip.add(c.cell_index())
ly2 = db.Layout()
ly2.dbu = DBU
t2 = ly2.create_cell("vssflat")
L2 = {}
for k, (l, d) in LAY.items():
    li = ly.find_layer(l, d)
    L2[k] = ly2.layer(l, d)
    if li is None:
        continue
    it = top.begin_shapes_rec(li)
    it.unselect_cells(list(skip))
    reg = db.Region(it)
    if k in ("TM1", "TV2", "TM2"):        # r1_ctrl_top power grid (TopMetal1 stripes, TopMetal2 straps) is kept
        for inst in top.each_inst():
            if inst.cell.name == "r1_ctrl_top":
                reg += db.Region(inst.cell.begin_shapes_rec(li)).transformed(inst.cplx_trans)
    t2.shapes(L2[k]).insert(reg)
    log("layer", k, "polygons", reg.count())

# ---- 2. VSS net
l2n = db.LayoutToNetlist(db.RecursiveShapeIterator(ly2, t2, []))
R = {k: l2n.make_layer(L2[k], k) for k in LAY}
for k in METALS:
    l2n.connect(R[k])
for v, (a, b) in VIAS.items():
    l2n.connect(R[v])
    l2n.connect(R[a], R[v])
    l2n.connect(R[v], R[b])
l2n.extract_netlist()
PROBE = {"VSS": (380.0, 336.0), "VDD": (380.0, 346.0), "VDDA": (380.0, 356.0)}[NET]     # south Metal4 trunks
net = l2n.probe_net(R["M4"], db.DPoint(*PROBE))
if net is None:
    raise SystemExit("no net under the %s trunk probe" % NET)
GEO = {k: l2n.shapes_of_net(net, R[k], True).merged() for k in LAY}
for k in LAY:
    log(NET, "net", k, "polygons", GEO[k].count(), "area um2 %.0f" % (GEO[k].area() * DBU * DBU))

# ---- 3. ports
P = asm["macro_pins_used"]


def box(b):
    return db.DBox(b[0], b[1], b[2], b[3])


PORTS = []          # (name, layer, DBox, current_mA)  current flows INTO the VSS net at the port
I = {"ctrl": 40.25, "afe": 2.00, "adc": 1.97, "isense": 1.588, "safe": 0.418, "bias": 0.196, "bgr": 0.080,
     "t2f": 0.0625, "osc": 0.317}
I_SRC = {"ctrl": "r1_ctrl 0.8 run r1ctrl_ll_20261027_t22 final/metrics.json power__total 0.0483 W (typ) / 1.2 V",
         "afe": "r1_afe README, VDDA ff 2.0 mA (as try f)",
         "adc": "r1_adc README layout B5: IDD 0.870 mA (SAR included) + IDDA 1.102 mA (tt, simulated)",
         "isense": "r1_isense README: 2 x 225 uA VDDA + 2 x 569 uA VDD (ff_hot)", "safe": "r1_safe README IDDA tt",
         "bias": "r1_bias README revision 2 ffx", "bgr": "r1_bgr README max", "t2f": "r1_t2f README",
         "osc": "r1_osc README post-layout max 316.6 uA"}
x_ctrl, y_ctrl = [r for r in asm["placement"] if r["instance"] == "u_ctrl"][0]["origin_um"]
for lx in [29.74, 105.34, 180.94, 256.54, 332.14, 407.74, 483.34]:
    x = x_ctrl + lx
    for ly_ in range(50, 651, 75):
        PORTS.append(("ctrl_s%d_y%d" % (int(lx), ly_), "TM1", db.DBox(x, y_ctrl + ly_ - 0.5, x + 2.2, y_ctrl + ly_ + 0.5),
                      I["ctrl"] / 63))
pb = box(P["isn"]["vss"])
PORTS.append(("isense", "M3", db.DBox(pb.left, pb.bottom - 0.6, pb.right, pb.bottom), I["isense"]))
for k, (x0, x1) in enumerate(((340.0, 360.0), (362.0, 382.0), (384.0, 404.0), (406.0, 430.0))):
    PORTS.append(("bgr_%d" % k, "M3", db.DBox(x0, 376.0, x1, 377.0), I["bgr"] / 4))
afe = [box(b) for b in P["afe_vss"]]
for k, b in enumerate(afe):
    PORTS.append(("afe_%d" % k, "M3", db.DBox(b.left, b.bottom - 0.6, b.right, b.bottom), I["afe"] / len(afe)))
b = box(P["adc"]["vss"])
PORTS.append(("adc", "M3", db.DBox(b.left, 375.4, b.right, 376.0), I["adc"]))
b = box(P["safe"]["vss"])
PORTS.append(("safe", "M3", db.DBox(1086.25, b.bottom, 1087.25, b.top), I["safe"]))
b = box(P["osc"]["vss"])
PORTS.append(("osc", "M3", db.DBox(1245.0, b.bottom, 1246.5, b.top), I["osc"]))
for k, fx in enumerate((452.0, 466.0, 480.0, 494.0, 508.0, 522.0)):
    PORTS.append(("bias_%d" % k, "M3", db.DBox(fx, 375.4, fx + 6.0, 376.0), I["bias"] / 6))
PORTS.append(("t2f", "M3", db.DBox(368.0, 621.5, 372.0, 622.5), I["t2f"]))
PADS = [("pad2", "TM2", db.DBox(607.0, 71.0, 667.0, 131.0)), ("pad5", "TM2", db.DBox(1033.0, 71.0, 1093.0, 131.0))]
if NET == "VDD":
    IV = {"ctrl": 40.25, "adc": 0.870, "isense": 1.138, "osc": 0.317, "bias": 0.05}
    I_SRC = {"ctrl": I_SRC["ctrl"], "adc": "r1_adc README layout B5 IDD 0.870 mA (SAR included, tt)",
             "isense": "r1_isense README 2 x 569 uA (ff_hot)", "osc": I_SRC["osc"],
             "bias": "r1_bias revision 2 vdd (estimate, as supply_f.py)"}
    PORTS = []
    for lx in [23.54, 99.14, 174.74, 250.34, 325.94, 401.54, 477.14]:
        x = x_ctrl + lx
        for ly_ in range(50, 651, 75):
            PORTS.append(("ctrl_s%d_y%d" % (int(lx), ly_), "TM1",
                          db.DBox(x, y_ctrl + ly_ - 0.5, x + 2.2, y_ctrl + ly_ + 0.5), IV["ctrl"] / 63))
    pb = box(P["isn"]["vdd"])
    PORTS.append(("isense", "M3", db.DBox(pb.left, pb.bottom - 0.6, pb.right, pb.bottom), IV["isense"]))
    b = box(P["osc"]["vdd"])
    PORTS.append(("osc", "M3", db.DBox(1245.0, b.bottom, 1246.5, b.top), IV["osc"]))
    b = box(P["adc"]["vdd"])
    PORTS.append(("adc", "M3", db.DBox(b.left, 375.4, b.right, 376.0), IV["adc"]))
    b = box(P["bias"]["vdd"])
    PORTS.append(("bias", "M3", db.DBox(564.0, b.bottom, 565.0, b.top), IV["bias"]))
    PADS = [("pad1", "TM2", db.DBox(465.0, 71.0, 525.0, 131.0))]
    I = IV
    # zero-current probes (where the drop is): south inner VDD row next to pad 1, south row under the strap, the
    # north VDD row at the ctrl, the inner west and east VDD columns at mid height
    for nm, lay, bx in [("probe_south_row_x495", "TM2", db.DBox(494.0, 350.0, 496.0, 352.0)),
                        ("probe_south_row_x578", "TM2", db.DBox(577.0, 350.0, 579.0, 352.0)),
                        ("probe_north_row_x800", "TM2", db.DBox(799.0, 1340.0, 801.0, 1342.0)),
                        ("probe_west_col_y1000", "TM2", db.DBox(350.0, 999.0, 352.0, 1001.0)),
                        ("probe_east_col_y1000", "TM1", db.DBox(1347.0, 999.0, 1349.0, 1001.0))]:
        PORTS.append((nm, lay, bx, 0.0))
elif NET == "VDDA":
    IV = {"afe": 2.00, "adc": 1.102, "isense": 0.450, "safe": 0.418, "bgr": 0.080, "bias": 0.196, "t2f": 0.0625}
    I_SRC = {"afe": I_SRC["afe"], "adc": "r1_adc README layout B5 IDDA 1.102 mA (tt)",
             "isense": "r1_isense README 2 x 225 uA (ff_hot)", "safe": I_SRC["safe"], "bgr": I_SRC["bgr"],
             "bias": I_SRC["bias"], "t2f": I_SRC["t2f"]}
    PORTS = []
    afv = [box(b) for b in P["afe_vdd"]]
    for k, b in enumerate(afv):
        PORTS.append(("afe_%d" % k, "M3", db.DBox(b.left, b.bottom - 0.6, b.right, b.bottom), IV["afe"] / len(afv)))
    b = box(P["adc"]["vdda"])
    PORTS.append(("adc", "M3", db.DBox(b.left, 375.4, b.right, 376.0), IV["adc"]))
    pb = box(P["isn"]["vdda"])
    PORTS.append(("isense", "M3", db.DBox(pb.left, pb.bottom - 0.6, pb.right, pb.bottom), IV["isense"]))
    b = box(P["safe"]["vdda"])
    PORTS.append(("safe", "M3", db.DBox(1338.14, b.bottom, 1339.0, b.top), IV["safe"]))
    PORTS.append(("bgr", "M3", db.DBox(380.0, 569.0, 386.0, 570.0), IV["bgr"]))
    b = box(P["bias"]["vdda"])
    PORTS.append(("bias", "M3", db.DBox(443.0, b.bottom, 444.0, b.top), IV["bias"]))
    PORTS.append(("t2f", "M3", db.DBox(369.0, 724.0, 373.0, 725.0), IV["t2f"]))
    PADS = [("pad7", "TM2", db.DBox(1569.0, 465.0, 1629.0, 525.0))]
    I = IV

LID = {k: i for i, k in enumerate(list(LAY))}
pp = {}
pmap = []          # global order -> (name, kind)
for name, lay, bx, cur in PORTS:
    poly = (GEO[lay] & db.Region(db.Box.from_dbox(bx * (1.0 / DBU)))).merged()
    if poly.is_empty():
        raise SystemExit("port %s: no %s of the VSS net inside %s" % (name, lay, bx))
    pg = sorted(poly.each(), key=lambda q: -q.area())[0]
    pp.setdefault(LID[lay], []).append(pg)
    pmap.append((name, lay, len(pp[LID[lay]]) - 1, cur))
for name, lay, bx in PADS:
    poly = (GEO[lay] & db.Region(db.Box.from_dbox(bx * (1.0 / DBU)))).merged()
    if poly.is_empty():
        raise SystemExit("pad %s: not on the VSS net" % name)
    pg = sorted(poly.each(), key=lambda q: -q.area())[0]
    pp.setdefault(LID[lay], []).append(pg)
    pmap.append((name, lay, len(pp[LID[lay]]) - 1, None))
log("ports", len(pmap))

# ---- 4. resistance network
tech = kp.RExtractorTech()
for k in METALS[1:]:
    c = kp.RExtractorTechConductor()
    c.layer = LID[k]
    c.resistance = RS[CORNER][k]
    c.algorithm = kp.Algorithm.SquareCounting
    c.triangulation_max_area = 25.0 if k in ("TM1", "TM2", "M5") else 9.0
    c.triangulation_min_b = 0.3
    tech.add_conductor(c)
for v, (a, b2) in VIAS.items():
    if v == "V1":
        continue
    t = kp.RExtractorTechVia()
    t.cut_layer = LID[v]
    t.bottom_conductor = LID[a]
    t.top_conductor = LID[b2]
    t.resistance = RV[CORNER][v] * VSZ[v] * VSZ[v]
    t.merge_distance = 0.0
    tech.add_via(t)
# Metal1 and Via1 are left out of the R network: the Metal1 IO-row VSS ring is one annular polygon (936 points, one
# hole) that the triangulation of klayout.pex rejects (internal error dbPLC.cc:543, probe RNET_PROBE=1). Leaving a
# parallel conductor out raises the resistance (conservative).
for _k in ("M1", "V1"):
    GEO[_k] = db.Region()
geo = {LID[k]: GEO[k] for k in LAY if not GEO[k].is_empty()}
if os.environ.get("RNET_PROBE"):
    # diagnostic: which conductor layer breaks the triangulation
    for k in METALS:
        t1 = kp.RExtractorTech()
        c = kp.RExtractorTechConductor()
        c.layer = LID[k]
        c.resistance = RS[CORNER][k]
        c.algorithm = kp.Algorithm.SquareCounting
        c.triangulation_max_area = 25.0
        c.triangulation_min_b = 0.3
        t1.add_conductor(c)
        try:
            r1 = kp.RNetExtractor(DBU).extract(t1, {LID[k]: GEO[k]}, {}, {})
            log("probe", k, "ok", r1.num_nodes())
        except RuntimeError as e:
            log("probe", k, "FAILED", e)
            for i, pg in enumerate(GEO[k].each()):
                try:
                    kp.RNetExtractor(DBU).extract(t1, {LID[k]: db.Region(pg)}, {}, {})
                except RuntimeError:
                    log("   polygon", i, "bbox", pg.bbox().to_dtype(DBU), "points", pg.num_points(), "holes", pg.holes())
    raise SystemExit("probe done")
ex = kp.RNetExtractor(DBU)
rn = ex.extract(tech, geo, {}, pp)
log("network: nodes", rn.num_nodes(), "elements", rn.num_elements())
rn.simplify()
log("simplified: nodes", rn.num_nodes(), "elements", rn.num_elements())
name_of = {}
k_int = 0
port_node = {}
NODE_XY = {}            # node name -> (layer name, x um, y um)
for node in rn.each_node():
    ty = node.type().to_s()
    _bx = node.location()
    _c = _bx.center()
    _ln = list(LAY)[node.layer()] if node.layer() is not None and node.layer() >= 0 else "?"
    if ty == "PolygonPort":
        lay_name = list(LAY)[node.layer()]
        m = [p for p in pmap if p[1] == lay_name and p[2] == node.port_index()][0]
        name_of[node.object_id()] = "p_" + m[0]
        port_node[m[0]] = "p_" + m[0]
    else:
        name_of[node.object_id()] = "n%d" % k_int
        k_int += 1
    NODE_XY[name_of[node.object_id()]] = (_ln, _c.x, _c.y)        # node.location() is a DBox in um
missing = [p[0] for p in pmap if p[0] not in port_node]
if missing:
    raise SystemExit("ports without a node: %s" % missing)
lines = ["* r1_top %s network (%s), RNetExtractor, from %s" % (NET, CORNER, "<G1_RESULTS_ROOT>/r1_top/" +
                                                                      os.path.basename(RUN.rstrip("/")))]
nr = 0
nopen = 0
ELEM = []
for e in rn.each_element():
    r = e.resistance()
    if r != r or r > 1e12:
        nopen += 1
        continue
    nr += 1
    ELEM.append((name_of[e.a().object_id()], name_of[e.b().object_id()], max(r, 1e-6)))
    lines.append("R%d %s %s %.6g" % (nr, name_of[e.a().object_id()], name_of[e.b().object_id()], max(r, 1e-6)))
log("resistors", nr, "open elements skipped", nopen)


def deck(sel, tag):
    d = list(lines)
    for name, lay, idx, cur in pmap:
        if cur is None:
            d.append("V%s p_%s 0 0" % (name, name))
        elif cur == 0.0:
            continue
        elif sel is None or name.startswith(sel):
            if NET == "VSS":
                d.append("I%s 0 p_%s %.6gm" % (name, name, cur))   # current into the VSS net at the port
            else:
                d.append("I%s p_%s 0 %.6gm" % (name, name, cur))   # current drawn from the supply net
    d += [".control", "op"]
    d += ["print " + " ".join("v(p_%s)" % p[0] for p in pmap[i:i + 8]) for i in range(0, len(pmap), 8)]
    d += [".endc", ".end"]
    f = os.path.join(OUT, "%s_%s_%s.spice" % (NET.lower(), CORNER, tag))
    open(f, "w").write("\n".join(d) + "\n")
    o = subprocess.run(["ngspice", "-b", f], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True).stdout
    open(f[:-6] + ".log", "w").write(o)
    v = {}
    for ln in o.splitlines():
        if ln.strip().startswith("v(p_") and "=" in ln:
            a, b3 = ln.split("=")
            v[a.strip()[4:-1]] = float(b3.split()[0])
    if len(v) != len(pmap):
        raise SystemExit("ngspice %s: %d of %d port voltages" % (tag, len(v), len(pmap)))
    return v


res = {"net": NET, "corner": CORNER, "method": __doc__.strip().splitlines()[0], "currents_mA": I,
       "current_sources": I_SRC, "resistors": nr, "ports": [p[0] for p in pmap], "runs": {}}


# EM on the trunks: all node voltages of the "all" deck, element currents, current through cut lines across a conductor
# (a cut line spans the full conductor width; every element of that layer whose end nodes lie on both sides of the
# line and inside the span carries a share of the current through the cut).
def solve_all():
    d = list(lines)
    for name, lay, idx, cur in pmap:
        if cur is None:
            d.append("V%s p_%s 0 0" % (name, name))
        elif cur != 0.0:
            d.append(("I%s 0 p_%s %.6gm" if NET == "VSS" else "I%s p_%s 0 %.6gm") % (name, name, cur))
    d += [".control", "op", "print all", ".endc", ".end"]
    f = os.path.join(OUT, "%s_%s_allnodes.spice" % (NET.lower(), CORNER))
    open(f, "w").write("\n".join(d) + "\n")
    o = subprocess.run(["ngspice", "-b", f], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       universal_newlines=True).stdout
    v = {"0": 0.0}
    for ln in o.splitlines():
        if " = " in ln:
            a, b3 = ln.split(" = ", 1)
            a = a.strip()
            try:
                v[a] = float(b3.split()[0])
            except ValueError:
                pass
    return v


SW = 10.0 if os.environ.get("RNET_STRAP10", "1") == "1" else 6.0
CUTS = {"VDD": [("IO-filler VDD strap Metal3 x %.0f (%.0f um)" % (f0 + 2, SW), "M3", "h", 325.0, f0 + 2, f0 + 2 + SW, SW)
                for f0 in (535.0, 677.0, 819.0, 961.0, 1103.0)] +
               [],
        # VDDA risers: the cut-line sum gave values above the total VDDA current (run g2/g3 try 1: 12.6, 135 and
        # 324 mA against 4.31 mA), so it is not used there; see GRAD and the bound rows of supply_g.py.
        "VDDA": [],
        "VSS": [("IO-filler VSS strap Metal4 x %.0f (30 um)" % (f0 + 9), "M4", "h", 325.0, f0 + 9, f0 + 39, 30.0)
                for f0 in (535.0, 677.0, 819.0, 961.0, 1103.0)] +
               []}
EM_W = {"M3": 2.0, "M4": 2.0, "M5": 2.0, "TM1": 15.0, "TM2": 16.0}
VALL = solve_all()
res["nodes_solved"] = len(VALL)
em_cuts = []
for nm, lay, ori, c0, lo, hi, w in CUTS[NET]:
    tot = 0.0
    n = 0
    for a, b, r in ELEM:
        la, xa, ya = NODE_XY.get(a, ("?", 0, 0))
        lb, xb, yb = NODE_XY.get(b, ("?", 0, 0))
        if la != lay or lb != lay or a not in VALL or b not in VALL:
            continue
        pa, pb = (ya, xa) if ori == "h" else (xa, ya)       # (coordinate across the cut, coordinate along it)
        qa, qb = (xa, xb) if ori == "h" else (ya, yb)
        if (pa - c0) * (pb - c0) < 0 and lo - 0.5 <= qa + (qb - qa) * (c0 - pa) / (pb - pa) <= hi + 0.5:
            ia = (VALL[a] - VALL[b]) / r
            tot += ia if pa < c0 else -ia
            n += 1
    lim = EM_W[lay] * w
    em_cuts.append({"cut": nm, "layer": lay, "I_mA": round(abs(tot) * 1e3, 3), "limit_mA": lim, "elements": n,
                    "pass": abs(tot) * 1e3 <= lim})
    log("EM cut", nm, "%.3f mA (limit %.1f, %d elements)" % (abs(tot) * 1e3, lim, n))
res["em_cuts"] = em_cuts
# EM by voltage gradient (try g3): on a long uniform strip the current is I = w * |dV/dl| / Rs. The node voltages of
# the "all" solve on that layer inside the strip are grouped by position along the strip (groups within 1 um merged),
# and the slope between neighbouring groups at least 5 um apart gives the strip current there; the item reports the
# largest value. Used for the trunks and risers where the cut-line sum is not valid (the RNetExtractor elements of a
# wide polygon join nodes that are not neighbours, so element currents of a cut line can cancel or add up wrongly).
GRAD = {"VDD": [("Metal4 VDD trunk 6 um (y 343-349)", "M4", "x", 343.0, 349.0, 371.0, 1360.0, 6.0),
                ] +
               [("ctrl VDD TopMetal1 stripe 2.2 um (local x %.2f)" % lx, "TM1", "y", 538.8 + lx, 538.8 + lx + 2.2,
                 684.0, 1352.3, 2.2) for lx in [23.54 + 75.6 * k for k in range(7)]],
        "VDDA": [("VDDA Metal4 trunk 8 um (y 352-360)", "M4", "x", 352.0, 360.0, 322.6, 1372.0, 8.0),
                 ("pad-7 VDDA riser Metal4 6 um (x 1366-1372)", "M4", "y", 1366.0, 1372.0, 360.0, 480.0, 6.0),
                 ("west VDDA riser Metal3 9.4 um (x 322.6-332)", "M3", "y", 322.6, 332.0, 362.0, 740.0, 9.4)],
        "VSS": [("Metal4 VSS trunk 8 um (y 332-340)", "M4", "x", 332.0, 340.0, 371.0, 1378.0, 8.0)]}
em_grad = []
for nm, lay, along, lo, hi, a0, a1, w in GRAD.get(NET, []):
    pts = []
    for n, (ln, x, y) in NODE_XY.items():
        if ln != lay or n not in VALL:
            continue
        acr, alo = (y, x) if along == "x" else (x, y)
        if lo - 0.01 <= acr <= hi + 0.01 and a0 <= alo <= a1:
            pts.append((alo, VALL[n]))
    pts.sort()
    grp = []
    for a, v in pts:
        if grp and a - grp[-1][0][-1] < 1.0:
            grp[-1][0].append(a)
            grp[-1][1].append(v)
        else:
            grp.append(([a], [v]))
    g = [(sum(a) / len(a), sum(v) / len(v)) for a, v in grp]
    best = (0.0, None)
    k0 = 0
    for k in range(1, len(g)):
        if g[k][0] - g[k0][0] < 5.0:
            continue
        i = w * abs(g[k][1] - g[k0][1]) / (g[k][0] - g[k0][0]) / RS[CORNER][lay]
        if i > best[0]:
            best = (i, (round(g[k0][0], 1), round(g[k][0], 1)))
        k0 = k
    lim = EM_W[lay] * w
    em_grad.append({"item": nm, "layer": lay, "I_mA": round(best[0] * 1e3, 3), "limit_mA": lim,
                    "at_um": best[1], "node_groups": len(g), "pass": best[0] * 1e3 <= lim})
    log("EM gradient", nm, "%.3f mA at %s (limit %.1f, %d node groups)" % (best[0] * 1e3, best[1], lim, len(g)))
res["em_gradient"] = em_grad


# ---- try h0 (T8f) additions: segment breakdown by cut sets, EM on the new feed shapes, node list
def region(x, y):
    if y < 299.0:
        return "S_io_pad"                  # south IO cells: pads and the IO-cell metal below the inner rail
    if y < 322.0 and 322.0 <= x <= 1378.0:
        return "S_io_rail"                 # south IO row, inner rail band (VSS TM1/M5, VDD M3)
    if x < 322.0 or x > 1378.0 or y > 1378.0 or y < 322.0:
        return "io_other"                  # west, east, north IO rows and the corners
    if y < 376.0:
        return "S_core_row"                # south core ring rows, Metal4 trunks, stacks, crossings
    if y > 1336.0:
        return "N_core_row"                # north core ring rows and the ctrl stripe ends above the ctrl ports
    if x < 365.0 or x > 1335.0:
        return "WE_columns"                # west and east core ring columns
    if 538.0 <= x <= 1072.0 and y >= 684.0:
        return "ctrl_grid"                 # ctrl 0.8 TopMetal1 stripes, TopVia2, TopMetal2 straps (ports inside)
    if y < 684.0:
        return "S_feed"                    # between the south core rows and the ctrl stripe ends
    return "core_other"


REG = {n: region(x, y) for n, (ln, x, y) in NODE_XY.items()}
cuts = {}
for a, b, r in ELEM:
    ra, rb = REG.get(a), REG.get(b)
    if ra is None or rb is None or ra == rb or a not in VALL or b not in VALL:
        continue
    i = (VALL[a] - VALL[b]) / r                       # conventional current a -> b
    k = tuple(sorted((ra, rb)))
    c = cuts.setdefault(k, {"I": 0.0, "wa": 0.0, "va": 0.0, "wb": 0.0, "vb": 0.0, "n": 0})
    s_ = 1.0 if ra == k[0] else -1.0                  # positive: from k[0] to k[1]
    c["I"] += s_ * i
    c["n"] += 1
    va, vb = (VALL[a], VALL[b]) if ra == k[0] else (VALL[b], VALL[a])
    c["wa"] += abs(i)
    c["va"] += abs(i) * va
    c["wb"] += abs(i)
    c["vb"] += abs(i) * vb
bd = {"regions": {}, "cuts": []}
for n, rg in REG.items():
    if n not in VALL:
        continue
    e = bd["regions"].setdefault(rg, {"nodes": 0, "V_min_mV": 1e9, "V_max_mV": -1e9})
    e["nodes"] += 1
    e["V_min_mV"] = round(min(e["V_min_mV"], VALL[n] * 1e3), 3)
    e["V_max_mV"] = round(max(e["V_max_mV"], VALL[n] * 1e3), 3)
for (ra, rb), c in sorted(cuts.items()):
    if c["wa"] <= 0:
        continue
    bd["cuts"].append({"from": ra, "to": rb, "I_mA": round(c["I"] * 1e3, 4), "elements": c["n"],
                       "V_from_mean_mV": round(c["va"] / c["wa"] * 1e3, 3), "V_to_mean_mV": round(c["vb"] / c["wb"] * 1e3, 3)})
res["breakdown"] = bd
for c in bd["cuts"]:
    log("cut %-10s -> %-10s I %9.3f mA  V %8.3f -> %8.3f mV  (%d elements)" % (c["from"], c["to"], c["I_mA"],
        c["V_from_mean_mV"], c["V_to_mean_mV"], c["elements"]))
for rg, e in sorted(bd["regions"].items()):
    log("region %-10s nodes %6d  V %8.3f .. %8.3f mV" % (rg, e["nodes"], e["V_min_mV"], e["V_max_mV"]))
em_feed = []
for it in asm.get("supply_h_feed", {}).get("em_items", []):
    if it["net"] != NET:
        continue
    x0, y0, x1, y1 = it["box"]
    lay, w = it["layer"], it["width"]
    vert = it["dir"] == "v"
    c0 = (y0 + y1) / 2.0 if vert else (x0 + x1) / 2.0
    tot = 0.0
    n = 0
    for a, b, r in ELEM:
        la, xa, ya = NODE_XY.get(a, ("?", 0, 0))
        lb, xb, yb = NODE_XY.get(b, ("?", 0, 0))
        if la != lay or lb != lay or a not in VALL or b not in VALL:
            continue
        if not (x0 - 0.01 <= xa <= x1 + 0.01 and x0 - 0.01 <= xb <= x1 + 0.01 and
                y0 - 0.01 <= ya <= y1 + 0.01 and y0 - 0.01 <= yb <= y1 + 0.01):
            continue
        pa, pb = (ya, yb) if vert else (xa, xb)
        if (pa - c0) * (pb - c0) < 0:
            ia = (VALL[a] - VALL[b]) / r
            tot += ia if pa < c0 else -ia
            n += 1
    # gradient along the shape (as try g GRAD)
    pts = []
    for nn, (ln, x, y) in NODE_XY.items():
        if ln == lay and nn in VALL and x0 - 0.01 <= x <= x1 + 0.01 and y0 - 0.01 <= y <= y1 + 0.01:
            pts.append(((y if vert else x), VALL[nn]))
    pts.sort()
    grp = []
    for a, v in pts:
        if grp and a - grp[-1][0][-1] < 1.0:
            grp[-1][0].append(a)
            grp[-1][1].append(v)
        else:
            grp.append(([a], [v]))
    g = [(sum(a) / len(a), sum(v) / len(v)) for a, v in grp]
    gbest = 0.0
    k0 = 0
    for k in range(1, len(g)):
        if g[k][0] - g[k0][0] < 5.0:
            continue
        gbest = max(gbest, w * abs(g[k][1] - g[k0][1]) / (g[k][0] - g[k0][0]) / RS[CORNER][lay])
        k0 = k
    lim = EM_W[lay] * w
    I_used = max(abs(tot), gbest) * 1e3
    em_feed.append({"item": it["name"], "layer": lay, "width_um": w, "I_cut_mA": round(abs(tot) * 1e3, 3),
                    "cut_elements": n, "I_gradient_mA": round(gbest * 1e3, 3), "I_used_mA": round(I_used, 3),
                    "limit_mA": lim, "pass": I_used <= lim})
    log("EM feed %-60s cut %8.3f mA (%d el.)  gradient %8.3f mA  limit %.1f" % (it["name"], abs(tot) * 1e3, n,
        gbest * 1e3, lim))
res["em_feed"] = em_feed
json.dump({"tag": TAG, "nodes": {n: [ln, round(x, 3), round(y, 3), round(VALL.get(n, float("nan")) * 1e3, 4)]
                                 for n, (ln, x, y) in NODE_XY.items()}},
          open(os.path.join(OUT, "nodes_%s.json" % TAG), "w"))
if NET != "VSS":
    v = deck(None, "all")
    res["runs"]["all"] = {"port_voltage_mV": {k: round(x * 1e3, 4) for k, x in v.items()}}
    res["static_drop_mV"] = {k: round(-x * 1e3, 3) for k, x in v.items() if not k.startswith("pad")}
    log("drops (mV)", json.dumps(res["static_drop_mV"]))
    json.dump(res, open(os.path.join(OUT, "supply_h_rnet_%s.json" % TAG), "w"), indent=1)
    raise SystemExit(0)
for sel, tag in ((None, "all"), ("ctrl", "ctrl_only"), ("isense", "isense_only")):
    v = deck(sel, tag)
    bgr = sum(v["bgr_%d" % k] for k in range(4)) / 4.0
    res["runs"][tag] = {"port_voltage_mV": {k: round(x * 1e3, 4) for k, x in v.items()},
                        "isense_minus_bgr_mV": round((v["isense"] - bgr) * 1e3, 4),
                        "bgr_mean_mV": round(bgr * 1e3, 4), "isense_mV": round(v["isense"] * 1e3, 4)}
    log(tag, "isense - bgr %.3f mV (isense %.3f, bgr %.3f)" % ((v["isense"] - bgr) * 1e3, v["isense"] * 1e3, bgr * 1e3))
# (a) path resistance isense <-> bgr: pads open, 1 mA in at the isense port, out at the four bgr ports (0 V);
# (b) effective offset resistance with the pads at 0 V: (V(isense) - V(bgr)) / I(isense), isense current alone.
def run_deck(body, tag, probes):
    f = os.path.join(OUT, "%s_%s_%s.spice" % (NET.lower(), CORNER, tag))
    d = list(lines) + body + [".control", "op", "print " + " ".join("v(p_%s)" % q for q in probes), ".endc", ".end"]
    open(f, "w").write("\n".join(d) + "\n")
    o = subprocess.run(["ngspice", "-b", f], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       universal_newlines=True).stdout
    open(f[:-6] + ".log", "w").write(o)
    vv = {}
    for ln in o.splitlines():
        if ln.strip().startswith("v(p_") and "=" in ln:
            a, b3 = ln.split("=")
            vv[a.strip()[4:-1]] = float(b3.split()[0])
    return vv


vv = run_deck(["Vbgr%d p_bgr_%d 0 0" % (k, k) for k in range(4)] + ["Itest 0 p_isense 1m"], "path", ["isense"])
res["path_R_isense_bgr_ohm"] = round(vv["isense"] / 1e-3, 4)
eff = res["runs"]["isense_only"]["isense_minus_bgr_mV"] / I["isense"]
res["offset_R_isense_bgr_pads_grounded_ohm"] = round(eff, 4)
log("path R isense-bgr (pads open) %.4f ohm; offset per isense current (pads 0 V) %.4f ohm" % (vv["isense"] / 1e-3, eff))
json.dump(res, open(os.path.join(OUT, "supply_h_rnet_%s.json" % TAG), "w"), indent=1)
