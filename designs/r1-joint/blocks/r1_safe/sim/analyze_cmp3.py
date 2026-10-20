#!/usr/bin/env python3
"""Analyse tb_safe_cmp3 (revision 3, same outputs as tb_safe_cmp): trip/release points vs code for the 4 comparators, hysteresis, delays at 10 % overdrive."""
import sys, os, json, glob
rdir, tdir = sys.argv[1], sys.argv[2]
cfg = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "tb_safe_cmp3.json")))
VREF, G, TR = cfg["VREF"], cfg["G"], cfg["TR"]
vth = lambda c: (2 * c - 63) / 63.0 * VREF
def load(f):
    with open(f) as fh:
        hdr = fh.readline().split()
        rows = [[float(x) for x in l.split()] for l in fh if len(l.split()) == len(hdr)]
    return {h: i for i, h in enumerate(hdr)}, rows
def cross(rows, col, lvl, rising, t0, t1, valcol=None):
    for i in range(1, len(rows)):
        a, b = rows[i - 1], rows[i]
        if t0 <= b[0] <= t1:
            if (rising and a[col] < lvl <= b[col]) or (not rising and a[col] > lvl >= b[col]):
                f = (lvl - a[col]) / (b[col] - a[col])
                t = a[0] + f * (b[0] - a[0])
                if valcol is None: return t
                return t, a[valcol] + f * (b[valcol] - a[valcol])
    return None
out = {}
for corner_dir in sorted(set(os.path.basename(f).split("_thr_")[0] for f in glob.glob(os.path.join(rdir, "*_thr_c*.txt")))):
    vdd = None
    res = {"thresholds": []}
    for c in cfg["codes"]:
        f = os.path.join(rdir, "%s_thr_c%02d.txt" % (corner_dir, c))
        if not os.path.exists(f): continue
        ix, rows = load(f)
        vdd = max(r[ix["v(oc_a)"]] for r in rows) if vdd is None else vdd
        lvl = 0.5 * max(max(r[ix["v(oc_a)"]] for r in rows), 0.6)
        DLY = cfg.get("DLY", 0)
        ch = "a"; code = c; th = vth(c)
        d = {"code": c, "vth_ideal_V": th}
        oc_t = cross(rows, ix["v(oc_a)"], lvl, True, 0, TR, ix["v(voda)"])
        oc_r = cross(rows, ix["v(oc_a)"], lvl, False, TR, 2 * TR, ix["v(voda)"])
        ng_t = cross(rows, ix["v(neg_b)"], lvl, True, DLY + TR, DLY + 2 * TR, ix["v(vodb)"])
        ng_r = cross(rows, ix["v(neg_b)"], lvl, False, DLY, DLY + TR, ix["v(vodb)"])
        if oc_t and oc_r:
            d.update({"oc_trip_err_mV": (oc_t[1] - th) * 1e3, "oc_release_err_mV": (oc_r[1] - th) * 1e3, "oc_hyst_mV": (oc_t[1] - oc_r[1]) * 1e3,
                      "oc_centre_err_mV": ((oc_t[1] + oc_r[1]) / 2 - th) * 1e3})
        if ng_t and ng_r:
            d.update({"neg_trip_err_mV": (ng_t[1] - th) * 1e3, "neg_release_err_mV": (ng_r[1] - th) * 1e3, "neg_hyst_mV": (ng_r[1] - ng_t[1]) * 1e3,
                      "neg_centre_err_mV": ((ng_t[1] + ng_r[1]) / 2 - th) * 1e3})
        d["parked_ok"] = (max(r[ix["v(neg_a)"]] for r in rows) < lvl) and (max(r[ix["v(oc_b)"]] for r in rows) < lvl)
        res["thresholds"].append(d)
    errs = [abs(d[k]) for d in res["thresholds"] for k in ("oc_trip_err_mV", "neg_trip_err_mV") if k in d]
    cerrs = [abs(d[k]) for d in res["thresholds"] for k in ("oc_centre_err_mV", "neg_centre_err_mV") if k in d]
    res["max_abs_centre_err_mV_vod"] = max(cerrs) if cerrs else None
    res["max_abs_centre_err_LSB"] = max(cerrs) / (cfg["lsb_V"] * 1e3) if cerrs else None
    hyst = [d[k] for d in res["thresholds"] for k in ("oc_hyst_mV", "neg_hyst_mV") if k in d]
    res["n_points"] = len(errs)
    res["n_expected"] = 2 * len(cfg["codes"])
    res["parked_comparators_quiet"] = all(d.get("parked_ok") for d in res["thresholds"])
    res["max_abs_trip_err_mV_vod"] = max(errs) if errs else None
    res["max_abs_trip_err_uV_shunt"] = max(errs) / G * 1e3 if errs else None
    res["max_abs_trip_err_LSB"] = max(errs) / (cfg["lsb_V"] * 1e3) if errs else None
    res["hyst_mV_vod_range"] = [min(hyst), max(hyst)] if hyst else None
    # delays
    f = os.path.join(rdir, "%s_delay.txt" % corner_dir)
    if os.path.exists(f):
        ix, rows = load(f)
        hi = max(r[ix["v(oc_a)"]] for r in rows); lvl = hi / 2
        dl = {}
        for name, col, rising, te in (("oc_trip_10pct", "v(oc_a)", True, 2.0005e-6), ("oc_release_10pct", "v(oc_a)", False, 5.0005e-6),
                                      ("neg_trip_10pct", "v(neg_a)", True, 8.0005e-6), ("neg_release_10pct", "v(neg_a)", False, 11.0005e-6),
                                      ("oc_trip_1LSB", "v(oc_b)", True, 3.0005e-6), ("oc_release_1LSB", "v(oc_b)", False, 6.0005e-6),
                                      ("neg_trip_1LSB", "v(neg_b)", True, 12.0005e-6)):
            t = cross(rows, ix[col], lvl, rising, te, te + 1.9e-6)
            dl[name + "_ns"] = None if t is None else (t - te) * 1e9
        res["delays"] = dl
        res["idda_uA_total"] = -sum(r[ix["i(vdda)"]] for r in rows[:50]) / 50 * 1e6
        res["idd_uA_total"] = -sum(r[ix["i(vdd)"]] for r in rows[:50]) / 50 * 1e6
    out[corner_dir] = res
summ = {"result": {c: {k: v for k, v in r.items() if k != "thresholds"} for c, r in out.items()},
        "criteria": "threshold = hysteresis centre (mean of trip and release points); its error vs ideal (2c-63)/63*VREF within +-0.5 LSB (16.7 mV Vod) at all codes, all points present, parked comparators quiet; trip-point error (centre + hysteresis/2) reported; delay < 300 ns at 10 % overdrive (overdrive measured from the ideal threshold)",
        "disposition": "; ".join("%s: thr %s, delay %s" % (c,
            "passed" if r.get("max_abs_centre_err_LSB") is not None and r["max_abs_centre_err_LSB"] <= 0.5 and r["n_points"] == r["n_expected"] and r["parked_comparators_quiet"] else "failed",
            "passed" if r.get("delays") and all(v is not None and v < 300 for k, v in r["delays"].items() if "10pct" in k) else "failed")
            for c, r in sorted(out.items())),
        "detail": out}
json.dump(summ, open(os.path.join(tdir, "summary.json"), "w"), indent=1)
print(json.dumps(summ["result"], indent=1)); print(summ["disposition"])
