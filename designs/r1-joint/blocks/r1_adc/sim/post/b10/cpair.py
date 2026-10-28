#!/usr/bin/env python3
"""T2p: total extracted C and the largest coupling partners of P/N comparator net pairs in the slice subcircuit of a
merged post-layout netlist (Cp lines, nets by name without __p/__i suffix). usage: cpair.py <netlist> [subckt]"""
import re, sys, collections
f = sys.argv[1]; sub = sys.argv[2] if len(sys.argv) > 2 else 'r1_adc_slice_post'
net = lambda n: re.sub(r'__[pie]\d+$', '', n)
C = collections.defaultdict(float); cur = None
for l in open(f):
    t = l.split()
    if not t: continue
    if t[0] == '.subckt': cur = t[1]
    elif t[0] == '.ends': cur = None
    elif cur == sub and re.match(r'Cp\d+', t[0]):
        a, b = net(t[1]), net(t[2]); v = float(re.sub(r'[fF]$', 'e-15', t[3])) if t[3][-1] in 'fF' else float(t[3])
        C[(a, b)] += v; C[(b, a)] += v
for p, n in (('xc4_dip', 'xc4_din'), ('op', 'on'), ('xc5_dip', 'xc5_din'), ('onp', 'onn'), ('xc4_outpb', 'xc4_outnb')):
    tp = sum(v for (a, b), v in C.items() if a == p); tn = sum(v for (a, b), v in C.items() if a == n)
    parts = set(b for (a, b) in C if a in (p, n)) - {p, n}
    diff = sorted(((C.get((p, x), 0) - C.get((n, x), 0)) * 1e15, x) for x in parts)
    big = [(x, round(d, 2)) for d, x in diff if abs(d) > 0.3]
    print('%-9s %-9s total %.1f / %.1f fF; P-N coupling > 0.3 fF: %s' % (p, n, tp * 1e15, tn * 1e15, big))
