#!/usr/bin/env python3
"""post_skew.py <ngspice.log> <copies file> <out.json> [tb.raw]: effective sampling instants and A-B skew (Python 3.6)."""
import json, re, sys
import numpy as np
T_EDGE = 200e-9
vals = {}
for line in open(sys.argv[1], errors="replace"):
    m = re.match(r"^\s*([hd])([ab])(\d+)\s*=\s*([-+0-9.eE]+)", line)
    if m:
        vals[(m.group(1), m.group(2), int(m.group(3)))] = float(m.group(4))
if not vals and len(sys.argv) > 4:
    # measures missing (control-section meas cannot take v(a,b)): read the held values from the raw file
    sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
    import rawread
    d, var = rawread.read(sys.argv[4])
    t = d["time"]
    n = sum(1 for v in var if v.startswith("v(tap"))
    for i in range(n):
        for sl in ("a", "b"):
            vd = d["v(t%sp%d)" % (sl, i)] - d["v(t%sn%d)" % (sl, i)]
            vals[("h", sl, i)] = float(np.interp(210e-9, t, vd))
            vals[("d", sl, i)] = float(np.interp(210.5e-9, t, vd))
copies = [tuple(float(x) for x in l.split()) for l in open(sys.argv[2]) if l.strip()]
rows = []
for i, (v0, s) in enumerate(copies):
    r = {"copy": i, "V0": v0, "S_V_per_ns": s * 1e-9}
    for sl in ("a", "b"):
        h = vals[("h", sl, i)]
        d = vals[("d", sl, i)]
        r["teff_%s_ps" % sl] = (h - v0) / s * 1e12
        r["droop_%s_uV_per_ns" % sl] = (d - h) / 0.5 * 1e6
    r["skew_ps"] = r["teff_a_ps"] - r["teff_b_ps"]
    rows.append(r)
sk = np.array([r["skew_ps"] for r in rows])
ta = np.array([r["teff_a_ps"] for r in rows])
out = {"label": "simulated", "t_edge_definition": "50 % of the ideal trk_enc fall (common to both slices)",
       "skew_ps": {"mean": float(sk.mean()), "sd": float(sk.std(ddof=1)) if len(sk) > 1 else 0.0,
                   "max_abs": float(np.abs(sk).max())},
       "teff_a_ps": {"min": float(ta.min()), "max": float(ta.max())},
       "rows": rows}
json.dump(out, open(sys.argv[3], "w"), indent=1)
print(json.dumps({k: v for k, v in out.items() if k != "rows"}, indent=1))
for r in rows:
    print("%5.2f %+.0e  teffA %8.1f ps  teffB %8.1f ps  skew %7.2f ps  droopA %8.1f uV/ns" % (r["V0"], r["S_V_per_ns"]*1e9, r["teff_a_ps"], r["teff_b_ps"], r["skew_ps"], r["droop_a_uV_per_ns"]))
