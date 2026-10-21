#!/usr/bin/env python3
"""Wiring resistance and IR drop of the r1_bias mirror array from the extracted networks (method of
blocks/r1_bgr/layout/pex_paths.py).

  flow/run.sh python3 designs/r1-joint/blocks/r1_bias/layout/pex_paths.py <pex-rc run dir> [<post op summary json>]

From <pex-rc run dir>/r1_bias_pex_rnets.json (pex_build.py):
  source bus (vdda): the vdda pin is the reference (0 V). Every mirror unit draws its unit current (leg current / units,
     from the post-layout op summary at tt if given, else 10.14/5.07 uA nominal) from its source port; all other ports
     of the vdda net are left open (the POR, the T2F and the dummies draw no current in this solve). Result: the
     source voltage drop of every unit and its mean per leg, and the effective resistance pin -> unit (unit alone).
  gate bus (pbias, pcasc): effective resistance from the pin to every gate port. The DC gate current is zero, so the
     DC gate drop is zero; the resistance matters only for transients and noise coupling.
  mirror drain node (xl_<leg>.d): resistance mirror drain(s) -> cascode source(s) (carries the leg current; the drop
     lowers the mirror V_DS only).
Writes pex_paths.json next to the networks and prints it.
"""
import json
import os
import sys

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as sla

PEX = sys.argv[1]
OP = sys.argv[2] if len(sys.argv) > 2 else None
D = json.load(open(os.path.join(PEX, 'r1_bias_pex_rnets.json')))
RN, DEV = D['rnets'], D['devices']
LEGS = {'ib_afe_s1': 2, 'ib_afe_s2': 2, 'ib_afe_c1': 2, 'ib_afe_c2': 2, 'ib_is_a': 1, 'ib_is_b': 1, 'ib_sf_oa': 1,
        'ib_sf_na': 1, 'ib_sf_ob': 1, 'ib_sf_nb': 1, 'ib_adc_ref': 1}
I_LEG = {k: (10.14e-6 if m == 2 else 5.07e-6) for k, m in LEGS.items()}
src = 'nominal 10.14 / 5.07 uA'
if OP:
    rows = json.load(open(OP))['result']
    r = [x for x in rows if x['case'] == 'tt'][0]
    I_LEG = {k: r['i_uA'][k] * 1e-6 for k in LEGS}
    src = 'post-layout op at tt (%s)' % os.path.basename(OP)


def network(net):
    els = RN[net]['elements']
    nodes = sorted({n for a, b, _ in els for n in (a, b)})
    idx = {n: i for i, n in enumerate(nodes)}
    rows, cols, vals = [], [], []
    for a, b, r in els:
        g = 1.0 / r
        i, j = idx[a], idx[b]
        rows += [i, j, i, j]
        cols += [i, j, j, i]
        vals += [g, g, -g, -g]
    return idx, sp.csr_matrix((vals, (rows, cols)), shape=(len(nodes), len(nodes)))


def solve(net, ref, inj):
    """node voltages with node ref at 0 V and currents inj {node: A} drawn out of the nodes"""
    idx, G = network(net)
    N = G.shape[0]
    r = idx[ref]
    free = [i for i in range(N) if i != r]
    b = np.zeros(N)
    for n, i_ in inj.items():
        b[idx[n]] -= i_
    v = np.zeros(N)
    v[free] = sla.spsolve(G[free][:, free].tocsc(), b[free])
    return {n: v[i] for n, i in idx.items()}


def reff(net, a, bnode):
    v = solve(net, bnode, {a: -1.0})       # inject 1 A into a, b at 0 V
    return v[a]


mir, cas = {}, {}
for k, d in DEV.items():
    if d['cls'] != 'sg13_hv_pmos':
        continue
    t = d['t']
    g = t['G'][0]
    sd = {t['S'][0]: t['S'][1], t['D'][0]: t['D'][1]}
    if g == 'pbias' and 'vdda' in sd:
        other = [n for n in sd if n != 'vdda'][0]
        leg = other[3:-2] if other.startswith('xl_') else other
        mir.setdefault(leg, []).append(dict(src=sd['vdda'], gate=t['G'][1], drain=sd[other], x=d['pos'][0]))
    elif g == 'pcasc':
        nets = list(sd)
        dn = [n for n in nets if n.startswith('xl_') or n in ('xpor.dr', 'xpor.dl')]
        if dn:
            leg = dn[0][3:-2] if dn[0].startswith('xl_') else dn[0]
            cas.setdefault(leg, []).append(dict(src=sd[dn[0]], gate=t['G'][1], x=d['pos'][0]))
assert sorted(k for k in mir if k in LEGS) == sorted(LEGS), mir.keys()
inj = {}
for leg, us in mir.items():
    if leg in LEGS:
        for u in us:
            inj[u['src']] = inj.get(u['src'], 0.0) + I_LEG[leg] / len(us)
v = solve('vdda', 'vdda', inj)
out = dict(currents=src, legs={})
allu = []
for leg in LEGS:
    us = mir[leg]
    drops = [-v[u['src']] for u in us]
    allu += drops
    rs = [reff('vdda', u['src'], 'vdda') for u in us]
    rg = [reff('pbias', u['gate'], 'pbias') for u in us]
    rc = [reff('pcasc', c['gate'], 'pcasc') for c in cas.get(leg, [])]
    dnet = 'xl_%s.d' % leg
    rd = None
    if dnet in RN and cas.get(leg):
        idx, _ = network(dnet)
        dr = [u['drain'] for u in us if u['drain'] in idx]
        cs = [c['src'] for c in cas[leg] if c['src'] in idx]
        if dr and cs:
            # all mirror drains shorted -> all cascode sources shorted (unit currents in, out)
            vv = solve(dnet, cs[0], {**{n: -I_LEG[leg] / len(dr) for n in dr}, **{n: I_LEG[leg] / len(cs) for n in cs[1:]}})
            rd = max(vv[n] for n in dr) / I_LEG[leg]
    out['legs'][leg] = dict(units=len(us), unit_x_um=[round(u['x'], 2) for u in us],
                            source_drop_uV=[round(x * 1e6, 3) for x in drops], source_drop_mean_uV=round(sum(drops) / len(drops) * 1e6, 3),
                            r_vdda_pin_to_source_ohm=[round(x, 2) for x in rs], r_pbias_pin_to_gate_ohm=[round(x, 2) for x in rg],
                            r_pcasc_pin_to_gate_ohm=[round(x, 2) for x in rc], gate_drop_dc_uV=0.0,
                            r_mirror_drain_to_cascode_source_ohm=round(rd, 2) if rd is not None else None)
m = sum(allu) / len(allu)
out['source_drop_all_units_uV'] = dict(min=round(min(allu) * 1e6, 3), mean=round(m * 1e6, 3), max=round(max(allu) * 1e6, 3),
                                       spread=round((max(allu) - min(allu)) * 1e6, 3))
json.dump(out, open(os.path.join(PEX, 'pex_paths.json'), 'w'), indent=1)
print(json.dumps(out, indent=1))
