#!/usr/bin/env python3
"""Wiring resistance of r1_isense_ch from the extracted networks (pex_build.py output; numpy/scipy), after
r1_bgr/layout/pex_paths.py.   flow/run.sh python3 pex_paths.py <pex rc dir> [net ...]
For every net (or the listed ones): effective resistance from the net's main node (the pin for ports) to each device
terminal port, all other ports open. Writes pex_paths.json in <pex rc dir> and prints the largest values, plus the
resistor-arm table (wiring in series with RIN, RF, RP per side and the ratio error of the gain network)."""
import json, os, sys
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as sla
PEX = sys.argv[1]
D = json.load(open(os.path.join(PEX, 'r1_isense_ch_pex_rnets.json')))
RN, DEV = D['rnets'], D['devices']


def reff(net, A, B):
    els = RN[net]['elements']
    nodes = sorted({n for a, b, _ in els for n in (a, b)})
    idx = {n: i for i, n in enumerate(nodes)}
    N = len(nodes)
    rows, cols, vals = [], [], []
    for a, b, r in els:
        g = 1.0 / r; i, j = idx[a], idx[b]
        rows += [i, j, i, j]; cols += [i, j, j, i]; vals += [g, g, -g, -g]
    G = sp.csr_matrix((vals, (rows, cols)), shape=(N, N))
    fix = {idx[n]: 1.0 for n in A}; fix.update({idx[n]: 0.0 for n in B})
    free = [i for i in range(N) if i not in fix]
    fi = np.array(sorted(fix)); vf = np.array([fix[i] for i in fi])
    v = np.zeros(N); v[fi] = vf
    if free:
        v[free] = sla.spsolve(G[free][:, free].tocsc(), -G[free][:, fi] @ vf)
    return 1.0 / (G @ v)[[idx[n] for n in A]].sum()


out = {}
nets = sys.argv[2:] or sorted(RN)
for net in nets:
    r = RN[net]; m = r['main']
    vals = {}
    for p in r['ports']:
        if p == m:
            continue
        try:
            vals[p] = reff(net, [p], [m])
        except Exception as e:
            vals[p] = None
    out[net] = dict(main=m, port_to_main=vals)
# device terminal lookup: (device class, other terminal nets) for each port
tport = {}
for did, d in DEV.items():
    for t, (nn, node) in d['t'].items():
        tport.setdefault(node, []).append((d['cls'], t, did, {k: v[0] for k, v in d['t'].items()}))
json.dump(dict(paths=out, port_devices={k: [(c, t, i) for c, t, i, _ in v] for k, v in tport.items()}),
          open(os.path.join(PEX, 'pex_paths.json'), 'w'), indent=0)
flat = sorted(((v, n, p) for n, o in out.items() for p, v in o['port_to_main'].items() if v is not None), reverse=True)
for v, n, p in flat[:25]:
    print('%8.2f ohm  %-10s %-14s %s' % (v, n, p, [(c, t) for c, t, _, _ in tport.get(p, [])][:3]))
