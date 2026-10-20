#!/usr/bin/env python3
"""Collect tb_isense_droop: drift over one 50 us PWM period after AZ, from the wrdata files (full precision):
input-referred drift of the zero-current output (Vod/14), drift of each hold-cap node, and a mismatch bound:
worst case one hold cap droops and the other not, referred to the input through the aux/main gm ratio (1/12)."""
import sys, os, re, json, glob
rdir, tdir = sys.argv[1], sys.argv[2]
LIM = 50.0   # uV input-referred: residual after AZ is <= 48 uV worst (MC tt/ss/ff), so drift must stay well inside the 100 uV budget
GMR = 12.0
def avg(rows, col, t0, t1):
    v = [r[col] for r in rows if t0 <= r[0] <= t1]; return sum(v) / len(v)
res = {}
temps = {}
for f in glob.glob(os.path.join(rdir, "*.log")):
    for line in open(f, errors="replace"):
        m = re.match(r"DROOP corner=(\S+) temp=(\S+)", line)
        if m: temps[m.group(1)] = float(m.group(2))
for f in sorted(glob.glob(os.path.join(rdir, "*_droop.txt"))):
    c = os.path.basename(f)[:-len("_droop.txt")]
    with open(f) as fh:
        hdr = fh.readline().split(); ix = {h: i for i, h in enumerate(hdr)}
        rows = [[float(x) for x in l.split()] for l in fh if len(l.split()) == len(hdr)]
    vod = lambda t0, t1: avg(rows, ix["v(outp)"], t0, t1) - avg(rows, ix["v(outn)"], t0, t1)
    d_vod = (vod(51.9e-6, 52e-6) - vod(3.9e-6, 4e-6)) / 14 * 1e6
    d_h1 = (avg(rows, ix["v(xdut.h1)"], 51.9e-6, 52e-6) - avg(rows, ix["v(xdut.h1)"], 3.9e-6, 4e-6)) * 1e6
    d_h2 = (avg(rows, ix["v(xdut.h2)"], 51.9e-6, 52e-6) - avg(rows, ix["v(xdut.h2)"], 3.9e-6, 4e-6)) * 1e6
    res["%s_%gC" % (c, temps.get(c, float("nan")))] = {"drift_in_uV": d_vod, "h1_drift_uV": d_h1, "h2_drift_uV": d_h2,
        "mismatch_bound_in_uV": max(abs(d_h1), abs(d_h2)) / GMR}
ok = res and all(abs(v["drift_in_uV"]) <= LIM and v["mismatch_bound_in_uV"] <= LIM for v in res.values())
summ = {"result": res, "criterion": "over 50 us after AZ: |input-referred drift| <= %g uV and the mismatch bound (one hold cap droops, the other not, /12) <= %g uV" % (LIM, LIM),
        "disposition": "%s: worst |drift| %.3f uV, worst hold-node droop %.2f uV, mismatch bound %.3f uV input-referred, %d corners" % ("passed" if ok else "failed",
            max(abs(v["drift_in_uV"]) for v in res.values()), max(max(abs(v["h1_drift_uV"]), abs(v["h2_drift_uV"])) for v in res.values()),
            max(v["mismatch_bound_in_uV"] for v in res.values()), len(res))}
json.dump(summ, open(os.path.join(tdir, "summary.json"), "w"), indent=1)
rp = os.path.join(tdir, "run.json")
if os.path.exists(rp):
    r = json.load(open(rp)); r["result"] = res; r["disposition"] = summ["disposition"]; json.dump(r, open(rp, "w"), indent=1, sort_keys=True)
print(json.dumps(summ, indent=1))
