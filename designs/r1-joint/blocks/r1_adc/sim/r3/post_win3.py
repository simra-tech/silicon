#!/usr/bin/env python3
"""Revision-3 static windows (circuit results of run_points3.py) and the reduced circuit-level calibration demo.

usage: post_win3.py OUT.json --runs <id>[,<id>...] [--fit top2] [--label "..."]
Each run is one window (points file with "a" and "b" input levels around one major code, M points per LSB).
Per slice:
  * design weights W_d (nominal AC-solved array, sim/results/r3/cdac3_mc50_tt_cp100_globalfit.json) -> codes;
  * --fit top2: reduced windowed fit (method W of cal3.py restricted to the circuit data): least squares of the
    input level (in LSB) against [one offset per window, b_0, b_1, g * sum_{j>=2} b_j W_d,j]; W_0 = x_0/g,
    W_1 = x_1/g, lower weights stay W_d; quantised to 1/8 LSB (14 bit).
  * per code inside every window: width = points with that code / M (LSB), DNL = width - 1 (resolution 1/M);
    codes at the window edges are not counted; monotonicity and missing codes inside the window.
"""
import json
import os
import sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p3common import load_segments, BLOCK
import cal3

out = sys.argv[1]
runs = sys.argv[sys.argv.index("--runs") + 1].split(",")
fit = sys.argv[sys.argv.index("--fit") + 1] if "--fit" in sys.argv else None
# --eval: windows on which the DNL is evaluated with the weights (default: the fit windows themselves)
evr = sys.argv[sys.argv.index("--eval") + 1].split(",") if "--eval" in sys.argv else runs
root = os.environ["G1_RESULTS_ROOT"]
Wd_lsb = np.array(json.load(open(os.path.join(BLOCK, "sim", "results", "r3", "cdac3_mc50_tt_cp100_globalfit.json")))["nominal_design_weights_lsb"])
def load_runs(rr):
  data = {"a": [], "b": []}
  for wi, rid in enumerate(rr):
    segj = os.path.join(BLOCK, "sim", "results", "r3", rid + "_segments.json")
    S = json.load(open(segj))
    P = json.load(open(os.path.join(BLOCK, S["points"])))
    slots, ba, bb = load_segments(segj, root)
    for sl, bits in (("a", ba), ("b", bb)):
        v = np.array(P[sl])[slots]
        data[sl].append((v, bits, wi, rid))
  return data


data = load_runs(runs)
edata = data if evr == runs else load_runs(evr)
res = {"label": "simulated (tb_adc3_points.cir, r1_adc3_core_fast, ideal VREF 1.0 V) + post_win3.py", "runs": runs,
       "eval_runs": evr, "slices": {}}
for sl in ("a", "b"):
    V = np.concatenate([d[0] for d in data[sl]])
    B = np.concatenate([d[1] for d in data[sl]])
    Wn = np.concatenate([np.full(len(d[0]), d[2]) for d in data[sl]])
    step = np.median(np.diff(np.sort(edata[sl][0][0])))
    lsb_guess = 446.6e-6
    M = int(round(lsb_guess / step))
    sets = {"design": cal3.quantise(Wd_lsb)}
    if fit == "top2":
        nw = int(Wn.max()) + 1
        O = np.zeros((len(V), nw))
        O[np.arange(len(V)), Wn] = 1
        low = B[:, 2:].astype(float) @ Wd_lsb[2:]
        A = np.column_stack([O, B[:, 0], B[:, 1], low])
        x = np.linalg.lstsq(A, V / lsb_guess, rcond=None)[0]
        g = x[-1]
        w = Wd_lsb.copy()
        w[0], w[1] = x[nw] / g, x[nw + 1] / g
        sets["fit_top2"] = cal3.quantise(w * 4095.0 / w.sum())
    r = {"conversions": int(len(V)), "points_per_lsb": M}
    for tag, W in sets.items():
        win = {}
        for v, bits, wi, rid in edata[sl]:
            o = np.argsort(v)
            c = cal3.code(bits[o], W)
            codes, cnt = np.unique(c, return_counts=True)
            inner = codes[1:-1]
            widths = {int(k): float(n) / M for k, n in zip(codes, cnt) if k in inner}
            win[rid] = {"codes": [int(c.min()), int(c.max())], "monotonic": bool(np.all(np.diff(c) >= 0)),
                        "missing_inside": int(np.sum(np.diff(c) > 1)),
                        "dnl_by_code": {k: round(w - 1, 3) for k, w in widths.items()},
                        "max_abs_dnl": float(max(abs(w - 1) for w in widths.values())) if widths else None}
        mj = {}
        for k in (1023, 1024, 2047, 2048, 3071, 3072):
            for wr in win.values():
                if k in wr["dnl_by_code"]:
                    mj[str(k)] = wr["dnl_by_code"][k]
        r[tag] = {"W": [int(x) for x in W], "windows": win, "major_code_dnl": mj,
                  "major_max_abs_dnl": max(abs(x) for x in mj.values()) if mj else None,
                  "all_windows_max_abs_dnl": max(w["max_abs_dnl"] for w in win.values() if w["max_abs_dnl"] is not None),
                  "monotonic": all(w["monotonic"] for w in win.values()),
                  "missing_inside": sum(w["missing_inside"] for w in win.values())}
    res["slices"][sl] = r
json.dump(res, open(out, "w"), indent=1)
for sl in ("a", "b"):
    for tag in [k for k in res["slices"][sl] if k in ("design", "fit_top2")]:
        x = res["slices"][sl][tag]
        print(sl, tag, "major", x["major_code_dnl"], "max|DNL| all windows %.3f mono %s missing %d" % (x["all_windows_max_abs_dnl"], x["monotonic"], x["missing_inside"]))
        print("   W", x["W"])
