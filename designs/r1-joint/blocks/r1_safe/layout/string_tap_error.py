#!/usr/bin/env python3
"""Tap error of the r1_safe 252-unit reference string from the extracted metal resistance (host Python, numpy/scipy).

  python3 string_tap_error.py <run dir with string_rnet.json> [R_unit_ohm]

Builds one linear network: the metal R networks of t1..t251, vref and vss (string_rnet.py) plus 252 equal unit
resistors between the rppd terminal ports (default R_unit = 260 Ohm/sq x 7.7/2 = 1001 Ohm, rppd typical sheet value
from the PDK cornerRES.lib; the unit value only scales the metal-to-unit ratio). The vref pin is 1 (normalised VREF),
the vss pin is 0. A tap voltage is read at every multiplexer input port (column-0 hv_nmos source/drain) of the net.
Ideal tap n = n/252. One tap step is VREF/252 = LSB/8 of the threshold DAC (README: 1 step = 4.167 mV Vod).
Error in steps = 252 * (V - n/252); in threshold LSB = steps / 8.
Writes <run dir>/string_tap_error.json and prints a summary.
"""
import json
import os
import re
import sys

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spl

RD = sys.argv[1]
RU = float(sys.argv[2]) if len(sys.argv) > 2 else 260.0 * 7.7 / 2.0
N = 252
D = json.load(open(os.path.join(RD, 'string_rnet.json')))

idx = {}


def node(n):
    if n not in idx:
        idx[n] = len(idx)
    return idx[n]


els = []
term = {}     # device -> list of node names
taps = {}     # net -> list of node names
for nn, v in D.items():
    for a, b, r in v['elements']:
        els.append((node(a), node(b), r))
    for pn, roles in v['ports'].items():
        node(pn)
        for role, info in roles:
            if role == 'res':
                dev = info.split(':')[0]
                term.setdefault(dev, []).append(pn)
            elif role == 'tap':
                taps.setdefault(nn, []).append(pn)
bad = {d: t for d, t in term.items() if len(set(t)) != 2}
assert not bad, 'devices without two terminal ports: %s' % list(bad.items())[:5]
assert len(term) == N, 'string units found %d' % len(term)
for d, t in term.items():
    els.append((node(t[0]), node(t[1]), RU))
n = len(idx)
G = sp.lil_matrix((n, n))
for a, b, r in els:
    g = 1.0 / r
    G[a, a] += g
    G[b, b] += g
    G[a, b] -= g
    G[b, a] -= g
G = G.tocsr()
fix = {idx['vref__pin']: 1.0, idx['vss__pin']: 0.0}
free = np.array([i for i in range(n) if i not in fix])
fx = np.array(list(fix.keys()))
vf = np.array(list(fix.values()))
rhs = -G[free][:, fx] @ vf
v = np.zeros(n)
v[fx] = vf
v[free] = spl.spsolve(G[free][:, free].tocsc(), rhs)

rows = []
for nn, tl in taps.items():
    k = N if nn == 'vref' else (0 if nn == 'vss' else int(re.match(r't(\d+)', nn).group(1)))
    vt = [v[idx[t]] for t in tl]
    e = [(x - k / N) * N for x in vt]          # in steps (LSB/8)
    rows.append(dict(net=nn, n=k, taps=len(tl), err_step_min=min(e), err_step_max=max(e)))
rows.sort(key=lambda r: r['n'])
worst = max(rows, key=lambda r: max(abs(r['err_step_min']), abs(r['err_step_max'])))
wl = max(abs(worst['err_step_min']), abs(worst['err_step_max']))
# error change between adjacent taps, in steps
mid = {r['n']: (r['err_step_min'] + r['err_step_max']) / 2 for r in rows}
dnl = max(abs(mid[k + 1] - mid[k]) for k in range(N) if k in mid and k + 1 in mid)
spread = max(r['err_step_max'] - r['err_step_min'] for r in rows)
c44 = (mid.get(176), mid.get(76))     # code 44, k = 32: REFP = T176, REFN = T76 (gen_tb_safe_joint3.npn)
res = dict(R_unit_ohm=RU, nodes=n, elements=len(els), units=len(term), tap_nets=len(rows),
           unit='step = VREF/252 = LSB/8', max_abs_tap_error_steps=wl, max_abs_tap_error_lsb=wl / 8,
           worst_net=worst['net'], max_adjacent_step_error_steps=dnl, max_spread_between_mux_inputs_steps=spread,
           code44_T176_T76_error_steps=c44, rows=rows)
json.dump(res, open(os.path.join(RD, 'string_tap_error.json'), 'w'), indent=1)
print('units %d, tap nets %d, nodes %d' % (len(term), len(rows), n))
print('max |tap error| %.4f steps (LSB/8) = %.5f LSB (net %s); max adjacent-step error %.4f steps; '
      'mux-input spread %.2e steps; code 44 taps T176 / T76 %.4f / %.4f steps' % (wl, wl / 8, worst['net'], dnl, spread, c44[0], c44[1]))
