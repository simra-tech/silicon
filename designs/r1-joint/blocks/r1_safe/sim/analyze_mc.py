#!/usr/bin/env python3
"""Collect tb_safe_mc lines: trip-point errors (Vod mV) of 4 comparators per sample; shunt-referred = /14."""
import sys, os, json, glob, statistics as st
rdir, tdir = sys.argv[1], sys.argv[2]
G, LSB = 14.0, 2 * 1.05 / 63 * 1e3
keys = ("oca_mV", "negb_mV", "hyst_oca_mV", "hyst_negb_mV", "ctr_oca_mV", "ctr_negb_mV")
rows = []
for f in sorted(glob.glob(os.path.join(rdir, "*.log"))):
    for line in open(f, errors="replace"):
        if line.startswith("MC "):
            p = line.replace("=", " = ").split(); d = {}
            for k in keys:
                try: d[k] = float(p[p.index(k) + 2])
                except (ValueError, IndexError): d[k] = None
            rows.append(d)
errs = [r[k] for r in rows for k in keys[:2] if r[k] is not None]
cerr = [r[k] for r in rows for k in keys[4:] if r[k] is not None]
missing = sum(1 for r in rows for k in keys[4:] if r[k] is None)
def s(v): return {"n": len(v), "mean": st.mean(v), "sigma": st.pstdev(v), "min": min(v), "max": max(v)} if v else None
res = {"samples": len(rows), "comparator_points": len(errs), "missing": missing,
       "trip_err_mV_vod": s(errs), "trip_err_uV_shunt": s([e / G * 1e3 for e in errs]),
       "max_abs_trip_LSB": max(abs(e) for e in errs) / LSB if errs else None,
       "max_abs_centre_LSB": max(abs(e) for e in cerr) / LSB if cerr else None,
       "hyst_mV_vod": s([r[k] for r in rows for k in keys[2:4] if r[k] is not None]),
       "hyst_centre_offset_mV_vod": s([r[k] for r in rows for k in keys[4:] if r[k] is not None])}
summ = {"result": res, "criterion": "every comparator threshold (hysteresis centre) within +-0.5 LSB (16.7 mV Vod, 1.19 mV shunt) of the ideal threshold; trip-point error reported",
        "disposition": "%s: max |centre error| = %.3f LSB, max |trip error| = %.3f LSB over %d comparator points, %d missing" % (
            "passed" if cerr and res["max_abs_centre_LSB"] <= 0.5 and missing == 0 else "failed", res["max_abs_centre_LSB"] or 0, res["max_abs_trip_LSB"] or 0, len(cerr), missing),
        "rows": rows}
json.dump(summ, open(os.path.join(tdir, "summary.json"), "w"), indent=1)
print(json.dumps(res, indent=1)); print(summ["disposition"])
