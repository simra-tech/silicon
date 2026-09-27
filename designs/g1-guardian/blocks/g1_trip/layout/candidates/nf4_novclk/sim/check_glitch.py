#!/usr/bin/env python3
"""Glitch check on gen_sweep.py waveforms (<name>.dat: t,clk t,dly t,cks t,ckh t,ckr), clk edges at 20 + k*100 ns.
For t in 150..460 ns: number of VDD/2 crossings of dly, cks, ckh (expected 2 rises + 2 falls... = 3 or 4 by window
position, equal to clk's own count); and the excursion from the rail of the nodes that must hold across a clk edge:
  dly  within [edge - 0.3 ns, edge + 1.0 ns] of both clk edges (the delayed copy has not switched yet)
  cks  at the clk falling edge (OR(0, dly=1) stays high) ;  ckh at the clk rising edge (NAND(1, dly=0) stays high)
  python3 check_glitch.py <vdd> <dat...>"""
import sys
import numpy as np
vdd = float(sys.argv[1])
for fn in sys.argv[2:]:
    d = np.loadtxt(fn)
    t = d[:, 0]; clk, dly, cks, ckh = d[:, 1], d[:, 3], d[:, 5], d[:, 7]
    m = (t > 150e-9) & (t < 460e-9)
    def nx(v):
        s = v[m] > vdd / 2
        return int(np.sum(s[1:] != s[:-1]))
    rise = [20e-9 + k * 200e-9 for k in range(3)]
    fall = [120e-9 + k * 200e-9 for k in range(3)]
    def exc(v, edges, level):
        w = np.zeros_like(t, bool)
        for e in edges:
            if e < 150e-9: continue
            w |= (t > e - 0.3e-9) & (t < e + 1.0e-9)
        return float(np.max(np.abs(v[w] - level))) if w.any() else float('nan')
    print('%-40s crossings clk %d dly %d cks %d ckh %d | hold excursion: dly@rise %.3f dly@fall %.3f cks@fall %.3f ckh@rise %.3f V'
          % (fn.split('/')[-1], nx(clk), nx(dly), nx(cks), nx(ckh),
             exc(dly, rise, 0.0), exc(dly, fall, vdd), exc(cks, fall, vdd), exc(ckh, rise, vdd)))
