#!/usr/bin/env python3
"""Summary of the parasitic capacitances in a post-layout netlist written by make_pex_netlist.py:
total capacitance per net for the named nets and the comparator input-pair drains (found from the
12/0.34 input devices: the drain is the source/drain node that is not the common tail), and the
couplings that matter for the comparator symmetry.

  python3 pex_summary.py g1_trip_pex.spice > pex_summary.txt
"""
import re
import sys


def val(s):
    m = re.match(r'([0-9.eE+-]+)([afpnum]?)', s)
    return float(m.group(1)) * {'a': 1e-18, 'f': 1e-15, 'p': 1e-12, 'n': 1e-9, 'u': 1e-6, 'm': 1e-3, '': 1.0}[m.group(2)] / 1e-15


def main():
    src = sys.argv[1]
    tot, pair, mos = {}, {}, []
    for ln in open(src):
        t = ln.split()
        if not t:
            continue
        if t[0].startswith('C'):
            a, b, v = t[1], t[2], val(t[3])
            tot[a] = tot.get(a, 0.0) + v
            tot[b] = tot.get(b, 0.0) + v
            k = tuple(sorted((a, b)))
            pair[k] = pair.get(k, 0.0) + v
        elif t[0].startswith('XM'):
            mos.append(t)
    print('# %s: %d parasitic capacitor entries, %d nets with parasitics, %d MOS' % (src, sum(1 for _ in pair), len(tot), len(mos)))
    print('# total parasitic capacitance per net (fF), named nets:')
    for n in ['isense', 'icmp', 'vref', 'vth_soft', 'vth_hard', 'cmp_clk', 'cmp_clk_n', 'cmp_soft', 'cmp_hard', 'vdd', 'vdda', 'vss']:
        print('%-10s %8.2f' % (n, tot.get(n, 0.0)))
    top = sorted(tot.items(), key=lambda kv: -kv[1])[:12]
    print('# largest totals:')
    for n, v in top:
        print('%-10s %8.2f' % (n, v))
    # comparator input pairs: the 12/0.34 devices (w=6u l=0.34u, two fingers each); the tail of a
    # comparator is the node its icmp devices share with its vth_* devices, the drain the other node
    dev = []
    for t in mos:
        d, g, s, b = t[1:5]
        pd = dict(p.split('=') for p in t[6:] if '=' in p)
        if pd.get('l') == '0.34u':
            dev.append((g, {d, s}))
    for cmpname, gn in (('soft', 'vth_soft'), ('hard', 'vth_hard')):
        nodes_n = set().union(*[ds for g, ds in dev if g == gn]) if any(g == gn for g, _ in dev) else set()
        nodes_p = set().union(*[ds for g, ds in dev if g == 'icmp']) if any(g == 'icmp' for g, _ in dev) else set()
        tail = nodes_n & nodes_p
        xq = nodes_n - tail
        xp = set().union(*[ds for g, ds in dev if g == 'icmp' and ds & tail]) - tail if tail else set()
        print('# comparator %s: tail %s, drains inp-side %s, inn-side %s' % (cmpname, sorted(tail), sorted(xp), sorted(xq)))
        for name, nodes in (('xp', xp), ('xq', xq)):
            for n in sorted(nodes):
                c_clk = sum(v for (a, b), v in pair.items() if n in (a, b) and ('cmp_clk' in (a, b) or 'cmp_clk_n' in (a, b)))
                print('  %s %-8s total %6.2f fF, to clock %5.2f fF' % (name, n, tot.get(n, 0.0), c_clk))


if __name__ == '__main__':
    main()
