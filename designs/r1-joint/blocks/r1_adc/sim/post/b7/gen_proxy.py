#!/usr/bin/env python3
"""T2m (layout B7, 2026-10-27): behavioural SAR with the gate-level output timing ("D23 proxy") for the R2-4 decks.

Why: the closed-loop decks with the gate-level r1_adc_sar run at 0.024 us per wall minute (tt); the 10-slot R2-4 deck
needs 5.4 h per run and 4 runs (tt / ss, buffer / base). The behavioural decks run about 8x faster. D23 asks for the
real CDAC switch and the real comparator strobe, so the behavioural SAR outputs get the gate-level timing:

  r1_sar5_logic_d23 = r1_sar5_logic (unchanged, schematic/r1_adc_r5.spice) whose 60 outputs (8 comparator clocks,
  52 CDAC lines) pass through adc_bridge (20 ps) -> d_buffer (rise / fall delay per output) -> dac_bridge (80 ps
  ramp, out_high = corner VDD). The raw words are not delayed.
  Delays (from sim/post/b7/results/gl_timing_b6.json, medians of the gate-level runs, ns after the clk edge):
    comparator clocks: target = GL (clock edge - mclk edge) at the same corner; the behavioural path mclk -> clock
      already has 0.09 ns (bridge 20 ps + AND 30 ps + dac 40 ps to 50 %) and the wrapper adds 0.06 ns + the delay.
    CDAC lines: target = GL line 50 % after E(k+1) per line (median; overall median if the line never switched in the
      GL run); the behavioural line reaches 50 % 0.435 (P) / 0.405 (N) ns before the edge (strobe 0.6 ns before E, dff 80 ps, AND 30 ps
      for N lines, dac 40 ps); the wrapper adds 0.06 ns + the delay.
  The decision capture (stb, 0.6 ns before E(k+1)) is not moved: the proxy comparator clocks fall 0.84 (tt) / 1.28
  (ss) ns after the edge, so the comparator still evaluates at the capture.
Writes sim/post/b7/r1_adc5_post_d23_<corner>.spice with r1_sar5_logic_d23 and the core r1_adc5_core_lay_d23 (copy of
sim/post/r1_adc5_post.spice r1_adc5_core_lay with XSAR -> r1_sar5_logic_d23).
usage: gen_proxy.py <corner tag> <GL run id for the timing> <vdd> [timing json, default results/gl_timing_b6.json]
(T2p, 2026-10-30: optional 4th argument, used for ff with sim/post/b10/results/gl_timing_b7_ffm40.json.)"""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
POST = os.path.dirname(HERE)
BLOCK = os.path.dirname(os.path.dirname(POST))
tag, rid, vdd = sys.argv[1], sys.argv[2], float(sys.argv[3])
TJ = sys.argv[4] if len(sys.argv) > 4 else os.path.join(HERE, "results", "gl_timing_b6.json")
G = json.load(open(TJ))["runs"][rid]
m = lambda k: G[k]["median"]
BEH_CLK = 0.09          # mclk -> behavioural clock output (50 %)
WRAP = 0.06             # adc bridge 20 ps + dac 40 ps (50 % of the 80 ps ramp)
BEH_LINE = {"cp": -0.435, "cn": -0.405}   # behavioural line 50 % relative to E(k+1) (cn: one AND more)
clk_on = {"X": m("clkX_on") - m("mclk_rise"), "Xb": m("clkXb_on") - m("mclk_rise")}
clk_off = {"X": m("clkX_off") - m("mclk_fall"), "Xb": m("clkXb_off") - m("mclk_fall")}
dl = {}
for sl in "ab":
    for pfx, kind in (("clk", "X"), ("clkn", "X")):
        n = pfx + sl
        dl[n] = (max(0.0, clk_on[kind] - BEH_CLK - WRAP), max(0.0, clk_off[kind] - BEH_CLK - WRAP))   # rise = enter evaluate
        nb = pfx + sl + "b"
        dl[nb] = (max(0.0, clk_off["Xb"] - BEH_CLK - WRAP), max(0.0, clk_on["Xb"] - BEH_CLK - WRAP))  # complement: rise = leave
    for pn in ("cp", "cn"):
        for b in range(13):
            k = "line_%s_%s%d" % (sl, pn, b)
            t = G[k]["median"] if k in G else m("line_all")
            d = max(0.0, t - BEH_LINE[pn] - WRAP)
            dl["%s%s%d" % (pn, sl, b)] = (d, d)
src = open(os.path.join(BLOCK, "schematic", "r1_adc_r5.spice")).read()
hdr = re.search(r"^\.subckt r1_sar5_logic ([^\n]*)", src, re.M).group(1).split()
outs = ["clka", "clkab", "clkb", "clkbb", "clkna", "clknab", "clknb", "clknbb"] + \
       ["%s%s%d" % (pn, sl, b) for sl in "ab" for pn in ("cp", "cn") for b in range(13)]
assert all(o in hdr for o in outs)
L = ["* %s -- written by sim/post/b7/gen_proxy.py (T2m); do not edit. Corner %s, timing from GL run %s, VDD %.3g V."
     % ("r1_adc5_post_d23_%s.spice" % tag, tag, rid, vdd),
     "* Behavioural SAR r1_sar5_logic with the gate-level output timing (delays in ns: rise / fall):",
     "* " + ", ".join("%s %.3f/%.3f" % (o, dl[o][0], dl[o][1]) for o in outs[:8]),
     "* CDAC lines: " + ", ".join("%s %.3f" % (o, dl[o][0]) for o in outs[8:]),
     ".subckt r1_sar5_logic_d23 " + " ".join(hdr),
     ".model r1_d23_adcb adc_bridge(in_low=%.4g in_high=%.4g rise_delay=20p fall_delay=20p)" % (vdd / 2, vdd / 2),
     ".model r1_d23_dacb dac_bridge(out_low=0 out_high=%.4g out_undef=%.4g input_load=1e-15 t_rise=80p t_fall=80p)" % (vdd, vdd / 2)]
for o in outs:
    L.append(".model r1_d23_dl_%s d_buffer(rise_delay=%.4fn fall_delay=%.4fn input_load=1e-15)" % (o, max(dl[o][0], 1e-3), max(dl[o][1], 1e-3)))
L.append("XS " + " ".join(("i_" + p) if p in outs else p for p in hdr) + " r1_sar5_logic")
for o in outs:
    L += ["AI_%s [i_%s] [di_%s] r1_d23_adcb" % (o, o, o), "AD_%s di_%s dd_%s r1_d23_dl_%s" % (o, o, o, o),
          "AO_%s [dd_%s] [%s] r1_d23_dacb" % (o, o, o)]
L.append(".ends r1_sar5_logic_d23")
core = open(os.path.join(POST, "r1_adc5_post.spice")).read()
mm = re.search(r"^\.subckt r1_adc5_core_lay .*?^\.ends r1_adc5_core_lay", core, re.M | re.S).group(0)
mm = mm.replace(".subckt r1_adc5_core_lay ", ".subckt r1_adc5_core_lay_d23 ").replace(".ends r1_adc5_core_lay", ".ends r1_adc5_core_lay_d23")
assert mm.count(" r1_sar5_logic\n") == 1
mm = mm.replace(" r1_sar5_logic\n", " r1_sar5_logic_d23\n")
L += ["* core: copy of sim/post/r1_adc5_post.spice r1_adc5_core_lay with XSAR -> r1_sar5_logic_d23", mm]
fn = os.path.join(HERE, "r1_adc5_post_d23_%s.spice" % tag)
open(fn, "w").write("\n".join(L) + "\n")
json.dump({"corner": tag, "gl_run": rid, "vdd": vdd, "delays_ns_rise_fall": dl}, open(os.path.join(HERE, "results", "proxy_delays_%s.json" % tag), "w"), indent=1)
print("wrote", fn); print({k: dl[k] for k in outs[:8]}); print("lines", min(dl[o][0] for o in outs[8:]), max(dl[o][0] for o in outs[8:]))
