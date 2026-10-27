#!/usr/bin/env python3
"""Layout B4 diagnostic: effective resistance from the slice pins of a net (all subcircuit port nodes of the net held
together) to the source node of each CDAC driver, in the slice subcircuit of a pex_build RC netlist (Laplacian of the
wiring R; the method of the README "Port resistance" table, B.1).
usage: strap_r.py <r1_adc_post_rc.spice> -> per net: median / max / worst devices; JSON on stdout last line"""
import json, re, sys
import numpy as np
f = sys.argv[1]
sub = 'r1_adc_slice_post'
R, dev, ports, cur = [], {}, [], None
for l in open(f):
    t = l.split()
    if not t:
        continue
    if t[0] == '.subckt':
        cur = t[1]
        if cur == sub:
            ports = t[2:]
    elif t[0] == '.ends':
        cur = None
    elif cur == sub and t[0][0] in 'Rr':
        R.append((t[1], t[2], float(t[3])))
    elif cur == sub and t[0][0] in 'Xx' and re.match(r'Xx(d[np]\d+_xm[pn]|lr[np])$', t[0]):
        dev[t[0][1:]] = t[1:5]           # d g s b
out = {}
for net, sel in (('vref', lambda n: n.endswith('_xmp') and dev[n][2].split('__')[0] == 'vref'),
                 ('vrefl', lambda n: (n.endswith('_xmp') or n.startswith('xlr')) and dev[n][2].split('__')[0] == 'vrefl'),
                 ('gnd', lambda n: n.endswith('_xmn'))):
    el = [(a, b, r) for a, b, r in R if a.split('__')[0] == net and b.split('__')[0] == net]
    nodes = sorted(set([a for a, b, r in el] + [b for a, b, r in el]))
    ix = {n: i for i, n in enumerate(nodes)}
    pins = [p for p in ports if p.split('__')[0] == net and p in ix]
    G = np.zeros((len(nodes),) * 2)
    for a, b, r in el:
        g = 1.0 / max(r, 1e-6); i, j = ix[a], ix[b]
        G[i, i] += g; G[j, j] += g; G[i, j] -= g; G[j, i] -= g
    # pins held together: merge them into one reference node (eliminate)
    keep = [i for i in range(len(nodes)) if nodes[i] not in pins]
    Zi = np.linalg.inv(G[np.ix_(keep, keep)])
    pos = {nodes[k]: q for q, k in enumerate(keep)}
    vals = {}
    for n in dev:
        if sel(n):
            s = dev[n][2]
            vals[n] = float(Zi[pos[s], pos[s]]) if s in pos else 0.0
    w = sorted(vals.items(), key=lambda x: -x[1])
    out[net] = dict(n=len(vals), median_ohm=round(float(np.median(list(vals.values()))), 2), max_ohm=round(w[0][1], 2),
                    worst=[(a, round(b, 1)) for a, b in w[:4]], pins=pins)
    print('%-6s n %2d median %6.2f max %6.2f worst %s pins %s' % (net, len(vals), out[net]['median_ohm'], out[net]['max_ohm'], out[net]['worst'], pins))
print(json.dumps(out))
