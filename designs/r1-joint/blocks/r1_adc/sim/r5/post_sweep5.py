#!/usr/bin/env python3
"""Revision 5 (copy of sim/r4/post_sweep4.py for sim/r5 runs): decision 0 with the NMOS-input comparator r1_cmp5n.
Pass criterion (item 2): the error of every input against the straight-line fit stays inside the redundancy that
follows decision 0 (about 30 LSB; reported) and the transfer is monotonic. Original header:
R2-3 / open issue 3 (revision 4): 64-input sweep at ss/125 C/1.08 V (run_points4.py, ss_sweep64.json).
Per slice: codes with the design weights; straight-line fit (gain, offset) over the 48 spread inputs; error of
every input against the fit (LSB). If an unresolved or wrong decision 0 were not covered by the 30 LSB of
redundancy, the inputs near the decision-0 toggle (16 inputs at -12..+3 mV) would show a code error of tens of LSB.
usage: post_sweep4.py <run id> OUT.json [near_first N]
near_first N: the first N frames are the near-toggle inputs and the rest are spread (ss_cm_test32.json, N 17);
default: frames 0..47 spread, 48.. near toggle (ss_sweep64.json).
Revision 5: frame 0 (the first conversion after t = 0) is a start-up frame. It is excluded from the fit and from the
pass criterion and reported separately (run r5-dbg-ss-slot0: the same -0.90 V input gives code 196 in frame 0 and 73
in frames 1 and 3, so the frame-0 error is a start-up effect, not a level effect; post_ref5.py also skips frame 0)."""
import json
import os
import sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "r4"))
sys.path.insert(0, os.path.join(HERE, "..", "r3"))
from p4common import load_segments, BLOCK
import cal3
rid, out = sys.argv[1:3]
root = os.environ["G1_RESULTS_ROOT"]
Wd = cal3.quantise(json.load(open(os.path.join(BLOCK, "sim", "results", "r3", "cdac3_mc50_tt_cp100_globalfit.json")))["nominal_design_weights_lsb"])
segj = os.path.join(BLOCK, "sim", "results", "r5", rid + "_segments.json")
if not json.load(open(segj))["segments"]:
    sys.exit("run did not complete: not post-processed")
S = json.load(open(segj))
P = json.load(open(os.path.join(BLOCK, S["points"])))
slots, ba, bb = load_segments(segj, root)
res = {"label": "simulated (sim/r5/tb_adc5_points.cir, r1_adc5_core_fast, ideal VREF 1.045 V) + post_sweep5.py",
       "run": rid, "frames": int(len(slots)), "slices": {}}
for sl, bits in (("a", ba), ("b", bb)):
    v = np.array(P[sl])[slots]
    c = cal3.code(bits, Wd).astype(float)
    nf = int(sys.argv[4]) if len(sys.argv) > 4 and sys.argv[3] == "near_first" else None
    spread = ((slots >= nf) if nf else (slots < 48)) & (slots > 0)
    A = np.column_stack([v[spread], np.ones(spread.sum())])
    g, o = np.linalg.lstsq(A, c[spread], rcond=None)[0]
    err = c - (g * v + o)
    near = ~spread & (slots > 0)
    f0 = slots == 0
    res["slices"][sl] = {"lsb_uV_fit": 1e6 / g, "offset_code": float(o),
                         "max_abs_err_spread_lsb": float(np.max(np.abs(err[spread]))),
                         "max_abs_err_near_toggle_lsb": float(np.max(np.abs(err[near]))) if near.any() else None,
                         "near_toggle": [{"v_mV": round(float(x) * 1e3, 2), "bit0": int(b[0]), "code": int(cc), "err_lsb": round(float(e), 2)}
                                         for x, b, cc, e in zip(v[near], bits[near], c[near], err[near])],
                         "monotonic_in_v": bool(np.all(np.diff(c[slots > 0][np.argsort(v[slots > 0])]) >= 0)),
                         "startup_frame0": {"v_mV": round(float(v[f0][0]) * 1e3, 2), "code": int(c[f0][0]), "err_lsb": round(float(err[f0][0]), 2),
                                            "note": "excluded (first conversion after t = 0)"} if f0.any() else None}
Wl = np.array(json.load(open(os.path.join(BLOCK, "sim", "results", "r3", "cdac3_mc50_tt_cp100_globalfit.json")))["nominal_design_weights_lsb"])
res["redundancy_after_decision0_lsb"] = float(Wl[1:].sum() + 0.311 - Wl[0])
res["max_abs_err_lsb"] = max(max(r["max_abs_err_spread_lsb"], r["max_abs_err_near_toggle_lsb"] or 0) for r in res["slices"].values())
res["pass_inside_redundancy"] = bool(res["max_abs_err_lsb"] < res["redundancy_after_decision0_lsb"] and all(r["monotonic_in_v"] for r in res["slices"].values()))
json.dump(res, open(out, "w"), indent=1)
print("redundancy after decision 0: %.1f LSB, max |err| %.2f LSB, pass %s" % (res["redundancy_after_decision0_lsb"], res["max_abs_err_lsb"], res["pass_inside_redundancy"]))
for sl, r in res["slices"].items():
    print(sl, "LSB %.1f uV, max|err| spread %.2f, near toggle %s LSB, monotonic %s" % (r["lsb_uV_fit"], r["max_abs_err_spread_lsb"], r["max_abs_err_near_toggle_lsb"], r["monotonic_in_v"]))
    print("  ", [(x["v_mV"], x["bit0"], x["err_lsb"]) for x in r["near_toggle"]])
