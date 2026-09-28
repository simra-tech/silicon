#!/usr/bin/env python3
"""Resistive mesh of one net from supply_geometry.py, DC solve in ngspice, IR drop and EM tables.

Mesh (finite-volume): every rectangle is cut into cells of at most --pitch um on each side;
neighbouring cells in a rectangle are joined by R = Rs * (centre distance / shared edge); cells of
two rectangles that share an edge are joined by R = Rs * (d1 + d2) / overlap, d = centre-to-edge
distance; via cuts join the lower- and upper-layer cells under their centre, R = Rcut / n per cell
pair. Ports: the bond-ball area of each bondpad is tied to an ideal source (0 V; the solution is the
drop, sign-free for supply and ground nets); the current of a sink group is spread over the cells
under its pin shapes in proportion to the overlap area. Parts of the mesh not connected to a pad are
dropped and listed (a sink in such a part is an open).

Load cases come from --loads (JSON: {case: {group: amps}}); groups not named draw nothing.
Tech: --tech typ|worst (sheet and via resistances in TECH below).
Outputs in --outdir: <net>_<tech>.cir (mesh) and <net>_<tech>_<case>.cir (sources + control),
ngspice logs, <net>_<tech>_<case>_ir.json (per sink group: max / area-weighted mean drop) and
<net>_<tech>_<case>_em.csv (segments: rectangle or via array, max current density or current per
cut against the IHP SG13G2 limits), a scipy cross-check of the ngspice node voltages, and a summary.
"""
import argparse, bisect, collections, csv, hashlib, json, math, os, subprocess, time
from pathlib import Path
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
from scipy.sparse.csgraph import connected_components
ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--geom', required=True, type=Path); ap.add_argument('--loads', required=True, type=Path)
ap.add_argument('--tech', default='typ', choices=('typ', 'worst')); ap.add_argument('--pitch', type=float, default=5.0)
ap.add_argument('--outdir', required=True, type=Path); ap.add_argument('--cases', default=None, help='comma list; default all in --loads')
ap.add_argument('--source-group', default=None, help='use this sink group (e.g. the driving block of a signal net) as the ideal source instead of the bondpads')
ap.add_argument('--em-keep', type=float, default=0.01, help='keep EM rows at or above this fraction of the limit (plus the top 40)')
a = ap.parse_args()
t0 = time.time()
# Ohm/sq and Ohm/cut. typ: IHP SG13G2 process specification rev 1.2 section 2.13/2.14 target values (= kpex
# ihp-sg13g2 tech). worst: maximum values of the same tables, metal sheet R raised by its TC1 to 125 C (+100 K);
# the specification gives no via TC, the via maximum is used unscaled.
TECH = {'typ': dict(Metal1=0.110, Metal2=0.088, Metal3=0.088, Metal4=0.088, Metal5=0.088, TopMetal1=0.018, TopMetal2=0.011,
                    Via1=9.0, Via2=9.0, Via3=9.0, Via4=9.0, TopVia1=2.2, TopVia2=1.1),
        'worst': dict(Metal1=0.135 * 1.34, Metal2=0.103 * 1.35, Metal3=0.103 * 1.35, Metal4=0.103 * 1.35, Metal5=0.103 * 1.35,
                      TopMetal1=0.021 * 1.37, TopMetal2=0.0145 * 1.38, Via1=20.0, Via2=20.0, Via3=20.0, Via4=20.0, TopVia1=4.0, TopVia2=2.2)}
# EM limits, IHP SG13G2 process specification rev 1.2 section 2.15 (note A.v: 11 years at 105 C, < 0.01 % failures)
JMAX = dict(Metal1=1.0, Metal2=2.0, Metal3=2.0, Metal4=2.0, Metal5=2.0, TopMetal1=15.0, TopMetal2=16.0)    # mA/um
WTH = dict(Metal1=0.36, Metal2=0.3, Metal3=0.3, Metal4=0.3, Metal5=0.3)                                   # mA limit at w <= WTH
IMAX_NARROW = dict(Metal1=0.36, Metal2=0.6, Metal3=0.6, Metal4=0.6, Metal5=0.6)                           # mA
IVIA = dict(Via1=0.4, Via2=0.4, Via3=0.4, Via4=0.4, TopVia1=1.4, TopVia2=10.0)                           # mA per cut
VIAS = [('Via1', 'Metal1', 'Metal2'), ('Via2', 'Metal2', 'Metal3'), ('Via3', 'Metal3', 'Metal4'), ('Via4', 'Metal4', 'Metal5'),
        ('TopVia1', 'Metal5', 'TopMetal1'), ('TopVia2', 'TopMetal1', 'TopMetal2')]
RS = TECH[a.tech]
G = json.loads(a.geom.read_text()); net = G['net']
loads = json.loads(a.loads.read_text())
cases = a.cases.split(',') if a.cases else list(loads)
a.outdir.mkdir(parents=True, exist_ok=True)
EPS = 1e-6
# ---------------- cells
cells = []          # (layer, x1, y1, x2, y2, rect_index)
rects = []          # (layer, x1, y1, x2, y2, origin, first_cell, nx, ny)
for layer, lst in G['layers'].items():
    for x1, y1, x2, y2, org in lst:
        w, h = x2 - x1, y2 - y1
        if w <= EPS or h <= EPS: continue
        nx, ny = max(1, math.ceil(w / a.pitch - 1e-9)), max(1, math.ceil(h / a.pitch - 1e-9))
        first = len(cells); ri = len(rects)
        dx, dy = w / nx, h / ny
        for j in range(ny):
            for i in range(nx):
                cells.append((layer, x1 + i * dx, y1 + j * dy, x1 + (i + 1) * dx, y1 + (j + 1) * dy, ri))
        rects.append((layer, x1, y1, x2, y2, org, first, nx, ny))
N = len(cells)
links = []          # (a, b, squares_or_None, via_name_or_None, n_cuts, width_um, owner) ; owner = ('r', rect) or ('v', key)
def cidx(r, i, j):
    return r[6] + j * r[7] + i
for ri, r in enumerate(rects):
    layer, x1, y1, x2, y2, org, first, nx, ny = r
    dx, dy = (x2 - x1) / nx, (y2 - y1) / ny
    for j in range(ny):
        for i in range(nx):
            if i + 1 < nx: links.append((cidx(r, i, j), cidx(r, i + 1, j), dx / dy, None, 0, dy, ('x', ri, i)))
            if j + 1 < ny: links.append((cidx(r, i, j), cidx(r, i, j + 1), dy / dx, None, 0, dx, ('y', ri, j)))
# rectangle adjacency on shared edges (same layer): horizontal edges keyed by y, vertical by x
def join(lo_side, hi_side, horizontal):
    # lo_side: rects whose top (horizontal) / right (vertical) edge is at this coordinate
    hi_sorted = sorted(hi_side, key=lambda t: t[0]); starts = [t[0] for t in hi_sorted]
    for s1, s2, ra in lo_side:
        k = max(0, bisect.bisect_left(starts, s1) - 1)
        while k < len(hi_sorted) and hi_sorted[k][0] < s2 - EPS:
            t1, t2, rb = hi_sorted[k]; k += 1
            if min(s2, t2) - max(s1, t1) <= EPS: continue
            A, B = rects[ra], rects[rb]
            # cells along the touching row/column
            if horizontal:
                ca = [(cidx(A, i, A[8] - 1), A[1] + i * (A[3] - A[1]) / A[7], A[1] + (i + 1) * (A[3] - A[1]) / A[7]) for i in range(A[7])]
                cb = [(cidx(B, i, 0), B[1] + i * (B[3] - B[1]) / B[7], B[1] + (i + 1) * (B[3] - B[1]) / B[7]) for i in range(B[7])]
                da, db = (A[4] - A[2]) / A[8] / 2, (B[4] - B[2]) / B[8] / 2
            else:
                ca = [(cidx(A, A[7] - 1, j), A[2] + j * (A[4] - A[2]) / A[8], A[2] + (j + 1) * (A[4] - A[2]) / A[8]) for j in range(A[8])]
                cb = [(cidx(B, 0, j), B[2] + j * (B[4] - B[2]) / B[8], B[2] + (j + 1) * (B[4] - B[2]) / B[8]) for j in range(B[8])]
                da, db = (A[3] - A[1]) / A[7] / 2, (B[3] - B[1]) / B[7] / 2
            for c1, u1, u2 in ca:
                for c2, v1, v2 in cb:
                    o = min(u2, v2) - max(u1, v1)
                    if o > EPS:
                        links.append((c1, c2, (da + db) / o, None, 0, o, ('e', ra, 't' if horizontal else 'r', rb, 'b' if horizontal else 'l')))
                        touch[ra]['t' if horizontal else 'r'] += o; touch[rb]['b' if horizontal else 'l'] += o
touch = collections.defaultdict(collections.Counter)   # abutting length per side of a rectangle (same layer)
byl = collections.defaultdict(lambda: collections.defaultdict(lambda: ([], [])))
for ri, r in enumerate(rects):
    layer, x1, y1, x2, y2 = r[:5]
    byl[(layer, 'h')][round(y2, 4)][0].append((x1, x2, ri)); byl[(layer, 'h')][round(y1, 4)][1].append((x1, x2, ri))
    byl[(layer, 'v')][round(x2, 4)][0].append((y1, y2, ri)); byl[(layer, 'v')][round(x1, 4)][1].append((y1, y2, ri))
for (layer, d), m in byl.items():
    for coord, (lo, hi) in m.items():
        if lo and hi: join(lo, hi, d == 'h')
# ---------------- point location per layer (bucketed cells)
BK = 10.0
buckets = collections.defaultdict(list)
for ci, (layer, x1, y1, x2, y2, ri) in enumerate(cells):
    for bx in range(int(math.floor(x1 / BK)), int(math.floor(x2 / BK)) + 1):
        for by in range(int(math.floor(y1 / BK)), int(math.floor(y2 / BK)) + 1):
            buckets[(layer, bx, by)].append(ci)
def locate(layer, x, y):
    for ci in buckets.get((layer, int(math.floor(x / BK)), int(math.floor(y / BK))), ()):
        c = cells[ci]
        if c[1] - EPS <= x <= c[3] + EPS and c[2] - EPS <= y <= c[4] + EPS: return ci
    return None
def cells_in_box(layer, box):
    x1, y1, x2, y2 = box; res = {}
    for bx in range(int(math.floor(x1 / BK)), int(math.floor(x2 / BK)) + 1):
        for by in range(int(math.floor(y1 / BK)), int(math.floor(y2 / BK)) + 1):
            for ci in buckets.get((layer, bx, by), ()):
                c = cells[ci]; ov = max(0.0, min(x2, c[3]) - max(x1, c[1])) * max(0.0, min(y2, c[4]) - max(y1, c[2]))
                if ov > 0: res[ci] = ov
    return res
# ---------------- vias
vgroups = collections.defaultdict(lambda: [0, None])     # (via, lower cell, upper cell) -> [cuts, origin]
dangling = collections.Counter()
for vname, lo, hi in VIAS:
    for x, y, n, org in G['vias'].get(vname, []):
        cl, cu = locate(lo, x, y), locate(hi, x, y)
        if cl is None or cu is None: dangling[vname] += n; continue
        g = vgroups[(vname, cl, cu)]; g[0] += n; g[1] = g[1] or org
vkeys = list(vgroups)
for k in vkeys:
    vname, cl, cu = k
    links.append((cl, cu, None, vname, vgroups[k][0], None, ('v', k)))
# ---------------- ports
pads = [p for p in G['ports'] if p['kind'] == 'pad']
sinks = collections.defaultdict(list)
for p in G['ports']:
    if p['kind'] == 'sink': sinks[p['group']].append(p)
sink_w = {}
for g, ps in sinks.items():
    w = collections.Counter()
    for p in ps:
        for ci, ov in cells_in_box(p['layer'], p['box']).items(): w[ci] += ov
    sink_w[g] = w
pad_cells = {}
if a.source_group:
    pads = [dict(kind='pad', group=a.source_group)]
    for ci in sink_w.pop(a.source_group): pad_cells[ci] = 0
for k, p in enumerate(pads):
    if 'box' in p:
        for ci in cells_in_box(p['layer'], p['box']): pad_cells[ci] = k
# ---------------- connectivity; keep the part reachable from a pad
ia = np.array([l[0] for l in links], dtype=np.int64); ib = np.array([l[1] for l in links], dtype=np.int64)
adj = sp.coo_matrix((np.ones(len(links)), (ia, ib)), shape=(N, N))
ncomp, lab = connected_components(adj, directed=False)
padcomp = {int(lab[ci]) for ci in pad_cells}
keep = np.array([lab[i] in padcomp for i in range(N)])
comp_area = collections.Counter(); comp_sinks = collections.defaultdict(set)
for ci, c in enumerate(cells):
    comp_area[int(lab[ci])] += (c[3] - c[1]) * (c[4] - c[2])
for g, w in sink_w.items():
    for ci in w: comp_sinks[int(lab[ci])].add(g)
islands = [dict(component=c, area_um2=round(comp_area[c], 2), sinks=sorted(comp_sinks[c])) for c in range(ncomp) if c not in padcomp]
open_sinks = sorted({g for isl in islands for g in isl['sinks']} - {g for c in padcomp for g in comp_sinks[c]})
# ---------------- resistances
def res(l):
    ca, cb, sq, vname, n, w, owner = l
    if vname: return RS[vname] / n
    return RS[cells[ca][0]] * sq
R = np.array([res(l) for l in links])
RTIE = 1e-6
# ---------------- netlist (mesh only, kept part) + per-case decks
mesh_path = a.outdir / ('%s_%s.cir' % (net, a.tech))
with open(mesh_path, 'w') as f:
    f.write('* %s mesh, tech %s, pitch %g um, %d cells, %d links\n' % (net, a.tech, a.pitch, N, len(links)))
    for k, l in enumerate(links):
        if keep[l[0]]: f.write('R%d n%d n%d %.9g\n' % (k, l[0], l[1], R[k]))
    for ci, pk in pad_cells.items():
        f.write('RT%d n%d pad%d %g\n' % (ci, ci, pk, RTIE))
    for pk in range(len(pads)):
        f.write('VP%d pad%d 0 0\n' % (pk, pk))
def case_currents(case):
    """cell -> A drawn (positive) for one load case."""
    cur = collections.Counter(); used = {}
    for gk, amps in loads[case].items():
        g, _, lays = gk.partition('@')
        if g not in sink_w:
            used[gk] = 'not on this net'; continue
        w = {ci: ov for ci, ov in sink_w[g].items() if keep[ci] and (not lays or cells[ci][0] in lays.split('+'))}
        tot = sum(w.values())
        if tot <= 0:
            used[gk] = 'open'; continue
        for ci, ov in w.items(): cur[ci] += amps * ov / tot
        used[gk] = amps
    return cur, used
summary = dict(net=net, tech=a.tech, sheet_and_via_ohm=RS, pitch_um=a.pitch, cells=N, links=len(links), via_arrays=len(vkeys),
               dangling_cuts=dict(dangling), pads=[p['group'] for p in pads], islands=islands, open_sinks=open_sinks,
               geom_sha256=hashlib.sha256(a.geom.read_bytes()).hexdigest(), script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               cases={})
kept = np.nonzero(keep)[0]
# conductance matrix for the scipy cross-check (pads as ideal 0 V nodes: eliminated)
isfixed = np.zeros(N, bool)
for ci in pad_cells: isfixed[ci] = True
for case in cases:
    cur, used = case_currents(case)
    deck = a.outdir / ('%s_%s_%s.cir' % (net, a.tech, case)); raw = deck.with_suffix('.raw'); log = deck.with_suffix('.log')
    with open(deck, 'w') as f:
        f.write('* %s %s %s: DC drop, sinks as current sources\n.include %s\n' % (net, a.tech, case, mesh_path.name))
        for ci, amps in cur.items():
            if amps: f.write('I%d n%d 0 %.9g\n' % (ci, ci, amps))
        f.write('.options klu\n.control\nset filetype=ascii\nop\nwrite %s\nquit\n.endc\n.end\n' % raw.name)
    t1 = time.time()
    pr = subprocess.Popen(['ngspice', '-b', deck.name], cwd=str(a.outdir), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    o, _ = pr.communicate(); log.write_bytes(o)
    V = np.zeros(N)
    with open(raw) as f:
        txt = f.read()
    head, _, body = txt.partition('Values:\n')
    names = []
    inv = False
    for line in head.splitlines():
        if line.startswith('Variables:'): inv = True; continue
        if inv:
            t = line.split()
            if len(t) >= 2: names.append(t[1])
    vals = body.split()
    vals = [float(v) for v in vals[1:1 + len(names)]]
    for nm, v in zip(names, vals):
        if nm.startswith('n') and nm[1:].isdigit(): V[int(nm[1:])] = v
        elif nm.startswith('v(n') and nm[3:-1].isdigit(): V[int(nm[3:-1])] = v
    drop = -V      # sinks pull current out: node voltage is minus the drop
    # scipy cross-check (tie resistors to the pads neglected: 1 uOhm)
    free = np.nonzero(keep & ~isfixed)[0]; pos = -np.ones(N, np.int64); pos[free] = np.arange(len(free))
    rows, cols, vals2 = [], [], []
    gsum = np.zeros(len(free))
    for k, l in enumerate(links):
        i, j = l[0], l[1]
        if not keep[i]: continue
        g = 1.0 / R[k]
        for p, q in ((i, j), (j, i)):
            if pos[p] >= 0:
                gsum[pos[p]] += g
                if pos[q] >= 0: rows.append(pos[p]); cols.append(pos[q]); vals2.append(-g)
    rows += list(range(len(free))); cols += list(range(len(free))); vals2 += list(gsum)
    Gm = sp.csr_matrix((vals2, (rows, cols)), shape=(len(free), len(free)))
    rhs = np.zeros(len(free))
    for ci, amps in cur.items():
        if pos[ci] >= 0: rhs[pos[ci]] += amps
    xs = spla.spsolve(Gm.tocsc(), rhs) if len(free) else np.zeros(0)
    dsp = np.zeros(N); dsp[free] = xs
    xcheck = float(np.max(np.abs(dsp[kept] - drop[kept]))) if len(kept) else 0.0
    # IR per sink group
    ir = {}
    for g, w in sink_w.items():
        w2 = {ci: ov for ci, ov in w.items() if keep[ci]}
        if not w2: ir[g] = dict(status='open' if g in open_sinks else 'no cells'); continue
        tot = sum(w2.values())
        ir[g] = dict(load_A=sum(v for k, v in used.items() if k.partition('@')[0] == g and isinstance(v, float)), max_drop_mV=1e3 * max(drop[ci] for ci in w2),
                     mean_drop_mV=1e3 * sum(drop[ci] * ov for ci, ov in w2.items()) / tot, pins=len(sinks[g]))
    # EM. Via arrays: current per cut. Wires: for every rectangle, the net current through each internal cross-section
    # (between two cell columns or rows) and through each of its four edges (inflow from abutting rectangles),
    # divided by the rectangle's extent across that section: the current per wire width of that piece.
    seg = {}
    flow = collections.defaultdict(float)        # (rect, 'x'|'y', index) or (rect, side) -> signed mA
    for k, l in enumerate(links):
        ca, cb, sq, vname, n, w, owner = l
        if not keep[ca]: continue
        Is = (drop[cb] - drop[ca]) / R[k] * 1e3     # mA flowing a -> b (drop rises along the current)
        if vname:
            I = abs(Is); util = I / n / IVIA[vname]; key = owner
            cl, cu = owner[1][1], owner[1][2]
            box = [max(cells[cl][1], cells[cu][1]), max(cells[cl][2], cells[cu][2]), min(cells[cl][3], cells[cu][3]), min(cells[cl][4], cells[cu][4])]
            seg[key] = (util, dict(kind='via', layer=vname, origin=vgroups[owner[1]][1], cuts=n, I_mA=I, I_per_cut_mA=I / n,
                                    limit='%.2f mA/cut' % IVIA[vname], box=box))
        elif owner[0] in ('x', 'y'):
            flow[owner] += Is
        else:
            _, ra, sa, rb, sb = owner
            flow[(ra, sa)] += Is; flow[(rb, sb)] += Is
    for key, Is in flow.items():
        ri = key[0] if len(key) == 2 else key[1]
        r = rects[ri]; layer = r[0]; w, h = r[3] - r[1], r[4] - r[2]
        axis = key[0] if len(key) == 3 else ('x' if key[1] in ('l', 'r') else 'y')
        across = h if axis == 'x' else w          # current along x crosses the rectangle's height
        I = abs(Is); J = I / across
        # a piece is a physically narrow wire when it is at most WTH across the flow and less than half of the two sides
        # that run along the flow abut other metal (otherwise it is a slice of a wider wire): minimum-width limit applies
        sides = ('b', 't') if axis == 'x' else ('l', 'r')
        along = w if axis == 'x' else h
        narrow = layer in WTH and across <= WTH[layer] + 1e-6 and sum(touch[ri][sd] for sd in sides) < 0.5 * along
        if narrow:
            util = I / IMAX_NARROW[layer]; lim = '%.2f mA (w <= %.2f um)' % (IMAX_NARROW[layer], WTH[layer])
        else:
            util = J / JMAX[layer]; lim = '%.0f mA/um' % JMAX[layer]
        k2 = ('r', ri)
        if k2 not in seg or util > seg[k2][0]:
            seg[k2] = (util, dict(kind='wire', layer=layer, origin=r[5], width_um=round(across, 3), I_mA=I, J_mA_per_um=J,
                                  limit=lim, box=[r[1], r[2], r[3], r[4]]))
    ordered = sorted(seg.values(), key=lambda t: -t[0])
    em_rows = [dict(net=net, tech=a.tech, case=case, rank=i + 1, utilisation=u, **d) for i, (u, d) in enumerate(ordered) if u >= a.em_keep or i < 40]
    with open(a.outdir / ('%s_%s_%s_em.csv' % (net, a.tech, case)), 'w', newline='') as f:
        cols = ['net', 'tech', 'case', 'rank', 'kind', 'layer', 'origin', 'width_um', 'cuts', 'I_mA', 'J_mA_per_um', 'I_per_cut_mA', 'limit', 'utilisation', 'box']
        wr = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore'); wr.writeheader()
        for r in em_rows:
            r = dict(r); r['box'] = '(%.3f,%.3f;%.3f,%.3f)' % tuple(r['box'])
            for c in ('I_mA', 'J_mA_per_um', 'I_per_cut_mA', 'utilisation'):
                if c in r: r[c] = '%.4g' % r[c]
            wr.writerow(r)
    by_origin = collections.defaultdict(float)
    for u, d in ordered:
        k = d['origin'] + ':' + d['kind']; by_origin[k] = max(by_origin[k], u)
    (a.outdir / ('%s_%s_%s_ir.json' % (net, a.tech, case))).write_text(json.dumps(ir, indent=1) + '\n')
    ok = pr.returncode == 0 and len(names) > 0
    summary['cases'][case] = dict(ngspice_rc=pr.returncode, ngspice_ok=ok, ngspice_s=round(time.time() - t1, 1), loads=used,
                                  total_A=sum(cur.values()), max_node_drop_mV=1e3 * float(drop[kept].max()) if len(kept) else 0.0,
                                  scipy_max_abs_diff_V=xcheck, ir=ir, em_max_by_origin=dict(by_origin), em_rows=len(em_rows),
                                  em_over_50pct=[dict(utilisation=u, **d) for u, d in ordered if u > 0.5])
summary['wall_s'] = round(time.time() - t0, 1)
(a.outdir / ('%s_%s_summary.json' % (net, a.tech))).write_text(json.dumps(summary, indent=1) + '\n')
print(net, a.tech, 'cells', N, 'links', len(links), 'islands', len(islands), 'open', open_sinks, 'wall', summary['wall_s'])
for c, d in summary['cases'].items():
    print(' ', c, 'ok', d['ngspice_ok'], 'I %.4g A' % d['total_A'], 'max drop %.4g mV' % d['max_node_drop_mV'], 'xcheck %.2g V' % d['scipy_max_abs_diff_V'],
          'EM max', {k: round(v, 4) for k, v in d['em_max_by_origin'].items()})
