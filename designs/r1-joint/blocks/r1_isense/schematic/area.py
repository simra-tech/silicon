#!/usr/bin/env python3
"""Device-area estimate from a generated SPICE netlist (drawn W*L of MOS gates, w*l of resistor bodies, MIM w*l),
summed per subcircuit through the hierarchy. Usage: python3 area.py netlist.spice TOP [TOP2 ...]"""
import sys, re, collections
def val(s):
    s = s.lower().rstrip("u")
    return float(s)
subs, cur = {}, None
for line in open(sys.argv[1]):
    t = line.split()
    if not t or t[0].startswith("*"): continue
    if t[0].lower() == ".subckt": cur = t[1]; subs[cur] = []; continue
    if t[0].lower() == ".ends": cur = None; continue
    if cur and t[0][0] in "Xx": subs[cur].append(t)
def area(name, memo={}):
    if name in memo: return memo[name]
    acc = collections.Counter()
    for t in subs.get(name, []):
        kv = dict(p.split("=", 1) for p in t if "=" in p)
        pos = [p for p in t if "=" not in p]
        model = pos[-1]
        m = float(kv.get("m", "1"))
        if model.startswith("sg13_"):
            k = "mos_hv" if "_hv_" in model else "mos_lv"
            acc[k] += val(kv["w"]) * val(kv["l"]) * m
        elif model in ("rppd", "rhigh", "rsil"):
            acc["res_" + model] += val(kv["w"]) * val(kv["l"]) * m
        elif model.startswith("cap_cmim"):
            acc["mim"] += val(kv["w"]) * val(kv["l"]) * m
        elif model in subs:
            for k, v in area(model).items(): acc[k] += v * m
    memo[name] = acc
    return acc
for top in sys.argv[2:]:
    a = area(top)
    print("%s: total %.0f um2 (%s)" % (top, sum(a.values()), ", ".join("%s %.0f" % kv for kv in sorted(a.items()))))
