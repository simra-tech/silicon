#!/usr/bin/env python3
"""T2o (D28, 2026-10-28): copy of sim/post/b7/r24_d23.py for the revision-6 strobe (comparator clock rises after the
falling clk edge, about 17-19 ns after E(k)); changes: the strobe search window ends at E(k) + 26 ns (was 8 ns), the
regeneration search ends at E(k) + T + 2 ns (was E(k) + T), and the settling sweep includes 15-19 ns. The metric is unchanged.

T2m (layout B7, 2026-10-27): R2-4 re-defined per PLAN.md D23 on closed-loop runs (gate-level r1_adc_sar, or the
behavioural SAR with the gate-level switch and strobe timing, sim/post/b7/gen_b7_decks.py).

D23 (1): R2-4 is the comparator-input error at the instant the comparator is strobed; the deck measures from the real
CDAC switch to the real strobe. Timing facts used here (recorded in README "Layout B7"):
  * r1_ctrl 0.8 issues every ADC command on the rising clk edge (r1_gate: adc_start, adc_hold, is_smp, adc_sel,
    cur_trk are posedge-clk registers; one decision per 33.3 ns tick); it issues no sub-tick strobe. The comparator
    strobe of each decision is made inside r1_adc from the same edge: the one-shot r1_cmp4_clkgen holds mclk low
    (comparator reset), then the SAR macro gates mclk to the comparator clock (clkX = mclk AND win). The comparator
    starts evaluating (strobe) when its clock rises.
  * Decision k is evaluated in tick k (E(k) .. E(k+1)); the CDAC line of decision k-1 switches after E(k).
Metric (this script, recommended option of T2m, spec-ambiguity recorded):
  * t_sw(s, k): 50 % crossing of the CDAC line switched by decision k-1 at the macro pin (sar_cpX / sar_cnX) after E(k).
  * t_stb(s, k): 50 % rising crossing of the comparator clock of decision k (k = 0: sar_clknX, r1_cmp5n; k >= 1:
    sar_clkX, r1_cmp4) after E(k), measured per tick on each run.
  * t_reg(s, k): regeneration, first time after t_stb at which a comparator output leaves its reset level by VDD/2
    (r1_cmp4: min(oXp, oXn) < VDD/2; r1_cmp5n: max(oXnp, oXnn) > VDD/2).
  * Capacitor steps, LSB unit and the reference correction of sim/r5/post_ref5.py (unchanged otherwise) from the base
    run sampled at t_stb (was 1.2 ns after E(k)).
  * Error of decision k (buffer run minus corrected base run, decisions 5..13 on the common path, slots >= 1):
      "strobe"  : at t_stb(s, k)                         -> R2-4 of record under D23 (literal)
      "boxcar"  : mean over t_stb .. t_reg (the double-tail comparator integrates its input over this interval)
      "regen"   : at t_reg(s, k) - 0.2 ns
      "25ns"    : at E(k) + 25 ns (the earlier convention, for comparison only)
      "at<x>"   : at E(k) + x ns (settling sweep: the strobe time after the edge that the reference needs)
usage: r24_d23.py OUT.json <buf run> <base run> va,vb vla,vlb Ma,La,Mb,Lb [--rundirs b6,b7]
Run ids are looked up under sim/post/b7/runs, b6/runs, b5/runs (raw file b5.raw or b7.raw in <G1_RESULTS_ROOT>/r1_adc/<id>/).
"""
import contextlib, io, json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
POST = os.path.dirname(HERE)
BLOCK = os.path.dirname(os.path.dirname(POST))
sys.path.insert(0, os.path.join(BLOCK, "sim"))
from rawread import read  # noqa: E402

root = os.environ["G1_RESULTS_ROOT"]
T = 1.0 / 30e6
ND = 14
out, rb, ri, pv, plv, sb = sys.argv[1:7]
Ma, La, Mb, Lb = [float(x) for x in sb.split(",")]
videal = 0.5 * (Ma + Mb)


def runjson(rid):
    for d in ("b9/runs", "b7/runs", "b6/runs", "b5/runs", "runs"):
        p = os.path.join(POST, d, rid, "run.json")
        if os.path.exists(p):
            return json.load(open(p))
    sys.exit("no run record " + rid)


cache, tim = {}, {}


def edges(d):
    """rising clk edges E(n) = n T (deck grid), returned as a function of the frame and tick"""
    return lambda s, k: (18 + 22 * s + k) * T


def cross(t, y, th, t0, t1, rising=True):
    m = (t >= t0) & (t <= t1)
    tt, yy = t[m], y[m]
    if not tt.size:
        return None
    ok = np.nonzero(yy >= th)[0] if rising else np.nonzero(yy <= th)[0]
    if not ok.size:
        return None
    i = ok[0]
    if i == 0:
        return float(tt[0])
    return float(tt[i - 1] + (th - yy[i - 1]) * (tt[i] - tt[i - 1]) / (yy[i] - yy[i - 1]))


def LOAD(rid):
    if rid in cache:
        return cache[rid]
    st = runjson(rid)["status"]
    if st not in ("completed", "completed-late"):
        sys.exit("run %s is %s" % (rid, st))
    rd = os.path.join(root, "r1_adc", rid)
    beh = os.path.exists(os.path.join(rd, "codes.raw"))
    fn = os.path.join(rd, "codes.raw") if beh else os.path.join(rd, "b5.raw")
    dd, _ = read(fn)
    if beh:
        # behavioural SAR runs (sim/post/run_post.py, D23 proxy core): map the names of the closed-loop decks
        for k in list(dd):
            if k.startswith("v(xadc.sar_"):
                dd["v(" + k[7:]] = dd[k]
        dd["v(clk)"] = dd["v(clk30)"]
    vdd = float(np.max(dd["v(clk)"]))
    for sl in ("" if beh else "ab"):
        w = np.zeros_like(dd["time"])
        for k in range(ND):
            w += (dd["v(adc_raw_%s_%d)" % (sl, k)] > 0.5 * vdd) * float(1 << k)
        dd["v(raw%s)" % sl] = w
    dd["v(vrefb)"], dd["v(vreflb)"] = dd["v(vrefa)"], dd["v(vrefla)"]
    t = dd["time"]
    nslot = int((t[-1] - 18 * T - ND * T - 30e-9) // (22 * T)) + 1
    E = edges(dd)
    TM = {}
    for sl in "ab":
        stb = np.full((nslot, ND), np.nan); reg = np.full((nslot, ND), np.nan); sw = np.full((nslot, ND), np.nan)
        for s in range(nslot):
            for k in range(ND):
                e = E(s, k)
                ck = "v(sar_clkn%s)" % sl if k == 0 else "v(sar_clk%s)" % sl
                # comparator clock: low at the edge (one-shot), rises after it
                tlow = cross(t, dd[ck], 0.5 * vdd, e - 0.2e-9, e + 4e-9, rising=False)
                ts_ = cross(t, dd[ck], 0.5 * vdd, (tlow if tlow is not None else e), e + 26e-9, rising=True)
                stb[s, k] = ts_ if ts_ is not None else np.nan
                if ts_ is not None:
                    if k == 0:
                        y = np.maximum(dd["v(sar_o%snp)" % sl], dd["v(sar_o%snn)" % sl])
                        tr = cross(t, y, 0.5 * vdd, ts_, e + T + 2e-9, rising=True)
                    else:
                        y = np.minimum(dd["v(sar_o%sp)" % sl], dd["v(sar_o%sn)" % sl])
                        tr = cross(t, y, 0.5 * vdd, ts_, e + T + 2e-9, rising=False)
                    reg[s, k] = tr if tr is not None else np.nan
                if k >= 1:
                    for pn in ("cp", "cn"):
                        nm = "v(sar_%s%s%d)" % (pn, sl, 13 - k)
                        x0, x1 = np.interp(e - 0.1e-9, t, dd[nm]), np.interp(e + 6e-9, t, dd[nm])
                        if x0 < 0.5 * vdd <= x1:
                            sw[s, k] = cross(t, dd[nm], 0.5 * vdd, e, e + 6e-9, True)
        TM[sl] = dict(stb=stb, reg=reg, sw=sw)
    dd["_T"] = TM
    dd["_E"] = E
    cache[rid] = dd
    return dd


R5 = os.path.join(BLOCK, "sim", "r5")
base = open(os.path.join(R5, "post_ref5.py")).read()
rep = [('seg = json.load(open(os.path.join(HERE, "..", "results", "r5", rid + "_segments.json")))', 'seg = {"segments": [1]}'),
       ('d, _ = read(os.path.join(root, "r1_adc", rid, "codes.raw"))', 'd = LOAD(rid)'),
       ('dM, dL = v1m * VIDEAL - VIDEAL, v1l * VIDEAL - VIDEAL',
        'dM, dL = v1m * VIDEAL - {"a": %r, "b": %r}[sl], v1l * VIDEAL - {"a": %r, "b": %r}[sl]' % (Ma, Mb, La, Lb)),
       # step samples at the measured strobe of the base run (per slot and tick)
       ('tr = [vd(d, sl, np.append(ts(s) + np.arange(ND) * T + 1.2e-9, ts(s) + ND * T + 5e-9)) for s in range(nslot)]',
        'tr = [vd(d, sl, np.append(STEPT(d, sl, s), ts(s) + ND * T + 5e-9)) for s in range(nslot)]'),
       ('        me = (vd(db, sl, tm) - (vd(di, sl, tm) - dM * SkM - dL * SkL)) / (v1m * lsb1)',
        '        me = MEFUN(vd, db, di, sl, s, dM * SkM + dL * SkL) / (v1m * lsb1)')]
for o, n in rep:
    assert base.count(o) == 1, o
    base = base.replace(o, n)
va, vb = pv.split(","); vla, vlb = plv.split(",")
for k, v in {'"v(vref%s)" % sl': '{"a": "%s", "b": "%s"}[sl]' % (va, vb),
             '"v(vrefl%s)" % sl': '{"a": "%s", "b": "%s"}[sl]' % (vla, vlb)}.items():
    base = base.replace("db, " + k, "db, " + v).replace("db[" + k, "db[" + v)


def STEPT(d, sl, s):
    st = d["_T"][sl]["stb"][s].copy()
    E = d["_E"]
    for k in range(ND):
        if np.isnan(st[k]):
            st[k] = E(s, k) + 2.0e-9
    return st


MODE = {"m": "strobe"}


def MEFUN(vd, db, di, sl, s, corr):
    E = db["_E"]
    st, rg = db["_T"][sl]["stb"][s], db["_T"][sl]["reg"][s]
    res = np.zeros(ND)
    for k in range(ND):
        e = E(s, k)
        tsk = st[k] if not np.isnan(st[k]) else e + 2e-9
        trk = rg[k] if not np.isnan(rg[k]) else e + 25e-9
        if MODE["m"] == "strobe":
            tq = np.array([tsk])
        elif MODE["m"] == "boxcar":
            tq = np.linspace(tsk, max(trk - 0.2e-9, tsk), 200)
        elif MODE["m"] == "regen":
            tq = np.array([max(trk - 0.2e-9, tsk)])
        elif MODE["m"].startswith("at"):
            tq = np.array([e + float(MODE["m"][2:]) * 1e-9])     # settling sweep: error at a fixed time after E(k)
        else:
            tq = np.array([e + 25e-9])
        res[k] = float(np.mean(vd(db, sl, tq) - (vd(di, sl, tq) - corr[k])))
    return res


def run(mode):
    MODE["m"] = mode
    tmp = out + ".tmp.json"
    sys.argv = ["post_ref5.py", rb, ri, tmp, str(videal)]
    g = {"__file__": os.path.join(R5, "post_ref5.py"), "__name__": "__main__", "LOAD": LOAD, "STEPT": STEPT, "MEFUN": MEFUN}
    with contextlib.redirect_stdout(io.StringIO()):
        exec(compile(src_, "post_ref5.py (b7 d23)", "exec"), g)
    D = json.load(open(tmp))
    os.remove(tmp)
    return D


src_ = base
var = {}
for mode in ("strobe", "boxcar", "regen", "25ns") + tuple("at%g" % x for x in (4, 6, 8, 10, 12, 14, 15, 16, 17, 18, 19, 20, 25)):
    D = run(mode)
    var[mode] = {"metric_lsb": D["max_abs_input_error_mid_eval_lsb"],
                 "after_gain_fit_lsb": D["max_abs_error_after_gain_fit_lsb"],
                 "max_code_diff_lsb": D["max_abs_code_diff_lsb"],
                 "slices": {sl: {"metric_lsb": D["slices"][sl]["max_abs_input_error_mid_eval_lsb"],
                                 "lsb_uV_at_1V": D["slices"][sl]["lsb_uV_at_1V"],
                                 "per_decision": D["slices"][sl]["max_abs_error_vs_decision_lsb"],
                                 "per_slot": {str(r["slot"]): (max([abs(x) for x in r["input_error_mid_eval_lsb_dec5_13"] if x is not None] or [0.0]),
                                                               r["bits_differ_at"][:1]) for r in D["slices"][sl]["slots"]}}
                            for sl in "ab"}}
db, di = LOAD(rb), LOAD(ri)
tim = {}
for nm, dd in (("buffer", db), ("base", di)):
    tim[nm] = {}
    for sl in "ab":
        X = dd["_T"][sl]
        e = np.array([[dd["_E"](s, k) for k in range(ND)] for s in range(X["stb"].shape[0])])
        stb, reg, sw = (X["stb"] - e) * 1e9, (X["reg"] - e) * 1e9, (X["sw"] - e) * 1e9
        avail = stb - sw
        f = lambda a: [round(float(np.nanmin(a)), 3), round(float(np.nanmax(a)), 3)] if np.any(~np.isnan(a)) else None
        tim[nm][sl] = {"switch_ns_after_edge": f(sw[:, 1:]), "strobe_ns_after_edge": f(stb), "strobe_dec0_ns": f(stb[:, :1]),
                       "regen_ns_after_edge": f(reg), "settling_available_ns_switch_to_strobe": f(avail[:, 1:]),
                       "integration_ns_strobe_to_regen": f((reg - stb)),
                       "per_decision_strobe_minus_switch_ns_min": [round(float(np.nanmin(avail[:, k])), 3) if np.any(~np.isnan(avail[:, k])) else None for k in range(ND)]}
res = {"tool": "sim/post/b9/r24_d28.py", "run_buffer": rb, "run_base": ri, "videal_V": videal,
       "static_base_correction_V": {"a": {"msb": Ma, "lsb": La}, "b": {"msb": Mb, "lsb": Lb}},
       "label": "simulated; R2-4 per PLAN.md D23 (steps and error at the measured comparator strobe); limit 0.25 LSB; "
                "boxcar / regen / 25ns are information", "timing": tim, "variants": var,
       "r24_d23_lsb": var["strobe"]["metric_lsb"], "pass_0p25": bool(var["strobe"]["metric_lsb"] <= 0.25)}
json.dump(res, open(out, "w"), indent=1)
for k, v in var.items():
    print("%-7s metric %.3f LSB (A %.3f, B %.3f), gain-fit %.3f" % (k, v["metric_lsb"], v["slices"]["a"]["metric_lsb"], v["slices"]["b"]["metric_lsb"], v["after_gain_fit_lsb"]))
print(json.dumps(tim, indent=0)[:3000])
