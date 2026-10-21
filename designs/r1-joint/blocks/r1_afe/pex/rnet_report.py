#!/usr/bin/env python3
"""Effective resistance from every port node of a net to the net's main node (cell pin or anchor), from the R elements
(Rw*/Rt*) of a pex_rc_build.py netlist; all other ports open. Pure Python + numpy.
  python3 pex/rnet_report.py <r1_afe_post_rc.spice> [net ...]   -> JSON on stdout (worst 3 ports per net, Ohm)"""
import collections, json, sys
import numpy as np
F = sys.argv[1]
want = sys.argv[2:]
els = {'ch': collections.defaultdict(list), 'top': collections.defaultdict(list)}
for l in open(F):
    if l.startswith(('Rw', 'Rt')):
        _, a, b, r = l.split()
        els['ch' if l.startswith('Rw') else 'top'][a.split('__')[0]].append((a, b, float(r)))
out = {}
for scope, E in els.items():
    for net, el in E.items():
        if want and net not in want:
            continue
        nodes = sorted({n for a, b, _ in el for n in (a, b)})
        if net not in nodes:
            continue
        ix = {n: i for i, n in enumerate(nodes)}
        G = np.zeros((len(nodes), len(nodes)))
        for a, b, r in el:
            g = 1.0 / r; i, j = ix[a], ix[b]
            G[i, i] += g; G[j, j] += g; G[i, j] -= g; G[j, i] -= g
        keep = [i for i in range(len(nodes)) if i != ix[net]]
        Z = np.linalg.inv(G[np.ix_(keep, keep)])
        r = sorted(((nodes[k], float(Z[q, q])) for q, k in enumerate(keep)), key=lambda kv: -kv[1])
        out['%s:%s' % (scope, net)] = dict(ports=len(r), worst=[[n, round(v, 2)] for n, v in r[:3]], all={n: round(v, 2) for n, v in r})
print(json.dumps(out, indent=1))
