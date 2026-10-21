#!/usr/bin/env python3
"""Analyse tb_isense_stbstep: shunt step 0 -> 100 mV (edge 3.000-3.010 us) after the auto-zero, differential output.
Settling to 0.5 % of the output step, overshoot count (excursions beyond the final value by more than 0.05 % of the step,
counted as separate segments), peak overshoot. Criterion: settled within 300 ns of the edge start (limit of the earlier
isense step row; the task gave no time) and at most one overshoot.
Usage: analyze_stbstep.py RAW_DIR TREE_DIR"""
import sys, os, json, glob
rdir, tdir = sys.argv[1], sys.argv[2]
T0, T1 = 3.0e-6, 3.01e-6
out = {}
for f in sorted(glob.glob(os.path.join(rdir, "*_step.txt"))):
    c = os.path.basename(f).replace("_step.txt", "")
    rows = []
    with open(f) as fh:
        hdr = fh.readline().split()
        for line in fh:
            p = line.split()
            if len(p) == len(hdr): rows.append([float(x) for x in p])
    ix = {h: i for i, h in enumerate(hdr)}
    t = [r[0] for r in rows]; vod = [r[ix["v(outa_p)"]] - r[ix["v(outa_n)"]] for r in rows]
    at = lambda tt: next(v for ti, v in zip(t, vod) if ti >= tt)
    vi, vf = at(2.95e-6), at(6.95e-6); st = vf - vi; sg = 1 if st > 0 else -1
    last = T0
    for ti, v in zip(t, vod):
        if T0 <= ti <= 6.95e-6 and abs(v - vf) > 0.005 * abs(st): last = ti
    segs, inseg, peak, reached = 0, False, 0.0, False
    for ti, v in zip(t, vod):
        if ti < T0: continue
        e = sg * (v - vf)
        if e >= 0: reached = True
        if reached and e > 0.0005 * abs(st):
            if not inseg: segs += 1; inseg = True
            peak = max(peak, e)
        elif e < 0.0005 * abs(st) * 0.5: inseg = False
    trip = next((ti for ti, v in zip(t, [r[ix["v(oc_a)"]] for r in rows]) if ti >= T0 and v > 0.6 * (max(r[ix["v(oc_a)"]] for r in rows))), None)
    out[c] = {"vod_before_V": vi, "vod_after_V": vf, "step_V": st, "settle_0p5pct_from_edge_start_ns": (last - T0) * 1e9,
              "settle_0p5pct_from_edge_end_ns": max(0.0, (last - T1) * 1e9), "overshoot_count": segs,
              "peak_overshoot_pct_of_step": 100 * peak / abs(st), "oc_a_high_after_ns": None if trip is None else (trip - T0) * 1e9}
ok = out and all(v["settle_0p5pct_from_edge_start_ns"] <= 300 and v["overshoot_count"] <= 1 for v in out.values())
disp = "%s: step 0 -> 100 mV, 10 ns edge: settling to 0.5 %% %s ns from the edge start, overshoot count %s, peak overshoot %s %%" % (
    "passed" if ok else "failed", "/".join("%s %.0f" % (k, v["settle_0p5pct_from_edge_start_ns"]) for k, v in out.items()),
    "/".join("%s %d" % (k, v["overshoot_count"]) for k, v in out.items()), "/".join("%s %.3f" % (k, v["peak_overshoot_pct_of_step"]) for k, v in out.items()))
json.dump({"result": out, "criterion": "settling to 0.5 % of the step within 300 ns of the edge start and at most one overshoot", "disposition": disp}, open(os.path.join(tdir, "summary.json"), "w"), indent=1)
print(json.dumps(out, indent=1)); print(disp)
