#!/usr/bin/env python3
"""Layout E5 (track T3): top-level supply impedance of the two channel instances from the Rt* elements of a
pex_rc_build.py netlist (pin node = ground): self Z of vdd__xsin / vdd__xcos (vss) and the mutual Z between them
(a current into one channel moves the other channel's supply by Z_mut).
  python3 pex/top_supply_z.py <r1_afe_post_rc.spice>   -> JSON on stdout"""
import collections, json, sys
import numpy as np
el = collections.defaultdict(list)
for l in open(sys.argv[1]):
    if l.startswith('Rt'):
        _, a, b, r = l.split()
        el[a.split('__')[0]].append((a, b, float(r)))
out = {}
for net in ('vdd', 'vss'):
    nodes = sorted({n for a, b, _ in el[net] for n in (a, b)}); ix = {n: i for i, n in enumerate(nodes)}
    G = np.zeros((len(nodes),) * 2)
    for a, b, r in el[net]:
        g = 1 / r; i, j = ix[a], ix[b]; G[i, i] += g; G[j, j] += g; G[i, j] -= g; G[j, i] -= g
    keep = [i for i in range(len(nodes)) if nodes[i] != net]
    Z = np.linalg.inv(G[np.ix_(keep, keep)]); zi = {nodes[k]: q for q, k in enumerate(keep)}
    s, c = net + '__xsin', net + '__xcos'
    out[net] = dict(z_sin=round(float(Z[zi[s], zi[s]]), 2), z_cos=round(float(Z[zi[c], zi[c]]), 2), z_mut=round(float(Z[zi[s], zi[c]]), 2))
print(json.dumps(out))
