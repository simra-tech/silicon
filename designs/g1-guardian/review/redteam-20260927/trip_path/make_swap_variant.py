#!/usr/bin/env python3
"""Red-team 2026-09-27: simulation-only what-if on g1_trip_nf4_pex.spice. Swap the strobe phases of the two
comparators: the soft (NF4) comparator's clock devices (gates on cmp_clk: tail XM1110-1113, precharge
XM1226-1229) move to cmp_clk_n and the hard (regenpair4) comparator's clock devices (XM1130-1133,
XM1239-1242) move to cmp_clk. The clock inverter (XM1141/XM1234) is unchanged. Parasitic capacitances stay on
the extracted nets (both comparators have identical clock-device sizes, so the inverter load is unchanged).
  python3 make_swap_variant.py <in> <out>"""
import sys
src, dst = sys.argv[1:3]
soft = {'XM1110', 'XM1111', 'XM1112', 'XM1113', 'XM1226', 'XM1227', 'XM1228', 'XM1229'}
hard = {'XM1130', 'XM1131', 'XM1132', 'XM1133', 'XM1239', 'XM1240', 'XM1241', 'XM1242'}
out, n = [], 0
for ln in open(src).read().split('\n'):
    t = ln.split()
    if t and t[0] in soft:
        assert t[2] == 'cmp_clk', ln; t[2] = 'cmp_clk_n'; ln = ' '.join(t); n += 1
    elif t and t[0] in hard:
        assert t[2] == 'cmp_clk_n', ln; t[2] = 'cmp_clk'; ln = ' '.join(t); n += 1
    out.append(ln)
assert n == 16, n
open(dst, 'w').write('\n'.join(out))
print('wrote', dst, n, 'gates moved')
