#!/usr/bin/env python3
"""Device-area estimate from a SPICE netlist (drawn W*L of MOS gates, w*l of resistor bodies, MIM w*l, HBT units
counted), summed per subcircuit through the hierarchy. Parameterised multipliers (m={m}) count as 1 inside the
subckt and are multiplied by the instance m. Same method as r1_isense/schematic/area.py plus HBT and device counts.
Usage: python3 area.py netlist.spice TOP [TOP2 ...]"""
import sys, collections
def val(s):
    return float(s.lower().rstrip("u"))
def num(s, d=1.0):
    try: return float(s)
    except ValueError: return d
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
        m = num(kv.get("m", "1"))
        if model.startswith("sg13_"):
            k = "mos_hv" if "_hv_" in model else "mos_lv"
            acc[k] += val(kv["w"]) * val(kv["l"]) * m; acc["n_" + k] += m
        elif model in ("rppd", "rhigh", "rsil"):
            acc["res_" + model] += val(kv["w"]) * val(kv["l"]) * m; acc["n_res"] += m
        elif model.startswith("cap_cmim"):
            acc["mim"] += val(kv["w"]) * val(kv["l"]) * m; acc["n_mim"] += m
        elif model.startswith("npn13G2"):
            acc["n_hbt"] += m
        elif model in subs:
            for k, v in area(model).items(): acc[k] += v * m
    memo[name] = acc
    return acc
for top in sys.argv[2:]:
    a = area(top)
    dev = sum(v for k, v in a.items() if not k.startswith("n_"))
    cnt = sum(v for k, v in a.items() if k.startswith("n_"))
    print("%s: drawn %.0f um2, %d devices (%s)" % (top, dev, cnt, ", ".join("%s %.0f" % kv for kv in sorted(a.items()))))
