#!/usr/bin/env python3
"""Post-process tb_cdac_mc: bit weights per MC sample -> SAR transfer -> DNL / INL (Python 3.6, numpy).

usage: post_cdac_mc.py <bulk raw dir of the run> sim/results/<name>.json

The SAR model is the monotonic algorithm of r1_sar_logic with an ideal comparator (no offset, no noise):
decision j = 0..11 compares top_p with top_n; after decision j <= 10 the capacitor C(10-j) of the side that was
higher steps VREF -> GND, which lowers that top node by the simulated weight. Code transitions are found on a
uniform input grid of 1/64 LSB. DNL and INL use the end-point line through the first and last transitions.
"""
import json
import os
import re
import sys

import numpy as np

NB = 11


def parse(rawdir, vref=1.2):
    """w_b<k>.txt: frequency, then (re, im) of v(tp0) v(tn0) v(tp1) v(tn1) ... -> weights in V for a VREF step."""
    w = None
    for k in range(NB):
        row = [float(x) for x in open(os.path.join(rawdir, "w_b%d.txt" % k)).read().split()]
        re_ = np.array(row[1::2])
        n = len(re_) // 2
        if w is None:
            w = {"p": np.zeros((n, NB)), "n": np.zeros((n, NB))}
        w["p"][:, k] = vref * re_[0::2]
        w["n"][:, k] = vref * re_[1::2]
    return n, w


def transfer(wp, wn, step):
    span = 1.02 * (wp.sum() + wn.sum()) / 2.0 + wp[10]
    vd = np.arange(-span, span, step)
    vp = vd / 2.0
    vn = -vd / 2.0
    code = np.zeros(vd.shape, dtype=np.int64)
    for j in range(12):
        b = vp > vn
        code |= (b.astype(np.int64) << (11 - j))
        if j <= 10:
            k = 10 - j
            vp = vp - b * wp[k]
            vn = vn - (~b) * wn[k]
    return vd, code


def dnl_inl(vd, code):
    trans = np.full(4096, np.nan)               # trans[c] = first vd with code >= c
    cmax = np.maximum.accumulate(code)
    for c in range(1, 4096):
        idx = np.searchsorted(cmax, c)
        if idx < len(vd):
            trans[c] = vd[idx]
    lsb = (trans[4095] - trans[1]) / 4094.0
    width = np.diff(trans[1:])                  # widths of codes 1..4094
    dnl = width / lsb - 1.0
    inl = (trans[1:] - (trans[1] + lsb * np.arange(4095))) / lsb
    hist = np.bincount(code, minlength=4096)
    missing = int(np.sum(hist[1:4095] == 0))
    return lsb, dnl, inl, missing


def main():
    rawdir, out = sys.argv[1], sys.argv[2]
    n, w = parse(rawdir)
    vref = 1.2
    res = []
    dnl_all = []
    inl_all = []
    for i in range(n):
        wp, wn = w["p"][i], w["n"][i]
        step = wp[0] / 64.0
        vd, code = transfer(wp, wn, step)
        lsb, dnl, inl, missing = dnl_inl(vd, code)
        dnl_all.append(dnl)
        inl_all.append(inl)
        res.append({"sample": i, "lsb_uV": lsb * 1e6, "dnl_max": float(np.nanmax(np.abs(dnl))),
                    "inl_max": float(np.nanmax(np.abs(inl))), "missing_codes": missing,
                    "weights_p_mV": [round(x * 1e3, 5) for x in wp], "weights_n_mV": [round(x * 1e3, 5) for x in wn]})
    dnl_all = np.array(dnl_all)
    inl_all = np.array(inl_all)
    dmax = np.array([r["dnl_max"] for r in res])
    imax = np.array([r["inl_max"] for r in res])
    sd_dnl_code = np.nanstd(dnl_all, axis=0)    # index c-1 -> code c
    worst = np.argsort(sd_dnl_code)[::-1][:8]
    # relative weight error of the MSB-array units, mean over samples (p side), expressed in LSB
    w0 = np.median(w["p"][:, 0])
    summary = {
        "deck": "tb_cdac_mc.cir", "samples": n, "label": "simulated (CDAC MIM mismatch only: AC-solved weights, behavioural SAR with ideal comparator)",
        "unit": "cap_cmim 3.78 x 3.78 um (22.04 fF), cap_typ_mismatch, mm_ok=1",
        "lsb_median_uV": float(np.median([r["lsb_uV"] for r in res])),
        "ideal_lsb_uV": 2 * vref / 4096 * 1e6,
        "weight_c0_median_uV": float(w0 * 1e6),
        "dnl_max_abs": {"mean": float(dmax.mean()), "sd": float(dmax.std()), "max": float(dmax.max()),
                        "median": float(np.median(dmax)), "fraction_le_0p5": float(np.mean(dmax <= 0.5)),
                        "fraction_le_1p0": float(np.mean(dmax <= 1.0))},
        "inl_max_abs": {"mean": float(imax.mean()), "sd": float(imax.std()), "max": float(imax.max()),
                        "median": float(np.median(imax)), "fraction_le_1p0": float(np.mean(imax <= 1.0)),
                        "fraction_le_2p0": float(np.mean(imax <= 2.0))},
        "samples_with_missing_codes": int(sum(1 for r in res if r["missing_codes"] > 0)),
        "dnl_sd_by_code_worst": [{"code": int(c + 1), "dnl_sd": float(sd_dnl_code[c])} for c in worst],
        "per_sample": res,
    }
    # derived (not simulated): weight deviations scaled by 1/sqrt(area factor) of every unit (all arrays)
    nom = {sd: np.median(w[sd], axis=0) for sd in ("p", "n")}
    scaled = []
    for af in (2, 4, 9, 16):
        dm = []
        for i in range(n):
            wp = nom["p"] + (w["p"][i] - nom["p"]) / np.sqrt(af)
            wn = nom["n"] + (w["n"][i] - nom["n"]) / np.sqrt(af)
            vd, code = transfer(wp, wn, wp[0] / 32.0)
            _, dnl, _, _ = dnl_inl(vd, code)
            dm.append(float(np.nanmax(np.abs(dnl))))
        dm = np.array(dm)
        scaled.append({"unit_area_factor": af, "unit_fF_approx": round(22.04 * af, 1), "dnl_max_median": float(np.median(dm)),
                       "dnl_max_max": float(dm.max()), "fraction_le_0p5": float(np.mean(dm <= 0.5))})
    summary["derived_unit_scaling"] = {"label": "derived from the same draws (deviation / sqrt(area factor)), not simulated",
                                       "rows": scaled}
    with open(out, "w") as f:
        json.dump(summary, f, indent=1)
    print(json.dumps({k: v for k, v in summary.items() if k != "per_sample"}, indent=1))


if __name__ == "__main__":
    main()
