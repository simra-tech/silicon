#!/usr/bin/env python3
"""Compare the pins of a LEF (written by the generator from the pin shapes) with the ports of the top subcircuit of the
LVS CDL, and print the edge of every pin. Needed because the PDK LVS runs with IGNORE_TOP_PORTS_MISMATCH (default),
so a missing or misnamed pin label is not an LVS error.   python3 check_pins.py <lef> <cdl> <subckt>   (host Python)"""
import re, sys
lef, cdl, sub = sys.argv[1:4]
t = open(lef).read()
w, h = map(float, re.search(r'SIZE ([\d.]+) BY ([\d.]+)', t).groups())
pins = {}
for m in re.finditer(r'PIN (\S+)\n(.*?)END \1', t, re.S):
    r = [tuple(map(float, x)) for x in re.findall(r'RECT ([\d.\-]+) ([\d.\-]+) ([\d.\-]+) ([\d.\-]+)', m.group(2))]
    pins[m.group(1)] = (re.findall(r'LAYER (\S+)', m.group(2))[0], r[0])
ports = [l.split()[2:] for l in open(cdl) if l.startswith('.subckt ' + sub + ' ')][0]
ok = sorted(ports) == sorted(pins)
print('macro %s: %g x %g um, area %.2f um2' % (sub, w, h, w * h))
for n, (lay, r) in pins.items():
    e = ''.join(c for c, f in (('W', r[0] <= 0.01), ('E', r[2] >= w - 0.01), ('S', r[1] <= 0.01), ('N', r[3] >= h - 0.01)) if f) or 'interior'
    print('  pin %-8s %-7s rect %s edge %s' % (n, lay, r, e))
print('PIN CHECK:', 'pins equal CDL ports' if ok else 'MISMATCH ports=%s pins=%s' % (sorted(ports), sorted(pins)))
sys.exit(0 if ok else 1)
