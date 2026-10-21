#!/usr/bin/env python3
"""Wiring resistance of the precision paths of r1_bgr from the extracted networks (pex_build.py output).

  flow/run.sh python3 designs/r1-joint/blocks/r1_bgr/layout/pex_paths.py <pex run dir> [<post run dir>]

Effective resistances (numpy/scipy Laplacian solve, all other ports open):
  dvbe : the 48 Q2 emitters (shorted) -> R1 dvbe-end terminal; and each emitter alone -> R1 terminal (min/max)
  vssq : the 12 Q1 emitters (shorted) -> R1 vss-end terminal (the star); star -> vss pin
  vbe  : the 12 Q1 base/collector ports (shorted) -> the 48 Q2 base ports (shorted)
  vbe3 : the 4 Q3 collector ports -> R2 vbe3-end terminal
  vref : R2 vref-end terminal -> vref pin
With <post run dir> (run_bgr_post.py, op_rc_ports.json) the IR drops at the tt/27 C operating point are added.
Writes pex_paths.json next to the networks and prints it.
"""
import json
import os
import sys

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as sla

PEX = sys.argv[1]
POST = sys.argv[2] if len(sys.argv) > 2 else None
D = json.load(open(os.path.join(PEX, 'r1_bgr_pex_rnets.json')))
RN, DEV = D['rnets'], D['devices']


def reff(net, A, B):
    """effective resistance between node sets A and B of net (A and B each shorted)"""
    els = RN[net]['elements']
    nodes = sorted({n for a, b, _ in els for n in (a, b)})
    idx = {n: i for i, n in enumerate(nodes)}
    for n in list(A) + list(B):
        if n not in idx:
            raise KeyError('%s not in network %s' % (n, net))
    N = len(nodes)
    rows, cols, vals = [], [], []
    for a, b, r in els:
        g = 1.0 / r
        i, j = idx[a], idx[b]
        rows += [i, j, i, j]
        cols += [i, j, j, i]
        vals += [g, g, -g, -g]
    G = sp.csr_matrix((vals, (rows, cols)), shape=(N, N))
    fix = {idx[n]: 1.0 for n in A}
    fix.update({idx[n]: 0.0 for n in B})
    free = [i for i in range(N) if i not in fix]
    fi = np.array(sorted(fix))
    vf = np.array([fix[i] for i in fi])
    Gff = G[free][:, free]
    Gfx = G[free][:, fi]
    v = np.zeros(N)
    v[fi] = vf
    if free:
        v[free] = sla.spsolve(Gff.tocsc(), -Gfx @ vf)
    i_in = (G @ v)[[idx[n] for n in A]].sum()
    return 1.0 / i_in


def ports(cls, cond, term):
    out = []
    for k, d in DEV.items():
        if d['cls'] == cls and cond(d):
            out.append(d['t'][term][1])
    return out


q2e = ports('npn13G2', lambda d: d['t']['E'][0] == 'dvbe', 'E')
q2b = ports('npn13G2', lambda d: d['t']['E'][0] == 'dvbe', 'B')
q1e = ports('npn13G2', lambda d: d['t']['C'][0] == 'vbe' and d['t']['E'][0] == 'vss', 'E')
q1b = ports('npn13G2', lambda d: d['t']['C'][0] == 'vbe' and d['t']['E'][0] == 'vss', 'B')
r1d = [d['t'][t][1] for d in DEV.values() if d['cls'] == 'rppd' for t in ('rppd_1', 'rppd_2') if d['t'][t][0] == 'dvbe']
r1s = [d['t'][t][1] for d in DEV.values() if d['cls'] == 'rppd' and any(d['t'][u][0] == 'dvbe' for u in ('rppd_1', 'rppd_2')) is False
       and abs(d.get('pos', [0, 0])[0]) >= 0 for t in ('rppd_1', 'rppd_2') if d['t'][t][0] == 'vss']
r2v = [d['t'][t][1] for d in DEV.values() if d['cls'] == 'rppd' for t in ('rppd_1', 'rppd_2') if d['t'][t][0] == 'vref']
vbe3_net = None
q3c = []
for d in DEV.values():
    if d['cls'] == 'npn13G2' and d['t']['C'][0] == d['t']['B'][0] and d['t']['E'][0] == 'vss' and d['t']['C'][0] not in ('vbe', 'vss'):
        if vbe3_net is None or d['t']['C'][0] == vbe3_net:
            n = d['t']['C'][0]
            # Q3 (4 units) vs QD2 (1 unit): take the net with 4 units
            q3c.append((n, d['t']['C'][1]))
from collections import Counter  # noqa: E402
n3 = Counter(n for n, _ in q3c).most_common(1)[0][0]
q3c = [p for n, p in q3c if n == n3]
r2e = [d['t'][t][1] for d in DEV.values() if d['cls'] == 'rppd' for t in ('rppd_1', 'rppd_2') if d['t'][t][0] == n3]
assert len(q2e) == 48 and len(q1e) == 12 and len(q3c) == 4, (len(q2e), len(q1e), len(q3c))
assert len(r1d) == 1 and len(r1s) == 1 and len(r2v) == 1 and len(r2e) == 1, (r1d, r1s, r2v, r2e)

res = {}
res['dvbe_Q2emitters_to_R1'] = reff('dvbe', set(q2e), {r1d[0]})
per = [reff('dvbe', {e}, {r1d[0]}) for e in q2e]
res['dvbe_single_emitter_to_R1_min'] = min(per)
res['dvbe_single_emitter_to_R1_max'] = max(per)
res['dvbe_R1_to_pin'] = reff('dvbe', {r1d[0]}, {'dvbe'})
res['vss_Q1emitters_to_R1star'] = reff('vss', set(q1e), {r1s[0]})
per = [reff('vss', {e}, {r1s[0]}) for e in q1e]
res['vss_single_Q1emitter_to_star_min'] = min(per)
res['vss_single_Q1emitter_to_star_max'] = max(per)
res['vss_R1star_to_pin'] = reff('vss', {r1s[0]}, {'vss'})
q1bs = set(q1b) - set(q2b)
res['vbe_Q1bases_to_Q2bases'] = reff('vbe', q1bs, set(q2b))
res['vbe3_Q3_to_R2'] = reff(n3, set(q3c), {r2e[0]})
res['vref_R2_to_pin'] = reff('vref', {r2v[0]}, {'vref'})
res = {k: round(v, 4) for k, v in res.items()}
res['units'] = 'Ohm'
res['nodes'] = dict(R1_dvbe=r1d[0], R1_star=r1s[0], R2_vref=r2v[0], R2_vbe3=r2e[0], vbe3_net=n3)

if POST:
    pv = json.load(open(os.path.join(POST, 'op_rc_ports.json')))
    g = lambda n: pv.get('v(xbgr.%s)' % n)
    ref = g(r1d[0])
    de = [g(e) - ref for e in q2e]
    star = g(r1s[0])
    se = [g(e) - star for e in q1e]
    ir = dict(dvbe_Q2emitter_minus_R1_uV=[round(min(de) * 1e6, 2), round(sum(de) / len(de) * 1e6, 2), round(max(de) * 1e6, 2)],
              vss_Q1emitter_minus_star_uV=[round(min(se) * 1e6, 2), round(sum(se) / len(se) * 1e6, 2), round(max(se) * 1e6, 2)],
              star_minus_vss_pin_uV=round(star * 1e6, 2),
              note='[min, mean, max] over the units; tt/27 C/3.3 V operating point of the full RC view')
    q1bv = [g(b) for b in q1bs]
    q2bv = [g(b) for b in q2b]
    ir['vbe_Q2base_minus_Q1base_mean_uV'] = round((sum(q2bv) / len(q2bv) - sum(q1bv) / len(q1bv)) * 1e6, 2)
    # error in delta-V_BE seen by R1: (V_E,Q1 - V_star) - (V_E,Q2 - V_R1top) referred to the R1 voltage
    ir['dvbe_error_estimate_uV'] = round(((sum(se) / len(se)) - (sum(de) / len(de)) + (ir['vbe_Q2base_minus_Q1base_mean_uV'] * 1e-6)) * 1e6, 2)
    res['ir_drop_tt27'] = ir
json.dump(res, open(os.path.join(PEX, 'pex_paths.json'), 'w'), indent=1)
print(json.dumps(res, indent=1))
