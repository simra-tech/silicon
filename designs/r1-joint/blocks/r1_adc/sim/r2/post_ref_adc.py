#!/usr/bin/env python3
"""Compare tb_adc2_ref.cir conversions with r1_refbuf (buf) and with an ideal VREF at the buffer DC level (ideal).
usage: post_ref_adc.py <buf codes.raw> <ideal codes.raw> <weights.json> OUT.json
Frames 0..7 hold vd = 0, +0.88, -0.88, +0.44, -0.44, +0.0003, +0.87, -0.87 V (slice A: vd, slice B: -vd)."""
import json
import os
import sys

import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import post_adc2 as p
from rawread import read

buf, ideal, wfile, out = sys.argv[1:5]
jw = json.load(open(wfile))
W = np.array(jw["W"] if "W" in jw else jw["weights_ramp_calibrated_W"], dtype=np.int64)
VD = [0, 0.88, -0.88, 0.44, -0.44, 0.0003, 0.87, -0.87]
res = {"label": "simulated (schematic, fast core both slices, tt 27 C, r1_refbuf msf 16 mib 80 ndec 6 ncg 1 vs ideal VREF)",
       "weights_from": os.path.basename(wfile), "frames": []}
cb = {}
for name, path in (("buf", buf), ("ideal", ideal)):
    f, ra, rb = p.words(path)
    cb[name] = (p.codes(ra[:8], W), p.codes(rb[:8], W))
for i in range(8):
    res["frames"].append({"vd_V": VD[i], "codeA_buf": int(cb["buf"][0][i]), "codeA_ideal": int(cb["ideal"][0][i]),
                          "codeB_buf": int(cb["buf"][1][i]), "codeB_ideal": int(cb["ideal"][1][i])})
dA = cb["buf"][0] - cb["ideal"][0]
dB = cb["buf"][1] - cb["ideal"][1]
res["max_abs_code_error_lsb"] = int(max(np.abs(dA).max(), np.abs(dB).max()))
d, _ = read(buf, ["time", "v(vref)"])
m = d["time"] > 1e-6
res["vref_buf_V"] = {"min": float(d["v(vref)"][m].min()), "max": float(d["v(vref)"][m].max()),
                     "mean": float(d["v(vref)"][m].mean())}
json.dump(res, open(out, "w"), indent=1)
print(json.dumps(res, indent=1))
