#!/usr/bin/env python3
"""Turn the kpex 2.5D CC extraction of the top-interconnect view (CSV) plus the per-net
route R table into lumped subcircuits for the chip deck, and a per-net summary JSON.

Net classes: signal nets are the labelled clusters (CDL names, '__fragN' = further
clusters of the same CDL net, e.g. an IO cell's pin stack). Ground-like nodes are VSUBS,
the supply nets (VDD VSS VDDA IOVDD IOVSS) and unnamed clusters ($n: std-cell/IO filler
supply rails, unidentified pin shapes). A fragment is 'route' when it carries top-level
routing (present in the route table), 'bondpad' when it is a bondpad TopMetal stack, else
'pin' (black-box pin shapes only; not added to the lumps)."""
import sys, csv, json, re, collections, hashlib
from pathlib import Path
csvp, rcp, prep, outsp, outjs = sys.argv[1:6]
rc = json.load(open(rcp))['nets']; pr = json.load(open(prep))
SUP = {'VDD', 'VSS', 'VDDA', 'IOVDD', 'IOVSS'}
base = lambda n: n.split('__frag')[0]
# bondpad fragments: clusters holding an IOPad 'pad' pin on TopMetal1/2
bp_clusters = {str(p['cluster']) for p in pr['pins'] if 'IOPad' in p['inst'] and 'pad' in p['labels'] and p['layer'] in (126, 134)}
lab2cl = {k: str(v['cluster']) for k, v in pr['labels'].items()}
def kind(n):
    if n in rc and lab2cl.get(n) not in bp_clusters: return 'route'
    if lab2cl.get(n) in bp_clusters: return 'bondpad'
    return 'pin'
def gnd(n): return n == 'VSUBS' or n.startswith('$') or base(n) in SUP or n == 'dummy_tap'
rows = list(csv.DictReader(open(csvp), delimiter=';'))
S = collections.defaultdict(lambda: collections.defaultdict(float))   # base -> key -> fF
CC = collections.defaultdict(float)                                   # (a,b) route-route coupling
ncap = 0
for r in rows:
    a, b, c = r['Net1'], r['Net2'], float(r['Capacitance [fF]']); ncap += 1
    for x, y in ((a, b), (b, a)):
        if gnd(x): continue
        kx = kind(x); bx = base(x)
        if gnd(y):
            tgt = 'sub' if y == 'VSUBS' else ('supply' if base(y) in SUP else 'unnamed')
            S[bx][kx + '_to_' + tgt] += c
        elif base(y) == bx:
            S[bx][kx + '_self'] += c / 2   # counted once per direction
        else:
            ky = kind(y)
            S[bx][kx + '_to_' + ky + '_signal'] += c
            if kx == 'route' and ky == 'route' and x < y: CC[tuple(sorted((bx, base(y))))] += c
            if kx == 'bondpad' or ky == 'bondpad' or kx == 'pin' or ky == 'pin': pass
sig = sorted(n for n in S if n not in SUP)
port = lambda n: re.sub(r'^i_core_', '', n).lower()
summary = {}
for n in sig:
    d = S[n]
    route_gnd = d['route_to_sub'] + d['route_to_supply'] + d['route_to_unnamed'] + d['route_to_pin_signal'] + d['route_to_bondpad_signal']
    route_cc = d['route_to_route_signal']
    frs = [k for k in rc if base(k) == n and kind(k) == 'route']
    R = sum(rc[k]['R_wire_ohm'] + rc[k]['R_via_ohm'] for k in frs)
    L = sum(e['length_um'] for k in frs for e in rc[k]['layers'].values())
    ap = sum(rc[k]['C_area_fF'] + rc[k]['C_perim_fF'] for k in frs)
    bp = d['bondpad_to_sub'] + d['bondpad_to_supply'] + d['bondpad_to_unnamed'] + d['bondpad_to_route_signal'] + d['bondpad_to_pin_signal'] + d['bondpad_to_bondpad_signal']
    pin = sum(v for k, v in d.items() if k.startswith('pin_'))
    summary[n] = dict(port=port(n), route_length_um=round(L, 1), R_route_ohm=round(R, 1),
        C_route_ground_fF=round(route_gnd, 3), C_route_coupling_fF=round(route_cc, 3),
        C_route_total_fF=round(route_gnd + route_cc, 3), C_route_area_perimeter_check_fF=round(ap, 2),
        C_bondpad_fF=round(bp, 2), C_pin_only_fragments_fF=round(pin, 2),
        top_coupling=sorted(((round(v, 3), (b if a == n else a)) for (a, b), v in CC.items() if n in (a, b)), reverse=True)[:3])
routed = [n for n in sig if summary[n]['route_length_um'] > 0]
h = hashlib.sha256
L = ['* g1_top_interconnect: lumped top-level routing parasitics of g1_chip_top_1414.gds (629d303a...)',
     '* kpex 0.3.12 2.5D CC on the top-interconnect view (fill removed, block macros/IO/std cells = pin shapes only)',
     '* + route R (kpex ihp-sg13g2 sheet/via tables, series upper bound). Values are extracted/estimated, not measured.',
     '* Source CSV sha256 ' + h(Path(csvp).read_bytes()).hexdigest() + ', route table sha256 ' + h(Path(rcp).read_bytes()).hexdigest(),
     '* Port names = canonical CDL net names without the i_core_ prefix, lower case; sub = substrate/ground (connect to 0).',
     '* Couplings between two routed signal nets are kept as net-to-net C; everything else a routed net sees',
     '* (substrate, supplies, unnamed rails, pin-only fragments, bondpads) is lumped to sub. Bondpad C is NOT included',
     '* (see README); add Cbp_* from the README table if the deck does not model pad metal.', '']
ports = ' '.join(summary[n]['port'] for n in routed)
L.append('* ---- C only (drop-in: connect ports to the deck nodes of the same net)')
L.append('.subckt g1_top_interconnect %s sub' % ports)
for n in routed:
    s = summary[n]; L.append('Cg_%s %s sub %.4gf' % (s['port'], s['port'], s['C_route_ground_fF']))
for (a, b), v in sorted(CC.items()):
    if v >= 0.01: L.append('Cc_%s__%s %s %s %.4gf' % (port(a), port(b), port(a), port(b), v))
L.append('.ends g1_top_interconnect'); L.append('')
L.append('* ---- pi RC variant: <net> = driver side, <net>_far = receiver side; R = series upper bound;')
L.append('* ground C split half/half, couplings placed at the driver-side nodes')
L.append('.subckt g1_top_interconnect_pi %s sub' % ' '.join('%s %s_far' % (summary[n]['port'], summary[n]['port']) for n in routed))
for n in routed:
    s = summary[n]; p = s['port']
    L += ['R_%s %s %s_far %.4g' % (p, p, p, max(s['R_route_ohm'], 1e-3)),
          'Cga_%s %s sub %.4gf' % (p, p, s['C_route_ground_fF']/2), 'Cgb_%s %s_far sub %.4gf' % (p, p, s['C_route_ground_fF']/2)]
for (a, b), v in sorted(CC.items()):
    if v >= 0.01: L.append('Cc_%s__%s %s %s %.4gf' % (port(a), port(b), port(a), port(b), v))
L.append('.ends g1_top_interconnect_pi'); L.append('')
def wrap(line, n=100):
    if len(line) <= n: return [line]
    out, cur = [], ''
    for w in line.split():
        if cur and len(cur) + 1 + len(w) > n: out.append(cur); cur = '+ ' + w
        else: cur = (cur + ' ' + w) if cur else w
    return out + [cur]
L = [x for l in L for x in wrap(l)]
Path(outsp).write_text('\n'.join(L) + '\n')
Path(outjs).write_text(json.dumps(dict(capacitors_in_csv=ncap, csv_sha256=h(Path(csvp).read_bytes()).hexdigest(), nets=summary,
    coupling_fF={'%s|%s' % k: round(v, 4) for k, v in sorted(CC.items())}), indent=1) + '\n')
print(len(routed), 'routed nets;', ncap, 'caps in CSV;', len(CC), 'route-route couplings')
