#!/usr/bin/env python3
"""Analyse tb_isense_stbcm: output common-mode response to a 20 mV step of the VCM reference (the CMFB reference) at 3.5 us.
Overshoot of the output common mode relative to its own step (cross-check of the CM/CMFB loop-gain phase margin).
Revision 2 (2026-10-21): criterion "no ringing": at most one overshoot beyond the +-2 % band around the final value
(excursions counted on either side after the first entry into the band) and settled to +-2 % of the CM step within 300 ns.
Usage: analyze_stbcm.py RAW_DIR TREE_DIR"""
import sys, os, json, glob, math
rdir, tdir = sys.argv[1], sys.argv[2]
out = {}
for f in sorted(glob.glob(os.path.join(rdir, "*_cmstep.txt"))):
    c = os.path.basename(f).replace("_cmstep.txt", "")
    rows = []
    with open(f) as fh:
        hdr = fh.readline().split()
        for line in fh:
            p = line.split()
            if len(p) == len(hdr): rows.append([float(x) for x in p])
    ix = {h: i for i, h in enumerate(hdr)}
    t = [r[0] for r in rows]; cm = [(r[ix["v(outa_p)"]] + r[ix["v(outa_n)"]]) / 2 for r in rows]
    vod = [r[ix["v(outa_p)"]] - r[ix["v(outa_n)"]] for r in rows]
    m = lambda a, b, v: sum(x for ti, x in zip(t, v) if a <= ti < b) / max(1, sum(1 for ti in t if a <= ti < b))
    v0, vf = m(3.3e-6, 3.49e-6, cm), m(4.4e-6, 4.6e-6, cm); st = vf - v0
    sg = 1 if st > 0 else -1
    pk = max(sg * (x - vf) for ti, x in zip(t, cm) if ti >= 3.5e-6)
    # settle to 2 % of the CM step
    last = 3.5e-6
    for ti, x in zip(t, cm):
        if ti >= 3.5e-6 and abs(x - vf) > 0.02 * abs(st): last = ti
    # excursions outside the 2 % band after the first entry into it (each exit counts once)
    band = 0.02 * abs(st); inside = False; n_exc = 0; out_now = False
    for ti, x in zip(t, cm):
        if ti < 3.5e-6: continue
        e = abs(x - vf) > band
        if not inside:
            if not e: inside = True
            continue
        if e and not out_now: n_exc += 1
        out_now = e
    n_over = n_exc if n_exc > 0 else (1 if pk > band else 0)
    zeta = None
    ov = max(pk, 0) / abs(st)
    if 0 < ov < 1: zeta = -math.log(ov) / math.sqrt(math.pi ** 2 + math.log(ov) ** 2)
    out[c] = {"cm_before_V": v0, "cm_after_V": vf, "cm_step_V": st, "overshoot_pct_of_cm_step": 100 * ov, "settle_2pct_ns": (last - 3.5e-6) * 1e9,
              "zeta_from_overshoot": zeta, "pm_equiv_deg_2nd_order": None if zeta is None else math.degrees(math.atan(2 * zeta / math.sqrt(math.sqrt(1 + 4 * zeta ** 4) - 2 * zeta ** 2))),
              "vod_change_mV": (m(4.4e-6, 4.6e-6, vod) - m(3.3e-6, 3.49e-6, vod)) * 1e3,
              "excursions_after_band_entry": n_exc, "overshoots_beyond_2pct": n_over}
    out[c]["status"] = "passed" if (n_over <= 1 and out[c]["settle_2pct_ns"] <= 300.0) else "failed"
disp = ("failed" if any(v["status"] == "failed" for v in out.values()) else "passed") + \
    " (at most one overshoot beyond 2 %, settled to 2 % within 300 ns): " + ", ".join(
    "%s %.1f %% / %d / %.0f ns" % (k, v["overshoot_pct_of_cm_step"], v["overshoots_beyond_2pct"], v["settle_2pct_ns"]) for k, v in out.items())
json.dump({"result": out, "criterion": "at most one overshoot beyond the 2 % band and settled to 2 % of the CM step within 300 ns (revision 2; revision 1 was informational)", "disposition": disp}, open(os.path.join(tdir, "summary.json"), "w"), indent=1)
print(json.dumps(out, indent=1)); print(disp)
