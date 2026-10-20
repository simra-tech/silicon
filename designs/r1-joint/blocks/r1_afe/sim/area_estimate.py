#!/usr/bin/env python3
"""Drawn-area estimate of r1_afe from schematic/r1_afe.spice (flattened instance count x device size).
Overhead factors are assumptions, not layout: MOS gate area x 4 (diffusion, contacts, guard rings),
rppd body area x 2 (head areas, spacing, dummies), MIM area x 1.3 (enclosure, spacing). Output JSON on stdout.
Usage: python3 area_estimate.py [netlist]   (default: ../schematic/r1_afe.spice)"""
import json, os, re, sys
SP = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'schematic', 'r1_afe.spice')
OVH = {'mos': 4.0, 'rppd': 2.0, 'mim': 1.3}

def num(v, params):
    v = v.strip('{}')
    if v in params:
        v = params[v]
    m = re.match(r'^([-+0-9.eE]+)(u|n|p)?$', str(v))
    k = {'u': 1.0, 'n': 1e-3, 'p': 1e-6, None: 1e6}[m.group(2)]
    return float(m.group(1)) * k  # in um

def parse():
    lines = []
    for l in open(SP):
        l = l.rstrip('\n')
        if l.startswith('+') and lines:
            lines[-1] += ' ' + l[1:]
        else:
            lines.append(l)
    gparams, subs, cur = {}, {}, None
    for l in lines:
        t = l.split()
        if not t or t[0].startswith('*'):
            continue
        if t[0].lower() == '.param':
            for kv in t[1:]:
                k, v = kv.split('='); gparams[k] = v
        elif t[0].lower() == '.subckt':
            defaults = dict(kv.split('=') for kv in t[2:] if '=' in kv)
            cur = subs[t[1]] = {'defaults': defaults, 'inst': []}
        elif t[0].lower() == '.ends':
            cur = None
        elif cur is not None and t[0][0] in 'Xx':
            pos = [x for x in t[1:] if '=' not in x]
            kv = dict(x.split('=') for x in t[1:] if '=' in x)
            cur['inst'].append((t[0], pos[-1], kv))
    return gparams, subs

def walk(name, subs, gparams, override, acc, mult=1):
    s = subs[name]
    params = dict(gparams); params.update(s['defaults']); params.update(override)
    for inst, model, kv in s['inst']:
        if model in subs:
            walk(model, subs, gparams, {k: params.get(v.strip('{}'), v) for k, v in kv.items()}, acc, mult)
            continue
        w, l = num(kv['w'], params), num(kv['l'], params)
        typ = 'mos' if model.startswith('sg13_hv') else ('rppd' if model == 'rppd' else 'mim')
        acc[typ] += mult * w * l

def main():
    gparams, subs = parse()
    acc = {'mos': 0.0, 'rppd': 0.0, 'mim': 0.0}
    walk('r1_afe', subs, gparams, {}, acc)
    est = {k: acc[k] * OVH[k] for k in acc}
    out = {'drawn_um2': {k: round(v) for k, v in acc.items()}, 'overhead_factors': OVH,
           'estimate_um2': {k: round(v) for k, v in est.items()},
           'total_estimate_mm2': round(sum(est.values()) / 1e6, 4),
           'note': 'estimated from the schematic; no layout. MIM assumed not placed over other devices.'}
    json.dump(out, sys.stdout, indent=1); print()

if __name__ == '__main__':
    main()
