# SPDX-License-Identifier: Apache-2.0
"""r1_top try g, filled-chip extraction (track T11b): fill correction of the sensitive nets for top_netlist.py.

  python3 fill_net.py <fill run dir (band_<tag>_fill, band_<tag>_nofill)> <full-chip kpex dir> <out json> <tag> [...]

Method (per-net band method, extension of pex/fill_eff.py to the whole sensitive-net set):
  1. For each net group (GROUPS below) top_wire.py --band writes the wiring within BAND um of the group nets, once
     with the metal fill of asm-20261028-g3-fill (datatype 22, floating) and once without; kpex 2.5D CC on both.
  2. Net classes as fill_eff.py: named nets (labels), other wiring pieces (pieces clipped by the band; AC ground),
     fill (floating). The Maxwell matrix of each band run is reduced over the floating fill (Schur complement).
  3. For every sensitive net s of the group: the row of the effective matrix with fill minus the row without fill
     gives the fill delta of the coupling to every named net t (delta_st) and of the total C (delta_s). The part of
     delta_s not in a named coupling (clipped pieces, substrate) goes to VSUBS.
  4. A pair of two sensitive nets of different groups gets the mean of the two row estimates (one per band run) when
     both exist. The VSUBS delta of each sensitive net is then set so that its total C change equals its own band
     result exactly.
  5. Window check: the C of every sensitive net in the band run without fill is compared with the full-chip kpex
     (the band must not lose coupling of the unfilled layout).
Output: <out json> with pair_delta_fF ([a, b, delta]), sensitive_nets, per-net table (C full chip / band nofill /
band fill, delta, P-N couplings), window check, class counts per band.
"""
import csv
import json
import os
import sys
from collections import defaultdict

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spl
import klayout.db as db

P, KFULL, OUTF = sys.argv[1:4]
TAGS = sys.argv[4:]
GROUPS = {
    "clk": ["OSC_CLK", "VREF_B", "VREF_BG", "CUR_TRK", "POR_N"],
    "ana": ["AFE_SOUTS_P", "AFE_SOUTS_N", "AFE_SOUTC_P", "AFE_SOUTC_N", "ISN_OUTA_P", "ISN_OUTA_N", "ISN_OUTB_P",
            "ISN_OUTB_N"],
    "tap": ["TAP_%s_%d" % (pn, i) for i in range(32) for pn in "PN"],
    "bus": ["ADC_RAW_%s_%d" % (ab, i) for i in range(14) for ab in "AB"] +
           ["ADC_VALID_A", "ADC_VALID_B", "ADC_START", "ADC_SEL", "ADC_HOLD", "IS_SMP"],
}
GROUPS["clk20"] = GROUPS["clk"]
MET = [("metal1_con", 8), ("metal2_con", 10), ("metal3_con", 30), ("metal4_con", 50), ("metal5_n_cap", 67),
       ("topmetal1_con", 126), ("topmetal2_con", 134)]
VIA = [("via1_drw", 19, 0, 1), ("via2_drw", 29, 1, 2), ("via3_drw", 49, 2, 3), ("via4_drw", 66, 3, 4),
       ("topvia1_n_cap", 125, 4, 5), ("topvia2_drw", 133, 5, 6)]
TXT = {8: "metal1_text", 10: "metal2_text", 30: "metal3_text", 50: "metal4_text", 67: "metal5_text",
       126: "topmetal1_text", 134: "topmetal2_text"}


def extract(gds):
    ly = db.Layout()
    ly.read(gds)
    top = ly.cell("r1_top_wire")
    lvs = db.LayoutVsSchematic(db.RecursiveShapeIterator(ly, top, []))
    M = []
    for nm, l in MET:
        r = lvs.make_layer(ly.layer(l, 0), nm)
        M.append((l, r))
        lvs.connect(r)
        t = lvs.make_text_layer(ly.layer(l, 25), TXT[l])
        lvs.connect(r, t)
    for nm, l, a, b in VIA:
        v = lvs.make_layer(ly.layer(l, 0), nm)
        lvs.connect(v)
        lvs.connect(M[a][1], v)
        lvs.connect(v, M[b][1])
    lvs.extract_netlist()
    return ly, top, lvs, M


def classify(gds, ref_gds=None):
    """as fill_eff.py: named / wire / fill; with ref_gds (the band without fill) a net touching a reference shape is
    wire, any other unnamed net is fill"""
    ly, top, lvs, M = extract(gds)
    c = lvs.netlist().circuit_by_name("r1_top_wire")
    kind = {}
    for n in c.each_net():
        kind[n.expanded_name()] = "named" if n.name else ("fill" if ref_gds else "wire")
    if ref_gds:
        rl = db.Layout()
        rl.read(ref_gds)
        rt = rl.cell("r1_top_wire")
        for l, r in M:
            li = rl.find_layer(l, 0)
            if li is None:
                continue
            for pg in db.Region(rt.begin_shapes_rec(li)).merged().each():
                p = None
                c0 = pg.bbox().center()
                if pg.inside(c0):
                    p = c0
                else:
                    for e in pg.each_edge():
                        m = db.Point((e.p1.x + e.p2.x) // 2, (e.p1.y + e.p2.y) // 2)
                        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                            q = db.Point(m.x + dx, m.y + dy)
                            if pg.inside(q):
                                p = q
                                break
                        if p is not None:
                            break
                if p is None:
                    continue
                n = lvs.probe_net(r, db.DPoint(p.x * ly.dbu, p.y * ly.dbu))
                if n is not None and kind.get(n.expanded_name()) == "fill":
                    kind[n.expanded_name()] = "wire"
    return kind


def load_pairs(d):
    kd = [os.path.join(d, "kpex", x) for x in os.listdir(os.path.join(d, "kpex"))][0]
    f = [x for x in os.listdir(kd) if x.endswith("_k25d_pex_netlist.csv")][0]
    out = []
    for row in csv.reader(open(os.path.join(kd, f)), delimiter=";"):
        if row and row[0].startswith("C"):
            out.append((row[1], row[2], float(row[3])))
    return out


def rows(d, kind, sens):
    """effective Maxwell rows (fF) of the sensitive nets: {s: {"total": C, "to": {named t: C_st}}}"""
    PR = load_pairs(d)
    nets = sorted(set([a for a, b, c in PR] + [b for a, b, c in PR]))
    flo = [n for n in nets if kind.get(n) == "fill"]
    fset = set(flo)
    keep = [n for n in nets if n not in fset and n != "VSUBS"]
    idx = {n: i for i, n in enumerate(keep + flo)}
    N = len(idx)
    I, J, V = [], [], []
    for a, b, c in PR:
        if a == "VSUBS" or b == "VSUBS":
            n = b if a == "VSUBS" else a
            I.append(idx[n]); J.append(idx[n]); V.append(c)
            continue
        i, j = idx[a], idx[b]
        I += [i, j, i, j]
        J += [i, j, j, i]
        V += [c, c, -c, -c]
    M = sp.coo_matrix((V, (I, J)), shape=(N, N)).tocsc()
    k = len(keep)
    si = [idx[s] for s in sens if s in idx and idx[s] < k]
    S = [s for s in sens if s in idx and idx[s] < k]
    Mks = M[:k, :][:, si].toarray()
    if flo:
        Mkf = M[:k, k:]
        Mff = M[k:, k:] + sp.identity(N - k, format="csc") * 1e-9     # 1e-9 fF: a fill piece with no C at all
        lu = spl.splu(Mff.tocsc())
        X = lu.solve(Mkf.T.tocsc()[:, si].toarray())
        Mks = Mks - Mkf @ X
    out = {}
    for col, s in enumerate(S):
        r = {"total": float(Mks[idx[s], col]), "to": {}, "to_wire": 0.0}
        for t, i in idx.items():
            if i >= k or t == s:
                continue
            c = -float(Mks[i, col])
            if kind.get(t) == "named" and t != "T11_SUBTAP":
                if abs(c) > 1e-6:
                    r["to"][t] = c
            else:
                r["to_wire"] += c
        out[s] = r
    return out, {"nets": len(nets), "fill_nets": len(flo), "kept_nets": k}


# full-chip kpex totals (unfilled, of record)
full_tot = defaultdict(float)
full_pair = defaultdict(float)
fcsv = [f for f in os.listdir(KFULL) if f.endswith("_k25d_pex_netlist.csv")][0]
for row in csv.reader(open(os.path.join(KFULL, fcsv)), delimiter=";"):
    if row and row[0].startswith("C"):
        a, b, c = row[1], row[2], float(row[3])
        full_tot[a] += c
        full_tot[b] += c
        full_pair[tuple(sorted((a, b)))] += c

res = {"method": __doc__.strip().splitlines()[0], "bands": {}, "nets": {}}
est = defaultdict(list)          # (a, b) sorted -> [delta estimates]
own = {}                         # s -> (tag, delta total)
for tag in TAGS:
    sens = GROUPS[tag]
    bf, bn = os.path.join(P, "band_%s_fill" % tag), os.path.join(P, "band_%s_nofill" % tag)
    kf = classify(os.path.join(bf, "r1_top_wire.gds"), os.path.join(bn, "r1_top_wire.gds"))
    kn = classify(os.path.join(bn, "r1_top_wire.gds"))
    rf, cf = rows(bf, kf, sens)
    rn, cn = rows(bn, kn, sens)
    res["bands"][tag] = {"fill": cf, "nofill": cn,
                         "class_counts_fill": {q: sum(1 for v in kf.values() if v == q) for q in ("named", "wire", "fill")}}
    for s in sens:
        if s not in rf or s not in rn:
            res["nets"].setdefault(s, {})["missing_in_band_" + tag] = True
            continue
        d_tot = rf[s]["total"] - rn[s]["total"]
        ent = {"band": tag, "C_full_chip_fF": round(full_tot.get(s, 0.0), 3), "C_band_nofill_fF": round(rn[s]["total"], 3),
               "C_band_fill_fF": round(rf[s]["total"], 3), "delta_fF": round(d_tot, 3),
               "window_err_pct": round(100 * (rn[s]["total"] - full_tot.get(s, 0.0)) / max(full_tot.get(s, 1e-9), 1e-9), 3),
               "C_filled_fF": round(full_tot.get(s, 0.0) + d_tot, 3)}
        if tag == "clk20":
            res["nets"].setdefault(s, {})["clk20"] = ent
            continue
        res["nets"].setdefault(s, {}).update(ent)
        own[s] = d_tot
        for t in set(rf[s]["to"]) | set(rn[s]["to"]):
            d = rf[s]["to"].get(t, 0.0) - rn[s]["to"].get(t, 0.0)
            est[tuple(sorted((s, t)))].append((s, d))
        # P-N couplings of the pairs, with and without fill
        for q in GROUPS[tag]:
            if q != s and q in rf[s]["to"] and s.endswith("_P") and q == s[:-2] + "_N":
                ent["C_to_N_nofill_fF"] = round(rn[s]["to"].get(q, 0.0), 3)
                ent["C_to_N_fill_fF"] = round(rf[s]["to"].get(q, 0.0), 3)
                ent["C_to_N_full_chip_fF"] = round(full_pair.get(tuple(sorted((s, q))), 0.0), 3)
SENS = sorted(own)
pd = {}
for k, L in est.items():
    a, b = k
    if a in own and b in own:
        # two sensitive nets: one estimate per row (mean over the rows that saw the pair)
        byrow = defaultdict(list)
        for s, d in L:
            byrow[s].append(d)
        pd[k] = float(np.mean([np.mean(v) for v in byrow.values()]))
    else:
        pd[k] = float(np.mean([d for s, d in L]))
for s in SENS:
    named = sum(d for (a, b), d in pd.items() if s in (a, b) and "VSUBS" not in (a, b))
    k = tuple(sorted((s, "VSUBS")))
    pd[k] = own[s] - named
    res["nets"][s]["delta_named_fF"] = round(named, 3)
    res["nets"][s]["delta_to_ground_fF"] = round(own[s] - named, 3)
res["sensitive_nets"] = SENS
res["pair_delta_fF"] = [[a, b, round(d, 6)] for (a, b), d in sorted(pd.items()) if abs(d) > 1e-6]
res["window_check_max_abs_err_pct"] = max(abs(res["nets"][s]["window_err_pct"]) for s in SENS)
json.dump(res, open(OUTF, "w"), indent=1)
for s in SENS:
    e = res["nets"][s]
    print("%-12s full %8.2f band-nofill %8.2f (%+.2f %%) fill %8.2f delta %+8.2f fF (%+.1f %%)" % (
        s, e["C_full_chip_fF"], e["C_band_nofill_fF"], e["window_err_pct"], e["C_band_fill_fF"], e["delta_fF"],
        100 * e["delta_fF"] / max(e["C_full_chip_fF"], 1e-9)))
print("pairs", len(res["pair_delta_fF"]), "window max err %", res["window_check_max_abs_err_pct"])
