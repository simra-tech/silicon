#!/usr/bin/env python3
"""Compare two SPICE netlists device by device per subckt (instance name, nodes, model, parameters).
Usage: python3 compare_netlists.py r1_osc.spice xschem_netlist/r1_osc.spice ; exit 0 when equal."""
import re
import sys


def parse(fn):
    subs, cur = {}, None
    for line in open(fn):
        line = line.strip()
        if not line or line.startswith("*"):
            continue
        tok = line.split()
        if tok[0].lower() == ".subckt":
            cur = tok[1]
            subs[cur] = {"ports": tok[2:], "dev": {}}
        elif tok[0].lower() == ".ends":
            cur = None
        elif cur and tok[0][0] in "XxRrCcMmDd":
            nodes = [t for t in tok[1:] if "=" not in t]
            params = dict(t.split("=", 1) for t in tok[1:] if "=" in t)
            params = {k: re.sub(r"(\d)\.0+u$", r"\1u", v) for k, v in params.items()}
            # normalise 4.03u / 4.030u, m=1 default
            subs[cur]["dev"][tok[0].upper()] = (tuple(nodes), tuple(sorted(params.items())))
    return subs


a, b = parse(sys.argv[1]), parse(sys.argv[2])
bad = 0
for s in sorted(set(a) | set(b)):
    if s not in a or s not in b:
        print("subckt only in one netlist:", s); bad += 1; continue
    if a[s]["ports"] != b[s]["ports"]:
        print(s, "ports differ", a[s]["ports"], b[s]["ports"]); bad += 1
    for d in sorted(set(a[s]["dev"]) | set(b[s]["dev"])):
        if a[s]["dev"].get(d) != b[s]["dev"].get(d):
            print(s, d, "\n  A:", a[s]["dev"].get(d), "\n  B:", b[s]["dev"].get(d)); bad += 1
print("subckts:", len(a), "differences:", bad)
sys.exit(1 if bad else 0)
