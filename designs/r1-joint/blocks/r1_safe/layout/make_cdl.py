#!/usr/bin/env python3
"""Flat LVS reference netlist (CDL) of r1_safe from the netlist of record schematic/r1_safe.spice.

Format conversion only: the hierarchy under r1_safe_an is expanded (instance path joined with '_'), X-lines of PDK
primitives become M/R lines (`ng` and `mm_ok` dropped, `w` is the total width; m = N becomes N parallel devices),
the two 1 mOhm string-end resistors (Rt252, Rt0) are shorts (T252 = vref, T0 = vss), `sub!`-less rppd keep their
third terminal (vss). Optional: drop the comparators (layout test without them) and add layout dummy devices.
Usage (host or container python3): make_cdl.py <out.cdl> [--no-cmp] [--extra <file with extra device lines>]
"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
NET = os.path.join(HERE, '..', 'schematic', 'r1_safe.spice')
PRIM = {'sg13_hv_pmos': 'M', 'sg13_hv_nmos': 'M', 'sg13_lv_pmos': 'M', 'sg13_lv_nmos': 'M', 'rppd': 'R'}


def parse(path):
    subs, cur = {}, None
    for raw in open(path):
        line = raw.strip()
        if not line or line.startswith('*'):
            continue
        t = line.split()
        if t[0].lower() == '.subckt':
            cur = t[1]
            subs[cur] = (t[2:], [])
        elif t[0].lower() == '.ends':
            cur = None
        elif cur:
            subs[cur][1].append(t)
    return subs


def flatten(subs, top='r1_safe_an', no_cmp=False):
    ports, _ = subs[top]
    devs, shorts = [], []

    def rec(name, nmap, path):
        p, body = subs[name]
        for t in body:
            inst = t[0]
            if inst[0] in 'Xx':
                params = [x for x in t[1:] if '=' in x]
                nodes = [x for x in t[1:] if '=' not in x]
                model = nodes[-1]
                nodes = nodes[:-1]
                mapped = [nmap.get(n, path + n) for n in nodes]
                if model in PRIM:
                    devs.append((PRIM[model], path + inst[1:], mapped, model, params))
                else:
                    if no_cmp and model == 'r1_safe_cmp':
                        continue
                    sp, _ = subs[model]
                    rec(model, dict(zip(sp, mapped)), path + inst[1:] + '_')
            elif inst[0] in 'Rr':
                a, b = nmap.get(t[1], path + t[1]), nmap.get(t[2], path + t[2])
                val = float(t[3])
                assert val < 1.0, t
                shorts.append((a, b))
            else:
                raise ValueError(t)
    rec(top, {p: p for p in ports}, '')
    # apply shorts (keep the port name)
    rep = {}
    for a, b in shorts:
        keep, drop = (a, b) if a in ports else (b, a)
        rep[drop] = keep
    def R(n):
        while n in rep:
            n = rep[n]
        return n
    out = []
    for kind, name, nodes, model, params in devs:
        nodes = [R(n) for n in nodes]
        pd = dict(x.split('=', 1) for x in params)
        m = int(float(pd.get('m', '1')))
        keep = [k for k in pd if k not in ('ng', 'mm_ok', 'm')]
        ptxt = ' '.join('%s=%s' % (k, pd[k]) for k in keep)
        for i in range(m):
            nm = name if m == 1 else '%s_m%d' % (name, i)
            out.append('%s%s %s %s %s m=1' % (kind, nm, ' '.join(nodes), model, ptxt))
    return ports, out


def main():
    args = sys.argv[1:]
    outp = args[0]
    no_cmp = '--no-cmp' in args
    extra = []
    if '--extra' in args:
        extra = [l.rstrip('\n') for l in open(args[args.index('--extra') + 1]) if l.strip()]
    ports_override = None
    if '--ports' in args:
        ports_override = args[args.index('--ports') + 1].split(',')
    subs = parse(NET)
    ports, lines = flatten(subs, no_cmp=no_cmp)
    if ports_override:
        ports = ports_override
    hdr = ['* r1_safe LVS reference netlist (flat), written by layout/make_cdl.py from schematic/r1_safe.spice '
           '(netlist of record). Format conversion only; see the script header.' + (' Comparators omitted (test).' if no_cmp else ''),
           '.subckt r1_safe ' + ' '.join(ports)]
    open(outp, 'w').write('\n'.join(hdr + lines + extra + ['.ends r1_safe', '']))
    print('cdl', outp, 'devices', len(lines) + len(extra))


if __name__ == '__main__':
    main()
