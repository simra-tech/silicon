#!/usr/bin/env python3
"""Layout E5 (track T3): effective wiring resistance of the stage-1 summing nodes x1p / x1n in the input-current path,
from the Rw* elements of a pex_rc_build.py netlist and the port list of the layout generator (r1_afe_ports.json).
  python3 pex/x1_pair_r.py <r1_afe_post_rc.spice> <r1_afe_ports.json>   -> JSON on stdout
Model: the main node of x1p/x1n (port 0 = feedback-unit head XUF; the OTA1 gates and the probe sit there in the netlist)
is ground; every conducting TG injects its share of the input current at its NMOS and PMOS source ports (half each).
R_eff = sum(w_k V_k) / I, with x32 = all 8 TGs, x1 = TG1 only. Difference P - N in Ohm; the x32 DC offset is about
I_in * dR * (noise gain) with I_in = 31 uA at input CM 2.5 V (estimate)."""
import collections, json, sys
import numpy as np
F, PJ = sys.argv[1], sys.argv[2]
ports = json.load(open(PJ))['r1_afe_ch']
el = collections.defaultdict(list)
for l in open(F):
    if l.startswith('Rw'):
        _, a, b, r = l.split()
        el[a.split('__')[0]].append((a, b, float(r)))
out = {}
for side, net in (('p', 'x1p'), ('n', 'x1n')):
    plist = [p for p in ports if p['net'] == net]
    names = ['%s__p%d' % (net, i) for i in range(len(plist))]
    names[0] = net
    nodes = sorted({n for a, b, _ in el[net] for n in (a, b)})
    ix = {n: i for i, n in enumerate(nodes)}
    G = np.zeros((len(nodes), len(nodes)))
    for a, b, r in el[net]:
        g = 1.0 / r; i, j = ix[a], ix[b]
        G[i, i] += g; G[j, j] += g; G[i, j] -= g; G[j, i] -= g
    keep = [i for i in range(len(nodes)) if nodes[i] != net]
    Z = np.linalg.inv(G[np.ix_(keep, keep)]); zi = {nodes[k]: q for q, k in enumerate(keep)}
    tg = {}
    for nm, p in zip(names, plist):
        d = p['dev']
        if '_xt' in d and d.split('_')[1].startswith('xt') and d.split('_')[1] != 'xtf':
            tg.setdefault(int(d.split('_')[1][2:]), []).append(nm)
    def reff(units):
        inj = {n: 1.0 / (len(units) * len(tg[u])) for u in units for n in tg[u]}
        v = {n: sum(Z[zi[n], zi[m]] * w for m, w in inj.items()) for n in inj}
        return sum(inj[n] * v[n] for n in inj)
    out[net] = dict(ports=len(plist), main=plist[0]['dev'], r_x32=round(reff(sorted(tg)), 2), r_x1=round(reff([1]), 2),
                    per_tg={u: [round(float(Z[zi[n], zi[n]]), 1) for n in tg[u]] for u in sorted(tg)})
out['diff_p_minus_n'] = dict(r_x32=round(out['x1p']['r_x32'] - out['x1n']['r_x32'], 2), r_x1=round(out['x1p']['r_x1'] - out['x1n']['r_x1'], 2))
print(json.dumps(out, indent=1))
