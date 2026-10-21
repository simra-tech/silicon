# SPDX-License-Identifier: Apache-2.0
"""R1 top-level assembly (track T8, P3 preparation), KLayout Python.

Places the 1600 um ring of record and the finished macros, draws placeholders for the pending
macros (afe, adc, isense a/b, osc), builds the supply connections and routes the macro-to-macro and
macro-to-pad nets that exist today. Writes r1_top.gds, a placement table and a net table (JSON).

Usage (inside the pinned container, repository root as cwd):
  python3 designs/r1-joint/blocks/r1_top/layout/r1_top_assemble.py <results_root> <out_dir>

Conventions: units um, chip origin at the lower-left die corner. Signal routing discipline:
vertical segments on Metal3, horizontal segments on Metal4 (distinct tracks per net), so two nets can
only touch at a via that the script places on purpose. Exceptions are short Metal3 necks into pins.
Floorplan F1 = S6 topology with the measured macro sizes (see README "Floorplan" for the deviations).
"""
import hashlib
import json
import os
import sys

import klayout.db as db

RES = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("G1_RESULTS_ROOT", "")
OUT = sys.argv[2] if len(sys.argv) > 2 else "."
os.makedirs(OUT, exist_ok=True)
HERE = os.path.dirname(os.path.abspath(__file__))
BLK = os.path.normpath(os.path.join(HERE, "..", ".."))           # designs/r1-joint/blocks

RING_GDS = os.path.join(RES, "r1_padring/ring-20261021-b/r1_padring_1600.gds")
RING_SHA = "40514b4f4ff7888ac0ca95329470e47c8c93c1b3efc7fec1bee2f646b8dbac19"
CTRL_GDS = os.path.join(RES, "r1_ctrl/r1ctrl_ll_20261021_t7/flow/runs/r1ctrl_ll_20261021_t7/final/gds/r1_ctrl_top.gds")
MACRO_GDS = {
    "r1_ctrl_top": CTRL_GDS,
    "r1_bgr": os.path.join(BLK, "r1_bgr/layout/r1_bgr.gds"),
    "r1_t2f": os.path.join(BLK, "r1_t2f/layout/r1_t2f.gds"),
    "r1_ls": os.path.join(BLK, "r1_ls/layout/r1_ls.gds"),
    "r1_gate_lv": os.path.join(BLK, "r1_gate/layout/r1_gate_lv_filled.gds"),
    "r1_safe": os.path.join(BLK, "r1_safe/layout/r1_safe.gds"),
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
# via size, space (array rule), enclosure used by this script (>= the PDK endcap rules on all sides)
VIA_RULE = {"V1": (0.19, 0.29, 0.10), "V2": (0.19, 0.29, 0.10), "V3": (0.19, 0.29, 0.10),
            "V4": (0.19, 0.29, 0.10), "TV1": (0.42, 0.42, 0.45), "TV2": (0.90, 1.06, 0.55)}
W = 0.5            # signal wire width (Metal2-Metal5)

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

# ---------------------------------------------------------------- ring of record
if sha256(RING_GDS) != RING_SHA:
    raise SystemExit("ring GDS hash differs from the ring of record")
ly.read(RING_GDS)
ring = ly.cell("r1_padring")
removed_fill = 0
for inst in list(ring.each_inst()):
    if inst.cell.name.endswith("_FILL_CELL"):
        removed_fill += 1
        inst.delete()
ly.cleanup()                     # drops the now unused fill cells

top = ly.create_cell("r1_top")
top.insert(db.CellInstArray(ring.cell_index(), db.Trans()))
# Pad labels: the ring of record carries its 22 pad names (TopMetal2 pin text 134/25) in its own top cell.
# Copy them into r1_top so that the chip-level nets carry the pad names (the PDK LVS deck runs flag_missing_ports,
# which needs the schematic top ports as named layout nets at the top level).
_lt = ly.layer(134, 25)
RING_LABELS = []
for _s in ring.shapes(_lt).each():
    if _s.is_text():
        top.shapes(_lt).insert(_s.dtext)
        RING_LABELS.append(_s.text_string)

def B(x0, y0, x1, y1):
    return db.DBox(min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))

# ---------------------------------------------------------------- shape bookkeeping
SHAPES = []                      # (layer, DBox, net) for the self-check

def rect(layer, box, net, cell=None):
    (cell or top).shapes(L[layer]).insert(box)
    if cell is None:
        SHAPES.append((layer, box, net))

def label(layer, x, y, text, cell=None):
    (cell or top).shapes(LT[layer]).insert(db.DText(text, db.DTrans(x, y)))

def via_array(via, box, cell=None, net=None):
    s, sp, enc = VIA_RULE[via]
    x0, y0, x1, y1 = box.left + enc, box.bottom + enc, box.right - enc, box.top - enc
    nx = max(1, int((x1 - x0 + sp) // (s + sp)))
    ny = max(1, int((y1 - y0 + sp) // (s + sp)))
    if x1 - x0 < s - 1e-6 or y1 - y0 < s - 1e-6:
        raise ValueError("via box too small: %s %s" % (via, box))
    # centre the array
    ox = x0 + (x1 - x0 - (nx * s + (nx - 1) * sp)) / 2.0
    oy = y0 + (y1 - y0 - (ny * s + (ny - 1) * sp)) / 2.0
    for i in range(nx):
        for j in range(ny):
            bx = ox + i * (s + sp)
            by = oy + j * (s + sp)
            (cell or top).shapes(L[via]).insert(db.DBox(bx, by, bx + s, by + s))

def stack(box, la, lb, net, cell=None):
    """Metal pads on every layer from la to lb over box, and via arrays between them."""
    i, j = sorted((STACK.index(la), STACK.index(lb)))
    for k in range(i, j + 1):
        rect(STACK[k], box, net, cell)
    for k in range(i, j):
        via_array(VIA_BETWEEN[(STACK[k], STACK[k + 1])], box, cell)

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
    """pts: list of (x, y). Segment k is vertical (Metal3) or horizontal (Metal4) by direction;
    a Via3 is placed at every bend between a vertical and a horizontal segment."""
    lays = []
    for p, q in zip(pts[:-1], pts[1:]):
        lay = "M3" if abs(p[0] - q[0]) < 1e-9 else "M4"
        seg(lay, p, q, net, w)
        lays.append(lay)
    for k in range(1, len(pts) - 1):
        if lays[k - 1] != lays[k]:
            x, y = pts[k]
            h = max(w, 0.5) / 2.0
            via_array("V3", B(x - h, y - h, x + h, y + h))
    if lbl and len(pts) > 1:
        (x0, y0), (x1, y1) = pts[0], pts[1]
        label(lays[0], (x0 + x1) / 2.0, (y0 + y1) / 2.0, net)
    return lays

def v3(x, y):
    via_array("V3", B(x - 0.25, y - 0.25, x + 0.25, y + 0.25))

# ---------------------------------------------------------------- macros
PLACED = []                      # placement table rows

def load_macro(name, path):
    src = db.Layout()
    src.read(path)
    tc = src.top_cell()
    new = ly.create_cell(name)
    new.copy_tree(tc)
    return new, src, tc

MAC = {}
for name, path in MACRO_GDS.items():
    MAC[name] = load_macro(name, path) + (sha256(path), path)

def tr(rot, mirror, x, y):
    return db.DCplxTrans(1.0, rot, mirror, x, y)

def place(inst_name, macro, trans, orient):
    cell, src, tc, sha, path = MAC[macro]
    top.insert(db.DCellInstArray(cell.cell_index(), trans))
    bb = tc.dbbox().transformed(trans)
    PLACED.append({"instance": inst_name, "macro": macro, "orientation": orient,
                   "origin_um": [round(trans.disp.x, 3), round(trans.disp.y, 3)],
                   "bbox_um": [round(bb.left, 3), round(bb.bottom, 3), round(bb.right, 3), round(bb.top, 3)],
                   "source": os.path.relpath(path, RES) if path.startswith(RES) else os.path.relpath(path, os.path.join(BLK, "..", "..", "..")),
                   "source_sha256": sha})
    return trans

def pin(macro, name, trans, layer="M3"):
    """Pin rectangle (chip coordinates) of a macro: the shape on the pin or drawing layer of `layer`
    that contains the label `name` in the macro top cell."""
    cell, src, tc, sha, path = MAC[macro]
    lt = src.find_layer(*LBL[layer])
    pts = []
    for s in tc.shapes(lt).each():
        if s.is_text() and s.text_string == name:
            pts.append(db.DPoint(s.dtext.x, s.dtext.y))
    if not pts:
        raise KeyError("no label %s on %s in %s" % (name, layer, macro))
    for lay in (PINP.get(layer), LY[layer]):
        li = src.find_layer(*lay)
        if li is None:
            continue
        reg = db.Region(tc.begin_shapes_rec(li)).merged()
        for p in pts:
            for poly in reg.each():
                if poly.inside(db.Point.from_dpoint(p * (1.0 / src.dbu))) or poly.bbox().contains(db.Point.from_dpoint(p * (1.0 / src.dbu))):
                    bb = poly.bbox().to_dtype(src.dbu)
                    if bb.width() < 20 and bb.height() < 20 or lay == PINP.get(layer):
                        return bb.transformed(trans)
    raise KeyError("no shape under label %s in %s" % (name, macro))

# ---- placement (F1; numbers in the README placement table)
T_CTRL = place("u_ctrl", "r1_ctrl_top", tr(0, False, 488.0, 573.0), "R0")
T_SAFE = place("u_safe", "r1_safe", tr(0, False, 1021.0, 371.0), "R0")
T_BGR = place("u_bgr", "r1_bgr", tr(270, False, 682.0, 467.0), "R270")
T_T2F = place("u_t2f", "r1_t2f", tr(180, True, 987.0, 371.0), "MY")
T_GATE = place("u_gate", "r1_gate_lv", tr(0, False, 440.0, 1196.0), "R0")
T_LS = {}
for k, x in enumerate([345.0, 365.0, 385.0, 405.0]):
    T_LS["u_ls_afe%d" % k] = place("u_ls_afe%d" % k, "r1_ls", tr(0, False, x, 628.0), "R0")
for k, x in enumerate([900.0, 920.0]):
    T_LS["u_ls_t2f%d" % k] = place("u_ls_t2f%d" % k, "r1_ls", tr(0, False, x, 482.0), "R0")

# ---- placeholders (S6 sizes; isense and osc moved 10 um west to clear the east TopMetal1 columns)
PH = {
    "r1_afe_ph": {"box": (336.0, 650.0, 476.0, 1143.0), "mim": True,
                  "pins": {"W": ["sinp", "sinn", "cosp", "cosn"],
                           "S": ["souts_p", "souts_n", "soutc_p", "soutc_n", "vcm2", "ib_s1", "ib_s2", "ib_c1",
                                 "ib_c2", "c1", "c2", "c3", "c4", "vdd", "vss"]}},
    "r1_adc_ph": {"box": (381.0, 371.0, 672.0, 543.0), "mim": True,
                  "pins": {"N": ["adc_hold", "is_smp", "adc_start", "adc_sel", "adc_valid_a"] +
                                ["adc_raw_a[%d]" % i for i in range(14)] + ["adc_valid_b"] +
                                ["adc_raw_b[%d]" % i for i in range(14)],
                           "W": ["ain_sin_p", "ain_sin_n", "ain_cos_p", "ain_cos_n"],
                           "E": ["ain_isa_p", "ain_isa_n", "ain_isb_p", "ain_isb_n", "vref_in"],
                           "S": ["vdda", "vdd", "vss"]}},
    "r1_isense_a_ph": {"box": (1056.0, 682.0, 1236.0, 843.0), "mim": True,
                       "pins": {"E": ["inp", "inn"], "W": ["outp", "outn", "az_win", "is_smp"],
                                "S": ["vdda", "vdd", "vss"]}},
    "r1_isense_b_ph": {"box": (1056.0, 853.0, 1236.0, 1014.0), "mim": True,
                       "pins": {"E": ["inp", "inn"], "W": ["outp", "outn", "az_win", "is_smp"],
                                "S": ["vdda", "vdd", "vss"]}},
    "r1_osc_ph": {"box": (1066.0, 1064.0, 1236.0, 1170.0), "mim": False,
                  "pins": {"W": ["clk", "osc_trim[0]", "osc_trim[1]", "osc_trim[2]", "osc_trim[3]",
                                 "osc_trim[4]", "vdd", "vss"]}},
}
PH_PINS = {}
for name, d in PH.items():
    x0, y0, x1, y1 = d["box"]
    c = ly.create_cell(name)
    w, h = x1 - x0, y1 - y0
    c.shapes(L["BND"]).insert(B(0, 0, w, h))
    c.shapes(L["TXT"]).insert(db.DText("PLACEHOLDER " + name, db.DTrans(w / 2.0, h / 2.0)))
    PH_PINS[name] = []
    for side, names in d["pins"].items():
        n = len(names)
        for k, pn in enumerate(names):
            f = (k + 1.0) / (n + 1.0)
            if side in ("N", "S"):
                px = round(f * w, 2)
                py0, py1 = (h - 1.0, h) if side == "N" else (0.0, 1.0)
                pb = B(px - 0.25, py0, px + 0.25, py1)
            else:
                py = round(f * h, 2)
                px0, px1 = (0.0, 1.0) if side == "W" else (w - 1.0, w)
                pb = B(px0, py - 0.25, px1, py + 0.25)
            c.shapes(L["M3"]).insert(pb)
            c.shapes(LP["M3"]).insert(pb)
            c.shapes(LT["M3"]).insert(db.DText(pn, db.DTrans(pb.center().x, pb.center().y)))
            PH_PINS[name].append({"pin": pn, "side": side,
                                  "box_um": [round(pb.left + x0, 3), round(pb.bottom + y0, 3),
                                             round(pb.right + x0, 3), round(pb.top + y0, 3)]})
    top.insert(db.DCellInstArray(c.cell_index(), db.DCplxTrans(1.0, 0, False, x0, y0)))
    PLACED.append({"instance": "u_" + name, "macro": name, "orientation": "R0", "origin_um": [x0, y0],
                   "bbox_um": [x0, y0, x1, y1], "source": "placeholder (outline + Metal3 pin stubs)",
                   "source_sha256": "-"})

# ---------------------------------------------------------------- ring ECO over the AFE (MIM, TopMetal1)
# Coordinator rule 2026-10-21: over MIM-bearing blocks the ring uses TopMetal2 only, no vias into the block.
# The west TopMetal1 columns (outer x 324.82-339.82, inner 344.82-361.8) are cut for y 645-1148 (AFE outline
# 650-1143 plus 5 um) and replaced by TopMetal2 strips of the same width (y 630-1163); TopVia2 arrays in the two
# 15 um overlaps outside the AFE outline.
ECO = {"cut_tm1": [321.0, 645.0, 365.0, 1148.0], "tm2": [], "tv2": []}
reg_tm1 = db.Region(ring.shapes(L["TM1"]))
cut = db.Region(db.Box.from_dbox(B(*ECO["cut_tm1"]) * (1.0 / ly.dbu)))
new_tm1 = reg_tm1 - cut
ring.shapes(L["TM1"]).clear()
ring.shapes(L["TM1"]).insert(new_tm1)
for (cx0, cx1, net) in [(324.82, 339.82, "VSS"), (344.82, 361.8, "VDD")]:
    tb = B(cx0, 630.0, cx1, 1163.0)
    rect("TM2", tb, net)
    ECO["tm2"].append([cx0, 630.0, cx1, 1163.0])
    for (vy0, vy1) in [(630.0, 645.0), (1148.0, 1163.0)]:
        via_array("TV2", B(cx0, vy0, cx1, vy1))
        ECO["tv2"].append([cx0, vy0, cx1, vy1])
# record the ring shapes in the self-check
SHAPES.append(("TM1", B(324.82, 321.0, 339.82, 645.0), "VSS"))
SHAPES.append(("TM1", B(344.82, 321.0, 361.8, 645.0), "VDD"))
SHAPES.append(("TM1", B(324.82, 1148.0, 339.82, 1279.0), "VSS"))
SHAPES.append(("TM1", B(344.82, 1148.0, 361.8, 1279.0), "VDD"))

# ---------------------------------------------------------------- supplies
# Ring identity chosen here: outer core ring = VSS, inner core ring = VDD.
# North: ctrl TopMetal1 stripes extended to the ring rows (VDD to the inner TM2 row 1237.3-1252.3, VSS through it
# to the outer row 1257.3-1272.3 and on to the IO-row vss TopMetal1 rail 1281-1299).
CTRL_VDD_X = [23.54, 99.14, 174.74, 250.34, 325.94, 401.54, 477.14]
CTRL_VSS_X = [29.74, 105.34, 180.94, 256.54, 332.14, 407.74, 483.34]
for lx in CTRL_VDD_X:
    x = 488.0 + lx
    rect("TM1", B(x, 1222.0, x + 2.2, 1252.3), "VDD")
    via_array("TV2", B(x, 1237.3, x + 2.2, 1252.3))
for lx in CTRL_VSS_X:
    x = 488.0 + lx
    rect("TM1", B(x, 1222.0, x + 2.2, 1297.0), "VSS")
    via_array("TV2", B(x, 1257.3, x + 2.2, 1272.3))
# North: VDD ring <-> IO-row vdd Metal3 rail (1281-1299) with Metal3 straps over fillers and a stack to TM2.
N_VDD_STRAPS = [(776.0, 783.0), (916.0, 923.0), (1056.0, 1063.0), (1196.0, 1203.0)]
for (x0, x1) in N_VDD_STRAPS:
    rect("M3", B(x0, 1238.0, x1, 1297.0), "VDD")
    stack(B(x0, 1238.0, x1, 1251.5), "M3", "TM2", "VDD")
# Antenna load on VDD (fix for Ant.e_Metal5/TopMetal1/TopMetal2 at the four IOPadIn receiver gates, which tie to the
# IO-row vdd rail): a row of PDK sg13g2_decap_8 cells (NMOS gate on VDD, 0.84 um^2 each) under the north VDD strap
# x 1056-1063, joined to VDD on Metal3 (strap) and to VSS on Metal4 (strap to the IO-row vss Metal4 rail 1281-1296.8).
# The r1_padring README records the cause: without core gate load the deck divides the whole vdd metal by the
# receiver gate area only.
import glob as _glob
_sc = db.Layout()
_sc.read(_glob.glob("/foss/pdks/ihp-sg13g2/libs.ref/sg13g2_stdcell/gds/sg13g2_stdcell.gds")[0])
# Reuse the library cell that came in with r1_ctrl_top (same PDK library, same name), so that LVS pairs it with
# the CDL subcircuit; a second copy would get the name sg13g2_decap_8$1 and be flattened by the deck.
DECAP = ly.cell("sg13g2_decap_8")
DECAP_SRC = "from r1_ctrl_top (PDK library cell)"
if DECAP is None:
    DECAP = ly.create_cell("sg13g2_decap_8")
    DECAP.copy_tree(_sc.cell("sg13g2_decap_8"))
    DECAP_SRC = "copied from the PDK library"
assert DECAP.dbbox() == _sc.cell("sg13g2_decap_8").dbbox()
N_DECAP, DX0, DY0, DPITCH = 34, 1057.0, 1255.0, 3.36
top.insert(db.DCellInstArray(DECAP.cell_index(), db.DTrans(DX0, DY0), db.DVector(DPITCH, 0), db.DVector(0, 0), N_DECAP, 1))
DEC_X1 = DX0 + N_DECAP * DPITCH
SHAPES.append(("M1", B(DX0, DY0 + 3.56, DEC_X1, DY0 + 4.0), "VDD"))
SHAPES.append(("M1", B(DX0, DY0 - 0.22, DEC_X1, DY0 + 0.22), "VSS"))
_vb = B(1057.2, DY0 + 3.56, 1062.8, DY0 + 4.0)                       # VDD rail under the Metal3 strap
rect("M2", _vb, "VDD")
via_array("V1", _vb)
via_array("V2", _vb)
_sb = B(1160.0, DY0 - 0.22, 1166.0, DY0 + 0.22)                      # VSS rail, stack to Metal4
stack(_sb, "M2", "M4", "VSS")
via_array("V1", _sb)
rect("M4", B(1160.0, DY0 - 0.22, 1166.0, 1290.0), "VSS")
DECAP_ROW = {"cell": "sg13g2_decap_8", "count": N_DECAP, "origin_um": [DX0, DY0], "pitch_um": DPITCH,
             "bbox_um": [DX0, DY0, round(DEC_X1, 3), DY0 + 3.78], "gate_area_on_VDD_um2": round(N_DECAP * 0.84, 2), "cell_source": DECAP_SRC}
# South analog trunks under the south ring band (Metal4)
TR = {"VSS": (332.0, 340.0), "VDD": (343.0, 349.0), "VDDA": (352.0, 360.0)}
rect("M4", B(371.0, 332.0, 1278.0, 340.0), "VSS")
rect("M4", B(371.0, 343.0, 1266.0, 349.0), "VDD")
rect("M4", B(371.0, 352.0, 1278.0, 360.0), "VDDA")
label("M4", 380.0, 336.0, "VSS")
label("M4", 380.0, 346.0, "VDD")
label("M4", 380.0, 356.0, "VDDA")
S_FILLERS = [(491.0, 549.0), (631.0, 689.0), (771.0, 829.0), (911.0, 969.0), (1051.0, 1109.0)]
for (f0, f1) in S_FILLERS:
    rect("M4", B(f0 + 9.0, 304.0, f0 + 39.0, 340.0), "VSS")            # IO vss Metal4 rail 303.2-319
    rect("M3", B(f0 + 2.0, 302.0, f0 + 8.0, 349.0), "VDD")             # IO vdd Metal3 rail 301-319
    via_array("V3", B(f0 + 2.0, 343.0, f0 + 8.0, 349.0))
# VDDA feed from pad 7 (sg13g2_IOPadAnalog `pad`, Metal3 at x 1279-1279.29, y 436.1-460.9)
rect("M3", B(1272.0, 437.0, 1279.29, 460.0), "VDDA")
rect("M4", B(1272.0, 352.0, 1278.0, 460.0), "VDDA")
via_array("V3", B(1272.0, 437.0, 1278.0, 460.0))
label("M3", 1275.0, 448.0, "VDDA")

# ---- macro supply hookups
def first_shape_box(macro, layer_key, pt_local, trans):
    cell, src, tc, sha, path = MAC[macro]
    li = src.find_layer(*LY[layer_key])
    reg = db.Region(tc.begin_shapes_rec(li)).merged()
    p = db.Point.from_dpoint(db.DPoint(*pt_local) * (1.0 / src.dbu))
    for poly in reg.each():
        if poly.inside(p):
            return poly.bbox().to_dtype(src.dbu).transformed(trans), poly.bbox().to_dtype(src.dbu)
    raise KeyError("no %s shape at %s in %s" % (layer_key, pt_local, macro))

BUS = {}
# bgr: vss bus (label at 48,1) and vdd bus (48,193.3) on Metal3; after R270 they are vertical bars.
BUS["bgr_vss"], _ = first_shape_box("r1_bgr", "M3", (48.0, 1.0), T_BGR)
BUS["bgr_vdd"], _ = first_shape_box("r1_bgr", "M3", (48.0, 193.3), T_BGR)
b = BUS["bgr_vss"]
rect("M3", B(b.left, 333.0, b.left + 2.0, b.bottom + 1.0), "VSS")
via_array("V3", B(b.left, 333.0, b.left + 2.0, 340.0))
b = BUS["bgr_vdd"]
rect("M3", B(b.right - 2.0, 352.0, b.right, b.bottom + 1.0), "VDDA")
via_array("V3", B(b.right - 2.0, 352.0, b.right, 360.0))
# t2f: vss bar (Metal3, y 371-373.6 after MY), vdd bar (471-473.6), vdd12 pin.
rect("M3", B(900.0, 333.0, 906.0, 372.0), "VSS")
via_array("V3", B(900.0, 333.0, 906.0, 340.0))
rect("M3", B(986.0, 471.0, 993.0, 473.6), "VDDA")
rect("M3", B(989.0, 352.0, 993.0, 473.6), "VDDA")
via_array("V3", B(989.0, 352.0, 993.0, 360.0))
# safe: vdda east pin into the VDDA feed; vss and vdd west pins to the trunks.
rect("M3", B(1270.34, 375.6, 1271.7, 376.0), "VDDA")
rect("M3", B(1271.6, 374.6, 1274.0, 377.0), "VDDA")
via_array("V3", B(1272.0, 374.6, 1274.0, 377.0))
rect("M3", B(1017.35, 374.8, 1021.0, 375.2), "VSS")
rect("M3", B(1017.35, 333.0, 1017.85, 375.2), "VSS")
via_array("V3", B(1017.35, 333.0, 1017.85, 340.0))
rect("M3", B(1016.35, 376.4, 1021.0, 376.8), "VDD")
rect("M3", B(1016.35, 343.0, 1016.85, 376.8), "VDD")
via_array("V3", B(1016.35, 343.0, 1016.85, 349.0))
# gate_lv: vdd from the inner west TM1 column (VDD), vss from the outer column (VSS); gate_en tied to vdd.
GY = 1196.0
rect("M3", B(437.6, GY + 14.08, 440.4, GY + 14.58), "VDD")              # vdd pin extension
rect("M3", B(437.6, GY + 16.45, 440.4, GY + 16.95), "VDD")              # gate_en pin extension (tied to VDD)
rect("M2", B(437.75, GY + 14.0, 438.15, GY + 17.05), "VDD")             # Metal2 jumper
via_array("V2", B(437.75, GY + 14.08, 438.15, GY + 14.58 + 0.06))
via_array("V2", B(437.75, GY + 16.45 - 0.06, 438.15, GY + 16.95))
rect("M4", B(346.0, GY + 14.08, 439.0, GY + 14.58), "VDD")
via_array("V3", B(438.0, GY + 14.08, 439.0, GY + 14.58))
stack(B(346.0, GY + 12.5, 360.0, GY + 16.0), "M4", "TM1", "VDD")
rect("M3", B(436.0, GY + 1.5, 440.4, GY + 4.5), "VSS")                  # vss bar extension
rect("M4", B(326.0, GY + 1.5, 439.5, GY + 4.5), "VSS")
via_array("V3", B(436.0, GY + 1.5, 439.5, GY + 4.5))
stack(B(326.0, GY + 0.5, 338.0, GY + 5.5), "M4", "TM1", "VSS")

# ---------------------------------------------------------------- signals
NETS = {}

def note(net, src, dst, layers, state):
    NETS[net] = {"source": src, "destinations": dst, "metal": layers, "state": state}

def ctrl_pin(name):
    return pin("r1_ctrl_top", name, T_CTRL, "M2" if name in ("gate_a", "gate_b", "gate_c", "cs_n", "ma_sclk",
                                                                  "slo_sdo", "por_n", "t2f_clk") else "M3")

def east_land(net, name, track_x):
    """ctrl east pin (Metal3, 0.4 x 0.4 at x 1007.6-1008) -> via pad at x 1009.3 -> Metal4 to track_x."""
    pb = ctrl_pin(name)
    yc = pb.center().y
    rect("M3", B(pb.left, pb.bottom, 1009.55, pb.top), net)
    rect("M3", B(1009.05, yc - 0.25, 1009.55, yc + 0.25), net)
    via_array("V3", B(1009.05, yc - 0.25, 1009.55, yc + 0.25))
    rect("M4", B(1009.05, yc - 0.25, track_x + 0.25, yc + 0.25), net)
    return yc

def north_up(net, name, y_level):
    """ctrl north pin (Metal2) -> Via2 just above the macro edge -> Metal3 up to y_level."""
    pb = ctrl_pin(name)
    xc = pb.center().x
    rect("M2", B(pb.left, pb.bottom, pb.right, 1238.2), net)
    rect("M3", B(xc - 0.25, 1237.4, xc + 0.25, 1238.2), net)
    via_array("V2", B(pb.left, 1237.4, pb.right, 1238.2))
    return xc

def pad_pin_down(net, x_pin, y_level):
    """Metal3 vertical from y_level up into a pad core pin at the north IO edge (y 1279-1279.29)."""
    seg("M3", (x_pin, y_level), (x_pin, 1279.29 - W / 2.0), net)

# --- R1: ctrl <-> north pads (Metal3 up, Metal4 across, Metal3 up into the pad pin)
for net, name, xpad, ylev in [("CS_N_P2C", "cs_n", 869.975, 1268.0), ("MA_SCLK_P2C", "ma_sclk", 1009.975, 1270.5),
                              ("SLO_SDO_C2P", "slo_sdo", 1150.0, 1273.0)]:
    xc = north_up(net, name, ylev)
    route(net, [(xc, 1237.8), (xc, ylev), (xpad, ylev), (xpad, 1279.04)])
    if net == "SLO_SDO_C2P":
        note(net, "u_ctrl/slo_sdo", ["pad 18 SLO_SDO c2p"], "M2 stub, M3, M4", "routed")
    else:
        note(net, "pad %s p2c" % net[:-4], ["u_ctrl/%s" % name], "M2 stub, M3, M4", "routed")
# --- R2: ctrl gate_a/b/c -> gate_lv pwm_a/b/c (inputs on the gate_lv west edge, Metal3 tracks x 432/434/436)
for net, name, tx, py, ylev in [("PWM_A", "gate_a", 432.0, GY + 15.9, 1240.5), ("PWM_B", "gate_b", 434.0, GY + 17.5, 1243.0),
                                ("PWM_C", "gate_c", 436.0, GY + 18.3, 1245.5)]:
    xc = north_up(net, name, ylev)
    route(net, [(xc, 1237.8), (xc, ylev), (tx, ylev), (tx, py)])
    rect("M3", B(tx - 0.25, py - 0.25, 441.0, py + 0.25), net)          # Metal3 neck east into the pin
    note(net, "u_ctrl/%s" % name, ["u_gate/pwm_%s" % net[-1].lower()], "M2 stub, M3, M4", "routed")
# --- gate_lv outputs -> pads 13-15 c2p (Metal3 east necks, Metal3 up, Metal4 across, Metal3 up)
for net, pnm, py, tx, ylev, xpad in [("GATE_A_C2P", "gc_a", GY + 15.9, 474.0, 1256.0, 450.0),
                                    ("GATE_C_C2P", "gc_c", GY + 16.7, 472.0, 1261.0, 730.0),
                                    ("GATE_B_C2P", "gc_b", GY + 17.5, 470.0, 1258.5, 590.0)]:
    rect("M3", B(467.4, py - 0.25, tx + 0.25, py + 0.25), net)
    route(net, [(tx, py), (tx, ylev), (xpad, ylev), (xpad, 1279.04)])
    note(net, "u_gate/%s" % pnm, ["pad %s c2p (sg13g2_IOPadOut30mA; its own 1.2->3.3 V shifter)" % net[:6]],
         "M3, M4", "routed")
# --- FAULT_N: ctrl east pin -> strip_e track 1014.5 -> y 1175 -> east -> Metal3 down into pad 12 c2p
yc = east_land("FAULT_N_C2P", "fault_n", 1014.5)
v3(1014.5, yc)
route("FAULT_N_C2P", [(1014.5, yc), (1014.5, 1175.0), (1277.5, 1175.0), (1277.5, 1150.0)])
rect("M3", B(1277.25, 1149.5, 1279.29, 1150.5), "FAULT_N_C2P")
note("FAULT_N_C2P", "u_ctrl/fault_n", ["pad 12 FAULT_N c2p"], "M3, M4", "routed")
# --- SDI and EN: west pads 19/20 p2c (Metal3 at x 320.71-321) -> ctrl west pins (x 488-488.4)
for net, ypad, name, path in [
        ("SDI_P2C", 449.975, "sdi", [(323.25, 449.975), (373.0, 449.975), (373.0, 548.0), (484.0, 548.0)]),
        ("EN_STO_IN_P2C", 589.975, "en_pad", [(323.25, 589.975), (478.0, 589.975)])]:
    pb = ctrl_pin(name)
    yc = pb.center().y
    rect("M3", B(320.71, ypad - 0.25, 323.5, ypad + 0.25), net)
    via_array("V3", B(323.0, ypad - 0.25, 323.5, ypad + 0.25))
    xv = path[-1][0]
    route(net, path + [(xv, yc), (487.25, yc)])
    rect("M3", B(487.0, yc - 0.25, 487.5, yc + 0.25), net)
    via_array("V3", B(487.0, yc - 0.25, 487.5, yc + 0.25))
    rect("M3", B(487.0, pb.bottom, pb.right, pb.top), net)
    note(net, "pad %s p2c" % net[:-4], ["u_ctrl/%s" % name], "M3, M4", "routed")
# --- bgr -> t2f (pbias, pcasc), bgr vref -> t2f and safe
P_BGR = {n: pin("r1_bgr", n, T_BGR) for n in ("vref", "pbias", "pcasc", "iptat", "vbe", "dvbe")}
P_T2F = {n: pin("r1_t2f", n, T_T2F) for n in ("vref", "pbias", "pcasc", "vdd12", "fout", "en", "mode")}
P_SAFE = {n: pin("r1_safe", n, T_SAFE) for n in ("vref", "oc_a", "neg_a", "oc_b", "neg_b")}

def t2f_land(net, pname, xtrack):
    """t2f west pin (after MY, x 895-896.6): Metal4 from xtrack to x 893.5, Via3, Metal3 neck into the pin."""
    pb = P_T2F[pname]
    yc = pb.center().y
    rect("M3", B(893.25, yc - 0.25, pb.right, yc + 0.25) if pb.height() >= 0.5 else B(893.25, pb.bottom, pb.right, pb.top), net)
    rect("M3", B(893.25, yc - 0.25, 893.75, yc + 0.25), net)
    via_array("V3", B(893.25, yc - 0.25, 893.75, yc + 0.25))
    rect("M4", B(xtrack - 0.25, yc - 0.25, 893.75, yc + 0.25), net)
    v3(xtrack, yc)
    return yc

for net, pname, ych, xtr in [("T2F_PBIAS", "pbias", 368.5, 880.0), ("T2F_PCASC", "pcasc", 366.5, 882.0)]:
    pb = P_BGR[pname]
    xc = pb.center().x
    rect("M3", B(pb.left, ych, pb.right, pb.top), net)
    yt = P_T2F[pname].center().y
    route(net, [(xc, ych), (xtr, ych), (xtr, yt)])
    rect("M3", B(xc - 0.25, ych - 0.25, xc + 0.25, ych + 0.25), net)   # Via3 endcap (V3.c1, try a)
    v3(xc, ych)
    t2f_land(net, pname, xtr)
    note(net, "u_bgr/%s" % pname, ["u_t2f/%s" % pname], "M3, M4", "routed")
pb = P_BGR["vref"]
xv = pb.center().x
rect("M3", B(pb.left, pb.bottom, pb.right, 468.0), "VREF_BG")
yv_safe = P_SAFE["vref"].center().y
route("VREF_BG", [(xv, 467.5), (xv, 520.0), (1015.6, 520.0), (1015.6, yv_safe), (1020.55, yv_safe)])
rect("M3", B(1020.3, yv_safe - 0.25, 1020.8, yv_safe + 0.25), "VREF_BG")
via_array("V3", B(1020.3, yv_safe - 0.25, 1020.8, yv_safe + 0.25))
ps = P_SAFE["vref"]
rect("M3", B(1020.3, ps.bottom, ps.right, ps.top), "VREF_BG")
yt = P_T2F["vref"].center().y
via_array("V3", B(885.75, 519.75, 886.25, 520.25))
route("VREF_BG", [(886.0, 520.0), (886.0, yt)], lbl=False)
t2f_land("VREF_BG", "vref", 886.0)
note("VREF_BG", "u_bgr/vref", ["u_t2f/vref", "u_safe/vref", "r1_adc_ph/vref_in (pending)"], "M3, M4",
     "routed to t2f and safe; adc pending")
# t2f vdd12 <- VDD trunk (Metal3 track x 891.5)
yt = t2f_land("VDD", "vdd12", 891.5)
seg("M3", (891.5, 343.25), (891.5, yt), "VDD")
via_array("V3", B(891.25, 343.0, 891.75, 349.0))
# t2f fout -> ctrl t2f_clk (south pin, Metal2)
yt = t2f_land("T2F_FOUT", "fout", 889.0)
pc = ctrl_pin("t2f_clk")
xc = pc.center().x
route("T2F_FOUT", [(889.0, yt), (889.0, 556.0), (xc, 556.0), (xc, 571.75)])
rect("M2", B(pc.left, 571.4, pc.right, pc.top), "T2F_FOUT")
rect("M3", B(xc - 0.25, 571.4, xc + 0.25, 572.1), "T2F_FOUT")
via_array("V2", B(pc.left, 571.4, pc.right, 572.1))
note("T2F_FOUT", "u_t2f/fout", ["u_ctrl/t2f_clk"], "M2 stub, M3, M4", "routed")
# --- safe flags -> ctrl cmp[3:0] (bottom channel y 362.5-367, strip_e tracks x 1010.5-1013.5)
for k, (flag, ych, xtr) in enumerate([("oc_a", 362.5, 1010.5), ("neg_a", 364.0, 1011.5),
                                       ("oc_b", 365.5, 1012.5), ("neg_b", 367.0, 1013.5)]):
    net = "CMP_%s" % flag.upper()
    pb = P_SAFE[flag]
    xc = pb.center().x
    rect("M3", B(pb.left, ych, pb.right, pb.top), net)
    yc = east_land(net, "cmp[%d]" % k, xtr)
    route(net, [(xc, ych), (xtr, ych), (xtr, yc)])
    rect("M3", B(xc - 0.25, ych - 0.25, xc + 0.25, ych + 0.25), net)   # Via3 endcap (V3.c1, try a)
    v3(xc, ych)
    v3(xtr, yc)
    note(net, "u_safe/%s" % flag, ["u_ctrl/cmp[%d]" % k], "M3, M4", "routed")

# ---------------------------------------------------------------- self-check: different nets on one layer
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

def overlap_check():
    rows = [r for r in PLACED]
    bad = []
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            a, b = rows[i]["bbox_um"], rows[j]["bbox_um"]
            if a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]:
                bad.append([rows[i]["instance"], rows[j]["instance"]])
    outside = [r["instance"] for r in rows if r["bbox_um"][0] < 321 or r["bbox_um"][1] < 321 or
               r["bbox_um"][2] > 1279 or r["bbox_um"][3] > 1279]
    return bad, outside

issues = self_check()
ovl, outside = overlap_check()
PLACED.insert(0, {"instance": "u_ring", "macro": "r1_padring", "orientation": "R0", "origin_um": [0, 0],
                  "bbox_um": [0, 0, 1600, 1600],
                  "source": "r1_padring/ring-20261021-b/r1_padring_1600.gds (fill instances removed: %d; west TopMetal1 ECO)" % removed_fill,
                  "source_sha256": RING_SHA})

gds = os.path.join(OUT, "r1_top.gds")
opt = db.SaveLayoutOptions()
opt.write_context_info = False
ly.write(gds, opt)
res = {"gds": "r1_top.gds", "gds_sha256": sha256(gds), "top": "r1_top", "die_um": 1600,
       "fill_instances_removed_from_ring": removed_fill, "ring_labels_copied_to_top": RING_LABELS, "antenna_decap_row": DECAP_ROW, "ring_eco": ECO,
       "self_check_net_conflicts": issues, "instance_overlaps": ovl, "outside_io_row": outside,
       "placement": PLACED, "nets": NETS, "placeholder_pins": PH_PINS}
with open(os.path.join(OUT, "r1_top_assembly.json"), "w") as f:
    json.dump(res, f, indent=1)
print("gds", gds, res["gds_sha256"])
print("net conflicts", len(issues))
for i in issues[:40]:
    print("  ", i)
print("overlaps", ovl, "outside", outside)
