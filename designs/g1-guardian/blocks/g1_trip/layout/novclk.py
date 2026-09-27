#!/usr/bin/env python3
"""r4 candidate (nf4_novclk): non-overlapping comparator clock generator that replaces the clock inverter XCLKI of
G1_TRIP. Single source of the device list for the schematic netlist (ngspice), the LVS CDL and the layout
(gen_trip_layout.py what=novclk).

  cmp_clk -> 3 inverters with long-L devices (n 0.3/2.5, p 0.6/2.5) -> sharpening inverter -> dly (cmp_clk delayed)
  cks = OR(cmp_clk, dly)  (NOR2 + inverter)  -> soft comparator clock: rises with cmp_clk, falls D after it
  ckh = NAND(cmp_clk, dly)                    -> hard comparator clock: rises when cmp_clk falls, falls D after
                                                 cmp_clk rises
so each comparator evaluates on an undelayed cmp_clk edge and resets D later, after the other comparator's
decision. Non-overlap window (fall/rise edge, ns): schematic with lumped clock loads (sim/gen_sweep.py) tt 6.49/5.67,
ss/1.08 V/-40 C 6.74/5.85, ff/1.32 V/125 C 7.17/6.39; on the kpex extraction of the drawn cell (sim/win_pex.py)
tt 9.37/7.86, ss/-40 C 10.31/8.41, ff/125 C 9.90/8.60. See candidates/nf4_novclk/README.md.

  python3 novclk.py spice <out>     ngspice subckt (PDK devices as X instances)
  python3 novclk.py cdl <out>       CDL subckt (M instances, as in g1_trip_nf4_lvs.cdl)"""
import sys

L_LONG = 2.5
# name, kind, W (um), L (um), D, G, S   (bulk: vss for n, vdd for p). The soft-clock inverter is two parallel halves
# so that the layout rows stay 2 um (PMOS) / 1 um (NMOS) tall.
DEVICES = [
    ('MIN1', 'n', 1.0, 0.13, 'cks', 'norb', 'vss'), ('MIN2', 'n', 1.0, 0.13, 'cks', 'norb', 'vss'),
    ('MON1', 'n', 0.5, 0.13, 'norb', 'clk', 'vss'), ('MON2', 'n', 0.5, 0.13, 'norb', 'dly', 'vss'),
    ('MDN1', 'n', 0.3, L_LONG, 'dl1', 'clk', 'vss'), ('MDN2', 'n', 0.3, L_LONG, 'dl2', 'dl1', 'vss'),
    ('MDN3', 'n', 0.3, L_LONG, 'dl3', 'dl2', 'vss'), ('MSN', 'n', 0.5, 0.13, 'dly', 'dl3', 'vss'),
    ('MAN2', 'n', 1.0, 0.13, 'nand1', 'dly', 'vss'), ('MAN1', 'n', 1.0, 0.13, 'ckh', 'clk', 'nand1'),
    ('MIP1', 'p', 2.0, 0.13, 'cks', 'norb', 'vdd'), ('MIP2', 'p', 2.0, 0.13, 'cks', 'norb', 'vdd'),
    ('MOP1', 'p', 2.0, 0.13, 'nor1', 'clk', 'vdd'), ('MOP2', 'p', 2.0, 0.13, 'norb', 'dly', 'nor1'),
    ('MDP1', 'p', 0.6, L_LONG, 'dl1', 'clk', 'vdd'), ('MDP2', 'p', 0.6, L_LONG, 'dl2', 'dl1', 'vdd'),
    ('MDP3', 'p', 0.6, L_LONG, 'dl3', 'dl2', 'vdd'), ('MSP', 'p', 1.0, 0.13, 'dly', 'dl3', 'vdd'),
    ('MAP1', 'p', 1.5, 0.13, 'ckh', 'clk', 'vdd'), ('MAP2', 'p', 1.5, 0.13, 'ckh', 'dly', 'vdd'),
]
PORTS = ('clk', 'cks', 'ckh', 'vdd', 'vss')


def lines(style):
    out = ['.subckt g1_novclk ' + ' '.join(PORTS)]
    for name, k, w, l, d, g, s in DEVICES:
        b = 'vss' if k == 'n' else 'vdd'
        dev = 'sg13_lv_nmos' if k == 'n' else 'sg13_lv_pmos'
        if style == 'spice':
            out.append('X%s %s %s %s %s %s w=%gu l=%gu ng=1 m=1' % (name, d, g, s, b, dev, w, l))
        else:
            out.append('%s %s %s %s %s %s w=%gu l=%gu m=1' % (name, d, g, s, b, dev, w, l))
    out.append('.ends' if style == 'cdl' else '.ends g1_novclk')
    return out


if __name__ == '__main__':
    style, path = sys.argv[1], sys.argv[2]
    hdr = '* g1_novclk (r4 candidate nf4_novclk), written by layout/novclk.py %s' % style
    open(path, 'w').write('\n'.join([hdr] + lines(style)) + '\n')
