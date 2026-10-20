#!/usr/bin/env python3
"""Collect tb_safe_dcmc: per sample and threshold, trip (up) and release (dn) points -> centre error, hysteresis."""
import sys, os, re, json, glob, statistics as st
rdir, tdir = sys.argv[1], sys.argv[2]
LSB = 2 * 1.05 / 63 * 1e3
pts = []
for f in sorted(glob.glob(os.path.join(rdir, "*.log"))):
    up = dn = None
    for line in open(f, errors="replace"):
        m = re.match(r"(up|dn)\s+=\s+(\S+)", line)
        if m:
            v = float(m.group(2))
            if m.group(1) == "up": up = v
            else: dn = v
            continue
        if "failed" in line and "meas dc up" in line: up = None
        if "failed" in line and "meas dc dn" in line: dn = None
        m = re.match(r"DCMC seed=(\S+) k=\s*(\S+)\s+th=\s*(\S+)", line)
        if m:
            th = float(m.group(3))
            d = {"seed": m.group(1), "k": int(float(m.group(2))), "th_V": th}
            if up is not None and dn is not None:
                d.update({"centre_err_mV": ((up + dn) / 2 - th) * 1e3, "hyst_mV": (up - dn) * 1e3, "trip_err_mV": (up - th) * 1e3})
            pts.append(d); up = dn = None
def s(v): return {"n": len(v), "mean": st.mean(v), "sigma": st.pstdev(v), "min": min(v), "max": max(v)} if v else None
res = {}
for th in sorted(set(p["th_V"] for p in pts)):
    q = [p for p in pts if p["th_V"] == th]
    c = [p["centre_err_mV"] for p in q if "centre_err_mV" in p]
    res["%+.4f" % th] = {"samples": len(q), "missing": len(q) - len(c), "centre_err_mV": s(c),
                          "hyst_mV": s([p["hyst_mV"] for p in q if "hyst_mV" in p]),
                          "max_abs_centre_LSB": max(abs(x) for x in c) / LSB if c else None}
allc = [p["centre_err_mV"] for p in pts if "centre_err_mV" in p]
miss = sum(1 for p in pts if "centre_err_mV" not in p)
ok = allc and miss == 0 and max(abs(x) for x in allc) <= LSB / 2
summ = {"result": res, "criterion": "comparator threshold (hysteresis centre) within +-0.5 LSB (16.7 mV Vod) of the ideal threshold for every sample and threshold; no missing points",
        "disposition": "%s: max |centre error| %.1f mV (%.2f LSB), sigma %.1f mV, %d points, %d missing (no crossing within +-150 mV)" % (
            "passed" if ok else "failed", max(abs(x) for x in allc) if allc else 0, (max(abs(x) for x in allc) / LSB) if allc else 0,
            st.pstdev(allc) if allc else 0, len(pts), miss),
        "points": pts}
json.dump(summ, open(os.path.join(tdir, "summary.json"), "w"), indent=1)
print(json.dumps(res, indent=1)); print(summ["disposition"])
