#!/usr/bin/env python3
"""r1_adc post-layout RC netlist (layout A). KLayout batch script, pinned container, G1_WORKDIR=designs/r1-joint/blocks/r1_adc:

  flow/run.sh klayout -b -r pex/pex_build.py -rd kdir=<pex run dir with kpex_slice/ and kpex_top/> -rd out=<dir>

Method (the method of r1_afe/pex/pex_rc_build.py, revision E2/E3; kpex 0.3.12 RC mode keeps every device on one
node per net, so the resistance comes from KLayout's RNetExtractor):
  1. Devices: the LVS reference devices of layout/r1_adc_netlist.py (netlist of record schematic/r1_adc_r5.spice,
     unchanged), with the finger count drawn in the layout (LV fingers <= 10 um; xc4_xs1_xmtc 4 fingers).
  2. Resistance: per net and per cell (slice r1_adc_slice, top r1_adc without the slices), a KLayout RNetExtractor
     network (square counting) over Metal1..Metal5 and Via1..Via4 with the PDK typical values (Metal1 0.110,
     Metal2-5 0.088 Ohm/sq, Via1-4 9 Ohm per 0.19 um cut). Net geometry from the LVS databases of the kpex runs.
     Ports (layout/r1_adc_layout.json): MOS source / drain Metal1 or Metal2 rails and LV gate rails (polygon ports),
     MIM collector / island / pin points (Metal4 vertex), rppd heads (Metal1 vertex), cell edge pins (Metal3 vertex:
     the generator constants SLICE_SOUTH / WEST / EAST and the floor-plan checklist).
  3. Main node of a net: the first cell pin; else the source of the first follower (vref: xref_xmsf_s0, vrefl:
     xref_xmsfl_s0); else its first port. MOS gate and bulk, rppd body and every terminal without a port connect to
     the main node, except MIM bottom plates of the CDAC (to the collector of the bit) and MIM top plates on an
     island net (to the first island). Port nodes that the extracted Metal1-5 geometry does not join (TopMetal1
     sheets, MIM plates) are tied to the main node with 1 mOhm (counted in the report).
  4. Multi-pin slice nets (gnd, vdd, vrefl): one slice subcircuit port per edge pin (net, net__e1, ...), so the
     slice and top networks meet at every pin.
  5. Capacitance: kpex 2.5D CC of the flat slice and of the top cell without the slices, lumped at the main node of
     each net (VSUBS -> gnd / vss; unnamed nets -> ground, counted). Both slice instances use the slice extraction;
     coupling between the top-level wiring and the slice interior is not extracted.
  6. Not modelled: contact resistance, GatPoly / Activ wiring, substrate resistance, TopMetal1 / Metal5 plate
     resistance (inside the cap_cmim model), MIM bit-line resistance between the units and the collector.
  7. Layout B (2026-10-26): the slice gnd has no edge pins; it is fed by the vss drops (generator constant SLICE_DROPS,
     Metal4 pads on the slice gnd strap). Each drop is one slice port. At the top level, the drop path (Metal4 pad, Via4,
     Metal5 island, TopVia1, TopMetal1 sheet) is not in the R extraction (pex_prepare.py removes the TopMetal1 inside the
     MIM, so the sheet is cut): each used drop is joined to the top vss main node by RDROP_EST (estimated, see below);
     unused drop positions of a slice instance get a dangling node.
  8. Layout B, build B.1 (2026-10-26): the top-level MIM decoupling plates have Metal5 ports (see DECAP_PORTS).
Outputs in <out>: r1_adc_post_rc.spice (subcircuits r1_adc_lay and r1_adc_lay_pr, the port lists of
sim/post/make_sim_netlist.py), r1_adc_post_c.spice (C only, port nodes merged), pex_report.json, pex_build.log.
"""
import ast
import json
import math
import os
import re
import sys
from collections import defaultdict

import pya
import klayout.pex as kp

BLOCK = os.getcwd()
sys.path.insert(0, os.path.join(BLOCK, 'layout'))
import r1_adc_netlist as N           # noqa: E402

KDIR = kdir        # noqa: F821  (-rd)
OUT = out          # noqa: F821
os.makedirs(OUT, exist_ok=True)
logf = open(os.path.join(OUT, 'pex_build.log'), 'w')


def P(*a):
    s = ' '.join(str(x) for x in a)
    print(s)
    logf.write(s + '\n')


DBU = 0.001
COND = {1: ('metal1_con', 0.110), 2: ('metal2_con', 0.088), 3: ('metal3_con', 0.088), 4: ('metal4_con', 0.088),
        5: ('metal5_con', 0.088)}
VIAS = {11: ('via1_drw', 1, 2), 12: ('via2_drw', 2, 3), 13: ('via3_drw', 3, 4), 14: ('via4_drw', 4, 5)}
RVIA = 9.0 * 0.19 * 0.19
KRON_MAX = 60
RDROP = 1e6
SRC = open(os.path.join(BLOCK, 'layout', 'r1_adc_layout.py')).read()


def const(name):
    return ast.literal_eval(re.search(r'^%s = ([\[\(].*?[\]\)])\s*(#.*)?$' % name, SRC, re.M | re.S).group(1))


SX = const('SX'); SY = float(re.search(r'^SY = ([0-9.]+)', SRC, re.M).group(1))
WS, HS = [float(v) for v in re.search(r'^WS, HS = ([0-9.]+), ([0-9.]+)', SRC, re.M).groups()]
W, H = [float(v) for v in re.search(r'^W, H = ([0-9.]+), ([0-9.]+)', SRC, re.M).groups()]
SLICE_PINS = [(n, 'S', x, 0.0) for n, x in const('SLICE_SOUTH')] + [(n, 'W', 0.0, y) for n, y in const('SLICE_WEST')] + \
             [(n, 'E', WS, y) for n, y in const('SLICE_EAST')]
try:
    SLICE_PINS += [(n, 'D', x, y) for n, x, y in const('SLICE_DROPS')]       # layout B
except AttributeError:
    pass
# layout B: estimated resistance of one vss drop path from the slice gnd strap to the vss pin (not extracted): 12 Via4
# (9 Ohm per cut in this extraction: 0.75 Ohm) + 3 TopVia1 (assumed 2 Ohm per cut: 0.67 Ohm) + TopMetal1 sheet to the
# pin-side gap (about 0.2 Ohm at 0.018 Ohm/sq) + the pin-side island and riser (0.75 + 0.67 + 0.35 Ohm), shared by all
# drops; about 2.0 Ohm per drop (estimated, not extracted)
RDROP_EST = 2.0


def load_lvs(path):
    lvs = pya.LayoutVsSchematic()
    lvs.read(path)
    LAY = {k: lvs.layer_by_name(v[0]) for k, v in COND.items()}
    LAY.update({k: lvs.layer_by_name(v[0]) for k, v in VIAS.items()})
    for k, v in LAY.items():
        if v is None:
            raise RuntimeError('layer %s not in the LVS database %s' % (k, path))
    return lvs, LAY


tech = kp.RExtractorTech()
for k, (_, rs) in COND.items():
    c = kp.RExtractorTechConductor()
    c.layer = k; c.resistance = rs; c.algorithm = kp.Algorithm.SquareCounting
    tech.add_conductor(c)
for k, (_, b, t) in VIAS.items():
    v = kp.RExtractorTechVia()
    v.cut_layer = k; v.bottom_conductor = b; v.top_conductor = t; v.resistance = RVIA; v.merge_distance = 0.0
    tech.add_via(v)

LJ = json.load(open(os.path.join(BLOCK, 'layout', 'r1_adc_layout.json')))
# layout B5 (2026-10-27, T2k): slice north pins (SAR ports) are slice edge pins; the SAR macro pins are top-level pins
# (Metal2 router node of each macro south pin), so each SAR line has R from the macro pin to the slice port; clk
# enters at the Metal5 feed on the macro clk pin; vdd / vss of the macro: extra ports vdd_sar / vss_sar (see write())
B5 = 'edge' in LJ['slice']
if B5:
    SLICE_PINS += [(n, 'N', x, y) for n, lst in sorted(LJ['slice']['edge'].items()) for (side, x, y) in lst if side == 'N']
PORTS = {'r1_adc_slice': [dict(p, key=(p['dev'], p['term'], p['net'])) for p in LJ['ports']['slice']],
         'r1_adc': [dict(p, key=(p['dev'], p['term'], p['net'])) for p in LJ['ports']['top']]}
# cell pins: slice edge pins (one port per pin, numbered per net); top checklist pins and slice-instance pins
cnt = defaultdict(int)
for (n, side, x, y) in SLICE_PINS:
    k = cnt[n]; cnt[n] += 1
    pt = {'S': (x, 0.05), 'W': (0.05, y), 'E': (WS - 0.05, y), 'D': (x, y), 'N': (x, HS - 0.05)}[side]
    PORTS['r1_adc_slice'].append(dict(dev='@pin', term=k, net=n, layer=4 if side == 'D' else 3, box=None, pt=list(pt),
                                      key=('@pin', k, n)))
SLICE_MULTI = {n: c for n, c in cnt.items() if c > 1}
for side, lst in (('N', N.NORTH), ('W', N.WEST), ('E', N.EAST), ('S', N.SOUTH)):
    for n, c in lst:
        pt = {'N': (c, H - 0.3), 'W': (0.3, c), 'E': (W - 0.3, c), 'S': (c, 0.3)}[side]
        L_ = 3
        if B5 and side == 'N':
            if n != 'clk':
                continue             # macro pins: no analog geometry
            xk, yk = LJ['top']['stats']['b5']['clk_feed'][:2]
            pt, L_ = (xk, yk), 5     # Metal5 feed on the macro clk pin
        PORTS['r1_adc'].append(dict(dev='@pin', term=0, net=n, layer=L_, box=None, pt=list(pt), key=('@pin', 0, n)))
if B5:
    for net, x, xg in LJ['top']['stats']['b5_jogs']:
        PORTS['r1_adc'].append(dict(dev='@pin', term=0, net=net, layer=2, box=None, pt=[xg, 180.8], key=('@pin', 0, net)))
    # macro supply points: vdd on the Metal5 riser at the VDD bus, vss on the Metal5 VSS bus (joined to the TopMetal1
    # strap by TopVia1, not extracted: tied with 1 mOhm)
    vx = LJ['top']['stats']['b5']['vdd_riser']['x']
    PORTS['r1_adc'].append(dict(dev='@sar', term=0, net='vdd', layer=5, box=None, pt=[(vx[0] + vx[1]) / 2, H + 5.5], key=('@sar', 0, 'vdd')))
    tx = LJ['top']['stats']['b5']['vss_tm1']['x']
    PORTS['r1_adc'].append(dict(dev='@sar', term=1, net='vss', layer=5, box=None, pt=[(tx[0] + tx[1]) / 2, H + 16.5], key=('@sar', 1, 'vss')))
# layout B (2026-10-26, PEX B.1): top-level MIM decoupling plates (r1_adc_decap plan: xref_xcd, xref_xcdl, xref_xcg,
# xfilt_xcf) get a Metal5 port at the plate centre for the bottom-plate terminal (cap_cmim terminal 1, the Metal5 plate
# that joins the bus through its Via4 array). Before (layout A and the first layout B build), these terminals had no port
# and sat on the main node of the net (for vref / vrefl: the source of the first follower) with no resistance, so the
# slices saw the decoupling through the full follower-to-bus wiring (pessimistic). The top plate (vss, TopMetal1 sheet)
# stays on the main node.
DECAP_PORTS = 0
for u_ in LJ['top']['stats'].get('decap_plan', []):
    PORTS['r1_adc'].append(dict(dev='%s_u%d' % (u_['name'], u_['u']), term=1, net=u_['net'], layer=5, box=None,
                                pt=[u_['x'] + u_['w'] / 2.0, u_['y'] + u_['h'] / 2.0],
                                key=('%s_u%d' % (u_['name'], u_['u']), 1, u_['net'])))
    DECAP_PORTS += 1
USED_DROPS = {(d['slice'], round(d['local_x'], 2)) for d in LJ['top']['stats'].get('vss_drops', [])}
DROP_KEYS = set()
for q, ch in enumerate('ab'):
    m = N.slice_map(ch)
    cnt = defaultdict(int)
    for (n, side, x, y) in SLICE_PINS:
        k = cnt[n]; cnt[n] += 1
        X, Y = SX[q] + x, SY + y
        if side == 'D':
            if (ch, round(x, 2)) in USED_DROPS:
                PORTS['r1_adc'].append(dict(dev='@xslice_' + ch, term=k, net=m[n], layer=4, box=None, pt=[X, Y],
                                            key=('@xslice_' + ch, k, n)))
                DROP_KEYS.add(('@xslice_' + ch, k, n))
            continue
        pt = {'S': (X, Y - 0.1), 'W': (X - 0.1, Y), 'E': (X + 0.1, Y), 'N': (X, Y + 0.1)}[side]
        PORTS['r1_adc'].append(dict(dev='@xslice_' + ch, term=k, net=m[n], layer=3, box=None, pt=list(pt),
                                    key=('@xslice_' + ch, k, n)))
MAIN_PREF = {'vref': ('xref_xmsf_s0', 2), 'vrefl': ('xref_xmsfl_s0', 2)}


def kron(els, keep):
    import numpy as np
    import scipy.sparse as sp
    import scipy.sparse.linalg as sla
    nodes = sorted({n for a, b, _ in els for n in (a, b)})
    par = {n: n for n in nodes}

    def f(x):
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x
    for a, b, _ in els:
        par[f(a)] = f(b)
    live = {f(n) for n in nodes if n in keep}
    nodes = [n for n in nodes if f(n) in live]
    K = [n for n in nodes if n in keep]
    I = [n for n in nodes if n not in keep]
    if len(K) < 2:
        return []
    ix = {n: i for i, n in enumerate(K + I)}
    nk = len(K)
    rows, cols, vals = [], [], []
    for a, b, r in els:
        if a not in ix or b not in ix:
            continue
        g = 1.0 / r
        i, j = ix[a], ix[b]
        rows += [i, j, i, j]; cols += [i, j, j, i]; vals += [g, g, -g, -g]
    G = sp.csr_matrix((vals, (rows, cols)), shape=(len(ix), len(ix)))
    Gkk = G[:nk, :nk].toarray()
    if I:
        Gki = G[:nk, nk:].tocsc(); Gii = G[nk:, nk:].tocsc()
        X = sla.splu(Gii).solve(Gki.T.toarray())
        Gr = Gkk - Gki @ X
    else:
        Gr = Gkk
    out = []
    for i in range(nk):
        for j in range(i + 1, nk):
            g = -Gr[i, j]
            if g > 1.0 / RDROP:
                out.append((K[i], K[j], 1.0 / g))
    return out


def safe(n):
    return re.sub(r'[^A-Za-z0-9_]', '_', n.replace('[', '_').replace(']', ''))


def build_cell(cname, lvspath):
    """R networks of every net of cell cname. Returns (elements, node_of[key], main[net], stats)."""
    lvs, LAY = load_lvs(lvspath)
    circ = lvs.netlist().top_circuit()
    by_net = defaultdict(list)
    for p in PORTS[cname]:
        by_net[p['net']].append(p)
    elements, node_of, main = [], {}, {}
    stats = dict(nets=0, ports=0, ties=0, open=0, neg=0, missing_net=[], kron_nets=0)
    for net, plist in sorted(by_net.items()):
        sn = safe(net)
        lnet = circ.net_by_name(net)
        if lnet is None:
            stats['missing_net'].append(net)
            main[net] = sn
            for p in plist:
                node_of[p['key']] = sn
            continue
        # main port: first pin, else preferred device port, else first port
        pins = [p for p in plist if p['dev'] == '@pin']
        pref = MAIN_PREF.get(net) if cname == 'r1_adc' else None
        mp = pins[0] if pins else ([p for p in plist if pref and (p['dev'], p['term']) == pref] or plist)[0]
        geo = {k: lvs.shapes_of_net(lnet, LAY[k], True).merged() for k in LAY}
        vports, pports, pidx = {}, {}, []
        for p in plist:
            L = p['layer']
            if p['box']:
                b = p['box']
                pports.setdefault(L, []).append(pya.Polygon(pya.Box(int(round(b[0] / DBU)), int(round(b[1] / DBU)),
                                                                    int(round(b[2] / DBU)), int(round(b[3] / DBU)))))
                pidx.append(('P', L, len(pports[L]) - 1, p))
            else:
                vports.setdefault(L, []).append(pya.Point(int(round(p['pt'][0] / DBU)), int(round(p['pt'][1] / DBU))))
                pidx.append(('V', L, len(vports[L]) - 1, p))
        rn = kp.RNetExtractor(DBU).extract(tech, geo, vports, pports)
        pname = {}
        for q, (kind, L, i, p) in enumerate(pidx):
            nm = sn if p is mp else '%s__p%d' % (sn, q)
            pname[(kind, L, i)] = nm
            node_of[p['key']] = nm
        main[net] = sn
        names = {}
        kint = 0
        for node in rn.each_node():
            ty = node.type().to_s()
            if ty in ('VertexPort', 'PolygonPort'):
                key = ('V' if ty == 'VertexPort' else 'P', node.layer(), node.port_index())
                if key not in pname:
                    raise SystemExit('port node without definition %s %s' % (net, key))
                names[node.object_id()] = pname[key]
            else:
                names[node.object_id()] = '%s__i%d' % (sn, kint)
                kint += 1
        par = {}

        def f(x):
            while par.get(x, x) != x:
                x = par[x]
            return x
        els = []
        for e in rn.each_element():
            a, b = names[e.a().object_id()], names[e.b().object_id()]
            r0 = e.resistance()
            if r0 != r0 or r0 > 1e12:
                stats['open'] += 1
                continue
            if r0 < 0:
                stats['neg'] += 1
            if a == b:
                continue
            els.append((a, b, max(r0, 1e-4)))
            par[f(a)] = f(b)
        drop_nodes = {pname[(kind, L, i)] for (kind, L, i, p) in pidx if p['key'] in DROP_KEYS}
        for w in sorted(set(pname.values())):
            if f(w) != f(sn):
                els.append((w, sn, RDROP_EST if w in drop_nodes else 1e-3))
                par[f(w)] = f(sn)
                stats['ties'] += 1
                P('tie', cname, net, w)
        if len(set(pname.values()) | {sn}) <= KRON_MAX:
            els = kron(els, set(pname.values()) | {sn})
            stats['kron_nets'] += 1
        elements += els
        stats['nets'] += 1
        stats['ports'] += len(pidx)
    return elements, node_of, main, stats


SDIR = os.path.join(KDIR, 'kpex_slice', 'r1_adc_slice_flat__r1_adc_slice')
TDIR = os.path.join(KDIR, 'kpex_top', 'r1_adc_top_flat__r1_adc')
sl_el, sl_node, sl_main, sl_st = build_cell('r1_adc_slice', os.path.join(SDIR, 'r1_adc_slice.lvsdb.gz'))
P('slice: R elements', len(sl_el), json.dumps(sl_st)[:400])
tp_el, tp_node, tp_main, tp_st = build_cell('r1_adc', os.path.join(TDIR, 'r1_adc.lvsdb.gz'))
P('top: R elements', len(tp_el), json.dumps(tp_st)[:400])

MODEL = {'nmos': 'sg13_lv_nmos', 'pmos': 'sg13_lv_pmos', 'nmosHV': 'sg13_hv_nmos', 'pmosHV': 'sg13_hv_pmos'}
NG_OVERRIDE = {'xc4_xs1_xmtc': 4}


def layout_ng(d):
    ng = NG_OVERRIDE.get(d['name'], d.get('ng', 1))
    if d['kind'] in ('nmos', 'pmos') and d['w'] / ng > 10.0 + 1e-9:
        ng = ng * int(math.ceil(d['w'] / ng / 10.0 - 1e-9))
    return ng


def dev_line(d, nodes):
    k = d['kind']
    if k in MODEL:
        return 'X%s %s %s w=%gu l=%gu ng=%d m=1' % (d['name'], ' '.join(nodes), MODEL[k], round(d['w'], 4), round(d['l'], 4), layout_ng(d))
    if k == 'rppd':
        return 'X%s %s rppd w=%gu l=%gu m=1 b=0' % (d['name'], ' '.join(nodes), round(d['w'], 4), round(d['l'], 4))
    return 'X%s %s cap_cmim w=%gu l=%gu m=1' % (d['name'], ' '.join(nodes), round(d['w'], 4), round(d['l'], 4))


def term_nodes(d, node_of, main, cname):
    out = []
    for t, net in enumerate(d['nets']):
        sn = main.get(net, safe(net))
        k = (d['name'], t, net)
        if d['kind'] in MODEL and t in (1, 3) and k not in node_of:
            out.append(sn)               # gate (no rail port) and bulk: main node
        elif d['kind'] == 'rppd' and t == 2:
            out.append(sn)
        elif k in node_of:
            out.append(node_of[k])
        else:
            coll = [v for kk, v in node_of.items() if kk[0] == '@coll' and kk[2] == net]
            isl = [v for kk, v in node_of.items() if kk[0] == '@isl' and kk[2] == net]
            out.append(coll[0] if coll else (isl[0] if isl else sn))
    return out


def readcaps(f):
    U = {'a': 1e-18, 'f': 1e-15, 'p': 1e-12, 'n': 1e-9}
    out = []
    for ln in open(f):
        t = ln.split()
        if t and t[0].startswith('Cext'):
            a_, b_ = (t[i].replace('\\', '') for i in (1, 2))
            v = t[3]
            out.append((a_, b_, float(v[:-1]) * U[v[-1]] if v[-1] in U else float(v)))
    return out


def lump(caps, known, main, gnd):
    acc, tot = defaultdict(float), defaultdict(float)
    stat = dict(unknown_to_ground_fF=0.0, renamed_fF=0.0, unknown_nets={})
    for a, b, c in caps:
        res, nm = [], []
        for n in (a, b):
            if n not in known and '$' in n and n.split('$')[0] in known:
                # a net that the MIM strip cuts in two (CDAC top plates: the sheets join the halves) keeps its name
                stat['renamed_fF'] += c * 1e15
                n = n.split('$')[0]
            nm.append(n)
            if n in ('VSUBS', gnd):
                res.append(main.get(gnd, gnd))
            elif n in known:
                res.append(main.get(n, safe(n)))
            else:
                res.append(main.get(gnd, gnd))
                stat['unknown_to_ground_fF'] += c * 1e15
                stat['unknown_nets'][n] = stat['unknown_nets'].get(n, 0) + c * 1e15
        tot[nm[0]] += c; tot[nm[1]] += c
        if res[0] != res[1]:
            acc[tuple(sorted(res))] += c
    return acc, stat, tot


sld = N.slice_devices(N.NDUMMY)
tpd = N.top_devices()
snets = set(N.SLICE_PORTS) | set(n for d in sld for n in d['nets'])
tnets = set(N.TOP_PORTS) | set(n for d in tpd for n in d['nets']) | {'vref', 'vrefl'}
for ch in 'ab':
    tnets |= set(N.slice_map(ch).values())
slc, slstat, sltot = lump(readcaps(os.path.join(SDIR, 'r1_adc_slice_k25d_pex_netlist.spice')), snets, sl_main, 'gnd')
tpc, tpstat, tptot = lump(readcaps(os.path.join(TDIR, 'r1_adc_k25d_pex_netlist.spice')), tnets, tp_main, 'vss')
CLOADS = ['xc4_outpb', 'xc4_outnb', 'xc5_outpb', 'xc5_outnb']


def slice_ports():
    ps = []
    for p in N.SLICE_PORTS:
        ps.append((p, ('@pin', 0, p)))
        for k in range(1, SLICE_MULTI.get(p, 1)):
            ps.append(('%s__e%d' % (p, k), ('@pin', k, p)))
    return ps


def write(path, with_r):
    mapn = (lambda n: n) if with_r else (lambda n: n.split('__')[0])
    L = ['* r1_adc post-layout netlist, layout %s (%s), written by pex/pex_build.py; see its docstring' % (globals().get('tag', 'B'), 'RC' if with_r else 'C only'),
         '* devices: LVS reference of layout/r1_adc_netlist.py; R: KLayout RNetExtractor Metal1-5/Via1-4; C: kpex 0.3.12 2.5D CC',
         '* requires cornerMOSlv/hv.lib, cornerCAP.lib, cornerRES.lib']
    sp = slice_ports()
    # slice port nodes: the pin node of each edge pin, else the main node
    spn = [mapn(sl_node.get(key, sl_main.get(p0, safe(p0)))) for p0, key in [(key[2], key) for _, key in sp]]
    seen = set(); hdr = []
    for n in spn:
        assert n not in seen or not with_r, ('duplicate slice port node', n)
        seen.add(n); hdr.append(n)
    L.append('.subckt r1_adc_slice_post ' + ' '.join(hdr if with_r else [safe(p) for p in N.SLICE_PORTS]))
    for d in sld:
        L.append(dev_line(d, [mapn(x) for x in term_nodes(d, sl_node, sl_main, 'r1_adc_slice')]))
    L += ['Cld_%s %s %s 3f' % (n, mapn(sl_main.get(n, n)), mapn(sl_main.get('gnd', 'gnd'))) for n in CLOADS]
    if with_r:
        L += ['Rw%d %s %s %.6g' % (k, a, b, r) for k, (a, b, r) in enumerate(sl_el)]
    L += ['Cp%d %s %s %.4g' % (k, mapn(a), mapn(b), c) for k, ((a, b), c) in enumerate(sorted(slc.items())) if mapn(a) != mapn(b)]
    L.append('.ends')
    body = []
    for d in tpd:
        body.append(dev_line(d, [mapn(x) for x in term_nodes(d, tp_node, tp_main, 'r1_adc')]))
    for ch in 'ab':
        m = N.slice_map(ch)
        if with_r:
            drop_k = {(k_, n_) for k_, n_ in [(i_, 'gnd') for i_ in range(len([1 for p_ in SLICE_PINS if p_[1] == 'D']))]}
            nodes = []
            for _, key in sp:
                kk = ('@xslice_' + ch, key[1], key[2])
                if kk in tp_node:
                    nodes.append(tp_node[kk])
                elif key[2] == 'gnd' and (key[1], 'gnd') in drop_k:
                    nodes.append('xslice_%s_gnd_nc%d' % (ch, key[1]))       # unused drop position: dangling node
                else:
                    nodes.append(tp_main.get(m[key[2]], safe(m[key[2]])))
        else:
            nodes = [safe(m[p]) for p in N.SLICE_PORTS]
        body.append('Xslice_%s %s r1_adc_slice_post' % (ch, ' '.join(mapn(n) for n in nodes)))
    if with_r:
        body += ['Rt%d %s %s %.6g' % (k, a, b, r) for k, (a, b, r) in enumerate(tp_el)]
    body += ['Cq%d %s %s %.4g' % (k, mapn(a), mapn(b), c) for k, ((a, b), c) in enumerate(sorted(tpc.items())) if mapn(a) != mapn(b)]
    ports = [safe(p) for p in N.TOP_PORTS]
    cells = [('r1_adc_lay', []), ('r1_adc_lay_pr', ['vref', 'vrefl'])]
    if B5:
        # layout B5: r1_adc_lay and r1_adc_lay_pr keep the B4 port list (behavioural-SAR decks unchanged; the macro supply
        # points stay internal). r1_adc_lay_sar = r1_adc_lay_pr + two ports vdd_sar, vss_sar: the macro VDD and VSS points
        # (Metal5 buses over the macro), joined by 1 mOhm to their extracted nodes; the gate-level SAR connects there
        vn = mapn(tp_node[('@sar', 0, 'vdd')]) if with_r else 'vdd'
        sn_ = mapn(tp_node[('@sar', 1, 'vss')]) if with_r else 'vss'
        cells.append(('r1_adc_lay_sar', ['vref', 'vrefl', 'vdd_sar', 'vss_sar']))
    for nm, extra in cells:
        L.append('.subckt %s %s' % (nm, ' '.join(ports + extra)))
        if nm == 'r1_adc_lay_sar':
            L += ['Rsar_vdd vdd_sar %s 1m' % vn, 'Rsar_vss vss_sar %s 1m' % sn_]
        L += body
        L.append('.ends')
    L.append('')
    open(path, 'w').write('\n'.join(L))


write(os.path.join(OUT, 'r1_adc_post_rc.spice'), True)
write(os.path.join(OUT, 'r1_adc_post_c.spice'), False)
rep = dict(slice=dict(r_elements=len(sl_el), stats=sl_st, c_unknown=slstat, n_caps=len(slc)),
           top=dict(r_elements=len(tp_el), stats=tp_st, c_unknown=tpstat, n_caps=len(tpc)),
           slice_multi_pin_ports=SLICE_MULTI,
           slice_net_total_fF={k: round(v * 1e15, 3) for k, v in sorted(sltot.items(), key=lambda kv: -kv[1])},
           top_net_total_fF={k: round(v * 1e15, 3) for k, v in sorted(tptot.items(), key=lambda kv: -kv[1])},
           slice_lumped_fF={'%s|%s' % k: round(v * 1e15, 3) for k, v in sorted(slc.items(), key=lambda kv: -kv[1])})
json.dump(rep, open(os.path.join(OUT, 'pex_report.json'), 'w'), indent=1)
P('wrote', OUT)
logf.close()
