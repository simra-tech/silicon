#!/usr/bin/env python3
"""Per-net top-level route R and C of the chip (for STA annotation and the chip deck records).

Inputs: the per-net summary of make_top_interconnect_spice.py (kpex 2.5D CC lumps of the
top-interconnect view + series-R upper bound of top_route_rc.py), the view's prepare.json
(pin -> cluster -> CDL net) and, optionally, the pin-to-pin resistor networks of
top_route_rnet.py. Output JSON, one entry per CDL net that has top-level routing:
C to ground / to other routed nets (fF), series-R upper bound (ohm), the pins the route
lands on (instance, pin label, layer) and, when the R networks are given, the effective
resistance from the reference pin to every other pin (ohm, all other pins open)."""
import sys, json, hashlib, collections, argparse
from pathlib import Path
ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('summary'); ap.add_argument('prepare'); ap.add_argument('out')
ap.add_argument('--rnet', default=None, help='top_route_rnet.py JSON (optional)')
ap.add_argument('--rc-spice', default=None, help='make_top_rc_spice.py element file (optional): supply-net R from the pad ring node to every block supply pin')
ap.add_argument('--note', default='')
a = ap.parse_args()
S = json.load(open(a.summary)); P = json.load(open(a.prepare))
R = json.load(open(a.rnet)) if a.rnet else None
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
pins = collections.defaultdict(set)
for p in P['pins']:
    if p.get('cdl'):
        inst = P['cellmap'].get(p['inst'].split('@')[0], p['inst'])
        pins[p['cdl']].add((inst, '/'.join(p['labels']), p['layer']))
out = collections.OrderedDict()
for n, s in sorted(S['nets'].items()):
    if s['route_length_um'] <= 0:
        continue
    e = collections.OrderedDict(port=s['port'], route_length_um=s['route_length_um'],
        R_series_upper_bound_ohm=s['R_route_ohm'], C_ground_fF=s['C_route_ground_fF'],
        C_coupling_fF=s['C_route_coupling_fF'], C_total_fF=s['C_route_total_fF'],
        C_bondpad_fF=s['C_bondpad_fF'], largest_couplings_fF=s['top_coupling'],
        pins=sorted([dict(inst=i, pin=l, layer=ly) for i, l, ly in pins.get(n, ())], key=lambda d: (d['inst'], d['pin'], d['layer'])))
    if R and n in R['nets']:
        e['R_pin_to_pin'] = R['nets'][n]['effective_R_ohm']
    out[n] = e
sup = collections.OrderedDict()
if a.rc_spice:
    import numpy as np
    edges = collections.defaultdict(list)
    for l in open(a.rc_spice):
        t = l.split()
        if t and t[0].startswith('Rtic'):
            N = t[1].split('__')[0]
            if N in ('VDD', 'VSS', 'VDDA', 'IOVDD', 'IOVSS'): edges[N].append((t[1], t[2], float(t[3])))
    for N, E in sorted(edges.items()):
        nodes = sorted(set([x for e in E for x in e[:2]]) | {N}); ix = {n: i for i, n in enumerate(nodes)}
        G = np.zeros((len(nodes), len(nodes)))
        for x, y, r in E:
            i, j = ix[x], ix[y]; g = 1.0 / r; G[i, i] += g; G[j, j] += g; G[i, j] -= g; G[j, i] -= g
        k = [i for i in range(len(nodes)) if nodes[i] != N]
        Z = np.linalg.pinv(G[np.ix_(k, k)])
        sup[N] = collections.OrderedDict((nodes[i].split('__', 1)[1], round(float(Z[m, m]), 3)) for m, i in enumerate(k))
res = collections.OrderedDict(
    what='top-level routing parasitics of g1_chip_top (r4), extracted: kpex 0.3.12 2.5D CC on the fill-free top-interconnect view; '
         'R from the kpex ihp-sg13g2 sheet/via tables. C_ground lumps substrate, supplies, unnamed rails and pin-only fragments; '
         'C_coupling is to other routed signal nets. Bondpad C is separate and not in C_total. Not measured. ' + a.note,
    inputs={Path(p).name: sha(p) for p in [a.summary, a.prepare] + ([a.rnet] if a.rnet else []) + ([a.rc_spice] if a.rc_spice else [])},
    script_sha256=sha(__file__), units=dict(R='ohm', C='fF', length='um'), nets=out,
    supply_R_from_pad_ring_ohm=sup or 'not computed (no --rc-spice)',
    supply_note='R from the ideal pad-ring node (all IO-cell supply pins of that net joined; ring rails inside the sg13g2_io cells are not in the view) to each pin node, all other pins open; top-level routing only, block-internal and IO-cell metal excluded')
Path(a.out).write_text(json.dumps(res, indent=1) + '\n'); print(len(out), 'nets ->', a.out)
