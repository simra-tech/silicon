# SPDX-License-Identifier: Apache-2.0
"""R1 top-level assembly, try e (track T8): floorplan C4 of S7 on the 1700 um ring of record, KLayout Python.

Places the 1700 um ring (r1_padring revision d) and every macro that exists today at its C4 position:
r1_ctrl_top 0.4 (t7), r1_afe (revision E of record), r1_isense (layout a of record), r1_osc (revision 2, layout r2d, commit 679a97320),
r1_safe, r1_bgr, r1_t2f, r1_bias (layout of record, commit 934b90195), r1_gate_lv, 6 x r1_ls. r1_adc is a
placeholder outline (S7 slot 439.0 x 182.3 um) with Metal3 pin stubs. Builds the core supplies (ring identity,
r1_ctrl stripes, north and south straps, south Metal4 trunks, VDDA feed from pad 7 and a west VDDA riser), the
coordinator MIM rule (TopMetal2 only over the AFE, the only MIM block under a ring column in C4) and every signal
route that has both ends today. Writes r1_top.gds and r1_top_assembly.json.

Usage (inside the pinned container, repository root as cwd):
  python3 designs/r1-joint/blocks/r1_top/layout/r1_top_assemble_e.py <results_root> <out_dir> <ofrecord_dir>
<ofrecord_dir> holds the block GDS of record of r1_afe and r1_isense (taken from git HEAD; the working-tree
files of these blocks were revisions in progress when try e started). r1_osc is read from the repository
(revision 2 committed during try e; run asm-20261021-e used layout k and is superseded). Their sha256 are checked below.

Conventions as try d: units um, chip origin at the lower-left die corner; vertical segments on Metal3, horizontal
segments on Metal4, Via3 at the bends; distinct tracks per net. Coordinates and their reasons: README "Try e".
"""
import hashlib
import json
import os
import sys

import klayout.db as db

RES = sys.argv[1]
OUT = sys.argv[2]
OFR = sys.argv[3]
os.makedirs(OUT, exist_ok=True)
HERE = os.path.dirname(os.path.abspath(__file__))
BLK = os.path.normpath(os.path.join(HERE, "..", ".."))           # designs/r1-joint/blocks
REPO = os.path.normpath(os.path.join(BLK, "..", "..", ".."))
DIE = 1700.0

RING_GDS = os.path.join(RES, "r1_padring/ring-20261021-d/r1_padring_1700.gds")
RING_SHA = "81bba04b3c0655ece75587d6c90b159d4bb860e0dbe0e3dd80e2c65c50d0725d"
CTRL_GDS = os.path.join(RES, "r1_ctrl/r1ctrl_ll_20261021_t7/flow/runs/r1ctrl_ll_20261021_t7/final/gds/r1_ctrl_top.gds")
MACRO_GDS = {
    "r1_ctrl_top": CTRL_GDS,
    "r1_bgr": os.path.join(BLK, "r1_bgr/layout/r1_bgr.gds"),
    "r1_t2f": os.path.join(BLK, "r1_t2f/layout/r1_t2f.gds"),
    "r1_ls": os.path.join(BLK, "r1_ls/layout/r1_ls.gds"),
    "r1_gate_lv": os.path.join(BLK, "r1_gate/layout/r1_gate_lv_filled.gds"),
    "r1_safe": os.path.join(BLK, "r1_safe/layout/r1_safe.gds"),
    "r1_bias": os.path.join(BLK, "r1_bias/layout/r1_bias.gds"),
    "r1_afe": os.path.join(OFR, "r1_afe.gds"),
    "r1_isense": os.path.join(OFR, "r1_isense.gds"),
    "r1_osc": os.path.join(BLK, "r1_osc/layout/r1_osc.gds"),
}
# GDS of record (block README / commit) - the generator refuses other files
EXPECT_SHA = {
    "r1_afe": "0181e98856e8bdd4500bb8d54b271c2a88209e3f5078f4a794a235af234891e1",      # revision E, d17d505f7
    "r1_isense": "054373fc72862c2a4567cda9e8c223ae0c2599604ad4f17f81115a7699e3f515",   # layout a, db5461161
    "r1_osc": "7c5fb60fdbbfa3cce7714520d3bc652292f0ff964452e3bf4afe226ea68ba971",      # revision 2, layout r2d, 679a97320
    "r1_bias": "354fa73cbf92bb82f4e0b1eea57acd3cd12aea2eeb19102be28ca925b07d2d14",     # 934b90195
}

# ---------------------------------------------------------------- layers
LY = {"M1": (8, 0), "V1": (19, 0), "M2": (10, 0), "V2": (29, 0), "M3": (30, 0), "V3": (49, 0),
      "M4": (50, 0), "V4": (66, 0), "M5": (67, 0), "TV1": (125, 0), "TM1": (126, 0), "TV2": (133, 0),
      "TM2": (134, 0), "BND": (189, 4), "TXT": (63, 0)}
PINP = {"M2": (10, 2), "M3": (30, 2), "M4": (50, 2)}
LBL = {"M2": (10, 25), "M3": (30, 25), "M4": (50, 25), "M5": (67, 25)}
STACK = ["M1", "M2", "M3", "M4", "M5", "TM1", "TM2"]
VIA_BETWEEN = {("M1", "M2"): "V1", ("M2", "M3"): "V2", ("M3", "M4"): "V3", ("M4", "M5"): "V4",
               ("M5", "TM1"): "TV1", ("TM1", "TM2"): "TV2"}
VIA_RULE = {"V1": (0.19, 0.29, 0.10), "V2": (0.19, 0.29, 0.10), "V3": (0.19, 0.29, 0.10),
            "V4": (0.19, 0.29, 0.10), "TV1": (0.42, 0.42, 0.45), "TV2": (0.90, 1.06, 0.55)}
W = 0.5

ly = db.Layout()
ly.dbu = 0.001
L = {k: ly.layer(*v) for k, v in LY.items()}
LP = {k: ly.layer(*v) for k, v in PINP.items()}
LT = {k: ly.layer(*v) for k, v in LBL.items()}


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


# ---------------------------------------------------------------- ring of record (1700 um, revision d)
if sha256(RING_GDS) != RING_SHA:
    raise SystemExit("ring GDS hash differs from the ring of record")
ly.read(RING_GDS)
ring = ly.cell("r1_padring")
removed_fill = 0
for inst in list(ring.each_inst()):
    if inst.cell.name.endswith("_FILL_CELL"):
        removed_fill += 1
        inst.delete()
ly.cleanup()
top = ly.create_cell("r1_top")
top.insert(db.CellInstArray(ring.cell_index(), db.Trans()))
_lt = ly.layer(134, 25)
RING_LABELS = []
for _s in ring.shapes(_lt).each():
    if _s.is_text():
        top.shapes(_lt).insert(_s.dtext)
        RING_LABELS.append(_s.text_string)


def B(x0, y0, x1, y1):
    return db.DBox(min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))


SHAPES = []


def rect(layer, box, net, cell=None):
    (cell or top).shapes(L[layer]).insert(box)
    if cell is None:
        SHAPES.append((layer, box, net))


def label(layer, x, y, text):
    top.shapes(LT[layer]).insert(db.DText(text, db.DTrans(x, y)))


def via_array(via, box, cell=None):
    s, sp, enc = VIA_RULE[via]
    x0, y0, x1, y1 = box.left + enc, box.bottom + enc, box.right - enc, box.top - enc
    if x1 - x0 < s - 1e-6 or y1 - y0 < s - 1e-6:
        raise ValueError("via box too small: %s %s" % (via, box))
    nx = max(1, int((x1 - x0 + sp) // (s + sp)))
    ny = max(1, int((y1 - y0 + sp) // (s + sp)))
    ox = x0 + (x1 - x0 - (nx * s + (nx - 1) * sp)) / 2.0
    oy = y0 + (y1 - y0 - (ny * s + (ny - 1) * sp)) / 2.0
    for i in range(nx):
        for j in range(ny):
            bx = ox + i * (s + sp)
            by = oy + j * (s + sp)
            (cell or top).shapes(L[via]).insert(db.DBox(bx, by, bx + s, by + s))


def stack(box, la, lb, net):
    i, j = sorted((STACK.index(la), STACK.index(lb)))
    for k in range(i, j + 1):
        rect(STACK[k], box, net)
    for k in range(i, j):
        via_array(VIA_BETWEEN[(STACK[k], STACK[k + 1])], box)


def seg(layer, p, q, net, w=W):
    (x0, y0), (x1, y1) = p, q
    h = w / 2.0
    if abs(y0 - y1) < 1e-9:
        rect(layer, B(min(x0, x1) - h, y0 - h, max(x0, x1) + h, y0 + h), net)
    elif abs(x0 - x1) < 1e-9:
        rect(layer, B(x0 - h, min(y0, y1) - h, x0 + h, max(y0, y1) + h), net)
    else:
        raise ValueError("non-Manhattan segment %s %s" % (p, q))


def route(net, pts, w=W, lbl=True):
    lays = []
    for p, q in zip(pts[:-1], pts[1:]):
        lay = "M3" if abs(p[0] - q[0]) < 1e-9 else "M4"
        seg(lay, p, q, net, w)
        lays.append(lay)
    for k in range(1, len(pts) - 1):
        if lays[k - 1] != lays[k]:
            v3(*pts[k])
    if lbl and len(pts) > 1:
        (x0, y0), (x1, y1) = pts[0], pts[1]
        label(lays[0], (x0 + x1) / 2.0, (y0 + y1) / 2.0, net)
    return lays


def v3(x, y, net=None):
    via_array("V3", B(x - 0.25, y - 0.25, x + 0.25, y + 0.25))
    if net:
        rect("M3", B(x - 0.25, y - 0.25, x + 0.25, y + 0.25), net)
        rect("M4", B(x - 0.25, y - 0.25, x + 0.25, y + 0.25), net)


# ---------------------------------------------------------------- macros
PLACED = []


def load_macro(name, path):
    src = db.Layout()
    src.read(path)
    tc = src.top_cell()
    new = ly.create_cell(name)
    new.copy_tree(tc)
    return new, src, tc


MAC = {}
for name, path in MACRO_GDS.items():
    h = sha256(path)
    if name in EXPECT_SHA and h != EXPECT_SHA[name]:
        raise SystemExit("%s: GDS hash %s is not the layout of record" % (name, h))
    MAC[name] = load_macro(name, path) + (h, path)


def tr(rot, mirror, x, y):
    return db.DCplxTrans(1.0, rot, mirror, x, y)


def relsrc(path):
    if path.startswith(RES):
        return "<G1_RESULTS_ROOT>/" + os.path.relpath(path, RES)
    return os.path.relpath(path, REPO)


def place(inst_name, macro, trans, orient, s7=None):
    cell, src, tc, sha, path = MAC[macro]
    top.insert(db.DCellInstArray(cell.cell_index(), trans))
    bb = tc.dbbox().transformed(trans)
    PLACED.append({"instance": inst_name, "macro": macro, "orientation": orient,
                   "origin_um": [round(trans.disp.x, 3), round(trans.disp.y, 3)],
                   "bbox_um": [round(bb.left, 3), round(bb.bottom, 3), round(bb.right, 3), round(bb.top, 3)],
                   "source": relsrc(path), "source_sha256": sha, "s7_c4": s7})
    return trans


def pins(macro, name, trans, layer="M3"):
    """All pin rectangles (chip coordinates) of a macro pin: the smallest shape on the pin layer (or the drawing
    layer) of `layer` that contains a label `name` in the macro top cell."""
    cell, src, tc, sha, path = MAC[macro]
    lt = src.find_layer(*LBL[layer])
    pts = [db.Point(s.text.x, s.text.y) for s in tc.shapes(lt).each() if s.is_text() and s.text_string == name]
    if not pts:
        raise KeyError("no label %s on %s in %s" % (name, layer, macro))
    out = []
    for p in pts:
        best = None
        for lay in (PINP.get(layer), LY[layer]):
            li = src.find_layer(*lay) if lay else None
            if li is None:
                continue
            for poly in db.Region(tc.begin_shapes_rec(li)).merged().each():
                if poly.bbox().contains(p):
                    bb = poly.bbox().to_dtype(src.dbu)
                    if best is None or bb.area() < best.area():
                        best = bb
            if best is not None:
                break
        if best is None:
            raise KeyError("no shape under label %s in %s" % (name, macro))
        bt = best.transformed(trans)
        if all(not bt == o for o in out):
            out.append(bt)
    return out


def pin(macro, name, trans, layer="M3", edge=None):
    """One pin rectangle; `edge` picks the one on the given macro edge (N, S, E, W) if a label repeats."""
    ps = pins(macro, name, trans, layer)
    if edge is None or len(ps) == 1:
        return min(ps, key=lambda b: b.area())
    cell, src, tc, sha, path = MAC[macro]
    bb = tc.dbbox().transformed(trans)
    key = {"N": lambda b: abs(b.top - bb.top), "S": lambda b: abs(b.bottom - bb.bottom),
           "E": lambda b: abs(b.right - bb.right), "W": lambda b: abs(b.left - bb.left)}[edge]
    return min(ps, key=lambda b: (round(key(b), 3), b.area()))     # on the edge; smallest shape wins a tie


# ---- placement: S7 C4 positions, pad-adjacent positions re-derived for the 142 um pitch (README "Try e")
X_CTRL, Y_CTRL = 543.8, 673.0
T_CTRL = place("u_ctrl", "r1_ctrl_top", tr(0, False, X_CTRL, Y_CTRL), "R0", [543.8, 673.3])
T_AFE = place("u_afe", "r1_afe", tr(0, False, 336.0, 740.0), "R0", [336.0, 720.0])
T_ISN = place("u_isense", "r1_isense", tr(0, False, 1088.8, 735.0), "R0", [1088.8, 735.0])
T_OSC = place("u_osc", "r1_osc", tr(0, False, 1088.8, 1041.8), "R0", [1088.8, 1041.8])
T_SAFE = place("u_safe", "r1_safe", tr(0, False, 1088.8, 376.0), "R0", [1088.8, 376.0])
T_BGR = place("u_bgr", "r1_bgr", tr(0, False, 336.0, 376.0), "R0", [336.0, 376.0])
T_T2F = place("u_t2f", "r1_t2f", tr(180, True, 536.0, 376.0), "MY", [442.0, 376.0])
T_BIAS = place("u_bias", "r1_bias", tr(0, False, 444.0, 488.6), "R0", [442.0, 488.6])
GY = 1296.0
T_GATE = place("u_gate", "r1_gate_lv", tr(0, False, 440.0, GY), "R0", [440.0, 1300.0])
LS_AFE_X = [405.0, 416.2, 427.4, 438.6]          # centred under AFE c1..c4 (409.6, 420.8, 432.0, 443.2)
for k, x in enumerate(LS_AFE_X):
    place("u_ls_afe%d" % k, "r1_ls", tr(0, False, x, 716.0), "R0", None)
for k, y in enumerate([400.0, 420.0]):
    place("u_ls_t2f%d" % k, "r1_ls", tr(0, False, 545.0, y), "R0", None)

# ---- placeholder: r1_adc (S7 slot 439.0 x 182.3 um). Pin stubs on Metal3 at the edge.
ADC = (592.0, 376.0, 1031.0, 558.3)
CTRL_S = {}                                       # ctrl south pin x (chip) for the ADC north stubs
for nm in (["adc_hold", "is_smp", "adc_start", "adc_sel", "adc_valid_a", "adc_valid_b"] +
           ["adc_raw_a[%d]" % i for i in range(14)] + ["adc_raw_b[%d]" % i for i in range(14)]):
    CTRL_S[nm] = round(pin("r1_ctrl_top", nm, T_CTRL, "M2").center().x, 3)
ADC_N = {}
for nm, x in CTRL_S.items():
    lx = round(x - ADC[0], 3)
    if 2.0 <= lx <= ADC[2] - ADC[0] - 6.0:
        ADC_N[nm] = lx
ADC_N.update({"adc_hold": 2.0, "is_smp": 4.0, "clk": 6.0, "adc_raw_b[12]": 431.0, "adc_raw_b[13]": 433.0,
              "por_n": 437.0})
PH = {
    "r1_adc_ph": {"box": ADC, "mim": True,
                  "pins": {"N": sorted(ADC_N.items(), key=lambda kv: kv[1]),
                           "W": [("ain_sin_p", 110.0), ("ain_sin_n", 114.0), ("ain_cos_p", 130.0),
                                 ("ain_cos_n", 134.0), ("vcm2", 150.0), ("ibias", 165.0)],
                           "E": [("ain_isa_p", 110.0), ("ain_isa_n", 114.0), ("ain_isb_p", 130.0),
                                 ("ain_isb_n", 134.0), ("vcm", 150.0)],
                           "S": [("vdda", 50.0), ("vdd", 100.0), ("vss", 150.0), ("vref_in", 400.0)]}},
}
PH_PINS = {}
for name, d in PH.items():
    x0, y0, x1, y1 = d["box"]
    c = ly.create_cell(name)
    w, h = x1 - x0, y1 - y0
    c.shapes(L["BND"]).insert(B(0, 0, w, h))
    c.shapes(L["TXT"]).insert(db.DText("PLACEHOLDER " + name, db.DTrans(w / 2.0, h / 2.0)))
    PH_PINS[name] = []
    for side, plist in d["pins"].items():
        for pn, pos in plist:
            if side in ("N", "S"):
                py0, py1 = (h - 1.0, h) if side == "N" else (0.0, 1.0)
                pb = B(pos - 0.25, py0, pos + 0.25, py1)
            else:
                px0, px1 = (0.0, 1.0) if side == "W" else (w - 1.0, w)
                pb = B(px0, pos - 0.25, px1, pos + 0.25)
            c.shapes(L["M3"]).insert(pb)
            c.shapes(LP["M3"]).insert(pb)
            c.shapes(LT["M3"]).insert(db.DText(pn, db.DTrans(pb.center().x, pb.center().y)))
            PH_PINS[name].append({"pin": pn, "side": side, "local_um": [round(pb.center().x, 3), round(pb.center().y, 3)],
                                  "box_um": [round(pb.left + x0, 3), round(pb.bottom + y0, 3),
                                             round(pb.right + x0, 3), round(pb.top + y0, 3)]})
    top.insert(db.DCellInstArray(c.cell_index(), db.DCplxTrans(1.0, 0, False, x0, y0)))
    PLACED.append({"instance": "u_" + name, "macro": name, "orientation": "R0", "origin_um": [x0, y0],
                   "bbox_um": [x0, y0, x1, y1], "source": "placeholder (outline + Metal3 pin stubs)",
                   "source_sha256": "-", "s7_c4": [556.0, 376.0]})

# ---------------------------------------------------------------- ring ECO over the AFE (MIM under the west columns)
# West TopMetal1 columns (outer VSS x 324.82-339.82, inner VDD 344.82-361.8) cut for y 735-1239.4 (AFE outline
# 740-1234.4 plus 5 um); TopMetal2 strips of the same width at y 720-1254.4; TopVia2 only in the 15 um overlaps.
AFE_Y0, AFE_Y1 = 740.0, 1234.4
CUT = [321.0, AFE_Y0 - 5.0, 365.0, AFE_Y1 + 5.0]
ECO = {"cut_tm1": CUT, "tm2": [], "tv2": [], "east_columns": "no MIM block under the east columns in C4 (isense "
       "and osc end at x 1247.2 / 1243.2, column from 1340.42); no cut"}
reg_tm1 = db.Region(ring.shapes(L["TM1"]))
new_tm1 = reg_tm1 - db.Region(db.Box.from_dbox(B(*CUT) * (1.0 / ly.dbu)))
ring.shapes(L["TM1"]).clear()
ring.shapes(L["TM1"]).insert(new_tm1)
for (cx0, cx1, net) in [(324.82, 339.82, "VSS"), (344.82, 361.8, "VDD")]:
    rect("TM2", B(cx0, CUT[1] - 15.0, cx1, CUT[3] + 15.0), net)
    ECO["tm2"].append([cx0, CUT[1] - 15.0, cx1, CUT[3] + 15.0])
    for (vy0, vy1) in [(CUT[1] - 15.0, CUT[1]), (CUT[3], CUT[3] + 15.0)]:
        via_array("TV2", B(cx0, vy0, cx1, vy1))
        ECO["tv2"].append([cx0, vy0, cx1, vy1])
    SHAPES.append(("TM1", B(cx0, 321.0, cx1, CUT[1]), net))
    SHAPES.append(("TM1", B(cx0, CUT[3], cx1, 1379.0), net))
SHAPES.append(("TM1", B(1340.42, 321.0, 1355.42, 1379.0), "VDD"))
SHAPES.append(("TM1", B(1360.42, 321.0, 1375.42, 1379.0), "VSS"))

# ---------------------------------------------------------------- supplies
# Ring identity (as try d): outer core ring = VSS, inner = VDD.
CTRL_VDD_X = [23.54, 99.14, 174.74, 250.34, 325.94, 401.54, 477.14]
CTRL_VSS_X = [29.74, 105.34, 180.94, 256.54, 332.14, 407.74, 483.34]
YT = Y_CTRL + 649.0                                 # top of the ctrl TopMetal1 stripes
for lx in CTRL_VDD_X:
    x = X_CTRL + lx
    rect("TM1", B(x, YT, x + 2.2, 1352.3), "VDD")
    via_array("TV2", B(x, 1337.3, x + 2.2, 1352.3))
for lx in CTRL_VSS_X:
    x = X_CTRL + lx
    rect("TM1", B(x, YT, x + 2.2, 1397.0), "VSS")
    via_array("TV2", B(x, 1357.3, x + 2.2, 1372.3))
# North VDD straps: inner TM2 row <-> IO-row vdd Metal3 rail (y 1381-1399), over IO fillers, east of the PWM tracks.
N_VDD_STRAPS = [(840.0, 847.0), (975.0, 982.0), (1120.0, 1127.0), (1250.0, 1257.0)]
for (x0, x1) in N_VDD_STRAPS:
    rect("M3", B(x0, 1338.0, x1, 1397.0), "VDD")
    stack(B(x0, 1338.5, x1, 1345.5), "M3", "TM2", "VDD")
# Antenna load on VDD (try d fix F2): 34 x sg13g2_decap_8 under the strap x 1250-1257, VSS strap Metal4 x 1300-1306.
DECAP = ly.cell("sg13g2_decap_8")
DECAP_SRC = "from r1_ctrl_top (PDK library cell)"
if DECAP is None:
    raise SystemExit("sg13g2_decap_8 not found in r1_ctrl_top")
N_DECAP, DX0, DY0, DPITCH = 34, 1215.0, 1355.0, 3.36
top.insert(db.DCellInstArray(DECAP.cell_index(), db.DTrans(DX0, DY0), db.DVector(DPITCH, 0), db.DVector(0, 0), N_DECAP, 1))
DEC_X1 = DX0 + N_DECAP * DPITCH
SHAPES.append(("M1", B(DX0, DY0 + 3.56, DEC_X1, DY0 + 4.0), "VDD"))
SHAPES.append(("M1", B(DX0, DY0 - 0.22, DEC_X1, DY0 + 0.22), "VSS"))
_vb = B(1250.2, DY0 + 3.56, 1256.8, DY0 + 4.0)
rect("M2", _vb, "VDD")
via_array("V1", _vb)
via_array("V2", _vb)
_sb = B(1300.0, DY0 - 0.22, 1306.0, DY0 + 0.22)
stack(_sb, "M2", "M4", "VSS")
via_array("V1", _sb)
rect("M4", B(1300.0, DY0 - 0.22, 1306.0, 1390.0), "VSS")
DECAP_ROW = {"cell": "sg13g2_decap_8", "count": N_DECAP, "origin_um": [DX0, DY0], "pitch_um": DPITCH,
             "bbox_um": [DX0, DY0, round(DEC_X1, 3), DY0 + 3.78], "gate_area_on_VDD_um2": round(N_DECAP * 0.84, 2),
             "cell_source": DECAP_SRC}
# South trunks (Metal4) under the south ring band; VDDA reaches west to the west VDDA riser.
TR = {"VSS": (332.0, 340.0), "VDD": (343.0, 349.0), "VDDA": (352.0, 360.0)}
rect("M4", B(371.0, 332.0, 1378.0, 340.0), "VSS")
rect("M4", B(371.0, 343.0, 1360.0, 349.0), "VDD")
rect("M4", B(326.0, 352.0, 1372.0, 360.0), "VDDA")
label("M4", 380.0, 336.0, "VSS")
label("M4", 380.0, 346.0, "VDD")
label("M4", 380.0, 356.0, "VDDA")
S_FILLERS = [535.0, 677.0, 819.0, 961.0, 1103.0]      # south IO filler gaps (62 um) of the 142 um pitch
for f0 in S_FILLERS:
    rect("M4", B(f0 + 9.0, 304.0, f0 + 39.0, 340.0), "VSS")           # IO vss Metal4 rail 303.2-319
    rect("M3", B(f0 + 2.0, 302.0, f0 + 8.0, 349.0), "VDD")            # IO vdd Metal3 rail 301-319
    via_array("V3", B(f0 + 2.0, 343.0, f0 + 8.0, 349.0))
# VDDA feed from pad 7 (sg13g2_IOPadAnalog `pad`, Metal3 x 1379-1379.29, y 481.105-505.875)
rect("M3", B(1366.0, 482.0, 1379.29, 505.0), "VDDA")
rect("M4", B(1366.0, 352.0, 1372.0, 505.0), "VDDA")
via_array("V3", B(1366.0, 482.0, 1372.0, 505.0))
label("M3", 1375.0, 493.0, "VDDA")
# West VDDA riser (Metal3 x 327-329, under the outer west column): bgr, bias, AFE
rect("M3", B(327.0, 352.0, 329.0, 738.0), "VDDA")
via_array("V3", B(327.0, 352.0, 329.0, 360.0))


def ctrl_pin(name):
    return pin("r1_ctrl_top", name, T_CTRL, "M2" if name in ("gate_a", "gate_b", "gate_c", "cs_n", "ma_sclk",
                                                                "slo_sdo", "por_n", "t2f_clk") or name in CTRL_S
               else "M3")


P = {}
P["bgr"] = {n: pin("r1_bgr", n, T_BGR) for n in ("vref", "pbias", "pcasc", "vdd", "vss")}
P["t2f"] = {n: pin("r1_t2f", n, T_T2F, edge="W" if n != "vdd" and n != "vss" else None)   # MY: pins face west
            for n in ("vref", "pbias", "pcasc", "vdd12", "fout", "en", "mode", "vdd", "vss")}
P["bias"] = {n: pin("r1_bias", n, T_BIAS) for n in ("vdda", "vdd", "vss", "pbias", "pcasc", "ib_afe_s1", "ib_afe_s2",
                                                     "ib_afe_c1", "ib_afe_c2", "ib_is_a", "ib_is_b", "ib_sf_oa",
                                                     "ib_sf_na", "ib_sf_ob", "ib_sf_nb", "ib_adc_ref", "por_n")}
P["afe"] = {n: pin("r1_afe", n, T_AFE) for n in ("sinp", "sinn", "cosp", "cosn", "ib_s1", "ib_s2", "ib_c1", "ib_c2")}
P["afe_vss"] = sorted(pins("r1_afe", "vss", T_AFE), key=lambda b: b.left)
P["afe_vdd"] = sorted(pins("r1_afe", "vdd", T_AFE), key=lambda b: b.left)
P["isn"] = {n: pin("r1_isense", n, T_ISN, edge=e) for n, e in
            [("isa_p", "E"), ("isa_n", "E"), ("isb_p", "E"), ("isb_n", "E"), ("vref", "S"), ("ibias_a", "S"),
             ("ibias_b", "N"), ("vss", "S"), ("vdda", "S"), ("vdd", "S")]}
P["osc"] = {n: pin("r1_osc", n, T_OSC) for n in ("en", "trim0", "trim1", "trim2", "trim3", "trim4", "osc_clk", "vdd", "vss")}
P["safe"] = {n: pin("r1_safe", n, T_SAFE, edge=e) for n, e in
             [("vref", "W"), ("oc_a", "S"), ("neg_a", "S"), ("oc_b", "S"), ("neg_b", "S"), ("ibias_oa", "S"),
              ("ibias_na", "S"), ("ibias_ob", "S"), ("ibias_nb", "S"), ("vss", "W"), ("vdd", "W"), ("vdda", "E")]}

# ---- macro supply hookups
# bgr: vss bar (y 376-378) <- VSS trunk; vdd bar (568.3-570.3) <- VDDA (west riser, Metal4 y 572-574)
rect("M3", B(380.0, 333.0, 386.0, 377.0), "VSS")
via_array("V3", B(380.0, 333.0, 386.0, 340.0))
rect("M4", B(327.0, 572.0, 441.75, 574.0), "VDDA")
via_array("V3", B(327.0, 572.0, 329.0, 574.0))
rect("M3", B(380.0, 569.0, 386.0, 574.0), "VDDA")
via_array("V3", B(380.0, 572.0, 386.0, 574.0))
# bias: vdda bar (top, y 650.94-652.94) <- riser x 441.5; vss bar (488.6-490.6) <- riser x 562.5-563.5 from the
# VSS trunk; vdd (east pin) <- riser x 566 from the VDD trunk.
rect("M3", B(441.25, 572.0, 441.75, 652.94), "VDDA")
via_array("V3", B(441.25, 572.0, 441.75, 574.0))
bv = P["bias"]["vdda"]
rect("M3", B(441.25, bv.bottom, 444.5, bv.top), "VDDA")
rect("M3", B(562.5, 333.0, 563.5, P["bias"]["vss"].bottom + 1.0), "VSS")
via_array("V3", B(562.5, 333.0, 563.5, 340.0))
pv = P["bias"]["vdd"]
rect("M3", B(565.75, 343.0, 566.25, pv.top), "VDD")
via_array("V3", B(565.75, 343.0, 566.25, 349.0))
rect("M3", B(pv.left, pv.bottom, 566.25, pv.top), "VDD")
# t2f (MY): vss bar (376-378.6) <- VSS trunk riser x 470-476; vdd bar (476-478.6) <- VDDA riser x 537-541
rect("M3", B(470.0, 333.0, 476.0, 377.0), "VSS")
via_array("V3", B(470.0, 333.0, 476.0, 340.0))
rect("M3", B(537.0, 352.0, 541.0, 478.6), "VDDA")
rect("M3", B(535.0, 476.5, 541.0, 478.6), "VDDA")
via_array("V3", B(537.0, 352.0, 541.0, 360.0))
# t2f vdd12 <- VDD trunk (Metal3 x 433.5, Metal4 into the pin)
pt = P["t2f"]["vdd12"]
yc = pt.center().y
rect("M3", B(433.25, 343.0, 433.75, yc + 0.25), "VDD")
via_array("V3", B(433.25, 343.0, 433.75, 349.0))
v3(433.5, yc)
rect("M4", B(433.25, yc - 0.25, pt.center().x + 0.25, yc + 0.25), "VDD")
v3(pt.center().x, yc)
# safe: vdda east pin -> VDDA feed (Metal4 y 379.6-382); vss and vdd west pins -> trunks (Metal3 x 1086.5 / 1085.5)
ps = P["safe"]["vdda"]
yc = ps.center().y
rect("M3", B(ps.left, ps.bottom, 1341.0, ps.top), "VDDA")
rect("M3", B(1338.8, yc - 1.0, 1341.0, yc + 1.2), "VDDA")
via_array("V3", B(1338.8, yc - 1.0, 1341.0, yc + 1.2))
rect("M4", B(1338.8, yc - 1.0, 1372.0, yc + 1.2), "VDDA")
ps = P["safe"]["vss"]
rect("M3", B(1086.25, ps.bottom, ps.right, ps.top), "VSS")
rect("M3", B(1086.25, 333.0, 1086.75, ps.top), "VSS")
via_array("V3", B(1086.25, 333.0, 1086.75, 340.0))
ps = P["safe"]["vdd"]
rect("M3", B(1085.25, ps.bottom, ps.right, ps.top), "VDD")
rect("M3", B(1085.25, 343.0, 1085.75, ps.top), "VDD")
via_array("V3", B(1085.25, 343.0, 1085.75, 349.0))
# AFE: vss pins <- outer west column (stack Metal4-TopMetal1 at y 729.5-733.5, Metal4 y 731-733);
#      vdd (VDDA) pins <- west VDDA riser (Metal4 y 736-738)
stack(B(325.5, 729.5, 339.5, 733.5), "M4", "TM1", "VSS")
rect("M4", B(325.5, 731.0, P["afe_vss"][-1].right + 0.5, 733.0), "VSS")
for pb in P["afe_vss"]:
    rect("M3", B(pb.left, 731.0, pb.right, pb.top), "VSS")
    via_array("V3", B(pb.center().x - 0.25, 731.0, pb.center().x + 0.25, 733.0))
    rect("M3", B(pb.center().x - 0.25, 731.0, pb.center().x + 0.25, 733.0), "VSS")
rect("M4", B(327.0, 736.0, P["afe_vdd"][-1].right + 0.5, 738.0), "VDDA")
via_array("V3", B(327.0, 736.0, 329.0, 738.0))
for pb in P["afe_vdd"]:
    rect("M3", B(pb.left, 736.0, pb.right, pb.top), "VDDA")
    rect("M3", B(pb.center().x - 0.25, 736.0, pb.center().x + 0.25, 738.0), "VDDA")
    via_array("V3", B(pb.center().x - 0.25, 736.0, pb.center().x + 0.25, 738.0))
# isense: vss <- outer east column (Metal4 y 721-724), vdd <- inner east column (726-729.5),
#         vdda <- VDDA riser x 1366-1370 from the pad-7 feed (Metal4 y 717-719)
pb = P["isn"]["vss"]
stack(B(1361.0, 721.0, 1374.5, 724.0), "M4", "TM1", "VSS")
rect("M4", B(pb.left, 721.0, 1374.5, 724.0), "VSS")
rect("M3", B(pb.left, 721.0, pb.right, pb.top), "VSS")
via_array("V3", B(pb.left, 721.0, pb.right, 724.0))
pb = P["isn"]["vdd"]
stack(B(1341.0, 726.0, 1354.5, 729.5), "M4", "TM1", "VDD")
rect("M4", B(pb.left, 726.0, 1354.5, 729.5), "VDD")
rect("M3", B(pb.left, 726.0, pb.right, pb.top), "VDD")
via_array("V3", B(pb.left, 726.0, pb.right, 729.5))
pb = P["isn"]["vdda"]
rect("M3", B(1366.0, 505.0, 1370.0, 719.0), "VDDA")
via_array("V3", B(1366.0, 717.0, 1370.0, 719.0))
rect("M4", B(pb.left, 717.0, 1370.0, 719.0), "VDDA")
rect("M3", B(pb.left, 717.0, pb.right, pb.top), "VDDA")
via_array("V3", B(pb.left, 717.0, pb.right, 719.0))
# osc: vss bar -> outer east column (Metal4 at the bar height); vdd bar -> inner east column
for nm, cx0, cx1, net in [("vss", 1361.0, 1374.5, "VSS"), ("vdd", 1341.0, 1354.5, "VDD")]:
    pb = P["osc"][nm]
    rect("M3", B(pb.right - 0.5, pb.bottom, 1246.5, pb.top), net)
    via_array("V3", B(1244.5, pb.bottom, 1246.5, pb.top))
    rect("M4", B(1244.5, pb.bottom, cx1, pb.top), net)
    stack(B(cx0, pb.bottom, cx1, pb.top), "M4", "TM1", net)
# osc en held high through a sg13g2_tiehi (register map ANA_CTRL: oscillator always enabled). Run asm-20261021-e
# tied en straight to VDD: antenna Ant.e_TopMetal1/TopMetal2 on the four en gates (the VDD net carries the ring).
# The tie cell (library cell already in r1_ctrl_top, see try-d F3) sits mirrored (MX) in the 10 um gap between
# r1_isense (top y 1031.8) and r1_osc (bottom y 1041.8): VSS rail on top -> riser into the osc vss bar; VDD rail at
# the bottom -> Metal1 west to the VDD riser x 1086.25-1086.75; L_HI -> OSC_EN on track x 1084 -> osc en pin.
TIE = ly.cell("sg13g2_tiehi")
if TIE is None:
    raise SystemExit("sg13g2_tiehi not found in r1_ctrl_top")
TX, TY = 1095.0, 1040.0
TT = db.DTrans(db.DTrans.M0, db.DVector(TX, TY))
top.insert(db.DCellInstArray(TIE.cell_index(), TT))
def tb(x0, y0, x1, y1):
    return db.DBox(x0, y0, x1, y1).transformed(TT)
t_vss, t_vdd, t_lhi = tb(0, -0.22, 1.92, 0.22), tb(0, 3.56, 1.92, 4.0), tb(1.3, 2.165, 1.585, 2.91)
SHAPES.append(("M1", t_vss, "VSS"))
SHAPES.append(("M1", t_vdd, "VDD"))
SHAPES.append(("M1", t_lhi, "OSC_EN"))
pv = P["osc"]["vss"]
_b = B(TX + 0.2, t_vss.bottom, TX + 1.7, t_vss.top)
stack(_b, "M1", "M3", "VSS")
rect("M3", B(TX + 0.2, t_vss.bottom, TX + 1.7, pv.bottom + 0.7), "VSS")
_b = B(1086.25, t_vdd.bottom, 1086.75, t_vdd.top)
rect("M1", B(1086.25, t_vdd.bottom, TX + 0.2, t_vdd.top), "VDD")
stack(_b, "M1", "M3", "VDD")
rect("M3", B(1086.25, t_vdd.bottom, 1086.75, P["osc"]["vdd"].top), "VDD")
rect("M3", B(1086.25, P["osc"]["vdd"].bottom, P["osc"]["vdd"].left + 1.0, P["osc"]["vdd"].top), "VDD")
ylh = round((t_lhi.bottom + t_lhi.top) / 2.0, 2)                # 1037.46 (on the 5 nm grid; run e3: 1037.4625, off grid)
rect("M1", B(TX + 1.3, ylh - 0.25, TX + 2.4, ylh + 0.25), "OSC_EN")
stack(B(TX + 1.6, ylh - 0.25, TX + 2.4, ylh + 0.25), "M1", "M3", "OSC_EN")
v3(TX + 2.0, ylh, "OSC_EN")
TIE_CELL = {"instance": "u_tie_osc", "cell": "sg13g2_tiehi", "orientation": "MX", "origin_um": [TX, TY],
            "bbox_um": [round(v, 3) for v in (lambda b: (b.left, b.bottom, b.right, b.top))(TIE.dbbox().transformed(TT))],
            "cell_source": "from r1_ctrl_top (PDK library cell)"}
# gate_lv: vdd and gate_en from the inner west column (VDD), vss from the outer column (as try d, y + 100)
rect("M3", B(437.6, GY + 14.08, 440.4, GY + 14.58), "VDD")
rect("M3", B(437.6, GY + 16.45, 440.4, GY + 16.95), "VDD")
rect("M2", B(437.75, GY + 14.0, 438.15, GY + 17.05), "VDD")
via_array("V2", B(437.75, GY + 14.08, 438.15, GY + 14.58 + 0.06))
via_array("V2", B(437.75, GY + 16.45 - 0.06, 438.15, GY + 16.95))
rect("M4", B(346.0, GY + 14.08, 439.0, GY + 14.58), "VDD")
via_array("V3", B(438.0, GY + 14.08, 439.0, GY + 14.58))
stack(B(346.0, GY + 12.5, 360.0, GY + 16.0), "M4", "TM1", "VDD")
rect("M3", B(436.0, GY + 1.5, 440.4, GY + 4.5), "VSS")
rect("M4", B(326.0, GY + 1.5, 439.5, GY + 4.5), "VSS")
via_array("V3", B(436.0, GY + 1.5, 439.5, GY + 4.5))
stack(B(326.0, GY + 0.5, 338.0, GY + 5.5), "M4", "TM1", "VSS")

# ---------------------------------------------------------------- signals
NETS = {}


def note(net, src, dst, layers, state="routed"):
    NETS[net] = {"source": src, "destinations": dst, "metal": layers, "state": state}


def east_land(net, name, track_x):
    """ctrl east pin (Metal3 at x 1063.4-1063.8) -> via pad at x 1064.8 -> Metal4 to track_x."""
    pb = ctrl_pin(name)
    yc = pb.center().y
    rect("M3", B(pb.left, yc - 0.2, 1065.05, yc + 0.2), net)
    v3(1064.8, yc, net)
    rect("M4", B(1064.55, yc - 0.25, track_x + 0.25, yc + 0.25), net)
    return yc


def north_up(net, name):
    """ctrl north pin (Metal2) -> Via2 just above the macro edge -> Metal3 stub (route continues upward)."""
    pb = ctrl_pin(name)
    xc = pb.center().x
    yt = Y_CTRL + 664.0
    rect("M2", B(pb.left, pb.bottom, pb.right, yt + 1.2), net)
    rect("M3", B(xc - 0.25, yt + 0.4, xc + 0.25, yt + 1.2), net)
    via_array("V2", B(pb.left, yt + 0.4, pb.right, yt + 1.2))
    return xc, yt + 0.8


def south_down(net, name, y_from):
    """ctrl south pin (Metal2 at y 673) <- Metal3 from y_from up to the pin, Via2 just below the macro edge."""
    pb = ctrl_pin(name)
    xc = pb.center().x
    rect("M2", B(pb.left, Y_CTRL - 1.6, pb.right, pb.top), net)
    rect("M3", B(xc - 0.25, y_from - 0.25, xc + 0.25, Y_CTRL - 0.9), net)
    via_array("V2", B(pb.left, Y_CTRL - 1.6, pb.right, Y_CTRL - 0.9))
    return xc


def pad_west(net, y):
    """West IO core pin (Metal3 at x 320.71-321): Metal3 neck to x 323.5, Via3 at x 323.25."""
    rect("M3", B(320.71, y - 0.25, 323.5, y + 0.25), net)
    v3(323.25, y)


def pad_east(net, y):
    """East IO core pin (Metal3 at x 1379-1379.29): Metal3 neck from x 1376.5, Via3 at x 1376.75."""
    rect("M3", B(1376.5, y - 0.25, 1379.29, y + 0.25), net)
    v3(1376.75, y)


def land(net, pb, xv, side):
    """Metal4 arrives at xv (Via3 there), Metal3 neck of the pin height into a pin on the W or E macro edge."""
    yc = pb.center().y
    v3(xv, yc, net)
    h = min(0.25, pb.height() / 2.0)
    if side == "W":          # pin on a west edge, via west of it
        rect("M3", B(xv - 0.25, yc - h, pb.right, yc + h), net)
    else:
        rect("M3", B(pb.left, yc - h, xv + 0.25, yc + h), net)


def land_v(net, pb, y_via, xc=None):
    """Via3 at (pin x, y_via) and a Metal3 riser of the pin width into a pin on an N or S macro edge."""
    xc = pb.center().x if xc is None else xc
    v3(xc, y_via, net)
    hw = min(0.25, pb.width() / 2.0)
    rect("M3", B(xc - hw, min(y_via, pb.bottom), xc + hw, max(y_via, pb.top)), net)


# --- encoder inputs: west analog pads 21-24 (`pad` terminal) -> AFE west pins (AFE README: `pad`, not `padres`)
for net, pname in [("SIN_P", "sinp"), ("COS_P", "cosp")]:        # pin y inside the pad window: straight Metal3
    pb = P["afe"][pname]
    rect("M3", B(320.71, pb.bottom, pb.right, pb.top), net)
    label("M3", 328.0, pb.center().y, net)
    note(net, "pad %s (`pad`)" % net, ["u_afe/%s" % pname], "M3 (straight, 15 um)")
for net, pname, ypad in [("SIN_N", "sinn", 919.49), ("COS_N", "cosn", 1203.49)]:
    pb = P["afe"][pname]
    pad_west(net, ypad)
    route(net, [(323.25, ypad), (330.5, ypad), (330.5, pb.center().y), (335.25, pb.center().y)])
    land(net, pb, 335.25, "W")
    note(net, "pad %s (`pad`)" % net, ["u_afe/%s" % pname], "M3, M4")
# --- current-sense inputs: east analog pads 8-11 (`pad`) -> isense east pins
for net, pname in [("ISA_N", "isa_n"), ("ISB_P", "isb_p")]:
    pb = P["isn"][pname]
    yc = pb.center().y
    rect("M3", B(pb.left, yc - 0.25, 1379.29, yc + 0.25), net)
    label("M3", 1300.0, yc, net)
    note(net, "pad %s (`pad`)" % net, ["u_isense/%s" % pname], "M3 (straight)")
for net, pname, ypad, xv in [("ISA_P", "isa_p", 635.49, 1345.0), ("ISB_N", "isb_n", 1061.49, 1300.0)]:
    pb = P["isn"][pname]
    pad_east(net, ypad)
    route(net, [(1376.75, ypad), (xv, ypad), (xv, pb.center().y), (1248.0, pb.center().y)])
    land(net, pb, 1248.0, "E")
    note(net, "pad %s (`pad`)" % net, ["u_isense/%s" % pname], "M3, M4")
# --- VREF_BG: bgr vref (west pin) -> strip y 361 -> t2f vref, safe vref, isense vref
pb = P["bgr"]["vref"]
rect("M3", B(332.75, pb.bottom, pb.right, pb.top), "VREF_BG")
rect("M3", B(332.75, 360.75, 333.25, pb.top), "VREF_BG")
label("M3", 333.0, 400.0, "VREF_BG")
route("VREF_BG", [(333.0, 361.0), (1083.0, 361.0), (1083.0, 728.0), (1091.2, 728.0)], lbl=False)
v3(333.0, 361.0)
land_v("VREF_BG", P["isn"]["vref"], 728.0)
pt = P["t2f"]["vref"]
v3(441.5, 361.0)
route("VREF_BG", [(441.5, 361.0), (441.5, pt.center().y), (pt.center().x, pt.center().y)], lbl=False)
v3(pt.center().x, pt.center().y)
ps = P["safe"]["vref"]
v3(1083.0, ps.center().y)
rect("M4", B(1082.75, ps.center().y - 0.25, 1088.3, ps.center().y + 0.25), "VREF_BG")
land("VREF_BG", ps, 1088.05, "W")
note("VREF_BG", "u_bgr/vref", ["u_t2f/vref", "u_safe/vref", "u_isense/vref", "r1_adc_ph/vref_in (pending)"],
     "M3, M4 (strip y 361, unshielded)", "routed to t2f, safe and isense; adc pending")
# --- PBIAS, PCASC: bgr east pins -> t2f (east pins after MY) and bias west pins (tracks x 435.5 / 437.5)
for net, pname, xt in [("PBIAS", "pbias", 435.5), ("PCASC", "pcasc", 437.5)]:
    pg = P["bgr"][pname]
    yg = pg.center().y
    rect("M3", B(pg.left, pg.bottom, 432.75, pg.top), net)
    v3(432.5, yg, net)
    pt = P["t2f"][pname]
    pbb = P["bias"][pname]
    route(net, [(432.5, yg), (xt, yg), (xt, pt.center().y), (pt.center().x, pt.center().y)])
    v3(pt.center().x, pt.center().y)
    route(net, [(xt, yg), (xt, pbb.center().y), (442.5, pbb.center().y)], lbl=False)
    land(net, pbb, 442.5, "W")
    note(net, "u_bgr/%s" % pname, ["u_t2f/%s" % pname, "u_bias/%s" % pname], "M3, M4")
# --- T2F_FOUT: t2f fout -> ctrl t2f_clk (south pin)
pt = P["t2f"]["fout"]
v3(pt.center().x, pt.center().y)
xc = ctrl_pin("t2f_clk").center().x
route("T2F_FOUT", [(pt.center().x, pt.center().y), (439.5, pt.center().y), (439.5, 662.0), (xc, 662.0), (xc, Y_CTRL - 1.25)])
south_down("T2F_FOUT", "t2f_clk", 662.0)
note("T2F_FOUT", "u_t2f/fout", ["u_ctrl/t2f_clk"], "M2 stub, M3, M4")
# --- SDI and EN: west pads 19/20 p2c -> ctrl west pins
for net, ypad, name, xr, yh in [("SDI_P2C", 494.975, "sdi", 330.75, 663.5), ("EN_STO_IN_P2C", 636.975, "en_pad", 332.5, 665.0)]:
    pb = ctrl_pin(name)
    yc = pb.center().y
    xv = 536.0 if name == "sdi" else 538.0
    pad_west(net, ypad)
    route(net, [(323.25, ypad), (xr, ypad), (xr, yh), (xv, yh), (xv, yc), (543.05, yc)])
    v3(543.05, yc, net)
    rect("M3", B(542.8, pb.bottom, pb.right, pb.top), net)
    note(net, "pad %s p2c" % net[:-4], ["u_ctrl/%s" % name], "M3, M4")
# --- POR_N: bias por_n (east pin) -> ctrl por_n (north pin): strip x 541 between AFE and ctrl, north band y 1348
pb = P["bias"]["por_n"]
yc = pb.center().y
rect("M3", B(pb.left, pb.bottom, 564.75, pb.top), "POR_N")
v3(564.5, yc, "POR_N")
xn, yn = north_up("POR_N", "por_n")
route("POR_N", [(564.5, yc), (567.5, yc), (567.5, 666.5), (541.0, 666.5), (541.0, 1348.0), (xn, 1348.0), (xn, yn)])
note("POR_N", "u_bias/por_n", ["u_ctrl/por_n"], "M2 stub, M3, M4")
# --- bias outputs to the consumers that exist (AFE x4, isense x2, safe x4); ib_adc_ref pending (ADC placeholder)
BT = P["bias"]
y_top = BT["ib_afe_s1"].top
for net, pname, ytr, dst in [("IB_AFE_S1", "ib_afe_s1", 668.0, "ib_s1"), ("IB_AFE_C1", "ib_afe_c1", 669.5, "ib_c1"),
                             ("IB_AFE_S2", "ib_afe_s2", 671.0, "ib_s2"), ("IB_AFE_C2", "ib_afe_c2", 672.5, "ib_c2")]:
    xb = BT[pname].center().x
    pa = P["afe"][dst]
    route(net, [(xb, y_top - 0.25), (xb, ytr), (pa.center().x, ytr), (pa.center().x, pa.bottom - 1.0)])
    rect("M3", B(pa.left, pa.bottom - 1.25, pa.right, pa.top), net)      # 0.4 um neck into the 0.4 um pin
    note(net, "u_bias/%s" % pname, ["u_afe/%s" % dst], "M3, M4")
EAST = [("IB_IS_A", "ib_is_a", 655.5, 1084.5), ("IB_SF_OA", "ib_sf_oa", 656.5, 1038.0), ("IB_SF_NA", "ib_sf_na", 657.5, 1040.0),
        ("IB_SF_OB", "ib_sf_ob", 658.5, 1042.0), ("IB_SF_NB", "ib_sf_nb", 659.5, 1044.0), ("IB_IS_B", "ib_is_b", 660.5, 1086.0)]
STRIP = {"IB_SF_OA": (362.2, "ibias_oa"), "IB_SF_NA": (363.4, "ibias_na"), "IB_SF_OB": (364.6, "ibias_ob"),
         "IB_SF_NB": (365.8, "ibias_nb")}
for net, pname, ytr, xv in EAST:
    xb = BT[pname].center().x
    if net in STRIP:
        ys, dst = STRIP[net]
        ps = P["safe"][dst]
        route(net, [(xb, y_top - 0.25), (xb, ytr), (xv, ytr), (xv, ys), (ps.center().x, ys)])
        land_v(net, ps, ys)
        note(net, "u_bias/%s" % pname, ["u_safe/%s" % dst], "M3, M4 (strip y %.1f)" % ys)
    elif net == "IB_IS_A":
        pi = P["isn"]["ibias_a"]
        route(net, [(xb, y_top - 0.25), (xb, ytr), (xv, ytr), (xv, 731.0), (pi.center().x, 731.0)])
        land_v(net, pi, 731.0)
        note(net, "u_bias/%s" % pname, ["u_isense/ibias_a"], "M3, M4")
    else:
        pi = P["isn"]["ibias_b"]
        route(net, [(xb, y_top - 0.25), (xb, ytr), (xv, ytr), (xv, 1034.5), (pi.center().x, 1034.5)])
        land_v(net, pi, 1034.5)
        note(net, "u_bias/%s" % pname, ["u_isense/ibias_b"], "M3, M4")
# --- safe flags -> ctrl cmp[3:0] (strip y 367.0-370.6, chan_e tracks x 1077-1081.5)
for k, (flag, ys, xtr) in enumerate([("oc_a", 367.0, 1077.0), ("neg_a", 368.2, 1078.5), ("oc_b", 369.4, 1080.0),
                                     ("neg_b", 370.6, 1081.5)]):
    net = "CMP_%s" % flag.upper()
    ps = P["safe"][flag]
    yc = east_land(net, "cmp[%d]" % k, xtr)
    route(net, [(ps.center().x, ys), (xtr, ys), (xtr, yc)])
    v3(xtr, yc)
    land_v(net, ps, ys)
    note(net, "u_safe/%s" % flag, ["u_ctrl/cmp[%d]" % k], "M3, M4")
# --- FAULT_N: ctrl east pin -> track 1066.5 -> y 1205 -> east -> pad 12 c2p (Metal3 x 1379, y 1203.1-1206.9)
yc = east_land("FAULT_N_C2P", "fault_n", 1066.5)
v3(1066.5, yc)
route("FAULT_N_C2P", [(1066.5, yc), (1066.5, 1205.0), (1376.75, 1205.0)])
pad_east("FAULT_N_C2P", 1205.0)
note("FAULT_N_C2P", "u_ctrl/fault_n", ["pad 12 FAULT_N c2p"], "M3, M4")
# --- OSC_CLK: osc osc_clk (west edge, revision 2) -> track 1068 -> ctrl clk (straight, no detour)
po = P["osc"]["osc_clk"]
yc = east_land("OSC_CLK", "clk", 1068.0)
v3(1068.0, yc)
route("OSC_CLK", [(1068.0, yc), (1068.0, po.center().y), (1088.05, po.center().y)])
land("OSC_CLK", po, 1088.05, "W")
note("OSC_CLK", "u_osc/osc_clk", ["u_ctrl/clk"], "M3, M4 (osc west edge)")
# --- OSC_TRIM[4:0]: ctrl osc_trim -> tracks 1069.5-1075.5 -> osc west pins (0.8 um pitch)
for k in range(5):
    net = "OSC_TRIM_%d" % k
    xtr = 1069.5 + 1.5 * k
    pt = P["osc"]["trim%d" % k]
    yc = east_land(net, "osc_trim[%d]" % k, xtr)
    v3(xtr, yc)
    route(net, [(xtr, yc), (xtr, pt.center().y), (1088.05, pt.center().y)])
    land(net, pt, 1088.05, "W")
    note(net, "u_ctrl/osc_trim[%d]" % k, ["u_osc/trim%d" % k], "M3, M4")
# --- OSC_EN: tie cell L_HI (gap between isense and osc) -> track x 1084 -> osc en (west edge)
pe = P["osc"]["en"]
route("OSC_EN", [(TX + 2.0, ylh), (1084.0, ylh), (1084.0, pe.center().y), (1088.05, pe.center().y)])
land("OSC_EN", pe, 1088.05, "W")
note("OSC_EN", "u_tie_osc/L_HI (sg13g2_tiehi)", ["u_osc/en"], "M1 pad, M3, M4")
# --- north: ctrl <-> pads 16-18; ctrl gate_a/b/c -> gate_lv; gate_lv -> pads 13-15 (as try d, ring band y + 100)
for net, name, xpad, ylev in [("CS_N_P2C", "cs_n", 920.975, 1368.0), ("MA_SCLK_P2C", "ma_sclk", 1062.975, 1370.5),
                              ("SLO_SDO_C2P", "slo_sdo", 1205.0, 1373.0)]:
    xc, yb = north_up(net, name)
    route(net, [(xc, yb), (xc, ylev), (xpad, ylev), (xpad, 1379.04)])
    note(net, ("pad %s p2c" % net[:-4]) if net.endswith("P2C") else "u_ctrl/slo_sdo",
         ["u_ctrl/%s" % name] if net.endswith("P2C") else ["pad 18 SLO_SDO c2p"], "M2 stub, M3, M4")
for net, name, tx, py, ylev in [("PWM_A", "gate_a", 432.0, GY + 15.9, 1340.5), ("PWM_B", "gate_b", 434.0, GY + 17.5, 1343.0),
                                ("PWM_C", "gate_c", 436.0, GY + 18.3, 1345.5)]:
    xc, yb = north_up(net, name)
    route(net, [(xc, yb), (xc, ylev), (tx, ylev), (tx, py)])
    rect("M3", B(tx - 0.25, py - 0.25, 441.0, py + 0.25), net)
    note(net, "u_ctrl/%s" % name, ["u_gate/pwm_%s" % net[-1].lower()], "M2 stub, M3, M4")
for net, pnm, py, tx, ylev, xpad in [("GATE_A_C2P", "gc_a", GY + 15.9, 474.0, 1356.0, 494.99),
                                    ("GATE_C_C2P", "gc_c", GY + 16.7, 472.0, 1361.0, 778.99),
                                    ("GATE_B_C2P", "gc_b", GY + 17.5, 470.0, 1358.5, 636.99)]:
    rect("M3", B(467.4, py - 0.25, tx + 0.25, py + 0.25), net)
    route(net, [(tx, py), (tx, ylev), (xpad, ylev), (xpad, 1379.04)])
    note(net, "u_gate/%s" % pnm, ["pad %s c2p (sg13g2_IOPadOut30mA; its own 1.2->3.3 V shifter)" % net[:6]], "M3, M4")


# ---------------------------------------------------------------- checks
def self_check():
    by_layer = {}
    for lay, box, net in SHAPES:
        by_layer.setdefault(lay, {}).setdefault(net, db.Region())
        by_layer[lay][net].insert(db.Box.from_dbox(box * (1.0 / ly.dbu)))
    space = {"M1": 0.18, "M2": 0.21, "M3": 0.21, "M4": 0.21, "M5": 0.21, "TM1": 1.64, "TM2": 2.0}
    issues = []
    for lay, nets in by_layer.items():
        keys = sorted(nets)
        grown = {k: nets[k].merged().sized(int(space[lay] / 2.0 / ly.dbu)) for k in keys}
        for i in range(len(keys)):
            for j in range(i + 1, len(keys)):
                ov = grown[keys[i]] & grown[keys[j]]
                if not ov.is_empty():
                    issues.append([lay, keys[i], keys[j], str(ov.bbox().to_dtype(ly.dbu))])
    return issues


def overlap_check(halo=0.0):
    rows = [r for r in PLACED if not r["instance"].startswith("u_ls")]
    bad = []
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            a, b = rows[i]["bbox_um"], rows[j]["bbox_um"]
            if a[0] - halo < b[2] and b[0] - halo < a[2] and a[1] - halo < b[3] and b[1] - halo < a[3]:
                bad.append([rows[i]["instance"], rows[j]["instance"]])
    outside = [r["instance"] for r in PLACED if r["bbox_um"][0] < 331 or r["bbox_um"][1] < 331 or
               r["bbox_um"][2] > DIE - 331 or r["bbox_um"][3] > DIE - 331]
    return bad, outside


def macro_vs_routes():
    """Top-level route shapes that enter a macro outline (other than pin landings within 1.5 um of the edge)."""
    hits = []
    for r in PLACED:
        if r["instance"] in ("u_ring",):
            continue
        x0, y0, x1, y1 = r["bbox_um"]
        inner = db.DBox(x0 + 1.5, y0 + 1.5, x1 - 1.5, y1 - 1.5)
        for lay, box, net in SHAPES:
            if lay in ("M2", "M3", "M4") and box.overlaps(inner):
                hits.append([r["instance"], lay, net, str(box)])
    return hits


issues = self_check()
ovl, outside = overlap_check()
ovl10, _ = overlap_check(10.0)
intrude = macro_vs_routes()
PLACED.insert(0, {"instance": "u_ring", "macro": "r1_padring", "orientation": "R0", "origin_um": [0, 0],
                  "bbox_um": [0, 0, DIE, DIE],
                  "source": "<G1_RESULTS_ROOT>/r1_padring/ring-20261021-d/r1_padring_1700.gds (fill instances removed: %d; west TopMetal1 ECO)" % removed_fill,
                  "source_sha256": RING_SHA, "s7_c4": [0, 0]})
gds = os.path.join(OUT, "r1_top.gds")
opt = db.SaveLayoutOptions()
opt.write_context_info = False
ly.write(gds, opt)
res = {"gds": "r1_top.gds", "gds_sha256": sha256(gds), "top": "r1_top", "die_um": DIE, "try": "e",
       "fill_instances_removed_from_ring": removed_fill, "ring_labels_copied_to_top": RING_LABELS,
       "antenna_decap_row": DECAP_ROW, "tie_cells": [TIE_CELL], "ring_eco": ECO,
       "self_check_net_conflicts": issues, "instance_overlaps": ovl, "instance_pairs_closer_than_10um": ovl10,
       "outside_extended_window": outside, "routes_inside_macros": intrude,
       "placement": PLACED, "nets": NETS, "placeholder_pins": PH_PINS,
       "macro_pins_used": {k: ({n: [round(b.left, 3), round(b.bottom, 3), round(b.right, 3), round(b.top, 3)]
                                for n, b in v.items()} if isinstance(v, dict) else
                               [[round(b.left, 3), round(b.bottom, 3), round(b.right, 3), round(b.top, 3)] for b in v])
                           for k, v in P.items()}}
with open(os.path.join(OUT, "r1_top_assembly.json"), "w") as f:
    json.dump(res, f, indent=1)
print("gds", gds, res["gds_sha256"])
print("net conflicts", len(issues))
for i in issues[:60]:
    print("  ", i)
print("overlaps", ovl, "closer than 10 um", ovl10, "outside", outside)
print("routes inside macros", len(intrude))
for i in intrude[:40]:
    print("  ", i)
