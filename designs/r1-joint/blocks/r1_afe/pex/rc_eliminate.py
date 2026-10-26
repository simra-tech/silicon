#!/usr/bin/env python3
"""Revision F (track T3): elimination variants of a post-layout RC netlist (pex_rc_build.py output).

  python3 rc_eliminate.py <in.spice> <out.spice> [rule ...]

Rules (applied in order; a net is matched by its base name, i.e. the node name without the '__p<n>', '__xsin', '__xcos' suffix,
in every subcircuit):
  R:<regex>=<factor>   multiply every wire resistor (Rw* channel, Rt* top) whose two nodes both belong to a matching net by <factor>
                       (factor 1e-3 = short the wiring of that net)
  C:<regex>            remove every extracted capacitor (Cp* channel, Cq* top) with at least one node on a matching net
  Cx:<regex>           remove every extracted capacitor with both nodes outside the ground net 0/vss and at least one
                       node on a matching net (coupling only)
  S:<subckt>           restrict the following rules to one subcircuit (S:* = all, default)
Prints the number of changed elements per rule. Device instances are not changed.
"""
import re, sys

def base(n):
    return re.sub(r'__(p\d+|xsin|xcos)$', '', n)

def main():
    src, dst, rules = sys.argv[1], sys.argv[2], sys.argv[3:]
    lines = open(src).read().split('\n')
    sub_of = []
    cur = None
    for l in lines:
        if l.lower().startswith('.subckt'):
            cur = l.split()[1]
        sub_of.append(cur)
        if l.lower().startswith('.ends'):
            cur = None
    scope = '*'
    report = []
    for r in rules:
        if r.startswith('S:'):
            scope = r[2:]; continue
        kind, arg = r.split(':', 1)
        n = 0
        if kind == 'R':
            rx, fac = arg.rsplit('=', 1)
            rx, fac = re.compile('^(%s)$' % rx), float(fac)
            for i, l in enumerate(lines):
                if not re.match(r'R[wt]\d', l) or (scope != '*' and sub_of[i] != scope):
                    continue
                t = l.split()
                if rx.match(base(t[1])) and rx.match(base(t[2])):
                    t[3] = '%.6g' % (float(t[3]) * fac); lines[i] = ' '.join(t); n += 1
        elif kind in ('C', 'Cx'):
            rx = re.compile('^(%s)$' % arg)
            for i, l in enumerate(lines):
                if not re.match(r'C[pq]\d', l) or (scope != '*' and sub_of[i] != scope):
                    continue
                t = l.split()
                a, b = base(t[1]), base(t[2])
                if kind == 'Cx' and (a in ('0', 'vss') or b in ('0', 'vss')):
                    continue
                if rx.match(a) or rx.match(b):
                    lines[i] = '* removed ' + l; n += 1
        else:
            raise SystemExit('unknown rule ' + r)
        report.append((scope, r, n))
    open(dst, 'w').write('* rc_eliminate.py %s\n' % ' '.join(rules) + '\n'.join(lines))
    for s, r, n in report:
        print('%-10s %-40s %d' % (s, r, n))

if __name__ == '__main__':
    main()
