# SPDX-License-Identifier: Apache-2.0
"""r1_top try g, chip-level extraction (track T11): effect of the metal fill on the sensitive nets.

  python3 fill_eff.py <band_fill dir> <band_nofill dir> <filled chip gds> <out json>

Method: kpex 2.5D CC on a 10 um band around AFE_SOUTS_P/N, AFE_SOUTC_P/N, OSC_CLK and VREF_B (top_wire.py --band),
once with the metal fill of the filled chip (asm-20261028-g3-fill, datatype 22, floating) and once without.
The nets of the band layout are classified by geometry (same LayoutVsSchematic extraction as make_lvsdb.py, so the
net names are the names kpex uses): named nets (labels of top_wire.py), other wiring pieces (pieces of nets clipped
by the band, found by probing every shape of the band layout without fill; AC ground), fill (all other nets: the
fill of the filled chip, datatype 22, floating). The Maxwell
capacitance matrix of the kpex pair values is reduced over the floating fill nets (Schur complement), which gives
the total capacitance of each sensitive net and the P-N coupling with the fill floating.
"""
import csv
import json
import os
import sys

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spl
import klayout.db as db

BF, BN, FGDS, OUTF = sys.argv[1:5]   # FGDS: the filled chip (recorded; the fill classes come from BN)
SENS = ["AFE_SOUTS_P", "AFE_SOUTS_N", "AFE_SOUTC_P", "AFE_SOUTC_N", "OSC_CLK", "VREF_B"]
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
    """Net classes of a band layout. With ref_gds (the band layout without fill, same window): a net is wiring if it
    touches a shape of the reference layout, else it is fill (the fill keeps its spacing to the wiring, so a fill
    piece never touches it). The fill region of the filled chip (datatype 22) defines the fill; the band layout
    without fill is the same layout minus that fill."""
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
    P = []
    for row in csv.reader(open(os.path.join(kd, f)), delimiter=";"):
        if row and row[0].startswith("C"):
            P.append((row[1], row[2], float(row[3])))
    return P


def analyse(d, kind):
    P = load_pairs(d)
    nets = sorted(set([a for a, b, c in P] + [b for a, b, c in P]))
    flo = [n for n in nets if kind.get(n) == "fill"]
    fset = set(flo)
    keep = [n for n in nets if n not in fset and n != "VSUBS"]
    idx = {n: i for i, n in enumerate(keep + flo)}
    N = len(idx)
    I, J, V = [], [], []
    for a, b, c in P:
        c *= 1e-15
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
    kidx = {n: i for i, n in enumerate(keep)}
    Mkk = M[:k, :k]
    out = {"nets": len(nets), "fill_nets": len(flo), "kept_nets": k}
    if flo:
        Mkf = M[:k, k:]
        Mff = M[k:, k:]
        # floating fill pieces with no capacitance at all would make Mff singular: add 1e-24 F to ground
        Mff = Mff + sp.identity(Mff.shape[0], format="csc") * 1e-24
        lu = spl.splu(Mff.tocsc())
        si = [kidx[s] for s in SENS if s in kidx]
        X = lu.solve(Mkf.T.tocsc()[:, si].toarray())
        corr = Mkf @ X                           # k x len(si)
        Meff = Mkk[:, si].toarray() - corr
    else:
        si = [kidx[s] for s in SENS if s in kidx]
        Meff = Mkk[:, si].toarray()
    res = {}
    for col, s in enumerate([s for s in SENS if s in keep]):
        ctot = Meff[kidx[s], col]
        res[s] = {"C_total_fF": round(ctot * 1e15, 3)}
        for t in SENS:
            if t != s and t in keep:
                res[s]["C_to_%s_fF" % t] = round(-Meff[kidx[t], col] * 1e15, 4)
    out["sens"] = res
    return out


kf = classify(os.path.join(BF, "r1_top_wire.gds"), os.path.join(BN, "r1_top_wire.gds"))
kn = classify(os.path.join(BN, "r1_top_wire.gds"))
rf = analyse(BF, kf)
rn = analyse(BN, kn)
summ = {}
for s in SENS:
    a, b = rn["sens"].get(s), rf["sens"].get(s)
    if a and b:
        summ[s] = {"C_nofill_fF": a["C_total_fF"], "C_fill_fF": b["C_total_fF"],
                   "delta_fF": round(b["C_total_fF"] - a["C_total_fF"], 3),
                   "delta_pct": round(100 * (b["C_total_fF"] - a["C_total_fF"]) / a["C_total_fF"], 2)}
for p, n in (("AFE_SOUTS_P", "AFE_SOUTS_N"), ("AFE_SOUTC_P", "AFE_SOUTC_N")):
    summ[p[:-2] + "_pair"] = {
        "dC_nofill_fF": round(rn["sens"][p]["C_total_fF"] - rn["sens"][n]["C_total_fF"], 3),
        "dC_fill_fF": round(rf["sens"][p]["C_total_fF"] - rf["sens"][n]["C_total_fF"], 3),
        "C_PN_nofill_fF": rn["sens"][p]["C_to_%s_fF" % n], "C_PN_fill_fF": rf["sens"][p]["C_to_%s_fF" % n]}
r = {"method": __doc__.strip().splitlines()[0], "fill": rf, "nofill": rn, "summary": summ,
     "class_counts_fill": {k: sum(1 for v in kf.values() if v == k) for k in ("named", "wire", "fill")},
     "class_counts_nofill": {k: sum(1 for v in kn.values() if v == k) for k in ("named", "wire", "fill")}}
json.dump(r, open(OUTF, "w"), indent=1)
print(json.dumps(summ, indent=1))
print(r["class_counts_fill"], r["class_counts_nofill"])
