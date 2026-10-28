#!/usr/bin/env python3
"""item3_regen.py OUT.json <run> <reference run> [capture]   (T2o, PLAN.md D28 item 3, 2026-10-28)
Regeneration budget of the revision-6 strobe on a closed-loop run (proxy deck: behavioural SAR with the gate-level
timing, decision captured at E(k+1) - 0.6 ns; gate-level runs: capture E(k+1) + 0.5 ns, pass 'gl').
Per slice, slot and decision: strobe t_stb (comparator clock rises), regeneration t_reg (first output leaves reset by
VDD/2, same definition as sim/post/b9/r24_d28.py), and the comparator input vd at t_stb. A decision is 'not
regenerated' when t_reg is later than the capture instant or absent. Codes: design weights (sim/r5/post_t2.py, cal3),
error = code(run) - code(reference run) per slot, in LSB.
The reference run is the same deck with the revision-5 strobe (e.g. postb7-d23-ref-tt-base)."""
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
POST = os.path.dirname(HERE)
BLOCK = os.path.dirname(os.path.dirname(POST))
sys.path.insert(0, os.path.join(BLOCK, "sim"))
sys.path.insert(0, os.path.join(BLOCK, "sim", "r4"))
sys.path.insert(0, os.path.join(BLOCK, "sim", "r3"))
import cal3  # noqa
from p4common import bits_from_raw  # noqa
WD = cal3.quantise(np.array(json.load(open(os.path.join(BLOCK, "sim", "results", "r3", "cdac3_mc50_tt_cp100_globalfit.json")))["nominal_design_weights_lsb"]))
from rawread import read  # noqa
root = os.environ["G1_RESULTS_ROOT"]
T = 1.0 / 30e6; ND = 14; NB = 13
out, rid, refid = sys.argv[1:4]
cap = sys.argv[4] if len(sys.argv) > 4 else "proxy"
CAPT = -0.6e-9 if cap == "proxy" else 0.5e-9


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


def load(r):
    rd = os.path.join(root, "r1_adc", r)
    beh = os.path.exists(os.path.join(rd, "codes.raw"))
    d, _ = read(os.path.join(rd, "codes.raw" if beh else "b5.raw"))
    if beh:
        for k in list(d):
            if k.startswith("v(xadc.sar_"):
                d["v(" + k[7:]] = d[k]
        d["v(clk)"] = d["v(clk30)"]
    return d, beh


def E(s, k):
    return (18 + 22 * s + k) * T


def analyse(d):
    t = d["time"]; vdd = float(np.max(d["v(clk)"]))
    nslot = int((t[-1] - 18 * T - ND * T - 30e-9) // (22 * T)) + 1
    R = {}
    for sl in "ab":
        p, n = ("v(topap)", "v(topan)") if sl == "a" else ("v(topbp)", "v(topbn)")
        rows = []
        for s in range(nslot):
            for k in range(ND):
                e = E(s, k)
                ck = "v(sar_clkn%s)" % sl if k == 0 else "v(sar_clk%s)" % sl
                tlow = cross(t, d[ck], 0.5 * vdd, e - 0.2e-9, e + 4e-9, rising=False)
                ts_ = cross(t, d[ck], 0.5 * vdd, tlow if tlow is not None else e, e + 26e-9, True)
                tr = None
                if ts_ is not None:
                    if k == 0:
                        y = np.maximum(d["v(sar_o%snp)" % sl], d["v(sar_o%snn)" % sl])
                        tr = cross(t, y, 0.5 * vdd, ts_, e + T + 2e-9, True)
                    else:
                        y = np.minimum(d["v(sar_o%sp)" % sl], d["v(sar_o%sn)" % sl])
                        tr = cross(t, y, 0.5 * vdd, ts_, e + T + 2e-9, False)
                vd = float(np.interp(ts_ if ts_ is not None else e + 17e-9, t, d[p]) - np.interp(ts_ if ts_ is not None else e + 17e-9, t, d[n]))
                capt = e + T + CAPT
                rows.append(dict(slot=s, k=k, stb_ns=None if ts_ is None else round((ts_ - e) * 1e9, 3),
                                 reg_ns=None if tr is None else round((tr - e) * 1e9, 3),
                                 slack_ns=None if tr is None else round((capt - tr) * 1e9, 3),
                                 vd_mV=round(vd * 1e3, 4), regenerated=bool(tr is not None and tr <= capt)))
        # code at the end of the conversion (raw word sampled after the last decision)
        raw = []
        for s in range(nslot):
            tq = E(s, 0) + ND * T + 5e-9
            if "v(raw%s)" % sl in d:
                w = int(round(float(np.interp(tq, t, d["v(raw%s)" % sl]))))
            else:
                w = sum((1 << b) for b in range(ND) if np.interp(tq, t, d["v(adc_raw_%s_%d)" % (sl, b)]) > 0.5 * vdd)
            raw.append(w)
        R[sl] = dict(rows=rows, raw=raw, nslot=nslot)
    return R


def weights(d, sl, nslot):
    p, n = ("v(topap)", "v(topan)") if sl == "a" else ("v(topbp)", "v(topbn)")
    t = d["time"]
    sp = [[] for _ in range(NB)]; sn = [[] for _ in range(NB)]
    for s in range(nslot):
        v = [np.interp(E(s, k) + 1.2e-9, t, d[p]) - np.interp(E(s, k) + 1.2e-9, t, d[n]) for k in range(ND)]
        dv = np.diff(v)
        for j in range(NB):
            (sp if dv[j] < 0 else sn)[NB - 1 - j].append(abs(dv[j]))
    wp = np.array([np.mean(x) if x else np.nan for x in sp]); wn = np.array([np.mean(x) if x else np.nan for x in sn])
    wp = np.where(np.isnan(wp), wn, wp); wn = np.where(np.isnan(wn), wp, wn)
    Wd = np.array([wp[NB - 1 - j] + wn[NB - 1 - j] for j in range(NB)] + [0.5 * (wp[0] + wn[0])])
    return Wd / Wd.sum() * 4095


def code(w, Wd=None):
    return float(cal3.code(bits_from_raw(np.array([w])), WD)[0])


dr, _ = load(rid); df, _ = load(refid)
A, B = analyse(dr), analyse(df)
res = {"tool": "sim/post/b9/item3_regen.py", "label": "simulated", "run": rid, "reference_run": refid, "capture": cap,
       "capture_ns_after_next_edge": CAPT * 1e9, "slices": {}}
for sl in "ab":
    ns = min(A[sl]["nslot"], B[sl]["nslot"])
    Wd = None
    rows = A[sl]["rows"]
    nr = [r for r in rows if not r["regenerated"] and r["slot"] < ns]
    errs = [code(A[sl]["raw"][s], Wd) - code(B[sl]["raw"][s], Wd) for s in range(ns)]
    def tail(kk):
        x = [r["reg_ns"] - r["stb_ns"] for r in rows if r["k"] in kk and r["reg_ns"] is not None and r["stb_ns"] is not None]
        return None if not x else {"n": len(x), "min": round(min(x), 3), "p50": round(float(np.percentile(x, 50)), 3),
                                   "p90": round(float(np.percentile(x, 90)), 3), "max": round(max(x), 3)}
    res["slices"][sl] = {
        "slots": ns, "raw_run": A[sl]["raw"][:ns], "raw_reference": B[sl]["raw"][:ns],
        "code_run": [code(w) for w in A[sl]["raw"][:ns]], "code_reference": [code(w) for w in B[sl]["raw"][:ns]],
        "code_error_lsb": [round(e, 2) for e in errs], "max_abs_code_error_lsb": round(max(abs(e) for e in errs), 2),
        "not_regenerated": len(nr), "decisions": ns * ND,
        "not_regenerated_by_decision": {str(k): sum(1 for r in nr if r["k"] == k) for k in range(ND)},
        "not_regenerated_vd_mV_max_abs": round(max([abs(r["vd_mV"]) for r in nr] or [0.0]), 3),
        "strobe_ns_after_edge": [min(r["stb_ns"] for r in rows if r["stb_ns"] is not None), max(r["stb_ns"] for r in rows if r["stb_ns"] is not None)],
        "integration_ns_cmp5n_dec0": tail([0]), "integration_ns_cmp4_dec1_13": tail(range(1, ND)),
        "slack_ns_min_regenerated": min([r["slack_ns"] for r in rows if r["regenerated"]] or [None] if rows else [None]),
        "rows": rows}
json.dump(res, open(out, "w"), indent=0)
for sl in "ab":
    x = res["slices"][sl]
    print(sl, "slots", x["slots"], "not regen", x["not_regenerated"], "/", x["decisions"], "by k", x["not_regenerated_by_decision"],
          "max|vd| nr %.3f mV" % x["not_regenerated_vd_mV_max_abs"], "max code err %.2f LSB" % x["max_abs_code_error_lsb"],
          "stb", x["strobe_ns_after_edge"], "int cmp4", x["integration_ns_cmp4_dec1_13"], "int cmp5n", x["integration_ns_cmp5n_dec0"])
