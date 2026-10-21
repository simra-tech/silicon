#!/usr/bin/env python3
"""Item 3 (revision 5): weight calibration on the circuit, MIM-mismatch MC (r1_adc5_core_fast_mc), all 14 weights
fitted per slice sample, DNL at the major transitions after loading the fitted weights.

usage: post_mc5.py OUT.json <run id> [<run id> ...]   (runs of run_points5.py --mcs K on points/mccal5.json; the PDK-agauss
MC core --mc has no DC operating point, see README revision 5, open issue 2)
Per slice sample (instance m<i>, slice a/b):
  * fit: least squares of the known input level (in LSB, LSB = 446.4 uV x 1.045) against [1, b_0 .. b_13] over all
    66 conversions (15 spread + 3 windows of 17); the 14 weights are scaled to sum 4095 LSB and quantised to 1/8 LSB
    (14 bit, as loaded in r1_ctrl). In simulation the input is exact, so one global offset is used (the bench
    method W of revision 3 uses one offset per window instead; not reproducible here at 81 windows).
  * DNL in each window (4 conversions per LSB, resolution 0.25 LSB) with the design weights and with the fitted
    weights; first and last code of a window not counted; monotonicity and missing codes inside the windows.
    Major-transition DNL = DNL of the two codes at the transition (1023/1024, 2047/2048, 3071/3072).
  * Window check: each window holds its code transition with the design weights (placement check of the MC).
The fit and the DNL use the same conversions (no separate evaluation set; recorded in the README).
Revision 5: frame 0 (start-up frame) is excluded from the fits. Cross-check "map": MAP fit with one offset per window
and PDK-mismatch priors (function mapfit). Register check: every fitted weight x 4 (1/4 LSB) against the stored
width WW(i) of r1_ctrl (R1_REGISTER_MAP.md 0.4, section 4.11), register index i = 13 - decision index.
"""
import json
import os
import sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
BLOCK = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(HERE, "..", "r4"))
sys.path.insert(0, os.path.join(HERE, "..", "r3"))
from p4common import load_segments
import cal3
out, runs = sys.argv[1], sys.argv[2:]
root = os.environ["G1_RESULTS_ROOT"]
Wl = np.array(json.load(open(os.path.join(BLOCK, "sim", "results", "r3", "cdac3_mc50_tt_cp100_globalfit.json")))["nominal_design_weights_lsb"])
Wd = cal3.quantise(Wl)
res = {"label": "simulated (sim/r5/tb_adc5_points.cir, run_points5.py --mcs: nominal fast core with sampled MIM mismatch, PDK cap_typ_mismatch statistics; ideal VREF 1.045 V, tt) + post_mc5.py",
       "runs": runs, "samples": {}}


def dnl_windows(P, v, bits, W):
    win = {}
    for k, (s0, n) in enumerate(P["windows"]):
        m = (np.arange(len(v)) >= s0) & (np.arange(len(v)) < s0 + n)
        vv, bb = v[m], bits[m]
        o = np.argsort(vv)
        c = cal3.code(bb[o], W)
        codes, cnt = np.unique(c, return_counts=True)
        M = P["points_per_lsb"]
        widths = {int(x): float(nn) / M - 1 for x, nn in zip(codes[1:-1], cnt[1:-1])}
        maj = 1024 * (k + 1)
        win[str(maj)] = {"codes": [int(c.min()), int(c.max())], "holds_transition": bool(c.min() < maj <= c.max()),
                         "monotonic": bool(np.all(np.diff(c) >= 0)), "missing_inside": int(np.sum(np.diff(c) > 1)),
                         "dnl_by_code": {str(x): round(y, 3) for x, y in widths.items()},
                         "max_abs_dnl": float(max(abs(y) for y in widths.values())) if widths else None,
                         "major_dnl": [widths.get(maj - 1), widths.get(maj)]}
    return win


# r1_ctrl register widths (R1_REGISTER_MAP.md 0.4, section 4.11): ADC_x_W<i>, units 1/4 LSB, unsigned, WW(i) bits.
# Register index i = 13 - decision index (raw[13] is the first decision); read from the map table.
REGMAP = os.path.join(BLOCK, "..", "r1_ctrl", "R1_REGISTER_MAP.md")
WW = None
for line in open(REGMAP):
    if line.startswith("| WW(i) bits |"):
        WW = [int(x) for x in line.strip().strip("|").split("|")[1:]]
assert WW and len(WW) == 14, "WW(i) row not found in R1_REGISTER_MAP.md"
REG = {"source": "blocks/r1_ctrl/R1_REGISTER_MAP.md section 4.11 (revision 0.4)", "WW_bits_by_register_index": WW,
       "unit": "1/4 LSB, unsigned", "per_sample": {}}


def regcheck(w_lsb):
    out = []
    for j, w in enumerate(w_lsb):
        i = 13 - j
        v = int(np.rint(w * 4.0))
        mx = (1 << WW[i]) - 1
        out.append({"register_index": i, "value": v, "max": mx, "fraction_of_max": round(v / mx, 4), "fits": bool(0 <= v <= mx),
                    "over_by": max(0, v - mx), "negative": v < 0})
    return out


summ = {"design": [], "fit": [], "map": []}
# MAP fit of all 14 weights (cross-check "map"): y = o_k + g (b . Wl) + b . dw, one offset per window (local: removes the
# input-dependent sampling error, which is several LSB at +-0.9 V) and one for the spread inputs; data sigma 0.29 LSB
# in the windows (input grid 1/4 LSB, residue uniform) and 5 LSB for the spread inputs; prior dw_j ~ N(0, s_j^2) with
# s_j = 3 x the PDK MIM mismatch of decision j (1 % / sqrt(unit area um^2) / sqrt(units), unit 3.78 um) + 0.05 LSB.
UNITS = np.array([16, 8, 4, 2, 1, 64, 32, 16, 8, 4, 2, 1, 0.5, 0.5])
SIGW = 3.0 * Wl * 0.01 / 3.78 / np.sqrt(UNITS) + 0.05


def mapfit(y, bits, P, keep):
    n = len(y)
    grp = np.full(n, len(P["windows"]))
    for k, (s0, nn) in enumerate(P["windows"]):
        grp[s0:s0 + nn] = k
    ng = len(P["windows"]) + 1
    sig = np.where(grp < len(P["windows"]), 0.29, 5.0)
    sig = np.where(keep, sig, 1e9)                       # start-up frame: no weight
    B = bits.astype(float)
    O = np.zeros((n, ng)); O[np.arange(n), grp] = 1.0
    A = np.column_stack([O, B @ Wl, B]) / sig[:, None]
    rhs = y / sig
    R = np.zeros((14, ng + 1 + 14)); R[:, ng + 1:] = np.diag(1.0 / SIGW)
    z = np.linalg.lstsq(np.vstack([A, R]), np.concatenate([rhs, np.zeros(14)]), rcond=None)[0]
    g, dw = z[ng], z[ng + 1:]
    w = g * Wl + dw
    w = w * 4095.0 / w.sum()
    res = (np.column_stack([O, B @ Wl, B]) @ z - y)
    return w, {"gain": float(g), "dw_lsb": [round(float(q), 3) for q in dw],
               "rms_residual_windows_lsb": float(np.sqrt(np.mean(res[grp < ng - 1] ** 2))),
               "rms_residual_spread_lsb": float(np.sqrt(np.mean(res[(grp == ng - 1) & keep] ** 2)))}
for rid in runs:
    S = json.load(open(os.path.join(BLOCK, "sim", "results", "r5", rid + "_segments.json")))
    if not S["segments"]:
        res["samples"][rid] = "run did not complete: %s" % S["stopped"]
        continue
    P = json.load(open(os.path.join(BLOCK, S["points"])))
    LSB = P["lsb_V"]
    for i in range(S["mc"]):
        slots, ba, bb = load_segments(os.path.join(BLOCK, "sim", "results", "r5", rid + "_segments.json"), root, "m%d" % i)
        for sl, bits in (("a", ba), ("b", bb)):
            v = np.array(P[sl])[slots]
            # frame 0 is the start-up frame (README revision 5, open issue 1): excluded from both fits
            k0 = np.asarray(slots) > 0
            A = np.column_stack([np.ones(len(v)), bits.astype(float)])[k0]
            x, rsd, rk, _ = np.linalg.lstsq(A, v[k0] / LSB, rcond=None)
            wls = x[1:] * 4095.0 / x[1:].sum()
            # primary ("fit"): plain known-input least squares of all 14 weights; cross-check ("map"): MAP fit
            w = wls
            Wf = np.rint(np.asarray(w) * 8.0).astype(np.int64)    # 1/8 LSB; range not enforced here (see register_check)
            wm, info = mapfit(v / LSB, bits, P, k0)
            Wm = np.rint(np.asarray(wm) * 8.0).astype(np.int64)
            r = {"seed": S["seed"], "rank": int(rk), "fit_rms_residual_lsb": float(np.sqrt(np.mean((A @ x - v[k0] / LSB) ** 2))),
                 "weights_fit_lsb": [round(float(y), 3) for y in w], "W_fit": [int(y) for y in Wf],
                 "weights_map_lsb": [round(float(y), 3) for y in wm], "map_fit": info}
            for tag, W in (("design", Wd), ("fit", Wf), ("map", Wm)):
                win = dnl_windows(P, v, bits, W)
                maj = [abs(z) for q in win.values() for z in q["major_dnl"] if z is not None]
                r[tag] = {"windows": win, "max_abs_dnl": max(q["max_abs_dnl"] for q in win.values()),
                          "max_abs_major_dnl": max(maj) if maj else None,
                          "monotonic": all(q["monotonic"] for q in win.values()),
                          "missing_inside": sum(q["missing_inside"] for q in win.values()),
                          "windows_hold_transitions": all(q["holds_transition"] for q in win.values())}
                summ[tag].append(r[tag])
            r["register_check"] = regcheck(w)
            REG["per_sample"]["%s/m%d%s" % (rid, i, sl)] = {"all_fit": all(q["fits"] for q in r["register_check"]),
                                                          "fraction_of_max": [q["fraction_of_max"] for q in r["register_check"]]}
            res["samples"]["%s/m%d%s" % (rid, i, sl)] = r
for tag in ("design", "fit", "map"):
    L = summ[tag]
    if L:
        mx = [q["max_abs_major_dnl"] for q in L if q["max_abs_major_dnl"] is not None]
        res[tag] = {"n": len(L), "major_dnl_max_abs": {"median": float(np.median(mx)), "max": float(max(mx)),
                                                         "n_le_0p5": int(sum(y <= 0.5 for y in mx))},
                    "window_dnl_max_abs": {"median": float(np.median([q["max_abs_dnl"] for q in L])),
                                           "max": float(max(q["max_abs_dnl"] for q in L))},
                    "all_monotonic": all(q["monotonic"] for q in L), "missing_total": int(sum(q["missing_inside"] for q in L)),
                    "all_windows_hold_transitions": all(q["windows_hold_transitions"] for q in L)}
if REG["per_sample"]:
    fr = np.array([v["fraction_of_max"] for v in REG["per_sample"].values()])     # samples x decision index j
    REG["largest_fraction_of_max_by_register_index"] = {str(13 - j): float(fr[:, j].max()) for j in range(14)}
    REG["smallest_value_fraction_by_register_index"] = {str(13 - j): float(fr[:, j].min()) for j in range(14)}
    REG["all_samples_fit"] = all(v["all_fit"] for v in REG["per_sample"].values())
    REG["saturations"] = [dict(sample=k, **q) for k, r in res["samples"].items() if not isinstance(r, str)
                          for q in r["register_check"] if not q["fits"]]
res["register_width_check"] = REG
json.dump(res, open(out, "w"), indent=1)
print("register check: all fit", REG.get("all_samples_fit"), "largest fraction", REG.get("largest_fraction_of_max_by_register_index"))
for k, r in res["samples"].items():
    if isinstance(r, str):
        print(k, r)
        continue
    print(k, "rank %d rms %.3f | design major %.2f max %.2f mono %s miss %d | fit major %.2f max %.2f mono %s miss %d" % (
        r["rank"], r["fit_rms_residual_lsb"], r["design"]["max_abs_major_dnl"] or -1, r["design"]["max_abs_dnl"], r["design"]["monotonic"],
        r["design"]["missing_inside"], r["fit"]["max_abs_major_dnl"] or -1, r["fit"]["max_abs_dnl"], r["fit"]["monotonic"], r["fit"]["missing_inside"]))
for tag in ("design", "fit", "map"):
    print(tag, res.get(tag))
