#!/usr/bin/env python3
"""Revision 5: PSD of the ngspice TRNOISE sources of tb_trnoise_cal.cir (Welch, one-sided) and the source
parameters that reproduce the r1_bgr vref noise density (run bgr-noise-20261021-b, summary-20261021.json).
White: S = k_w * NA^2 * NT. 1/f: S(f) = k_f * NAMP^2 / f^1.15 (fit at 1-30 kHz). The r1_bgr density is modelled
as floor (density at 200 kHz) + a 1/f term fitted at 1 kHz.
usage: post_trnoise_cal.py <run id> OUT.json"""
import json
import os
import sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
BLOCK = os.path.dirname(os.path.dirname(HERE))
rid, out = sys.argv[1:3]
a = np.loadtxt(os.path.join(os.environ["G1_RESULTS_ROOT"], "r1_adc", rid, "trnoise.txt"))
t, w, f1 = a[:, 0], a[:, 1], a[:, 3]
dt = t[1] - t[0]


def welch(x, n=2 ** 15):
    win = np.hanning(n)
    segs = [x[i:i + n] for i in range(0, len(x) - n + 1, n // 2)]
    p = np.mean([np.abs(np.fft.rfft((s - s.mean()) * win)) ** 2 for s in segs], axis=0)
    p = 2 * p * dt / np.sum(win ** 2)
    return np.fft.rfftfreq(n, dt), p


fw, pw = welch(w)
ff, pf = welch(f1)
NT, NA, NAMP, AL = 50e-9, 1e-3, 1e-3, 1.15
m = (fw > 1e5) & (fw < 2e6)
kw = float(np.median(pw[m]) / (NA ** 2 * NT))
m2 = (ff > 1e3) & (ff < 3e4)
kf = float(np.median(pf[m2] * ff[m2] ** AL) / NAMP ** 2)
B = json.load(open(os.path.join(BLOCK, "..", "r1_bgr", "sim", "results", "summary-20261021.json")))["noise"]
res = {"label": "simulated (TRNOISE PSD, tb_trnoise_cal.cir) + derived source parameters", "run": rid, "NT_s": NT,
       "k_white": kw, "k_flicker": kf, "alpha": AL, "corners": {}}
for c in ("tt27", "ss125"):
    floor = B[c]["floor_nV_rtHz"] * 1e-9
    d1k = B[c]["density_nV_rtHz"]["1000"] * 1e-9
    na = floor / np.sqrt(kw * NT)
    s1f = max(d1k ** 2 - floor ** 2, 0.0) * 1e3 ** AL          # S_1/f(f) = s1f / f^alpha
    namp = np.sqrt(s1f / kf)
    res["corners"][c] = {"floor_nV_rtHz": B[c]["floor_nV_rtHz"], "density_1kHz_nV_rtHz": B[c]["density_nV_rtHz"]["1000"],
                         "NA_V": float(na), "NAMP_V": float(namp),
                         "model_density_10kHz_nV_rtHz": float(np.sqrt(floor ** 2 + s1f / 1e4 ** AL) * 1e9),
                         "bgr_density_10kHz_nV_rtHz": B[c]["density_nV_rtHz"]["10000"]}
json.dump(res, open(out, "w"), indent=1)
print(json.dumps(res, indent=1))
