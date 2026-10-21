#!/usr/bin/env python3
"""S7 re-floorplan of R1 with the real macro sizes: rectangles only (no layout, no PDK layers).

Usage (inside the pinned container, through flow/run.sh):
    python3 gen_s7_floorplan.py <out_dir>
Writes one outline GDS and one PNG per candidate, and s7_floorplan.json with the checks.
All coordinates in um, lower-left die corner at the origin.

Layers (not PDK layers): 200 die, 201 IO row, 202 core power ring band, 203 conservative window,
204 bondpads, 205 extended window outline, 210 digital macro, 211 analog block (real size),
219 analog block re-shaped or pending slot, 212 guard strip, 213 routing channel, 214 supply trunk band,
215 decoupling, 216 ring ECO zone (TopMetal2 only over MIM), 217 halo (5 um keep-out), 218 routing band (pads),
220 shortfall (outside the die), 230 text.
"""
import json, os, sys, itertools
import klayout.db as db

HALO = 5.0
IO_IN = 321.0
EXT = 331.0                     # extended window edge (G1 r4 practice, S6)

# Real macro sizes (um) and their source. "slot" = not laid out, size set by this study.
MACROS = {
    "r1_ctrl":   (520.0, 664.0, "0.4 run r1ctrl_ll_20261021_t7 (hardened)"),
    "r1_afe":    (192.8, 494.4, "revision E layout d17d505f7 (laid out)"),
    "r1_safe":   (249.34, 287.81, "layout-gen-20261021-b (laid out)"),
    "r1_bgr":    (96.0, 194.3, "layout-20261021-c (laid out)"),
    "r1_t2f":    (92.0, 102.6, "G1 revision 2 layout (laid out)"),
    "r1_osc":    (154.4, 118.4, "layout k (laid out); revision 2 working tree 148.2 x 110.4"),
    "r1_isense": (158.4, 296.8, "working tree 2026-10-21 07:41, both channels (not of record)"),
    "r1_gate_lv": (28.39, 27.9, "variant L (laid out)"),
}
ADC_SLOT_MM2 = 0.080   # revision 5 estimate 0.0755 (README) + 6 % for layout; this study's slot
NEED = {"r1_ctrl": 0.34528, "r1_afe": 0.09532, "r1_safe": 0.07176, "r1_bgr": 0.01865, "r1_t2f": 0.00944,
        "r1_osc": 0.01828, "r1_isense": 0.04701, "r1_adc": 0.0800, "r1_gate_lv": 0.00079,
        "r1_bias": 0.006, "r1_por": 0.003, "decap_vdda": 0.0075}

def ring(die):
    """Ring geometry for a die, from the r1_padring record (1600) and its build rule (1700: same offsets)."""
    return {"die": die, "ext": (EXT, EXT, die - EXT, die - EXT),
            "cons": (361.8, 362.16, die - 359.58, die - 362.7),
            "tm1_cols": [(324.82, 361.8), (die - 359.58, die - 324.58)],   # west, east (VSS outer, VDD inner)
            "tm2_rows": [(327.16, 362.16), (die - 362.7, die - 327.7)]}   # south, north

def pads(die):
    c = die / 2.0
    pos = [c - 2.5 * 140 + 140 * i for i in range(6)]
    names = ["VDD", "VSS", "IOVDD", "IOVSS", "VSS", "IOVSS", "VDDA", "ISA_P", "ISA_N", "ISB_P", "ISB_N", "FAULT_N",
             "GATE_A", "GATE_B", "GATE_C", "CS_N", "MA_SCLK", "SLO_SDO", "SDI", "EN", "SIN_P", "SIN_N", "COS_P", "COS_N"]
    out = {}
    for i, n in enumerate(names):
        side = "SENW"[i // 6]; p = pos[i % 6]
        xy = {"S": (p, 101.0), "E": (die - 101.0, p), "N": (p, die - 101.0), "W": (101.0, p)}[side]
        edge = {"S": (p, IO_IN), "E": (die - IO_IN, p), "N": (p, die - IO_IN), "W": (IO_IN, p)}[side]
        out[i + 1] = {"net": n, "side": side, "centre": xy, "edge": edge}
    return out

def swap_west(pd):
    """S6 item 6 pin-map change: west side bottom to top SIN_P, SIN_N, COS_P, COS_N, SDI, EN."""
    order = ["SIN_P", "SIN_N", "COS_P", "COS_N", "SDI", "EN"]
    for k, n in zip(range(19, 25), order):
        pd[k]["net"] = n
    return pd

def B(name, kind, x0, y0, w, h, **o):
    return dict(name=name, kind=kind, box=(x0, y0, x0 + w, y0 + h), **o)

def R(name, kind, x0, y0, x1, y1, **o):
    return dict(name=name, kind=kind, box=(x0, y0, x1, y1), **o)

def adc(x0, y0, h=None, w=None):
    a = ADC_SLOT_MM2 * 1e6
    if h: w = a / h
    else: h = a / w
    return B("r1_adc", "slot", x0, y0, round(w, 1), round(h, 1), mim=True, note="ADC slot (estimate 0.0755)")

# ------------------------------------------------------------------ candidates
def cand_c0():
    """Try-d topology (S6 F1) with the real macros, nothing changed: r1_safe has no place."""
    die = 1600.0; r = []
    r.append(R("trunk_s", "band", 331, 331, 1269, 371, note="Metal4 VSS/VDD/VDDA trunks + routing strip 361-371 (try d)"))
    r.append(R("nband", "rband", 405, 1237.3, 1195, 1269, note="pad 13-18 routes, decap row (try d)"))
    r.append(B("r1_afe", "ana", 336, 620, 192.8, 494.4, mim=True))
    r.append(R("chan_sw", "chan", 331, 575.3, 543.8, 615, nets=15, pitch=1.5, dir="h", note="AFE out, c1..c4, bias, SDI/EN"))
    r.append(R("strip_w", "strip", 533.8, 615, 543.8, 1237.3))
    r.append(B("r1_ctrl", "dig", 543.8, 573.3, 520, 664))
    r.append(R("strip_s", "strip", 543.8, 563.3, 1063.8, 573.3))
    r.append(R("chan_e", "chan", 1063.8, 563.3, 1083.8, 1237.3, nets=10, pitch=2.0, dir="v", note="isense out, bias"))
    r.append(B("r1_isense", "ana", 1088.8, 795.8, 158.4, 296.8, mim=True))
    r.append(B("r1_osc", "ana", 1088.8, 1102.6, 154.4, 118.4, mim=True))
    r.append(B("r1_bgr", "ana", 336, 376, 96, 194.3))
    r.append(B("r1_t2f", "ana", 442, 376, 92, 102.6))
    r.append(B("r1_bias", "slot", 442, 488.6, 87, 69.7, note="bias source, pending (no block)"))
    r.append(R("chan_swv", "chan", 539, 371, 551, 563.3, nets=5, pitch=2.0, dir="v", note="AFE -> ADC, shielded"))
    r.append(R("chan_link", "chan", 437, 563.3, 543.8, 575.3, nets=5, pitch=2.0, dir="h"))
    r.append(adc(556, 376, h=182.3))
    r.append(B("decap_vdda", "decap", 1005, 376, 73.8, 102.6, mim=True))
    r.append(R("chan_se", "chan", 1000, 483.6, 1083.8, 563.3, nets=10, pitch=2.0, dir="h"))
    r.append(B("r1_gate_lv", "ana", 440, 1196, 28.39, 27.9))
    r.append(B("r1_por", "slot", 345, 1165, 55, 55, note="POR, pending (no block)"))
    pins = {21: ("r1_afe", 336, 658.8), 22: ("r1_afe", 336, 662.8), 23: ("r1_afe", 336, 938.8), 24: ("r1_afe", 336, 942.8),
            8: ("r1_isense", 1247.2, 836.6), 9: ("r1_isense", 1247.2, 839.8), 10: ("r1_isense", 1247.2, 981.4),
            11: ("r1_isense", 1247.2, 984.6)}
    return dict(id="c0", die=die, title="C0: try-d topology, real macros unchanged", rects=r, pins=pins,
                unplaced={"r1_safe": 0.07176}, swap=False,
                needs=["none (baseline): shows the misfit"],
                links=links_c1())

def links_c1():
    return [
        ("ctrl S -> ADC N", "adc_raw_a/b[13:0], adc_valid_a/b, adc_hold, adc_start, adc_sel", 35, "strip_s + ADC halo 15 um", 15.0, "pitch-matched pins (ctrl 0.5 pin template)"),
        ("ctrl E -> safe W", "nP/nN[7:0] x 4 (64), oc/neg flags (4)", 68, "chan_e 20 um", 20.0, "pitch-matched pins; safe re-shape puts codes and flags on its west edge"),
        ("ctrl E -> isense W", "az_a, azh_a, az_b, azh_b", 4, "chan_e", 20.0, "straight"),
        ("ctrl E -> osc W", "clk, osc_trim[4:0]", 6, "chan_e", 20.0, "osc revision 2 must put osc_clk on the west edge"),
        ("AFE S -> ADC W", "souts_p/n, soutc_p/n, vcm2 (shielded)", 5, "chan_sw -> chan_link -> chan_swv 12 um", 12.0, "2 um per shielded net"),
        ("ctrl W -> AFE S", "ana_ctrl[2:0] -> decoder -> 4 x r1_ls -> c1..c4", 7, "chan_sw", 39.7, "ls cells and decoder inside chan_sw"),
        ("isense W -> ADC E", "outa_p/n, outb_p/n (shielded) + vref, vcm, ibias_a/b in", 8, "chan_e -> chan_se", 20.0, "crosses the 68 ctrl->safe lines at right angles (M3 over M4)"),
        ("bgr -> t2f, safe, ADC", "vref, pbias, pcasc; vref to safe and ADC vref_in", 5, "south routing strip y 361-371 (try d)", 10.0, "as try d"),
        ("bias -> AFE, safe, isense", "ib_s1/2, ib_c1/2, ibias_oa/na/ob/nb, ibias_a/b", 10, "chan_sw, south strip, chan_e", 10.0, "bias block pending"),
        ("pads 19-20 -> ctrl W", "SDI, EN", 2, "west band x 321-331 + chan_sw", 10.0, "as try d"),
        ("pads 13-18 -> ctrl N / gate_lv", "gates, CS_N, MA_SCLK, SLO_SDO, PWM", 9, "north band (try d)", 31.7, "routed in try d"),
        ("pads 8-11 -> isense E", "ISA_P/N, ISB_P/N", 4, "east band x 1269-1279", 10.0, "Kelvin lines, 2 um pitch"),
        ("ctrl -> pad 12", "FAULT_N", 1, "north band", 31.7, "as try d"),
    ]

def cand_c1():
    """Best 1.6 mm candidate: try-d topology, r1_safe re-shaped into the east column."""
    c = cand_c0()
    r = [x for x in c["rects"]]
    r.append(B("r1_safe", "reshape", 1088.8, 376, 175.2, 409.6, note="r1_safe re-shaped 175.2 x 409.6 (same 0.0718 mm2)"))
    c.update(id="c1", title="C1: try-d topology, r1_safe re-shaped to 175 x 410 um (east column)", rects=r, unplaced={},
             needs=["r1_safe re-layout to <= 175.2 x 409.6 um, codes and flags on the west edge (layout only)",
                    "r1_ctrl 0.5 pin template: ADC pins on the south edge over x 556-995, safe pins on the east edge over y 376-786 (re-harden at the same 520 x 664)",
                    "ring ECO on the east columns over r1_isense and r1_osc (TopMetal2 only, as on the west)",
                    "r1_osc revision 2: osc_clk on the west edge",
                    "ADC slot 439 x 182.3 um"])
    return c

def cand_c2():
    """Digital macro in landscape (664 x 520, re-hardened), all analog except the AFE in one south band."""
    die = 1600.0; r = []
    r.append(R("trunk_s", "band", 331, 331, 1269, 371))
    r.append(R("nband", "rband", 405, 1237.3, 1195, 1269))
    r.append(B("r1_afe", "ana", 336, 727.3, 192.8, 494.4, mim=True))
    r.append(R("chan_afe", "chan", 331, 707.3, 533.8, 722.3, nets=13, pitch=1.15, dir="h", note="AFE out -> ADC N, c1..c4, bias"))
    r.append(R("strip_w", "strip", 533.8, 717.3, 543.8, 1237.3))
    r.append(B("r1_ctrl", "dig", 543.8, 717.3, 664, 520, note="re-hardened landscape"))
    r.append(R("strip_s", "strip", 533.8, 707.3, 1207.8, 717.3))
    r.append(R("chan_e", "chan", 1207.8, 707.3, 1269, 1237.3, nets=8, pitch=2.0, dir="v", note="pads 8-12 down to the south band"))
    r.append(B("r1_bgr", "ana", 336, 376, 96, 194.3))
    r.append(B("r1_t2f", "ana", 336, 580.3, 92, 102.6))
    r.append(adc(442, 376, h=326.3))
    r.append(B("r1_safe", "ana", 697.2, 376, 249.34, 287.81))
    r.append(B("r1_isense", "reshape", 956.6, 376, 296.8, 158.4, mim=True, note="r1_isense rotated, inputs re-pinned to the east short edge"))
    r.append(B("r1_osc", "reshape", 956.6, 544.4, 154.4, 118.4, mim=True, note="pins re-placed on the north edge"))
    r.append(B("r1_bias", "slot", 1121.1, 544.4, 80, 75))
    r.append(B("r1_por", "slot", 1211.1, 544.4, 52.8, 56.8))
    r.append(B("decap_vdda", "decap", 1121.1, 629.4, 142.9, 72.9, mim=True))
    r.append(B("r1_gate_lv", "ana", 338, 1233, 28.39, 27.9))
    pins = {21: ("r1_afe", 336, 766.1), 22: ("r1_afe", 336, 770.1), 23: ("r1_afe", 336, 1046.1), 24: ("r1_afe", 336, 1050.1),
            8: ("r1_isense", 1253.4, 440), 9: ("r1_isense", 1253.4, 444), 10: ("r1_isense", 1253.4, 470), 11: ("r1_isense", 1253.4, 474)}
    links = [
        ("ctrl S -> ADC N", "35 ADC lines", 35, "strip_s + halo 15 um, ADC edge under ctrl x 543.8-687", 15.0, "pitch-matched, 4.1 um pitch"),
        ("ctrl S -> safe N", "64 codes + 4 flags", 68, "strip_s + halo", 15.0, "native safe pin side (codes on top), pitch-matched"),
        ("ctrl S -> isense N, osc N", "az x 4, clk, trim x 5", 10, "strip_s + halo", 15.0, "re-pinned blocks"),
        ("AFE S -> ADC N", "5 shielded", 5, "chan_afe 15 um", 15.0, "short"),
        ("isense -> ADC E", "4 shielded + refs", 8, "south routing strip y 361-371, 400 um", 10.0, "long analog route under safe"),
        ("pads 8-11 -> isense E", "Kelvin lines", 4, "chan_e 61 um, up to 540 um long", 61.2, "long"),
    ]
    return dict(id="c2", die=die, title="C2: r1_ctrl landscape 664 x 520 (re-hardened), analog in one south band", rects=r,
                pins=pins, unplaced={}, swap=False, links=links,
                needs=["r1_ctrl 0.5 re-hardened at DIE_AREA 0 0 664 520 with all analog-facing pins on the south edge",
                       "r1_isense re-layout as 296.8 x 158.4 with inputs on the east short edge",
                       "r1_osc pins on the north edge", "gate_lv in the north-west ring-band corner",
                       "ring ECO on the east columns over r1_isense (south end)"])

def cand_c3():
    """S6 item 6 pin-map change: AFE in the south-west corner next to the ADC; safe re-shaped as C1."""
    die = 1600.0; r = []
    r.append(R("trunk_s", "band", 331, 331, 1269, 371))
    r.append(R("nband", "rband", 405, 1237.3, 1195, 1269))
    r.append(B("r1_afe", "ana", 336, 400, 192.8, 494.4, mim=True))
    r.append(R("chan_afe", "chan", 331, 371, 551, 395, nets=13, pitch=1.6, dir="h", note="AFE out -> ADC W, c1..c4, bias"))
    r.append(R("strip_w", "strip", 533.8, 573.3, 543.8, 1237.3))
    r.append(R("chan_wv", "chan", 533.8, 395, 551, 573.3, nets=5, pitch=2.0, dir="v"))
    r.append(B("r1_ctrl", "dig", 543.8, 573.3, 520, 664))
    r.append(R("strip_s", "strip", 551, 563.3, 1063.8, 573.3))
    r.append(R("chan_e", "chan", 1063.8, 563.3, 1083.8, 1237.3, nets=10, pitch=2.0, dir="v"))
    r.append(B("r1_safe", "reshape", 1088.8, 376, 175.2, 409.6))
    r.append(B("r1_isense", "ana", 1088.8, 795.8, 158.4, 296.8, mim=True))
    r.append(B("r1_osc", "ana", 1088.8, 1102.6, 154.4, 118.4, mim=True))
    r.append(adc(556, 376, h=182.3))
    r.append(B("decap_vdda", "decap", 1005, 376, 73.8, 102.6, mim=True))
    r.append(R("chan_se", "chan", 1000, 483.6, 1083.8, 563.3, nets=10, pitch=2.0, dir="h"))
    # north-west pocket above the AFE
    r.append(B("r1_bgr", "ana", 336, 904.4, 96, 194.3))
    r.append(B("r1_t2f", "ana", 336, 1108.7, 92, 102.6))
    r.append(B("r1_bias", "slot", 442, 904.4, 86.8, 69.7))
    r.append(B("r1_por", "slot", 442, 1060, 55, 55))
    r.append(B("r1_gate_lv", "ana", 440, 1196, 28.39, 27.9))
    pins = {19: ("r1_afe", 336, 438.8), 20: ("r1_afe", 336, 442.8), 21: ("r1_afe", 336, 718.8), 22: ("r1_afe", 336, 722.8),
            8: ("r1_isense", 1247.2, 836.6), 9: ("r1_isense", 1247.2, 839.8), 10: ("r1_isense", 1247.2, 981.4),
            11: ("r1_isense", 1247.2, 984.6)}
    lk = links_c1()
    lk[4] = ("AFE S -> ADC W", "5 shielded", 5, "chan_afe 24 um + chan_wv 17 um", 17.2, "short, no digital crossing")
    lk[7] = ("bgr -> t2f, safe, ADC", "vref (high impedance, 90-200 kOhm)", 5, "west band x 321-331 down, south strip east: about 1100 um", 10.0, "long vref route (risk)")
    lk[9] = ("pads 23-24 -> ctrl W", "SDI, EN", 2, "straight east above the AFE", 10.0, "short")
    return dict(id="c3", die=die, title="C3: pin-map swap (S6 item 6), AFE in the south-west corner, r1_safe re-shaped",
                rects=r, pins=pins, unplaced={}, swap=True, links=lk,
                needs=["pin-map change on the west side (spec section 3, T6 ring and bond-plan rerun)",
                       "r1_safe re-layout to <= 175.2 x 409.6 um (as C1)", "r1_ctrl 0.5 pin template (as C1)",
                       "long vref route from the north-west pocket"])

def cand_c4():
    """1.7 mm die, try-d topology, every macro as laid out (no re-shape)."""
    die = 1700.0; r = []
    r.append(R("trunk_s", "band", 331, 331, 1369, 371))
    r.append(R("nband", "rband", 455, 1337.3, 1245, 1369))
    r.append(B("r1_afe", "ana", 336, 720, 192.8, 494.4, mim=True))
    r.append(R("chan_sw", "chan", 331, 575.3, 543.8, 715, nets=15, pitch=1.5, dir="h"))
    r.append(R("strip_w", "strip", 533.8, 715, 543.8, 1337.3))
    r.append(B("r1_ctrl", "dig", 543.8, 673.3, 520, 664))
    r.append(R("strip_s", "strip", 543.8, 663.3, 1063.8, 673.3))
    r.append(R("chan_e", "chan", 1063.8, 663.3, 1083.8, 1337.3, nets=10, pitch=2.0, dir="v"))
    r.append(B("r1_safe", "ana", 1088.8, 376, 249.34, 287.81))
    r.append(R("chan_safe", "chan", 1083.8, 668.9, 1369, 730, nets=68, pitch=0.84, dir="h", note="safe codes (native top edge) to chan_e"))
    r.append(B("r1_isense", "ana", 1088.8, 735, 158.4, 296.8, mim=True))
    r.append(B("r1_osc", "ana", 1088.8, 1041.8, 154.4, 118.4, mim=True))
    r.append(B("r1_bgr", "ana", 336, 376, 96, 194.3))
    r.append(B("r1_t2f", "ana", 442, 376, 92, 102.6))
    r.append(B("r1_bias", "slot", 442, 488.6, 87, 69.7))
    r.append(R("chan_swv", "chan", 539, 371, 551, 575.3, nets=5, pitch=2.0, dir="v"))
    r.append(R("chan_link", "chan", 437, 563.3, 539, 575.3, nets=5, pitch=2.0, dir="h"))
    r.append(adc(556, 376, h=282.3))
    r.append(B("decap_vdda", "decap", 849.4, 376, 150, 102.6, mim=True))
    r.append(R("chan_se", "chan", 844.4, 483.6, 1083.8, 663.3, nets=10, pitch=2.0, dir="h"))
    r.append(B("r1_gate_lv", "ana", 440, 1300, 28.39, 27.9))
    r.append(B("r1_por", "slot", 345, 1270, 55, 55))
    pins = {21: ("r1_afe", 336, 758.8), 22: ("r1_afe", 336, 762.8), 23: ("r1_afe", 336, 1038.8), 24: ("r1_afe", 336, 1042.8),
            8: ("r1_isense", 1247.2, 775.8), 9: ("r1_isense", 1247.2, 779.0), 10: ("r1_isense", 1247.2, 920.6),
            11: ("r1_isense", 1247.2, 923.8)}
    lk = links_c1()
    lk[1] = ("ctrl E -> safe N", "64 codes + 4 flags (codes on the safe top edge, native)", 68, "chan_safe 61 um + chan_e", 61.2, "no pin template needed: 68 tracks at 0.84 um")
    return dict(id="c4", die=die, title="C4: 1.7 mm die, try-d topology, macros as laid out", rects=r, pins=pins,
                unplaced={}, swap=False, links=lk, needs=["T6 ring and bond plan at 1700 um", "r1_ctrl 0.5 pin template (recommended, not required)"])

def levers(c, cid, title):
    """Two area levers on top of a candidate: (1) VDDA decoupling as MIM over the south Metal4 trunks, under the
    TopMetal2 ring rows (x 371 to the east TopMetal1 column - 1.64 um, y 332-360), thick-oxide MOS under it on
    Metal1/2; nothing of it in the window. (2) r1_osc at the revision-2 working-tree size 148.2 x 110.4 um
    (its MIM then stays 1.64 um clear of the east TopMetal1 column: no ring ECO over the oscillator)."""
    r = [x for x in c["rects"] if x["name"] not in ("decap_vdda", "r1_osc")]
    x1 = ring(c["die"])["tm1_cols"][1][0] - 2.0
    r.append(R("decap_vdda", "overlay", 371, 332, x1, 360, note="MIM over the trunks, under the TopMetal2 ring rows"))
    o = [x for x in c["rects"] if x["name"] == "r1_osc"][0]
    r.append(B("r1_osc", "slot", o["box"][0], o["box"][1], 148.2, 110.4, mim=True, note="osc revision 2 slot"))
    n = dict(c); n.update(id=cid, title=title, rects=r, need={"r1_osc": 0.01636},
                          needs=c["needs"] + ["VDDA decoupling as MIM (+ thick-oxide MOS) over the south trunks under the TopMetal2 ring rows (new integration rule; DRC not run)",
                                              "r1_osc revision 2 at <= 148.2 x 110.4 um"])
    return n

def cand_c5():
    return levers(cand_c3(), "c5", "C5: C3 + VDDA decap in the south ring band + osc revision 2")

def cand_c6():
    return levers(cand_c1(), "c6", "C6: C1 + VDDA decap in the south ring band + osc revision 2")

# ------------------------------------------------------------------ checks
def area(b): return max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1]) / 1e6
def grow(b, d): return (b[0] - d, b[1] - d, b[2] + d, b[3] + d)
def inter(a, b): return a[0] < b[2] - 1e-6 and b[0] < a[2] - 1e-6 and a[1] < b[3] - 1e-6 and b[1] < a[3] - 1e-6
def inside(a, w): return a[0] >= w[0] - 1e-6 and a[1] >= w[1] - 1e-6 and a[2] <= w[2] + 1e-6 and a[3] <= w[3] + 1e-6
HALOED = ("ana", "slot", "reshape", "decap")

def occ(r):
    return grow(r["box"], HALO) if r["kind"] in HALOED else r["box"]

def solid(rs):
    return [r for r in rs if r["kind"] != "overlay"]

def check(c):
    g = ring(c["die"]); rs = c["rects"]; ext = g["ext"]
    win = area(ext)
    ov = [(a["name"], b["name"]) for a, b in itertools.combinations(solid(rs), 2) if inter(occ(a), occ(b))]
    out = [r["name"] for r in rs if not inside(occ(r), ext)]
    dig_out = [r["name"] for r in rs if r["kind"] == "dig" and not inside(r["box"], g["cons"])]
    eco = []
    for r in rs:
        if r.get("mim"):
            for (x0, x1) in g["tm1_cols"]:
                if r["box"][0] < x1 and r["box"][2] > x0:
                    eco.append({"block": r["name"], "column_x": [x0, x1], "y": [r["box"][1] - HALO, r["box"][3] + HALO]})
    have = {}
    for r in rs:
        have[r["name"]] = have.get(r["name"], 0.0) + area(r["box"])
    short = dict(c["unplaced"])
    need = dict(NEED); need.update(c.get("need", {}))
    for k, v in need.items():
        if k in short: continue
        if have.get(k, 0.0) + 2e-4 < v:
            short[k] = round(v - have.get(k, 0.0), 4)
    by = {}
    for r in solid(rs): by[r["kind"]] = by.get(r["kind"], 0.0) + area(r["box"])
    halo = sum(area(occ(r)) - area(r["box"]) for r in rs if r["kind"] in HALOED)
    used = sum(area(occ(r)) for r in solid(rs))
    req = used + sum(short.values())
    analog = sum(area(r["box"]) for r in rs if r["kind"] in ("ana", "slot", "reshape") and r["name"] not in ("r1_bias", "r1_por"))
    analog += sum(v for k, v in short.items() if k not in ("decap_vdda",))
    chans = []
    for r in rs:
        if r["kind"] == "chan":
            b = r["box"]; span = (b[2] - b[0]) if r["dir"] == "v" else (b[3] - b[1])
            cap = int(span // r["pitch"])
            chans.append({"channel": r["name"], "width_um": round(span, 1), "pitch_um": r["pitch"], "capacity": cap,
                          "nets": r["nets"], "ok": cap >= r["nets"], "note": r.get("note", "")})
    pd = pads(c["die"])
    if c.get("swap"): swap_west(pd)
    pr = []
    for k, (blk, x, y) in sorted(c["pins"].items()):
        ex, ey = pd[k]["edge"]
        pr.append({"pad": k, "net": pd[k]["net"], "block": blk, "manhattan_um": round(abs(ex - x) + abs(ey - y), 1)})
    return {"id": c["id"], "title": c["title"], "die_um": c["die"], "window_extended_mm2": round(win, 4),
            "overlaps": ov, "outside_extended_window": out, "digital_outside_conservative": dig_out,
            "ring_eco_tm2_over_mim": eco, "area_by_kind_mm2": {k: round(v, 4) for k, v in by.items()},
            "halo_mm2": round(halo, 4), "occupied_mm2": round(used, 4), "shortfall_mm2": short,
            "required_mm2": round(req, 4), "white_mm2": round(win - used, 4),
            "margin": round(1 - req / win, 4), "analog_sum_mm2": round(analog, 4),
            "channels": chans, "links": [list(l) for l in c["links"]], "pad_routes": pr, "needs": c["needs"],
            "rects": [[r["name"], r["kind"]] + [round(v, 2) for v in r["box"]] for r in rs]}

# ------------------------------------------------------------------ drawing
LAY = {"overlay": 215, "dig": 210, "ana": 211, "slot": 219, "reshape": 219, "strip": 212, "chan": 213, "band": 214, "decap": 215, "rband": 218}

def draw(c, res, outdir):
    g = ring(c["die"]); die = c["die"]
    ly = db.Layout(); ly.dbu = 0.001
    top = ly.create_cell("s7_" + c["id"])
    L = lambda n: ly.layer(n, 0)
    bx = lambda b: db.DBox(*b)
    top.shapes(L(200)).insert(bx((0, 0, die, die)))
    for b in [(141, 141, die - 141, IO_IN), (141, die - IO_IN, die - 141, die - 141),
              (141, IO_IN, IO_IN, die - IO_IN), (die - IO_IN, IO_IN, die - 141, die - IO_IN)]:
        top.shapes(L(201)).insert(bx(b))
    rb = db.Region(db.DBox(324.8, 324.8, die - 324.8, die - 324.8).to_itype(0.001)) - \
         db.Region(db.DBox(*g["cons"]).to_itype(0.001))
    top.shapes(L(202)).insert(rb)
    top.shapes(L(203)).insert(bx(g["cons"]))
    pd = pads(die)
    if c.get("swap"): swap_west(pd)
    for k, p in pd.items():
        x, y = p["centre"]
        top.shapes(L(204)).insert(bx((x - 35, y - 35, x + 35, y + 35)))
        top.shapes(L(230)).insert(db.DText("%d %s" % (k, p["net"]), db.DTrans(x - 30, y)))
    for r in c["rects"]:
        top.shapes(L(LAY[r["kind"]])).insert(bx(r["box"]))
        if r["kind"] in HALOED:
            top.shapes(L(217)).insert(db.Region(bx(occ(r)).to_itype(0.001)) - db.Region(bx(r["box"]).to_itype(0.001)))
        b = r["box"]
        if r["kind"] not in ("band", "rband", "strip"):
            top.shapes(L(230)).insert(db.DText(r["name"].replace("r1_", ""), db.DTrans(b[0] + 3, (b[1] + b[3]) / 2)))
    for e in res["ring_eco_tm2_over_mim"]:
        top.shapes(L(216)).insert(bx((e["column_x"][0], e["y"][0], e["column_x"][1], e["y"][1])))
    sh = sum(res["shortfall_mm2"].values())
    if sh > 0:
        s = (sh * 1e6) ** 0.5
        top.shapes(L(220)).insert(bx((die + 40, 0, die + 40 + s, s)))
        top.shapes(L(230)).insert(db.DText("shortfall %.3f mm2" % sh, db.DTrans(die + 45, s + 20)))
    lbl = ("does not fit (%s not placed)" % ", ".join(c["unplaced"])) if c["unplaced"] else ("margin %.1f %%" % (100 * res["margin"]))
    top.shapes(L(230)).insert(db.DText("%s  %s" % (c["title"][:3], lbl), db.DTrans(20, die - 60)))
    gds = os.path.join(outdir, "s7_%s.gds" % c["id"])
    ly.write(gds)
    import klayout.lay as lay_
    v = lay_.LayoutView(); v.load_layout(gds, True)
    cols = {200: 0x000000, 201: 0xb0b0b0, 202: 0xd8c070, 203: 0x707070, 204: 0x404040, 210: 0x3060c0, 211: 0x30a050,
            219: 0xe0b020, 212: 0xe08020, 213: 0xa040a0, 214: 0x806040, 215: 0x60c0c0, 216: 0xff40ff, 217: 0x90d090,
            218: 0xc0a080, 220: 0xd02020, 230: 0x000000}
    for n, col in cols.items():
        lp = lay_.LayerPropertiesNode(); lp.source = "%d/0" % n
        lp.fill_color = col; lp.frame_color = col
        lp.dither_pattern = 0 if n in (210, 211, 219, 220) else (1 if n in (200, 203) else 5)
        v.insert_layer(v.end_layers(), lp)
    v.set_config("background-color", "#ffffff"); v.set_config("grid-visible", "false")
    v.set_config("text-font", "1"); v.set_config("default-text-size", "12")
    v.max_hier(); v.zoom_box(db.DBox(-20, -20, die + (300 if sh > 0 else 20), die + 20))
    png = os.path.join(outdir, "s7_%s.png" % c["id"])
    v.save_image(png, 860, 860 if sh <= 0 else 700)
    res["gds"] = os.path.basename(gds); res["png"] = os.path.basename(png)

if __name__ == "__main__":
    outdir = sys.argv[1]; os.makedirs(outdir, exist_ok=True)
    allr = {}
    for f in (cand_c0, cand_c1, cand_c2, cand_c3, cand_c4, cand_c5, cand_c6):
        c = f(); res = check(c); draw(c, res, outdir); allr[c["id"]] = res
        print(c["id"], "margin %.2f %%" % (100 * res["margin"]), "req", res["required_mm2"], "win", res["window_extended_mm2"],
              "short", res["shortfall_mm2"], "ov", res["overlaps"], "out", res["outside_extended_window"],
              "digout", res["digital_outside_conservative"], "analog", res["analog_sum_mm2"],
              "chan_fail", [x["channel"] for x in res["channels"] if not x["ok"]])
    with open(os.path.join(outdir, "s7_floorplan.json"), "w") as fh:
        json.dump(allr, fh, indent=1)
