#!/usr/bin/env python3
"""tabulate the RESULT lines of gen_sweep.py decks: python3 tab.py <log...>"""
import sys
for fn in sorted(sys.argv[1:]):
    for l in open(fn):
        if not l.startswith('RESULT'): continue
        t = l.split(); d = dict(x.split('=') for x in t[2:])
        f = lambda k: float(d[k]) * 1e9
        print('%-30s W_fall %6.2f W_rise %6.2f | dly r/f %5.2f/%5.2f | eval-edge delay soft %.3f hard %.3f | tr/tf cks %.3f/%.3f ckh %.3f/%.3f XCLKI-ref %.3f/%.3f | swing cks %.3f..%.3f ckh %.3f..%.3f | Idd %.2f uA'
              % (t[1][4:], f('w_fall'), f('w_rise'), f('d_rise'), f('d_fall'), f('ev_soft'), f('ev_hard'), f('cks_tr'), f('cks_tf'),
                 f('ckh_tr'), f('ckh_tf'), f('ref_tr'), f('ref_tf'), float(d['cks_min']), float(d['cks_max']),
                 float(d['ckh_min']), float(d['ckh_max']), -float(d['idd']) * 1e6))
