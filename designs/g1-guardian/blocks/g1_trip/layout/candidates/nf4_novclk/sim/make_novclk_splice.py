#!/usr/bin/env python3
"""r4 candidate nf4_novclk, Gate 1: splice the schematic non-overlap clock generator into the r3 TRIP extraction.
Input: sim/postlayout/g1_trip_nf4_pex.spice (the r3 TRIP macro, kpex 2.5D CC). Edits (all asserted):
  - the extracted clock inverter XCLKI (XM1141 nmos, XM1234 pmos; gate cmp_clk, drain cmp_clk_n) is removed;
  - the soft (NF4) comparator's clock devices (tail XM1110-1113, precharge XM1226-1229) move from cmp_clk to the
    new net cmp_clk_s (as in review/redteam-20260927/trip_path/make_nov_variant.py);
  - the hard comparator's clock devices (XM1130-1133, XM1239-1242) stay on the extracted net cmp_clk_n, which keeps
    its wiring capacitance and is now driven by the generator's NAND output;
  - XNOV cmp_clk cmp_clk_s cmp_clk_n vdd vss g1_novclk is added; the generator subckt (<gen>) is written before
    the g1_trip subckt. The cmp_clk wiring capacitance stays on the pin net.
  python3 make_novclk_splice.py <pex.spice> <gen.spice> <out.spice>"""
import sys
src, gen, dst = sys.argv[1:4]
soft = {'XM1110', 'XM1111', 'XM1112', 'XM1113', 'XM1226', 'XM1227', 'XM1228', 'XM1229'}
hard = {'XM1130', 'XM1131', 'XM1132', 'XM1133', 'XM1239', 'XM1240', 'XM1241', 'XM1242'}
inv = {'XM1141': 'sg13_lv_nmos', 'XM1234': 'sg13_lv_pmos'}
lines = open(src).read().rstrip('\n').split('\n')
assert lines[-1] == '.ends'
out, ns, nh, ni = [], 0, 0, 0
for ln in lines[:-1]:
    t = ln.split()
    if t and t[0] in inv:
        assert t[1:3] == ['cmp_clk_n', 'cmp_clk'] and t[5] == inv[t[0]], ln
        ni += 1
        continue
    if t and t[0] in soft:
        assert t[2] == 'cmp_clk', ln; t[2] = 'cmp_clk_s'; ln = ' '.join(t); ns += 1
    elif t and t[0] in hard:
        assert t[2] == 'cmp_clk_n', ln; nh += 1
    out.append(ln)
assert (ns, nh, ni) == (8, 8, 2), (ns, nh, ni)
g = open(gen).read().rstrip('\n')
out += ['* make_novclk_splice.py: generator replaces XCLKI', 'XNOV cmp_clk cmp_clk_s cmp_clk_n vdd vss g1_novclk', '.ends']
hdr = [l for l in out if l.startswith('*')][:2]
body = [l for l in out if not (l in hdr and out.index(l) < 2)]
open(dst, 'w').write('\n'.join(hdr + ['* spliced by make_novclk_splice.py with ' + gen.split('/')[-1], g] + body) + '\n')
print('wrote', dst)
