#!/usr/bin/env python3
"""Pin template of r1_ctrl 0.6 (S7 floorplan C4, 1.7 mm die).
Writes the LibreLane pin order file (pins_v06.cfg) and the pin table (pins_v06.md / pins_v06.json).

usage: gen_pins_v06.py [W H] [outdir]       default die 520 x 664 um, outdir = this directory
Revision 0.7: PINS_V07=1 adds `cur_trk` (r1_adc SAR input, INTERFACES "ADC -> ctrl") at the next free south
slot of the ADC group (n = 34, local x 280.80) and writes pins_v07*; every other pin keeps its 0.6 slot.

How exact positions are obtained. LibreLane's custom I/O placement puts the pins of one side on the
slots of a track subset (E/W: Metal3, one slot per `min_distance`; N/S: Metal2). If the number of pins
(real + virtual, `$n` lines) is S-1, with S the slot count of the side, every pin sits on slot
(index in the list). This script therefore writes `$n` gap lines and a final filler, and the table
below is the exact result (checked against the final DEF of the run by check_pins_v06.py).
Local frame: ctrl lower-left corner at the origin, orientation R0.
Chip frame of the C4 placement: ctrl origin (543.8, 673.3) um (S7 rects, run s7-floorplan/run-20261021-d).
SPDX-License-Identifier: Apache-2.0"""
import json, math, os, sys

W = float(sys.argv[1]) if len(sys.argv) > 2 else 520.0
H = float(sys.argv[2]) if len(sys.argv) > 2 else 664.0
OUT = sys.argv[3] if len(sys.argv) > 3 else os.path.dirname(os.path.abspath(__file__))
STRIDE = int(os.environ.get("PIN_STRIDE_E", "1"))   # slots between consecutive cmp / tap pins (1 = 0.84 um)
TAG = ("" if (W, H) == (520.0, 664.0) else "_%dx%d" % (W, H)) + ("" if STRIDE == 1 else "_s%d" % STRIDE)
ORG = (543.8, 673.3)          # C4 chip origin of r1_ctrl
SAFE = (1088.8, 376.0)        # r1_safe origin (C4), native pins
OSC = (1088.8, 1041.8)        # r1_osc origin (C4); pins of the revision-2 working-tree GDS
ISE = (1088.8, 735.0)         # r1_isense origin (C4), working-tree GDS
AFE = (336.0, 720.0)          # r1_afe origin (C4)

# ---------------- slot grids (verified against the t7 run: Metal3 Y 420 step 420, Metal2 X 480 step 480)
def ntracks(extent, origin, step): return int(math.floor((extent - origin) / step + 1e-9)) + 1
EW_STEP, NS_STEP = 0.84, 0.96            # min_distance in um (2 tracks)
ey = [0.42 + 0.42 * i for i in range(ntracks(H, 0.42, 0.42))][::2]
nx = [0.48 + 0.48 * i for i in range(ntracks(W, 0.48, 0.48))][::2]
SLOTS = {"E": ey, "W": ey, "N": nx, "S": nx}
STEP = {"E": EW_STEP, "W": EW_STEP, "N": NS_STEP, "S": NS_STEP}

def slot_near(side, v, after=-1):
    s = SLOTS[side]
    k = min(range(len(s)), key=lambda i: abs(s[i] - v))
    return max(k, after + 1)

pins = []   # dict(net, side, k, want, consumer)

def put(side, net, want, consumer, after):
    k = slot_near(side, want, after)
    pins.append(dict(net=net, side=side, k=k, want=want, consumer=consumer))
    return k

# ---------------- SOUTH: 34 ADC pins at the ADC slot (N edge of r1_adc, chip x 556.0-839.4 in C4), pitch 8 slots
s_nets = ["adc_raw_a[%d]" % b for b in range(13, -1, -1)] + ["adc_valid_a"] + \
         ["adc_raw_b[%d]" % b for b in range(13, -1, -1)] + ["adc_valid_b"] + \
         ["adc_hold", "adc_start", "adc_sel", "is_smp"]
V07 = bool(os.environ.get("PINS_V07"))
if V07: s_nets += ["cur_trk"]      # revision 0.7
PFX = "pins_v07" if V07 else "pins_v06"
k = slot_near("S", 20.0)
for i, n in enumerate(s_nets):
    pins.append(dict(net=n, side="S", k=k + 8 * i, want=None,
                     consumer="r1_adc N edge (slot pin, at this x)"))

# ---------------- NORTH
k = -1
for n, x, cons in [("gate_a", 14.0, "r1_gate_lv pwm_a (W edge, chip 441.0, 1315.9) via north band"),
                   ("gate_b", 18.0, "r1_gate_lv pwm_b (chip 441.0, 1317.5)"),
                   ("gate_c", 22.0, "r1_gate_lv pwm_c (chip 441.0, 1318.3)"),
                   ("cs_n", 1.0 * 921.0 - ORG[0], "pad 16 CS_N (chip x 921)"),
                   ("ma_sclk", W - 24.0, "pad 17 MA_SCLK (chip x 1063, east of the macro: clamped)"),
                   ("slo_sdo", W - 12.0, "pad 18 SLO_SDO (chip x 1205, east of the macro: clamped)")]:
    k = put("N", n, x, cons, k)

# ---------------- WEST (local y)
k = -1
for n, y, cons in [("t2f_clk", 6.0, "r1_t2f fout (via chan_swv, x 539-551)"),
                   ("t2f_en", 10.0, "r1_t2f en through an r1_ls"),
                   ("t2f_mode", 14.0, "r1_t2f mode through an r1_ls"),
                   ("bias_en", 18.0, "bias source slot (442, 488.6) through an r1_ls"),
                   ("sdi", 22.0, "pad 19 SDI (west band)"),
                   ("en_pad", 26.0, "pad 20 EN (west band)"),
                   ("pga_c[0]", 30.0, "r1_ls -> r1_afe c1 (chip x 409.6, y 720.8)"),
                   ("pga_c[1]", 34.0, "r1_ls -> r1_afe c2 (chip x 420.8)"),
                   ("pga_c[2]", 38.0, "r1_ls -> r1_afe c3 (chip x 432.0)"),
                   ("pga_c[3]", 42.0, "r1_ls -> r1_afe c4 (chip x 443.2)"),
                   ("por_n", 1297.0 - ORG[1], "r1_por slot (345, 1270)-(400, 1325), chip y 1297")]:
    k = put("W", n, y, cons, k)

# ---------------- EAST (local y), bottom to top
k = -1
safe_x = {}
for ci, pre in enumerate(["oa", "na", "ob", "nb"]):
    for j in range(8):
        safe_x["tap_p[%d]" % (8 * ci + j)] = (pre + "_p%d" % j)
        safe_x["tap_n[%d]" % (8 * ci + j)] = (pre + "_n%d" % j)
SAFE_PINX = json.load(open(os.path.join(OUT, "safe_pinx.json"))) if os.path.exists(os.path.join(OUT, "safe_pinx.json")) else None
for ci, fl in enumerate(["oc_a", "neg_a", "oc_b", "neg_b"]):
    k = put("E", "cmp[%d]" % ci, 0.0, "r1_safe %s (bottom edge, chip x %.2f, y 376.5)" % (fl, SAFE[0] + SAFE_PINX[fl]), k + STRIDE - 1)
order = sorted(safe_x, key=lambda n: SAFE_PINX[safe_x[n]])
for n in order:
    xs = SAFE[0] + SAFE_PINX[safe_x[n]]
    k = put("E", n, 0.0, "r1_safe %s (top edge, chip x %.2f, y 663.3)" % (safe_x[n], xs), k + STRIDE - 1)
for n, y, cons in [("az_win", ISE[1] + 0.8 - ORG[1], "r1_isense az_a / azh_a (chip 1092.8, 735.8); az_b / azh_b at chip y 1031-1031.8 by top-level wiring"),
                   ("clk", OSC[1] + 21.15 - ORG[1], "r1_osc osc_clk (W edge, chip 1089.55, 1062.95)"),
                   ("osc_trim[0]", OSC[1] + 25.95 - ORG[1] + 0.0, "r1_osc trim0 (chip 1089.55, 1067.75)"),
                   ("osc_trim[1]", OSC[1] + 26.75 - ORG[1], "r1_osc trim1 (chip y 1068.55)"),
                   ("osc_trim[2]", OSC[1] + 27.55 - ORG[1], "r1_osc trim2 (chip y 1069.35)"),
                   ("osc_trim[3]", OSC[1] + 28.35 - ORG[1], "r1_osc trim3 (chip y 1070.15)"),
                   ("osc_trim[4]", OSC[1] + 29.15 - ORG[1], "r1_osc trim4 (chip y 1070.95)"),
                   ("fault_n", 1205.0 - ORG[1], "pad 12 FAULT_N (east, chip y 1205)")]:
    k = put("E", n, y, cons, k)

# ---------------- resolve coordinates, write the cfg
def coord(p):
    s = SLOTS[p["side"]][p["k"]]
    if p["side"] == "S": return (s, 0.0)
    if p["side"] == "N": return (s, H)
    if p["side"] == "W": return (0.0, s)
    return (W, s)

cfg = ["# r1_ctrl 0.6 pin template, die %g x %g um, generated by gen_pins_v06.py (do not edit by hand)" % (W, H)]
cfg = []
for side in "NESW":
    sp = sorted([p for p in pins if p["side"] == side], key=lambda p: p["k"])
    S = len(SLOTS[side])
    cfg += ["#" + side, "@min_distance=%g" % STEP[side]]
    pos = 0
    for p in sp:
        gap = p["k"] - pos
        if gap > 0: cfg.append("$%d" % gap)
        cfg.append(p["net"].replace("[", "\\[").replace("]", "\\]"))
        pos = p["k"] + 1
    tail = (S - 1) - pos
    assert tail >= 0, (side, S, pos)
    if tail > 0: cfg.append("$%d" % tail)
    # total entries (real + virtual) is S-1: every pin sits on slot = running index
    if not sp: cfg = cfg[:-1] + ["$%d" % (S - 1)]
open(os.path.join(OUT, "%s%s.cfg" % (PFX, TAG)), "w").write("\n".join(cfg) + "\n")

rows = []
for side in "SWEN":
    for p in sorted([p for p in pins if p["side"] == side], key=lambda p: p["k"]):
        x, y = coord(p)
        rows.append(dict(net=p["net"], edge=side, x=round(x, 3), y=round(y, 3), chip_x=round(ORG[0] + x, 2),
                         chip_y=round(ORG[1] + y, 2), consumer=p["consumer"]))
json.dump(dict(die=[W, H], origin_chip=ORG, pins=rows), open(os.path.join(OUT, "%s%s.json" % (PFX, TAG)), "w"), indent=1)
md = ["| Net | Edge | Local x (um) | Local y (um) | Chip x, y (C4, um) | Consumer pin |", "| --- | --- | ---: | ---: | --- | --- |"]
for r in rows:
    md.append("| `%s` | %s | %.2f | %.2f | %.2f, %.2f | %s |" % (r["net"], r["edge"], r["x"], r["y"], r["chip_x"], r["chip_y"], r["consumer"]))
open(os.path.join(OUT, "%s%s.md" % (PFX, TAG)), "w").write("\n".join(md) + "\n")
print("pins", len(rows), {s: len([r for r in rows if r["edge"] == s]) for s in "NESW"})
