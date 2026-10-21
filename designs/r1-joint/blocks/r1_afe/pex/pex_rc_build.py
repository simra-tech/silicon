#!/usr/bin/env python3
"""r1_afe post-layout RC netlist (layout revision E2). KLayout batch script, run in the pinned container from the block
directory (G1_WORKDIR=designs/r1-joint/blocks/r1_afe):

  flow/run.sh klayout -b -r pex/pex_rc_build.py -rd kchdir=<kpex run dir of the flat channel, r1_afe_ch_flat__r1_afe_ch>
      -rd ktopdir=<kpex run dir of the top cell without channels, r1_afe_top_flat__r1_afe> -rd ports=<r1_afe_ports.json> -rd out=<dir>

Method (the r1_bgr method, layout/pex_build.py of r1_bgr; kpex 0.3.12 RC mode keeps every device on one node per net):
  1. Devices: the LVS reference of layout/r1_afe_netlist.py (revision-E values, unit split, plate orientation), with
     the instance names of the netlist of record, so that the loop-gain probe edits of sim/run_afe.py still apply.
  2. Resistance: per net and per cell (channel cell r1_afe_ch, top cell r1_afe), a KLayout RNetExtractor network
     (klayout.pex, square counting) over Metal1..Metal5 and Via1..Via4 with the PDK typical values (sg13g2_typ.itf:
     Metal1 0.110, Metal2-5 0.088 Ohm/sq, Via1-4 9 Ohm per 0.19 um cut; Metal5 carries the top-level supply straps
     and the MIM bottom plates, whose MIM is removed for the extraction). Net geometry from the LVS databases that
     kpex writes for the two flat extraction layouts (named layers; the PDK LVS run's database has unnamed layers). Ports from the layout generator (layout/r1_afe_ports.json): MOS source and drain Metal1 rails
     (polygon ports), rppd heads (Metal1 vertex), MIM top and bottom plate pins (Metal4 vertex), cell pins (Metal3).
  3. Every net has a main node: the cell pin for port nets, else the port of the first loop-probe device on the
     net (XMN7/XMN8 drain, XCC*, XCX*, XMC1), else its first port. Gate, bulk and rppd substrate terminals and the
     terminals of the loop-probe devices (XMN7, XMN8, XMP7, XMP8, XCC1, XCC2, XCC1B, XCC2B, XCX1, XCX2, XMC1 of both
     OTAs) connect to the main node (the probe edits need the plain net names on these lines).
  4. Capacitance: kpex 2.5D CC of the flat channel cell and of the top cell without the channel instances, lumped
     at the main node of each net (VSUBS -> vss; unnamed nets -> vss, counted). Both channel instances use the
     channel extraction; coupling between the top-level wiring and the channel interior is not extracted.
  5. Not modelled: contact (Cont) resistance, GatPoly and Activ wiring, substrate resistance, TopMetal1/Metal5 plate
     resistance (inside the cap_cmim model).
Outputs in <out>: r1_afe_post_rc.spice (RC), r1_afe_post_c.spice (C only: every port node merged into its net),
r1_afe_post_r.spice (R only), pex_rc_report.json (per-net C totals, R network sizes, ties), pex_rc_build.log.
"""
import json
import os
import sys
from collections import defaultdict

import pya
import klayout.pex as kp

BLOCK = os.getcwd()
sys.path.insert(0, os.path.join(BLOCK, 'layout'))
sys.path.insert(0, os.path.join(BLOCK, 'pex'))
import r1_afe_netlist as N           # noqa: E402
import make_postlayout as MP         # noqa: E402

KCHDIR = kchdir    # noqa: F821  (-rd)
KTOPDIR = ktopdir  # noqa: F821
PORTS = ports      # noqa: F821
KCH = os.path.join(KCHDIR, 'r1_afe_ch_k25d_pex_netlist.spice')
KTOP = os.path.join(KTOPDIR, 'r1_afe_k25d_pex_netlist.spice')
OUT = out          # noqa: F821
os.makedirs(OUT, exist_ok=True)
logf = open(os.path.join(OUT, 'pex_rc_build.log'), 'w')


def P(*a):
    s = ' '.join(str(x) for x in a)
    print(s)
    logf.write(s + '\n')


DBU = 0.001
ALGO = globals().get('algo', 'sq')       # 'sq' (square counting, as r1_bgr; default) or 'tess' (tesselation, check only)
COND = {1: ('metal1_con', 0.110), 2: ('metal2_con', 0.088), 3: ('metal3_con', 0.088), 4: ('metal4_con', 0.088),
        5: ('metal5_con', 0.088)}
VIAS = {11: ('via1_drw', 1, 2), 12: ('via2_drw', 2, 3), 13: ('via3_drw', 3, 4), 14: ('via4_drw', 4, 5)}
RVIA = 9.0 * 0.19 * 0.19
PROBE_DEVS = {'xmn7', 'xmn8', 'xmp7', 'xmp8', 'xcc1', 'xcc2', 'xcc1b', 'xcc2b', 'xcx1', 'xcx2', 'xmc1'}
OTA_PREF = ('xa1', 'xa2')



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
    c.layer = k
    c.resistance = rs
    c.algorithm = kp.Algorithm.Tesselation if ALGO == 'tess' else kp.Algorithm.SquareCounting
    c.triangulation_max_area = 4.0
    c.triangulation_min_b = 0.3
    tech.add_conductor(c)
for k, (_, b, t) in VIAS.items():
    v = kp.RExtractorTechVia()
    v.cut_layer = k
    v.bottom_conductor = b
    v.top_conductor = t
    v.resistance = RVIA
    v.merge_distance = 0.0
    tech.add_via(v)

PJ = json.load(open(PORTS))


def is_probe(dev):
    return dev.startswith(OTA_PREF) and dev.split('_', 1)[1] in PROBE_DEVS


def mos_term_name(kind, t):
    return {0: 'D', 1: 'G', 2: 'S', 3: 'B'}[t]


KRON_MAX = 60      # nets with at most this many port nodes are reduced to port-to-port resistors (exact at DC)
RDROP = 1e6        # reduced resistors above this value are dropped (parallel to metal paths of < 1 kOhm)


def kron(els, keep):
    """exact elimination of the internal nodes of a resistor network (Schur complement); returns port-to-port R."""
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
        rows += [i, j, i, j]
        cols += [i, j, j, i]
        vals += [g, g, -g, -g]
    G = sp.csr_matrix((vals, (rows, cols)), shape=(len(ix), len(ix)))
    Gkk = G[:nk, :nk].toarray()
    if I:
        Gki = G[:nk, nk:].tocsc()
        Gii = G[nk:, nk:].tocsc()
        lu = sla.splu(Gii)
        X = lu.solve(Gki.T.toarray())
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


def build_cell(cname, lvspath, recursive=False):
    """R networks of every net of layout circuit cname. Returns (elements, node_of[(dev, term)], main[net], stats)."""
    lvs, LAY = load_lvs(lvspath)
    circ = lvs.netlist().top_circuit()
    by_net = defaultdict(list)
    for p in PJ[cname]:
        by_net[p['net']].append(p)
    elements, node_of, main, stats = [], {}, {}, dict(nets=0, ports=0, ties=0, open=0, neg=0, missing_net=[])
    for net, plist in sorted(by_net.items()):
        lnet = circ.net_by_name(net)
        pins = [p for p in plist if p['dev'] == '@pin']
        devp = [p for p in plist if p['dev'] != '@pin']
        mainname = net
        if lnet is None:
            stats['missing_net'].append(net)
            main[net] = net
            for p in plist:
                node_of[(p['dev'], p['term'])] = net
            continue
        geo = {k: lvs.shapes_of_net(lnet, LAY[k], recursive).merged() for k in LAY}
        vports, pports, pidx = {}, {}, []      # pidx: (kind, layer, index) -> port record
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
        ex = kp.RNetExtractor(DBU)
        rn = ex.extract(tech, geo, vports, pports)
        # port node names
        pname = {}
        for q, (kind, L, i, p) in enumerate(pidx):
            if p['dev'] == '@pin':
                nm = net
            elif p['dev'].startswith('@'):
                nm = '%s__%s' % (net, p['dev'][1:])      # channel instance pin (top cell)
            else:
                nm = '%s__p%d' % (net, q)
            pname[(kind, L, i)] = nm
            node_of[(p['dev'], p['term'])] = nm
        # main: cell pin, else the first probe-device port, else the first port
        if not pins:
            anc = [pname[(k_, L, i)] for (k_, L, i, p) in pidx if is_probe(p['dev'])]
            mainname = anc[0] if anc else pname[(pidx[0][0], pidx[0][1], pidx[0][2])]
            # rename the main port node to the plain net name
            for key, nm in list(pname.items()):
                if nm == mainname:
                    pname[key] = net
            for key, nm in list(node_of.items()):
                if nm == mainname:
                    node_of[key] = net
            mainname = net
        main[net] = mainname
        # probe devices: every terminal on the main node
        for (k_, L, i, p) in pidx:
            if is_probe(p['dev']):
                node_of[(p['dev'], p['term'])] = net
                pname[(k_, L, i)] = net
        names = {}
        kint = 0
        for node in rn.each_node():
            ty = node.type().to_s()
            if ty in ('VertexPort', 'PolygonPort'):
                kind = 'V' if ty == 'VertexPort' else 'P'
                key = (kind, node.layer(), node.port_index())    # port index counts within (kind, layer)
                if key not in pname:
                    raise SystemExit('port node without definition %s %s' % (net, key))
                names[node.object_id()] = pname[key]
            else:
                names[node.object_id()] = '%s__i%d' % (net, kint)
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
            r = max(r0, 1e-4)
            if a == b:
                continue
            els.append((a, b, r))
            par[f(a)] = f(b)
        want = sorted(set(pname.values()))
        for w in want:
            if f(w) != f(net):
                els.append((w, net, 1e-3))
                par[f(w)] = f(net)
                stats['ties'] += 1
                P('tie', cname, net, w, '-> main (not connected through Metal1-4 in the extracted geometry)')
        nports = len(set(pname.values()) | {net})
        if nports <= KRON_MAX:
            n0 = len(els)
            els = kron(els, set(pname.values()) | {net})
            stats['kron_nets'] = stats.get('kron_nets', 0) + 1
            stats['kron_elements_in'] = stats.get('kron_elements_in', 0) + n0
        elements += els
        stats['nets'] += 1
        stats['ports'] += len(pidx)
    return elements, node_of, main, stats


ch_el, ch_node, ch_main, ch_st = build_cell('r1_afe_ch', os.path.join(KCHDIR, 'r1_afe_ch.lvsdb.gz'))
P('channel: R elements', len(ch_el), ch_st)
top_el, top_node, top_main, top_st = build_cell('r1_afe', os.path.join(KTOPDIR, 'r1_afe.lvsdb.gz'))
P('top: R elements', len(top_el), top_st)


# ---------------------------------------------------------------------------------------------------------------
def tnode(node_of, d, t, net):
    """node of device d terminal t (net = schematic net); gate/bulk/substrate -> main (plain net name)"""
    if d['kind'] in ('nmos', 'pmos') and t in (1, 3):
        return net
    if d['kind'] == 'rppd' and t == 2:
        return net
    return node_of.get((d['name'], t), net)


gp, sc = N.parse()
ch = N.channel_devices()
topd, insts, tports = N.top_devices()
chlines = {t[0].lower(): t for t in sc['r1_afe_ch']['lines']}
L = ['* r1_afe post-layout netlist, layout revision E2 (RC), written by pex/pex_rc_build.py',
     '* devices: LVS reference of layout/r1_afe_netlist.py (revision-E values); R: KLayout RNetExtractor Metal1-5/Via1-4;',
     '* C: kpex 0.3.12 2.5D CC (channel cell; top cell without channels). See the module docstring.']
ota_ext = {}
OTA_TXT = {}


def ota_blocks(mapn):
    """OTA subcircuits with node map mapn (identity: RC view; strip port suffix: C-only view). Returns (lines, ext)."""
    out, exts = [], {}
    for a in OTA_PREF:
        t = chlines[a]
        nodes = [x for x in t[1:] if '=' not in x][:-1]
        pmap = dict(zip(nodes, MP.OTA_PORTS[a]))

        def loc(n, a=a, pmap=pmap):
            base, sep, suf = n.partition('__')
            if base in pmap:
                b = pmap[base]
            elif base.startswith(a + '_'):
                b = base[len(a) + 1:]
            else:
                b = base
            return b + sep + suf
        devs = [d for d in ch if d['path'][0].startswith(a)]
        used, lines = [], []
        for d in devs:
            nets = [mapn(tnode(ch_node, d, i, n)) for i, n in enumerate(d['nets'])]
            for n in nets:
                if n not in used:
                    used.append(n)
            nm = d['name'][len(a) + 1:]
            lines.append(MP.dev_line(d, [loc(n) for n in nets], (nm[1:] if nm.startswith('x') else nm).upper()))
        ext = [n for n in used if n not in nodes]
        exts[a] = ext
        out.append('.subckt %s %s %s' % (MP.OTA_NAME[a], ' '.join(MP.OTA_PORTS[a]), ' '.join(loc(n) for n in ext)))
        out += lines
        out.append('.ends')
    return out, exts


def readcaps(f):
    U = {'a': 1e-18, 'f': 1e-15, 'p': 1e-12, 'n': 1e-9}
    out = []
    for ln in open(f):
        t = ln.split()
        if t and t[0].startswith('Cext'):
            a_, b_ = (t[i].replace('\\', '') for i in (1, 2))
            v = t[3]
            val = float(v[:-1]) * U[v[-1]] if v[-1] in U else float(v)
            out.append((a_, b_, val))
    return out


def lump(caps, known, main):
    acc, stat, tot = defaultdict(float), defaultdict(float), defaultdict(float)
    for a, b, c in caps:
        res = []
        for n in (a, b):
            if n in ('VSUBS', 'vss', 'VSS'):
                res.append(main.get('vss', 'vss'))
            elif n in known:
                res.append(main.get(n, n))
            else:
                res.append(main.get('vss', 'vss'))
                stat['unknown_to_vss_fF'] += c * 1e15
        tot[a] += c
        tot[b] += c
        if res[0] != res[1]:
            acc[tuple(sorted(res))] += c
    return acc, stat, tot


NOC = globals().get('noc', '0') == '1'      # development: R networks only (no kpex netlists needed); not a post-layout view
chnets = set(n for d in ch for n in d['nets']) | set(N.CH_PORTS)
chc, chstat, chtot = lump([] if NOC else readcaps(KCH), chnets, ch_main)
topnets = set(tports) | set(n for d in topd for n in d['nets']) | set(v for _, pm in insts for v in pm.values())
topc, topstat, toptot = lump([] if NOC else readcaps(KTOP), topnets, top_main)


def write(path, with_r, with_c):
    mapn = (lambda n: n) if with_r else (lambda n: n.split('__')[0])   # C-only view: every port node merged
    otxt, oext = ota_blocks(mapn)
    W = list(L) + otxt
    W.append('.subckt r1_afe_ch ' + ' '.join(N.CH_PORTS))
    for a in OTA_PREF:
        t = chlines[a]
        nodes = [x for x in t[1:] if '=' not in x][:-1]
        W.append('%s %s %s %s' % (t[0], ' '.join(nodes), ' '.join(oext[a]), MP.OTA_NAME[a]))
    for d in ch:
        if d['path'][0].startswith(OTA_PREF):
            continue
        W.append(MP.dev_line(d, [mapn(tnode(ch_node, d, i, n)) for i, n in enumerate(d['nets'])], d['name']))
    if with_r:
        for k, (a, b, r) in enumerate(ch_el):
            W.append('Rw%d %s %s %.6g' % (k, a, b, r))
    if with_c:
        for k, ((a, b), c) in enumerate(sorted(chc.items())):
            W.append('Cp%d %s %s %.4g' % (k, a, b, c))
    W.append('.ends')
    W.append('.subckt r1_afe ' + ' '.join(tports))
    for d in topd:
        W.append(MP.dev_line(d, [mapn(tnode(top_node, d, i, n)) for i, n in enumerate(d['nets'])], d['name']))
    for nm, pm in insts:
        W.append('X%s %s r1_afe_ch' % (nm[1:] if nm.startswith('x') else nm,
                                       ' '.join(mapn(top_node.get(('@' + nm, p), pm[p])) for p in N.CH_PORTS)))
    if with_r:
        for k, (a, b, r) in enumerate(top_el):
            W.append('Rt%d %s %s %.6g' % (k, a, b, r))
    if with_c:
        for k, ((a, b), c) in enumerate(sorted(topc.items())):
            W.append('Cq%d %s %s %.4g' % (k, a, b, c))
    W += ['.ends', '']
    open(path, 'w').write('\n'.join(W))


write(os.path.join(OUT, 'r1_afe_post_rc.spice'), True, True)
write(os.path.join(OUT, 'r1_afe_post_c.spice'), False, True)
write(os.path.join(OUT, 'r1_afe_post_r.spice'), True, False)
rsum = defaultdict(float)
for a, b, r in ch_el:
    rsum[a.split('__')[0]] += r
rep = dict(channel=dict(r_elements=len(ch_el), stats=ch_st, c_unknown=chstat, n_caps=len(chc)),
           top=dict(r_elements=len(top_el), stats=top_st, c_unknown=topstat, n_caps=len(topc)),
           channel_net_total_fF={k: round(v * 1e15, 3) for k, v in sorted(chtot.items(), key=lambda kv: -kv[1])},
           top_net_total_fF={k: round(v * 1e15, 3) for k, v in sorted(toptot.items(), key=lambda kv: -kv[1])})
json.dump(rep, open(os.path.join(OUT, 'pex_rc_report.json'), 'w'), indent=1)
P('wrote', OUT)
logf.close()
