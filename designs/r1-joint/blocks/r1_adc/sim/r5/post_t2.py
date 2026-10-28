#!/usr/bin/env python3
"""T2 2026-10-21: post-processors of the revision-5 closure campaign (one file, one sub-command per check).
Codes use the design weights (nominal AC-solved array, sim/results/r3/cdac3_mc50_tt_cp100_globalfit.json; the CDAC
is unchanged since revision 3) unless stated. Frame timing, raw-word decoding: sim/r4/p4common.py.

  post_t2.py first OUT.json <run id> ...       first conversion: frame 0 against frame 1 (same input), per slice;
                                               bootstrap-capacitor voltage of the slice-A N-side in0 switch at 599 ns
  post_t2.py win OUT.json <run id> <lsb V>     static windows (points/cornwin5.json: frame 0 start-up, 2 windows of 25)
  post_t2.py dyn OUT.json N M <run c0> <run c1> ...   coherent FFT; chunk c: local frames 1..128 = global 128c..128c+127
  post_t2.py isa OUT.json <run id>             mux sequence e c e e (tb_adc5_isa.cir), track, latch, IDD, IDDA
  post_t2.py inl OUT.json <mc5 sample prefix> <run:points file> ...   reduced-ramp INL with the fitted weights of
                                               mc5_summary.json (runs of one MC seed; frame 0 of every run not used)
"""
import json
import os
import sys
import numpy as np
_trapz = getattr(np, "trapezoid", None) or np.trapz  # numpy 2 removed np.trapz (ledger F-20261030-273)
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "r4"))
sys.path.insert(0, os.path.join(HERE, "..", "r3"))
from p4common import read, ts, sample, bits_from_raw, BLOCK, TLAT, T, load_segments
import cal3
root = os.environ["G1_RESULTS_ROOT"]
WL = np.array(json.load(open(os.path.join(BLOCK, "sim", "results", "r3", "cdac3_mc50_tt_cp100_globalfit.json")))["nominal_design_weights_lsb"])
WD = cal3.quantise(WL)
_C = json.load(open(os.path.join(BLOCK, "sim", "results", "r5", "mc_window_check.json")))["slices"]["a"]
# LSB of the design-weight transfer (locate run r5-locate-tt, tt, VREF 1.045 V): transitions 2047/2048 and 3071/3072
# are 1024 LSB apart -> 454.9 uV. (lsb_V 466.5 uV in that file is the point-placement scale, not the LSB; using it gave
# a false +2.4 % gain in the first mux post-processing, T2 2026-10-21.)
LSB_LOC = (_C["code_3071_3072_V"] - _C["code_2047_2048_V"]) / 1024.0
STEP_WIN = 0.5 * 466.488e-6   # point spacing of points/cornwin5.json
cmd, out = sys.argv[1], sys.argv[2]
A = sys.argv[3:]
raw = lambda rid: read(os.path.join(root, "r1_adc", rid, "codes.raw"))[0]
res = {"tool": "sim/r5/post_t2.py " + cmd}

if cmd == "first":
    res["label"] = "simulated (sim/r5/tb_adc5_points.cir, r1_adc5_core_fast, ideal VREF 1.045 V), design weights"
    res["runs"] = {}
    for rid in A:
        d = raw(rid)
        r = {}
        for sl in "ab":
            c = cal3.code(bits_from_raw(sample(d, "v(raw%s)" % sl, ts([0, 1], sl) + TLAT)), WD)
            r[sl] = {"code_frame0": int(c[0]), "code_frame1": int(c[1]), "frame0_minus_frame1_lsb": int(c[0] - c[1])}
        if "v(xadc.xtha.xs0n.cbp)" in d:
            r["slice_a_in0n_boost_V_at_599ns"] = round(float(sample(d, "v(xadc.xtha.xs0n.cbp)", [599e-9])[0] - sample(d, "v(xadc.xtha.xs0n.cbn)", [599e-9])[0]), 4)
            r["slice_a_topan_V_at_599ns"] = round(float(sample(d, "v(topan)", [599e-9])[0]), 4)
            r["slice_a_in0n_gate_V_at_599ns"] = round(float(sample(d, "v(xadc.xtha.xs0n.g)", [599e-9])[0]), 4)
        res["runs"][rid] = r
elif cmd == "win":
    rid, lsb = A[0], float(A[1])
    P = json.load(open(os.path.join(BLOCK, "sim", "r5", "points", "cornwin5.json")))
    slots, ba, bb = load_segments(os.path.join(BLOCK, "sim", "results", "r5", rid + "_segments.json"), root)
    res.update(label="simulated (sim/r5/tb_adc5_points.cir, r1_adc5_core_fast, ideal VREF 1.045 V), design weights", run=rid)
    for sl, bits in (("a", ba), ("b", bb)):
        keep = slots >= 1
        v = np.array(P[sl])[slots[keep]]
        bt = bits[keep]
        wi = (slots[keep] - 1) // 25
        M = LSB_LOC / STEP_WIN       # conversions per LSB (1.95)
        rs = {}
        for w in range(2):
            o = np.argsort(v[wi == w])
            c = cal3.code(bt[wi == w][o], WD)
            codes, cnt = np.unique(c, return_counts=True)
            widths = {int(k): float(n) / M for k, n in zip(codes[1:-1], cnt[1:-1])}
            rs[str(w)] = {"codes": [int(c.min()), int(c.max())], "monotonic": bool(np.all(np.diff(c) >= 0)),
                          "missing_inside": int(np.sum(np.diff(c) > 1)), "missing_codes": [int(x) + 1 for x, y in zip(c[:-1], c[1:]) if y - x > 1],
                          "dnl_by_code": {k: round(x - 1, 3) for k, x in widths.items()},
                          "max_abs_dnl": float(max(abs(x - 1) for x in widths.values())) if widths else None}
        res[sl] = {"windows": rs, "points_per_lsb": round(M, 3), "max_abs_dnl": max(x["max_abs_dnl"] for x in rs.values()),
                   "monotonic": all(x["monotonic"] for x in rs.values()), "missing_inside": sum(x["missing_inside"] for x in rs.values())}
elif cmd == "dyn":
    N, Mc, runs = int(A[0]), int(A[1]), A[2:]
    codes = {"a": [], "b": []}
    for rid in runs:
        d = raw(rid)
        loc = np.arange(1, 129)
        loc = loc[ts(loc) + TLAT < d["time"][-1]]
        for sl in "ab":
            codes[sl] += list(cal3.code(bits_from_raw(sample(d, "v(raw%s)" % sl, ts(loc, sl) + TLAT)), WD))
    res.update(label="simulated (sim/r5/tb_adc5_dyn.cir, r1_adc5_core_fast, ideal VREF 1.045 V), design weights, no device noise",
               runs=runs, N=N, cycles=Mc, frames_available=len(codes["a"]))
    if len(codes["a"]) < N:
        res["error"] = "fewer than N frames"
    else:
        for sl in "ab":
            c = np.array(codes[sl][:N], dtype=float)
            X = np.abs(np.fft.rfft(c - c.mean())) ** 2
            sig = X[Mc]
            hb = [(k * Mc) % N for k in range(2, 6)]
            harm = [X[h if h <= N // 2 else N - h] for h in hb]
            noise = X[1:].sum() - sig
            sndr = 10 * np.log10(sig / noise)
            res[sl] = {"sndr_dB": float(sndr), "enob": float((sndr - 1.76) / 6.02),
                       "sfdr_dB": float(10 * np.log10(sig / np.max(np.delete(X[1:], Mc - 1)))),
                       "thd_dB": float(10 * np.log10(sum(harm) / sig)),
                       "amplitude_codes": float(2 * np.sqrt(sig) / N), "codes_min_max": [int(c.min()), int(c.max())]}
elif cmd == "isa":
    rid = A[0]
    d = raw(rid)
    SEQ = [("enc", "0", 0.40, -0.40), ("cur", "1", 0.85, -0.85), ("enc", "0", -0.40, 0.40), ("enc", "0", 0.72, -0.72)]
    res.update(label="simulated (sim/r5/tb_adc5_isa.cir, r1_adc5_core full core, option 3c reference with the r1_bgr model), design weights; "
               "nominal line 2047.5 + v / LSB, LSB = 454.9 uV x VREF / 1.045 V (locate run)", run=rid, frames=[])
    t = d["time"]
    for f, (kind, inp, va, vb) in enumerate(SEQ):
        row = {"frame": f, "input": kind}
        for sl, v in (("a", va), ("b", vb)):
            e = float(ts(f, sl))
            vr = float(sample(d, "v(vrefa)", [e - 0.2e-9])[0])
            lsb = LSB_LOC * vr / 1.045
            c = int(cal3.code(bits_from_raw(sample(d, "v(raw%s)" % sl, [e + TLAT])), WD)[0])
            x = d["v(trk%s%s)" % (sl, inp)]
            m = (t > e - 400e-9) & (t < e - 0.01e-9)
            hi = t[m][x[m] > 0.6 * x.max()]
            m2 = (t > e) & (t < e + 600e-9)
            la = t[m2][d["v(lat%s)" % sl][m2] > 0.6 * d["v(lat%s)" % sl].max()]
            row[sl] = {"vin_V": v, "code": c, "ideal_code": round(2047.5 + v / lsb, 1), "error_lsb": round(c - (2047.5 + v / lsb), 2),
                       "track_ns": round(float(hi.max() - hi.min()) * 1e9, 1) if hi.size else None,
                       "latch_after_edge_ticks": round(float(la.min() - e) / T, 2) if la.size else None, "vref_V": round(vr, 5)}
        res["frames"].append(row)
    m = t > 0.6e-6
    tt, idd = t[m], -d["i(vdd)"][m]
    res["idd_mA"] = float(_trapz(idd, tt) / (tt[-1] - tt[0]) * 1e3)
    if "i(vdda)" in d:
        res["idda_mA"] = float(_trapz(-d["i(vdda)"][m], tt) / (tt[-1] - tt[0]) * 1e3)
    res["max_abs_error_lsb"] = max(abs(r[s]["error_lsb"]) for r in res["frames"] for s in "ab")
    # linear part (gain and offset, removed by the gain/weight calibration): least squares over the 8 conversions
    x = np.array([r[s]["ideal_code"] - 2047.5 for r in res["frames"] for s in "ab"])
    y = np.array([r[s]["code"] - 2047.5 for r in res["frames"] for s in "ab"], dtype=float)
    g, o = np.polyfit(x, y, 1)
    res["gain_fit"] = {"gain": round(float(g), 5), "offset_lsb": round(float(o), 2),
                       "max_abs_residual_lsb": round(float(np.max(np.abs(y - g * x - o))), 2)}
    res["min_track_ns"] = min(r[s]["track_ns"] for r in res["frames"] for s in "ab" if r[s]["track_ns"] is not None)
elif cmd == "inl":
    pref, runs = A[0], A[1:]
    S = json.load(open(os.path.join(BLOCK, "sim", "results", "r5", "mc5_summary.json")))["samples"]
    V = {"a": [], "b": []}
    BT = {"a": [], "b": []}
    for arg in runs:
        rid, pf = arg.split(":")
        P = json.load(open(os.path.join(BLOCK, "sim", "r5", "points", pf)))
        slots, ba, bb = load_segments(os.path.join(BLOCK, "sim", "results", "r5", rid + "_segments.json"), root, "m0")
        keep = slots >= 1
        for sl, bits in (("a", ba), ("b", bb)):
            V[sl].append(np.array(P[sl])[slots[keep]] / LSB_LOC)
            BT[sl].append(bits[keep])
    res.update(label="simulated (sim/r5/tb_adc5_points.cir, run_points5.py --mcs 1: nominal fast core with sampled MIM mismatch, "
               "ideal VREF 1.045 V, tt), fitted weights of sim/results/r5/mc5_summary.json; reduced ramp (one conversion per "
               "about 40 LSB); INL = deviation from the best straight line, in LSB", runs=runs)
    for sl in "ab":
        v, bt = np.concatenate(V[sl]), np.concatenate(BT[sl])
        smp = S["%s/m0%s" % (pref, sl)]
        r = {"mc_sample": "%s/m0%s" % (pref, sl), "conversions": int(len(v)), "input_range_lsb": [round(float(v.min()), 1), round(float(v.max()), 1)]}
        for tag, W in (("fit", np.array(smp["W_fit"])), ("design", WD)):
            c = cal3.code(bt, W).astype(float)
            y = bt.astype(float) @ (W / 8.0)                 # unrounded reconstruction (LSB)
            inside = (c > 0) & (c < 4095)
            for nm, z in (("code", c), ("unrounded", y)):
                p = np.polyfit(v[inside], z[inside], 1)
                e = z[inside] - np.polyval(p, v[inside])
                r["%s_%s" % (tag, nm)] = {"gain": float(p[0]), "max_abs_inl_lsb": float(np.max(np.abs(e))), "rms_lsb": float(np.sqrt(np.mean(e ** 2))),
                                          "cubic_fit_peak_lsb": float(np.max(np.abs(np.polyval(np.polyfit(v[inside], e, 3), v[inside])))),
                                          "inl_lsb": [round(float(x), 3) for x in e]}
            r["%s_monotonic_ramp" % tag] = bool(np.all(np.diff(c[np.argsort(v)]) >= 0))
        res[sl] = r
else:
    sys.exit("unknown command")
json.dump(res, open(out, "w"), indent=1)
print(json.dumps({k: v for k, v in res.items() if k not in ("frames",)}, indent=1)[:3000])
if cmd == "isa":
    for r in res["frames"]:
        print(r)
