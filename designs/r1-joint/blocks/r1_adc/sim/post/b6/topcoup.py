#!/usr/bin/env python3
"""T2l (layout B6): extracted coupling to the slice top plates, per net and in total, from post-layout RC netlists
(subckt r1_adc_slice_post; one slice, both slices are copies). Prints top_p / top_n / difference in fF for the nets of
the elimination groups and every net with |difference| >= 0.1 fF, plus the total top-plate parasitic.
usage: topcoup.py OUT.json label=netlist [label=netlist ...]"""
import collections, json, os, re, sys
GROUPS = {"clocks": ["clk", "clkb", "clkn", "clknb"], "trk": ["trk0", "trk1", "t0", "t1", "t0b", "t1b"],
          "north_out_and_switch": ["op", "on", "onp", "onn"] + ["cp%d" % k for k in range(13)] + ["cn%d" % k for k in range(13)],
          "vdd": ["vdd"], "gnd": ["gnd"]}
net = lambda n: re.sub(r"__[pi]\d+$", "", n)
res = {}
for arg in sys.argv[2:]:
    lab, f = arg.split("=", 1)
    s = re.search(r"^\.subckt r1_adc_slice_post.*?^\.ends", open(f).read(), re.S | re.M).group(0)
    agg = collections.defaultdict(lambda: [0.0, 0.0])
    for ln in s.split("\n"):
        if re.match(r"C\w+ ", ln):
            t = ln.split()
            try:
                v = float(t[3].replace("f", "e-15")) if t[3].endswith("f") else float(t[3])
            except ValueError:
                continue
            a, b = net(t[1]), net(t[2])
            for x, y in ((a, b), (b, a)):
                if x == "top_p": agg[y][0] += v * 1e15
                if x == "top_n": agg[y][1] += v * 1e15
    r = {"total_fF": [round(sum(v[0] for v in agg.values()), 3), round(sum(v[1] for v in agg.values()), 3)],
         "groups_fF": {g: [round(sum(agg[n][0] for n in ns), 3), round(sum(agg[n][1] for n in ns), 3),
                           round(sum(agg[n][0] - agg[n][1] for n in ns), 3)] for g, ns in GROUPS.items()},
         "nets_fF": {k: [round(v[0], 3), round(v[1], 3), round(v[0] - v[1], 3)] for k, v in sorted(agg.items())
                     if abs(v[0] - v[1]) >= 0.1 or any(k in ns for ns in GROUPS.values())}}
    res[lab] = r
    print(lab, "total top_p/top_n", r["total_fF"], "imbalance %.3f" % (r["total_fF"][0] - r["total_fF"][1]))
    for g, v in r["groups_fF"].items():
        print("   %-22s p %7.3f n %7.3f diff %+7.3f" % (g, *v))
    for n in ("clk", "clkb", "clkn", "clknb", "trk0", "trk1"):
        print("   %-8s" % n, r["nets_fF"].get(n))
json.dump({"tool": "sim/post/b6/topcoup.py", "label": "extracted (kpex 2.5D CC), fF, slice subcircuit", "netlists": {a.split("=")[0]: a.split("=", 1)[1].replace(os.environ.get("G1_RESULTS_ROOT", "<G1_RESULTS_ROOT>"), "<G1_RESULTS_ROOT>") for a in sys.argv[2:]}, "results": res}, open(sys.argv[1], "w"), indent=1)
