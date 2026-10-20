#!/usr/bin/env python3
"""Revision-3 comparator input noise, method A of revision 2 (quasi-static first-stage PSD at the integration
operating point, CM 0.1 V, integrated with the sinc^2 window of an integrator of length T_int = t_dec - 1 ns,
t_dec from tb_cmp3_tran at the same corner and CM 0.1 V). All variants, all corners.
usage: post_cmp3_noise.py <bulk root>/r1_adc OUT.json"""
import json
import os
import sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_cmp3_decks import VARIANTS, SET
SFX = "" if SET == "a" else "_" + SET

root, out = sys.argv[1], sys.argv[2]
RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results", "r3")
res = {"label": "simulated PSD (.noise, quasi-static, CM 0.1 V, dip/din at 0.3 V) + derived integration window "
                "T_int = t_dec(CM 0.1 V) - 1 ns (revision-2 method A)", "target_uV": 60.0}
for c in ("tt27", "ss125", "ffm40"):
    tr = json.load(open(os.path.join(RES, "cmp3_tran_%s%s.json" % (c, SFX))))
    for v in VARIANTS:
        a = np.loadtxt(os.path.join(root, "r3-cmp-noise-%s-cm01-%s" % (c, SET), "noise_%s.txt" % v), skiprows=1)
        f, vn = a[:, 0], a[:, 1]
        tdec = tr[v]["cm0.10"]["t_dec_ns"]
        T = (tdec - 1.0) * 1e-9
        sig = float(np.sqrt(np.trapz(vn ** 2 * np.sinc(f * T) ** 2, f)))
        res.setdefault(v, {})[c] = {"t_dec_cm01_ns": tdec, "t_dec_cm035_ns": tr[v]["cm0.35"]["t_dec_ns"],
                                    "t_dec_cm06_ns": tr[v]["cm0.60"]["t_dec_ns"], "T_int_ns": T * 1e9,
                                    "white_nV_rtHz_100MHz": float(np.interp(1e8, f, vn) * 1e9), "sigma_uV": sig * 1e6,
                                    "supply_uA_3cmp_continuous_clock": tr[v]["supply_uA_3cmp_plus_bias"]}
json.dump(res, open(out, "w"), indent=1)
print("variant  " + "  ".join("%-34s" % c for c in ("tt27", "ss125", "ffm40")))
for v in VARIANTS:
    print("%-6s %s" % (v, "  ".join("sig %5.1f uV tdec %5.2f/%5s ns" % (res[v][c]["sigma_uV"], res[v][c]["t_dec_cm01_ns"],
          "%.2f" % res[v][c]["t_dec_cm035_ns"] if res[v][c]["t_dec_cm035_ns"] else "-") for c in ("tt27", "ss125", "ffm40"))))
