#!/usr/bin/env python3
"""Layout E5 (track T3): mutual (transfer) resistances of the channel vss network between the output-stage sources and
the mirror-reference sources of both OTAs, from the Rw* elements of a pex_rc_build.py netlist (vss pin = ground).
  python3 pex/vss_mutual.py <r1_afe_post_rc.spice> [net]   -> JSON on stdout
Z[a][b] = voltage at port a per ampere injected at port b (Ohm). A current I in the output stage (port b) moves the
source of a mirror reference a and its mirror output c by Z[a][b] and Z[c][b]; the error voltage is I * (Z[c][b] - Z[a][b])."""
import collections, json, re, sys
import numpy as np
F = sys.argv[1]; NET = sys.argv[2] if len(sys.argv) > 2 else 'vss'
el, sub, devs = [], None, collections.defaultdict(dict)
inst = {}
for l in open(F):
    t = l.split()
    if not t:
        continue
    if t[0].lower() == '.subckt':
        sub = t[1]; continue
    if t[0].lower() == '.ends':
        sub = None; continue
    if sub == 'r1_afe_ch' and t[0].startswith('Rw') and t[1].split('__')[0] == NET:
        el.append((t[1], t[2], float(t[3])))
    if sub in ('r1_afe_ota', 'r1_afe_ota2') and t[0].startswith('XM'):
        devs[sub][t[0]] = t[1:5]      # d g s b
nodes = sorted({n for a, b, _ in el for n in (a, b)})
ix = {n: i for i, n in enumerate(nodes)}
G = np.zeros((len(nodes), len(nodes)))
for a, b, r in el:
    g = 1.0 / r; i, j = ix[a], ix[b]
    G[i, i] += g; G[j, j] += g; G[i, j] -= g; G[j, i] -= g
keep = [i for i in range(len(nodes)) if nodes[i] != NET]
Z = np.linalg.inv(G[np.ix_(keep, keep)])
zi = {nodes[k]: q for q, k in enumerate(keep)}
def z(a, b):
    if a == NET or b == NET:
        return 0.0
    return float(Z[zi[a], zi[b]])
out = {}
for sub, label in (('r1_afe_ota', 'xa1'), ('r1_afe_ota2', 'xa2')):
    D = devs[sub]
    src = {n: v[2] for n, v in D.items() if v[2].split('__')[0] == NET}
    outs = [n for n in ('XMN7', 'XMN8') if n in src]
    rows = {}
    for n, s in sorted(src.items()):
        rows[n] = dict(port=s, r_self=round(z(s, s), 2), **{'z_' + o: round(z(s, src[o]), 2) for o in outs})
    out[label] = rows
print(json.dumps(out, indent=1))
