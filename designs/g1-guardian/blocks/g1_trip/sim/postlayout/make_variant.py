#!/usr/bin/env python3
"""Derived copies of a post-layout g1_trip netlist for simulation-only what-if studies (the extracted
netlist itself is not modified; the copy gets additions before .ends).

  python3 make_variant.py <in.spice> <out.spice> caps=<K>      the three hold capacitors (XCHS vth_soft,
      XCHH vth_hard, XCH icmp; 26x26 um cap_cmim each) get K-1 identical cap_cmim in parallel (K x value)
  python3 make_variant.py <in.spice> <out.spice> hclk=<D ns>   the hard comparator's clock net cmp_clk_n is
      cut from the clock inverter (its two drains move to cmp_clk_n_inv) and driven by an ideal source:
      the inverse of the testbench clock pulse(0 VDD 20n 0.2n 0.2n 99.8n 200n) delayed by D ns (D = 0 is the
      ideal-clock reference); the net keeps its extracted parasitic capacitances
"""
import sys

src, dst, opt = sys.argv[1:4]
key, val = opt.split('=')
lines = open(src).read().rstrip('\n').split('\n')
assert lines[-1] == '.ends'
body, add = lines[:-1], []
if key == 'caps':
    k = int(val)
    add = ['* make_variant.py caps=%d: hold capacitors x%d' % (k, k)] + [
        'X%s_x %s vss cap_cmim w=26u l=26u m=%d' % (n, node, k - 1)
        for n, node in (('CHS', 'vth_soft'), ('CHH', 'vth_hard'), ('CH', 'icmp'))]
elif key == 'hclk':
    d = float(val)
    out, ninv = [], 0
    for ln in body:
        t = ln.split()
        if t and t[0].startswith('XM') and t[2] == 'cmp_clk' and t[1] == 'cmp_clk_n':
            t[1] = 'cmp_clk_n_inv'; ninv += 1; ln = ' '.join(t)
        out.append(ln)
    assert ninv == 2, ninv
    body = out
    add = ['* make_variant.py hclk=%g: hard comparator clock from an ideal source, delayed %g ns' % (d, d),
           'Vhclk cmp_clk_n vss pulse({VDD} 0 %gn 0.2n 0.2n 99.8n 200n)' % (20 + d)]
open(dst, 'w').write('\n'.join(body + add + ['.ends']) + '\n')
print('wrote', dst)
