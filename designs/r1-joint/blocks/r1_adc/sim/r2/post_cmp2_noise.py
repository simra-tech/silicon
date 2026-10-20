#!/usr/bin/env python3
"""Comparator input-referred noise, method A (quasi-static).
usage: post_cmp2_noise.py <noise_X.txt> <cmp2_tran_*.json> <variant>_cm<CM> OUT.json
noise_X.txt: ngspice wrdata of the first-stage .noise run (frequency, inoise V/sqrt(Hz)) at the integration
operating point (tb_cmp2_noise.cir). The first stage integrates for T_int = t_dec - 1 ns (t_dec from the
transient deck at the same corner and common mode; 1 ns is the latch regeneration after the integration).
sigma^2 = integral S_in(f) * sinc^2(pi f T_int) df (integrator of length T_int; one-sided PSD)."""
import json
import sys
import numpy as np

nf, tj, key, out = sys.argv[1:5]
a = np.loadtxt(nf, skiprows=1)
f, vn = a[:, 0], a[:, 1]
tdec = json.load(open(tj))[key]["t_dec_ns"] * 1e-9
T = tdec - 1e-9
w = np.sinc(f * T) ** 2          # numpy sinc(x) = sin(pi x)/(pi x)
sig = float(np.sqrt(np.trapz(vn ** 2 * w, f)))
res = {"label": "simulated PSD (.noise, quasi-static) + derived integration window", "noise_file": nf.split("/")[-2] + "/" + nf.split("/")[-1],
       "tran_file": tj.split("/")[-1], "key": key, "t_dec_ns": tdec * 1e9, "T_int_ns": T * 1e9,
       "white_level_nV_per_rtHz_at_100MHz": float(np.interp(1e8, f, vn) * 1e9),
       "sigma_uV_rms": sig * 1e6}
json.dump(res, open(out, "w"), indent=1)
print(json.dumps(res))
