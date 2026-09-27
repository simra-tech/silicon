#!/usr/bin/env python3
"""r4 candidate nf4_novclk: chip CDLs for g1_chip_top_1414_r4 from the r3 ones, with exactly the macro edit of
make_cdl.py inside the g1_trip source block (BEGIN_SOURCE g1_trip .. END_SOURCE g1_trip):
  XCLKI clk cmp_clk_n VDD VSS g1_inv                         -> XNOV clk cmp_clk_s cmp_clk_n VDD VSS g1_novclk
  XCS icmp vth_soft clk cmp_soft cmp_soft_n VDD VSS g1_cmp   -> XCS icmp vth_soft cmp_clk_s ...
  + .subckt g1_novclk (layout/novclk.py, CDL style) before '* END_SOURCE g1_trip'
Applied to the canonical r3 CDL (header line replaced by an r4 header) and to r3's comparison-only projection
(the canonical minus one LevelDown dummy MP0 line, digital-eco-r3cand2-20260926/cdl/comparison_only.cdl), which
flatten_reference.rb then flattens into the projected reference. Every other line is asserted byte-identical.
  python3 make_chip_cdl.py <in.cdl> <out.cdl> [header]"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
import novclk  # noqa: E402
src, dst = sys.argv[1:3]
hdr = sys.argv[3] if len(sys.argv) > 3 else None
L = open(src).read().split('\n')
b = L.index('* BEGIN_SOURCE g1_trip'); e = L.index('* END_SOURCE g1_trip')
assert L.count('* BEGIN_SOURCE g1_trip') == 1 and L.count('* END_SOURCE g1_trip') == 1
old_i = 'XCLKI clk cmp_clk_n VDD VSS g1_inv'
old_s = 'XCS icmp vth_soft clk cmp_soft cmp_soft_n VDD VSS g1_cmp'
assert L.count(old_i) == 1 and L.count(old_s) == 1 and b < L.index(old_i) < e and b < L.index(old_s) < e
assert not any('g1_novclk' in l for l in L)
M = list(L)
M[M.index(old_i)] = 'XNOV clk cmp_clk_s cmp_clk_n VDD VSS g1_novclk'
M[M.index(old_s)] = 'XCS icmp vth_soft cmp_clk_s cmp_soft cmp_soft_n VDD VSS g1_cmp'
new = novclk.lines('cdl')
M[e:e] = new
if hdr is not None:
    assert L[0].startswith('* g1_chip_top_1414_r3')
    M[0] = hdr
# control: removing the inserted block and undoing the two edits gives the input back
C = M[:e] + M[e + len(new):]
C[C.index('XNOV clk cmp_clk_s cmp_clk_n VDD VSS g1_novclk')] = old_i
C[C.index('XCS icmp vth_soft cmp_clk_s cmp_soft cmp_soft_n VDD VSS g1_cmp')] = old_s
if hdr is not None:
    C[0] = L[0]
assert C == L
open(dst, 'w').write('\n'.join(M))
print('wrote', dst, 'lines', len(L), '->', len(M))
