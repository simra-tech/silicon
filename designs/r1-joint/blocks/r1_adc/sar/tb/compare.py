#!/usr/bin/env python3
"""T2j: compare r1_adc_sar (RTL or gate level, log of tb_sar_vec.v) with the behavioural r1_sar5_logic (SAR-only
ngspice run on the same vectors, sar/sim/tb_beh_sar.cir) and write a JSON summary.

Compared at every clk30 tick n (edge E_n = n T) at E_n + 10 ns and E_n + 20 ns (the CDAC lines and the comparator
clocks have settled in both models; the models differ inside the first 2 ns after an edge by design, README):
  cdac   26 lines per slice (cp, cn)                                  must be identical at every sample
  cmpclk clka clkab clkna clknab clkb clkbb clknb clknbb               identical at every sample
  trk    trka0 trka1 trkb0 trkb1                                      identical except the listed protocol ticks
  decisions and valid: per frame and slice, the 14 decisions (behavioural ra/rb after lat; RTL raw while valid) and
  the valid tick (RTL valid high at E14 + 5 ns  <->  behavioural lat in [E14, E14 + 2 ns])
Also: comparator output edges inside [E - 0.6 ns, E + 0.2 ns] (between the behavioural strobe and the RTL latch close)
for the comparator used at that decision; such an edge could make the two models differ on analog vectors.
usage: compare.py <case> <beh run id> <dut log> <out json> [--label rtl|gl-slow ...]
"""
import argparse, json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SAR = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(os.path.dirname(SAR), "sim"))
import rawread  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("case")
ap.add_argument("beh")
ap.add_argument("log")
ap.add_argument("out")
ap.add_argument("--label", default="rtl")
a = ap.parse_args()
info = json.load(open(os.path.join(HERE, "vec", a.case + ".json")))
T = info["T_s"]
raw = os.path.join(os.environ["G1_RESULTS_ROOT"], "r1_adc_sar", a.beh, "sar.raw")
names = ["clka", "clkab", "clkna", "clknab", "clkb", "clkbb", "clknb", "clknbb", "trka0", "trka1", "trkb0", "trkb1",
         "lata", "latb"]
cd = ["c%s%s%d" % (p, s, k) for s in "ab" for p in "pn" for k in range(13)]
rr = ["xsar.r%s%d" % (s, k) for s in "ab" for k in range(14)]
d, var = rawread.read(raw, ["time"] + ["v(%s)" % n for n in names + cd + rr])
tb = np.abs(d["time"])


def beh(n, tq):
    return int(np.interp(tq, tb, d["v(%s)" % n]) > 0.6)


# DUT log: "t_ps bits ctrl"; bit order as tb_sar_vec.v obus
order = ["va", "vb"] + ["raw_a%d" % k for k in range(13, -1, -1)] + ["raw_b%d" % k for k in range(13, -1, -1)] + \
        ["clka", "clkab", "clkna", "clknab", "clkb", "clkbb", "clknb", "clknbb", "trka0", "trka1", "trkb0", "trkb1"] + \
        ["cpa%d" % k for k in range(12, -1, -1)] + ["cna%d" % k for k in range(12, -1, -1)] + \
        ["cpb%d" % k for k in range(12, -1, -1)] + ["cnb%d" % k for k in range(12, -1, -1)]
ev = []
for l in open(a.log):
    if l.startswith("#"):
        continue
    tp, bits, ctl = l.split()
    ev.append((int(tp) * 1e-12, bits))
ts_dut = np.array([e[0] for e in ev])


def dut_bits(tq):
    i = np.searchsorted(ts_dut, tq, side="right") - 1
    return ev[i][1] if i >= 0 else None


def dut(n, tq):
    b = dut_bits(tq)
    c = b[order.index(n)]
    return None if c not in "01" else int(c)


ntick = int(info["tend_s"] / T) - 1
res = {"case": a.case, "beh_run": a.beh, "dut_log": os.path.basename(a.log), "label": a.label, "ticks": ntick,
       "samples_per_tick": [10e-9, 20e-9]}
mm = {"cdac": [], "cmpclk": [], "trk": []}
nsamp = {"cdac": 0, "cmpclk": 0, "trk": 0}
for n in range(1, ntick + 1):
    for off in (10e-9, 20e-9):
        tq = n * T + off
        for s in "ab":
            for p in "pn":
                for k in range(13):
                    nm = "c%s%s%d" % (p, s, k)
                    nsamp["cdac"] += 1
                    x, y = beh(nm, tq), dut(nm, tq)
                    if x != y:
                        mm["cdac"].append([n, off * 1e9, nm, x, y])
        for nm in names[:8]:
            nsamp["cmpclk"] += 1
            x, y = beh(nm, tq), dut(nm, tq)
            if x != y:
                mm["cmpclk"].append([n, off * 1e9, nm, x, y])
        for nm in names[8:12]:
            nsamp["trk"] += 1
            x, y = beh(nm, tq), dut(nm, tq)
            if x != y:
                mm["trk"].append([n, off * 1e9, nm, x, y])
# expected differences (protocol, not logic), README "Equivalence": (1) bootstrap pre-charge: the deck holds trk0
# low 33 ns from 106 ns, the ctrl protocol (r1_gate PRE_HOLD) holds 2 ticks (edges 3 to 5): trk only, ticks 3-5;
# (2) after the last frame the deck has no further track edge, so its flags and trk stay as at the end of the
# conversion; the macro releases at E14: all groups, ticks >= last start + 14.
last_end = int(round(info["ts_s"][-1] / T)) + 14
def expected(m, grp):
    if grp == "trk" and 3 <= m[0] <= 5:
        return "precharge"
    if m[0] >= last_end:
        return "after_last_frame"
    return None
cls = {}
unexpl = {}
for grp, v in mm.items():
    for m in v:
        c = expected(m, grp)
        cls[c or "unexplained"] = cls.get(c or "unexplained", 0) + 1
        if c is None:
            unexpl.setdefault(grp, []).append(m)
res["mismatch_classes"] = cls
res["unexplained"] = unexpl
res["samples"] = nsamp
res["mismatch_count"] = {k: len(v) for k, v in mm.items()}
res["mismatches"] = {k: v[:60] for k, v in mm.items()}
# decisions and valid per frame
frames = []
dec_ok = True
for f, ts in enumerate(info["ts_s"]):
    n0 = int(round(ts / T))
    row = {"frame": f, "type": info["frames"][f], "start_tick": n0}
    for s in "ab":
        # behavioural: lat pulse tick and the raw register after it
        lt = [n for n in range(n0, n0 + 20) if beh("lat" + s, n * T + 1.0e-9)]
        bw = [beh("xsar.r%s%d" % (s, k), (n0 + 14) * T + 5e-9) for k in range(13, -1, -1)]
        vt = [n for n in range(n0, n0 + 20) if dut("v" + s, n * T + 5e-9)]
        dw = [dut("raw_%s%d" % (s, k), (vt[0] if vt else n0 + 14) * T + 5e-9) for k in range(13, -1, -1)]
        row[s] = {"beh_lat_tick": [x - n0 for x in lt], "dut_valid_tick": [x - n0 for x in vt],
                  "beh_dec": "".join(map(str, bw)), "dut_dec": "".join("x" if x is None else str(x) for x in dw),
                  "equal": bw == dw and [x - n0 for x in lt] == [x - n0 for x in vt]}
        dec_ok &= row[s]["equal"]
    frames.append(row)
res["frames"] = frames
res["decisions_and_valid_equal"] = dec_ok
# comparator edges between the behavioural strobe and the RTL latch close
vec = open(os.path.join(HERE, "vec", a.case + "_stim.vh")).read().split("\n")
t = 0.0
edges = {}
for l in vec:
    l = l.strip()
    if l.startswith("#"):
        t += float(l[1:-1]) * 1e-9
    elif "= 1'b" in l and t > 0:
        nm = l.split("=")[0].strip()
        edges.setdefault(nm, []).append(t)
near = []
for f, ts in enumerate(info["ts_s"]):
    for k in range(14):
        e = ts + (k + 1) * T
        for s in "ab":
            nm = ("o%snp" if k == 0 else "o%sp") % s
            for te in edges.get(nm, []):
                if e - 0.6e-9 <= te <= e + 0.2e-9:
                    near.append([f, s, k, nm, round((te - e) * 1e9, 3)])
res["cmp_edges_in_strobe_to_latch_window"] = near
res["pass"] = dec_ok and not unexpl
json.dump(res, open(a.out, "w"), indent=1)
print(json.dumps({k: res[k] for k in ("case", "label", "ticks", "samples", "mismatch_count", "mismatch_classes", "decisions_and_valid_equal",
                                       "pass")}))
for r in frames:
    print(r["frame"], r["type"], "A", r["a"]["beh_dec"], r["a"]["dut_dec"], r["a"]["beh_lat_tick"], r["a"]["dut_valid_tick"],
          "B", r["b"]["beh_dec"], r["b"]["dut_dec"], r["a"]["equal"] and r["b"]["equal"])
if mm["trk"]:
    print("trk mismatches (tick, ns, signal, beh, dut):", mm["trk"][:30])
if near:
    print("edges near strobe:", near)
