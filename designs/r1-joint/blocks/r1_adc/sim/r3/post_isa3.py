#!/usr/bin/env python3
"""Revision-3 mux sequence (tb_adc3_isa.cir, full core): codes per slot and slice with design weights against the
ideal code 2047.5 + v / LSB (LSB from the residue analysis of the ideal-VREF run, post_ref3.py output).
usage: post_isa3.py <run id> <ref json> OUT.json"""
import json
import os
import sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p3common import read, ts, sample, bits_from_raw, BLOCK, H
import cal3

rid, refj, out = sys.argv[1:4]
root = os.environ["G1_RESULTS_ROOT"]
Wd = cal3.quantise(json.load(open(os.path.join(BLOCK, "sim", "results", "r3", "cdac3_mc50_tt_cp100_globalfit.json")))["nominal_design_weights_lsb"])
R = json.load(open(refj))
d, _ = read(os.path.join(root, "r1_adc", rid, "codes.raw"))
SEQ = [("enc", 0.40, -0.40), ("cur", 0.85, -0.85), ("enc", -0.40, 0.40), ("cur", -0.85, 0.85), ("enc", 0.72, -0.72)]
res = {"label": "simulated (tb_adc3_isa.cir, r1_adc3_core full core, ideal VREF 1.0 V), design weights", "run": rid, "slots": []}
t = d["time"]
for s, (kind, va, vb) in enumerate(SEQ):
    row = {"slot": s, "input": kind}
    for sl, v in (("a", va), ("b", vb)):
        lsb = R["slices"][sl]["lsb_uV_at_1V"] * 1e-6
        c = int(cal3.code(bits_from_raw(sample(d, "v(raw%s)" % sl, [ts(s) + 260e-9])), Wd)[0])
        row[sl] = {"vin_V": v, "code": c, "ideal_code": round(2047.5 + v / lsb, 1), "error_lsb": round(c - (2047.5 + v / lsb), 2)}
    # track windows of this slot (track signal of the selected input high before the edge)
    for nm in ("trka0", "trka1", "trkb0", "trkb1"):
        x = d["v(%s)" % nm]
        m = (t > ts(s) - 400e-9) & (t < ts(s) - 1e-9)
        hi = t[m][x[m] > 0.6]
        if hi.size:
            row["track_ns_" + nm] = round((hi.max() - hi.min()) * 1e9, 1)
    m = (t > ts(s)) & (t < ts(s) + 400e-9)
    la = t[m][d["v(lata)"][m] > 0.6]
    row["latch_after_edge_ticks"] = round((la.min() - ts(s)) * 30e6, 2) if la.size else None
    res["slots"].append(row)
res["max_abs_error_lsb"] = max(abs(r[s]["error_lsb"]) for r in res["slots"] for s in ("a", "b"))
json.dump(res, open(out, "w"), indent=1)
print(json.dumps(res, indent=1))
