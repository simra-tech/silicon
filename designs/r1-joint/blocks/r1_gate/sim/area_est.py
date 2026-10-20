#!/usr/bin/env python3
"""Device-area based area estimate for r1_gate and r1_ls cells (host python 3.6).
Method: sum of W*L (um^2, times ng*m) per cell from the G1 netlists; calibrate um^2 of layout per um^2 of gate area
on two known G1 layouts (g1_ls_up cell 9.2 x 11.7 um, g1_gate macro 130.68 x 50.65 um); apply to the R1 cells.
The result is an ESTIMATE, not a layout."""
import re, json, sys
def parse(path):
    subs, cur = {}, None
    for line in open(path):
        line = line.strip()
        if line.startswith(".subckt"):
            cur = line.split()[1]; subs[cur] = {"dev": 0.0, "inst": {}}; continue
        if line.startswith(".ends"): cur = None; continue
        if cur is None or not line or line[0] in "*": continue
        t = line.split()
        if "sg13_" in line:
            w = float(re.search(r"w=([\d.]+)u", line).group(1)); l = float(re.search(r"l=([\d.]+)u", line).group(1))
            subs[cur]["dev"] += w * l
        elif t[0].startswith("X"):
            sub = t[-1]; subs[cur]["inst"][sub] = subs[cur]["inst"].get(sub, 0) + 1
    return subs
def total(subs, name):
    s = subs[name]; tot = s["dev"]
    for k, n in s["inst"].items(): tot += n * total(subs, k)
    return tot
g1 = parse("../schematic/g1_cells_copy.spice")
ls = parse("../../r1_ls/schematic/g1_ls_up_copy.spice")
dn = parse("../../r1_ls/schematic/g1_lvldn_copy.spice")
wl = {k: total(g1, k) for k in g1}
wl["g1_ls_up"] = total(ls, "g1_ls_up")
k_ls = 9.2 * 11.7 / wl["g1_ls_up"]
k_gate = 130.68 * 50.65 / wl["g1_gate"]
res = {"sumWL_um2": {k: round(v, 3) for k, v in wl.items()}, "k_ls_layout_per_WL": round(k_ls, 2), "k_gate_layout_per_WL": round(k_gate, 2)}
# R1 sets
hv = 4 * wl["g1_lvlup"] + 4 * wl["g1_hv_inv"] + 3 * wl["g1_hv_nor2"] + 3 * wl["g1_hv_inv"] + 3 * wl["g1_lvldn"]
lv = 3 * wl["g1_lv_nand2"] + 3 * wl["g1_lv_inv"]
res["r1_gate_hv_sumWL_um2"] = round(hv, 2); res["r1_gate_lv_sumWL_um2"] = round(lv, 2)
res["r1_gate_hv_area_um2_est"] = [round(hv * k_gate), round(hv * k_ls)]
res["r1_gate_lv_area_um2_est"] = [round(lv * k_gate), round(lv * k_ls)]
res["cells_um2_est(k_ls)"] = {k: round(wl[k] * k_ls, 1) for k in ("g1_lvlup", "g1_lvldn", "g1_hv_nor2", "g1_hv_inv", "g1_lv_inv", "g1_lv_nand2")}
res["g1_ls_up_um2_layout"] = round(9.2 * 11.7, 2)
print(json.dumps(res, indent=1))
