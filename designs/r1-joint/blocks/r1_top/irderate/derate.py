# SPDX-License-Identifier: Apache-2.0
"""r1_top try g, ctrl IR-drop derate (track T11b), step 3: derate factors, STA cases, feed-resistance target.

  python3 derate.py factors <out json> <nominal V: 1.08 slow | 1.32 fast> <char json> [<char json> ...]
  python3 derate.py target  <out json> <factors json> <sweep summary json> <slack target ns>

factors: F(V) = delay(V) / delay(nominal V) per cell and load (mean of rise and fall); the derate of record is the
largest ratio over the cells and loads (conservative), the mean ratio is reported too. F at the internal voltages of
try g (spec VDD minimum 1.08 V minus the supply loss at the ctrl, reports/supply_g.md) by linear interpolation:
  worst grid point: typ 22.8 + 46.1 = 68.9 mV, max sheet 30.6 + 63.6 = 94.2 mV
  best grid point:  typ 18.0 + 31.7 = 49.7 mV, max sheet 25.1 + 46.8 = 71.9 mV
target: the uniform-derate sweep gives setup slack (flop D) against F (linear fit); F at the slack target, the
voltage V* with F(V*) = F_target, the allowed loss 1.08 V - V*, and the combined VDD + VSS feed resistance at the ctrl
worst point that keeps it (ctrl current 40.25 mA, as supply_g.md).
"""
import json
import sys

import numpy as np

VMIN = 1.08
LOSS = {"typ_worst": 0.0689, "max_worst": 0.0942, "typ_best": 0.0497, "max_best": 0.0719}
I_CTRL = 40.25e-3


def curve(chars):
    D = {}
    for f in chars:
        c = json.load(open(f))
        for k, d in c["delay_ps"].items():
            for v, x in d.items():
                if x["mean"] is not None and x["mean"] > 0:
                    D.setdefault(k, {})[float(v)] = x["mean"]
    R = {}
    for k, d in D.items():
        if VMIN not in d:
            continue
        R[k] = {v: d[v] / d[VMIN] for v in sorted(d)}
    vs = sorted(set.intersection(*[set(r) for r in R.values()]))
    worst = {v: max(R[k][v] for k in R) for v in vs}
    mean = {v: float(np.mean([R[k][v] for k in R])) for v in vs}
    return D, R, vs, worst, mean


def interp(curve_, v):
    xs = sorted(curve_)
    return float(np.interp(v, xs, [curve_[x] for x in xs]))


if sys.argv[1] == "factors":
    out = sys.argv[2]
    VMIN = float(sys.argv[3])
    D, R, vs, worst, mean = curve(sys.argv[4:])
    res = {"method": __doc__.strip().splitlines()[0], "nominal_V": VMIN, "voltages": vs,
           "ratio_per_cell": {k: {"%.4f" % v: round(r[v], 4) for v in vs} for k, r in R.items()},
           "delay_ps_nominal": {k: round(D[k][VMIN], 2) for k in R},
           "F_worst": {"%.4f" % v: round(worst[v], 4) for v in vs}, "F_mean": {"%.4f" % v: round(mean[v], 4) for v in vs},
           "points": {}}
    for k, l in LOSS.items():
        v = VMIN - l
        res["points"][k] = {"V": round(v, 4), "F_worst": round(interp(worst, v), 4), "F_mean": round(interp(mean, v), 4)}
    json.dump(res, open(out, "w"), indent=1)
    print(json.dumps(res["points"], indent=1))
    for k in R:
        print(k, " ".join("%.3f:%.4f" % (v, R[k][v]) for v in vs))
else:
    out, ff, sw, tgt = sys.argv[2], sys.argv[3], sys.argv[4], float(sys.argv[5])
    F = json.load(open(ff))
    S = json.load(open(sw))
    pts = sorted((v["late"], v["setup_ff"]) for v in S.values() if v["early"] == v["late"])
    x = np.array([p[0] for p in pts]); y = np.array([p[1] for p in pts])
    a, b = np.polyfit(x, y, 1)            # slack = a F + b
    resid = float(np.max(np.abs(y - (a * x + b))))
    Ft = (tgt - b) / a
    F0 = -b / a
    worst = {float(v): r for v, r in F["F_worst"].items()}
    mean = {float(v): r for v, r in F["F_mean"].items()}

    def inv(c, f):
        xs = sorted(c)                     # F decreases with V
        return float(np.interp(f, [c[v] for v in xs][::-1], xs[::-1]))
    res = {"method": __doc__.strip().splitlines()[0], "fit": {"slope_ns_per_unit_F": round(a, 4),
                                                                "intercept_ns": round(b, 4), "max_residual_ns": round(resid, 5)},
           "slack_target_ns": tgt, "F_at_target": round(Ft, 4), "F_at_zero_slack": round(F0, 4)}
    for nm, c in (("worst_cell", worst), ("mean_cell", mean)):
        vt, v0 = inv(c, Ft), inv(c, F0)
        res[nm] = {"V_at_target": round(vt, 4), "allowed_loss_mV": round((VMIN - vt) * 1e3, 1),
                   "R_feed_total_max_ohm": round((VMIN - vt) / I_CTRL, 3),
                   "V_at_zero_slack": round(v0, 4), "loss_at_zero_slack_mV": round((VMIN - v0) * 1e3, 1)}
    res["R_feed_total_now_ohm"] = {"typ": round(LOSS["typ_worst"] / I_CTRL, 3), "max": round(LOSS["max_worst"] / I_CTRL, 3)}
    json.dump(res, open(out, "w"), indent=1)
    print(json.dumps(res, indent=1))
