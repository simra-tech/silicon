#!/usr/bin/env python3
"""Analyse tb_isense_dc: least-squares gain and pedestal, offset vs the ideal network, INL, pedestal-off offset."""
import sys, os, json, glob
rdir, tdir = sys.argv[1], sys.argv[2]
cfg = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "dc_points.json")))
VPED_IDEAL = 1.05 / 26.0
G_IDEAL = 14.0
def load(f):
    rows = []
    with open(f) as fh:
        hdr = fh.readline().split()
        for line in fh:
            p = line.split()
            if len(p) == len(hdr): rows.append([float(x) for x in p])
    return hdr, rows
def at(rows, tt, col):
    for r in rows:
        if r[0] >= tt: return r[col]
    return rows[-1][col]
out = {}
for f in sorted(glob.glob(os.path.join(rdir, "*_dc_ped.txt"))):
    c = os.path.basename(f).replace("_dc_ped.txt", "")
    hdr, rows = load(f)
    xs, ys = [], []
    for k, v in enumerate(cfg["points_V"]):
        tr = cfg["t0_s"] + (k + 1) * cfg["dt_s"] - 50e-9
        xs.append(at(rows, tr, 3) - at(rows, tr, 4))
        ys.append(at(rows, tr, 1) - at(rows, tr, 2))
    n = len(xs); mx = sum(xs) / n; my = sum(ys) / n
    a = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    b = my - a * mx
    ped = -b / a
    inl = [y - (a * x + b) for x, y in zip(xs, ys)]
    fs = a * (max(xs) - min(xs))
    hdr2, rows2 = load(f.replace("_dc_ped.txt", "_dc_nop.txt"))
    vod_nop = at(rows2, 4.4e-6, 1) - at(rows2, 4.4e-6, 2)
    vcm_nop = (at(rows2, 4.4e-6, 1) + at(rows2, 4.4e-6, 2)) / 2
    out[c] = {"gain": a, "gain_error_pct": 100 * (a / G_IDEAL - 1), "pedestal_mV": ped * 1e3,
              "pedestal_error_uV": (ped - VPED_IDEAL) * 1e6,
              "offset_pedestal_off_uV": vod_nop / a * 1e6, "vcm_out_V": vcm_nop,
              "inl_max_pct_fs": 100 * max(abs(e) for e in inl) / fs, "inl_V": inl,
              "vod_V": ys, "vin_V": xs, "vod_range_V": [min(ys), max(ys)]}
res = {c: {k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items() if k not in ("inl_V", "vod_V", "vin_V")} for c, r in out.items()}
summ = {"result": res,
        "criteria": "gain 14 (report); |offset, pedestal off| <= 100 uV after AZ; INL report (% of the -20..100 mV output span)",
        "disposition": "offset <= 100 uV: " + ", ".join("%s %s" % (c, "passed" if abs(r["offset_pedestal_off_uV"]) <= 100 else "failed") for c, r in sorted(out.items())),
        "detail": out}
json.dump(summ, open(os.path.join(tdir, "summary.json"), "w"), indent=1)
print(json.dumps(res, indent=1))
