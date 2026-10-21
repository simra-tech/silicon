#!/usr/bin/env python3
"""r1_safe comparator hysteresis in units of the calibration step (VREF/252 = 4.1667 mV Vod = LSB/8), and the error of the
two-sided average of r1_ctrl 0.3 as a function of the hysteresis.
Part A: hysteresis = up - dn (trip minus release, DC sweep, 0.5 mV resolution) from tb_safe_dcmc3 summaries
        (MC: one draw per sample; nominal corner runs: one sample per corner), at all 13 thresholds and at the
        calibration points (cell frame -0.5654 V for OC, +0.5654 V for NEG).
Part B: model of the search with continuous hysteresis h (steps) and a uniformly distributed sub-step position u of the
        centre: k_rel = floor(u) + 1, k_trip = ceil(u - h) - 1, k_cal = floor((k_rel + k_trip - IDEAL2)/2) + 32 with
        IDEAL2 = 72 (OC) / 55 (NEG) against the real-valued centre code; error in steps.
Usage: python3 analyze_hyst.py OUT_DIR RUN_ID [RUN_ID ...]   (run ids under sim/results/)"""
import sys, os, json, math, numpy as np
VREF = 1.05; STEP = VREF / 252 * 1e3      # mV
here = os.path.dirname(os.path.abspath(__file__))
odir = sys.argv[1]; os.makedirs(odir, exist_ok=True)
CAL = {"OC": -0.565385, "NEG": 0.565385}
res = {}
def stat(v):
    v = np.array(v); return {"n": len(v), "mean": float(v.mean()), "sigma": float(v.std()), "min": float(v.min()), "max": float(v.max())}
for run in sys.argv[2:]:
    S = json.load(open(os.path.join(here, "results", run, "summary.json")))["samples"]
    groups = {}
    for s in S:
        corner = s["sample"].split(":")[0] if ":" in s["sample"] else {"4": "ss_mm", "5": "ff_mm"}.get(s["sample"].split("_")[0], "tt_mm")
        g = groups.setdefault(corner, {"all": [], "OC_cal": [], "NEG_cal": []})
        for q in s["pts"]:
            if q["up_V"] is None or q["dn_V"] is None: continue
            h = (q["up_V"] - q["dn_V"]) * 1e3 / STEP
            g["all"].append(h)
            for role, vc in CAL.items():
                if abs(q["th_V"] - vc) < 1e-4: g[role + "_cal"].append(h)
    for c, g in groups.items():
        res["%s/%s" % (run, c)] = {k: stat(v) for k, v in g.items() if v}
# Part B: u = real-valued code coordinate of the release crossing (k_rel = floor(u) + 1), centre = u - h/2 in codes,
# target code = 32 + (u - h/2) - k_ideal (exact), stored code = 32 + floor((k_rel + k_trip - IDEAL2)/2)
q = {}
for role, i2, kid in (("OC", 72, 36.31), ("NEG", 55, 27.69)):
    row = {}
    for h in (1.0, 1.5, 2.0, 2.5, 3.0, 3.5):
        u = kid + np.linspace(-4, 4, 16001)[:-1]
        krel = np.floor(u) + 1; ktrip = np.ceil(u - h) - 1
        e = np.floor((krel + ktrip - i2) / 2) - (u - h / 2 - kid)
        row["h=%.1f" % h] = {"min": float(e.min()), "max": float(e.max()), "rms": float(np.sqrt((e ** 2).mean())), "max_abs": float(np.abs(e).max())}
    q[role] = row
json.dump({"hysteresis_steps": res, "step_mV_Vod": STEP, "step_LSB": 0.125, "search_error_model_steps": q,
           "note": "search_error_model: error = stored code - exact target code, in calibration steps, over all sub-step phases u of the comparator centre (continuous hysteresis h in steps; no noise, no code-change transient)"},
          open(os.path.join(odir, "summary.json"), "w"), indent=1)
for k, v in res.items():
    print(k, {kk: (round(vv["mean"], 2), round(vv["sigma"], 2), round(vv["min"], 2), round(vv["max"], 2)) for kk, vv in v.items()})
for role, row in q.items():
    print(role, {h: (round(x["min"], 2), round(x["max"], 2), round(x["rms"], 2)) for h, x in row.items()})
