#!/usr/bin/env python3
"""T2n (layout B8, D25): decoupling calibration netlists. Adds ideal capacitors from the slice reference port nodes
(vref__p<k>, vrefl__p<k> tokens of the Xslice_a / Xslice_b lines) to the top-level vss in every top subckt of an
extracted r1_adc netlist (r1_adc_lay, r1_adc_lay_pr, r1_adc_lay_sar). Diagnostic only: it sizes the local decoupling
of netlist revision 6 before it is drawn (README "Layout B8", decoupling sizing).
usage: make_cal_netlist.py <in.spice> <out.spice> <C_vref per slice, pF> <C_vrefl per slice, pF>
The capacitance of one net is split equally over its port nodes of that slice."""
import re, sys
src, out, cv, cl = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
L = open(src).read().split('\n')
top, n_add = False, 0
for i, ln in enumerate(L):
    if re.match(r'\.subckt r1_adc_lay(_pr|_sar)? ', ln):
        top = True
    elif ln.startswith('.ends'):
        top = False
    elif top and re.match(r'Xslice_[ab] ', ln):
        sl = ln[7]
        t = ln.split(' ')
        pv = [x for x in t if re.fullmatch(r'vref__p\d+', x)]
        pl = [x for x in t if re.fullmatch(r'vrefl__p\d+', x)]
        assert pv and pl, (sl, pv, pl)
        add = []
        for nets, c, tag in ((pv, cv, 'v'), (pl, cl, 'l')):
            if c > 0:
                for x in nets:
                    add.append('Ccal%s_%s_%s %s vss %.6gp' % (tag, sl, x, x, c / len(nets)))
        L[i] = '\n'.join([ln] + add)
        n_add += len(add)
hdr = '* %s: %s + ideal calibration decoupling %.4g pF (vref) / %.4g pF (vrefl) per slice at the slice ports ' \
      '(sim/post/b8/make_cal_netlist.py; diagnostic only)' % (out.split('/')[-1], src.split('/')[-1], cv, cl)
open(out, 'w').write(hdr + '\n' + '\n'.join(L))
print(out, 'capacitors added', n_add)
