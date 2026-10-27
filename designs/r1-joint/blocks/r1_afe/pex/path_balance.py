#!/usr/bin/env python3
"""Layout E7 (track T3k): wiring balance of the stage-1 input-current path per TG port type (N / P), from the Rw* wire
resistors of a pex_rc_build.py netlist (R-only or RC view).

  python3 pex/path_balance.py <r1_afe_post_rc.spice>   -> JSON on stdout

Input path of one side (s = p: inp, xs1p_a<k>, x1p; s = n: inn, xs1n_a<k>, x1n): pin node of inp/inn -> inp wiring ->
unit resistor U<k> (ideal 40 kOhm from its inp port to the main node of a<k>) -> a<k> wiring -> TG device (ideal resistor
R_N from the a<k> N port to its x1 port, R_P from the a<k> P port to its x1 port) -> x1 wiring -> x1 main node (OTA1 gate,
unit UF head). Feedback path: x1 main -> UF (40 kOhm) -> af wiring -> TGF device -> m1 wiring -> m1 main node (OTA1
output); the m1 ports of stage 2 and of the C_F plates carry no DC current in this model.
Wiring R of a path = R(path) - R(path with all wiring shorted). Cases: N only (R_N = 2k, R_P open), P only (R_P = 2k,
R_N open), mixed (R_N = R_P = 2k). Per-unit 'a' table: a-net main -> N port and main -> P port (other ports open).
Units: x32 = U1..U8 in parallel, x1 = U1 only. Difference = p side - n side in Ohm (input path: the parallel value).
"""
import collections, json, re, sys
import numpy as np

F = sys.argv[1]
el = []
sub = None
for l in open(F):
    if l.lower().startswith('.subckt'):
        sub = l.split()[1]
    if sub == 'r1_afe_ch' and l.startswith('Rw'):
        t = l.split(); el.append((t[1], t[2], float(t[3])))
devs = {}
sub = None
for l in open(F):
    if l.lower().startswith('.subckt'):
        sub = l.split()[1]
    if sub == 'r1_afe_ch' and re.match(r'Xxs1[pn]_xt(\d|f)_x[np] ', l):
        t = l.split(); devs[t[0]] = (t[1], t[3])   # (a-side node, x-side node)
def base(n):
    return n.split('__')[0]
bynet = collections.defaultdict(list)
for a, b, r in el:
    bynet[base(a)].append((a, b, r))

def solve(edges, src, gnd):
    nodes = sorted({n for a, b, _ in edges for n in (a, b)} | {src, gnd})
    ix = {n: i for i, n in enumerate(nodes)}
    G = np.zeros((len(nodes), len(nodes)))
    for a, b, r in edges:
        g = 1.0 / r; i, j = ix[a], ix[b]
        G[i, i] += g; G[j, j] += g; G[i, j] -= g; G[j, i] -= g
    keep = [i for i in range(len(nodes)) if nodes[i] != gnd]
    Gk = G[np.ix_(keep, keep)] + 1e-15 * np.eye(len(keep))
    I = np.zeros(len(keep)); I[keep.index(ix[src])] = 1.0
    v = np.linalg.solve(Gk, I)
    return v[keep.index(ix[src])]

def path(side, units, rn, rp, wire=True, fb=False):
    s = side
    E = []
    W = 1.0 if wire else 1e-6
    if not fb:
        nets = ['inp' if s == 'p' else 'inn', 'x1' + s] + ['xs1%s_a%d' % (s, k) for k in units]
        for n in nets:
            E += [(a, b, r * W) for a, b, r in bynet[n]]
        inn = 'inp' if s == 'p' else 'inn'
        for k in units:
            E.append(('%s__p%d' % (inn, k - 1) if k > 1 or True else inn, 'xs1%s_a%d' % (s, k), 40e3))
            dn, dp = devs['Xxs1%s_xt%d_xn' % (s, k)], devs['Xxs1%s_xt%d_xp' % (s, k)]
            if rn: E.append((dn[0], dn[1], rn))
            if rp: E.append((dp[0], dp[1], rp))
        return solve(E, inn, 'x1' + s)
    m1 = 'm1n' if s == 'p' else 'm1p'
    for n in ['x1' + s, 'xs1%s_af' % s, m1]:
        E += [(a, b, r * W) for a, b, r in bynet[n]]
    E.append(('x1' + s, 'xs1%s_af' % s, 40e3))
    dn, dp = devs['Xxs1%s_xtf_xn' % s], devs['Xxs1%s_xtf_xp' % s]
    if rn: E.append((dn[0], dn[1], rn))
    if rp: E.append((dp[0], dp[1], rp))
    return solve(E, 'x1' + s, m1)

CASES = {'N': (2e3, None), 'P': (None, 2e3), 'NP': (2e3, 2e3)}
out = {'netlist_rw': len(el)}
for name, units in (('x32', list(range(1, 9))), ('x1', [1])):
    row = {}
    for c, (rn, rp) in CASES.items():
        w = {s: path(s, units, rn, rp) - path(s, units, rn, rp, wire=False) for s in 'pn'}
        row[c] = dict(p=round(w['p'], 3), n=round(w['n'], 3), d=round(w['p'] - w['n'], 3))
    out['in_' + name] = row
row = {}
for c, (rn, rp) in CASES.items():
    w = {s: path(s, None, rn, rp, fb=True) - path(s, None, rn, rp, wire=False, fb=True) for s in 'pn'}
    row[c] = dict(p=round(w['p'], 3), n=round(w['n'], 3), d=round(w['p'] - w['n'], 3))
out['fb'] = row
# per-unit series wiring with one device type (unit alone; a net + x1 net + inp share), N and P, p - n
units = {}
for k in range(1, 9):
    u = {}
    for c, (rn, rp) in (('N', (2e3, None)), ('P', (None, 2e3))):
        w = {s: path(s, [k], rn, rp) - path(s, [k], rn, rp, wire=False) for s in 'pn'}
        u[c] = dict(p=round(w['p'], 2), n=round(w['n'], 2), d=round(w['p'] - w['n'], 2))
    # a-net part alone
    for s in 'pn':
        net = 'xs1%s_a%d' % (s, k)
        dn, dp = devs['Xxs1%s_xt%d_xn' % (s, k)][0], devs['Xxs1%s_xt%d_xp' % (s, k)][0]
        u['a_%s' % s] = dict(N=round(solve(bynet[net], dn, net), 2), P=round(solve(bynet[net], dp, net), 2))
    units[k] = u
out['units'] = units
# port table: self resistance main -> port (other ports open) per side, averaged over the 8 input units; P - N side diff
def selfr(net, node):
    return solve(bynet[net], node, net) if node != net else 0.0
ports = {}
for s in 'pn':
    x = 'x1' + s; inn = 'inp' if s == 'p' else 'inn'; m1 = 'm1n' if s == 'p' else 'm1p'; af = 'xs1%s_af' % s
    d = {}
    d['x1_N'] = np.mean([selfr(x, devs['Xxs1%s_xt%d_xn' % (s, k)][1]) for k in range(1, 9)])
    d['x1_P'] = np.mean([selfr(x, devs['Xxs1%s_xt%d_xp' % (s, k)][1]) for k in range(1, 9)])
    d['a_N'] = np.mean([selfr('xs1%s_a%d' % (s, k), devs['Xxs1%s_xt%d_xn' % (s, k)][0]) for k in range(1, 9)])
    d['a_P'] = np.mean([selfr('xs1%s_a%d' % (s, k), devs['Xxs1%s_xt%d_xp' % (s, k)][0]) for k in range(1, 9)])
    d['inp_ports'] = np.mean([selfr(inn, '%s__p%d' % (inn, k)) for k in range(8)])
    d['af_N'] = selfr(af, devs['Xxs1%s_xtf_xn' % s][0]); d['af_P'] = selfr(af, devs['Xxs1%s_xtf_xp' % s][0])
    d['m1_tgf_N'] = selfr(m1, devs['Xxs1%s_xtf_xn' % s][1]); d['m1_tgf_P'] = selfr(m1, devs['Xxs1%s_xtf_xp' % s][1])
    ports[s] = d
# x1 summing-node term (inside the loop): R_eff of x1 with the input current injected only at the N ports or only at
# the P ports of the conducting input TGs (equal shares), main node = OTA1 gate / UF head (x1_pair_r.py model, per type)
def x1eff(s, units, t):
    net = 'x1' + s
    nodes = sorted({n for a, b, _ in bynet[net] for n in (a, b)})
    ix = {n: i for i, n in enumerate(nodes)}
    G = np.zeros((len(nodes), len(nodes)))
    for a, b, r in bynet[net]:
        g = 1.0 / r; i, j = ix[a], ix[b]
        G[i, i] += g; G[j, j] += g; G[i, j] -= g; G[j, i] -= g
    keep = [i for i in range(len(nodes)) if nodes[i] != net]
    Z = np.linalg.inv(G[np.ix_(keep, keep)]); zi = {nodes[k]: q for q, k in enumerate(keep)}
    inj = {}
    for k in units:
        n_ = devs['Xxs1%s_xt%d_x%s' % (s, k, t)][1]
        inj[n_] = inj.get(n_, 0) + 1.0 / len(units)
    return sum(w * sum(Z[zi[n], zi[m]] * w2 for m, w2 in inj.items()) for n, w in inj.items())
out['x1_eff'] = {}
for nm, units in (('x32', list(range(1, 9))), ('x1', [1])):
    for t in 'np':
        a_, b_ = x1eff('p', units, t), x1eff('n', units, t)
        out['x1_eff']['%s_%s' % (nm, t.upper())] = dict(p=round(a_, 2), n=round(b_, 2), d=round(a_ - b_, 2))
out['ports'] = {k: dict(p=round(ports['p'][k], 2), n=round(ports['n'][k], 2), d=round(ports['p'][k] - ports['n'][k], 2)) for k in ports['p']}
print(json.dumps(out, indent=1))
