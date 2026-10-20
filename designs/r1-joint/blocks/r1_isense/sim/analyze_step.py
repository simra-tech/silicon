#!/usr/bin/env python3
"""Analyse tb_isense_step wrdata: offset after AZ, settling of each edge to 0.5 % of the step, currents."""
import sys, os, json, glob
rdir, tdir = sys.argv[1], sys.argv[2]
EDGES = [(4e-6, 7e-6), (7e-6, 9e-6), (9e-6, 10e-6), (10e-6, 13e-6), (13e-6, 16e-6)]
G, VPED = 14.0, 1.05/26
out = {}
for f in sorted(glob.glob(os.path.join(rdir, "*_step.txt"))):
    c = os.path.basename(f).replace("_step.txt", "")
    rows = []
    with open(f) as fh:
        hdr = fh.readline().split()
        for line in fh:
            p = line.split()
            if len(p) == len(hdr):
                rows.append([float(x) for x in p])
    ix = {h: i for i, h in enumerate(hdr)}
    t = [r[0] for r in rows]
    vod = [r[ix["v(outp)"]] - r[ix["v(outn)"]] for r in rows]
    vcm = [(r[ix["v(outp)"]] + r[ix["v(outn)"]]) / 2 for r in rows]
    def at(tt, v):
        for i in range(len(t)):
            if t[i] >= tt: return v[i]
        return v[-1]
    res = {}
    v0 = at(3.95e-6, vod)
    res["vod_at_0mV_V"] = v0
    res["offset_in_uV_vs_ideal_pedestal"] = (v0 / G + VPED) * 1e6
    res["vcm_out_V"] = at(3.95e-6, vcm)
    res["outp_outn_range_V"] = [min(r[ix["v(outp)"]] for r in rows if r[0] > 2.5e-6),
                                max(r[ix["v(outp)"]] for r in rows if r[0] > 2.5e-6)]
    vfull = at(6.95e-6, vod)
    res["vod_at_100mV_V"] = vfull
    res["gain_0_100"] = (vfull - v0) / 0.1
    # recovery after AZ release: time from 2.05 us to within 0.5 % of 1.68 V... of the final 0 mV value
    band = 0.005 * abs(vfull - v0)
    last = None
    for i in range(len(t)):
        if 2.05e-6 <= t[i] <= 3.95e-6 and abs(vod[i] - v0) > band: last = t[i]
    res["az_release_recovery_ns"] = None if last is None else (last - 2.05e-6) * 1e9
    st = []
    for (t1, t2) in EDGES:
        vi = at(t1 - 5e-9, vod); vf = at(t2 - 5e-9, vod)
        band = 0.005 * abs(vf - vi)
        last = t1
        for i in range(len(t)):
            if t1 <= t[i] <= t2 - 5e-9 and abs(vod[i] - vf) > band: last = t[i]
        sgn = 1 if vf > vi else -1
        ov = max(sgn * (vod[i] - vf) for i in range(len(t)) if t1 <= t[i] <= t2 - 5e-9)
        st.append({"t_edge_us": t1 * 1e6, "vod_from": vi, "vod_to": vf, "settle_0p5pct_ns": (last - t1) * 1e9,
                   "overshoot_pct": 100 * max(ov, 0) / abs(vf - vi)})
    res["edges"] = st
    rec = {}
    for name, t1, t2 in (("from_-200mV", 18.3e-6, 20e-6), ("from_+200mV", 20.3e-6, 23e-6)):
        vf = at(t2 - 5e-9, vod)
        band = 0.005 * abs(vfull - v0)   # 0.5 % of the 100 mV step
        last = t1
        for i in range(len(t)):
            if t1 <= t[i] <= t2 - 5e-9 and abs(vod[i] - vf) > band: last = t[i]
        rec[name] = (last - t1) * 1e9
    res["overload_recovery_ns"] = rec
    cmr = 0
    for (a, b) in ((3.0e-6, 3.95e-6), (5.5e-6, 6.95e-6), (11.5e-6, 12.95e-6), (14.5e-6, 15.95e-6), (21.5e-6, 22.95e-6)):
        seg = [vcm[i] for i in range(len(t)) if a <= t[i] <= b]
        cmr = max(cmr, max(seg) - min(seg))
    res["cm_ripple_pp_mV"] = cmr * 1e3
    res["max_output_node_V"] = max(max(r[ix["v(outp)"]], r[ix["v(outn)"]]) for r in rows)
    res["min_output_node_V"] = min(min(r[ix["v(outp)"]], r[ix["v(outn)"]]) for r in rows)
    res["settle_worst_ns"] = max(s["settle_0p5pct_ns"] for s in st if abs(s["vod_to"] - s["vod_from"]) > 1.0)
    res["settle_small_edge_ns"] = max(s["settle_0p5pct_ns"] for s in st if abs(s["vod_to"] - s["vod_from"]) <= 1.0)
    res["idda_uA"] = -at(3.95e-6, [r[ix["i(vdda)"]] for r in rows]) * 1e6
    res["idd_uA"] = -at(3.95e-6, [r[ix["i(vdd)"]] for r in rows]) * 1e6
    res["h1_h2_V"] = [at(3.95e-6, [r[ix["v(xdut.h1)"]] for r in rows]), at(3.95e-6, [r[ix["v(xdut.h2)"]] for r in rows])]
    out[c] = res
summ = {"result": {c: {"settle_100mV_edges_worst_ns": round(r["settle_worst_ns"], 1),
                      "settle_20mV_edge_ns": round(r["settle_small_edge_ns"], 1),
                      "overshoot_max_pct": round(max(e["overshoot_pct"] for e in r["edges"]), 2),
                      "overload_recovery_ns": {k: round(v, 1) for k, v in r["overload_recovery_ns"].items()},
                      "az_release_recovery_ns": round(r["az_release_recovery_ns"] or 0, 1),
                      "output_node_range_V": [round(r["min_output_node_V"], 4), round(r["max_output_node_V"], 4)],
                      "vcm_out_V": round(r["vcm_out_V"], 4), "cm_ripple_pp_mV": round(r["cm_ripple_pp_mV"], 3),
                      "idda_uA": round(r["idda_uA"], 1), "idd_uA": round(r["idd_uA"], 1)} for c, r in out.items()},
        "criterion": "settling of the 100 mV and 120 mV PWM edges into +-0.5 % of the step < 300 ns; 2 pF load per output",
        "disposition": "settling limit 300 ns: " + ", ".join("%s %s" % (c, "passed" if r["settle_worst_ns"] < 300 else "failed") for c, r in out.items()),
        "detail": out}
json.dump(summ, open(os.path.join(tdir, "summary.json"), "w"), indent=1)
print(json.dumps(summ, indent=1))
