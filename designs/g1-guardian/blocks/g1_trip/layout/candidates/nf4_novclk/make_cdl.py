#!/usr/bin/env python3
"""r4 candidate nf4_novclk: LVS reference of the candidate macro from the r3 macro CDL.
  python3 make_cdl.py <g1_trip_nf4_lvs.cdl> <out.cdl>
Edits (asserted, nothing else changes):
  - first line: a new comment line naming this candidate (the r3 comment lines stay);
  - in .subckt g1_trip:  XCLKI clk cmp_clk_n VDD VSS g1_inv  ->  XNOV clk cmp_clk_s cmp_clk_n VDD VSS g1_novclk
                         XCS icmp vth_soft clk ...           ->  XCS icmp vth_soft cmp_clk_s ...
  - the subckt g1_novclk of layout/novclk.py (CDL style) is appended after the last .ends of the g1_trip source.
g1_inv stays (the DAC level shifters use it)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
import novclk  # noqa: E402
src, dst = sys.argv[1:3]
L = open(src).read().split('\n')
old_i = 'XCLKI clk cmp_clk_n VDD VSS g1_inv'
old_s = 'XCS icmp vth_soft clk cmp_soft cmp_soft_n VDD VSS g1_cmp'
assert L.count(old_i) == 1 and L.count(old_s) == 1
L[L.index(old_i)] = 'XNOV clk cmp_clk_s cmp_clk_n VDD VSS g1_novclk'
L[L.index(old_s)] = 'XCS icmp vth_soft cmp_clk_s cmp_soft cmp_soft_n VDD VSS g1_cmp'
end = [i for i, l in enumerate(L) if l.strip() == '* END_SOURCE g1_trip']
ins = end[0] if end else max(i for i, l in enumerate(L) if l.lower().startswith('.ends')) + 1
L[ins:ins] = novclk.lines('cdl')
hdr = '* r4 candidate nf4_novclk: r3 NF4 TRIP CDL with XCLKI replaced by the non-overlap clock generator g1_novclk (make_cdl.py)'
open(dst, 'w').write('\n'.join([hdr] + L))
print('wrote', dst)
