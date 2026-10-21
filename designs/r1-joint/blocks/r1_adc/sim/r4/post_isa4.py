#!/usr/bin/env python3
"""Revision-4 D18 frame sequence (tb_adc4_isa.cir, full core, r1_refbuf4): codes per frame and slice with the
design weights against the ideal code 2047.5 + v / LSB, LSB = 446.4 uV x VREF (VREF measured at the sampling
edge); track window of every frame and slice (selected track signal above 0.6 V before the edge); conversion
time (latch after the sampling edge, ticks); average IDD (1.2 V) and IDDA (3.3 V buffer).
usage: post_isa4.py <run id> OUT.json"""
import json
import os
import sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "r3"))
from p4common import read, ts, sample, bits_from_raw, BLOCK, TLAT, T
import cal3
rid, out = sys.argv[1:3]
root = os.environ["G1_RESULTS_ROOT"]
Wd = cal3.quantise(json.load(open(os.path.join(BLOCK, "sim", "results", "r3", "cdac3_mc50_tt_cp100_globalfit.json")))["nominal_design_weights_lsb"])
d, _ = read(os.path.join(root, "r1_adc", rid, "codes.raw"))
SEQ = [("enc", "0", 0.40, -0.40), ("cur", "1", 0.85, -0.85), ("enc", "0", -0.40, 0.40), ("enc", "0", 0.72, -0.72)]
res = {"label": "simulated (tb_adc4_isa.cir, r1_adc4_core full core, r1_refbuf4), design weights", "run": rid, "frames": []}
t = d["time"]
for f, (kind, inp, va, vb) in enumerate(SEQ):
    row = {"frame": f, "input": kind}
    for sl, v in (("a", va), ("b", vb)):
        e = float(ts(f, sl))
        vr = float(sample(d, "v(vref)", [e - 0.2e-9])[0])
        lsb = 446.4e-6 * vr / 1.0
        c = int(cal3.code(bits_from_raw(sample(d, "v(raw%s)" % sl, [e + TLAT])), Wd)[0])
        x = d["v(trk%s%s)" % (sl, inp)]
        m = (t > e - 400e-9) & (t < e - 0.01e-9)
        hi = t[m][x[m] > 0.6]
        m2 = (t > e) & (t < e + 600e-9)
        la = t[m2][d["v(lat%s)" % sl][m2] > 0.6]
        row[sl] = {"vin_V": v, "code": c, "ideal_code": round(2047.5 + v / lsb, 1), "error_lsb": round(c - (2047.5 + v / lsb), 2),
                   "track_ns": round(float(hi.max() - hi.min()) * 1e9, 1) if hi.size else None,
                   "latch_after_edge_ticks": round(float(la.min() - e) / T, 2) if la.size else None, "vref_V": round(vr, 5)}
    res["frames"].append(row)
m = t > 0.6e-6
res["idd_mA"] = float(-np.mean(d["i(vdd)"][m]) * 1e3)
if "i(vdda)" in d:
    res["idda_mA"] = float(-np.mean(d["i(vdda)"][m]) * 1e3)
res["max_abs_error_lsb"] = max(abs(r[s]["error_lsb"]) for r in res["frames"] for s in ("a", "b"))
res["min_track_ns"] = min(r[s]["track_ns"] for r in res["frames"] for s in ("a", "b"))
json.dump(res, open(out, "w"), indent=1)
print(json.dumps(res, indent=1))
