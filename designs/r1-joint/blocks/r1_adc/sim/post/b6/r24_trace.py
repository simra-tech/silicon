#!/usr/bin/env python3
"""T2l (layout B6, 2026-10-27): where does the R2-4 value of the closed-loop runs (gate-level r1_adc_sar) come from?

The metric is not changed: sim/r5/post_ref5.py through sim/post/b5/b5_post.py r24 (error at 25 ns into the tick, the
capacitor steps and the LSB unit from the base run at 1.2 ns after each clk edge). This script only adds diagnostics:

  1. switch timing per decision (base run): t_pin = 50 % crossing of the CDAC line that decision k switches
     (sar_cpX(12-k) or sar_cnX(12-k), the macro-pin node) after E(k+1); t90 / t99 = time after E(k+1) at which the
     top-plate differential step reaches 90 / 99 % of its value at 8 ns; fraction of the step present at 1.2 ns.
  2. the metric with the step sample time t_step in (1.2, 1.5, 2, 2.5, 3, 4) ns (1.2 = as defined; the others only
     locate the cause) and two attribution variants at t_step 1.2 ns: the LSB unit taken from the 4 ns steps
     (correction terms from 1.2 ns), and the correction terms from 4 ns with the LSB unit from 1.2 ns.
usage: r24_trace.py OUT.json <buf run> <base run> va,vb vla,vlb Ma,La,Mb,Lb   (run ids of sim/post/b5/runs or b6/runs)
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
    for d in ("b6", "b5"):
        p = os.path.join(POST, d, "runs", rid, "run.json")
        if os.path.exists(p):
            return json.load(open(p))
    sys.exit("no run record " + rid)


cache = {}


def B5LOAD(rid):
    if rid not in cache:
        st = runjson(rid)["status"]
        if st not in ("completed", "completed-late"):
            sys.exit("run %s is %s" % (rid, st))
        dd, _ = read(os.path.join(root, "r1_adc", rid, "b5.raw"))
        vth = 0.5 * float(np.max(dd["v(clk)"]))
        for sl in "ab":
            w = np.zeros_like(dd["time"])
            for k in range(ND):
                w += (dd["v(adc_raw_%s_%d)" % (sl, k)] > vth) * float(1 << k)
            dd["v(raw%s)" % sl] = w
        dd["v(vrefb)"], dd["v(vreflb)"] = dd["v(vrefa)"], dd["v(vrefla)"]
        cache[rid] = dd
    return cache[rid]


# ---- 1. switch timing on the base run
d = B5LOAD(ri)
tt = d["time"]
vdd = float(np.max(d["v(clk)"]))
nslot = int((tt[-1] - 18 * T - ND * T - 30e-9) // (22 * T)) + 1
timing = {}
for sl in "ab":
    vd = d["v(top%sp)" % sl] - d["v(top%sn)" % sl]
    rows = []
    for s in range(nslot):
        e0 = (18 + 22 * s) * T
        for k in range(13):
            E = e0 + (k + 1) * T
            line = None
            for pn in ("cp", "cn"):
                nm = "v(sar_%s%s%d)" % (pn, sl, 12 - k)
                x0, x1 = np.interp(E - 0.1e-9, tt, d[nm]), np.interp(E + 6e-9, tt, d[nm])
                if x0 < 0.5 * vdd <= x1:
                    line = nm
            if line is None:
                continue
            m = (tt >= E) & (tt <= E + 6e-9)
            tp = tt[m][np.argmax(d[line][m] >= 0.5 * vdd)] - E
            v0 = np.interp(E - 0.2e-9, tt, vd)
            v8 = np.interp(E + 8e-9, tt, vd)
            st = v8 - v0
            if abs(st) < 1e-4:
                continue
            g = np.arange(0.0, 8.0001, 0.02) * 1e-9
            fr = (np.interp(E + g, tt, vd) - v0) / st
            def tfrac(q):
                ok = np.nonzero(np.abs(fr - 1) > (1 - q))[0]
                return float(g[ok[-1] + 1] * 1e9) if ok.size and ok[-1] + 1 < g.size else 0.0
            rows.append(dict(slot=s, dec=k, line=line[2:-1], t_pin_ns=round(float(tp * 1e9), 3), step_mV=round(float(st * 1e3), 3),
                             frac_at_1p2=round(float(np.interp(1.2e-9, g, fr)), 4), frac_at_4=round(float(np.interp(4e-9, g, fr)), 4),
                             t90_ns=round(tfrac(0.90), 3), t99_ns=round(tfrac(0.99), 3)))
    big = [r for r in rows if abs(r["step_mV"]) > 2.0]
    timing[sl] = dict(rows=rows, t_pin_ns=[min(r["t_pin_ns"] for r in rows), max(r["t_pin_ns"] for r in rows)],
                      t99_ns_steps_gt_2mV=[min(r["t99_ns"] for r in big), max(r["t99_ns"] for r in big)] if big else None,
                      frac_at_1p2_range=[min(r["frac_at_1p2"] for r in rows), max(r["frac_at_1p2"] for r in rows)])

# ---- 2. metric variants (sim/r5/post_ref5.py patched as sim/post/b5/b5_post.py r24 does)
R5 = os.path.join(BLOCK, "sim", "r5")
base = open(os.path.join(R5, "post_ref5.py")).read()
rep = [('seg = json.load(open(os.path.join(HERE, "..", "results", "r5", rid + "_segments.json")))', 'seg = {"segments": [1]}'),
       ('d, _ = read(os.path.join(root, "r1_adc", rid, "codes.raw"))', 'd = B5LOAD(rid)'),
       ('dM, dL = v1m * VIDEAL - VIDEAL, v1l * VIDEAL - VIDEAL',
        'dM, dL = v1m * VIDEAL - {"a": %r, "b": %r}[sl], v1l * VIDEAL - {"a": %r, "b": %r}[sl]' % (Ma, Mb, La, Lb)),
       ('    lsb1 = (wp.sum() + wn.sum() + 0.5 * (wp[0] + wn[0])) / 4095.0',
        '    lsb1 = (wp.sum() + wn.sum() + 0.5 * (wp[0] + wn[0])) / 4095.0\n    LSBSEEN[sl] = lsb1\n    lsb1 = LSBFIX.get(sl, lsb1)\n'
        '    if STEPFIX: wp, wn = STEPFIX[sl]\n    STEPSEEN[sl] = (wp.copy(), wn.copy())')]
for o, n in rep:
    assert base.count(o) == 1, o
    base = base.replace(o, n)
va, vb = pv.split(","); vla, vlb = plv.split(",")
for k, v in {'"v(vref%s)" % sl': '{"a": "%s", "b": "%s"}[sl]' % (va, vb),
             '"v(vrefl%s)" % sl': '{"a": "%s", "b": "%s"}[sl]' % (vla, vlb)}.items():
    base = base.replace("db, " + k, "db, " + v).replace("db[" + k, "db[" + v)
o_stp = "np.arange(ND) * T + 1.2e-9"
assert base.count(o_stp) == 1


def run(tstep, lsbfix=None, stepfix=None):
    src = base.replace(o_stp, "np.arange(ND) * T + %ge-9" % tstep)
    tmp = out + ".tmp.json"
    sys.argv = ["post_ref5.py", rb, ri, tmp, str(videal)]
    g = {"__file__": os.path.join(R5, "post_ref5.py"), "__name__": "__main__", "B5LOAD": B5LOAD,
         "LSBFIX": lsbfix or {}, "STEPFIX": stepfix or {}, "LSBSEEN": {}, "STEPSEEN": {}}
    with contextlib.redirect_stdout(io.StringIO()):
        exec(compile(src, "post_ref5.py (b6 trace)", "exec"), g)
    D = json.load(open(tmp))
    os.remove(tmp)
    return D, g["LSBSEEN"], g["STEPSEEN"]


var = {}
seen = {}
for ts_ in (1.2, 1.5, 2.0, 2.5, 3.0, 4.0):
    D, L, S = run(ts_)
    seen[ts_] = (L, S)
    var["steps_at_%gns" % ts_] = {"metric_lsb": D["max_abs_input_error_mid_eval_lsb"],
                                  "slices": {sl: {"metric_lsb": D["slices"][sl]["max_abs_input_error_mid_eval_lsb"],
                                                  "lsb_uV": round(L[sl] * 1e6, 3),
                                                  "per_decision": D["slices"][sl]["max_abs_error_vs_decision_lsb"]} for sl in "ab"}}
D, _, _ = run(1.2, lsbfix=seen[4.0][0])
var["steps_1.2ns_lsb_unit_from_4ns"] = {"metric_lsb": D["max_abs_input_error_mid_eval_lsb"],
                                         "slices": {sl: D["slices"][sl]["max_abs_input_error_mid_eval_lsb"] for sl in "ab"}}
D, _, _ = run(1.2, stepfix=seen[4.0][1], lsbfix=seen[1.2][0])
var["steps_4ns_corrections_lsb_unit_from_1.2ns"] = {"metric_lsb": D["max_abs_input_error_mid_eval_lsb"],
                                                    "slices": {sl: D["slices"][sl]["max_abs_input_error_mid_eval_lsb"] for sl in "ab"}}
res = {"tool": "sim/post/b6/r24_trace.py", "run_buffer": rb, "run_base": ri,
       "label": "simulated; diagnostics only, the R2-4 metric as defined is variant steps_at_1.2ns",
       "switch_timing": {sl: {k: v for k, v in timing[sl].items() if k != "rows"} for sl in "ab"},
       "switch_timing_per_decision": {sl: {str(k): {"t_pin_ns": [min(r["t_pin_ns"] for r in timing[sl]["rows"] if r["dec"] == k),
                                                                  max(r["t_pin_ns"] for r in timing[sl]["rows"] if r["dec"] == k)],
                                                     "frac_at_1p2": [min(r["frac_at_1p2"] for r in timing[sl]["rows"] if r["dec"] == k),
                                                                     max(r["frac_at_1p2"] for r in timing[sl]["rows"] if r["dec"] == k)],
                                                     "t99_ns_max": max(r["t99_ns"] for r in timing[sl]["rows"] if r["dec"] == k)}
                                           for k in range(13) if any(r["dec"] == k for r in timing[sl]["rows"])} for sl in "ab"},
       "variants": var, "rows": {sl: timing[sl]["rows"] for sl in "ab"}}
json.dump(res, open(out, "w"), indent=1)
for k, v in var.items():
    print(k, json.dumps(v)[:300])
print(json.dumps(res["switch_timing"]))
for sl in "ab":
    print(sl, {k: (v["t_pin_ns"], v["frac_at_1p2"], v["t99_ns_max"]) for k, v in res["switch_timing_per_decision"][sl].items()})
