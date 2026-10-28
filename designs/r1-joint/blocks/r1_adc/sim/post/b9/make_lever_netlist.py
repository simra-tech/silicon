#!/usr/bin/env python3
"""make_lever_netlist.py <in.spice> <out.spice> <R_ohm> [node,node,...]
T2o (PLAN.md D28 item 4, 2026-10-28): what-if of the drift lever before the B9 layout. Adds one resistor of R_ohm from
each listed node of the slice subckt r1_adc_slice_post to its port node 'vdd' (default nodes vdd__p22..p25: the vdd
terminals of the r1_cmp4 integration capacitors xci1 / xci2 under the CDAC, extracted R to the port 74-138 Ohm in B7).
The added resistor models a Metal3 strap with a via stack from above. Nothing else changes."""
import sys
src, out, r = sys.argv[1], sys.argv[2], float(sys.argv[3])
nodes = sys.argv[4].split(',') if len(sys.argv) > 4 else ['vdd__p22', 'vdd__p23', 'vdd__p24', 'vdd__p25']
L = open(src).read().split('\n')
inside = False; done = False; R = []
for ln in L:
    if ln.startswith('.subckt r1_adc_slice_post '):
        inside = True
    if inside and ln.startswith('.ends'):
        R += ['Rlev%d %s vdd %g' % (k, n, r) for k, n in enumerate(nodes)]
        inside = False; done = True
    R.append(ln)
assert done
body = '\n'.join(R)
for n in nodes:
    assert (' %s ' % n) in body, n
hdr = '* %s: drift-lever what-if of %s: %s each tied to the slice port vdd by %g Ohm' % (
    out.split('/')[-1], src.split('/')[-1], ','.join(nodes), r)
open(out, 'w').write(hdr + '\n' + body)
print(hdr)
