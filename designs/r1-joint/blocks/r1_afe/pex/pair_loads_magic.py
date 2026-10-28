#!/usr/bin/env python3
"""Layout E8 (track T3l): per-net capacitance of the channel P/N pairs from a kpex --magic CC netlist (fast estimate,
seconds instead of the 50-70 min kpex 2.5D run); used only to place the x1 C trim before the 2.5D extraction, never as the
record. Calibrated against kpex 2.5D on layout-e7-dev17 (see README "Layout E8").
  python3 pex/pair_loads_magic.py <label>=<r1_afe_ch.pex.spice> ...  -> JSON on stdout"""
import json, re, sys
from collections import defaultdict
U = {'a': 1e-18, 'f': 1e-15, 'p': 1e-12}
CH = [('outp', 'outn'), ('op2', 'on2'), ('m1p', 'm1n'), ('x1p', 'x1n'), ('x2p', 'x2n'), ('inp', 'inn'), ('xa1_o1n', 'xa1_o1p')]
def load(f):
    d = defaultdict(float)
    for ln in open(f):
        t = ln.split()
        if len(t) >= 4 and re.match(r'^C\d', t[0]):
            v = t[3]
            v = float(v[:-1]) * U[v[-1]] if v[-1] in U else float(v)
            for n in (t[1], t[2]):
                d[n] += v * 1e15
    return d
out = {}
for arg in sys.argv[1:]:
    lab, f = arg.split('=', 1)
    ch = load(f)
    out[lab] = {'%s/%s' % (a, b): [round(ch[a], 2), round(ch[b], 2), round(ch[a] - ch[b], 2)] for a, b in CH}
print(json.dumps(out, indent=1))
