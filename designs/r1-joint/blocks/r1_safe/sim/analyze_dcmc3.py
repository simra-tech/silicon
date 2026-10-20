#!/usr/bin/env python3
"""Collect tb_safe_dcmc3: per sample (seed, k) and cell threshold, trip (up) and release (dn) points.
Writes summary.json with the per-sample table (input of cal_model.py) and raw statistics."""
import sys, os, re, json, glob, statistics as st
rdir, tdir = sys.argv[1], sys.argv[2]
LSB = 2 * 1.05 / 63 * 1e3
samples = {}
for f in sorted(glob.glob(os.path.join(rdir, "*.log"))):
    up = dn = None
    corner = os.path.basename(f)[len("tb_safe_dcmc3_"):-4]
    pre = "" if "_mm_" in corner else corner + ":"     # nominal-corner runs: one sample per corner
    for line in open(f, errors="replace"):
        m = re.match(r"(up|dn)\s+=\s+(\S+)", line)
        if m:
            if m.group(1) == "up": up = float(m.group(2))
            else: dn = float(m.group(2))
            continue
        if "failed" in line and "meas dc up" in line: up = None
        if "failed" in line and "meas dc dn" in line: dn = None
        m = re.match(r"DCMC seed=(\S+) k=\s*(\S+)\s+th=\s*(\S+)", line)
        if m:
            key = pre + "%s_%03d" % (m.group(1), int(float(m.group(2))))
            s = samples.setdefault(key, {"pts": []})
            s["pts"].append({"th_V": float(m.group(3)), "up_V": up, "dn_V": dn})
            up = dn = None
rows, rep, miss = [], [], 0
for key, s in sorted(samples.items()):
    p = s["pts"]
    if len(p) >= 2 and p[0]["up_V"] is not None and p[-1]["up_V"] is not None:
        rep.append(abs(p[0]["up_V"] - p[-1]["up_V"]) * 1e3 + abs(p[0]["dn_V"] - p[-1]["dn_V"]) * 1e3)
    pts = p[:-1] if len(p) > 1 and p[-1]["th_V"] == p[0]["th_V"] else p
    pts = sorted(pts, key=lambda q: q["th_V"])
    miss += sum(1 for q in pts if q["up_V"] is None or q["dn_V"] is None)
    rows.append({"sample": key, "pts": pts})
def s(v): return {"n": len(v), "mean": st.mean(v), "sigma": st.pstdev(v), "min": min(v), "max": max(v)} if v else None
ths = sorted(set(q["th_V"] for r in rows for q in r["pts"]))
res = {}
for th in ths:
    c = [((q["up_V"] + q["dn_V"]) / 2 - th) * 1e3 for r in rows for q in r["pts"] if q["th_V"] == th and q["up_V"] is not None and q["dn_V"] is not None]
    h = [(q["up_V"] - q["dn_V"]) * 1e3 for r in rows for q in r["pts"] if q["th_V"] == th and q["up_V"] is not None and q["dn_V"] is not None]
    res["%+.4f" % th] = {"centre_err_mV": s(c), "hyst_mV": s(h), "max_abs_centre_LSB": max(abs(x) for x in c) / LSB if c else None}
allc = [((q["up_V"] + q["dn_V"]) / 2 - q["th_V"]) * 1e3 for r in rows for q in r["pts"] if q["up_V"] is not None and q["dn_V"] is not None]
summ = {"result": {"per_threshold": res, "samples": len(rows), "missing_points": miss,
                   "raw_centre_sigma_mV": st.pstdev(allc) if allc else None, "raw_centre_max_abs_mV": max(abs(x) for x in allc) if allc else None,
                   "repeat_check_max_mV": max(rep) if rep else None},
        "criterion": "raw data for cal_model.py (no pass/fail here); repeat check: first threshold repeated at the end of each sample must agree (same draw)",
        "disposition": "raw (uncalibrated): sigma %.1f mV, max |centre error| %.1f mV (%.2f LSB), %d samples, %d missing points; repeat check max %.3f mV" % (
            st.pstdev(allc), max(abs(x) for x in allc), max(abs(x) for x in allc) / LSB, len(rows), miss, max(rep) if rep else -1),
        "samples": rows}
json.dump(summ, open(os.path.join(tdir, "summary.json"), "w"), indent=1)
print(summ["disposition"])
