#!/usr/bin/env python3
"""S6 floorplan study for R1: rectangles only (no layout).

Writes one GDS per die (1414 um and 1600 um), a JSON summary and a PNG per die.
Usage (inside the pinned container, through flow/run.sh):
    python3 gen_s6_floorplan.py <out_dir>
All coordinates are um, lower-left die corner at the origin.
Layers (not PDK layers): 200 die, 201 IO row + corners, 202 core power ring band,
203 conservative core window (inside the ring), 204 bondpads, 210 digital macro,
211 analog block, 212 guard strip (guard rings + interface channel), 213 digital routing channel,
214 supply trunk, 215 decoupling, 220 shortfall (area that does not fit, drawn outside the die), 230 text.
"""
import json, os, sys, itertools
import klayout.db as db

IO_DEPTH = 180.0      # sg13g2_IOPad* cell 80 x 180 um (r1_padring record)
IO_IN = 321.0         # IO row inner edge from the die edge (r1_padring record)
RING_IN = 361.8       # core window starts 361.8 um from the die edge (r1_padring record; y side 362.16)
EXT_IN = 331.0        # G1 r4 macros start 331 um from the die edge (under the core ring; measured, g1check)
HALO = 5.0            # per-side keep-out around each analog block (allowance A1)

def pads(die):
    """Pad centres per side. 1414: G1 ring (pitch 112, first 395). 1600: same order, pitch 140, centred."""
    if die == 1414.0:
        pos = [395, 507, 619, 731, 843, 955]
    else:
        c = die / 2.0; pos = [c - 2.5 * 140 + 140 * i for i in range(6)]
    names = ["VDD", "VSS", "IOVDD", "IOVSS", "VSS", "IOVSS",           # 1-6 south, left to right
             "VDDA", "ISA_P", "ISA_N", "ISB_P", "ISB_N", "FAULT_N",     # 7-12 east, bottom to top
             "GATE_A", "GATE_B", "GATE_C", "CS_N", "MA_SCLK", "SLO_SDO",  # 13-18 north, left to right
             "SDI", "EN_STO_IN", "SIN_P", "SIN_N", "COS_P", "COS_N"]   # 19-24 west, bottom to top
    out = []
    for i, n in enumerate(names):
        side = ["S", "E", "N", "W"][i // 6]; p = pos[i % 6]
        xy = {"S": (p, 101.0), "E": (die - 101.0, p), "N": (p, die - 101.0), "W": (101.0, p)}[side]
        out.append((i + 1, n, side, p, xy))
    return out

# Block areas (mm2) used for the drawing, after the recommended cuts (C5 ADC decoupling, C6 AFE MIM stacking).
# r1_ctrl: 520 x 664 um macro = core 498.6 x 642.6 um (LibreLane margin 10.7 um, t6) at 75 % for 240 000 um2 placed.
NEED = {"r1_ctrl": 0.3453, "r1_afe": 0.069, "r1_adc": 0.050, "r1_bgr": 0.018, "r1_osc": 0.018,
        "r1_isense_a": 0.029, "r1_isense_b": 0.029, "r1_safe": 0.055, "r1_t2f": 0.0094,
        "r1_ls": 0.0014, "decap_vdda": 0.015}

# Placements: (name, kind, x0, y0, x1, y1). kind: dig, ana, strip, chan, trunk, decap.
# Gate pad routes (13-15) run in the core-ring band (Metal2-4 under the TopMetal ring), as on G1; no window area.
PLACE = {
 1600.0: [
  ("r1_ctrl", "dig", 511, 573, 1031, 1237),
  ("strip_w", "strip", 481, 543, 511, 1237), ("strip_s", "strip", 511, 543, 1031, 573),
  ("strip_e", "strip", 1031, 543, 1061, 1237), ("strip_ne", "strip", 1061, 1024, 1269, 1054),
  ("chan_sw_h", "chan", 331, 543, 481, 573), ("chan_sw_v", "chan", 331, 420, 371, 543),
  ("r1_afe", "ana", 336, 650, 476, 1143),
  ("r1_ls_afe", "ana", 341, 590, 441, 620),
  ("trunk_vdda", "trunk", 371, 331, 1269, 361), ("trunk_vdda_e", "trunk", 1249, 361, 1269, 470),
  ("r1_adc", "ana", 381, 366, 672, 538), ("r1_bgr", "ana", 682, 366, 787, 538),
  ("decap_vdda", "decap", 797, 366, 885, 538),
  ("r1_t2f", "ana", 895, 366, 987, 469), ("r1_ls_t2f", "ana", 895, 479, 955, 509),
  ("r1_safe", "ana", 1066, 366, 1246, 672), ("r1_isense_a", "ana", 1066, 682, 1246, 843),
  ("r1_isense_b", "ana", 1066, 853, 1246, 1014),
  ("r1_osc", "ana", 1076, 1064, 1246, 1170), ("decap_vdd_ne", "decap", 1076, 1180, 1246, 1237),
 ],
 1414.0: [
  ("r1_ctrl", "dig", 511, 573, 873, 1051),
  ("strip_w", "strip", 481, 543, 511, 1051), ("strip_s", "strip", 511, 543, 873, 573),
  ("strip_e", "strip", 873, 543, 903, 1051),
  ("chan_sw_h", "chan", 331, 543, 481, 573), ("chan_sw_v", "chan", 331, 380, 371, 543),
  ("r1_afe", "ana", 336, 583, 476, 1076),
  ("trunk_vdda", "trunk", 371, 331, 1083, 361),
  ("r1_adc", "ana", 381, 366, 672, 538), ("r1_bgr", "ana", 682, 366, 787, 538),
  ("r1_t2f", "ana", 797, 366, 889, 469), ("r1_ls_t2f", "ana", 797, 479, 857, 509),
  ("decap_vdda", "decap", 908, 366, 1073, 446),
  ("r1_isense_a", "ana", 908, 456, 1073, 632), ("r1_isense_b", "ana", 908, 642, 1073, 818),
  ("r1_safe", "ana", 908, 828, 1073, 1083),
 ],
}

def area(r): return (r[4] - r[2]) * (r[5] - r[3]) / 1e6

def overlaps(rs):
    bad = []
    for a, b in itertools.combinations(rs, 2):
        if a[2] < b[4] and b[2] < a[4] and a[3] < b[5] and b[3] < a[5]:
            bad.append((a[0], b[0]))
    return bad

def run(die, outdir):
    rs = PLACE[die]
    lo, hi = EXT_IN, die - EXT_IN
    out_of_window = [r[0] for r in rs if r[2] < lo - 1e-6 or r[3] < lo - 1e-6 or r[4] > hi + 1e-6 or r[5] > hi + 1e-6]
    ov = overlaps(rs)
    ext = (hi - lo) ** 2 / 1e6
    cons = (die - 361.8 - 359.58) * (die - 362.16 - 362.7) / 1e6  # 1414: 692.6 x 689.1 (padring record)
    placed = {}
    for r in rs:
        key = r[0].replace("_afe", "").replace("_t2f", "") if r[0].startswith("r1_ls") else r[0]
        placed[key] = placed.get(key, 0) + area(r)
    short = {}
    for k, v in NEED.items():
        got = placed.get(k, 0.0) if k not in ("decap_vdda",) else placed.get("decap_vdda", 0.0)
        if k == "r1_ls":
            got = placed.get("r1_ls", 0.0)
        if got + 1e-4 < v:
            short[k] = round(v - got, 4)
    kinds = {}
    for r in rs: kinds[r[1]] = kinds.get(r[1], 0) + area(r)
    halo = sum(2 * ((r[4] - r[2]) + (r[5] - r[3])) * HALO / 1e6 for r in rs if r[1] == "ana")
    drawn = sum(area(r) for r in rs)
    req = drawn + halo + sum(short.values())
    res = {"die_um": die, "window_extended_mm2": round(ext, 4), "window_conservative_mm2": round(cons, 4),
           "overlaps": ov, "outside_extended_window": out_of_window,
           "area_by_kind_mm2": {k: round(v, 4) for k, v in kinds.items()},
           "halo_allowance_mm2": round(halo, 4), "drawn_total_mm2": round(drawn, 4),
           "shortfall_mm2": short, "shortfall_total_mm2": round(sum(short.values()), 4),
           "required_mm2": round(req, 4),
           "margin_extended": round(1 - req / ext, 4), "margin_conservative": round(1 - req / cons, 4),
           "white_space_extended_mm2": round(ext - drawn, 4),
           "rects": [list(r) for r in rs], "pads": [[p[0], p[1], p[2], p[4][0], p[4][1]] for p in pads(die)]}
    # GDS
    ly = db.Layout(); ly.dbu = 0.001
    top = ly.create_cell("s6_fp_%d" % int(die))
    L = lambda n: ly.layer(n, 0)
    box = lambda x0, y0, x1, y1: db.DBox(x0, y0, x1, y1)
    top.shapes(L(200)).insert(box(0, 0, die, die))
    for x0, y0, x1, y1 in [(141, 141, die - 141, IO_IN), (141, die - IO_IN, die - 141, die - 141),
                           (141, IO_IN, IO_IN, die - IO_IN), (die - IO_IN, IO_IN, die - 141, die - IO_IN)]:
        top.shapes(L(201)).insert(box(x0, y0, x1, y1))
    reg = db.Region(db.Box(int(324.8e3), int(324.8e3), int((die - 324.8) * 1e3), int((die - 324.8) * 1e3))) - \
          db.Region(db.Box(int(361.8e3), int(362.16e3), int((die - 359.58) * 1e3), int((die - 362.7) * 1e3)))
    top.shapes(L(202)).insert(reg)
    top.shapes(L(203)).insert(box(361.8, 362.16, die - 359.58, die - 362.7))
    for p in pads(die):
        x, y = p[4]
        top.shapes(L(204)).insert(box(x - 35, y - 35, x + 35, y + 35))
        top.shapes(L(230)).insert(db.DText("%d %s" % (p[0], p[1]), db.DTrans(x - 30, y)))
    lay = {"dig": 210, "ana": 211, "strip": 212, "chan": 213, "trunk": 214, "decap": 215}
    for r in rs:
        top.shapes(L(lay[r[1]])).insert(box(*r[2:]))
        top.shapes(L(230)).insert(db.DText(r[0], db.DTrans((r[2] + r[4]) / 2 - 20, (r[3] + r[5]) / 2)))
    if short:
        s = sum(short.values()) * 1e6; side = s ** 0.5
        top.shapes(L(220)).insert(box(die + 50, 0, die + 50 + side, side))
        top.shapes(L(230)).insert(db.DText("shortfall %.3f mm2" % (s / 1e6), db.DTrans(die + 60, side / 2)))
    gds = os.path.join(outdir, "s6_floorplan_%d.gds" % int(die))
    ly.write(gds)
    res["gds"] = os.path.basename(gds)
    # PNG
    try:
        import klayout.lay as lay_
        v = lay_.LayoutView(); v.load_layout(gds, True)
        cols = {200: 0x000000, 201: 0xb0b0b0, 202: 0xd8c070, 203: 0x707070, 204: 0x404040, 210: 0x3060c0,
                211: 0x30a050, 212: 0xe08020, 213: 0xa040a0, 214: 0x806040, 215: 0x60c0c0, 220: 0xd02020, 230: 0x000000}
        for n, c in cols.items():
            lp = lay_.LayerPropertiesNode(); lp.source = "%d/0" % n
            lp.fill_color = c; lp.frame_color = c; lp.dither_pattern = 0 if n in (210, 211, 220) else (5 if n != 203 else 1)
            if n in (200, 203): lp.dither_pattern = 1
            v.insert_layer(v.end_layers(), lp)
        v.set_config("background-color", "#ffffff"); v.set_config("grid-visible", "false")
        v.set_config("text-font", "1"); v.set_config("default-text-size", "14")
        v.max_hier(); v.zoom_box(db.DBox(-20, -20, die + (480 if short else 20), die + 20))
        png = os.path.join(outdir, "s6_floorplan_%d.png" % int(die))
        v.save_image(png, 900, 760 if short else 900)
        res["png"] = os.path.basename(png)
    except Exception as e:
        res["png_error"] = repr(e)
    return res

if __name__ == "__main__":
    outdir = sys.argv[1]; os.makedirs(outdir, exist_ok=True)
    allr = {str(int(d)): run(d, outdir) for d in (1414.0, 1600.0)}
    with open(os.path.join(outdir, "s6_floorplan.json"), "w") as f:
        json.dump(allr, f, indent=1)
    for d, r in allr.items():
        print(d, {k: r[k] for k in r if k not in ("rects", "pads")})
