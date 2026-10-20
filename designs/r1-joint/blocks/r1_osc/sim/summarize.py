#!/usr/bin/env python3
"""Collect the rev r1 runs of R1_OSC into sim/results/summary_r1.json (checks and key numbers, all simulated).
Usage (host or container, from the block directory): python3 sim/summarize.py"""
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def load(run):
    fn = os.path.join(HERE, "runs", run, "results.json")
    return json.load(open(fn)) if os.path.exists(fn) else None


def trim_check(rows):
    rows = sorted(rows, key=lambda r: r["code"])
    f = [r["f_MHz"] for r in rows]
    steps = [(f[i] - f[i + 1]) / f[i] * 100 for i in range(len(f) - 1)]
    return {"f_code0_MHz": f[0], "f_code31_MHz": f[-1], "monotonic": all(s > 0 for s in steps),
            "step_max_pct": max(steps), "step_min_pct": min(steps), "n_codes": len(f)}


def stats(x):
    m = sum(x) / len(x)
    s = math.sqrt(sum((v - m) ** 2 for v in x) / (len(x) - 1))
    return {"mean": m, "sigma": s, "min": min(x), "max": max(x), "n": len(x)}


out = {"revision": "r1", "label": "simulated (schematic level, ngspice 46, PDK 84374023)"}
t = load("r1a-trim32-tt")
if t:
    tc = trim_check(t)
    nom = min(t, key=lambda r: abs(r["f_MHz"] - 30.0))
    tc.update(code_nearest_30MHz=nom["code"], f_at_that_code_MHz=nom["f_MHz"],
              f_code16_MHz=[r for r in t if r["code"] == 16][0]["f_MHz"],
              idd_uA_range=[min(r["idd_uA"] for r in t), max(r["idd_uA"] for r in t)],
              duty_pct_range=[min(r["duty_pct"] for r in t), max(r["duty_pct"] for r in t)],
              tloop_ns_range=[min(r["tloop_ns"] for r in t), max(r["tloop_ns"] for r in t)])
    out["trim_tt_1.2V_27C"] = tc
r = load("r1a-reach")
if r:
    for key in sorted(set((x["corner"], x["vdd"], x["temp"]) for x in r)):
        rows = [x for x in r if (x["corner"], x["vdd"], x["temp"]) == key]
        out["trim_%s_%gV_%gC" % key] = dict(trim_check(rows),
                                            tloop_ns_max=max(x["tloop_ns"] for x in rows),
                                            idd_uA_max=max(x["idd_uA"] for x in rows))
for code in (16, 22):
    c = load("r1a-corners27-c%d" % code)
    if c:
        ref = [x for x in c if x["corner"] == "tt" and x["vdd"] == 1.2 and x["temp"] == 27][0]["f_MHz"]
        lo = min(c, key=lambda x: x["f_MHz"])
        hi = max(c, key=lambda x: x["f_MHz"])
        out["corners27_code%d" % code] = {
            "f_tt_MHz": ref, "f_min_MHz": lo["f_MHz"], "at_min": [lo["corner"], lo["vdd"], lo["temp"]],
            "f_max_MHz": hi["f_MHz"], "at_max": [hi["corner"], hi["vdd"], hi["temp"]],
            "spread_pct": [(lo["f_MHz"] / ref - 1) * 100, (hi["f_MHz"] / ref - 1) * 100],
            "duty_pct_range": [min(x["duty_pct"] for x in c), max(x["duty_pct"] for x in c)],
            "idd_uA_range": [min(x["idd_uA"] for x in c), max(x["idd_uA"] for x in c)],
            "tloop_ns_max": max(x["tloop_ns"] for x in c), "n": len(c)}
m = load("r1a-mc50")
if m:
    ok = [x for x in m if "f_MHz" in x]
    out["mc50_tt_code16"] = {"f_MHz": stats([x["f_MHz"] for x in ok]), "duty_pct": stats([x["duty_pct"] for x in ok]),
                             "idd_uA": stats([x["idd_uA"] for x in ok]), "tloop_ns": stats([x["tloop_ns"] for x in ok]),
                             "vth_V": stats([x["vth"] for x in ok]), "n_failed": len(m) - len(ok)}
    s = out["mc50_tt_code16"]["f_MHz"]
    s["sigma_pct"] = s["sigma"] / s["mean"] * 100
p = load("r1a-psrr")
if p:
    out["psrr_tt_code16"] = {x["case"]: {k: v for k, v in x.items() if k not in ("deck", "corner", "vdd", "temp", "code", "tag")}
                             for x in p}
s = load("r1a-startup")
if s:
    out["startup_code16"] = [{k: v for k, v in x.items() if k not in ("deck", "tag")} for x in s]
n = load("r1b-cmpnoise")
if n:
    out["cmpnoise_tt"] = {k: v for k, v in n[0].items() if k not in ("deck", "tag")}
jit = {}
for run in ("r1b-jitter", "r1c-jitter-ref"):
    for x in load(run) or []:
        if x["rc"] == 0:
            jit[x["case"]] = dict({k: v for k, v in x.items() if k not in ("deck", "tag")}, run=run)
if jit:
    out["jitter_tt_code22"] = jit
mr = load("r1a-mcreach")
if mr:
    ok = [x for x in mr if "f_MHz" in x]
    f = stats([x["f_MHz"] for x in ok])
    f["sigma_pct"] = f["sigma"] / f["mean"] * 100
    out["mcreach_ss_1.08V_125C_code0"] = {"f_MHz": f, "n_below_32MHz": sum(1 for x in ok if x["f_MHz"] < 32.0),
                                          "duty_pct": stats([x["duty_pct"] for x in ok]), "n_failed": len(mr) - len(ok)}
os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
with open(os.path.join(HERE, "results", "summary_r1.json"), "w") as f:
    json.dump(out, f, indent=1)
print(json.dumps(out, indent=1))
