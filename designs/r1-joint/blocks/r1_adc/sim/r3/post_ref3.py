#!/usr/bin/env python3
"""R2-4 (revision 3): conversion error caused by reference settling, both slices converting in parallel.

usage: post_ref3.py <run id with r1_refbuf3> <run id with ideal VREF> OUT.json [ideal VREF, default 1.0]
The ideal run should use the buffer DC value (1.004 V): with 1.0 V the codes differ by a static 0.4 % gain
(found 2026-10-20: 7.9 LSB at full scale, first misread as a settling error).
Both runs: tb_adc3_points.cir with the same per-slot inputs, --save full.
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
from p3common import read, ts, H, ND, sample, bits_from_raw

root = os.environ["G1_RESULTS_ROOT"]
rb_id, ri_id, out = sys.argv[1:4]
VIDEAL = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0   # VREF of the ideal run
NB = 13


def load(rid):
    d, _ = read(os.path.join(root, "r1_adc", rid, "codes.raw"))
    return d


def trace(d, sl, s):
    p, n = ("v(topap)", "v(topan)") if sl == "a" else ("v(topbp)", "v(topbn)")
    t = ts(s) + np.arange(ND) * H + 0.8e-9
    return sample(d, p, t) - sample(d, n, t)          # V_diff before decision k = 0..13


di, db = load(ri_id), load(rb_id)
tmax = min(di["time"][-1], db["time"][-1])
nslot = int((tmax - ts(0) - 300e-9) // (18 / 30e6)) + 1
res = {"label": "simulated (tb_adc3_points.cir, r1_adc3_core_fast); residue-resolved error, see header",
       "run_buffer": rb_id, "run_ideal": ri_id, "slices": {}}
for sl in ("a", "b"):
    steps = {"p": [[] for _ in range(NB)], "n": [[] for _ in range(NB)]}
    tr_i = [trace(di, sl, s) for s in range(nslot)]
    for v in tr_i:
        dv = np.diff(v)                                 # 13 steps (decisions 0..12)
        for j in range(NB):
            k = NB - 1 - j
            (steps["p"][k] if dv[j] < 0 else steps["n"][k]).append(abs(dv[j]))
    wp = np.array([np.mean(x) if x else np.nan for x in steps["p"]])
    wn = np.array([np.mean(x) if x else np.nan for x in steps["n"]])
    wp = np.where(np.isnan(wp), wn, wp)
    wn = np.where(np.isnan(wn), wp, wn)
    lsb1 = (wp.sum() + wn.sum() + 0.5 * (wp[0] + wn[0])) / 4095.0

    def est(v, v1):
        dv = np.diff(v)
        x = v[-1]
        for j in range(NB):
            k = NB - 1 - j
            x += v1 * (wp[k] if dv[j] < 0 else -wn[k])
        return x, (dv < 0).astype(int)
    rows = []
    rawi = bits_from_raw(sample(di, "v(raw%s)" % sl, ts(np.arange(nslot)) + 260e-9))
    rawb = bits_from_raw(sample(db, "v(raw%s)" % sl, ts(np.arange(nslot)) + 260e-9))
    Wd = np.array([wp[NB - 1 - j] + wn[NB - 1 - j] for j in range(NB)] + [0.5 * (wp[0] + wn[0])])
    Wd = np.rint(Wd / Wd.sum() * 4095 * 8).astype(np.int64)
    for s in range(nslot):
        v1 = float(sample(db, "v(vref)", ts(s) - 0.2e-9)) / VIDEAL
        vr = db["v(vref)"][(db["time"] > ts(s)) & (db["time"] < ts(s) + 14 * H)]
        xi, bi = est(tr_i[s], 1.0)
        xb, bb = est(trace(db, sl, s), v1)
        ci = int(np.clip((int(rawi[s] @ Wd) + 4) >> 3, 0, 4095))
        cb = int(np.clip((int(rawb[s] @ Wd) + 4) >> 3, 0, 4095))
        rows.append({"slot": s, "vin_est_ideal_V": float(xi), "vref_at_sampling_V": v1 * VIDEAL, "code_diff_lsb": None,
                     "vref_min_max_during_conversion_V": [float(vr.min()), float(vr.max())],
                     "error_lsb": float((xb - xi) / (v1 * lsb1)), "code_ideal": ci, "code_buffer": cb,
                     "bits_differ_at": [int(j) for j in np.nonzero(rawi[s] != rawb[s])[0]]})
        rows[-1]["code_diff_lsb"] = cb - ci
    e = np.array([r["error_lsb"] for r in rows])
    cd = np.array([r["code_diff_lsb"] for r in rows])
    res["slices"][sl + "_max_abs_code_diff_lsb"] = int(np.max(np.abs(cd[1:])))
    res["slices"][sl] = {"lsb_uV_at_1V": lsb1 * 1e6, "fs_diff_V_at_1V": lsb1 * 2048,
                         "max_abs_error_lsb": float(np.max(np.abs(e[1:]))), "slots": rows}
res["max_abs_error_lsb"] = max(res["slices"][s]["max_abs_error_lsb"] for s in ("a", "b"))
res["max_abs_code_diff_lsb"] = max(res["slices"][s + "_max_abs_code_diff_lsb"] for s in ("a", "b"))
res["pass_0p25"] = bool(res["max_abs_error_lsb"] <= 0.25)
json.dump(res, open(out, "w"), indent=1)
for sl in ("a", "b"):
    print(sl, "LSB %.1f uV FS %.4f V" % (res["slices"][sl]["lsb_uV_at_1V"], res["slices"][sl]["fs_diff_V_at_1V"]))
    for r in res["slices"][sl]["slots"]:
        print("  slot %d vin %+.4f err %+.3f LSB codes %d/%d vref %.5f [%.5f %.5f]" % (r["slot"], r["vin_est_ideal_V"], r["error_lsb"],
              r["code_ideal"], r["code_buffer"], r["vref_at_sampling_V"], *r["vref_min_max_during_conversion_V"]))
print("max |error| %.3f LSB (residue-resolved), max |code difference| %d LSB (slot 0 excluded: start-up)" % (res["max_abs_error_lsb"], res["max_abs_code_diff_lsb"]))
