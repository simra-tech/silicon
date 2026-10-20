#!/usr/bin/env python3
"""Collect tb_safe_mc3: per sample the calibration search result (CAL3 lines) and, with the codes applied, the
shunt-referred threshold-centre error, hysteresis and delay at 10 % overdrive (MC3 lines)."""
import sys, os, json, glob, statistics as st
rdir, tdir = sys.argv[1], sys.argv[2]
cfg = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "tb_safe_mc3.json")))
LSB = cfg["LSB_shunt_V"] * 1e6          # uV shunt (2.381 mV)
rows = {}
def parse(line):
    p = line.replace("=", " = ").split(); d = {}
    for i, t in enumerate(p):
        if i + 2 < len(p) + 1 and i + 1 < len(p) and p[i + 1] == "=" and i + 2 < len(p):
            try: d[t] = float(p[i + 2])
            except ValueError: d[t] = p[i + 2]
    return p[1], d
for f in sorted(glob.glob(os.path.join(rdir, "*.log"))):
    corner = os.path.basename(f)[len("tb_safe_mc3_"):-4]
    for line in open(f, errors="replace"):
        if line.startswith("CAL3 ") or line.startswith("MC3 "):
            i, d = parse(line); key = "%s_%03d" % (corner, int(float(i)))
            rows.setdefault(key, {"sample": key}).update(d)
R = list(rows.values())
def s(v): return {"n": len(v), "mean": st.mean(v), "sigma": st.pstdev(v), "min": min(v), "max": max(v)} if v else None
def num(r, k): return r.get(k) if isinstance(r.get(k), float) else None
res = {}
for c in ("oc", "ng"):
    e = [num(r, c + "_err_uV") for r in R if num(r, c + "_err_uV") is not None]
    res[c] = {"centre_err_uV_shunt": s(e), "centre_err_LSB": s([x / LSB for x in e]),
              "within_0p25LSB": sum(1 for x in e if abs(x) <= 0.25 * LSB), "within_0p5LSB": sum(1 for x in e if abs(x) <= 0.5 * LSB),
              "hyst_uV_shunt": s([num(r, c + "_hyst_uV") for r in R if num(r, c + "_hyst_uV") is not None]),
              "delay_10pct_ns": s([num(r, c + "_dly_ns") for r in R if num(r, c + "_dly_ns") is not None]),
              "k_cal": s([num(r, c + "_kc") for r in R if num(r, c + "_kc") is not None]),
              "search_failed": [r["sample"] for r in R if num(r, c + "_krel") is None or num(r, c + "_ktrip") is None or r.get(c + "_krel") < 0 or r.get(c + "_ktrip") < 0],
              "missing": sum(1 for r in R if num(r, c + "_err_uV") is None)}
n = len(R)
ok = n > 0 and all(res[c]["within_0p25LSB"] >= n - 1 and res[c]["missing"] == 0 and not res[c]["search_failed"] for c in ("oc", "ng")) and \
     all(res[c]["delay_10pct_ns"] and res[c]["delay_10pct_ns"]["max"] < 300 for c in ("oc", "ng"))
summ = {"result": res, "samples": n,
        "criterion": "with the in-sample calibration codes applied: shunt-referred threshold-centre error within 0.25 LSB (595 uV shunt) in >= n-1 of n samples for OC (thr %d) and NEG (thr %d); search toggles found in every sample; trip delay at 10 %% overdrive < 300 ns" % (cfg["THR_OC"], cfg["THR_NEG"]),
        "disposition": "%s: %d samples; OC within 0.25 LSB %d, worst %.3f LSB, sigma %.3f LSB; NEG within 0.25 LSB %d, worst %.3f LSB, sigma %.3f LSB; delay OC %.0f-%.0f ns, NEG %.0f-%.0f ns" % (
            "passed" if ok else "failed", n, res["oc"]["within_0p25LSB"], max(abs(res["oc"]["centre_err_LSB"]["min"]), abs(res["oc"]["centre_err_LSB"]["max"])) if res["oc"]["centre_err_LSB"] else -1,
            res["oc"]["centre_err_LSB"]["sigma"] if res["oc"]["centre_err_LSB"] else -1,
            res["ng"]["within_0p25LSB"], max(abs(res["ng"]["centre_err_LSB"]["min"]), abs(res["ng"]["centre_err_LSB"]["max"])) if res["ng"]["centre_err_LSB"] else -1,
            res["ng"]["centre_err_LSB"]["sigma"] if res["ng"]["centre_err_LSB"] else -1,
            res["oc"]["delay_10pct_ns"]["min"] if res["oc"]["delay_10pct_ns"] else -1, res["oc"]["delay_10pct_ns"]["max"] if res["oc"]["delay_10pct_ns"] else -1,
            res["ng"]["delay_10pct_ns"]["min"] if res["ng"]["delay_10pct_ns"] else -1, res["ng"]["delay_10pct_ns"]["max"] if res["ng"]["delay_10pct_ns"] else -1),
        "per_sample": sorted(R, key=lambda r: r["sample"])}
json.dump(summ, open(os.path.join(tdir, "summary.json"), "w"), indent=1)
print(summ["disposition"])
