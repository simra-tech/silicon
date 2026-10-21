#!/usr/bin/env python3
"""R2-4 (revision 5): comparator-input error caused by the reference, both slices converting in parallel (N = 0).
Method of sim/r4/post_ref4.py (third version), extended for per-slice and split references:
  * Capacitor steps wp_k, wn_k (V per V of reference) from the ideal-reference run (top plates 1.2 ns after each
    clk30 edge, comparator in reset), mean over all slots.
  * Mid-evaluation error of decision k (25 ns into tick k, comparator integrating), on the common decision path:
      e_k = V_diff_buf(k) - [V_diff_ideal(k) - (v1M - 1) S_k^M - (v1L - 1) S_k^L]
    S_k^M / S_k^L: signed sum of the MSB-array (C12..C8, decisions 0..4) / LSB-array (C7..C0, decisions 5..12)
    steps of the ideal run before decision k. v1M = v(vrefX) / VIDEAL and v1L = v(vreflX) / VIDEAL at the sampling
    edge of slice X (X = a, b): the static reference value at sampling is a gain term (bench gain calibration;
    for a separate LSB reference it is a weight term of the LSB array, removed by the weight calibration).
    Reported in LSB(v1M) for decisions 5..13 ("worst-case": decisions 5..13 have about 0.31 LSB redundancy).
  * Gain-corrected error (additional, not the R2-4 criterion): per slice, one least-squares gain per reference
    (g_M, g_L) over all slots and decisions: e_k - g_M S_k^M - g_L S_k^L. This is what a single gain/weight
    calibration can remove when the reference moves the same way in every conversion.
  * Error vs time: max |e_k| over the slots per decision k (waveform summary).
  * Final residue error and the 12-bit code difference with the design weights, as in revision 4.
  * Second ideal run (5th/6th argument, revision-5 fix): the capacitor steps measured on the top plates also hold
    comparator kickback and switch charge that do not scale with VREF. Scaling the whole step by v1 (first version,
    and revision 4 when the ideal run was not at the buffer DC value) gives an error proportional to the input
    (1.98 LSB at 0.87 V for a 5.3 mV VREF difference). With a second ideal run at VIDEAL2 the VREF-proportional part
    of each step is a_k = (step_k(VIDEAL2) - step_k(VIDEAL)) / (VIDEAL2 - VIDEAL), and the correction becomes
    (vM - VIDEAL) S_k^M(a) + (vL - VIDEAL) S_k^L(a) with the buffer values vM, vL (V) at the sampling edge.
usage: post_ref5.py <buffer run id> <ideal run id> OUT.json [VIDEAL, default 1.045] [<ideal run 2 id> VIDEAL2]
"""
import json
import os
import sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "r4"))
from p4common import read, ts, T, ND, TLAT, sample, bits_from_raw

root = os.environ["G1_RESULTS_ROOT"]
rb_id, ri_id, out = sys.argv[1:4]
VIDEAL = float(sys.argv[4]) if len(sys.argv) > 4 else 1.045
RI2 = sys.argv[5] if len(sys.argv) > 6 else None
V2 = float(sys.argv[6]) if RI2 else None
NB = 13
NMSB = 5                      # decisions 0..4 switch C12..C8 (MSB array on vref)


def load(rid):
    seg = json.load(open(os.path.join(HERE, "..", "results", "r5", rid + "_segments.json")))
    if not seg["segments"]:
        sys.exit("run %s did not complete (%s): not post-processed" % (rid, seg["stopped"]))
    d, _ = read(os.path.join(root, "r1_adc", rid, "codes.raw"))
    return d


di, db = load(ri_id), load(rb_id)
di2 = load(RI2) if RI2 else None
F = 22 * T
tmax = min(di["time"][-1], db["time"][-1])
nslot = int((tmax - ts(0, "a", 0) - ND * T - 30e-9) // F) + 1
res = {"label": "simulated (sim/r5/tb_adc5_points.cir, r1_adc5_core_fast) + post_ref5.py; see header for the metric",
       "run_buffer": rb_id, "run_ideal": ri_id, "videal_V": VIDEAL, "run_ideal2": RI2, "videal2_V": V2,
       "step_model": "two ideal runs: per-slot interpolation of the trajectory in VREF (mid-evaluation error); averaged proportional steps for the gain-fit regressors" if RI2 else "steps scaled by v1 (assumes steps proportional to VREF)",
       "slices": {}}


def vd(d, sl, t):
    p, n = ("v(topap)", "v(topan)") if sl == "a" else ("v(topbp)", "v(topbn)")
    return sample(d, p, t) - sample(d, n, t)


def capsteps(d, sl):
    tr = [vd(d, sl, np.append(ts(s) + np.arange(ND) * T + 1.2e-9, ts(s) + ND * T + 5e-9)) for s in range(nslot)]
    steps = {"p": [[] for _ in range(NB)], "n": [[] for _ in range(NB)]}
    for v in tr:
        dv = np.diff(v[:ND])
        for j in range(NB):
            k = NB - 1 - j
            (steps["p"][k] if dv[j] < 0 else steps["n"][k]).append(abs(dv[j]))
    wp = np.array([np.mean(x) if x else np.nan for x in steps["p"]])
    wn = np.array([np.mean(x) if x else np.nan for x in steps["n"]])
    wp = np.where(np.isnan(wp), wn, wp)
    wn = np.where(np.isnan(wn), wp, wn)
    return tr, wp, wn


for sl in ("a", "b"):
    tr_i, wp, wn = capsteps(di, sl)
    if di2 is not None:
        _, wp2, wn2 = capsteps(di2, sl)
        ap, an = (wp2 - wp) / (V2 - VIDEAL), (wn2 - wn) / (V2 - VIDEAL)      # V per V of reference
    else:
        ap, an = wp / VIDEAL, wn / VIDEAL
    res.setdefault("vref_proportional_fraction_of_step", {})[sl] = [round(float(x), 4) for x in (ap * VIDEAL / wp)]
    lsb1 = (wp.sum() + wn.sum() + 0.5 * (wp[0] + wn[0])) / 4095.0
    rawi = bits_from_raw(sample(di, "v(raw%s)" % sl, ts(np.arange(nslot)) + TLAT))
    rawb = bits_from_raw(sample(db, "v(raw%s)" % sl, ts(np.arange(nslot)) + TLAT))
    Wd = np.array([wp[NB - 1 - j] + wn[NB - 1 - j] for j in range(NB)] + [0.5 * (wp[0] + wn[0])])
    Wd = np.rint(Wd / Wd.sum() * 4095 * 8).astype(np.int64)
    rows, E, SM, SL = [], [], [], []
    for s in range(nslot):
        t0 = ts(s)
        v1m = float(sample(db, "v(vref%s)" % sl, t0 - 0.2e-9)) / VIDEAL
        v1l = float(sample(db, "v(vrefl%s)" % sl, t0 - 0.2e-9)) / VIDEAL
        stp = np.array([(wp[NB - 1 - j] if rawi[s][j] == 1 else -wn[NB - 1 - j]) for j in range(NB)])
        sta = np.array([(ap[NB - 1 - j] if rawi[s][j] == 1 else -an[NB - 1 - j]) for j in range(NB)])
        stM = np.where(np.arange(NB) < NMSB, sta, 0.0)            # VREF-proportional steps (V per V)
        stL = sta - stM
        SkM = np.concatenate([[0.0], np.cumsum(stM)])
        SkL = np.concatenate([[0.0], np.cumsum(stL)])
        dM, dL = v1m * VIDEAL - VIDEAL, v1l * VIDEAL - VIDEAL                 # buffer minus ideal reference (V)
        dif = np.nonzero(rawi[s] != rawb[s])[0]
        jmax = int(dif[0]) if dif.size else ND - 1
        tm = t0 + np.arange(ND) * T + 25e-9
        if di2 is not None:
            # per-slot interpolation between the two ideal runs (exact VREF sensitivity of this trajectory, including
            # non-proportional parts); valid up to the first decision where the two ideal runs differ. The LSB array
            # term (dL - dM) uses the nominal steps (zero when vrefl = vref).
            rawi2 = bits_from_raw(sample(di2, "v(raw%s)" % sl, np.array([ts(s) + TLAT])))[0]
            d2 = np.nonzero(rawi[s] != rawi2)[0]
            if d2.size:
                jmax = min(jmax, int(d2[0]))
            stn = np.array([(wp[NB - 1 - j] if rawi[s][j] == 1 else -wn[NB - 1 - j]) for j in range(NB)]) / VIDEAL
            SkLn = np.concatenate([[0.0], np.cumsum(np.where(np.arange(NB) < NMSB, 0.0, stn))])
            sens = (vd(di2, sl, tm) - vd(di, sl, tm)) / (V2 - VIDEAL)
            pred = vd(di, sl, tm) + dM * sens + (dL - dM) * SkLn
            me = (vd(db, sl, tm) - pred) / (v1m * lsb1)
        else:
            me = (vd(db, sl, tm) - (vd(di, sl, tm) - dM * SkM - dL * SkL)) / (v1m * lsb1)
        # final residue (tick 14) -> input estimate with the design weights at the reference of each array
        xi = tr_i[s][-1] + float(np.sum(stp))
        # buffer run: its own bits (first version used the ideal run's bits here: 11 LSB artefact on diverged paths)
        stb = np.array([(wp[NB - 1 - j] if rawb[s][j] == 1 else -wn[NB - 1 - j]) for j in range(NB)])
        # proportional steps here (the averaged two-run steps are too noisy for a 14-step sum)
        stba = np.array([(wp[NB - 1 - j] if rawb[s][j] == 1 else -wn[NB - 1 - j]) for j in range(NB)]) / VIDEAL
        stbaM = np.where(np.arange(NB) < NMSB, stba, 0.0)
        xb = vd(db, sl, np.array([t0 + ND * T + 5e-9]))[0] + float(np.sum(stb)) + dM * float(np.sum(stbaM)) + dL * float(np.sum(stba - stbaM))
        fin_err = float((xb - xi) / (v1m * lsb1))
        if di2 is not None and not dif.size and not d2.size:
            tf = np.array([t0 + ND * T + 5e-9])
            sf = (vd(di2, sl, tf) - vd(di, sl, tf)) / (V2 - VIDEAL)
            fin_err = float((vd(db, sl, tf) - vd(di, sl, tf) - dM * sf - (dL - dM) * SkLn[-1])[0] / (v1m * lsb1))
        ci = int(np.clip((int(rawi[s] @ Wd) + 4) >> 3, 0, 4095))
        cb = int(np.clip((int(rawb[s] @ Wd) + 4) >> 3, 0, 4095))
        vr = db["v(vref%s)" % sl][(db["time"] > t0) & (db["time"] < t0 + 14 * T)]
        vrl = db["v(vrefl%s)" % sl][(db["time"] > t0) & (db["time"] < t0 + 14 * T)]
        ok = [j for j in range(5, ND) if j <= jmax]
        rows.append({"slot": s, "vin_est_ideal_V": float(xi), "vref_at_sampling_V": v1m * VIDEAL, "vrefl_at_sampling_V": v1l * VIDEAL,
                     "vref_min_max_during_conversion_V": [float(vr.min()), float(vr.max())],
                     "vrefl_min_max_during_conversion_V": [float(vrl.min()), float(vrl.max())],
                     "error_lsb": fin_err, "code_ideal": ci, "code_buffer": cb, "code_diff_lsb": cb - ci,
                     "bits_differ_at": [int(j) for j in dif],
                     "input_error_mid_eval_lsb_dec5_13": [round(float(me[j]), 3) if j <= jmax else None for j in range(5, ND)]})
        if s > 0:
            for j in ok:
                E.append(me[j]); SM.append(SkM[j] / lsb1); SL.append(SkL[j] / lsb1)
    E, SM, SL = np.array(E), np.array(SM), np.array(SL)
    A = np.column_stack([SM, SL]) if np.any(SL != 0) else SM[:, None]
    g = np.linalg.lstsq(A, E, rcond=None)[0]
    resid = E - A @ g
    pd = {}
    for r in rows[1:]:
        for j, x in zip(range(5, ND), r["input_error_mid_eval_lsb_dec5_13"]):
            if x is not None:
                pd[j] = max(pd.get(j, 0.0), abs(x))
    e = np.array([r["error_lsb"] for r in rows[1:]])
    res["slices"][sl] = {"lsb_uV_at_1V": lsb1 * 1e6, "fs_diff_V_at_videal": lsb1 * 2048 * VIDEAL,
                         "max_abs_input_error_mid_eval_lsb": float(np.max(np.abs(E))),
                         "max_abs_error_after_gain_fit_lsb": float(np.max(np.abs(resid))),
                         "gain_fit_per_lsb_of_dac": [float(x) for x in g],
                         "max_abs_error_vs_decision_lsb": {str(k): round(v, 3) for k, v in sorted(pd.items())},
                         "max_abs_final_residue_error_lsb": float(np.max(np.abs(e))),
                         "max_abs_code_diff_lsb": int(np.max(np.abs([r["code_diff_lsb"] for r in rows[1:]]))),
                         "slots": rows}
S = res["slices"]
res["max_abs_input_error_mid_eval_lsb"] = max(S[x]["max_abs_input_error_mid_eval_lsb"] for x in "ab")
res["max_abs_error_after_gain_fit_lsb"] = max(S[x]["max_abs_error_after_gain_fit_lsb"] for x in "ab")
res["max_abs_code_diff_lsb"] = max(S[x]["max_abs_code_diff_lsb"] for x in "ab")
res["pass_0p25_r24"] = bool(res["max_abs_input_error_mid_eval_lsb"] <= 0.25)
if "i(vdda)" in db:
    m = db["time"] > 0.7e-6
    res["idda_mA"] = float(-np.mean(db["i(vdda)"][m]) * 1e3)
json.dump(res, open(out, "w"), indent=1)
for sl in "ab":
    x = S[sl]
    print(sl, "FS %.4f V | worst-case %.3f LSB, after gain fit %.3f, code diff %d, residue %.3f | per decision %s"
          % (x["fs_diff_V_at_videal"], x["max_abs_input_error_mid_eval_lsb"], x["max_abs_error_after_gain_fit_lsb"],
             x["max_abs_code_diff_lsb"], x["max_abs_final_residue_error_lsb"], x["max_abs_error_vs_decision_lsb"]))
print("R2-4 worst-case %.3f LSB (pass %s), after gain fit %.3f LSB, IDDA %s mA" % (
    res["max_abs_input_error_mid_eval_lsb"], res["pass_0p25_r24"], res["max_abs_error_after_gain_fit_lsb"], res.get("idda_mA")))
