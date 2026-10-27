#!/usr/bin/env python3
"""T2k (layout B5 helper, 2026-10-27): post-processing of the closed-loop decks of sim/post/b5 (run_b5.py runs).

  b5_post.py dec    OUT.json <run> <ref run> <frames>   decisions per frame and slice against a behavioural-SAR run of
                                                          sim/post (codes.raw, v(rawa) / v(rawb)); frames e.g. ecee / ee
  b5_post.py timing OUT.json <run>                        output-change window of adc_raw_* / adc_valid_* after the
                                                          rising clk edge (INTERFACES "ADC -> ctrl timing")
  b5_post.py r24    OUT.json <buf run> <base run> va,vb vla,vlb Ma,La,Mb,Lb
                                                          R2-4 (post_post.py ref method) on two closed-loop runs

Common definitions (simulated values only):
  * Frame f of a deck samples at tick n0 = 18 + 22 f; E(k) = (n0 + k) T, T = 1 / 30 MHz (clk rising edges at n T; the
    behavioural decks use the same grid: sim/r4/p4common.py ts()). Decision k is evaluated in tick k (E(k) .. E(k+1))
    and taken at E(k+1). raw[13] = decision 0.
  * Closed-loop word: adc_raw_X_k at E15 - 1 ns (the edge at which r1_ctrl captures it), threshold VDD / 2; valid must
    be high there and low at E14 - 1 ns. Reference word: v(rawX) of the behavioural run at E0 + 14 T + 20 ns
    (p4common TLAT), as every sim/post post-processor.
  * Codes: design weights (sim/results/r3/cdac3_mc50_tt_cp100_globalfit.json, cal3.quantise / cal3.code), as post_t2.py.
  * Tie classification (recommended option, recorded): for the first differing decision k of a frame and slice, the
    top-plate differential vd = v(topXp) - v(topXn) is read 10, 16 and 19 ns after E(k) (16 ns = before the comparator
    regenerates at tt, README B4 "R2-4 at decisions 12-13") and its minimum |vd| over E(k) + 4 .. 16 ns. It is given in
    LSB at the top plate (lsb_uV_at_1V of the B4 R2-4 record x VREF 1.045 V). The comparator does not switch at vd = 0:
    its effective threshold (offset and dynamic effects) is estimated per slice from all decisions 1..13 of the
    closed-loop run (midpoint between the largest vd(16 ns) with decision 0 and the smallest with decision 1). Class
    "tie" if |vd(16 ns) - threshold| <= 0.25 LSB (the R2-4 limit), "near threshold" if <= 0.5 LSB, else "not a tie".
    (First version: distance from 0 V; it called every difference of run b5pre-ms-mux-tt "not a tie" although vd had
    the same sign in both runs.) Later differing decisions of the same word follow from the first one.
"""
import json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
POST = os.path.dirname(HERE)
BLOCK = os.path.dirname(os.path.dirname(POST))
sys.path.insert(0, os.path.join(BLOCK, "sim"))
sys.path.insert(0, os.path.join(BLOCK, "sim", "r3"))
sys.path.insert(0, os.path.join(BLOCK, "sim", "r4"))
from rawread import read  # noqa: E402
import cal3  # noqa: E402

root = os.environ["G1_RESULTS_ROOT"]
T = 1.0 / 30e6
ND = 14
TLAT = ND * T + 20e-9
cmd, out, A = sys.argv[1], sys.argv[2], sys.argv[3:]
WD = cal3.quantise(np.array(json.load(open(os.path.join(BLOCK, "sim", "results", "r3", "cdac3_mc50_tt_cp100_globalfit.json")))["nominal_design_weights_lsb"]))
RAWN = ["v(adc_raw_%s_%d)" % (s, k) for s in "ab" for k in range(ND)]


def b5run(rid):
    rj = os.path.join(HERE, "runs", rid, "run.json")
    if not os.path.exists(rj):      # T2l: layout B6 runs are recorded under sim/post/b6/runs
        rj = os.path.join(HERE, "..", "b6", "runs", rid, "run.json")
    d = json.load(open(rj))
    if d["status"] not in ("completed", "completed-late") or d.get("smoke_test"):
        sys.exit("run %s is %s%s: not post-processed" % (rid, d["status"], " (smoke test)" if d.get("smoke_test") else ""))
    raw, var = read(os.path.join(root, "r1_adc", rid, "b5.raw"))
    return d, raw


def interp(d, n, t):
    return np.interp(t, d["time"], d[n])


def e0(f):
    return (18 + 22 * f) * T


def word_cl(d, f, sl, vth):
    t15, t14 = e0(f) + 15 * T - 1e-9, e0(f) + 14 * T - 1e-9
    w = 0
    for k in range(ND):
        w |= (1 if interp(d, "v(adc_raw_%s_%d)" % (sl, k), t15) > vth else 0) << k
    v_on = bool(interp(d, "v(adc_valid_%s)" % sl, t15) > vth)
    v_off = bool(interp(d, "v(adc_valid_%s)" % sl, t14) < vth)
    return w, v_on, v_off


def bits(w):
    return np.array([(w >> (ND - 1 - j)) & 1 for j in range(ND)], dtype=np.uint8)


def lsb_top(corner):
    f = "postb4_ref_ss125_rc.json" if corner == "mos_ss" else "postb4_ref_tt_rc.json"
    R = json.load(open(os.path.join(POST, "results", f)))
    return {sl: R["slices"][sl]["lsb_uV_at_1V"] * 1e-6 * 1.045 for sl in "ab"}, f


def vd(d, sl, t):
    return interp(d, "v(top%sp)" % sl, t) - interp(d, "v(top%sn)" % sl, t)


if cmd == "dec":
    rid, rref, frames = A[0], A[1], A[2]
    meta, d = b5run(rid)
    vdd = float(np.max(d["v(clk)"]))
    vth = 0.5 * vdd
    corner = "mos_ss" if vdd < 1.15 else "mos_tt"
    L, lsbsrc = lsb_top(corner)
    dr, var_r = read(os.path.join(root, "r1_adc", rref, "codes.raw"))
    has_top_ref = "v(topap)" in dr
    res = {"tool": "sim/post/b5/b5_post.py dec", "run": rid, "reference_run": rref,
           "label": "simulated; closed loop (gate-level r1_adc_sar) against the behavioural r1_sar5_logic run on the same "
                    "analog netlist; design weights; tie threshold 0.25 LSB at 16 ns (see header)",
           "top_plate_lsb_V": L, "lsb_source": "sim/post/results/" + lsbsrc, "frames": [], "decisions_total": 0,
           "decisions_equal": 0, "words_equal": 0, "words_total": 0, "valid_ok": 0, "first_differences": []}
    # effective comparator threshold per slice (closed-loop run): vd(16 ns) of decisions 1..13 of all frames; threshold =
    # midpoint between the largest vd with decision 0 and the smallest vd with decision 1 (comparator offset + dynamic
    # effects; at tt it is about +0.2 .. +0.4 mV, not 0)
    VTH = {}
    for sl in "ab":
        p0, p1 = [], []
        for f in range(len(frames)):
            w, _, _ = word_cl(d, f, sl, vth)
            b = bits(w)
            for k in range(1, ND):
                (p1 if b[k] else p0).append(float(vd(d, sl, e0(f) + k * T + 16e-9)))
        lo, hi = max(p0), min(p1)
        VTH[sl] = {"vth_mV": round(0.5 * (lo + hi) * 1e3, 4), "dec0_max_mV": round(lo * 1e3, 4), "dec1_min_mV": round(hi * 1e3, 4),
                   "separable": bool(lo < hi)}
    res["comparator_threshold_16ns"] = VTH
    for f, c in enumerate(frames):
        for sl in "ab":
            w, von, voff = word_cl(d, f, sl, vth)
            wr = int(np.rint(interp(dr, "v(raw%s)" % sl, e0(f) + TLAT)))
            bc, br = bits(w), bits(wr)
            cc, cr = int(cal3.code(bc[None, :], WD)[0]), int(cal3.code(br[None, :], WD)[0])
            dif = [int(j) for j in np.nonzero(bc != br)[0]]
            row = {"frame": f, "type": c, "slice": sl.upper(), "word_bits": "".join(map(str, bc)), "ref_bits": "".join(map(str, br)),
                   "code": cc, "ref_code": cr, "code_diff_lsb": cc - cr, "valid_at_E15": von, "valid_low_before_E14": voff,
                   "decisions_differ_at": dif}
            if dif:
                k = dif[0]
                tk = e0(f) + k * T
                tt = d["time"]
                m = (tt >= tk + 4e-9) & (tt <= tk + 16e-9)
                x = (d["v(top%sp)" % sl] - d["v(top%sn)" % sl])[m]
                fd = {"frame": f, "slice": sl.upper(), "decision": k,
                      "vd_cl_mV": {"%dns" % n: round(float(vd(d, sl, tk + n * 1e-9)) * 1e3, 4) for n in (10, 16, 19)},
                      "vd_cl_lsb_16ns": round(float(vd(d, sl, tk + 16e-9)) / L[sl], 3),
                      "min_abs_vd_cl_4_16ns_lsb": round(float(np.min(np.abs(x))) / L[sl], 3) if x.size else None,
                      "closed_loop_decision": int(bc[k]), "reference_decision": int(br[k])}
                if has_top_ref:
                    fd["vd_ref_mV"] = {"%dns" % n: round(float(vd(dr, sl, tk + n * 1e-9)) * 1e3, 4) for n in (10, 16, 19)}
                    fd["vd_ref_lsb_16ns"] = round(float(vd(dr, sl, tk + 16e-9)) / L[sl], 3)
                else:
                    fd["vd_ref_mV"] = "not saved in the reference run"
                dv = (float(vd(d, sl, tk + 16e-9)) - VTH[sl]["vth_mV"] * 1e-3) / L[sl]
                fd["vd_cl_minus_vth_lsb_16ns"] = round(dv, 3)
                fd["class"] = "tie" if abs(dv) <= 0.25 else ("near threshold" if abs(dv) <= 0.5 else "not a tie")
                row["first_difference"] = fd
                res["first_differences"].append(fd)
            res["frames"].append(row)
            res["decisions_total"] += ND
            res["decisions_equal"] += ND - len(dif)
            res["words_total"] += 1
            res["words_equal"] += int(not dif)
            res["valid_ok"] += int(von and voff)
    if frames == "ee":
        res["first_conversion"] = {sl: {"frame0_minus_frame1_lsb": res["frames"][0 + i]["code"] - res["frames"][2 + i]["code"],
                                        "codes": [res["frames"][0 + i]["code"], res["frames"][2 + i]["code"]],
                                        "ref_codes": [res["frames"][0 + i]["ref_code"], res["frames"][2 + i]["ref_code"]]}
                                   for i, sl in enumerate("ab")}
    tt = d["time"]
    m = tt > 0.6e-6
    avg = lambda n: float(np.trapz(-d[n][m], tt[m]) / (tt[m][-1] - tt[m][0]) * 1e3)
    if "i(vsarm)" in d:
        res["supply_mA"] = {"idd_total": avg("i(vdd)"), "idd_sar": avg("i(vsarm)"), "idd_analog": avg("i(vdd)") - avg("i(vsarm)"),
                            "idda": avg("i(vdda)"), "window": "0.6 us .. end, time average"}
    else:
        res["supply_mA"] = {"note": "not saved"}
    res["pass_bit_exact"] = res["decisions_equal"] == res["decisions_total"]
    res["all_differences_ties"] = all(x["class"] == "tie" for x in res["first_differences"])
    res["all_differences_within_0p5lsb_of_threshold"] = all(x["class"] != "not a tie" for x in res["first_differences"])
    res["max_abs_code_diff_lsb"] = max(abs(r["code_diff_lsb"]) for r in res["frames"])
    json.dump(res, open(out, "w"), indent=1)
    for r in res["frames"]:
        print(r["frame"], r["type"], r["slice"], r["word_bits"], r["ref_bits"], r["code"], r["ref_code"], r["valid_at_E15"],
              r.get("first_difference", ""))
    print("threshold", VTH)
    print("decisions %d/%d, words %d/%d, valid %d/%d; supply %s" % (res["decisions_equal"], res["decisions_total"], res["words_equal"],
          res["words_total"], res["valid_ok"], res["words_total"], {k: (round(v, 4) if isinstance(v, float) else v) for k, v in res["supply_mA"].items()}))
    if "first_conversion" in res:
        print("first conversion", res["first_conversion"])

elif cmd == "timing":
    rid = A[0]
    meta, d = b5run(rid)
    t = d["time"]
    vdd = float(np.max(d["v(clk)"]))

    def cross(x, lev):
        """all crossings of level lev: (time, +1 rising / -1 falling), linear interpolation"""
        s = x - lev
        i = np.nonzero((s[:-1] < 0) & (s[1:] >= 0) | (s[:-1] >= 0) & (s[1:] < 0))[0]
        tc = t[i] + (t[i + 1] - t[i]) * (-s[i]) / (s[i + 1] - s[i])
        return tc, np.where(s[i + 1] >= 0, 1, -1)

    ce, cd = cross(d["v(clk)"], 0.5 * vdd)
    edges = ce[cd > 0]
    res = {"tool": "sim/post/b5/b5_post.py timing", "run": rid, "vdd_V": vdd,
           "label": "simulated; delays from the rising clk edge (VDD/2 at the macro clk pin = deck clk node) to the output "
                    "transitions at the macro pins (B4: the same nodes as the ADC north pins; 50 fF load each). change = output "
                    "leaves its old level (10 % / 90 % of VDD), mid = VDD/2, settled = 90 % / 10 % of VDD",
           "limits": {"change_min_ns": 0.5, "settle_max_ns": 7.0}, "groups": {}}
    groups = {"adc_raw_a": ["v(adc_raw_a_%d)" % k for k in range(ND)], "adc_raw_b": ["v(adc_raw_b_%d)" % k for k in range(ND)],
              "adc_valid_a": ["v(adc_valid_a)"], "adc_valid_b": ["v(adc_valid_b)"]}
    allrows = []
    for g, names in groups.items():
        rows = []
        for n in names:
            x = d[n]
            tm, dm = cross(x, 0.5 * vdd)
            for tc, dr in zip(tm, dm):
                j = np.searchsorted(edges, tc) - 1
                if j < 0:
                    continue
                te = edges[j]
                # change: last time before tc at the old level band; settled: first time after tc at the new level band
                lo, hi = 0.1 * vdd, 0.9 * vdd
                i0 = np.searchsorted(t, tc)
                seg_b = slice(max(np.searchsorted(t, te), 0), i0)
                xb, tb = x[seg_b], t[seg_b]
                old = (xb <= lo) if dr > 0 else (xb >= hi)
                tch = float(tb[np.nonzero(old)[0][-1]]) if old.any() else float(te)
                xa, ta = x[i0:], t[i0:]
                new = (xa >= hi) if dr > 0 else (xa <= lo)
                tse = float(ta[np.nonzero(new)[0][0]]) if new.any() else float("nan")
                rows.append({"signal": n[2:-1], "edge_ns": round(te * 1e9, 3), "tick": int(round(te / T)), "dir": "rise" if dr > 0 else "fall",
                             "change_ns": round((tch - te) * 1e9, 4), "mid_ns": round((tc - te) * 1e9, 4), "settled_ns": round((tse - te) * 1e9, 4)})
        allrows += rows
        if rows:
            res["groups"][g] = {"transitions": len(rows),
                                "change_min_ns": min(r["change_ns"] for r in rows), "mid_min_ns": min(r["mid_ns"] for r in rows),
                                "mid_max_ns": max(r["mid_ns"] for r in rows), "settled_max_ns": max(r["settled_ns"] for r in rows)}
        else:
            res["groups"][g] = {"transitions": 0}
    # glitch check: more than one VDD/2 crossing of the same output in the same tick
    seen = {}
    for r in allrows:
        seen.setdefault((r["signal"], r["tick"]), []).append(r)
    res["glitches"] = [v for v in seen.values() if len(v) > 1]
    tr = [r for r in allrows]
    res["all"] = {"change_min_ns": min(r["change_ns"] for r in tr), "mid_min_ns": min(r["mid_ns"] for r in tr),
                  "mid_max_ns": max(r["mid_ns"] for r in tr), "settled_max_ns": max(r["settled_ns"] for r in tr),
                  "transitions": len(tr)}
    # per frame tick (E0 = adc_start edge of the frame): r1_ctrl samples valid at every edge and captures raw at E15
    # only (sar/README.md "Timing" note 2: raw changes at E1..E14 and E16; multicycle hold on raw)
    for r in allrows:
        r["frame_tick"] = (r["tick"] - 18) % 22
    rawr = [r for r in allrows if r["signal"].startswith("adc_raw")]
    valr = [r for r in allrows if r["signal"].startswith("adc_valid")]
    res["by_frame_tick"] = {str(k): len([r for r in allrows if r["frame_tick"] == k]) for k in range(22) if any(r["frame_tick"] == k for r in allrows)}
    res["raw_transitions_at_E15"] = len([r for r in rawr if r["frame_tick"] == 15])
    e14 = [r for r in rawr if r["frame_tick"] <= 14]
    e16 = [r for r in rawr if r["frame_tick"] >= 16]
    res["raw_capture_window_at_E15"] = {
        "setup_ns": round(T * 1e9 - max(r["settled_ns"] for r in e14), 3) if e14 else None,
        "hold_ns": round(T * 1e9 + min(r["change_ns"] for r in e16), 3) if e16 else None,
        "note": "setup = E15 - (latest settled raw transition at E1..E14); hold = (earliest raw change at E16) - E15"}
    res["valid"] = {"change_min_ns": min(r["change_ns"] for r in valr), "settled_max_ns": max(r["settled_ns"] for r in valr)} if valr else None
    res["raw"] = {"change_min_ns": min(r["change_ns"] for r in rawr), "settled_max_ns": max(r["settled_ns"] for r in rawr)} if rawr else None
    res["pass_change_ge_0p5ns"] = bool(res["all"]["change_min_ns"] >= 0.5)
    res["pass_settle_le_7ns"] = bool(res["all"]["settled_max_ns"] <= 7.0)
    res["transitions"] = allrows
    json.dump(res, open(out, "w"), indent=1)
    for g, x in res["groups"].items():
        print(g, x)
    print("valid", res["valid"], "raw", res["raw"], "raw at E15", res["raw_transitions_at_E15"], "capture window", res["raw_capture_window_at_E15"])
    print("all", res["all"], "glitches", len(res["glitches"]), "pass", res["pass_change_ge_0p5ns"], res["pass_settle_le_7ns"])

elif cmd == "r24":
    # post_post.py ref method: sim/r5/post_ref5.py executed with text patches (port vectors, static base correction as
    # post_post.py; loader for the b5 raw files: v(rawX) = word of adc_raw_X_k at VDD/2, v(vrefb) = v(vrefa),
    # v(vreflb) = v(vrefla)); in addition the error sample time in the tick (25 ns as defined) and the capacitor-step
    # sample time (1.2 ns as defined) are varied. Outputs: the metric as defined, the corrected value of README B4
    # (25 ns where both runs decide the same, 16 ns at the first differing decision), and both again with the steps
    # sampled at 4 ns (the gate-level SAR switches the CDAC 0.7-1.0 ns after the edge at tt, so at 1.2 ns a step may
    # not be complete).
    rb, ri, pv, plv, sb = A[:5]
    R5 = os.path.join(BLOCK, "sim", "r5")
    Ma, La, Mb, Lb = [float(x) for x in sb.split(",")]
    videal = 0.5 * (Ma + Mb)
    cache = {}

    def B5LOAD(rid):
        if rid not in cache:
            _, dd = b5run(rid)
            vth = 0.5 * float(np.max(dd["v(clk)"]))
            for sl in "ab":
                w = np.zeros_like(dd["time"])
                for k in range(ND):
                    w += (dd["v(adc_raw_%s_%d)" % (sl, k)] > vth) * float(1 << k)
                dd["v(raw%s)" % sl] = w
            dd["v(vrefb)"], dd["v(vreflb)"] = dd["v(vrefa)"], dd["v(vrefla)"]
            cache[rid] = dd
        return cache[rid]

    base = open(os.path.join(R5, "post_ref5.py")).read()
    rep = [('seg = json.load(open(os.path.join(HERE, "..", "results", "r5", rid + "_segments.json")))', 'seg = {"segments": [1]}'),
           ('d, _ = read(os.path.join(root, "r1_adc", rid, "codes.raw"))', 'd = B5LOAD(rid)'),
           ('dM, dL = v1m * VIDEAL - VIDEAL, v1l * VIDEAL - VIDEAL',
            'dM, dL = v1m * VIDEAL - {"a": %r, "b": %r}[sl], v1l * VIDEAL - {"a": %r, "b": %r}[sl]' % (Ma, Mb, La, Lb))]
    for o, n in rep:
        assert base.count(o) == 1, o
        base = base.replace(o, n)
    va, vb = pv.split(","); vla, vlb = plv.split(",")
    for k, v in {'"v(vref%s)" % sl': '{"a": "%s", "b": "%s"}[sl]' % (va, vb),
                 '"v(vrefl%s)" % sl': '{"a": "%s", "b": "%s"}[sl]' % (vla, vlb)}.items():
        base = base.replace("db, " + k, "db, " + v).replace("db[" + k, "db[" + v)
    o_tin, o_stp = "tm = t0 + np.arange(ND) * T + 25e-9", "np.arange(ND) * T + 1.2e-9"
    assert base.count(o_tin) == 1 and base.count(o_stp) == 1
    TIN = [4, 10, 16, 19, 22, 25]
    per = {}
    import io, contextlib
    for tstep in (1.2, 4.0):
        for tin in TIN:
            src = base.replace(o_tin, "tm = t0 + np.arange(ND) * T + %de-9" % tin).replace(o_stp, "np.arange(ND) * T + %ge-9" % tstep)
            tmp = out + ".tmp.json"
            sys.argv = ["post_ref5.py", rb, ri, tmp, str(videal)]
            g = {"__file__": os.path.join(R5, "post_ref5.py"), "__name__": "__main__", "B5LOAD": B5LOAD}
            with contextlib.redirect_stdout(io.StringIO()):
                exec(compile(src, "post_ref5.py (b5)", "exec"), g)
            per[(tstep, tin)] = json.load(open(tmp))
            os.remove(tmp)
    res = {"tool": "sim/post/b5/b5_post.py r24", "run_buffer": rb, "run_base": ri, "videal_V": videal,
           "static_base_correction_V": {"a": {"msb": Ma, "lsb": La}, "b": {"msb": Mb, "lsb": Lb}}, "port_vectors": [pv, plv],
           "label": "simulated; R2-4 metric of sim/post/post_post.py ref (sim/r5/post_ref5.py) on closed-loop runs with the "
                    "gate-level r1_adc_sar; limit 0.25 LSB", "variants": {}}
    for tstep in (1.2, 4.0):
        D = per[(tstep, 25)]
        v = {"metric_as_defined_lsb": D["max_abs_input_error_mid_eval_lsb"], "slices": {}}
        for sl in "ab":
            S = D["slices"][sl]
            same, first = [], []
            for r in S["slots"][1:]:
                s = r["slot"]
                dif = r["bits_differ_at"]
                fdd = dif[0] if dif else None
                for i in range(9):
                    j = 5 + i
                    x25 = r["input_error_mid_eval_lsb_dec5_13"][i]
                    if x25 is None:
                        continue
                    if j == fdd:
                        first.append(abs(per[(tstep, 16)]["slices"][sl]["slots"][s]["input_error_mid_eval_lsb_dec5_13"][i]))
                    else:
                        same.append(abs(x25))
            v["slices"][sl] = {"metric_as_defined_lsb": S["max_abs_input_error_mid_eval_lsb"],
                               "same_decision_25ns_lsb": max(same) if same else None,
                               "first_differing_decision_16ns_lsb": max(first) if first else None,
                               "corrected_lsb": max([x for x in (max(same) if same else None, max(first) if first else None) if x is not None]),
                               "per_decision_25ns_lsb": S["max_abs_error_vs_decision_lsb"],
                               "after_gain_fit_lsb": S["max_abs_error_after_gain_fit_lsb"],
                               "code_diff_max_lsb": S["max_abs_code_diff_lsb"],
                               "per_tin_max_lsb": {str(tin): per[(tstep, tin)]["slices"][sl]["max_abs_input_error_mid_eval_lsb"] for tin in TIN}}
        v["corrected_lsb"] = max(v["slices"][x]["corrected_lsb"] for x in "ab")
        v["pass_0p25_as_defined"] = bool(v["metric_as_defined_lsb"] <= 0.25)
        res["variants"]["steps_at_%gns" % tstep] = v
    res["metric_as_defined_lsb"] = res["variants"]["steps_at_1.2ns"]["metric_as_defined_lsb"]
    res["corrected_lsb"] = res["variants"]["steps_at_1.2ns"]["corrected_lsb"]
    json.dump(res, open(out, "w"), indent=1)
    for k, v in res["variants"].items():
        print(k, "as defined %.3f, corrected %.3f" % (v["metric_as_defined_lsb"], v["corrected_lsb"]),
              {sl: {kk: vv for kk, vv in v["slices"][sl].items() if kk in ("metric_as_defined_lsb", "same_decision_25ns_lsb", "first_differing_decision_16ns_lsb")} for sl in "ab"})
else:
    sys.exit(__doc__)
