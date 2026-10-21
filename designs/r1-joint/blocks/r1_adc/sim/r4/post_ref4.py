#!/usr/bin/env python3
"""R2-4 (revision 4, D18 frame, one decision per tick): conversion error caused by reference settling, both slices
converting in parallel, slice B N ticks after slice A (n_stag from the segments file of the buffer run).
Same method as sim/r3/post_ref3.py; the top-plate difference is read 1.2 ns after each clk30 edge (comparator
still in reset, CDAC switched at the edge - 0.6 ns) for the capacitor steps (ideal run), and the final residue
is read in tick 14 (14 T + 5 ns: conversion done, comparator in reset, no switching, before the track start at
14 T + 6 ns). The first version read the final residue at 13 T + 1.2 ns, inside the reference dip of the
decision-12 switch, and gave 10-20 LSB "errors" with codes within 1 LSB (measurement-instant artefact).

usage: post_ref4.py <run id with r1_refbuf4> <run id with ideal VREF> OUT.json [ideal VREF, default 1.0]
The ideal run should use the buffer DC value (1.004 V): with 1.0 V the codes differ by a static 0.4 % gain
(found 2026-10-20: 7.9 LSB at full scale, first misread as a settling error).
Both runs: tb_adc4_points.cir with the same per-frame inputs, --save full, same stagger.
Method (residue-resolved, sub-LSB):
  * In the ideal run, the step of every capacitor (slice, side, cap) is measured on the top plates in the reset
    phase just before each evaluation (ts + k H + 0.8 ns): wp_k, wn_k (V per 1.0 V reference, mean of all slots).
  * In each run and slot, the back-end estimate with exact nominal weights and the final residue is
    x = V_res + V1 * (sum_{b=1} wp_k - sum_{b=0} wn_k), V_res = top-plate difference before decision 13,
    V1 = VREF at the sampling edge (1.0 in the ideal run). Bits are read from the step signs.
  * error[LSB] = (x_buf - x_ideal) / LSB(V1), LSB(V1) = V1 * (sum wp + sum wn + (wp_0 + wn_0)/2) / 4095.
    This removes the static VREF value (a gain term calibrated on the bench) and keeps the dynamic error.
  * The rounded 12-bit code difference with the design weights is reported as well.
"""
import json
import os
import sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p4common import read, ts, T, F, ND, TLAT, sample, bits_from_raw

root = os.environ["G1_RESULTS_ROOT"]
rb_id, ri_id, out = sys.argv[1:4]
VIDEAL = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0   # VREF of the ideal run
NB = 13


def load(rid):
    d, _ = read(os.path.join(root, "r1_adc", rid, "codes.raw"))
    return d


NST = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results", "r4", rb_id + "_segments.json")))["n_stag"]
NSTI = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results", "r4", ri_id + "_segments.json")))["n_stag"]
# an ideal-VREF run with another stagger is a valid reference: with ideal sources each slice is independent of the
# other, so its traces are those of the same inputs shifted in time (used for n2: r4-ref-tt-n2-ideal1004 aborted)


def trace(d, sl, s, nst=None):
    nst = NST if nst is None else nst
    p, n = ("v(topap)", "v(topan)") if sl == "a" else ("v(topbp)", "v(topbn)")
    t = np.append(ts(s, sl, nst) + np.arange(ND) * T + 1.2e-9, ts(s, sl, nst) + ND * T + 5e-9)
    return sample(d, p, t) - sample(d, n, t)          # V_diff before decision k = 0..13, then the late residue


di, db = load(ri_id), load(rb_id)
tmax = min(di["time"][-1], db["time"][-1])
nslot = int((tmax - ts(0, "b", NST) - ND * T - 30e-9) // F) + 1
res = {"label": "simulated (tb_adc4_points.cir, r1_adc4_core_fast); residue-resolved error, see header",
       "run_buffer": rb_id, "run_ideal": ri_id, "n_stag": NST, "n_stag_ideal_run": NSTI, "slices": {}}
for sl in ("a", "b"):
    steps = {"p": [[] for _ in range(NB)], "n": [[] for _ in range(NB)]}
    tr_i = [trace(di, sl, s, NSTI) for s in range(nslot)]
    for v in tr_i:
        dv = np.diff(v[:ND])                            # 13 steps (decisions 0..12)
        for j in range(NB):
            k = NB - 1 - j
            (steps["p"][k] if dv[j] < 0 else steps["n"][k]).append(abs(dv[j]))
    wp = np.array([np.mean(x) if x else np.nan for x in steps["p"]])
    wn = np.array([np.mean(x) if x else np.nan for x in steps["n"]])
    wp = np.where(np.isnan(wp), wn, wp)
    wn = np.where(np.isnan(wn), wp, wn)
    lsb1 = (wp.sum() + wn.sum() + 0.5 * (wp[0] + wn[0])) / 4095.0

    def est(v, v1, bits):
        x = v[-1]                                       # late residue (tick 14)
        for j in range(NB):
            k = NB - 1 - j
            x += v1 * (wp[k] if bits[j] == 1 else -wn[k])
        return x

    def mid(d, s, nst):                                 # V_diff 25 ns into each tick (comparator integrating)
        p, n = ("v(topap)", "v(topan)") if sl == "a" else ("v(topbp)", "v(topbn)")
        t = ts(s, sl, nst) + np.arange(ND) * T + 25e-9
        return sample(d, p, t) - sample(d, n, t)
    rows = []
    rawi = bits_from_raw(sample(di, "v(raw%s)" % sl, ts(np.arange(nslot), sl, NSTI) + TLAT))
    rawb = bits_from_raw(sample(db, "v(raw%s)" % sl, ts(np.arange(nslot), sl, NST) + TLAT))
    Wd = np.array([wp[NB - 1 - j] + wn[NB - 1 - j] for j in range(NB)] + [0.5 * (wp[0] + wn[0])])
    Wd = np.rint(Wd / Wd.sum() * 4095 * 8).astype(np.int64)
    for s in range(nslot):
        v1 = float(sample(db, "v(vref)", ts(s, sl, NST) - 0.2e-9)) / VIDEAL
        vr = db["v(vref)"][(db["time"] > ts(s, sl, NST)) & (db["time"] < ts(s, sl, NST) + 14 * T)]
        xi = est(tr_i[s], 1.0, rawi[s])
        xb = est(trace(db, sl, s), v1, rawb[s])
        dif = np.nonzero(rawi[s] != rawb[s])[0]
        jmax = int(dif[0]) if dif.size else ND - 1      # common decision path: decisions 0..jmax compare
        # V_diff = k Vin - VREF D(t): only the DAC part scales with VREF. k Vin = V_diff of the ideal run in tick 0
        # (1.2 ns, no capacitor switched yet). First version scaled the whole ideal V_diff by v1 (wrong when the
        # buffer's static VREF differs from the ideal run: 2.8 LSB artefact at 0.87 V with a 1.4 mV offset).
        # exact form (third version): V_diff_i = k Vin + c(t) - S_k, S_k = sum of the signed capacitor steps of the
        # ideal run before decision k (c = comparator input-pair charge, equal in both runs on a common path);
        # expected buffer V_diff = V_diff_i - (v1 - 1) S_k. No matched-VREF ideal run needed.
        stp = np.array([(wp[NB - 1 - j] if rawi[s][j] == 1 else -wn[NB - 1 - j]) for j in range(NB)])
        Sk = np.concatenate([[0.0], np.cumsum(stp)])            # before decisions 0..13
        me = (mid(db, s, NST) - (mid(di, s, NSTI) - (v1 - 1.0) * Sk)) / (v1 * lsb1)
        me = [round(float(me[j]), 3) if j <= jmax else None for j in range(5, ND)]
        ci = int(np.clip((int(rawi[s] @ Wd) + 4) >> 3, 0, 4095))
        cb = int(np.clip((int(rawb[s] @ Wd) + 4) >> 3, 0, 4095))
        rows.append({"slot": s, "vin_est_ideal_V": float(xi), "vref_at_sampling_V": v1 * VIDEAL, "code_diff_lsb": None,
                     "vref_min_max_during_conversion_V": [float(vr.min()), float(vr.max())],
                     "error_lsb": float((xb - xi) / (v1 * lsb1)), "code_ideal": ci, "code_buffer": cb,
                     "bits_differ_at": [int(j) for j in np.nonzero(rawi[s] != rawb[s])[0]],
                     "input_error_mid_eval_lsb_dec5_13": me if jmax >= 5 else None})
        rows[-1]["code_diff_lsb"] = cb - ci
    e = np.array([r["error_lsb"] for r in rows])
    cd = np.array([r["code_diff_lsb"] for r in rows])
    res["slices"][sl + "_max_abs_code_diff_lsb"] = int(np.max(np.abs(cd[1:])))
    mm = [max(abs(x) for x in r["input_error_mid_eval_lsb_dec5_13"] if x is not None) for r in rows[1:] if r["input_error_mid_eval_lsb_dec5_13"]]
    res["slices"][sl + "_max_abs_input_error_mid_eval_lsb"] = max(mm) if mm else None
    res["slices"][sl] = {"lsb_uV_at_1V": lsb1 * 1e6, "fs_diff_V_at_1V": lsb1 * 2048,
                         "max_abs_error_lsb": float(np.max(np.abs(e[1:]))), "slots": rows}
res["max_abs_error_lsb"] = max(res["slices"][s]["max_abs_error_lsb"] for s in ("a", "b"))
res["max_abs_code_diff_lsb"] = max(res["slices"][s + "_max_abs_code_diff_lsb"] for s in ("a", "b"))
res["pass_0p25"] = bool(res["max_abs_error_lsb"] <= 0.25)
if "i(vdda)" in db:
    m = db["time"] > 0.7e-6
    res["idda_mA"] = float(-np.mean(db["i(vdda)"][m]) * 1e3)
json.dump(res, open(out, "w"), indent=1)
for sl in ("a", "b"):
    print(sl, "LSB %.1f uV FS %.4f V" % (res["slices"][sl]["lsb_uV_at_1V"], res["slices"][sl]["fs_diff_V_at_1V"]))
    for r in res["slices"][sl]["slots"]:
        print("  slot %d vin %+.4f err %+.3f LSB codes %d/%d vref %.5f [%.5f %.5f]" % (r["slot"], r["vin_est_ideal_V"], r["error_lsb"],
              r["code_ideal"], r["code_buffer"], r["vref_at_sampling_V"], *r["vref_min_max_during_conversion_V"]))
res["max_abs_input_error_mid_eval_lsb"] = max(res["slices"][s + "_max_abs_input_error_mid_eval_lsb"] or 0 for s in ("a", "b"))
json.dump(res, open(out, "w"), indent=1)
print("max |error| %.3f LSB (residue-resolved), max |code difference| %d LSB (slot 0 excluded: start-up), max |input error mid-eval, dec 5-13| %.3f LSB, IDDA %s mA"
      % (res["max_abs_error_lsb"], res["max_abs_code_diff_lsb"], res["max_abs_input_error_mid_eval_lsb"], res.get("idda_mA")))
