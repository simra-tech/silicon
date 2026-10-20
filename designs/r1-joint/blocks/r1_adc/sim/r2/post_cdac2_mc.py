#!/usr/bin/env python3
"""Revision-2 CDAC mismatch MC through the digital weight correction (Python 3.6, numpy).

usage: post_cdac2_mc.py <bulk dir of a tb_cdac2_mc run> sim/results/<name>.json [--noise-uV 60] [--ktc-uV 108]

Per MC sample (weights from the AC-solved array, VREF = 1.0 V):
  (1) uncorrected: design (nominal) weights applied to the raw bits of the mismatched array;
  (2) bench calibration: a ramp over +-0.995 FS with M = 16 conversions per LSB, comparator noise and kT/C noise
      on every conversion (values from the command line), least-squares weights, quantised to 14 bit (11.3);
  (3) corrected transfer: noiseless fine ramp (1/32 LSB), code = sat12((sum b W + 4) >> 3), end-point DNL/INL.
Pass criteria (task): max |DNL| <= 0.5 LSB; no missing codes in >= 48 of 50 samples.
Derived unit scaling (not simulated): mismatch deviations / sqrt(area factor) for the samples that fail.
"""
import json
import os
import sys

import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sar2_model as m

NB = 12


def parse(rawdir, vref=1.0):
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


def evaluate(wp, wn, Wnom, noise, ktc, rng, M=16, fine=32):
    fs = m.full_scale(wp, wn)
    lsb = 2 * fs / 4096
    # (1) uncorrected
    vd = np.arange(-fs * 1.002, fs * 1.002, lsb / fine)
    bits = m.convert(vd, wp, wn)
    lsb_u, dnl_u, inl_u, miss_u, nm_u = m.dnl_inl(vd, m.code_from_bits(bits, m.quantise(Wnom)))
    # (2) bench ramp with noise
    vr = np.linspace(-0.995 * fs, 0.995 * fs, int(4096 * 0.995 * M))
    vr_n = vr + rng.normal(0, ktc, vr.size)
    rb = m.convert(vr_n, wp, wn, noise=noise, rng=rng)
    wext = m.extract_weights(rb, np.arange(vr.size))
    W = m.quantise(wext)
    # (3) corrected, noiseless fine ramp
    lsb_c, dnl_c, inl_c, miss_c, nm_c = m.dnl_inl(vd, m.code_from_bits(bits, W))
    return {"fs_V": fs, "lsb_uV": lsb_c * 1e6,
            "uncorrected": {"dnl_max": float(np.nanmax(np.abs(dnl_u))), "inl_max": float(np.nanmax(np.abs(inl_u))),
                            "missing_codes": miss_u},
            "corrected": {"dnl_max": float(np.nanmax(np.abs(dnl_c))), "dnl_min": float(np.nanmin(dnl_c)),
                          "inl_max": float(np.nanmax(np.abs(inl_c))), "missing_codes": miss_c, "non_monotonic": nm_c},
            "weights_W": [int(x) for x in W]}


def main():
    rawdir, out = sys.argv[1], sys.argv[2]
    noise = float(sys.argv[sys.argv.index("--noise-uV") + 1]) * 1e-6 if "--noise-uV" in sys.argv else 60e-6
    ktc = float(sys.argv[sys.argv.index("--ktc-uV") + 1]) * 1e-6 if "--ktc-uV" in sys.argv else 108e-6
    n, w = parse(rawdir)
    rng = np.random.RandomState(20261020)
    nom_p, nom_n = np.median(w["p"], axis=0), np.median(w["n"], axis=0)
    Wnom = m.nominal_weights_lsb(nom_p, nom_n)
    res = [evaluate(w["p"][i], w["n"][i], Wnom, noise, ktc, rng) for i in range(n)]
    for i, r in enumerate(res):
        r["sample"] = i
    dc = np.array([r["corrected"]["dnl_max"] for r in res])
    ic = np.array([r["corrected"]["inl_max"] for r in res])
    du = np.array([r["uncorrected"]["dnl_max"] for r in res])
    mc = np.array([r["corrected"]["missing_codes"] for r in res])
    mu = np.array([r["uncorrected"]["missing_codes"] for r in res])
    S = {"label": "simulated weights (AC-solved, cap_typ_mismatch) + behavioural SAR/correction model (sar2_model.py)",
         "samples": n, "vref_V": 1.0,
         "bench_calibration": {"ramp_conversions_per_lsb": 16, "comparator_noise_uV": noise * 1e6,
                               "ktc_noise_uV": ktc * 1e6, "weights": "14 bit, 11.3 fixed point, sum 4095 LSB"},
         "nominal_design_weights_lsb": [round(x, 3) for x in Wnom],
         "full_scale_diff_V_median": float(np.median([r["fs_V"] for r in res])),
         "uncorrected": {"dnl_max_median": float(np.median(du)), "dnl_max_max": float(du.max()),
                         "samples_dnl_le_0p5": int(np.sum(du <= 0.5)), "samples_with_missing_codes": int(np.sum(mu > 0))},
         "corrected": {"dnl_max_median": float(np.median(dc)), "dnl_max_max": float(dc.max()),
                       "samples_dnl_le_0p5": int(np.sum(dc <= 0.5)),
                       "samples_without_missing_codes": int(np.sum(mc == 0)),
                       "inl_max_median": float(np.median(ic)), "inl_max_max": float(ic.max()),
                       "samples_inl_le_1p0": int(np.sum(ic <= 1.0))},
         "pass_dnl_0p5_all": bool(np.all(dc <= 0.5)),
         "pass_missing_codes_48_of_50": bool(np.sum(mc == 0) >= 48 * n / 50.0),
         "per_sample": res}
    with open(out, "w") as f:
        json.dump(S, f, indent=1)
    print(json.dumps({k: v for k, v in S.items() if k != "per_sample"}, indent=1))


if __name__ == "__main__":
    main()
