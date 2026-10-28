# SPDX-License-Identifier: Apache-2.0
"""R1 top-level assembly, try h (tracks T8f h0, T8g h1): the try-g assembly with a new supply feed for r1_ctrl, KLayout Python.

Try h1 (track T8g, PLAN.md D24, default): every IO cell stays as shipped. The h0 network below without item 1 (no cell
edit): instead, two 28 um TopMetal2 fingers per IOPadVss over the cell (local y 160-201.16, the only free top-cell layer
there) with TopVia2 onto the cell's TopMetal1 vss pin, joined to the outer south VSS row (pin access). New: AFE VDDA
TopMetal1 strap x 368-522, y 727-738 over the 2.8 um Metal4 AFE VDDA rail (R1H_NO_VDDA_STRAP=1 leaves it out).
Switches: R1H_IOPADVSS_ECO=1 (with R1H_NO_VDDA_STRAP=1: the rejected h0 network, record only); R1H_PADMAP=vss4 / vss6
(pin-map variant: die pad 4 / 6 IOPadIOVss replaced by the unmodified IOPadVss; LVS reference from
flow/ring_cdl_padswap.py through R1H_RING_CDL in lvs/make_top_cdl_g.py); R1H_NO_FEED=1 (the try-g network).
README "Supply feed with unmodified pads (try h1)", reports/supply_h1.md.

--- try h0 (track T8f) ---

Copy of r1_top_assemble_g.py (try g, track T8e; placement, macros, signal routing and checks unchanged) with the try-h0
supply network (README "Supply feed redesign (try h preparation)", reports/supply_h0.md). Every change is in the
section "try h0 supply feed" and in the south VDD bar; with R1H_NO_FEED=1 the generator draws the try-g supply network.
  1. IOPadVss riser (ring ECO): in the ring copy of sg13g2_IOPadVss (pads 2 and 5) the IO TopMetal2 rails are cut over
     the pad (local x 3.9-76.1, the IOPadVdd pattern) and a TopMetal2 riser (local 5-75 x 0-178) joins the bondpad to
     the VSS TopMetal1 rail (TopVia2, local y 160-178). Two 28 um TopMetal2 fingers join the riser to the outer south
     VSS TopMetal2 row. The PDK cell joins pad and rail only through a Metal2 plate (extracted try g: 27 mV at max sheet).
  2. VDD riser at pad 1: the outer south VSS TopMetal2 row is opened over x 453-537; two 28 um TopMetal2 fingers join
     the pad-1 TopMetal2 riser to the inner south VDD row. A TopMetal1 bridge under the fingers and TopMetal1 tabs
     join the VSS row to the VSS TopMetal1 IO rail on both sides of the gap.
  3. VSS TopMetal1 tabs (rail <-> outer VSS row, TopVia2) along the south side.
  4. South VSS feed of r1_ctrl: TopMetal1 straps from the VSS IO rail to a TopMetal1 bar under the ctrl south band
     (west x 566-590 under the VDD TopMetal2 strap, east x 1036-1064 in the ADC-safe channel; no TopMetal1 over a MIM
     block), bar y 654.5-682.5, TopMetal1 extensions onto the 7 ctrl VSS stripes (they start at local y 10.71).
  5. South VDD feed: the TopMetal2 bar over the ctrl south band is 28 um (y 664-692, try g 684-692); a second
     TopMetal2 strap from the inner south VDD row (x 1036-1064) over the VSS strap.
  No signal route is crossed (the new shapes are TopMetal1/TopMetal2; the signal routes use Metal2-Metal5).

--- try g docstring ---
R1 top-level assembly, try g (track T8e): current macros, floorplan C4 on the 1700 um ring of record, KLayout Python.

Copy of r1_top_assemble_f.py with the try-g changes (README "Try g"): r1_ctrl_top 0.8 (release r1ctrl_08_release, 532 x 679,
128 pins incl. cur_trk), r1_adc with the SAR sub-macro (439.0 x 205.42; north pins Metal2, labels in CDL form
`adc_raw_a<k>`, new pin cur_trk; GDS taken from blocks/r1_adc/layout/r1_adc.gds at the start of try g), r1_afe layout E6,
no temporary antenna diodes (the ADC drives its outputs), supply necks at the full width of the 1.0 um macro supply pins,
identical PDK standard cells of different macros merged into one cell (LVS hierarchy).
Places the 1700 um ring (r1_padring revision d) and every macro of record: r1_ctrl_top, r1_adc, r1_afe,
r1_isense layout c, r1_bias revision 2 (vref_b), r1_osc revision 2, r1_safe, r1_bgr, r1_t2f,
r1_gate_lv, 6 x r1_ls. Builds the core supplies, the MIM ring rule (TopMetal2 only over the AFE under the west columns),
hand routes (pads, oscillator, north, the 64 safe tap lines, the Metal5 analog lines vref, vref_b and the AFE / isense
pairs with VSS shields, the isense vss path to the ring) and routes the remaining signal nets with a grid maze router
(Metal2-Metal4, layout/maze_router_top.py). Writes r1_top.gds and r1_top_assembly.json (placement, nets, instance
pin-to-net map for lvs/make_top_cdl_f.py, self-checks).

Usage (inside the pinned container, repository root as cwd):
  python3 designs/r1-joint/blocks/r1_top/layout/r1_top_assemble_h.py <results_root> <out_dir> <ofrecord_dir>
<ofrecord_dir> holds the input GDS snapshots of r1_afe, r1_adc, r1_isense and r1_bias. Drop-in of a new
revision (ADC B6 final, AFE E7): copy the new GDS into <ofrecord_dir> under the same name and set the environment variable
R1G_SHA_<macro> (e.g. R1G_SHA_r1_adc) to its sha256; pins are read from the GDS labels, the AFE ring cut follows the
AFE height. Coordinates and their reasons: README "Try g"; drop-in rules: reports/integration_checklist_g.md.
"""
import hashlib
import json
import os
import sys

import klayout.db as db

RES, OUT, OFR = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(OUT, exist_ok=True)
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import maze_router_top as MZ  # noqa: E402

BLK = os.path.normpath(os.path.join(HERE, "..", ".."))           # designs/r1-joint/blocks
REPO = os.path.normpath(os.path.join(BLK, "..", "..", ".."))
DIE = 1700.0
LOG = open(os.path.join(OUT, "gen_detail.log"), "w")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    LOG.write(s + "\n")
    LOG.flush()


RING_GDS = os.path.join(RES, "r1_padring/ring-20261021-d/r1_padring_1700.gds")
RING_SHA = "81bba04b3c0655ece75587d6c90b159d4bb860e0dbe0e3dd80e2c65c50d0725d"
CTRL_GDS = os.path.join(RES, "r1_ctrl/r1ctrl_08_release/r1_ctrl_top.gds")
MACRO_GDS = {
    "r1_ctrl_top": CTRL_GDS,
    "r1_bgr": os.path.join(BLK, "r1_bgr/layout/r1_bgr.gds"),
    "r1_t2f": os.path.join(BLK, "r1_t2f/layout/r1_t2f.gds"),
    "r1_ls": os.path.join(BLK, "r1_ls/layout/r1_ls.gds"),
    "r1_gate_lv": os.path.join(BLK, "r1_gate/layout/r1_gate_lv_filled.gds"),
    "r1_safe": os.path.join(BLK, "r1_safe/layout/r1_safe.gds"),
    "r1_osc": os.path.join(BLK, "r1_osc/layout/r1_osc.gds"),
    "r1_bias": os.path.join(OFR, "r1_bias.gds"),
    "r1_afe": os.path.join(OFR, "r1_afe.gds"),
    "r1_adc": os.path.join(OFR, "r1_adc.gds"),
    "r1_isense": os.path.join(OFR, "r1_isense.gds"),
}
# GDS of record - the generator refuses other files (override per macro: environment R1G_SHA_<macro>)
EXPECT_SHA = {
    "r1_ctrl_top": "f8bc16ed7233d1ea3eb12dd3f0cc1045eb169ea842c0d7ab6aad06d9ed302d2e",  # 0.8, r1ctrl_ll_20261027_t22
    "r1_afe": "12a059ca4b9468541c479b13e8e77d946852b57c826f7dd568db60ae4f64ba7f",       # layout E6, fd0fcf4e4
    "r1_adc": "9d6dad3d23a033e0484d4fc8d23ba25280c3231680f244c25b44dc9c5c49d880",       # working tree at the try-g start (B6-dev3; B5 = 551dab83...)
    "r1_isense": "192dd37aa592b85d68b158b18f0f71c8e906664783b047dcdd3bf1ceacd6c7ac",    # layout c, c09410f07
    "r1_bias": "e7ee13940db0ecc2a36c8bf7c6d1947358aceb6dd1dff3b3add9f4eafa2bb78c",      # revision 2, ae4dfac95
    "r1_osc": "7c5fb60fdbbfa3cce7714520d3bc652292f0ff964452e3bf4afe226ea68ba971",       # revision 2, layout r2d
    "r1_safe": "fbc3113948e0c15e1e049cfad1e2e5c5349b10ba0ae7d250f5b228e50aa28324",
    "r1_bgr": "324e3c27477a77c4a32d6760366d8d1fb82bea4887ae26b905cd7022aac54005",
    "r1_t2f": "5e7aa75ae9335b12b1c825d326e586c742755bd9305074fc1cdc2507d17af9a7",
    "r1_ls": "a4f496364b55c71a035f44a9b13b68fd8475f98b05f5e13a4e38e9ec1703b4de",
    "r1_gate_lv": "a3dee0f091c5236f7b6ff231b765d0b70e60a6e791d9db0b12fd821ce44e013b",
}
for _k in list(EXPECT_SHA):
    if os.environ.get("R1G_SHA_" + _k):
        EXPECT_SHA[_k] = os.environ["R1G_SHA_" + _k]

# ---------------------------------------------------------------- layers
LY = {"M1": (8, 0), "V1": (19, 0), "M2": (10, 0), "V2": (29, 0), "M3": (30, 0), "V3": (49, 0),
      "M4": (50, 0), "V4": (66, 0), "M5": (67, 0), "TV1": (125, 0), "TM1": (126, 0), "TV2": (133, 0),
      "TM2": (134, 0), "BND": (189, 4), "TXT": (63, 0)}
PINP = {"M2": (10, 2), "M3": (30, 2), "M4": (50, 2)}
LBL = {"M1": (8, 25), "M2": (10, 25), "M3": (30, 25), "M4": (50, 25), "M5": (67, 25)}
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
# Try h1 (track T8g, PLAN.md D24): every IO cell stays as shipped. R1H_IOPADVSS_ECO=1 draws the rejected try-h0 riser
# (edited IOPadVss copy, record only). R1H_PADMAP=vss4 / vss6: variant with die pad 4 / 6 (IOPadIOVss, IOVSS) replaced
# by the unmodified IOPadVss cell (a third core VSS pad; pin-map change, owner decision; README "try h1").
RISER = bool(os.environ.get("R1H_IOPADVSS_ECO"))
PADMAP = os.environ.get("R1H_PADMAP", "")
if PADMAP not in ("", "vss4", "vss6"):
    raise SystemExit("R1H_PADMAP must be empty, vss4 or vss6")
VSS_PAD_X = [597.0, 1023.0]                          # IOPadVss cell origins (die pads 2 and 5), y 141
PADSWAP = {}
if PADMAP:
    _px = 881.0 if PADMAP == "vss4" else 1165.0
    _vcell = ly.cell("retained_fullchip_sg13g2_IOPadVss")
    _hit = [i for i in ring.each_inst() if i.cell.name == "retained_fullchip_sg13g2_IOPadIOVss"
            and abs(i.dcplx_trans.disp.x - _px) < 1e-3 and abs(i.dcplx_trans.disp.y - 141.0) < 1e-3]
    if len(_hit) != 1:
        raise SystemExit("pad swap: IOPadIOVss at x %.0f not found" % _px)
    _hit[0].cell_index = _vcell.cell_index()
    VSS_PAD_X = sorted(VSS_PAD_X + [_px])
    _ltr = ly.layer(134, 25)
    _relab = []
    if PADMAP == "vss4":            # first-pad label rule: pad 4 loses the IOVSS label, pad 6 (now the first IOVSS pad) gets it
        for _sh in list(ring.shapes(_ltr).each()):
            if _sh.is_text() and _sh.text_string == "IOVSS" and abs(_sh.dtext.x - 921.0) < 1e-3:
                _t = _sh.dtext
                ring.shapes(_ltr).erase(_sh)
                ring.shapes(_ltr).insert(db.DText("IOVSS", db.DTrans(1205.0, _t.y)))
                _relab.append(["IOVSS", [921.0, _t.y], [1205.0, _t.y]])
    PADSWAP = {"padmap": PADMAP, "die_pad": 4 if PADMAP == "vss4" else 6, "cell_origin_um": [_px, 141.0],
               "from": "retained_fullchip_sg13g2_IOPadIOVss", "to": "retained_fullchip_sg13g2_IOPadVss (unmodified, as pads 2 and 5)",
               "labels_moved": _relab}
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


SHAPES = []          # (layer, DBox, net) of every top-level metal shape (self-check, router reservation)


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
        if via in ("V1", "V2", "V3", "V4"):        # small pad: one via centred (enclosure >= 0.05 checked by DRC)
            cx, cy = box.center().x, box.center().y
            (cell or top).shapes(L[via]).insert(db.DBox(cx - s / 2, cy - s / 2, cx + s / 2, cy + s / 2))
            return 1
        raise ValueError("via box too small: %s %s" % (via, box))
    nx = max(1, int((x1 - x0 + sp) // (s + sp)))
    ny = max(1, int((y1 - y0 + sp) // (s + sp)))
    ox = x0 + (x1 - x0 - (nx * s + (nx - 1) * sp)) / 2.0
    oy = y0 + (y1 - y0 - (ny * s + (ny - 1) * sp)) / 2.0
    for i in range(nx):
        for j in range(ny):
            bx = round(ox + i * (s + sp), 3)
            by = round(oy + j * (s + sp), 3)
            (cell or top).shapes(L[via]).insert(db.DBox(bx, by, bx + s, by + s))
    return nx * ny


def stack(box, la, lb, net):
    i, j = sorted((STACK.index(la), STACK.index(lb)))
    for k in range(i, j + 1):
        rect(STACK[k], box, net)
    n = {}
    for k in range(i, j):
        v = VIA_BETWEEN[(STACK[k], STACK[k + 1])]
        n[v] = via_array(v, box)
    return n


def spt(x, y, la, lb, net, h=0.25):
    """point via stack (pads 2h x 2h) between layers la and lb."""
    stack(B(x - h, y - h, x + h, y + h), la, lb, net)


def seg(layer, p, q, net, w=W):
    (x0, y0), (x1, y1) = p, q
    h = w / 2.0
    if abs(y0 - y1) < 1e-9:
        rect(layer, B(min(x0, x1) - h, y0 - h, max(x0, x1) + h, y0 + h), net)
    elif abs(x0 - x1) < 1e-9:
        rect(layer, B(x0 - h, min(y0, y1) - h, x0 + h, max(y0, y1) + h), net)
    else:
        raise ValueError("non-Manhattan segment %s %s" % (p, q))


def mpath(layer, net, pts, w=W):
    """single-layer Manhattan path (any direction)."""
    for p, q in zip(pts[:-1], pts[1:]):
        seg(layer, p, q, net, w)


def route(net, pts, w=W, lbl=True):
    """vertical segments Metal3, horizontal Metal4, Via3 at the bends (try-e convention)."""
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
    if h != EXPECT_SHA[name]:
        raise SystemExit("%s: GDS hash %s is not the layout of record %s" % (name, h, EXPECT_SHA[name]))
    MAC[name] = load_macro(name, path) + (h, path)

# Try g: r1_adc now holds PDK standard cells (SAR sub-macro) that r1_ctrl_top also holds. copy_tree gives the second
# copy a "$<n>" name; the LVS comparer would then see two different cells. Identical copies (same merged shapes per
# layer, same labels) are merged into the first cell; a copy that differs is kept and listed.
import re as _re  # noqa: E402


def _cell_sig(c):
    h = hashlib.sha256()
    for li in ly.layer_indexes():
        r = db.Region(c.begin_shapes_rec(li)).merged()
        info = ly.get_info(li)
        if not r.is_empty():
            h.update(("%d/%d:" % (info.layer, info.datatype)).encode())
            for poly in sorted(str(x) for x in r.each()):
                h.update(poly.encode())
        txt = []
        it = c.begin_shapes_rec(li)
        while not it.at_end():
            sh = it.shape()
            if sh.is_text():
                t = sh.text.transformed(it.trans())
                txt.append("%s@%d,%d" % (t.string, t.x, t.y))
            it.next()
        for t in sorted(txt):
            h.update(("%d/%d:T%s" % (info.layer, info.datatype, t)).encode())
    return h.hexdigest()


MERGED_STD = []
for _c in list(ly.each_cell()):
    _m = _re.match(r"^(sg13g2_[A-Za-z0-9_]+)\$\d+$", _c.name)
    if not _m:
        continue
    _base = ly.cell(_m.group(1))
    if _base is None or _base.cell_index() == _c.cell_index():
        continue
    if _cell_sig(_base) != _cell_sig(_c):
        MERGED_STD.append({"cell": _c.name, "merged": False, "reason": "geometry differs from %s" % _base.name})
        continue
    _n = 0
    for _pi in list(_c.each_parent_inst()):
        _pi.child_inst().cell_index = _base.cell_index()
        _n += 1
    _nm = _c.name
    ly.delete_cell(_c.cell_index())
    MERGED_STD.append({"cell": _nm, "into": _base.name, "parent_instance_arrays": _n, "merged": True})


def tr(rot, mirror, x, y):
    return db.DCplxTrans(1.0, rot, mirror, x, y)


def relsrc(path):
    if path.startswith(RES):
        return "<G1_RESULTS_ROOT>/" + os.path.relpath(path, RES)
    if path.startswith(OFR):
        return "<G1_RESULTS_ROOT>/r1_top/<run>/inputs/ofrecord/" + os.path.basename(path)
    return os.path.relpath(path, REPO)


TRY_F = {"u_ctrl": [538.8, 673.3], "u_afe": [336.0, 740.0], "u_isense": [1113.8, 735.0], "u_osc": [1088.8, 1041.8],
         "u_safe": [1088.8, 376.0], "u_bgr": [336.0, 376.0], "u_t2f": [366.8, 622.74], "u_bias": [444.0, 376.0],
         "u_gate": [440.0, 1296.0], "u_adc": [592.0, 376.0], "u_ls_t2f0": [480.25, 640.3], "u_ls_t2f1": [495.45, 640.3],
         "u_ls_afe0": [510.65, 640.3], "u_ls_afe1": [480.25, 660.3], "u_ls_afe2": [495.45, 660.3],
         "u_ls_afe3": [510.65, 660.3]}
TRY_F_SIZE = {"u_ctrl": [532.0, 679.0], "u_adc": [439.0, 182.3]}


def place(inst_name, macro, trans, orient, s7=None):
    cell, src, tc, sha, path = MAC[macro]
    top.insert(db.DCellInstArray(cell.cell_index(), trans))
    bb = tc.dbbox().transformed(trans)
    e = TRY_F.get(inst_name)
    PLACED.append({"instance": inst_name, "macro": macro, "orientation": orient,
                   "origin_um": [round(trans.disp.x, 3), round(trans.disp.y, 3)],
                   "bbox_um": [round(bb.left, 3), round(bb.bottom, 3), round(bb.right, 3), round(bb.top, 3)],
                   "size_um": [round(bb.width(), 3), round(bb.height(), 3)],
                   "source": relsrc(path), "source_sha256": sha, "s7_c4": s7, "try_f_origin_um": e,
                   "delta_vs_try_f_um": ([round(trans.disp.x - e[0], 3), round(trans.disp.y - e[1], 3)] if e else None),
                   "try_f_size_um": TRY_F_SIZE.get(inst_name)})
    return trans


PIN_CACHE = {}


def pins(macro, name, trans, layer="M3"):
    """All pin rectangles (chip coordinates) of a macro pin: the smallest shape on the pin layer (or the drawing
    layer) of `layer` that contains a label `name` in the macro top cell."""
    cell, src, tc, sha, path = MAC[macro]
    key = (macro, layer)
    if key not in PIN_CACHE:
        lt = src.find_layer(*LBL[layer])
        labs = {}
        if lt is not None:
            for s in tc.shapes(lt).each():
                if s.is_text():
                    labs.setdefault(s.text_string, []).append(db.Point(s.text.x, s.text.y))
        regs = []
        for lay in (PINP.get(layer), LY[layer]):
            li = src.find_layer(*lay) if lay else None
            regs.append(list(db.Region(tc.begin_shapes_rec(li)).merged().each()) if li is not None else [])
        PIN_CACHE[key] = (labs, regs)
    labs, regs = PIN_CACHE[key]
    pts = labs.get(name)
    if not pts:
        raise KeyError("no label %s on %s in %s" % (name, layer, macro))
    out = []
    for p in pts:
        best = None
        for reg in regs:
            for poly in reg:
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
    return min(ps, key=lambda b: (round(key(b), 3), b.area()))


# ---- placement (README "Try f"): try-e C4 positions; ctrl 0.6 box; bias revision 2 in the former t2f slot; t2f above
# the bandgap (MIM: east of the west TopMetal1 columns); isense +25 um in x for the tap-line columns.
X_CTRL, Y_CTRL = 538.8, 673.3
X_ISN, Y_ISN = 1113.8, 735.0
AFE_X, AFE_Y = 336.0, 740.0
T_CTRL = place("u_ctrl", "r1_ctrl_top", tr(0, False, X_CTRL, Y_CTRL), "R0", [543.8, 673.3])
T_AFE = place("u_afe", "r1_afe", tr(0, False, AFE_X, AFE_Y), "R0", [336.0, 720.0])
T_ISN = place("u_isense", "r1_isense", tr(0, False, X_ISN, Y_ISN), "R0", [1088.8, 735.0])
T_OSC = place("u_osc", "r1_osc", tr(0, False, 1088.8, 1041.8), "R0", [1088.8, 1041.8])
T_SAFE = place("u_safe", "r1_safe", tr(0, False, 1088.8, 376.0), "R0", [1088.8, 376.0])
T_BGR = place("u_bgr", "r1_bgr", tr(0, False, 336.0, 376.0), "R0", [336.0, 376.0])
T_BIAS = place("u_bias", "r1_bias", tr(0, False, 444.0, 376.0), "R0", [442.0, 488.6])
T_T2F = place("u_t2f", "r1_t2f", tr(0, False, 366.8, 622.74), "R0", [442.0, 376.0])
T_ADC = place("u_adc", "r1_adc", tr(0, False, 592.0, 376.0), "R0", [556.0, 376.0])
GY = 1296.0
T_GATE = place("u_gate", "r1_gate_lv", tr(0, False, 440.0, GY), "R0", [440.0, 1300.0])
# 6 x r1_ls in two rows of 3 between the bias (top 612.74) and the ctrl (bottom 673.3); origins on the router grid
# offsets (pin access nodes on the 0.8 um grid, layout/maze_router_top.py)
LS_ROWS = {"u_ls_t2f0": (480.25, 640.3), "u_ls_t2f1": (495.45, 640.3), "u_ls_afe0": (510.65, 640.3),
           "u_ls_afe1": (480.25, 660.3), "u_ls_afe2": (495.45, 660.3), "u_ls_afe3": (510.65, 660.3)}
T_LS = {}
for _n, (_x, _y) in LS_ROWS.items():
    T_LS[_n] = place(_n, "r1_ls", tr(0, False, _x, _y), "R0", None)
BB = {r["instance"]: r["bbox_um"] for r in PLACED}
log("placement", json.dumps({r["instance"]: [r["origin_um"], r["bbox_um"]] for r in PLACED}))

# ---------------------------------------------------------------- ring ECO over the AFE (MIM under the west columns)
# As try e: west TopMetal1 columns (outer VSS x 324.82-339.82, inner VDD 344.82-361.8) cut over the AFE outline
# plus 5 um; TopMetal2 strips of the column width 15 um beyond the cut; TopVia2 only in the 15 um overlaps.
_afe_bb = MAC["r1_afe"][2].dbbox()
AFE_Y0, AFE_Y1 = AFE_Y, AFE_Y + _afe_bb.height()
CUT = [321.0, AFE_Y0 - 5.0, 365.0, AFE_Y1 + 5.0]
ECO = {"cut_tm1": CUT, "tm2": [], "tv2": [], "east_columns": "no MIM block under the east columns (isense ends at "
       "x 1272.2, osc at 1237.0; column from 1340.42); no cut"}
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
SHAPES.append(("TM2", B(328.0, 327.16, 1372.0, 342.16), "VSS"))
SHAPES.append(("TM2", B(344.82, 347.16, 1355.42, 362.16), "VDD"))
SHAPES.append(("TM2", B(344.82, 1337.3, 1355.42, 1352.3), "VDD"))
SHAPES.append(("TM2", B(328.0, 1357.3, 1372.0, 1372.3), "VSS"))

# ---------------------------------------------------------------- supplies
# Ring identity (as try d/e): outer core ring = VSS, inner = VDD. VDDA from pad 7 (east) and the south trunk.
CTRL_VDD_X = [23.54, 99.14, 174.74, 250.34, 325.94, 401.54, 477.14]
CTRL_VSS_X = [29.74, 105.34, 180.94, 256.54, 332.14, 407.74, 483.34]
YT = Y_CTRL + 665.0                                  # ctrl 0.6 TopMetal1 stripes end at local 665.5 / 665.91
for lx in CTRL_VDD_X:
    x = X_CTRL + lx
    rect("TM1", B(x, YT, x + 2.2, 1352.3), "VDD")
    via_array("TV2", B(x, 1337.3, x + 2.2, 1352.3))
for lx in CTRL_VSS_X:
    x = X_CTRL + lx
    rect("TM1", B(x, YT, x + 2.2, 1397.0), "VSS")
    via_array("TV2", B(x, 1357.3, x + 2.2, 1372.3))
# Try g (run g2): south VDD feed of r1_ctrl. The extracted VDD network of run g1 (flow/supply_g_rnet.py) gives a
# 56 mV (typ) / 73 mV (max sheet) static drop at the ctrl stripes: the 40 mA of ctrl 0.8 come from pad 1 (south,
# x 495) around the ring to the north row. A TopMetal2 strap (x 566-590, in the channel between r1_bias and r1_adc,
# over no MIM block) joins the inner south VDD TopMetal2 row (y 347.16-362.16) to a TopMetal2 bar over the ctrl south
# band (y 684.0-692.0, 5.14 um below the first ctrl TopMetal2 strap at y 697.14: TM2.bR needs 5.0 um for a parallel run
# > 50 um; run g2 had the bar top at 694.0 and gave 1 TM2.bR), with TopVia2 onto the 7 ctrl VDD TopMetal1 stripes
# (they start at local y 10.71 = chip 684.01).
NO_H = bool(os.environ.get("R1H_NO_FEED"))           # 1: the try-g supply network (regression of the generator)
if not os.environ.get("R1G_NO_SFEED"):
    rect("TM2", B(566.0, 347.16, 590.0, 692.0), "VDD")
    # try h0: bar 28 um (y 664-692; try g 684-692). Top edge unchanged (5.14 um to the first ctrl TopMetal2 strap).
    rect("TM2", B(561.0, 684.0 if NO_H else 664.0, 1068.0, 692.0), "VDD")
    for lx in CTRL_VDD_X:
        x = X_CTRL + lx
        via_array("TV2", B(x, 685.0, x + 2.2, 692.0))
# North VDD straps (inner TM2 row <-> IO-row vdd Metal3 rail, y 1381-1399), east of the ctrl 0.6 box (x <= 1070.8)
N_VDD_STRAPS = [(1120.0, 1127.0), (1140.0, 1147.0), (1250.0, 1257.0)]
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
# South trunks (Metal4) under the south ring band (as try e)
TR = {"VSS": (332.0, 340.0), "VDD": (343.0, 349.0), "VDDA": (352.0, 360.0)}
rect("M4", B(371.0, 332.0, 1378.0, 340.0), "VSS")
rect("M4", B(371.0, 343.0, 1360.0, 349.0), "VDD")
rect("M4", B(322.6, 352.0, 1372.0, 360.0), "VDDA")
label("M4", 380.0, 336.0, "VSS")
label("M4", 380.0, 346.0, "VDD")
label("M4", 380.0, 356.0, "VDDA")
S_FILLERS = [535.0, 677.0, 819.0, 961.0, 1103.0]      # south IO filler gaps (62 um) of the 142 um pitch
for f0 in S_FILLERS:
    rect("M4", B(f0 + 9.0, 304.0, f0 + 39.0, 340.0), "VSS")           # IO vss Metal4 rail 303.2-319
    # try g (run g3): 10 um wide (try f: 6 um). Extracted run g2: the strap next to pad 1 carries 10.5 mA (typ) against
    # 12 mA for 6 um (EM, 2 mA/um); 10 um gives 20 mA.
    _sw = 6.0 if os.environ.get("R1G_STRAP6") else 10.0
    rect("M3", B(f0 + 2.0, 302.0, f0 + 2.0 + _sw, 349.0), "VDD")      # IO vdd Metal3 rail 301-319
    via_array("V3", B(f0 + 2.0, 343.0, f0 + 2.0 + _sw, 349.0))
# VDDA feed from pad 7 (sg13g2_IOPadAnalog `pad`, Metal3 x 1379-1379.29, y 481.105-505.875)
rect("M3", B(1366.0, 482.0, 1379.29, 505.0), "VDDA")
rect("M4", B(1366.0, 352.0, 1372.0, 505.0), "VDDA")
via_array("V3", B(1366.0, 482.0, 1372.0, 505.0))
label("M3", 1375.0, 493.0, "VDDA")
# VDDA Metal5 trunk (y 343-361, under the south ring rows) and Metal5 riser over the pad-7 Metal4 riser (x 1362-1377,
# under the east VSS column; no TopVia1 there): Via4 arrays to the Metal4 trunk / riser. Lowers the VDDA trunk
# resistance about three times (README "Try f", supply).
# Try g (run g2): the inner south VDD TopMetal2 row reached pad 1 only through the ring (run g1, extracted: 58 mV at
# the row next to pad 1 with the 40 mA of ctrl 0.8). Five VDD stacks join the Metal4 VDD trunk (fed by the IO-filler
# straps) to the inner VDD TopMetal2 row through 10 um notches in the bottom edge of this VDDA Metal5 trunk
# (Metal5 island, TopVia1, TopMetal1 pad, TopVia2), next to each IO-filler gap. Five VSS stacks join the Metal4 VSS trunk
# to the outer VSS TopMetal2 row in the same way (Metal5 is free there). Switch off: R1G_NO_SSTACK=1 (run g1 form).
SSTACK = [] if os.environ.get("R1G_NO_SSTACK") else [f0 + 10.0 for f0 in (535.0, 677.0, 819.0, 961.0, 1103.0)]
if SSTACK:
    rect("M5", B(322.6, 349.6, 1377.0, 361.0), "VDDA")                  # upper part, full length
    _xs = [322.6] + [v for _a in SSTACK for v in (_a, _a + 10.0)] + [1377.0]
    for _x0, _x1 in zip(_xs[0::2], _xs[1::2]):                           # lower part between the notches
        rect("M5", B(_x0, 343.0, _x1, 349.6), "VDDA")
else:
    rect("M5", B(322.6, 343.0, 1377.0, 361.0), "VDDA")
via_array("V4", B(322.6, 352.0, 1372.0, 360.0))
SSTACK_REC = []
for _a in SSTACK:
    _isl = B(_a + 0.6, 343.0, _a + 9.4, 349.0)
    rect("M5", _isl, "VDD")
    via_array("V4", _isl)
    via_array("TV1", _isl)
    rect("TM1", B(_a + 0.6, 343.0, _a + 9.4, 362.16), "VDD")
    via_array("TV2", B(_a + 0.6, 347.16, _a + 9.4, 362.16))
    _vs = B(_a + 14.0, 332.0, _a + 26.0, 340.0)               # VSS stack on the Metal4 VSS trunk (332-340)
    rect("M5", _vs, "VSS")
    via_array("V4", _vs)
    via_array("TV1", _vs)
    rect("TM1", B(_a + 14.0, 327.5, _a + 26.0, 341.0), "VSS")
    via_array("TV2", B(_a + 14.0, 327.5, _a + 26.0, 341.0))
    SSTACK_REC.append({"vdd_stack_um": [_a + 0.6, 343.0, _a + 9.4, 362.16], "vss_stack_um": [_a + 14.0, 327.5, _a + 26.0, 341.0]})
rect("M5", B(1362.0, 343.0, 1377.0, 505.0), "VDDA")
via_array("V4", B(1366.0, 361.0, 1372.0, 505.0))
# West VDDA riser, Metal3 9.4 um wide (x 322.6-332, under the outer west column): bgr, bias, t2f, AFE, gate_lv.
# Try e: 2 um (x 327-329); widened for the AFE 2 mA (README "Try f", supply).
rect("M3", B(322.6, 352.0, 332.0, 738.0), "VDDA")
via_array("V3", B(322.6, 352.0, 332.0, 360.0))


# ---------------------------------------------------------------- try h0 supply feed (track T8f)
# Diagnosis (try g, extracted, max sheet; reports/supply_h0.md): of the 63.6 mV VSS rise at the ctrl, 27 mV are inside
# the two IOPadVss cells (bondpad -> Metal2 plate -> rail), 20 mV in the ring path (south rows, columns, north row) and
# 16.4 mV along the ctrl VSS stripes (fed from the north end only). Of the 30.6 mV VDD drop, 6.9 mV are in the IOPadVdd
# cell, about 9 mV between the IO VDD rail and the inner VDD row (Metal3 straps, Metal4 trunk, stacks), 8 mV along the
# 8 um south bar.
FEED = {"description": "try h0 supply feed (README 'Supply feed redesign (try h preparation)')", "enabled": not NO_H,
        "shapes": [], "em_items": [], "ring_eco": {}}


def feed(layer, box, net, em=None, d=None, w=None):
    rect(layer, box, net)
    FEED["shapes"].append([layer, net, [round(box.left, 3), round(box.bottom, 3), round(box.right, 3), round(box.top, 3)]])
    if em:
        eb = em if isinstance(em, db.DBox) else box
        FEED["em_items"].append({"name": em if isinstance(em, str) else "%s %s" % (layer, net), "net": net, "layer": layer,
                                 "box": [round(eb.left, 3), round(eb.bottom, 3), round(eb.right, 3), round(eb.top, 3)],
                                 "dir": d, "width": w})


if not NO_H and RISER:
    # 1. IOPadVss riser (ring ECO, cell edit; both instances are VSS pads 2 and 5, cell origins x 597 and 1023, y 141).
    # Pattern of the PDK IOPadVdd cell of the same ring: IO TopMetal2 rails cut to stubs x 0-3.9 and 76.1-80 (pins and
    # the iovdd / iovss labels on the stubs), TopVia2 kept only under the stubs with 0.5 um enclosure, riser = bottom
    # strip 5-75 x 0-3, three 18.33 um fingers (x 7.5-25.83, 30.83-49.16, 54.17-72.5, y 3-159.5; the IOPadVdd slot
    # pattern) and a top band 7.5-72.5 x 159.5-178 with TopVia2 onto the VSS TopMetal1 rail (local y 160-178).
    _vc = ly.cell("retained_fullchip_sg13g2_IOPadVss")
    _cut = db.Region(db.Box.from_dbox(B(3.9, 3.0, 76.1, 140.0) * (1.0 / ly.dbu)))
    _stubv = db.Region(db.Box.from_dbox(B(0.0, 3.0, 3.4, 140.0) * (1.0 / ly.dbu))) + \
        db.Region(db.Box.from_dbox(B(76.6, 3.0, 80.0, 140.0) * (1.0 / ly.dbu)))
    _band = db.Region(db.Box.from_dbox(B(0.0, 3.0, 80.0, 140.0) * (1.0 / ly.dbu)))
    _tm2 = db.Region(_vc.shapes(L["TM2"]))
    _tv2 = db.Region(_vc.shapes(L["TV2"]))
    _tv2_keep = _tv2.outside(_band) + _tv2.inside(_stubv)
    FEED["ring_eco"]["iopadvss_tm2_rail_shapes_before"] = _tm2.count()
    FEED["ring_eco"]["iopadvss_tv2_removed"] = _tv2.count() - _tv2_keep.count()
    _vc.shapes(L["TM2"]).clear()
    _vc.shapes(L["TM2"]).insert(_tm2 - _cut)
    for _bx in (B(5.0, 0.0, 75.0, 3.0), B(7.5, 3.0, 25.83, 159.5), B(30.83, 3.0, 49.16, 159.5),
                B(54.17, 3.0, 72.5, 159.5), B(7.5, 159.5, 72.5, 178.0)):
        _vc.shapes(L["TM2"]).insert(_bx)
    _vc.shapes(L["TV2"]).clear()
    _vc.shapes(L["TV2"]).insert(_tv2_keep)
    FEED["ring_eco"]["iopadvss_riser_tv2"] = via_array("TV2", B(7.5, 160.0, 72.5, 178.0), cell=_vc)
    _lp = ly.layer(134, 2)
    _pins = db.Region(_vc.shapes(_lp))
    _vc.shapes(_lp).clear()
    _vc.shapes(_lp).insert((_pins - _cut))
    _ll = ly.layer(134, 25)
    _moved = []
    for _sh in list(_vc.shapes(_ll).each()):
        if _sh.is_text() and _sh.text_string in ("iovdd", "iovss"):
            _t = _sh.dtext
            _vc.shapes(_ll).erase(_sh)
            for _xl in (1.95, 78.05):
                _vc.shapes(_ll).insert(db.DText(_t.string, db.DTrans(_xl, _t.y)))
            _moved.append([_t.string, _t.y])
    FEED["ring_eco"]["iopadvss_labels_moved_to_stubs"] = _moved
    FEED["ring_eco"]["iopadvss"] = ("cell retained_fullchip_sg13g2_IOPadVss: IO TopMetal2 rails cut to stubs (IOPadVdd "
                                    "pattern), TopVia2 only under the stubs, iovdd/iovss labels moved to the stubs, "
                                    "slotted riser (3 x 18.33 um fingers) from the bondpad strip to a top band with "
                                    "TopVia2 onto the VSS TopMetal1 rail (local y 160-178)")
    for _cx in (597.0, 1023.0):
        for _f0 in (7.5, 44.5):                     # aligned to the riser top band (local x 7.5-72.5)
            feed("TM2", B(_cx + _f0, 317.0, _cx + _f0 + 28.0, 342.16), "VSS",
                 "VSS pad riser finger TopMetal2 28 um (x %.0f)" % (_cx + _f0), "v", 28.0)
if not NO_H and not RISER:
    # 1'. try h1 (D24): no cell edit. The IOPadVss cell joins its bondpad (local y 0-3) to the core vss rail only through
    # its Metal2 plate (local x 3.91-75, y 0-158): every layer Metal3-TopMetal2 carries the full-width iovss / iovdd
    # rails between them (LEF OBS Metal1-TopMetal1 y 0-178, TopMetal2 y 0-132.5), and the fillers continue the rails, so
    # no top-cell shape can bypass the plate. The only free top-cell layer over the cell is TopMetal2 above local
    # y 132.5. There, two 28 um TopMetal2 fingers per VSS pad (local y 160-201.16) take the cell's TopMetal1 vss pin
    # (local y 160-178) with TopVia2 and join it to the outer south VSS TopMetal2 row (pin access, parallel to the tabs).
    for _cx in VSS_PAD_X:
        for _f0 in (7.5, 44.5):
            feed("TM2", B(_cx + _f0, 301.0, _cx + _f0 + 28.0, 342.16), "VSS",
                 "VSS pad finger TopMetal2 28 um over the unmodified IOPadVss (x %.0f)" % (_cx + _f0), "v", 28.0)
            via_array("TV2", B(_cx + _f0, 301.0, _cx + _f0 + 28.0, 319.0))
if not NO_H:
    # 2. VDD riser at pad 1 through a gap in the outer VSS TopMetal2 row (ring cell shape)
    _gap = db.Region(db.Box.from_dbox(B(453.0, 326.0, 537.0, 343.5) * (1.0 / ly.dbu)))
    _rt = db.Region(ring.shapes(L["TM2"]))
    ring.shapes(L["TM2"]).clear()
    ring.shapes(L["TM2"]).insert(_rt - _gap)
    FEED["ring_eco"]["vss_row_gap"] = [453.0, 327.16, 537.0, 342.16]
    _i = [k for k, t in enumerate(SHAPES) if t[0] == "TM2" and t[2] == "VSS" and abs(t[1].bottom - 327.16) < 1e-6][0]
    SHAPES[_i:_i + 1] = [("TM2", B(328.0, 327.16, 453.0, 342.16), "VSS"), ("TM2", B(537.0, 327.16, 1372.0, 342.16), "VSS")]
    for _x0 in (460.0, 502.0):
        feed("TM2", B(_x0, 296.0, _x0 + 28.0, 362.16), "VDD", "VDD pad-1 riser finger TopMetal2 28 um (x %.0f)" % _x0, "v", 28.0)
    # TopMetal1 bridge under the fingers (y 323.5-341, 2 um below the VDD stack islands at 343), joined to the VSS row
    # on both sides of the gap by TopVia2 and to the VSS IO rail by the tabs below
    feed("TM1", B(425.0, 323.5, 571.0, 341.0), "VSS", "VSS bridge TopMetal1 17.5 um under the VDD riser", "h", 17.5)
    via_array("TV2", B(538.0, 327.66, 544.0, 340.6))      # west side: the TopVia2 of the tab x 425-448
    # 3. TopMetal1 tabs: VSS IO rail (TopMetal1, y 301-319) <-> outer VSS TopMetal2 row (TopVia2)
    TABS = [(400.0, 422.0), (425.0, 448.0), (640.0, 662.0), (760.0, 782.0), (900.0, 922.0), (1080.0, 1102.0),
            (1180.0, 1202.0), (1250.0, 1272.0), (1300.0, 1322.0)]
    for (_x0, _x1) in TABS:
        feed("TM1", B(_x0, 317.0, _x1, 341.0), "VSS")
        via_array("TV2", B(_x0, 327.66, _x1, 340.6))
    # existing VSS stack pads (and the bgr stack) reach down to the rail; not the pad at x 559-571 (it joins the west
    # strap x 566-590: rail + pad + strap would be 31 um wide over 40 um, Slt.c.TM1)
    for (_x0, _x1) in [(_a + 14.0, _a + 26.0) for _a in SSTACK if _a != 545.0] + [(372.0, 392.0)]:
        feed("TM1", B(_x0, 317.0, _x1, 333.0), "VSS")
    # 4. south VSS feed of r1_ctrl: TopMetal1 straps and bar, extensions onto the ctrl VSS stripes
    feed("TM1", B(566.0, 317.0, 590.0, 682.5), "VSS", "west VSS TopMetal1 strap 24 um (x 566-590)", "v", 24.0)
    FEED["em_items"][-1]["box"] = [566.0, 380.0, 590.0, 640.0]
    feed("TM1", B(1036.0, 317.0, 1064.0, 682.5), "VSS", "east VSS TopMetal1 strap 28 um (x 1036-1064)", "v", 28.0)
    FEED["em_items"][-1]["box"] = [1036.0, 380.0, 1064.0, 640.0]
    feed("TM1", B(561.0, 654.5, 1068.0, 682.5), "VSS", "VSS TopMetal1 bar 28 um (y 654.5-682.5)", "h", 28.0)
    FEED["em_items"][-1]["box"] = [592.0, 654.5, 1034.0, 682.5]
    for lx in CTRL_VSS_X:
        x = X_CTRL + lx
        feed("TM1", B(x, 682.0, x + 2.2, 684.6), "VSS", "VSS stripe south end TopMetal1 2.2 um (x %.2f)" % x, "v", 2.2)
        FEED["em_items"][-1]["box"] = [round(x, 3), 682.0, round(x + 2.2, 3), 715.0]     # cut at y 698.5 (stripe)
    # 5. second south VDD strap (TopMetal2, over the east VSS strap), inner VDD row -> bar
    feed("TM2", B(1036.0, 347.16, 1064.0, 692.0), "VDD", "east VDD TopMetal2 strap 28 um (x 1036-1064)", "v", 28.0)
    FEED["em_items"][-1]["box"] = [1036.0, 380.0, 1064.0, 640.0]
    FEED["em_items"].append({"name": "west VDD TopMetal2 strap 24 um (x 566-590, try g)", "net": "VDD", "layer": "TM2",
                             "box": [566.0, 380.0, 590.0, 640.0], "dir": "v", "width": 24.0})
    FEED["em_items"].append({"name": "VDD TopMetal2 bar 28 um (y 664-692)", "net": "VDD", "layer": "TM2",
                             "box": [592.0, 664.0, 1034.0, 692.0], "dir": "h", "width": 28.0})


def ctrl_pin(name):
    lay = "M2" if (name.startswith("adc_") or name in ("is_smp", "cur_trk", "gate_a", "gate_b", "gate_c", "cs_n", "ma_sclk",
                                                        "slo_sdo")) else "M3"
    return pin("r1_ctrl_top", name, T_CTRL, lay)


P = {}
P["bgr"] = {n: pin("r1_bgr", n, T_BGR) for n in ("vref", "pbias", "pcasc", "vdd", "vss")}
P["t2f"] = {n: pin("r1_t2f", n, T_T2F) for n in ("vref", "pbias", "pcasc", "vdd12", "fout", "en", "mode", "vdd", "vss")}
P["bias"] = {n: pin("r1_bias", n, T_BIAS) for n in ("vdda", "vdd", "vss", "pbias", "pcasc", "ib_afe_s1", "ib_afe_s2",
                                                     "ib_afe_c1", "ib_afe_c2", "ib_is_a", "ib_is_b", "ib_sf_oa",
                                                     "ib_sf_na", "ib_sf_ob", "ib_sf_nb", "ib_adc_ref", "por_n",
                                                     "vref", "vref_b")}
P["afe"] = {n: pin("r1_afe", n, T_AFE) for n in ("sinp", "sinn", "cosp", "cosn", "ib_s1", "ib_s2", "ib_c1", "ib_c2",
                                                  "souts_p", "souts_n", "soutc_p", "soutc_n", "vcm2", "c1", "c2", "c3",
                                                  "c4")}
P["afe_vss"] = sorted(pins("r1_afe", "vss", T_AFE), key=lambda b: b.left)
P["afe_vdd"] = sorted(pins("r1_afe", "vdd", T_AFE), key=lambda b: b.left)
P["isn"] = {n: pin("r1_isense", n, T_ISN, edge=e) for n, e in
            [("isa_p", "E"), ("isa_n", "E"), ("isb_p", "E"), ("isb_n", "E"), ("vref", "S"), ("ibias_a", "S"),
             ("ibias_b", "N"), ("vss", "S"), ("vdda", "S"), ("vdd", "S"), ("vcm", "S"), ("az_a", "S"), ("azh_a", "S"),
             ("az_b", "N"), ("azh_b", "N"), ("outa_p", "W"), ("outa_n", "W"), ("outb_p", "W"), ("outb_n", "W")]}
P["osc"] = {n: pin("r1_osc", n, T_OSC) for n in ("en", "trim0", "trim1", "trim2", "trim3", "trim4", "osc_clk", "vdd", "vss")}
P["safe"] = {n: pin("r1_safe", n, T_SAFE, edge=e) for n, e in
             [("vref", "W"), ("oc_a", "S"), ("neg_a", "S"), ("oc_b", "S"), ("neg_b", "S"), ("ibias_oa", "S"),
              ("ibias_na", "S"), ("ibias_ob", "S"), ("ibias_nb", "S"), ("vss", "W"), ("vdd", "W"), ("vdda", "E"),
              ("outa_p", "S"), ("outa_n", "S"), ("outb_p", "S"), ("outb_n", "S")]}
# ADC with the SAR sub-macro (B5/B6): north pins are the sub-macro's Metal2 pins (0.4 x 0.4 um), labels in CDL form
# adc_raw_a<k>; new north pin cur_trk. West, east and south pins Metal3 as before (supply pins 1.0 um).
ADC_PINS_N = (["adc_hold", "is_smp", "clk", "adc_start", "cur_trk", "adc_sel", "adc_valid_a", "adc_valid_b", "por_n"] +
              ["adc_raw_a[%d]" % k for k in range(14)] + ["adc_raw_b[%d]" % k for k in range(14)])
ADC_PINS = ["ain_sin_p", "ain_sin_n", "ain_cos_p", "ain_cos_n", "vcm2", "ibias", "ain_isa_p", "ain_isa_n",
            "ain_isb_p", "ain_isb_n", "vcm", "vdda", "vdd", "vss", "vref_in"]


def adc_label(n):
    return _re.sub(r"\[(\d+)\]", r"<\1>", n)


P["adc"] = {n: pin("r1_adc", n, T_ADC) for n in ADC_PINS}
P["adc"].update({n: pin("r1_adc", adc_label(n), T_ADC, "M2") for n in ADC_PINS_N})

# ---- macro supply hookups
# bgr: vss bar (y 376-378) <- VSS trunk through a 90 um wide Metal3 riser and a Metal4-TopMetal2 stack into the outer
# south VSS row (the isense ground path, README "Try f" supply); vdd bar (568.3-570.3) <- VDDA (Metal4 y 572-574)
# split by 2 um gaps (y 342-377) so that no part is wider than 30 um: maximal rule Slt.c.M3 (run asm-20261027-f2-fill2)
for _x0, _x1 in ((340.0, 360.0), (362.0, 382.0), (384.0, 404.0), (406.0, 430.0)):
    rect("M3", B(_x0, 342.0, _x1, 377.0), "VSS")
rect("M3", B(340.0, 333.0, 430.0, 342.0), "VSS")
via_array("V3", B(371.0, 333.0, 430.0, 340.0))
stack(B(372.0, 333.0, 392.0, 341.5), "M4", "TM2", "VSS")
rect("M4", B(322.6, 572.0, 441.75, 574.0), "VDDA")
via_array("V3", B(322.6, 572.0, 332.0, 574.0))
rect("M3", B(380.0, 569.0, 386.0, 574.0), "VDDA")
via_array("V3", B(380.0, 572.0, 386.0, 574.0))
# bias revision 2: vdda bar (top, y 609.14-611.14) <- Metal3 x 441.25-441.75 from the bgr VDDA rail;
# vss bar (376-378) <- 108 um wide Metal3 riser from the VSS trunk; vdd (east pin y 424.74) <- VDD riser x 569.5-571.
rect("M3", B(441.25, 572.0, 441.75, 611.14), "VDDA")
via_array("V3", B(441.25, 572.0, 441.75, 574.0))
bv = P["bias"]["vdda"]
rect("M3", B(441.25, bv.bottom, 444.5, bv.top), "VDDA")
# 84 um wide body up to y 374 and 6 um fingers into the bar (a wide plate on the bar made the bar "wide": M3.f
# against bias-internal Metal3 0.3 um above the bar, run asm-20261027-f)
# split by 2 um gaps (y 342-374) for Slt.c.M3 (max 30 um without slit); ends 3 um west of the IO-filler VDD strap x 537
for _x0, _x1 in ((450.0, 470.0), (472.0, 491.0), (493.0, 512.0), (514.0, 534.0)):
    rect("M3", B(_x0, 342.0, _x1, 374.0), "VSS")
rect("M3", B(450.0, 333.0, 534.0, 342.0), "VSS")
via_array("V3", B(450.0, 333.0, 534.0, 340.0))
for _fx in (452.0, 466.0, 480.0, 494.0, 508.0, 522.0):
    rect("M3", B(_fx, 373.0, _fx + 6.0, 377.0), "VSS")
rect("M3", B(569.5, 343.0, 571.0, 662.0), "VDD")                     # VDD riser (also the ls / t2f VDD source)
via_array("V3", B(569.5, 343.0, 571.0, 349.0))
rect("M3", B(567.5, 333.0, 569.0, 662.0), "VSS")                     # VSS riser (VREF_B shields, ls VSS source)
via_array("V3", B(567.5, 333.0, 569.0, 340.0))
pv = P["bias"]["vdd"]
yc = pv.center().y
rect("M3", B(pv.left, pv.bottom, 565.45, pv.top), "VDD")
rect("M3", B(564.95, yc - 0.25, 565.45, yc + 0.25), "VDD")
v3(565.2, yc)
rect("M4", B(564.95, yc - 0.25, 570.5, yc + 0.25), "VDD")
v3(570.25, yc)
# t2f (R0 above the bgr): vss bar (622.74-625.34) <- outer west VSS column (TopMetal1-Metal4 stack y 617.5-621.5,
# Metal4 y 618-621, Metal3 x 368-372); vdd (VDDA) bar (722.74-725.34) <- AFE VDDA rail (Metal3 x 369-373)
stack(B(325.5, 617.5, 339.5, 621.5), "M4", "TM1", "VSS")
rect("M4", B(325.5, 618.0, 372.0, 621.0), "VSS")
rect("M3", B(368.0, 618.0, 372.0, 623.6), "VSS")
via_array("V3", B(368.0, 618.0, 372.0, 621.0))
rect("M3", B(369.0, 724.0, 373.0, 738.0), "VDDA")
via_array("V3", B(369.0, 736.0, 373.0, 738.0))
# ADC layout A: south pins 0.4 x 1 um (vdda x 642, vdd 692, vss 742): 2 um Metal3 risers from the trunks, 0.4 um neck
for nm, xc, (t0, t1), net in [("vdda", 642.0, TR["VDDA"], "VDDA"), ("vdd", 692.0, TR["VDD"], "VDD"),
                              ("vss", 742.0, TR["VSS"], "VSS")]:
    pa = P["adc"][nm]
    rect("M3", B(xc - 1.0, t0 + 1.0, xc + 1.0, 375.6), net)
    rect("M3", B(pa.left, 375.4, pa.right, pa.top), net)
    via_array("V3", B(xc - 1.0, t0 + 1.0, xc + 1.0, t1))
# safe: vdda east pin -> VDDA feed (Metal4 at the pin, to the riser x 1366-1372); vss / vdd west pins -> trunks
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
# AFE: vss pins <- outer west column (stack Metal4-TopMetal1 y 729.5-733.5, Metal4 y 731-733);
#      vdd (VDDA) pins <- west VDDA riser (Metal4 y 736-738)
stack(B(325.5, 729.5, 339.5, 733.5), "M4", "TM1", "VSS")
rect("M4", B(325.5, 731.0, P["afe_vss"][-1].right + 0.5, 733.0), "VSS")
for pb in P["afe_vss"]:
    rect("M3", B(pb.left, 731.0, pb.right, pb.top), "VSS")
    via_array("V3", B(pb.left, 731.0, pb.right, 733.0))             # try g: full pin width (1.0 um pins, EM)
rect("M4", B(322.6, 735.6, P["afe_vdd"][-1].right + 0.5, 738.4), "VDDA")       # 2.8 um (AFE 2 mA)
via_array("V3", B(322.6, 735.6, 332.0, 738.0))                          # Metal3 riser ends at y 738 (V3.c1, run -f2-fill2)
for pb in P["afe_vdd"]:
    rect("M3", B(pb.left, 736.0, pb.right, pb.top), "VDDA")
    via_array("V3", B(pb.left, 736.0, pb.right, 738.0))             # try g: full pin width (1.0 um pins, EM)
# try h1 (track T8g): AFE VDDA TopMetal1 strap over the 2.8 um Metal4 rail (extracted h1-dev1, max sheet: 16 mV of the
# 57 mV AFE VDDA drop are on the rail between the west riser and the AFE pins). TopMetal1 x 368-522, y 727-738 in the
# channel between r1_t2f (top 725.34) and r1_afe (bottom 740), no MIM block under it, 6.2 um from the inner west VDD
# column; Metal5 islands with Via4 / TopVia1 onto the rail between the AFE Metal5 lines (x 354.15, 365.35, 475.75,
# 486.95). Switch off: R1H_NO_VDDA_STRAP=1.
if not NO_H and not os.environ.get("R1H_NO_VDDA_STRAP"):
    feed("TM1", B(368.0, 727.0, 522.0, 738.0), "VDDA", "AFE VDDA TopMetal1 strap 11 um (x 368-522)", "h", 11.0)
    FEED["em_items"][-1]["box"] = [380.0, 727.0, 460.0, 738.0]
    FEED["vdda_vias"] = []
    for (_x0, _x1) in ((366.9, 474.7), (488.5, 521.8)):
        _isl = B(_x0, 735.6, _x1, 738.4)
        rect("M5", _isl, "VDDA")
        _n4 = via_array("V4", _isl)
        _n1 = via_array("TV1", B(max(_x0, 368.0), 735.6, _x1, 738.0))
        FEED["vdda_vias"].append({"name": "AFE VDDA strap Via4 (x %.1f-%.1f)" % (_x0, _x1), "via": "V4", "cuts": _n4, "I_mA": 2.0})
        FEED["vdda_vias"].append({"name": "AFE VDDA strap TopVia1 (x %.1f-%.1f)" % (_x0, _x1), "via": "TV1", "cuts": _n1, "I_mA": 2.0})
# isense: vss <- Metal3-Metal5 stack (y 705-734.5) + Metal5 plate (x 1121.5-1376, y 705-734) + TopMetal1 plate
# (x 1121.5-1338.7, y 705-731) -> outer east VSS column (TopVia1 at x 1361-1375): shared ground path to the bgr
# (README "Try f" supply, <= 2.3 ohm); vdd <- inner east column (Metal4 y 729-731); vdda <- riser x 1366-1370
pb = P["isn"]["vss"]
rect("M3", B(pb.left, 705.0, pb.right, pb.top), "VSS")
stack(B(pb.left, 705.0, pb.right, 734.5), "M3", "M5", "VSS")
rect("M5", B(1121.5, 705.0, 1376.0, 726.0), "VSS")
rect("TM1", B(1121.5, 705.0, 1338.7, 731.0), "VSS")
via_array("TV1", B(1121.5, 705.0, 1338.7, 726.0))
via_array("TV1", B(1361.0, 705.0, 1375.0, 726.0))
pb = P["isn"]["vdd"]
stack(B(1341.0, 728.6, 1354.5, 730.6), "M4", "TM1", "VDD")
rect("M4", B(pb.left, 728.6, 1354.5, 730.6), "VDD")
rect("M3", B(pb.left, 728.6, pb.right, pb.top), "VDD")
via_array("V3", B(pb.left, 728.6, pb.right, 730.6))
pb = P["isn"]["vdda"]
rect("M3", B(1366.0, 505.0, 1370.0, 734.0), "VDDA")
via_array("V3", B(1366.0, 732.0, 1370.0, 734.0))
rect("M4", B(pb.left, 732.0, 1370.0, 734.0), "VDDA")
rect("M3", B(pb.left, 732.0, pb.right, pb.top), "VDDA")
via_array("V3", B(pb.left, 732.0, pb.right, 734.0))
# osc: vss bar -> outer east column (Metal4 at the bar height); vdd bar -> inner east column (as try e)
for nm, cx0, cx1, net in [("vss", 1361.0, 1374.5, "VSS"), ("vdd", 1341.0, 1354.5, "VDD")]:
    pb = P["osc"][nm]
    rect("M3", B(pb.right - 0.5, pb.bottom, 1246.5, pb.top), net)
    via_array("V3", B(1244.5, pb.bottom, 1246.5, pb.top))
    rect("M4", B(1244.5, pb.bottom, cx1, pb.top), net)
    stack(B(cx0, pb.bottom, cx1, pb.top), "M4", "TM1", net)
# osc en held high through a sg13g2_tiehi (try e2 F-fix), mirrored (MX) in the 10 um gap between r1_isense (top
# 1031.8) and r1_osc (bottom 1041.8). Try f: the VDD rail feeds from the inner east column (Metal4 y 1035.9-1036.5),
# not from a riser at x 1086 (that riser would cross the straight oscillator lines).
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
rect("M1", B(TX + 1.5, t_vdd.bottom, TX + 3.6, t_vdd.top), "VDD")
stack(B(TX + 2.9, t_vdd.bottom, TX + 3.6, t_vdd.top), "M1", "M4", "VDD")
rect("M4", B(TX + 2.9, t_vdd.bottom - 0.08, 1354.5, t_vdd.top + 0.08), "VDD")
stack(B(1341.0, 1034.5, 1354.5, 1038.0), "M4", "TM1", "VDD")
ylh = round((t_lhi.bottom + t_lhi.top) / 2.0, 2)
rect("M1", B(TX + 1.3, ylh - 0.25, TX + 2.4, ylh + 0.25), "OSC_EN")
stack(B(TX + 1.6, ylh - 0.25, TX + 2.4, ylh + 0.25), "M1", "M4", "OSC_EN")
TIE_CELL = {"instance": "u_tie_osc", "cell": "sg13g2_tiehi", "orientation": "MX", "origin_um": [TX, TY],
            "bbox_um": [round(v, 3) for v in (lambda b: (b.left, b.bottom, b.right, b.top))(TIE.dbbox().transformed(TT))],
            "cell_source": "from r1_ctrl_top (PDK library cell)"}
# gate_lv: vdd and gate_en from the inner west column (VDD), vss from the outer column (stack moved to x 330-339.5,
# east of the VDDA Metal5 riser), vdda from the AFE VDDA rail (Metal5 riser x 327.5-328.5, Metal4 y 1326-1327)
rect("M3", B(437.6, GY + 14.08, 440.4, GY + 14.58), "VDD")
rect("M3", B(437.6, GY + 16.45, 440.4, GY + 16.95), "VDD")
rect("M2", B(437.75, GY + 14.0, 438.15, GY + 17.05), "VDD")
via_array("V2", B(437.75, GY + 14.08, 438.15, GY + 14.58 + 0.06))
via_array("V2", B(437.75, GY + 16.45 - 0.06, 438.15, GY + 16.95))
rect("M4", B(346.0, GY + 14.08, 439.0, GY + 14.58), "VDD")
via_array("V3", B(438.0, GY + 14.08, 439.0, GY + 14.58))
stack(B(346.0, GY + 12.5, 360.0, GY + 16.0), "M4", "TM1", "VDD")
rect("M3", B(436.0, GY + 1.5, 440.4, GY + 4.5), "VSS")
rect("M4", B(330.0, GY + 1.5, 439.5, GY + 4.5), "VSS")
via_array("V3", B(436.0, GY + 1.5, 439.5, GY + 4.5))
stack(B(330.0, GY + 0.5, 339.5, GY + 5.5), "M4", "TM1", "VSS")
pg = pin("r1_gate_lv", "vdda", T_GATE)
rect("M5", B(327.5, 736.0, 328.5, 1327.0), "VDDA")
via_array("V4", B(327.5, 736.0, 328.5, 738.0))
rect("M4", B(327.5, 1326.0, 454.7, 1327.0), "VDDA")
via_array("V4", B(327.5, 1326.0, 328.5, 1327.0))
rect("M3", B(453.7, pg.bottom, 454.7, 1327.0), "VDDA")
WHITELIST = [("u_gate", B(453.7, pg.bottom, 454.7, pg.top))]          # landing on the gate_lv vdda bar (pin)
via_array("V3", B(453.7, 1326.0, 454.7, 1327.0))

# ---------------------------------------------------------------- hand-routed signals
NETS = {}


def note(net, src, dst, layers, state="routed", how="hand"):
    NETS[net] = {"source": src, "destinations": dst, "metal": layers, "state": state, "route": how}


def pad_west(net, y):
    rect("M3", B(320.71, y - 0.25, 323.5, y + 0.25), net)
    v3(323.25, y)


def pad_east(net, y):
    rect("M3", B(1376.5, y - 0.25, 1379.29, y + 0.25), net)
    v3(1376.75, y)


def land(net, pb, xv, side):
    yc = pb.center().y
    v3(xv, yc, net)
    h = min(0.25, pb.height() / 2.0)
    if side == "W":
        rect("M3", B(xv - 0.25, yc - h, pb.right, yc + h), net)
    else:
        rect("M3", B(pb.left, yc - h, xv + 0.25, yc + h), net)


def north_up(net, name):
    """ctrl north pin (Metal2 at y 1351.9-1352.3) -> Via2 just above the macro edge -> Metal3 stub."""
    pb = ctrl_pin(name)
    xc = pb.center().x
    yt = Y_CTRL + 679.0
    rect("M2", B(pb.left, pb.bottom, pb.right, yt + 1.2), net)
    rect("M3", B(xc - 0.25, yt + 0.4, xc + 0.25, yt + 1.2), net)
    via_array("V2", B(pb.left, yt + 0.4, pb.right, yt + 1.2))
    return xc, yt + 0.8


def mstack(x, y, net, la="M3", lb="M5", hx=0.25, hy=0.25):
    return stack(B(x - hx, y - hy, x + hx, y + hy), la, lb, net)


# --- encoder inputs: west analog pads 21-24 (`pad`) -> AFE west pins (as try e)
for net, pname in [("SIN_P", "sinp"), ("COS_P", "cosp")]:
    pb = P["afe"][pname]
    rect("M3", B(320.71, pb.bottom, pb.right, pb.top), net)
    label("M3", 328.0, pb.center().y, net)
    note(net, "pad %s (`pad`)" % net, ["u_afe/%s" % pname], "M3 (straight)")
for net, pname, ypad in [("SIN_N", "sinn", 919.49), ("COS_N", "cosn", 1203.49)]:
    pb = P["afe"][pname]
    pad_west(net, ypad)
    route(net, [(323.25, ypad), (330.5, ypad), (330.5, pb.center().y), (335.25, pb.center().y)])
    land(net, pb, 335.25, "W")
    note(net, "pad %s (`pad`)" % net, ["u_afe/%s" % pname], "M3, M4")
# --- current-sense inputs: east analog pads 8-11 (`pad`) -> isense east pins (isense +25 um in x)
for net, pname in [("ISA_N", "isa_n"), ("ISB_P", "isb_p")]:
    pb = P["isn"][pname]
    yc = pb.center().y
    rect("M3", B(pb.left, yc - 0.25, 1379.29, yc + 0.25), net)
    label("M3", 1300.0, yc, net)
    note(net, "pad %s (`pad`)" % net, ["u_isense/%s" % pname], "M3 (straight)")
for net, pname, ypad, xv in [("ISA_P", "isa_p", 635.49, 1345.0), ("ISB_N", "isb_n", 1061.49, 1300.0)]:
    pb = P["isn"][pname]
    pad_east(net, ypad)
    route(net, [(1376.75, ypad), (xv, ypad), (xv, pb.center().y), (1273.0, pb.center().y)])
    land(net, pb, 1273.0, "E")
    note(net, "pad %s (`pad`)" % net, ["u_isense/%s" % pname], "M3, M4")
# --- FAULT_N: ctrl east pin -> straight Metal3 at y 1204.6 -> pad 12 c2p (window y 1203.14-1206.86)
pb = ctrl_pin("fault_n")
yc = pb.center().y
rect("M3", B(pb.left + 0.1, yc - 0.2, 1379.29, yc + 0.2), "FAULT_N_C2P")
label("M3", 1200.0, yc, "FAULT_N_C2P")
note("FAULT_N_C2P", "u_ctrl/fault_n", ["pad 12 FAULT_N c2p"], "M3 (straight)")
# --- oscillator: ctrl clk / osc_trim[4:0] face the osc west pins (revision 2): straight Metal3 lines at the osc pin
# heights (0.3 um, 0.8 um pitch) overlapping the ctrl pins (0.84 um pitch)
OSC_LINE = {}
for net, cname, oname in ([("OSC_CLK", "clk", "osc_clk")] +
                          [("OSC_TRIM_%d" % k, "osc_trim[%d]" % k, "trim%d" % k) for k in range(5)]):
    pc, po = ctrl_pin(cname), P["osc"][oname]
    yo = po.center().y
    if net == "OSC_CLK":
        yo = 1062.8                                   # on the router grid (branch to the ADC clk)
    if not (pc.bottom < yo + 0.15 and yo - 0.15 < pc.top and po.bottom < yo + 0.15 and yo - 0.15 < po.top):
        raise SystemExit("osc line %s does not overlap both pins" % net)
    rect("M3", B(pc.left + 0.1, yo - 0.15, po.left + 1.2, yo + 0.15), net)
    label("M3", 1080.0, yo, net)
    OSC_LINE[net] = yo
    note(net, "u_ctrl/%s" % cname if net != "OSC_CLK" else "u_osc/osc_clk",
         ["u_osc/%s" % oname] if net != "OSC_CLK" else ["u_ctrl/clk", "u_adc/clk (maze branch)"], "M3 (straight)")
# --- OSC_EN: tie L_HI -> Metal4 west to x 1084 -> Metal4 north -> Via3 -> Metal3 into the osc en pin
pe = P["osc"]["en"]
ye = pe.center().y
mpath("M4", "OSC_EN", [(TX + 2.0, ylh), (1084.0, ylh), (1084.0, ye)], w=0.3)
stack(B(1083.85, ye - 0.15, 1084.15, ye + 0.15), "M3", "M4", "OSC_EN")
rect("M3", B(1083.85, ye - 0.15, pe.left + 1.2, ye + 0.15), "OSC_EN")
note("OSC_EN", "u_tie_osc/L_HI (sg13g2_tiehi)", ["u_osc/en"], "M1 pad, M4, M3")
# --- north: ctrl <-> pads 16-18; ctrl gate_a/b/c -> gate_lv; gate_lv -> pads 13-15
for net, name, xpad, ylev in [("CS_N_P2C", "cs_n", 920.975, 1368.0), ("MA_SCLK_P2C", "ma_sclk", 1062.975, 1370.5),
                              ("SLO_SDO_C2P", "slo_sdo", 1205.0, 1373.0)]:
    xc, yb = north_up(net, name)
    route(net, [(xc, yb), (xc, ylev), (xpad, ylev), (xpad, 1379.04)])
    note(net, ("pad %s p2c" % net[:-4]) if net.endswith("P2C") else "u_ctrl/slo_sdo",
         ["u_ctrl/%s" % name] if net.endswith("P2C") else ["pad 18 SLO_SDO c2p"], "M2 stub, M3, M4")
for net, name, tx, pname, ylev in [("PWM_A", "gate_a", 432.0, "pwm_a", 1374.0), ("PWM_B", "gate_b", 434.0, "pwm_b", 1375.0),
                                   ("PWM_C", "gate_c", 436.0, "pwm_c", 1376.0)]:
    py = pin("r1_gate_lv", pname, T_GATE).center().y
    xc, yb = north_up(net, name)
    route(net, [(xc, yb), (xc, ylev), (tx, ylev), (tx, py)])
    rect("M3", B(tx - 0.25, py - 0.25, 441.0, py + 0.25), net)
    note(net, "u_ctrl/%s" % name, ["u_gate/%s" % pname], "M2 stub, M3, M4")
for net, pnm, tx, ylev, xpad in [("GATE_A_C2P", "gc_a", 474.0, 1356.0, 494.99),
                                 ("GATE_C_C2P", "gc_c", 472.0, 1361.0, 778.99),
                                 ("GATE_B_C2P", "gc_b", 470.0, 1358.5, 636.99)]:
    py = pin("r1_gate_lv", pnm, T_GATE).center().y
    rect("M3", B(467.4, py - 0.25, tx + 0.25, py + 0.25), net)
    route(net, [(tx, py), (tx, ylev), (xpad, ylev), (xpad, 1379.04)])
    note(net, "u_gate/%s" % pnm, ["pad %s c2p (sg13g2_IOPadOut30mA; its own 1.2->3.3 V shifter)" % net[:6]], "M3, M4")

# --- safe tap lines (64): two-layer crossbar between the ctrl east pins (y 681-787, 1.68 um pitch) and the safe top
# pins (0.665 / 5.235 um pitches). Rank r by ctrl pin height: Metal3 column x_c(r) = 1075.6 + 0.54 r (y_k .. y_p),
# Metal4 row y_k(r) = 665.4 + 0.6 r (x_c .. safe pin), Metal3 riser at the safe pin, Metal3 neck at y_p into the
# ctrl pin. Necks only cross columns of lower ranks below their tops: no crossing on one layer.
GRP = ["oa", "na", "ob", "nb"]
TAPS = []
for pol in ("p", "n"):
    for t in range(32):
        i, b = divmod(t, 8)
        TAPS.append(("TAP_%s_%d" % (pol.upper(), t), "tap_%s[%d]" % (pol, t), "%s_%s%d" % (GRP[i], pol, b)))
for net, cname, sname in TAPS:
    P.setdefault("safe_taps", {})[sname] = pin("r1_safe", sname, T_SAFE)
TAPS.sort(key=lambda r: ctrl_pin(r[1]).center().y)
XBAR = []
for r, (net, cname, sname) in enumerate(TAPS):
    pc = ctrl_pin(cname)
    ps = P["safe_taps"][sname]
    yp, xs = round(pc.center().y, 3), round(ps.center().x, 3)
    xcol, yk = round(1075.6 + 0.54 * r, 3), round(665.4 + 0.6 * r, 3)
    h = 0.15
    rect("M3", B(pc.left + 0.1, yp - h, xcol + h, yp + h), net)               # neck into the ctrl pin
    rect("M3", B(xcol - h, yk - h, xcol + h, yp + h), net)                     # column
    via_array("V3", B(xcol - h, yk - h, xcol + h, yk + h))
    rect("M4", B(xcol - h, yk - h, xs + h, yk + h), net)                       # row
    via_array("V3", B(xs - h, yk - h, xs + h, yk + h))
    rect("M3", B(xs - h, ps.bottom + 0.05, xs + h, yk + h), net)               # riser into the safe pin
    label("M4", (xcol + xs) / 2.0, yk, net)
    XBAR.append({"net": net, "ctrl_pin": cname, "safe_pin": sname, "rank": r, "y_ctrl": yp, "x_col": xcol, "y_row": yk,
                 "x_safe": xs})
    note(net, "u_ctrl/%s" % cname, ["u_safe/%s" % sname], "M3, M4 (crossbar rank %d)" % r)

# --- VREF_BG (raw bandgap): bgr vref (west pin) -> Metal4 x 334.8 -> Metal5 1 um at y 368 (VSS Metal5 shields at
# y 365.5 and 370.5) -> ADC vref_in (Metal3 riser x 992); branch Metal4 x 438 -> bias revision 2 vref (buffer input)
pb = P["bgr"]["vref"]
yb = pb.center().y
rect("M3", B(334.55, pb.bottom, pb.left + 1.0, pb.top), "VREF_BG")
mstack(334.8, yb, "VREF_BG", "M3", "M4")
rect("M4", B(334.55, 367.5, 335.05, yb + 0.25), "VREF_BG")
stack(B(334.55, 367.5, 335.05, 368.5), "M4", "M5", "VREF_BG")
rect("M5", B(334.55, 367.5, 992.5, 368.5), "VREF_BG")
label("M5", 600.0, 368.0, "VREF_BG")
pa = P["adc"]["vref_in"]
stack(B(991.75, 367.5, 992.25, 368.5), "M3", "M5", "VREF_BG")
rect("M3", B(pa.left, 367.5, pa.right, pa.top), "VREF_BG")
stack(B(437.75, 367.5, 438.25, 368.5), "M4", "M5", "VREF_BG")
pv = P["bias"]["vref"]
yv = pv.center().y
rect("M4", B(437.75, 367.5, 438.25, yv + 0.25), "VREF_BG")
mstack(438.0, yv, "VREF_BG", "M3", "M4")
rect("M3", B(437.75, pv.bottom, pv.left + 1.0, pv.top), "VREF_BG")
for ys in (365.5, 370.5):
    rect("M5", B(337.0, ys - 0.5, 995.0, ys + 0.5), "VSS")
    for x0, x1 in [(341.0, 345.0), (452.0, 456.0), (741.0, 743.0)]:
        stack(B(x0, ys - 0.5, x1, ys + 0.5), "M3", "M5", "VSS")
note("VREF_BG", "u_bgr/vref", ["u_adc/vref_in", "u_bias/vref"], "M3, M4, M5 (1 um, VSS Metal5 shields both sides)")

# --- VREF_B (bias revision 2 buffer output): east pin -> Metal4 1 um x 566 (VSS Metal4 shield x 568, VSS Metal3
# riser under it) -> Metal5 2 um at y 645 (VSS Metal5 shields y 642 / 648) -> Metal4 hop over the isense lines
# (x 1034-1050) -> Metal5 x 1068 -> safe vref (y 622.95) and isense vref (Metal5 y 696, x 1116.2); t2f branch
# by the maze router from the Metal4 riser.
pb = P["bias"]["vref_b"]
yb = pb.center().y
rect("M3", B(pb.left + 0.5, pb.bottom, 566.25, pb.top), "VREF_B")
mstack(566.0, yb, "VREF_B", "M3", "M4")
rect("M4", B(565.5, yb - 0.5, 566.5, 646.0), "VREF_B")
via_array("V4", B(565.5, 644.0, 566.5, 646.0))
rect("M5", B(565.5, 644.0, 1036.0, 646.0), "VREF_B")
label("M5", 800.0, 645.0, "VREF_B")
rect("M4", B(567.5, 521.0, 568.5, 640.0), "VSS")
via_array("V3", B(567.5, 521.0, 568.5, 640.0))
for ys in (642.0, 648.0):
    rect("M5", B(567.5, ys - 0.5, 1035.0, ys + 0.5), "VSS")
    stack(B(567.5, ys - 0.5, 569.0, ys + 0.5), "M3", "M5", "VSS")
via_array("V4", B(1034.0, 644.5, 1036.0, 645.5))
rect("M4", B(1034.0, 644.5, 1050.0, 645.5), "VREF_B")
via_array("V4", B(1048.0, 644.5, 1050.0, 645.5))
rect("M5", B(1048.0, 644.0, 1081.0, 646.0), "VREF_B")
rect("M5", B(1079.0, 622.45, 1081.0, 646.0), "VREF_B")
ps = P["safe"]["vref"]
ysv = ps.center().y
rect("M5", B(1079.0, ysv - 0.25, 1086.75, ysv + 0.25), "VREF_B")
stack(B(1086.25, ysv - 0.25, 1086.75, ysv + 0.25), "M3", "M5", "VREF_B")
rect("M3", B(1086.25, ps.bottom, ps.left + 1.0, ps.top), "VREF_B")
pi = P["isn"]["vref"]
xi = pi.center().x
rect("M5", B(1079.0, 644.5, xi + 0.25, 645.5), "VREF_B")             # over r1_safe (no Metal5 in the safe)
rect("M5", B(xi - 0.25, 644.5, xi + 0.25, 733.7), "VREF_B")
stack(B(xi - 0.15, 732.9, xi + 0.15, 733.7), "M3", "M5", "VREF_B")
rect("M3", B(xi - 0.15, 732.9, xi + 0.15, pi.top), "VREF_B")
note("VREF_B", "u_bias/vref_b", ["u_safe/vref", "u_isense/vref", "u_t2f/vref (maze branch)"],
     "M3, M4 (1 um), M5 (2 um), VSS shields on the Metal4 riser and the Metal5 run")

# --- AFE outputs -> ADC west inputs: Metal5 0.5 um, 1 um pitch, around the bias (MIM) and under nothing else
def pair_stack(x, y, net, pin_box=None, down=True):
    stack(B(x - 0.25, y - 0.25, x + 0.25, y + 0.25), "M3", "M5", net)


AFE_RT = [("AFE_SOUTS_P", "souts_p", "ain_sin_p", 615.0, 577.0), ("AFE_SOUTS_N", "souts_n", "ain_sin_n", 616.0, 578.0),
          ("AFE_SOUTC_P", "soutc_p", "ain_cos_p", 618.0, 582.0), ("AFE_SOUTC_N", "soutc_n", "ain_cos_n", 619.0, 583.0)]
for net, apin, dpin, yh, xv in AFE_RT:
    pa, pd = P["afe"][apin], P["adc"][dpin]
    xa, yd = pa.center().x, pd.center().y
    stack(B(xa - 0.25, 739.0, xa + 0.25, 739.6), "M3", "M5", net)
    rect("M3", B(pa.left, 739.0, pa.right, pa.top), net)
    mpath("M5", net, [(xa, 739.3), (xa, yh), (xv, yh), (xv, yd), (589.5, yd)])
    stack(B(589.25, yd - 0.25, 589.75, yd + 0.25), "M3", "M5", net)
    rect("M3", B(589.25, pd.bottom, pd.left + 0.6, pd.top), net)
    label("M5", xa, 700.0, net)
    note(net, "u_afe/%s" % apin, ["u_adc/%s" % dpin], "M3, M4 stacks, M5 0.5 um")

# --- isense outputs -> ADC east inputs and safe bottom inputs: Metal5 0.5 um, 1 um pitch
ISN_RT = [("ISN_OUTA_P", "outa_p", "ain_isa_p", 1110.5, 667.0, 1044.0, 368.0),     # y_h between the safe top
          ("ISN_OUTA_N", "outa_n", "ain_isa_n", 1109.5, 668.0, 1043.0, 367.0),     # (663.81) and the ctrl
          ("ISN_OUTB_P", "outb_p", "ain_isb_p", 1108.5, 669.0, 1042.0, 366.0),     # bottom (673.3)
          ("ISN_OUTB_N", "outb_n", "ain_isb_n", 1107.5, 670.0, 1041.0, 365.0)]
for net, ipin, dpin, xc, yh, xse, ys in ISN_RT:
    pi, pd, ps = P["isn"][ipin], P["adc"][dpin], P["safe"][ipin]
    yi, yd, xs = pi.center().y, pd.center().y, ps.center().x
    rect("M3", B(1112.05, pi.bottom, pi.left + 0.5, pi.top), net)
    stack(B(1112.05, yi - 0.25, 1112.55, yi + 0.25), "M3", "M5", net)
    mpath("M5", net, [(1112.3, yi), (xc, yi), (xc, yh), (xse, yh), (xse, ys), (xs, ys), (xs, 373.5)])
    stack(B(xse - 0.25, yd - 0.25, xse + 0.25, yd + 0.25), "M4", "M5", net)
    rect("M4", B(1031.75, yd - 0.25, xse + 0.25, yd + 0.25), net)
    mstack(1032.0, yd, net, "M3", "M4")
    rect("M3", B(pd.right - 0.5, pd.bottom, 1032.25, pd.top), net)
    stack(B(xs - 0.25, 373.25, xs + 0.25, 373.75), "M3", "M5", net)
    rect("M3", B(ps.left, 373.25, ps.right, ps.top), net)
    label("M5", xse, 600.0, net)
    note(net, "u_isense/%s" % ipin, ["u_adc/%s" % dpin, "u_safe/%s" % ipin], "M3, M4 stacks, M5 0.5 um")

# ---------------------------------------------------------------- level shifters: hand pin landings (Metal3 nodes)
# local offsets: in (0.75, 4.9) V2 on the in pin; out (8.75, 4.9) V1+V2; vss (3.15, 0.1) V1 at (3.15, 0.575);
# vdd (1.55, 10.5) V1 at (1.55, 10.0); vdda (6.35, 11.3) V1 at (6.35, 11.4). Metal2 pads drawn here.
LS_NODE = {}
for n, (x, y) in LS_ROWS.items():
    nd = {}

    def lpad(x0, y0, x1, y1, net):
        rect("M2", B(x + x0, y + y0, x + x1, y + y1), net)

    def lvia(v, cx, cy):
        top.shapes(L[v]).insert(B(x + cx - 0.095, y + cy - 0.095, x + cx + 0.095, y + cy + 0.095))

    net_i, net_o = "%s__in" % n, "%s__out" % n            # renamed to the real nets below
    nd["in"] = (x + 0.75, y + 4.9)
    lpad(0.5, 4.65, 1.0, 5.15, net_i)
    lvia("V2", 0.75, 4.9)
    nd["out"] = (x + 8.75, y + 4.9)
    rect("M1", B(x + 8.5, y + 4.65, x + 9.0, y + 5.15), net_o)
    lpad(8.5, 4.65, 9.0, 5.15, net_o)
    lvia("V1", 8.75, 4.9)
    lvia("V2", 8.75, 4.9)
    nd["vss"] = (x + 3.15, y + 0.1)
    lpad(2.9, -0.15, 3.4, 0.85, "VSS")
    lvia("V1", 3.15, 0.575)
    lvia("V2", 3.15, 0.1)
    nd["vdd"] = (x + 1.55, y + 10.5)
    lpad(1.3, 9.75, 1.8, 10.75, "VDD")
    lvia("V1", 1.55, 10.0)
    lvia("V2", 1.55, 10.5)
    nd["vdda"] = (x + 6.35, y + 11.3)
    lpad(6.1, 11.05, 6.6, 11.65, "VDDA")
    lvia("V1", 6.35, 11.4)
    lvia("V2", 6.35, 11.3)
    LS_NODE[n] = nd
LS_NET = {"u_ls_t2f0": ("T2F_EN", "T2F_EN_HV"), "u_ls_t2f1": ("T2F_MODE", "T2F_MODE_HV"),
          "u_ls_afe0": ("PGA_C0", "PGA_C0_HV"), "u_ls_afe1": ("PGA_C1", "PGA_C1_HV"),
          "u_ls_afe2": ("PGA_C2", "PGA_C2_HV"), "u_ls_afe3": ("PGA_C3", "PGA_C3_HV")}
_ren = {}
for n, (ni, no) in LS_NET.items():
    _ren["%s__in" % n], _ren["%s__out" % n] = ni, no
SHAPES[:] = [(la, bx, _ren.get(nt, nt)) for (la, bx, nt) in SHAPES]

ADC_NET = {"adc_hold": "ADC_HOLD", "is_smp": "IS_SMP", "clk": "OSC_CLK", "adc_start": "ADC_START", "cur_trk": "CUR_TRK",
           "adc_sel": "ADC_SEL", "adc_valid_a": "ADC_VALID_A", "adc_valid_b": "ADC_VALID_B", "por_n": "POR_N"}
for k in range(14):
    ADC_NET["adc_raw_a[%d]" % k] = "ADC_RAW_A_%d" % k
    ADC_NET["adc_raw_b[%d]" % k] = "ADC_RAW_B_%d" % k
# ---------------------------------------------------------------- antenna diodes: removed in try g
# Try f placed 30 sg13g2_antennanp under the ctrl adc_raw_* / adc_valid_* inputs because layout A did not drive them.
# The SAR sub-macro of the ADC drives these nets now (diffusion on every net): no diode.
DIODE_CELLS = []
X0G, Y0G = 319.4, 330.0              # router grid origin (maze section)

# ---------------------------------------------------------------- instance pin -> net map (LVS reference)
CONN = {
    "u_ctrl": ("r1_ctrl_top", dict(
        {"cs_n": "CS_N_P2C", "ma_sclk": "MA_SCLK_P2C", "slo_sdo": "SLO_SDO_C2P", "sdi": "SDI_P2C",
         "en_pad": "EN_STO_IN_P2C", "fault_n": "FAULT_N_C2P", "gate_a": "PWM_A", "gate_b": "PWM_B", "gate_c": "PWM_C",
         "cmp[0]": "CMP_OC_A", "cmp[1]": "CMP_NEG_A", "cmp[2]": "CMP_OC_B", "cmp[3]": "CMP_NEG_B",
         "t2f_clk": "T2F_FOUT", "t2f_en": "T2F_EN", "t2f_mode": "T2F_MODE", "clk": "OSC_CLK", "por_n": "POR_N",
         "az_win": "AZ_WIN", "VDD": "VDD", "VSS": "VSS"},
        **dict({"osc_trim[%d]" % k: "OSC_TRIM_%d" % k for k in range(5)},
               **dict({"pga_c[%d]" % k: "PGA_C%d" % k for k in range(4)},
                      **dict({c: n for (n, c, s) in TAPS}, **{k: v for k, v in ADC_NET.items() if k not in ("clk", "por_n")}))))),
    "u_adc": ("r1_adc", dict(ADC_NET, **{
        "ain_sin_p": "AFE_SOUTS_P", "ain_sin_n": "AFE_SOUTS_N", "ain_cos_p": "AFE_SOUTC_P", "ain_cos_n": "AFE_SOUTC_N",
        "ain_isa_p": "ISN_OUTA_P", "ain_isa_n": "ISN_OUTA_N", "ain_isb_p": "ISN_OUTB_P", "ain_isb_n": "ISN_OUTB_N",
        "vcm2": "VCM2", "vcm": "VCM", "ibias": "IB_ADC_REF", "vref_in": "VREF_BG",
        "vdda": "VDDA", "vdd": "VDD", "vss": "VSS"})),
    "u_gate": ("r1_gate_lv", {"pwm_a": "PWM_A", "pwm_b": "PWM_B", "pwm_c": "PWM_C", "gate_en": "VDD",
                              "gc_a": "GATE_A_C2P", "gc_b": "GATE_B_C2P", "gc_c": "GATE_C_C2P",
                              "vdd": "VDD", "vdda": "VDDA", "vss": "VSS"}),
    "u_bgr": ("r1_bgr", {"vdd": "VDDA", "vss": "VSS", "vref": "VREF_BG", "pbias": "PBIAS", "pcasc": "PCASC"}),
    "u_t2f": ("r1_t2f", {"vdd": "VDDA", "vdd12": "VDD", "vss": "VSS", "pbias": "PBIAS", "pcasc": "PCASC",
                         "vref": "VREF_B", "en": "T2F_EN_HV", "mode": "T2F_MODE_HV", "fout": "T2F_FOUT"}),
    "u_safe": ("r1_safe", dict({"vref": "VREF_B", "oc_a": "CMP_OC_A", "neg_a": "CMP_NEG_A", "oc_b": "CMP_OC_B",
                                "neg_b": "CMP_NEG_B", "ibias_oa": "IB_SF_OA", "ibias_na": "IB_SF_NA",
                                "ibias_ob": "IB_SF_OB", "ibias_nb": "IB_SF_NB", "outa_p": "ISN_OUTA_P",
                                "outa_n": "ISN_OUTA_N", "outb_p": "ISN_OUTB_P", "outb_n": "ISN_OUTB_N",
                                "vdda": "VDDA", "vdd": "VDD", "vss": "VSS"}, **{s: n for (n, c, s) in TAPS})),
    "u_bias": ("r1_bias", {"vdda": "VDDA", "vdd": "VDD", "vss": "VSS", "pbias": "PBIAS", "pcasc": "PCASC",
                           "ib_afe_s1": "IB_AFE_S1", "ib_afe_s2": "IB_AFE_S2", "ib_afe_c1": "IB_AFE_C1",
                           "ib_afe_c2": "IB_AFE_C2", "ib_is_a": "IB_IS_A", "ib_is_b": "IB_IS_B",
                           "ib_sf_oa": "IB_SF_OA", "ib_sf_na": "IB_SF_NA", "ib_sf_ob": "IB_SF_OB",
                           "ib_sf_nb": "IB_SF_NB", "ib_adc_ref": "IB_ADC_REF", "por_n": "POR_N",
                           "vref": "VREF_BG", "vref_b": "VREF_B"}),
    "u_afe": ("r1_afe", {"sinp": "SIN_P", "sinn": "SIN_N", "cosp": "COS_P", "cosn": "COS_N",
                         "souts_p": "AFE_SOUTS_P", "souts_n": "AFE_SOUTS_N", "soutc_p": "AFE_SOUTC_P",
                         "soutc_n": "AFE_SOUTC_N", "vcm2": "VCM2", "ib_s1": "IB_AFE_S1", "ib_s2": "IB_AFE_S2",
                         "ib_c1": "IB_AFE_C1", "ib_c2": "IB_AFE_C2", "c1": "PGA_C0_HV", "c2": "PGA_C1_HV",
                         "c3": "PGA_C2_HV", "c4": "PGA_C3_HV", "vdd": "VDDA", "vss": "VSS"}),
    "u_isense": ("r1_isense", {"isa_p": "ISA_P", "isa_n": "ISA_N", "isb_p": "ISB_P", "isb_n": "ISB_N",
                               "outa_p": "ISN_OUTA_P", "outa_n": "ISN_OUTA_N", "outb_p": "ISN_OUTB_P",
                               "outb_n": "ISN_OUTB_N", "vref": "VREF_B", "vcm": "VCM", "ibias_a": "IB_IS_A",
                               "ibias_b": "IB_IS_B", "az_a": "AZ_WIN", "azh_a": "AZ_WIN", "az_b": "AZ_WIN",
                               "azh_b": "AZ_WIN", "vdda": "VDDA", "vdd": "VDD", "vss": "VSS"}),
    "u_osc": ("r1_osc", dict({"en": "OSC_EN", "osc_clk": "OSC_CLK", "vdd": "VDD", "vss": "VSS"},
                             **{"trim%d" % k: "OSC_TRIM_%d" % k for k in range(5)})),
    "u_tie_osc": ("sg13g2_tiehi", {"L_HI": "OSC_EN", "VDD": "VDD", "VSS": "VSS"}),
}
for n, (ni, no) in LS_NET.items():
    CONN[n] = ("r1_ls", {"in": ni, "out": no, "vdd": "VDD", "vdda": "VDDA", "vss": "VSS"})
for d in DIODE_CELLS:
    CONN[d["instance"]] = ("sg13g2_antennanp", {"A": d["net"], "VDD": "VDD", "VSS": "VSS"})

# ---------------------------------------------------------------- maze router (Metal2-Metal4, 0.8 um grid)
import math  # noqa: E402
import time  # noqa: E402

PG = MZ.P
X0G, Y0G = 319.4, 330.0              # grid origin: isense south/north pins and the ls nodes fall on the grid
NXG, NYG = int((1379.0 - X0G) / PG) + 1, int((1379.0 - Y0G) / PG) + 1
LI = {"M2": 0, "M3": 1, "M4": 2}
R = MZ.Router(X0G, Y0G, NXG, NYG)
R.block_edges()
R.block_area([0, 1, 2], 0.0, 0.0, 321.0, DIE)                     # IO ring (west), keep 0.45 um off the IO pins
R.reserve(0, 0.0, 0.0, 321.0, DIE, None, 0.45)
R.reserve(1, 0.0, 0.0, 321.0, DIE, None, 0.45)
R.reserve(2, 0.0, 0.0, 321.0, DIE, None, 0.45)
for r in PLACED:
    x0, y0, x1, y1 = r["bbox_um"]
    for l in ([0] if r["macro"] == "r1_ls" else [0, 1, 2]):
        R.reserve(l, x0, y0, x1, y1, None, 0.45)
for bb in (TIE.dbbox().transformed(TT), B(DX0, DY0 - 0.3, DEC_X1, DY0 + 4.1)):
    R.reserve(0, bb.left, bb.bottom, bb.right, bb.top, None, 0.45)
_ring_core = db.Region(ring.begin_shapes_rec(L["M2"])) + db.Region(ring.begin_shapes_rec(L["M3"])) + \
    db.Region(ring.begin_shapes_rec(L["M4"]))
_core = db.Region(db.Box.from_dbox(B(321.0, 321.0, 1379.0, 1379.0) * (1.0 / ly.dbu)))
RING_IN_CORE = 0
for lay in ("M2", "M3", "M4"):
    for poly in (db.Region(ring.begin_shapes_rec(L[lay])) & _core).each():
        bb = poly.bbox().to_dtype(ly.dbu)
        R.reserve(LI[lay], bb.left, bb.bottom, bb.right, bb.top, None, 0.45)
        RING_IN_CORE += 1


class SIdx:
    """bucketed index of top-level shapes per layer (spacing checks of the pin access stubs)."""
    def __init__(self, bs=10.0):
        self.bs, self.b = bs, {}

    def add(self, lay, box, net):
        for i in range(int(box.left // self.bs), int(box.right // self.bs) + 1):
            for j in range(int(box.bottom // self.bs), int(box.top // self.bs) + 1):
                self.b.setdefault((lay, i, j), []).append((box, net))

    def near(self, lay, box, d):
        seen = set()
        for i in range(int((box.left - d) // self.bs), int((box.right + d) // self.bs) + 1):
            for j in range(int((box.bottom - d) // self.bs), int((box.top + d) // self.bs) + 1):
                for (bx, nt) in self.b.get((lay, i, j), []):
                    if id(bx) in seen:
                        continue
                    seen.add(id(bx))
                    if bx.left - d < box.right and box.left - d < bx.right and bx.bottom - d < box.top and \
                            box.bottom - d < bx.top:
                        yield bx, nt


SI = SIdx()
for (la, bx, nt) in SHAPES:
    if la in LI:
        SI.add(la, bx, nt)
        w = min(bx.width(), bx.height())
        R.reserve(LI[la], bx.left, bx.bottom, bx.right, bx.top, nt, 0.85 if w > 9.9 else 0.45)
for r in PLACED:                                                    # macro outlines (other macros' stubs stay out)
    x0, y0, x1, y1 = r["bbox_um"]
    for la in (["M2"] if r["macro"] == "r1_ls" else ["M2", "M3", "M4"]):
        SI.add(la, B(x0 + 1.6, y0 + 1.6, x1 - 1.6, y1 - 1.6), "__macro_" + r["instance"])


def g_round(v, base):
    return round(base + round((v - base) / PG) * PG, 4)


def g_out(v, base, sgn):
    q = (v - base) / PG
    return round(base + (math.ceil(q - 1e-9) if sgn > 0 else math.floor(q + 1e-9)) * PG, 4)


ACCESS = []
ACC_FAIL = []


def access(net, pb, layer, edge, hw=0.2):
    """pin access: a stub of the pin layer from the pin out of the macro edge to a free grid node (L-shaped when
    the pin centre is off the grid), checked against the shapes of other nets (0.25 um), then a router pin there."""
    li = LI[layer]
    k = R.nid(net)
    sgn = 1 if edge in "NE" else -1
    if edge in "NS":
        along, o_in, o_edge = pb.center().x, pb.center().y, (pb.top if edge == "N" else pb.bottom)
        ba, bo = X0G, Y0G
    else:
        along, o_in, o_edge = pb.center().y, pb.center().x, (pb.right if edge == "E" else pb.left)
        ba, bo = Y0G, X0G
    o0 = g_out(o_edge + sgn * 0.45, bo, sgn)
    a0 = g_round(along, ba)
    cands = sorted([(abs(da) + 1.5 * ko, ko, da) for ko in range(4) for da in range(-4, 5)])
    for _, ko, da in cands:
        on, an = round(o0 + sgn * ko * PG, 4), round(a0 + da * PG, 4)
        hi = min(hw, (pb.width() if edge in "NS" else pb.height()) / 2.0)     # inside the outline: pin width
        if edge in "NS":
            x, y = an, on
            boxes = [B(along - hi, o_in, along + hi, o_edge), B(along - hw, o_edge, along + hw, on),
                     B(min(along, an) - hw, on - hw, max(along, an) + hw, on + hw)]
        else:
            x, y = on, an
            boxes = [B(o_in, along - hi, o_edge, along + hi), B(o_edge, along - hw, on, along + hw),
                     B(on - hw, min(along, an) - hw, on + hw, max(along, an) + hw)]
        try:
            i, j = R.ij(x, y)
        except ValueError:
            continue
        if not R.inside(i, j) or R.res[li, i, j] not in (MZ.FREE, k):
            continue
        padb = B(x - 0.2, y - 0.2, x + 0.2, y + 0.2)
        bad = False
        for bx in boxes + [padb]:
            for (ob, onet) in SI.near(layer, bx, 0.25):
                if onet != net and not (onet.startswith("__macro_") and bx is not padb and False):
                    bad = True
                    break
            if bad:
                break
        if bad:
            continue
        for bx in boxes:
            if bx.width() > 1e-6 and bx.height() > 1e-6:
                rect(layer, bx, net)
                SI.add(layer, bx, net)
                R.reserve(li, bx.left, bx.bottom, bx.right, bx.top, net, 0.45)
        SI.add(layer, padb, net)
        R.add_pin(net, [(li, x, y)])
        ACCESS.append({"net": net, "layer": layer, "edge": edge, "node": [x, y], "pin": [round(pb.left, 3),
                       round(pb.bottom, 3), round(pb.right, 3), round(pb.top, 3)]})
        return (x, y)
    ACC_FAIL.append({"net": net, "pin": str(pb), "layer": layer, "edge": edge})
    log("ACCESS FAILED", net, pb, layer, edge)
    return None


def node_pin(net, layer, pts):
    li = LI[layer]
    nodes = [(li, x, y) for (x, y) in pts]
    R.add_pin(net, nodes)
    for (x, y) in pts:
        SI.add(layer, B(x - 0.2, y - 0.2, x + 0.2, y + 0.2), net)


def box_pin(net, layer, box, step=1):
    """router pin: the grid nodes inside a hand-drawn shape of the net (pads stay inside the shape)."""
    pts = []
    i0, i1 = math.ceil((box.left + 0.2 - X0G) / PG - 1e-9), math.floor((box.right - 0.2 - X0G) / PG + 1e-9)
    j0, j1 = math.ceil((box.bottom + 0.2 - Y0G) / PG - 1e-9), math.floor((box.top - 0.2 - Y0G) / PG + 1e-9)
    for i in range(i0, i1 + 1, step):
        for j in range(j0, j1 + 1, step):
            pts.append((round(X0G + i * PG, 4), round(Y0G + j * PG, 4)))
    if not pts:
        raise SystemExit("box_pin %s: no node inside %s" % (net, box))
    R.add_pin(net, [(LI[layer], x, y) for (x, y) in pts])
    return pts


MAZE = {}


def mz(net, *ends):
    MAZE.setdefault(net, []).extend(ends)


# ADC north digital pins <-> ctrl south pins (34 nets) and the OSC_CLK / POR_N branches
for apin, net in ADC_NET.items():
    if apin in ("clk", "por_n"):
        continue
    access(net, ctrl_pin(apin), "M2", "S")
    access(net, P["adc"][apin], "M2", "N")
    mz(net, "u_ctrl/" + apin, "u_adc/" + apin)
node_pin("OSC_CLK", "M3", [(1072.2, 1062.8)])
access("OSC_CLK", P["adc"]["clk"], "M2", "N")
mz("OSC_CLK", "hand line u_osc/osc_clk - u_ctrl/clk", "u_adc/clk")
access("POR_N", P["bias"]["por_n"], "M3", "E")
access("POR_N", ctrl_pin("por_n"), "M3", "W")
access("POR_N", P["adc"]["por_n"], "M2", "N")
mz("POR_N", "u_bias/por_n", "u_ctrl/por_n", "u_adc/por_n")
# bias currents (11)
IBD = [("IB_AFE_S1", "ib_afe_s1", ("afe", "ib_s1", "S")), ("IB_AFE_S2", "ib_afe_s2", ("afe", "ib_s2", "S")),
       ("IB_AFE_C1", "ib_afe_c1", ("afe", "ib_c1", "S")), ("IB_AFE_C2", "ib_afe_c2", ("afe", "ib_c2", "S")),
       ("IB_IS_A", "ib_is_a", ("isn", "ibias_a", "N")), ("IB_IS_B", "ib_is_b", ("isn", "ibias_b", "S")),
       ("IB_SF_OA", "ib_sf_oa", ("safe", "ibias_oa", "S")), ("IB_SF_NA", "ib_sf_na", ("safe", "ibias_na", "S")),
       ("IB_SF_OB", "ib_sf_ob", ("safe", "ibias_ob", "S")), ("IB_SF_NB", "ib_sf_nb", ("safe", "ibias_nb", "S")),
       ("IB_ADC_REF", "ib_adc_ref", ("adc", "ibias", "W"))]
EDGE_OF = {("afe", "S"): "S", ("isn", "ibias_a"): "S", ("isn", "ibias_b"): "N", ("safe", "S"): "S", ("adc", "W"): "W"}
for net, bpin, (blk, dpin, _e) in IBD:
    access(net, P["bias"][bpin], "M3", "N")
    edge = {"afe": "S", "safe": "S", "adc": "W"}.get(blk) or ("S" if dpin == "ibias_a" else "N")
    access(net, P[blk][dpin], "M3", edge)
    mz(net, "u_bias/" + bpin, "u_%s/%s" % ({"isn": "isense"}.get(blk, blk), dpin))
for net, nm in [("PBIAS", "pbias"), ("PCASC", "pcasc")]:
    access(net, P["bgr"][nm], "M3", "E")
    access(net, P["bias"][nm], "M3", "W")
    access(net, P["t2f"][nm], "M3", "E")
    mz(net, "u_bgr/" + nm, "u_bias/" + nm, "u_t2f/" + nm)
for net, ypad, cname in [("SDI_P2C", 494.975, "sdi"), ("EN_STO_IN_P2C", 636.975, "en_pad")]:
    access(net, B(320.71, ypad - 0.25, 321.0, ypad + 0.25), "M3", "E")
    access(net, ctrl_pin(cname), "M3", "W")
    mz(net, "pad %s p2c" % net[:-4], "u_ctrl/" + cname)
access("T2F_FOUT", P["t2f"]["fout"], "M3", "E")
access("T2F_FOUT", ctrl_pin("t2f_clk"), "M3", "W")
mz("T2F_FOUT", "u_t2f/fout", "u_ctrl/t2f_clk")
for n, (ni, no) in LS_NET.items():
    cn = {"T2F_EN": "t2f_en", "T2F_MODE": "t2f_mode"}.get(ni) or "pga_c[%s]" % ni[-1]
    access(ni, ctrl_pin(cn), "M3", "W")
    node_pin(ni, "M3", [LS_NODE[n]["in"]])
    node_pin(no, "M3", [LS_NODE[n]["out"]])
    if no.startswith("T2F"):
        access(no, P["t2f"]["en" if "EN" in no else "mode"], "M3", "E")
        mz(no, n + "/out", "u_t2f/" + ("en" if "EN" in no else "mode"))
    else:
        access(no, P["afe"]["c%d" % (int(ni[-1]) + 1)], "M3", "S")
        mz(no, n + "/out", "u_afe/c%d" % (int(ni[-1]) + 1))
    mz(ni, "u_ctrl/" + cn, n + "/in")
access("AZ_WIN", ctrl_pin("az_win"), "M3", "E")
for nm in ("az_a", "azh_a", "az_b", "azh_b"):
    access("AZ_WIN", P["isn"][nm], "M3", "S" if nm.endswith("_a") else "N")
mz("AZ_WIN", "u_ctrl/az_win", "u_isense/az_a", "u_isense/azh_a", "u_isense/az_b", "u_isense/azh_b")
access("VCM", P["isn"]["vcm"], "M3", "S")
access("VCM", P["adc"]["vcm"], "M3", "E")
mz("VCM", "u_isense/vcm", "u_adc/vcm")
access("VCM2", P["afe"]["vcm2"], "M3", "S")
access("VCM2", P["adc"]["vcm2"], "M3", "W")
mz("VCM2", "u_afe/vcm2", "u_adc/vcm2")
node_pin("VREF_B", "M4", [(565.8, round(Y0G + j * PG, 4)) for j in range(int((620.0 - Y0G) / PG), int((645.0 - Y0G) / PG))])
access("VREF_B", P["t2f"]["vref"], "M3", "E")
mz("VREF_B", "Metal4 riser x 566 (hand)", "u_t2f/vref")
for k, flag in enumerate(["oc_a", "neg_a", "oc_b", "neg_b"]):
    net = "CMP_%s" % flag.upper()
    access(net, P["safe"][flag], "M3", "S")
    access(net, ctrl_pin("cmp[%d]" % k), "M3", "E")
    mz(net, "u_safe/" + flag, "u_ctrl/cmp[%d]" % k)
for net, sx0, sx1 in [("VSS", 567.5, 569.0), ("VDD", 569.5, 571.0)]:
    box_pin(net, "M3", B(sx0, 600.0, sx1, 661.0), step=4)
    for n in LS_NODE:
        node_pin(net, "M3", [LS_NODE[n][net.lower()]])
    mz(net, "riser x %.1f (hand)" % sx0, "6 x r1_ls/%s" % net.lower())
access("VDD", P["t2f"]["vdd12"], "M3", "E")
box_pin("VDDA", "M4", B(470.0, 736.0, 521.0, 738.0), step=4)
for n in LS_NODE:
    node_pin("VDDA", "M3", [LS_NODE[n]["vdda"]])
mz("VDDA", "AFE VDDA rail (hand)", "6 x r1_ls/vdda")
mz("VDD", "u_t2f/vdd12")
log("access stubs", len(ACCESS), "failed", len(ACC_FAIL))
t0 = time.time()
ok = R.route_all(rounds=8, log=log) if not os.environ.get("R1G_NOMAZE") else False
log("maze: ok", ok, "failed", R.failed, "time %.0f s" % (time.time() - t0))
LV = {"M2": "V2", "M3": "V3"}
MZ_STATS = {}
for kind, net, lname, x1, y1, x2, y2 in list(R.shapes()):
    bx = B(round(x1, 4), round(y1, 4), round(x2, 4), round(y2, 4))
    if kind == "via":
        top.shapes(L["V2" if lname == "Via2" else "V3"]).insert(bx)
    else:
        rect(lname, bx, net)
for net in MAZE:
    k = R.nets.get(net)
    st = R.net_stats(k) if k is not None else None
    MZ_STATS[net] = st
    routed = net not in R.failed
    pins_ = R.pins.get(k, [])
    if net not in NETS:
        note(net, MAZE[net][0], MAZE[net][1:], "M2, M3, M4 (maze, 0.4 um)", "routed" if routed else "FAILED", "maze")
    else:
        NETS[net]["maze_branch"] = {"ends": MAZE[net], "state": "routed" if routed else "FAILED"}
    if pins_ and net not in ("VSS", "VDD", "VDDA"):
        l0, i0, j0 = pins_[0][0]
        x, y = R.xy(i0, j0)
        label(MZ.LNAME[l0], x, y, net)


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
        allr = db.Region()
        for k in keys:
            allr += grown[k]
        for i in range(len(keys)):
            ki = keys[i]
            others = db.Region()
            for j in range(i + 1, len(keys)):
                if not grown[keys[j]].bbox().overlaps(grown[ki].bbox()):
                    continue
                ov = grown[ki] & grown[keys[j]]
                if not ov.is_empty():
                    issues.append([lay, ki, keys[j], str(ov.bbox().to_dtype(ly.dbu))])
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
    """top-level M2-M5 shapes that enter a macro outline deeper than 1.5 um (pin landings excepted)."""
    hits = []
    for r in PLACED:
        x0, y0, x1, y1 = r["bbox_um"]
        inner = db.DBox(x0 + 1.5, y0 + 1.5, x1 - 1.5, y1 - 1.5)
        lays = ("M2",) if r["macro"] == "r1_ls" else ("M2", "M3", "M4", "M5")
        if r["macro"] in ("r1_safe",):
            lays = ("M2", "M3", "M4")                        # no Metal5 / TopMetal in r1_safe: Metal5 crossings allowed
        for lay, box, net in SHAPES:
            if lay in lays and box.overlaps(inner):
                if r["macro"] == "r1_ls" or any(w[0] == r["instance"] and w[1].enlarged(0.01, 0.01).inside(box & inner) is False and (box & inner).inside(w[1].enlarged(0.01, 0.01)) for w in WHITELIST):
                    continue                                 # r1_ls: the hand pin landings (Metal2 pads)
                hits.append([r["instance"], lay, net, str(box)])
    return hits


def tm_over_mim():
    """TopMetal1 (top level) over a block with MIM (bias, t2f, AFE, isense, ADC) - must be empty."""
    hits = []
    for r in PLACED:
        if r["macro"] not in ("r1_bias", "r1_t2f", "r1_afe", "r1_isense", "r1_adc"):
            continue
        x0, y0, x1, y1 = r["bbox_um"]
        ob = db.DBox(x0, y0, x1, y1)
        for lay, box, net in SHAPES:
            if lay == "TM1" and box.overlaps(ob):
                hits.append([r["instance"], net, str(box)])
    return hits


issues = self_check()
ovl, outside = overlap_check()
ovl10, _ = overlap_check(10.0)
intrude = macro_vs_routes()
mim = tm_over_mim()
PLACED.insert(0, {"instance": "u_ring", "macro": "r1_padring", "orientation": "R0", "origin_um": [0, 0],
                  "bbox_um": [0, 0, DIE, DIE],
                  "source": "<G1_RESULTS_ROOT>/r1_padring/ring-20261021-d/r1_padring_1700.gds (fill instances removed: %d; west TopMetal1 ECO%s%s)" % (removed_fill, "" if NO_H else ("; try-h0 IOPadVss riser and south VSS row gap at pad 1" if RISER else "; south VSS row gap at pad 1; IO cells unmodified"), ("; die pad %d IOPadIOVss -> IOPadVss" % PADSWAP["die_pad"]) if PADSWAP else ""),
                  "source_sha256": RING_SHA, "s7_c4": [0, 0], "try_f_origin_um": [0, 0], "delta_vs_try_f_um": [0, 0]})
gds = os.path.join(OUT, "r1_top.gds")
opt = db.SaveLayoutOptions()
opt.write_context_info = False
ly.write(gds, opt)
res = {"gds": "r1_top.gds", "gds_sha256": sha256(gds), "top": "r1_top", "die_um": DIE, "try": "g" if NO_H else ("h0" if RISER else "h1" + (("-" + PADMAP) if PADMAP else "")),
       "iopadvss_eco": RISER, "padmap": PADSWAP, "vss_pad_cell_origins_x": VSS_PAD_X,
       "fill_instances_removed_from_ring": removed_fill, "ring_labels_copied_to_top": RING_LABELS,
       "ring_shapes_in_core_M2_M4": RING_IN_CORE,
       "antenna_decap_row": DECAP_ROW, "tie_cells": [TIE_CELL], "antenna_diodes": DIODE_CELLS,
       "antenna_diodes_removed": "30 sg13g2_antennanp of try f (the ADC SAR sub-macro drives the nets)",
       "merged_std_cells": MERGED_STD, "south_supply_stacks": SSTACK_REC,
       "south_vdd_feed": not bool(os.environ.get("R1G_NO_SFEED")), "ring_eco": ECO, "supply_h_feed": FEED,
       "self_check_net_conflicts": issues, "instance_overlaps": ovl, "instance_pairs_closer_than_10um": ovl10,
       "outside_extended_window": outside, "routes_inside_macros": intrude, "tm1_over_mim_blocks": mim,
       "placement": PLACED, "nets": NETS, "connections": {k: {"cell": c, "pins": m} for k, (c, m) in CONN.items()},
       "crossbar": XBAR, "maze": {"grid_origin_um": [X0G, Y0G], "pitch_um": PG, "nodes": [NXG, NYG],
                                  "nets": len(MAZE), "failed": R.failed, "access_failed": ACC_FAIL,
                                  "stats": MZ_STATS},
       "macro_pins_used": {k: ({n: [round(b.left, 3), round(b.bottom, 3), round(b.right, 3), round(b.top, 3)]
                                for n, b in v.items()} if isinstance(v, dict) else
                               [[round(b.left, 3), round(b.bottom, 3), round(b.right, 3), round(b.top, 3)] for b in v])
                           for k, v in P.items()}}
with open(os.path.join(OUT, "r1_top_assembly.json"), "w") as f:
    json.dump(res, f, indent=1)
log("gds", gds, res["gds_sha256"])
log("net conflicts", len(issues))
for i in issues[:80]:
    log("  ", i)
log("overlaps", ovl, "closer than 10 um", ovl10, "outside", outside)
log("routes inside macros", len(intrude))
for i in intrude[:40]:
    log("  ", i)
log("TM1 over MIM blocks", len(mim), mim[:10])
log("maze failed", R.failed, "access failed", len(ACC_FAIL))
