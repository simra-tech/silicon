#!/usr/bin/env python3
"""Revision-4 static windows and the circuit-level weight calibration (MC), from run_points4.py runs.

usage: post_win4.py OUT.json --run <id> --nwin K [--inst m0,m1,...] [--fit top2|w0|w1] [--lsb V] [--label "..."]
The points file of the run holds K windows of equal length (frames in order). Per slice (and per MC instance):
  * design weights W_d (nominal AC-solved array, sim/results/r3/cdac3_mc50_tt_cp100_globalfit.json; the CDAC is
    unchanged in revision 4) -> codes;
  * --fit top2: reduced windowed fit (method W of sim/r3/cal3.py restricted to circuit data, as in revision 3):
    least squares of the input level (in LSB) against [one offset per window, b_0, b_1, g * sum_{j>=2} b_j W_d,j];
    W_0 = x_0/g, W_1 = x_1/g, lower weights stay W_d; scaled to sum 4095 LSB, quantised to 1/8 LSB (14 bit).
    --fit w0 / w1: only W_0 or only W_1 is fitted (the other weights stay W_d): a window set that holds only the
    decision-1 toggles (mcwin3.json in revision 4) or only the decision-0 toggle (mcwin0.json) identifies one weight.
    The fit and the DNL use the same conversions (no separate evaluation set; recorded in the README).
  * per code inside every window: width = conversions with that code / M (LSB), DNL = width - 1 (resolution
    1/M); the first and last code of a window are not counted; monotonicity and missing codes inside the window.
"""
import json
import os
import sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "r3"))
from p4common import load_segments, BLOCK
import cal3

out = sys.argv[1]
arg = lambda k, d=None: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
rid, nwin, fit = arg("--run"), int(arg("--nwin")), arg("--fit")
insts = arg("--inst", "").split(",") if arg("--inst") else [""]
LSB = float(arg("--lsb", "446.4e-6"))
root = os.environ["G1_RESULTS_ROOT"]
Wd_lsb = np.array(json.load(open(os.path.join(BLOCK, "sim", "results", "r3", "cdac3_mc50_tt_cp100_globalfit.json")))["nominal_design_weights_lsb"])
segj = os.path.join(BLOCK, "sim", "results", "r4", rid + "_segments.json")
S = json.load(open(segj))
P = json.load(open(os.path.join(BLOCK, S["points"])))
nper = len(P["a"]) // nwin
res = {"label": arg("--label", "simulated (tb_adc4_points.cir) + post_win4.py"), "run": rid, "nwin": nwin,
       "frames_per_window": nper, "samples": {}}


def windows(v, bits, slots):
    return [(v[(slots // nper) == w], bits[(slots // nper) == w], w) for w in range(nwin)]


summary = []
for inst in insts:
    slots, ba, bb = load_segments(segj, root, inst)
    for sl, bits in (("a", ba), ("b", bb)):
        v = np.array(P[sl])[slots]
        wins = windows(v, bits, slots)
        M = int(round(LSB / np.median(np.diff(np.sort(wins[0][0])))))
        sets = {"design": cal3.quantise(Wd_lsb)}
        if fit:
            FI = {"top2": [0, 1], "w0": [0], "w1": [1]}[fit]
            NF = [j for j in range(len(Wd_lsb)) if j not in FI]
            O = np.zeros((len(v), nwin))
            O[np.arange(len(v)), slots // nper] = 1
            low = bits[:, NF].astype(float) @ Wd_lsb[NF]
            A = np.column_stack([O] + [bits[:, j] for j in FI] + [low])
            x = np.linalg.lstsq(A, v / LSB, rcond=None)[0]
            g = x[-1]
            w = Wd_lsb.copy()
            for n, j in enumerate(FI):
                w[j] = x[nwin + n] / g
            sets["fit_" + fit] = cal3.quantise(w * 4095.0 / w.sum())
        r = {"conversions": int(len(v)), "points_per_lsb": M}
        for tag, W in sets.items():
            win = {}
            for vv, bb_, wi in wins:
                o = np.argsort(vv)
                c = cal3.code(bb_[o], W)
                codes, cnt = np.unique(c, return_counts=True)
                inner = codes[1:-1]
                widths = {int(k): float(n) / M for k, n in zip(codes, cnt) if k in inner}
                win[str(wi)] = {"codes": [int(c.min()), int(c.max())], "monotonic": bool(np.all(np.diff(c) >= 0)),
                                "missing_inside": int(np.sum(np.diff(c) > 1)),
                                "dnl_by_code": {k: round(x - 1, 3) for k, x in widths.items()},
                                "max_abs_dnl": float(max(abs(x - 1) for x in widths.values())) if widths else None}
            r[tag] = {"W": [int(x) for x in W], "windows": win,
                      "max_abs_dnl": max(x["max_abs_dnl"] for x in win.values() if x["max_abs_dnl"] is not None),
                      "monotonic": all(x["monotonic"] for x in win.values()),
                      "missing_inside": sum(x["missing_inside"] for x in win.values())}
        key = (inst + sl) if inst else sl
        res["samples"][key] = r
        summary.append((key, r))
TAGS = ("design", "fit_" + fit) if fit else ("design",)
for tag in TAGS:
    vals = [r[tag]["max_abs_dnl"] for _, r in summary if tag in r]
    if vals:
        res[tag + "_max_abs_dnl"] = {"median": float(np.median(vals)), "max": float(max(vals)), "n": len(vals),
                                     "n_le_0p5": int(sum(x <= 0.5 for x in vals)),
                                     "all_monotonic": all(r[tag]["monotonic"] for _, r in summary),
                                     "missing_total": int(sum(r[tag]["missing_inside"] for _, r in summary))}
json.dump(res, open(out, "w"), indent=1)
for key, r in summary:
    print(key, " ".join("%s max|DNL| %.2f mono %s miss %d W0/W1 %s" % (t, r[t]["max_abs_dnl"], r[t]["monotonic"], r[t]["missing_inside"], r[t]["W"][:2])
                        for t in TAGS if t in r))
for tag in TAGS:
    if tag + "_max_abs_dnl" in res:
        print(tag, res[tag + "_max_abs_dnl"])
