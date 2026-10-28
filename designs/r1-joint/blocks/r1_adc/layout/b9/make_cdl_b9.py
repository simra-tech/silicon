#!/usr/bin/env python3
"""LVS reference of r1_adc layout B9 (revision-6 netlist + SAR sub-macro r1_adc_sar), T2o 2026-10-28, PLAN.md D28.

  python3 make_cdl_b9.py <b5 cdl> <revision-6 analog cdl> <out cdl>

<b5 cdl>: layout/r1_adc_lvs_b5.cdl (analog revision 5 + r1_adc_sar, layout/b5/make_cdl_b5.py).
<revision-6 analog cdl>: the CDL that r1_adc_layout.py -rd rev=B9 writes (r1_adc_netlist.py with SCHEM = 'r6').
Changes, the only ones: in subcircuit r1_adc the gates of Mxckg_xpd0 / Mxckg_xnd0 move from clk to vss
(r1_cmp6_clkgen), and Mxref_xmsfl_s1/_s2 and Mxref_xmibl_s1/_s2 are added (r1_refbuf6 msfl 24 / mibl 120, drawn as
three devices each). Check: the device lines of r1_adc in the result (without the SAR instance) equal those of the
revision-6 analog CDL, and the r1_adc_slice subcircuit is unchanged."""
import re
import sys

b5, r6, out = sys.argv[1:4]
B = open(b5).read().split('\n')
R6 = open(r6).read()
o, n = [], 0
for ln in B:
    if ln.startswith('Mxckg_xpd0 ') or ln.startswith('Mxckg_xnd0 '):
        t = ln.split(' ')
        assert t[2] == 'clk', ln
        t[2] = 'vss'; ln = ' '.join(t); n += 1
    o.append(ln)
    for dev in ('Mxref_xmsfl_s0 ', 'Mxref_xmibl_s0 '):
        if ln.startswith(dev):
            for k in (1, 2):
                o.append(ln.replace(dev, dev.replace('_s0 ', '_s%d ' % k), 1)); n += 1
assert n == 6, n
res = '\n'.join(o)


def sub(txt, name):
    m = re.search(r'^\.subckt %s .*?^\.ends' % name, txt, re.M | re.S | re.I)
    return m.group(0)


def mlines(s):
    return sorted(l for l in s.split('\n') if l.startswith(('M', 'C', 'R')))


assert mlines(sub(res, 'r1_adc')) == mlines(sub(R6, 'r1_adc')), 'r1_adc device lines differ from the revision-6 CDL'
assert sub(res, 'r1_adc_slice') == sub(R6, 'r1_adc_slice'), 'slice changed'
hdr = '* r1_adc_lvs_b9.cdl: layout/r1_adc_lvs_b5.cdl with the revision-6 changes (layout/b9/make_cdl_b9.py; T2o, D28)\n'
open(out, 'w').write(hdr + res)
print('wrote', out, 'changes', n)
