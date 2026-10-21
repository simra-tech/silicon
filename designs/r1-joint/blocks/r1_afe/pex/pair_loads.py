#!/usr/bin/env python3
"""Per-net extracted capacitance (sum of all kpex Cext elements on the net, fF) of the P/N pairs and the CM-sense nets,
for a list of kpex 2.5D CC netlists. Pure Python.
  python3 pex/pair_loads.py <label>=<channel kpex netlist>[,<top kpex netlist>] ...  -> JSON on stdout
Channel pairs: outp/outn, op2/on2, m1p/m1n, x1p/x1n, x2p/x2n, inp/inn; CM nets xa1_vcms, xa2_vcms, xa1_vcmfb, xa2_vcmfb.
Top pairs (top cell without channels): souts_p/souts_n, soutc_p/soutc_n, sinp/sinn, cosp/cosn."""
import json, sys
from collections import defaultdict
U = {'a': 1e-18, 'f': 1e-15, 'p': 1e-12}
CH = [('outp', 'outn'), ('op2', 'on2'), ('m1p', 'm1n'), ('x1p', 'x1n'), ('x2p', 'x2n'), ('inp', 'inn')]
CM = ['xa1_vcms', 'xa2_vcms', 'xa1_vcmfb', 'xa2_vcmfb']
TOP = [('souts_p', 'souts_n'), ('soutc_p', 'soutc_n'), ('sinp', 'sinn'), ('cosp', 'cosn')]


def load(f):
    d = defaultdict(float)
    for ln in open(f):
        t = ln.split()
        if t and t[0].startswith('Cext'):
            a, b = t[1].replace('\\', ''), t[2].replace('\\', '')
            v = t[3]
            v = float(v[:-1]) * U[v[-1]] if v[-1] in U else float(v)
            d[a] += v * 1e15
            d[b] += v * 1e15
    return d


out = {}
for arg in sys.argv[1:]:
    lab, files = arg.split('=', 1)
    fs = files.split(',')
    ch = load(fs[0])
    r = dict(channel={'%s/%s' % (a, b): [round(ch[a], 1), round(ch[b], 1), round(ch[a] - ch[b], 1)] for a, b in CH},
             cm={n: round(ch[n], 1) for n in CM}, channel_total_fF=round(sum(ch.values()) / 2, 1))
    if len(fs) > 1:
        tp = load(fs[1])
        r['top'] = {'%s/%s' % (a, b): [round(tp[a], 1), round(tp[b], 1), round(tp[a] - tp[b], 1)] for a, b in TOP}
    out[lab] = r
print(json.dumps(out, indent=1))
