#!/usr/bin/env python3
"""Layout E7 (track T3k): port-level elimination variants of a post-layout netlist (pex_rc_build.py output).

  python3 pex/port_eliminate.py <in.spice> <out.spice> [rule ...]

Rules (applied in order):
  T:<device regex>:<k>   for every device instance whose name matches (anchored), connect terminal k (1 = first node)
                         to the main node of its net (the node name without '__p<n>'). The wiring from the main node
                         to that port then carries no device current: the port's wiring term is removed, its C stays.
  R:<net regex>=<f>      as pex/rc_eliminate.py: multiply the wire resistors of matching nets by f.
  S:<device regex>:<k>:<ohm>  insert a series resistor of <ohm> between terminal k of every matching device and its
                         node (sensitivity probe: offset change per Ohm of one port type on one side).
Prints the number of changed elements per rule.
"""
import re, sys

def base(n):
    return re.sub(r'__(p\d+|xsin|xcos)$', '', n)

src, dst, rules = sys.argv[1], sys.argv[2], sys.argv[3:]
lines = open(src).read().split('\n')
for r in rules:
    kind, arg = r.split(':', 1)
    n = 0
    if kind == 'T':
        rx, k = arg.rsplit(':', 1)
        rx, k = re.compile('^(%s)$' % rx), int(k)
        for i, l in enumerate(lines):
            if not l.startswith('X'):
                continue
            t = l.split()
            if rx.match(t[0]) and base(t[k]) != t[k]:
                t[k] = base(t[k]); lines[i] = ' '.join(t); n += 1
    elif kind == 'S':
        rx, k, ohm = arg.rsplit(':', 2)
        rx, k = re.compile('^(%s)$' % rx), int(k)
        out = []
        for l in lines:
            t = l.split()
            if l.startswith('X') and rx.match(t[0]):
                nn = '%s_ser_%s' % (t[k], t[0].lower())
                out.append('Rser_%s_%d %s %s %s' % (t[0], k, t[k], nn, ohm)); t[k] = nn; l = ' '.join(t); n += 1
            out.append(l)
        lines = out
    elif kind == 'R':
        rx, fac = arg.rsplit('=', 1)
        rx, fac = re.compile('^(%s)$' % rx), float(fac)
        for i, l in enumerate(lines):
            if not re.match(r'R[wt]\d', l):
                continue
            t = l.split()
            if rx.match(base(t[1])) and rx.match(base(t[2])):
                t[3] = '%.6g' % (float(t[3]) * fac); lines[i] = ' '.join(t); n += 1
    else:
        raise SystemExit('unknown rule ' + r)
    print('%s: %d' % (r, n))
open(dst, 'w').write('\n'.join(lines))
