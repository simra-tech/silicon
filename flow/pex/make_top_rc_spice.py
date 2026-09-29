#!/usr/bin/env python3
"""Distributed RC of the chip's top-level routing, for the full-chip CDL deck
(run_top_cdl.py --interconnect extracted-rc).

Inputs: the pin-to-pin resistor networks of top_route_rnet.py (every labelled net of the
top-interconnect view, supply nets included), the kpex 2.5D CC CSV of the same view, the
view's prepare.json and route table (top_route_rc.py, which fragments carry routing).

Node naming, per CDL net N:
  * IO-cell pins on a supply net (VDD VSS VDDA IOVDD IOVSS) or on a chip-pin net, and the
    reference port of every other net (see top_route_rnet.py), are the node N itself. The IO
    ring rails run inside the sg13g2_io cells, which the view does not contain, so the ring
    is one ideal node per supply (T2 covers the ring resistance).
  * every other port is the node N__<CDL instance>; the deck connects that instance's pin
    there instead of on N. Pins the view does not reach stay on N.
  * internal network nodes (N__n<fragment>_<k>) are eliminated by Kron reduction onto the
    port nodes of each fragment (exact at DC); conductances below 1e-9 S are left open.
  * a network component that reaches neither N nor any shared node (e.g. the BGR supply
    pins, joined only inside the BGR macro) is merged into N (its pins stay on N, no rename);
    it is listed under 'tied_to_N'.
Capacitance: every kpex CSV entry with a routed fragment on at least one side (same rule as
make_top_interconnect_spice.py). VSUBS, unnamed rails ($n) and bondpad stacks are VSS.
Pin-only-to-pin-only and bondpad self C are left out (as before). C of a fragment sits on
its port nodes, split evenly; a coupling is split over the first side's nodes, each to the
nearest node of the other side. Nothing here is measured; values are extracted."""
import sys, csv, json, re, collections, hashlib, math, argparse
from pathlib import Path
ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('rnet'); ap.add_argument('csv'); ap.add_argument('prepare'); ap.add_argument('route_rc')
ap.add_argument('out_spice'); ap.add_argument('out_map')
a = ap.parse_args()
RN = json.load(open(a.rnet))['nets']; P = json.load(open(a.prepare)); RC = json.load(open(a.route_rc))['nets']
SUP = {'VDD', 'VSS', 'VDDA', 'IOVDD', 'IOVSS'}
CHIP_PINS = set('D_ELT D_STD EN FAULT_N GATE G_SHARED HBT_B HBT_C HBT_E SCLK SDI SDO SENSE_N SENSE_P TEMP_OUT TRIP_SET VDDA VREF VDD VSS IOVDD IOVSS'.split())
base = lambda n: n.split('__frag')[0]
is_io = lambda inst: inst.startswith('Xpad') or 'IOPad' in inst
bp_clusters = {str(p['cluster']) for p in P['pins'] if 'IOPad' in p['inst'] and 'pad' in p['labels'] and p['layer'] in (126, 134)}
lab2cl = {k: str(v['cluster']) for k, v in P['labels'].items()}
def kind(n):
    if n == 'VSUBS' or n.startswith('$'): return 'gnd'
    if lab2cl.get(n) in bp_clusters: return 'bp'
    if n in RC: return 'route'
    return 'pin'
def shortinst(i):
    return re.sub(r'[^A-Za-z0-9_]', '_', i)
# ---- node names
node_of = {}          # (fragment, node index) -> node name
port_node = {}        # (N, port name) -> node name
renames = collections.defaultdict(dict)   # CDL inst -> {pin label lower: node}
frag_nodes = collections.defaultdict(list)
xy = {}
for fi, (frag, v) in enumerate(sorted(RN.items())):
    N = base(frag)
    if not v.get('ports'): continue
    for k, nd in enumerate(v['nodes']):
        p = nd['port']
        if p:
            inst, pin = p.split(':', 1)
            if (is_io(inst) and (N in SUP or N in CHIP_PINS)) or p == v.get('reference_port') and N not in SUP and N not in CHIP_PINS:
                name = N
            else:
                name = '%s__%s' % (N, shortinst(inst))
            port_node[(N, p)] = name
            if name != N and not inst.startswith('retained_'):
                for lb in pin.split('/'):
                    old = renames[inst].get(lb.lower())
                    if old and old != name: raise SystemExit('pin %s:%s on two nodes %s %s' % (inst, lb, old, name))
                    renames[inst][lb.lower()] = name
            if name not in frag_nodes[frag]: frag_nodes[frag].append(name)
        else:
            name = '%s__n%d_%d' % (N, fi, k)
        node_of[(frag, k)] = name
        xy.setdefault(name, nd['xy_um'])
# ---- resistors, and connectivity per net to tie floating components to N
R = collections.OrderedDict(); uf = {}
def f(x):
    uf.setdefault(x, x)
    while uf[x] != x: uf[x] = uf[uf[x]]; x = uf[x]
    return x
import numpy as np
kron = collections.OrderedDict()
for frag, v in sorted(RN.items()):
    if not v.get('ports'): continue
    for n in frag_nodes[frag]: f(n)
    names = sorted(set(node_of[(frag, k)] for k in range(len(v['nodes']))))
    ix = {n: i for i, n in enumerate(names)}
    G = np.zeros((len(names), len(names)))
    for x, y, r in v['resistors']:
        i, j = ix[node_of[(frag, x)]], ix[node_of[(frag, y)]]
        if i == j: continue
        g = 1.0 / max(r, 1e-6); G[i, i] += g; G[j, j] += g; G[i, j] -= g; G[j, i] -= g
    keep = [ix[n] for n in names if '__n' not in n]
    drop = [ix[n] for n in names if '__n' in n]
    if drop:   # Kron reduction onto the port nodes (exact for DC; C sits on the port nodes)
        Gkk, Gkd, Gdd = G[np.ix_(keep, keep)], G[np.ix_(keep, drop)], G[np.ix_(drop, drop)]
        G = Gkk - Gkd.dot(np.linalg.lstsq(Gdd, Gkd.T, rcond=None)[0])
    else:
        G = G[np.ix_(keep, keep)]
    kn = [names[i] for i in keep]
    kron[frag] = dict(nodes_before=len(names), ports=len(kn))
    for i in range(len(kn)):
        for j in range(i + 1, len(kn)):
            g = -G[i, j]
            if g <= 1e-9: continue           # > 1 GOhm: open
            na, nb = kn[i], kn[j]
            uf[f(na)] = f(nb)
            key = tuple(sorted((na, nb)))
            R[key] = 1.0 / (1.0 / R[key] + g) if key in R else 1.0 / g
for n in list(uf): f(n)
tied = []; alias = {}
comps = collections.defaultdict(set)
for (frag, k), n in node_of.items():
    if '__n' not in n: comps[(base(frag), f(n))].add(n)
for (N, root), members in sorted(comps.items()):
    if f(N) == root if N in uf else False: continue
    ports_here = sorted(m for m in members if '__n' not in m)
    if not ports_here: continue        # internal-only islands (should not occur)
    tied.append(dict(net=N, nodes=ports_here))
    for m in ports_here:
        alias[m] = N
# tied components are merged into N (no tie resistor: a milliohm element next to fF capacitors made the
# ss/125 C operating point and transient of the chip deck very slow)
if alias:
    R2 = collections.OrderedDict()
    for (p, q), r in R.items():
        p, q = alias.get(p, p), alias.get(q, q)
        if p == q: continue
        key = tuple(sorted((p, q)))
        R2[key] = 1.0 / (1.0 / R2[key] + 1.0 / r) if key in R2 else r
    R = R2
    for inst in list(renames):
        for lb in list(renames[inst]):
            if renames[inst][lb] in alias: del renames[inst][lb]
        if not renames[inst]: del renames[inst]
    for fr in frag_nodes:
        frag_nodes[fr] = list(dict.fromkeys(alias.get(n, n) for n in frag_nodes[fr]))
# ---- capacitance
C = collections.defaultdict(float); skipped = collections.Counter(); ncsv = 0
def nodes_for(frag):
    if kind(frag) in ('gnd', 'bp'): return ['VSS']
    return frag_nodes.get(frag) or [base(frag)]
def nearest(n, cands):
    if n not in xy: return cands[0]
    return min(cands, key=lambda c: (xy[c][0] - xy[n][0]) ** 2 + (xy[c][1] - xy[n][1]) ** 2 if c in xy else 1e18)
for r in csv.DictReader(open(a.csv), delimiter=';'):
    x, y, c = r['Net1'], r['Net2'], float(r['Capacitance [fF]']); ncsv += 1
    kx, ky = kind(x), kind(y)
    if 'route' not in (kx, ky): skipped['no_route_side'] += 1; continue
    if kx not in ('gnd', 'bp') and ky not in ('gnd', 'bp') and base(x) == base(y): skipped['same_net'] += 1; continue
    if kx != 'route': x, y, kx, ky = y, x, ky, kx
    A, B = nodes_for(x), nodes_for(y)
    for n in A:
        m = nearest(n, B)
        if n == m: continue
        C[tuple(sorted((n, m)))] += c / len(A)
# ---- write
h = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
L = ['* g1_top_interconnect_rc: distributed RC of the top-level routing of g1_chip_top (r4), element lines for the',
     '* body of the deck-local g1_chip_top (run_top_cdl.py --interconnect extracted-rc; pin renames in the map JSON).',
     '* R: KLayout RNetExtractor (square counting, kpex ihp-sg13g2 sheet/via tables) on the fill-free top-interconnect view,',
     '* Kron-reduced onto the pin nodes of each network fragment (exact at DC).',
     '* C: kpex 0.3.12 2.5D CC on the same view. Extracted, not measured. Inputs (sha256): rnet %s, csv %s.' % (h(a.rnet)[:16], h(a.csv)[:16]),
     '* %d resistors, %d capacitors; %d network components tied to their net node (see map JSON).' % (len(R), len(C), len(tied))]
for i, ((p, q), r) in enumerate(R.items()):
    L.append('Rtic%d %s %s %.6g' % (i, p, q, max(r, 1e-3)))
for i, ((p, q), c) in enumerate(sorted(C.items())):
    if c >= 1e-4: L.append('Ctic%d %s %s %.6gf' % (i, p, q, c))
Path(a.out_spice).write_text('\n'.join(L) + '\n')
nets = collections.defaultdict(lambda: dict(R_count=0, R_total_ohm=0.0, C_to_VSS_fF=0.0, C_other_fF=0.0))
for (p, q), r in R.items():
    N = p.split('__')[0]; nets[N]['R_count'] += 1; nets[N]['R_total_ohm'] += r
for (p, q), c in C.items():
    for s in (p, q):
        o = q if s == p else p
        N = s.split('__')[0]
        if N == 'VSS': continue
        nets[N]['C_to_VSS_fF' if o.split('__')[0] == 'VSS' else 'C_other_fF'] += c
Path(a.out_map).write_text(json.dumps(dict(spice=Path(a.out_spice).name, spice_sha256=h(a.out_spice), inputs={Path(p).name: h(p) for p in (a.rnet, a.csv, a.prepare, a.route_rc)},
    script_sha256=h(__file__), renames=renames, tied_to_N=tied, capacitors_in_csv=ncsv, csv_rows_skipped=dict(skipped),
    n_resistors=len(R), n_capacitors=len(C), kron_reduction=kron, nets={k: {kk: round(vv, 4) if isinstance(vv, float) else vv for kk, vv in v.items()} for k, v in sorted(nets.items())}), indent=1) + '\n')
print(len(R), 'R;', len(C), 'C;', len(tied), 'tied;', sum(len(v) for v in renames.values()), 'pin renames on', len(renames), 'instances')
