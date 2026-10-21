#!/usr/bin/env python3
"""Analyse tb_isense_stbcm: output common-mode response to a 20 mV step of the VCM reference (the CMFB reference) at 3.5 us.
Overshoot of the output common mode relative to its own step (cross-check of the CM/CMFB loop-gain phase margin; informational).
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
    zeta = None
    ov = max(pk, 0) / abs(st)
    if 0 < ov < 1: zeta = -math.log(ov) / math.sqrt(math.pi ** 2 + math.log(ov) ** 2)
    out[c] = {"cm_before_V": v0, "cm_after_V": vf, "cm_step_V": st, "overshoot_pct_of_cm_step": 100 * ov, "settle_2pct_ns": (last - 3.5e-6) * 1e9,
              "zeta_from_overshoot": zeta, "pm_equiv_deg_2nd_order": None if zeta is None else math.degrees(math.atan(2 * zeta / math.sqrt(math.sqrt(1 + 4 * zeta ** 4) - 2 * zeta ** 2))),
              "vod_change_mV": (m(4.4e-6, 4.6e-6, vod) - m(3.3e-6, 3.49e-6, vod)) * 1e3}
disp = "informational: CM step response overshoot " + ", ".join("%s %.1f %%" % (k, v["overshoot_pct_of_cm_step"]) for k, v in out.items())
json.dump({"result": out, "criterion": "informational cross-check of the CM loop phase margin (no limit)", "disposition": disp}, open(os.path.join(tdir, "summary.json"), "w"), indent=1)
print(json.dumps(out, indent=1)); print(disp)
