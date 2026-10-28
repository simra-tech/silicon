#!/usr/bin/env python3
"""T2m (layout B7): edge-relative timing of the gate-level SAR outputs in a closed-loop run (for the behavioural
proxy deck sim/post/b7/gen_b7_decks.py): per slice, the 50 % crossings after each clk rising edge E(n) inside the
conversions of mclk (fall / rise), the comparator clocks clkX / clkXb / clknX / clknXb (fall / rise), and each CDAC
line (rise, the tick after its decision). Medians and ranges in ns after the edge.
usage: gl_timing.py OUT.json <run id> [<run id> ...]   (raw b5.raw under <G1_RESULTS_ROOT>/r1_adc/<id>/)"""
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
BLOCK = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(BLOCK, "sim"))
from rawread import read  # noqa
root = os.environ["G1_RESULTS_ROOT"]
T = 1.0 / 30e6
ND = 14


def cross(t, y, th, t0, t1, rising):
    m = (t >= t0) & (t <= t1)
    tt, yy = t[m], y[m]
    ok = np.nonzero(yy >= th)[0] if rising else np.nonzero(yy <= th)[0]
    if not ok.size or ok[0] == 0:
        return None
    i = ok[0]
    return float(tt[i - 1] + (th - yy[i - 1]) * (tt[i] - tt[i - 1]) / (yy[i] - yy[i - 1]))


out = {}
for rid in sys.argv[2:]:
    d, _ = read(os.path.join(root, "r1_adc", rid, "b5.raw"))
    t = d["time"]
    vdd = float(np.max(d["v(clk)"]))
    nf = int((t[-1] - 18 * T - 15 * T) // (22 * T)) + 1
    acc = {}
    def add(k, v):
        if v is not None:
            acc.setdefault(k, []).append(v * 1e9)
    for f in range(nf):
        for k in range(ND):
            e = (18 + 22 * f + k) * T
            add("mclk_fall", (cross(t, d["v(sar_mclk)"], 0.5 * vdd, e - 0.1e-9, e + 4e-9, False) or e) - e if cross(t, d["v(sar_mclk)"], 0.5 * vdd, e - 0.1e-9, e + 4e-9, False) else None)
            tf = cross(t, d["v(sar_mclk)"], 0.5 * vdd, e - 0.1e-9, e + 4e-9, False)
            if tf:
                tr = cross(t, d["v(sar_mclk)"], 0.5 * vdd, tf, e + 8e-9, True)
                add("mclk_rise", tr - e if tr else None)
            for sl in "ab":
                for nm, kk in (("clk%s", range(1, ND)), ("clkn%s", (0,))):
                    if k not in kk:
                        continue
                    for suf, inv in (("", False), ("b", True)):
                        n = "v(sar_" + (nm % sl) + suf + ")"
                        a1 = cross(t, d[n], 0.5 * vdd, e - 0.1e-9, e + 4e-9, inv)       # leave evaluate (fall; complement rises)
                        if a1:
                            add("%s%s_off" % (nm % "X", suf), a1 - e)
                            a2 = cross(t, d[n], 0.5 * vdd, a1, e + 8e-9, not inv)
                            add("%s%s_on" % (nm % "X", suf), a2 - e if a2 else None)
                if k >= 1:
                    for pn in ("cp", "cn"):
                        n = "v(sar_%s%s%d)" % (pn, sl, 13 - k)
                        if np.interp(e - 0.1e-9, t, d[n]) < 0.5 * vdd <= np.interp(e + 6e-9, t, d[n]):
                            add("line_%s_%s%d" % (sl, pn, 13 - k), cross(t, d[n], 0.5 * vdd, e, e + 6e-9, True) - e)
                            add("line_all", cross(t, d[n], 0.5 * vdd, e, e + 6e-9, True) - e)
    out[rid] = {k: {"median": round(float(np.median(v)), 4), "min": round(float(np.min(v)), 4), "max": round(float(np.max(v)), 4), "n": len(v)}
                for k, v in sorted(acc.items())}
json.dump({"tool": "sim/post/b7/gl_timing.py", "label": "simulated (gate-level r1_adc_sar in the closed-loop decks); ns after the clk rising edge",
           "runs": out}, open(sys.argv[1], "w"), indent=1)
for rid, v in out.items():
    print(rid)
    for k, x in v.items():
        if not k.startswith("line_") or k == "line_all":
            print("  %-12s %s" % (k, x))
