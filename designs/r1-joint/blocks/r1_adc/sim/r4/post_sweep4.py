#!/usr/bin/env python3
"""R2-3 / open issue 3 (revision 4): 64-input sweep at ss/125 C/1.08 V (run_points4.py, ss_sweep64.json).
Per slice: codes with the design weights; straight-line fit (gain, offset) over the 48 spread inputs; error of
every input against the fit (LSB). If an unresolved or wrong decision 0 were not covered by the 30 LSB of
redundancy, the inputs near the decision-0 toggle (16 inputs at -12..+3 mV) would show a code error of tens of LSB.
usage: post_sweep4.py <run id> OUT.json [near_first N]
near_first N: the first N frames are the near-toggle inputs and the rest are spread (ss_cm_test32.json, N 17);
default: frames 0..47 spread, 48.. near toggle (ss_sweep64.json)."""
import json
import os
import sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "r3"))
from p4common import load_segments, BLOCK
import cal3
rid, out = sys.argv[1:3]
root = os.environ["G1_RESULTS_ROOT"]
Wd = cal3.quantise(json.load(open(os.path.join(BLOCK, "sim", "results", "r3", "cdac3_mc50_tt_cp100_globalfit.json")))["nominal_design_weights_lsb"])
segj = os.path.join(BLOCK, "sim", "results", "r4", rid + "_segments.json")
S = json.load(open(segj))
P = json.load(open(os.path.join(BLOCK, S["points"])))
slots, ba, bb = load_segments(segj, root)
res = {"label": "simulated (tb_adc4_points.cir, r1_adc4_core_fast, ss/125 C/1.08 V, ideal VREF) + post_sweep4.py",
       "run": rid, "frames": int(len(slots)), "slices": {}}
for sl, bits in (("a", ba), ("b", bb)):
    v = np.array(P[sl])[slots]
    c = cal3.code(bits, Wd).astype(float)
    nf = int(sys.argv[4]) if len(sys.argv) > 4 and sys.argv[3] == "near_first" else None
    spread = (slots >= nf) if nf else (slots < 48)
    A = np.column_stack([v[spread], np.ones(spread.sum())])
    g, o = np.linalg.lstsq(A, c[spread], rcond=None)[0]
    err = c - (g * v + o)
    near = ~spread
    res["slices"][sl] = {"lsb_uV_fit": 1e6 / g, "offset_code": float(o),
                         "max_abs_err_spread_lsb": float(np.max(np.abs(err[spread]))),
                         "max_abs_err_near_toggle_lsb": float(np.max(np.abs(err[near]))) if near.any() else None,
                         "near_toggle": [{"v_mV": round(float(x) * 1e3, 2), "bit0": int(b[0]), "code": int(cc), "err_lsb": round(float(e), 2)}
                                         for x, b, cc, e in zip(v[near], bits[near], c[near], err[near])],
                         "monotonic_in_v": bool(np.all(np.diff(c[np.argsort(v)]) >= 0))}
res["max_abs_err_lsb"] = max(max(r["max_abs_err_spread_lsb"], r["max_abs_err_near_toggle_lsb"] or 0) for r in res["slices"].values())
json.dump(res, open(out, "w"), indent=1)
for sl, r in res["slices"].items():
    print(sl, "LSB %.1f uV, max|err| spread %.2f, near toggle %s LSB, monotonic %s" % (r["lsb_uV_fit"], r["max_abs_err_spread_lsb"], r["max_abs_err_near_toggle_lsb"], r["monotonic_in_v"]))
    print("  ", [(x["v_mV"], x["bit0"], x["err_lsb"]) for x in r["near_toggle"]])
