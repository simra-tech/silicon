#!/usr/bin/env python3
"""Coupling between the auto-zero clock nets and the sensitive differential pairs of r1_isense_ch, from kpex 2.5D CC
netlists (host python3, standard library). Layout b, 2026-10-21.

  python3 coupling_table.py <label>=<kpex *_k25d_pex_netlist.spice> [...]  > table.md

Per clock net and pair: C to the p side, C to the n side, difference dC (fF). For the floating hold nodes (h1/h2) the
table also gives the charge-injection difference dV = sum dC x dV_clock / C_hold (dV_clock: the step of the clock net at the end of AZ) at the hold node (C_hold = 1.01 pF, cap_cmim
26 x 26 um at 1.5 fF/um2, estimated) and the input-referred estimate dV x gm_aux/gm1 (1/12, netlist comment, estimated).
The other pairs are driven nodes; their dC is listed for the symmetry record only."""
import sys, collections
U = {'a': 1e-3, 'f': 1.0, 'p': 1e3}
# clock nets and their step at the end of the auto-zero (V): az/azh fall, the complements rise; in the level shifters
# node b follows the input, node a and the input complement inb go the other way
CLK = [('az', -3.3), ('azb', 3.3), ('azh', -3.3), ('azhb', 3.3), ('az_lv', -1.2), ('azh_lv', -1.2),
       ('xls1_a', 3.3), ('xls1_b', -3.3), ('xls1_inb', 1.2), ('xls2_a', 3.3), ('xls2_b', -3.3), ('xls2_inb', 1.2)]
PAIRS = [('h1', 'h2'), ('xh1', 'xh2'), ('x1a', 'x1b'), ('sa', 'sb'), ('f1', 'f2'), ('outp', 'outn'), ('rfoa', 'rfob')]
CH, AUX = 1.01e3, 1 / 12.0      # fF, ratio


def load(f):
    C = collections.defaultdict(float)
    for l in open(f):
        if not l.startswith('Cext'):
            continue
        a, b, v = l.split()[1:4]
        a = a.replace('\\', ''); b = b.replace('\\', '')
        x = float(v[:-1]) * U[v[-1]] if v[-1] in U else float(v) * 1e15
        C[frozenset((a, b))] += x
    return C


runs = [(a.split('=', 1)[0], load(a.split('=', 1)[1])) for a in sys.argv[1:]]
hdr = '| Clock net (swing) | Pair | ' + ' | '.join('%s C_p / C_n, dC (fF)' % lab for lab, _ in runs) + ' |'
print(hdr)
print('|' + ' --- |' * (2 + len(runs)))
worst = {lab: 0.0 for lab, _ in runs}
for clk, sw in CLK:
    for p, n in PAIRS:
        cells, show = [], False
        for lab, C in runs:
            cp, cn = C.get(frozenset((clk, p)), 0.0), C.get(frozenset((clk, n)), 0.0)
            d = cp - cn
            worst[lab] = max(worst[lab], abs(d))
            show = show or abs(d) >= 0.01 or cp >= 0.05 or cn >= 0.05
            cells.append('%.3f / %.3f, **%+.3f**' % (cp, cn, d))
        if show:
            print('| `%s` (%+.1f V) | `%s/%s` | %s |' % (clk, sw, p, n, ' | '.join(cells)))
print()
print('| Hold node h1 - h2, sum over the clock nets | ' + ' | '.join(lab for lab, _ in runs) + ' |')
print('| --- |' + ' --- |' * len(runs))
for what in ('sum of abs(dC) (fF)', 'sum dC x dV_clock (fC)', 'dV at the hold node (mV, estimated)', 'input referred (uV, estimated)'):
    cells = []
    for lab, C in runs:
        sa = sum(abs(C.get(frozenset((c, 'h1')), 0) - C.get(frozenset((c, 'h2')), 0)) for c, _ in CLK)
        q = sum((C.get(frozenset((c, 'h1')), 0) - C.get(frozenset((c, 'h2')), 0)) * sw for c, sw in CLK)
        v = {'sum of abs(dC) (fF)': '%.3f' % sa, 'sum dC x dV_clock (fC)': '%+.3f' % q,
             'dV at the hold node (mV, estimated)': '%+.3f' % (q / CH * 1e3),
             'input referred (uV, estimated)': '%+.1f' % (q / CH * 1e6 * AUX)}[what]
        cells.append(v)
    print('| %s | %s |' % (what, ' | '.join(cells)))
print()
print('Largest per-pair |dC| over all clock nets and pairs: ' + ', '.join('%s %.3f fF' % (l, w) for l, w in worst.items()))
