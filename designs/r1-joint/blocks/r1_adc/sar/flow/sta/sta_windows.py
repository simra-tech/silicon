#!/usr/bin/env python3
"""T2j: window table of r1_adc_sar from the sta_windows.tcl logs of the three corners.
usage: sta_windows.py <out.json> <out.md> fast=<log> typ=<log> slow=<log>
Arrival values are path delays from the launching edge (the mclk edge time of sta_windows.sdc is subtracted).
One-shot reset width per corner (r1_adc README revision 4): fast 0.91, typ 1.38, slow 2.27 ns; mclk falls
0.04 to 0.05 ns after the clk edge (decks); the comparator outputs answer the reset 0.18-0.23 ns after their
clock pin (decks; the lower bound is used). The sg13g2_dlhq_1 hold time is negative at all corners (-0.001 ns at
worst, fast), so it is taken as 0."""
import json, re, sys

W = {"fast": 0.91, "typ": 1.38, "slow": 2.27}
MCLK_EDGE = {"^": 1.0, "v": 12.0}
MCLK_FALL_AFTER_CLK = 0.04
CMP_RESET_RESPONSE = 0.18   # lower bound of the decks (0.18-0.23 ns); latch hold <= 0 at all corners (liberty)


def parse_cdac(path):
    """CDAC lines 11..0 from the flag flip-flops: {port: {max: t, min: t}} (data arrival of report_checks)"""
    out, cur = {}, None
    for l in open(path):
        m = re.match(r"CDAC (\S+) (max|min)", l)
        if m:
            cur = (m.group(1), m.group(2)); continue
        m = re.match(r"\s*(-?[\d.]+)\s+data arrival time", l)
        if m and cur:
            out.setdefault(cur[0], {})[cur[1]] = float(m.group(1)); cur = None
    return out


def gating(path):
    """worst setup and hold slack of the 'gated clock' path group in a signoff_sta.tcl log"""
    if not path:
        return (None, None)
    sl, on = [], False
    for l in open(path):
        if l.startswith("GATING_BEGIN"): on = True
        elif l.startswith("GATING_END"): on = False
        elif on:
            m = re.match(r"\s*(-?[\d.]+)\s+slack", l)
            if m: sl.append(float(m.group(1)))
    return (sl[0] if sl else None, sl[1] if len(sl) > 1 else None)


def parse(path):
    arr, cur = {}, None
    for l in open(path):
        if l.startswith("CDAC ") or l.startswith("BUSY_CELL"):
            cur = None
            continue
        if l.startswith("ARR "):
            cur = l.split()[1]; arr[cur] = {}
            continue
        m = re.match(r"\((\w+) ([\^v])\) r ([\d.\-]+|---):([\d.\-]+|---) f ([\d.\-]+|---):([\d.\-]+|---)", l.strip())
        if m and cur:
            ck, e = m.group(1), m.group(2)
            v = [None if x == "---" else float(x) for x in m.group(3, 4, 5, 6)]
            off = MCLK_EDGE[e] if ck == "mclk" else 0.0
            v = [None if x is None else round(x - off, 4) for x in v]
            arr[cur]["%s%s" % (ck, e)] = {"rmin": v[0], "rmax": v[1], "fmin": v[2], "fmax": v[3]}
    return arr


def mm(arr, pins, key, which="any"):
    lo, hi = [], []
    for p in pins:
        a = arr.get(p, {}).get(key)
        if not a:
            continue
        for t in (("r", "f") if which == "any" else (which,)):
            if a[t + "min"] is not None:
                lo.append(a[t + "min"]); hi.append(a[t + "max"])
    return (min(lo), max(hi)) if lo else (None, None)


out, md = {}, []
logs = dict(a.split("=", 1) for a in sys.argv[3:])
cdac = ["%s[%d]" % (b, k) for b in ("cpa", "cna", "cpb", "cnb") for k in range(13)]
ctrl = ["adc_valid_a", "adc_valid_b"] + ["adc_raw_%s[%d]" % (s, k) for s in "ab" for k in range(14)]
rows = []
for c in ("fast", "typ", "slow"):
    if c not in logs:
        continue
    a = parse(logs[c]); w = W[c]; r = {}
    cd = parse_cdac(logs[c])
    l12 = mm(a, ["%s[12]" % b for b in ("cpa", "cna", "cpb", "cnb")], "clk^")
    lo = [v["min"] for v in cd.values() if "min" in v] + [l12[0]]
    hi = [v["max"] for v in cd.values() if "max" in v] + [l12[1]]
    r["cdac_lines_measured"] = len(cd) + 4
    r["cdac_clk_to_pin_ns"] = (round(min(lo), 4), round(max(hi), 4))
    r["cdac_limit_ns"] = round(w - 0.2, 3)
    r["cdac_clear_ns"] = mm(a, [x for x in cdac if not x.endswith("[12]")], "clk^")[1]
    r["cdac_clear_pass"] = r["cdac_clear_ns"] < 23.81
    r["cdac_pass"] = r["cdac_clk_to_pin_ns"][1] <= r["cdac_limit_ns"]
    r["valid_clk_to_pin_ns"] = mm(a, ["adc_valid_a", "adc_valid_b"], "clk^")
    r["raw_clk_to_pin_ns"] = mm(a, ctrl[2:], "clk^")
    r["ctrl_out_pass"] = r["valid_clk_to_pin_ns"][0] >= 0.5 and max(r["valid_clk_to_pin_ns"][1], r["raw_clk_to_pin_ns"][1]) <= 7.0
    ck = {}
    for p in ("clka", "clkab", "clkna", "clknab", "clkb", "clkbb", "clknb", "clknbb"):
        ck[p] = {"mclk_rise": mm(a, [p], "mclk^"), "mclk_fall": mm(a, [p], "mclk v".replace(" ", "")),
                 "win_close_clk": mm(a, [p], "clk^")}
    r["cmpclk"] = ck
    allr = [v["mclk_rise"] for v in ck.values() if v["mclk_rise"][0] is not None]
    allf = [v["mclk_fall"] for v in ck.values() if v["mclk_fall"][0] is not None]
    r["mclk_rise_to_cmpclk_ns"] = (min(x[0] for x in allr), max(x[1] for x in allr))
    r["mclk_fall_to_cmpclk_ns"] = (min(x[0] for x in allf), max(x[1] for x in allf))
    sk = []
    for t, cpl in (("clka", "clkab"), ("clkna", "clknab"), ("clkb", "clkbb"), ("clknb", "clknbb")):
        for e, te, ce in (("mclk^", "r", "f"), ("mclkv", "f", "r")):
            at, ac = a.get(t, {}).get(e), a.get(cpl, {}).get(e)
            if at and ac and at[te + "max"] is not None and ac[ce + "max"] is not None:
                sk.append(abs(at[te + "max"] - ac[ce + "max"])); sk.append(abs(at[te + "min"] - ac[ce + "min"]))
    r["true_complement_skew_max_ns"] = round(max(sk), 4)
    # window close: the clock-gating checks of the sign-off STA at the gates themselves (mclk rise per corner)
    gs = gating(logs.get(c + "_so"))
    r["gating_setup_slack_ns"], r["gating_hold_slack_ns"] = gs
    r["win_close_pass"] = gs[0] is not None and gs[0] >= 0 and gs[1] is not None and gs[1] >= 0
    # decision latches: the gate must close before the comparator output answers its reset
    g = {}
    for lat, pin in (("u_lat_pa", "clka"), ("u_lat_na", "clkna"), ("u_lat_pb", "clkb"), ("u_lat_nb", "clknb")):
        gf = mm(a, [lat + "/GATE"], "mclkv", "f")
        pf = mm(a, [pin], "mclkv", "f")
        g[lat] = {"gate_fall_max_ns": gf[1], "pin_fall_min_ns": pf[0],
                  "margin_ns": round(pf[0] + CMP_RESET_RESPONSE - gf[1], 4) if gf[1] is not None and pf[0] is not None else None}
    r["latch_close"] = g
    r["latch_pass"] = all(v["margin_ns"] is not None and v["margin_ns"] > 0 for v in g.values())
    trk = {p: mm(a, [p], "vctl^") for p in ("trka0", "trka1", "trkb0", "trkb1")}
    trkf = {p: mm(a, [p], "vctl^", "f") for p in ("trka0", "trka1", "trkb0", "trkb1")}
    r["ctrl_to_trk_ns"] = trk
    r["ctrl_to_trk_fall_ns"] = trkf
    # sample-instant skew A / B: same corner, same transition (trk falls), max - max and min - min
    r["trk_ab_skew_ns"] = round(max(abs(trkf["trka0"][1] - trkf["trkb0"][1]), abs(trkf["trka0"][0] - trkf["trkb0"][0]),
                                    abs(trkf["trka1"][1] - trkf["trkb1"][1]), abs(trkf["trka1"][0] - trkf["trkb1"][0])), 4)
    out[c] = r
    rows.append("| %s | %.3f .. %.3f (limit %.2f) %s | %.3f .. %.3f / %.3f .. %.3f %s | %.3f .. %.3f / %.3f .. %.3f | %.3f | setup %.3f / hold %.3f %s | %s %s | %.3f .. %.3f, A/B %.3f |" % (
        c, *r["cdac_clk_to_pin_ns"], r["cdac_limit_ns"], "pass" if r["cdac_pass"] else "FAIL",
        *r["valid_clk_to_pin_ns"], *r["raw_clk_to_pin_ns"], "pass" if r["ctrl_out_pass"] else "FAIL",
        *r["mclk_rise_to_cmpclk_ns"], *r["mclk_fall_to_cmpclk_ns"], r["true_complement_skew_max_ns"],
        gs[0], gs[1], "pass" if r["win_close_pass"] else "FAIL",
        min(v["margin_ns"] for v in g.values()), "pass" if r["latch_pass"] else "FAIL",
        min(v[0] for v in trk.values()), max(v[1] for v in trk.values()), r["trk_ab_skew_ns"]))
json.dump(out, open(sys.argv[1], "w"), indent=1)
md = ["| Corner | clk -> CDAC lines (ns) | clk -> valid / raw (ns), need valid min >= 0.5, max <= 7.0 | mclk rise / fall -> comparator clocks (ns) | true / complement skew (ns) | window gates: clock-gating check slack (ns) | latch close margin (ns) | ctrl request -> trk (ns) |",
      "| --- | --- | --- | --- | --- | --- | --- | --- |"] + rows
open(sys.argv[2], "w").write("\n".join(md) + "\n")
print("\n".join(md))
