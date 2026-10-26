#!/usr/bin/env python3
"""Effective resistance from the main node of a net to each of its port nodes (net__pK) in a post-layout netlist
(T2 harness diagnostic, 2026-10-26): Laplacian of the R elements of one subcircuit, other ports open.
usage: net_reff.py <netlist> <subckt> <net> [<net> ...]   -> prints max / median and the worst ports"""
import sys
import numpy as np
f, sub, nets = sys.argv[1], sys.argv[2], sys.argv[3:]
R, cur = [], None
for l in open(f):
    t = l.split()
    if not t:
        continue
    if t[0] == '.subckt':
        cur = t[1]
    elif t[0] == '.ends':
        cur = None
    elif cur == sub and t[0][0] in 'Rr':
        R.append((t[1], t[2], float(t[3])))
for net in nets:
    el = [(a, b, r) for a, b, r in R if a.split('__')[0] == net and b.split('__')[0] == net]
    nodes = sorted(set([a for a, b, r in el] + [b for a, b, r in el]))
    if net not in nodes:
        print(net, 'no R network'); continue
    ix = {n: i for i, n in enumerate(nodes)}
    G = np.zeros((len(nodes),) * 2)
    for a, b, r in el:
        g = 1.0 / max(r, 1e-6)
        i, j = ix[a], ix[b]
        G[i, i] += g; G[j, j] += g; G[i, j] -= g; G[j, i] -= g
    k = ix[net]
    keep = [i for i in range(len(nodes)) if i != k]
    Gr = G[np.ix_(keep, keep)]
    Zi = np.linalg.inv(Gr)
    reff = {nodes[keep[i]]: Zi[i, i] for i in range(len(keep))}
    w = sorted(reff.items(), key=lambda x: -x[1])
    print('%-8s ports %3d  Reff max %9.1f Ohm  median %8.1f Ohm  worst: %s' % (net, len(reff), w[0][1], np.median(list(reff.values())),
          ', '.join('%s %.0f' % x for x in w[:3])))
