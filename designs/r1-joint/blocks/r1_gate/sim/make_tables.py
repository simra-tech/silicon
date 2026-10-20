#!/usr/bin/env python3
"""Markdown tables for the r1_gate README from runs/<tag>/*/metrics.json (host python 3.6). Usage: make_tables.py <tag>"""
import json, sys, glob, os
tag = sys.argv[1]
R = {}
for f in glob.glob("runs/%s/*/metrics.json" % tag):
    m = json.load(open(f))
    R[m["case"]] = m
CN = {"tt": "tt 27 C 3.3 V / 1.2 V", "ss": "ss 125 C 3.0 V / 1.08 V", "ff": "ff -40 C 3.6 V / 1.32 V"}
def get(case):
    m = R.get(case)
    return m["metrics"] if m and m.get("completed") and "metrics" in m else None
def n(x, f="%.0f", s=1e9):
    return "n/a" if x is None else f % (x * s)
out = []
out.append("### (a) Timing, ideal supply (0.5 ohm + 1 nF), pad node and FET-gate node (10 ohm + C)\n")
out.append("Single-channel edges. Rise: `c` rises alone. Fall: `b` falls alone. Delay = pwm 50 % to node 50 % (half of IOVDD). Times in ns.\n")
out.append("| Path | Corner | Load | pwm->`gc` rise | pwm->pad rise | pad 10-90 % | FET gate 10-90 % | pwm->`gc` fall | pwm->pad fall | pad 90-10 % | FET gate 90-10 % |")
out.append("| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
for ld in ("5n", "1n"):
    for c in ("tt", "ss", "ff"):
        for t in ("hv", "lv"):
            M = get("%s_%s_%s_pkg0_nodcn" % (t, c, ld))
            if not M:
                out.append("| %s | %s | %s | not run or failed | | | | | | | |" % (t.upper(), CN[c], ld)); continue
            r = M["events"]["c_rise_single"]["c"]; f = M["events"]["b_fall_single"]["b"]
            out.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
                t.upper(), CN[c], ld.replace("n", " nF"), n(r["d50_gc"], "%.2f"), n(r["d50_pad"]), n(r["slew_pad"]), n(r["slew_gf"]),
                n(f["d50_gc"], "%.2f"), n(f["d50_pad"]), n(f["slew_pad"]), n(f["slew_gf"])))
out.append("\n### (b) Skew and edge overlap (50 ns ideal dead time between a/c and b)\n")
out.append("Gap = time when the turn-on edge crosses the level minus time when the turn-off edge crosses the level. Positive: no overlap. Negative: both nodes are above the level together. Level 1 V stands for a FET threshold, level IOVDD/2 is the logic mid-point. Same edge pairs at the pad node and at the FET-gate node (after 10 ohm + C). Times in ns.\n")
out.append("| Path | Corner | Load | gap b off -> a on, pad, IOVDD/2 | pad, 1 V | FET gate, IOVDD/2 | FET gate, 1 V | gap a off -> b on, pad, IOVDD/2 | pad, 1 V | FET gate, IOVDD/2 | FET gate, 1 V | spread of 3 pad delays, 3 gates rising together | falling together | fall - rise delay (single edges) |")
out.append("| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
for ld in ("5n", "1n"):
    for c in ("tt", "ss", "ff"):
        for t in ("hv", "lv"):
            M = get("%s_%s_%s_pkg0_nodcn" % (t, c, ld))
            if not M: continue
            o, s = M["overlap"], M["skew"]
            def g(k): return "n/a" if o.get(k) is None else "%.1f" % o[k]
            fr = s["single_fall_b_d50_pad_ns"] - s["single_rise_c_d50_pad_ns"]
            out.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %.4f | %.4f | %.1f |" % (t.upper(), CN[c], ld.replace("n", " nF"),
                g("b_off_then_a_on_pad_half_gap_ns"), g("b_off_then_a_on_pad_1v_gap_ns"), g("b_off_then_a_on_gf_half_gap_ns"), g("b_off_then_a_on_gf_1v_gap_ns"),
                g("a_off_then_b_on_pad_half_gap_ns"), g("a_off_then_b_on_pad_1v_gap_ns"), g("a_off_then_b_on_gf_half_gap_ns"), g("a_off_then_b_on_gf_1v_gap_ns"),
                s["sso_rise1_pad_spread_ns"], s["sso_fall_pad_spread_ns"], fr))
out.append("\n### (b-i) Pad output stage cross-conduction (current from the opposite rail during an edge, baseline removed, first 200 ns)\n")
out.append("Fall edge: IOVDD current (the load discharges to ground through IOVSS, so IOVDD current is cross-conduction and shifter current). Rise edge: IOVSS current. Single-channel edges.\n")
out.append("| Corner | Load | fall edge: IOVDD peak (mA) | fall edge: IOVDD charge (pC) | rise edge: IOVSS peak (mA) | rise edge: IOVSS charge (pC) |")
out.append("| --- | --- | ---: | ---: | ---: | ---: |")
for ld, pk in (("1p", 0), ("1n", 0), ("5n", 0)):
    for c in ("tt", "ss", "ff"):
        case = ("lv_%s_%s_pkg0_nodcn" % (c, ld))
        M = get(case)
        if not M: continue
        f = M["supply"]["b_fall_single"]; r = M["supply"]["c_rise_single"]
        out.append("| %s | %s | %.2f | %.1f | %.3f | %.1f |" % (CN[c], ld.replace("p", " pF").replace("n", " nF"), f["cw_iovdd_peak_mA"], f["cw_iovdd_Q_nC"] * 1e3, r["cw_iovss_peak_mA"], r["cw_iovss_Q_nC"] * 1e3))
out.append("\n### (c) Three gates switching together into 5 nF, package model (1 nH + 0.1 ohm IOVDD pin, 2 IOVSS pins in parallel at 0.5 nH + 0.05 ohm)\n")
out.append("Rising: IOVDD current peak and mean over the 10-90 % window of the slowest FET gate. Falling: IOVSS return current. Bounce = deviation of the on-chip IOVDD / IOVSS node from the ideal rail.\n")
out.append("| Path | Corner | On-chip IOVDD-IOVSS decap | rise: IOVDD peak (mA) | rise: mean (mA) | rise: charge (nC) | IOVDD droop (mV) | fall: IOVSS peak (mA) | IOVSS bounce, max (mV) | core VDD min (V) |")
out.append("| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
for cd in ("1n", "100p"):
    for c in ("tt", "ss", "ff"):
        for t in ("hv", "lv"):
            M = get("%s_%s_5n_pkg1_cd%s_nodcn" % (t, c, cd))
            if not M: continue
            r = M["supply"]["sso_rise1"]; f = M["supply"]["sso_fall"]
            out.append("| %s | %s | %s | %.1f | %.1f | %.1f | %.1f | %.1f | %.1f | %.4f |" % (t.upper(), CN[c], cd.replace("p", " pF").replace("n", " nF"),
               r["iovdd_peak_mA"], r["iovdd_avg_mA"], r["iovdd_Q_nC"], r["iovdd_droop_mV"], f["iovss_peak_mA"], f["iovss_node_max_V"] * 1e3, min(r["core_node_min_V"], f["core_node_min_V"])))
out.append("\n### (d) Fault path: `gate_en` falls with all three `pwm` high (ideal supply)\n")
out.append("Time from `gate_en` 50 % to the node below 0.33 V (10 % of 3.3 V) and below 1 V; worst of three channels. Requirement: pad below 0.33 V within 200 ns.\n")
out.append("| Path | Corner | Load | pad < 0.33 V (ns) | pad < 1 V (ns) | FET gate < 0.33 V (ns) | pad voltage at 200 ns (V) | Requirement 200 ns |")
out.append("| --- | --- | --- | ---: | ---: | ---: | ---: | --- |")
for ld in ("5n", "1n"):
    for c in ("tt", "ss", "ff"):
        for t in ("hv", "lv"):
            M = get("%s_%s_%s_pkg0_nodcn" % (t, c, ld))
            if not M: continue
            fa = M["fault"]
            w = lambda k: max(fa["%s_%s" % (ch, k)] for ch in "abc")
            ok = w("pad_below_033_ns") < 200
            out.append("| %s | %s | %s | %.0f | %.0f | %.0f | %.2f | %s |" % (t.upper(), CN[c], ld.replace("n", " nF"), w("pad_below_033_ns"), w("pad_below_1v_ns"), w("gf_below_033_ns"),
                       max(fa["%s_pad_V_at_200ns" % ch] for ch in "abc"), "passed" if ok else "failed"))
out.append("\n### (e) Static and per-edge supply current (ideal supply, single-channel edges)\n")
out.append("Static values are the mean over 90 ns before an edge with all three channels low or all high (three pads, three paths, includes the pad). Charge per edge: `c` rises alone (IOVDD) and `b` falls alone; core charge is taken from the 1.2 V supply.\n")
out.append("| Path | Corner | Load | static IOVDD, all low / all high (nA) | static core VDD, all low / all high (nA) | IOVDD charge per rising edge (nC) | core VDD charge, rising edge / falling edge (pC) |")
out.append("| --- | --- | --- | --- | --- | ---: | --- |")
for ld in ("5n", "1n"):
    for c in ("tt", "ss", "ff"):
        for t in ("hv", "lv"):
            M = get("%s_%s_%s_pkg0_nodcn" % (t, c, ld))
            if not M: continue
            i = M["idle_mA"]; r = M["supply"]["c_rise_single"]; f = M["supply"]["b_fall_single"]
            if ld == "5n":
                st = ("not static (5 nF still settles in the window)", "%.2f / %.2f" % (i["all_low_core"] * 1e6, i["all_high_core"] * 1e6))
            else:
                st = ("%.2f / %.2f" % (i["all_low_iovdd"] * 1e6, i["all_high_iovdd"] * 1e6), "%.2f / %.2f" % (i["all_low_core"] * 1e6, i["all_high_core"] * 1e6))
            out.append("| %s | %s | %s | %s | %s | %.2f | %.2f / %.2f |" % (t.upper(), CN[c], ld.replace("n", " nF"), st[0], st[1], r["iovdd_Q_nC"], r["core_Q_nC"] * 1e3, f["core_Q_nC"] * 1e3))
print("\n".join(out))
