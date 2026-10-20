#!/usr/bin/env python3
"""Analyse tb_safe_joint3: shunt-referred threshold centres through the real r1_isense output, simultaneous vs
staggered switching, delays at 10 % overdrive, string-tap disturbance."""
import sys, os, json, glob
rdir, tdir = sys.argv[1], sys.argv[2]
import re
DECK = os.environ.get("R1_DECK", "tb_safe_joint3")
cfg = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), DECK + ".json")))
TH = cfg["vsh_th_V"]; LSBSH = 2 * cfg["VREF"] / 63 / cfg["G"]
def load(f):
    with open(f) as fh:
        hdr = fh.readline().split()
        rows = [[float(x) for x in l.split()] for l in fh if len(l.split()) == len(hdr)]
    return {h: i for i, h in enumerate(hdr)}, rows
def cross(rows, col, lvl, rising, t0, t1, valcol=None):
    for i in range(1, len(rows)):
        a, b = rows[i - 1], rows[i]
        if t0 <= b[0] <= t1 and ((rising and a[col] < lvl <= b[col]) or (not rising and a[col] > lvl >= b[col])):
            f = (lvl - a[col]) / (b[col] - a[col]); t = a[0] + f * (b[0] - a[0])
            return t if valcol is None else (t, a[valcol] + f * (b[valcol] - a[valcol]))
    return None
out = {}
for f in sorted(glob.glob(os.path.join(rdir, "*_joint.txt"))):
    corner = os.path.basename(f)[:-len("_joint.txt")]
    ix, rows = load(f)
    lvl = 0.5 * max(r[ix["v(oc_a)"]] for r in rows if r[0] > 2.5e-6)
    res = {}
    for seg, (ta, tb) in (("simultaneous", ((3e-6, 8e-6, 13e-6), (3e-6, 8e-6, 13e-6))), ("staggered", ((14e-6, 19e-6, 24e-6), (16.5e-6, 21.5e-6, 26.5e-6)))):
        for ch, (t0, t1, t2) in (("a", ta), ("b", tb)):
            vin = ix["v(is%s_p)" % ch]
            oc_t = cross(rows, ix["v(oc_%s)" % ch], lvl, True, t0, t1, vin); oc_r = cross(rows, ix["v(oc_%s)" % ch], lvl, False, t1, t2, vin)
            ng_r = cross(rows, ix["v(neg_%s)" % ch], lvl, False, t0, t1, vin); ng_t = cross(rows, ix["v(neg_%s)" % ch], lvl, True, t1, t2, vin)
            for name, a, b in (("oc", oc_t, oc_r), ("neg", ng_t, ng_r)):
                k = "%s_%s_%s" % (seg, name, ch)
                if a and b:
                    c = (a[1] + b[1]) / 2
                    res[k] = {"centre_err_uV_shunt": (c - TH) * 1e6, "centre_err_LSB": (c - TH) / LSBSH, "hyst_uV_shunt": abs(a[1] - b[1]) * 1e6}
                else:
                    res[k] = None
    dsim = [abs(res["simultaneous_%s" % k]["centre_err_uV_shunt"] - res["staggered_%s" % k]["centre_err_uV_shunt"]) for k in ("oc_a", "neg_a", "oc_b", "neg_b") if res.get("simultaneous_%s" % k) and res.get("staggered_%s" % k)]
    res["max_sim_minus_stag_uV_shunt"] = max(dsim) if dsim else None
    res["max_sim_minus_stag_LSB"] = max(dsim) / LSBSH / 1e6 if dsim else None
    dl = {}
    for ch in "ab":
        for name, col, rising, te in (("oc_trip", "oc", True, 27.001e-6), ("neg_release", "neg", False, 27.001e-6), ("oc_release", "oc", False, 29.001e-6), ("neg_trip", "neg", True, 29.001e-6)):
            t = cross(rows, ix["v(%s_%s)" % (col, ch)], lvl, rising, te, te + 1.9e-6)
            dl["%s_%s_ns" % (name, ch)] = None if t is None else (t - te) * 1e9
    res["delays_from_shunt_step"] = dl
    # cross-channel kickback: channel b static near its threshold while channel a steps (31-37 us); b transitions = glitches
    # (33.9-34.7 us excluded: channel b itself moves from below to above its threshold there, an expected transition)
    if rows[-1][0] > 36.9e-6:
        gl = {}
        for o in ("oc_b", "neg_b"):
            col = ix["v(%s)" % o]; ev = []
            for i in range(1, len(rows)):
                if 31.2e-6 <= rows[i][0] <= 37e-6 and not (33.9e-6 <= rows[i][0] <= 34.7e-6):
                    a, b = rows[i - 1][col], rows[i][col]
                    if (a - lvl) * (b - lvl) < 0: ev.append(round(rows[i][0] * 1e6, 4))
            gl[o] = ev
        res["cross_channel_transitions_us"] = gl
        res["cross_channel_glitches"] = sum(len(v) for v in gl.values())
        for tap in ("v(t176)", "v(t76)"):
            v = [r[ix[tap]] for r in rows if 30.5e-6 <= r[0] <= 31.4e-6]; med = sum(v) / len(v)
            res["tap_%s_max_dev_step_mV" % tap[2:-1]] = max(abs(r[ix[tap]] - med) for r in rows if 31.4e-6 <= r[0] <= 33.4e-6) * 1e3
    for tap in ("v(t176)", "v(t76)"):
        v = [r[ix[tap]] for r in rows if 3e-6 <= r[0] <= 13e-6]
        vs = sorted(v); med = vs[len(vs) // 2]
        res["tap_%s_max_dev_mV" % tap[2:-1]] = max(abs(x - med) for x in v) * 1e3
    cen = [abs(v["centre_err_LSB"]) for k, v in res.items() if isinstance(v, dict) and "centre_err_LSB" in v]
    res["max_abs_centre_err_LSB"] = max(cen) if cen else None
    res["n_points"] = len(cen)
    res["idda_uA_total"] = -sum(r[ix["i(vdda)"]] for r in rows if 2.6e-6 < r[0] < 2.9e-6) / max(1, sum(1 for r in rows if 2.6e-6 < r[0] < 2.9e-6)) * 1e6
    out[corner] = res
def ok(r):
    return (r["n_points"] == 8 and r.get("cross_channel_glitches", 0) == 0 and r["max_abs_centre_err_LSB"] <= 0.5 and r["max_sim_minus_stag_LSB"] is not None and r["max_sim_minus_stag_LSB"] <= 0.1
            and all(v is not None and v < 300 for k, v in r["delays_from_shunt_step"].items() if "trip" in k))
summ = {"result": out, "criteria": "all 8 crossings present (2 segments x 2 channels x OC/NEG); no transition of channel b outputs while channel a steps (cross-channel kickback, if the segment exists); uncalibrated threshold centre (shunt-referred) within +-0.5 LSB (1.19 mV shunt) of VREF*(1/26+(2c-63)/882); simultaneous minus staggered centre <= 0.1 LSB; trip delay (from the shunt step, through r1_isense) < 300 ns at 10 % overdrive",
        "disposition": "; ".join("%s: %s (max centre %.3f LSB, sim-stag %.4f LSB, cross-channel glitches %s, worst trip delay %.0f ns)" % (c, "passed" if ok(r) else "failed", r["max_abs_centre_err_LSB"] or -1, r["max_sim_minus_stag_LSB"] or -1, r.get("cross_channel_glitches", "not in deck"),
                                   max([v for k, v in r["delays_from_shunt_step"].items() if "trip" in k and v is not None] or [-1])) for c, r in sorted(out.items()))}
json.dump(summ, open(os.path.join(tdir, "summary.json"), "w"), indent=1)
print(json.dumps(summ, indent=1))
