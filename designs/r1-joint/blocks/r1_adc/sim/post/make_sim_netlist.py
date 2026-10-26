#!/usr/bin/env python3
"""Simulatable ngspice netlist of the r1_adc layout (T2 post-layout harness, 2026-10-26). Pure Python.

Source of the devices: the layout netlist contract layout/r1_adc_netlist.py (read only): slice_devices(NDUMMY),
top_devices(), slice_map(ch), SLICE_PORTS, TOP_PORTS. So the simulated devices are the LVS reference devices: CDAC
as unit MIMs + dummy units, Cboot / clkgen capacitors as MIM, MSPLIT multi-finger devices, DECAP rectangles, rppd bias
resistors as 4 series segments. Differences to the CDL (simulation only):
  * MOS as X instances of sg13_lv_nmos / sg13_lv_pmos / sg13_hv_nmos / sg13_hv_pmos with w, l, ng (finger count of
    the module) and m=1; cap_cmim with w, l; rppd with w, l, b=0.
  * The comparator output loads Cbp / Cbn (3 fF, model of the SAR flip-flop input; not drawn) are added as ideal
    capacitors on the slice nets xc4_outpb, xc4_outnb, xc5_outpb, xc5_outnb (layout/r1_adc_netlist.py docstring).
  * Port names: '[' and ']' of the bus pins become '_' and '' (adc_raw_a[3] -> adc_raw_a_3). Order = TOP_PORTS.
  * Two top cells: r1_adc_lay (ports = TOP_PORTS) and r1_adc_lay_pr (TOP_PORTS + vref vrefl: the internal reference
    nets exposed as probe ports, for the R2-4 metric and the ideal-reference base runs). Same body.

Parasitics hook (format fixed when the extraction exists):
  --pex-slice FILE     R / C elements of one slice, net names = slice net names (SLICE_PORTS and internal nets such as
                       xs0p_g, lsb_p). Appended to the slice subcircuit (both slice instances).
  --pex-slice-b FILE   optional, slice B only (then two slice subcircuits r1_adc_slice_lay_a / _b).
  --pex-top FILE       R / C elements of the top cell, net names = top net names (TOP_PORTS, vref, vrefl, xref_ng, ...).
  --pex-flat FILE      kpex-style flat extraction of the whole r1_adc: nets with prefix --prefix-a (default
                       'xslice_a_') go to slice A scope, --prefix-b to slice B scope, the rest to the top scope
                       (as r1_afe/pex/make_postlayout.py does with xsin_ / xcos_).
  Mapping rules (per element, after scope assignment): substrate names (VSUBS, sub!, 0) -> ground of the scope
  (gnd in the slice, vss at the top); a known net name -> that net; an unknown name -> for C: ground of the scope
  (counted as lumped_to_ground_F), for R: an internal node 'px_<name>' (reduced RC networks keep their nodes).
  A capacitor between a slice net and a top net (or the other slice) is put to the ground of the scope of the
  first named net (counted). Device terminals stay on the net names: an RC extraction whose device terminals are
  on sub-nodes needs a terminal map (not implemented; see README_harness.md).
usage: make_sim_netlist.py [--out sim/post/r1_adc_lay0.spice] [--report <json>] [pex options]
"""
import argparse, hashlib, json, os, re, sys
from collections import defaultdict
HERE = os.path.dirname(os.path.abspath(__file__))
BLOCK = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(BLOCK, 'layout'))
import r1_adc_netlist as N            # noqa: E402  (layout contract, read only)

MODEL = {'nmos': 'sg13_lv_nmos', 'pmos': 'sg13_lv_pmos', 'nmosHV': 'sg13_hv_nmos', 'pmosHV': 'sg13_hv_pmos'}
CLOADS = ['xc4_outpb', 'xc4_outnb', 'xc5_outpb', 'xc5_outnb']     # Cbp / Cbn of r1_cmp4 / r1_cmp5n, 3 fF each
SUBST = ('vsubs', 'sub!', '0', 'gnd!')


def pname(n):
    return n.replace('[', '_').replace(']', '')


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def r4(x):
    return round(x, 4)


def dev_line(d):
    k = d['kind']
    if k in MODEL:
        return 'X%s %s %s w=%gu l=%gu ng=%d m=%d' % (d['name'], ' '.join(d['nets']), MODEL[k], r4(d['w']), r4(d['l']), d.get('ng', 1), d.get('m', 1))
    if k == 'rppd':
        assert d.get('m', 1) == 1, d
        return 'X%s %s rppd w=%gu l=%gu m=1 b=0' % (d['name'], ' '.join(d['nets']), r4(d['w']), r4(d['l']))
    if k == 'cmim':
        return 'X%s %s cap_cmim w=%gu l=%gu m=%d' % (d['name'], ' '.join(d['nets']), r4(d['w']), r4(d['l']), d.get('m', 1))
    raise ValueError(d)


def merge(devs):
    """Identical parallel devices (same kind, nets, w, l, ng) -> one device with m = count. Exact for simulation when the
    parasitics are mapped by net name (all units of a CDAC bit share the plate nets). Why (2026-10-26): each cap_cmim
    is R 55 mOhm + C in the PDK; the ~830 unit MIMs of the CDAC added ~830 stiff internal nodes and the first-conversion
    deck ran 14 x slower than the netlist of record (runs post-fc-tt-lay0, scratch post-dbg-speed). Merged, it runs at
    the speed of the netlist of record. Dummy units (both plates on gnd) merge into one device per slice."""
    out, idx = [], {}
    for d in devs:
        k = (d['kind'], tuple(d['nets']), r4(d['w']), r4(d['l']), d.get('ng', 1))
        if k in idx:
            out[idx[k]]['m'] += d.get('m', 1)
            out[idx[k]]['merged'].append(d['name'])
        else:
            idx[k] = len(out)
            out.append(dict(d, m=d.get('m', 1), merged=[d['name']]))
    return out


def val(s):
    m = re.match(r'^([-+0-9.eE]+)([a-zA-Z]*)$', s)
    if not m:
        raise ValueError(s)
    u = m.group(2).lower()
    mult = 1e6 if u.startswith('meg') else {'': 1, 'a': 1e-18, 'f': 1e-15, 'p': 1e-12, 'n': 1e-9, 'u': 1e-6, 'm': 1e-3, 'k': 1e3, 'g': 1e9}[u[:1]]
    return float(m.group(1)) * mult


def read_rc(path):
    """R and C elements of a spice file: (kind, n1, n2, value). Continuation lines and subckt wrappers are ignored."""
    out = []
    for ln in open(path):
        t = ln.split()
        if not t or t[0][0] in '*.+':
            continue
        c = t[0][0].upper()
        if c in 'RC' and len(t) >= 4:
            v = [x for x in t[3:] if '=' not in x]
            if not v:
                continue
            out.append((c, t[1].replace('\\', ''), t[2].replace('\\', ''), val(v[0])))
    return out


class Scope:
    def __init__(self, name, nets, ground):
        self.name, self.nets, self.ground = name, set(nets), ground
        self.c = defaultdict(float)
        self.r = []
        self.stat = defaultdict(float)
        self.rnodes = set()

    def node(self, n, kind):
        if n.lower() in SUBST:
            return self.ground
        if n in self.nets:
            return n
        if n in self.rnodes:          # internal node of an R network (reduced RC): kept, for R and C alike
            return 'px_' + re.sub(r'[^A-Za-z0-9_]', '_', n)
        return None

    def add_all(self, elems):
        """two passes: names that appear on R elements and are not nets become internal nodes; then add."""
        self.rnodes |= set(x for k, a, b, v in elems if k == 'R' for x in (a, b)
                           if x not in self.nets and x.lower() not in SUBST)
        self.stat['internal_R_nodes'] = len(self.rnodes)
        for e in elems:
            self.add(*e)

    def add(self, kind, a, b, v):
        na, nb = self.node(a, kind), self.node(b, kind)
        if kind == 'C':
            if na is None or nb is None:
                self.stat['lumped_to_ground_F'] += v
                na, nb = na or self.ground, nb or self.ground
            if na != nb:
                self.c[tuple(sorted((na, nb)))] += v
            self.stat['C_F'] += v
            self.stat['C_elements_in'] += 1
        else:
            if na is None or nb is None:
                sys.exit('R element with an unmapped node: %s %s' % (a, b))
            self.r.append((na, nb, v))
            self.stat['R_count'] += 1

    def lines(self, tag):
        L = ['* parasitics, scope %s: %d C (%.4g F total), %d R' % (self.name, len(self.c), sum(self.c.values()), len(self.r))
             + (', %d internal nodes' % len(self.rnodes) if self.rnodes else '')]
        L += ['C%s%d %s %s %.5g' % (tag, k, a, b, c) for k, ((a, b), c) in enumerate(sorted(self.c.items()))]
        L += ['R%s%d %s %s %.5g' % (tag, k, a, b, r) for k, (a, b, r) in enumerate(self.r)]
        return L


def build(args):
    sl = N.slice_devices(N.NDUMMY)
    top = N.top_devices()
    for d in sl + top:
        if d['kind'] in MODEL or d['kind'] == 'rppd':
            assert d.get('m', 1) == 1, d      # the contract draws every device with m = 1
    nsl0, ntop0 = len(sl), len(top)
    if not args.no_merge:
        sl, top = merge(sl), merge(top)
    snets = set(N.SLICE_PORTS) | set(n for d in sl for n in d['nets'])
    tnets = set(N.TOP_PORTS) | set(n for d in top for n in d['nets']) | {'vref', 'vrefl'}
    for ch in 'ab':
        tnets |= set(N.slice_map(ch).values())
    sc = {'a': Scope('slice_a', snets, 'gnd'), 'b': Scope('slice_b', snets, 'gnd'), 'top': Scope('top', tnets, 'vss')}
    sources = {}
    if args.pex_slice:
        sources['slice'] = os.path.relpath(args.pex_slice, BLOCK)
        el = read_rc(args.pex_slice)
        sc['a'].add_all(el)
        if not args.pex_slice_b:
            sc['b'].add_all(el)
    if args.pex_slice_b:
        sources['slice_b'] = os.path.relpath(args.pex_slice_b, BLOCK)
        sc['b'].add_all(read_rc(args.pex_slice_b))
    if args.pex_top:
        sources['top'] = os.path.relpath(args.pex_top, BLOCK)
        sc['top'].add_all(read_rc(args.pex_top))
    cross = 0.0
    if args.pex_flat:
        sources['flat'] = os.path.relpath(args.pex_flat, BLOCK)
        pre = {'a': args.prefix_a, 'b': args.prefix_b}
        per = {'a': [], 'b': [], 'top': []}
        def where(n):
            for ch in 'ab':
                if n.startswith(pre[ch]):
                    return ch, n[len(pre[ch]):]
            return 'top', n
        for kind, a, b, v in read_rc(args.pex_flat):
            (sa, la), (sb, lb) = where(a), where(b)
            if sa == sb or 'vsubs' in (la.lower(), lb.lower()):
                s0 = sa if sa != 'top' or lb.lower() in SUBST else sb
                per[s0].append((kind, la, lb, v))
            elif kind == 'C':      # cross-scope coupling: to ground in the scope of the slice net
                cross += v
                s0, l0 = (sa, la) if sa != 'top' else (sb, lb)
                per[s0].append(('C', l0, '0', v))
            else:
                sys.exit('R element across scopes (%s %s): needs a terminal map' % (a, b))
        for k in per:
            sc[k].add_all(per[k])
    split = bool(args.pex_slice_b or args.pex_flat)
    hdr = ['* r1_adc layout-mapped simulation netlist, written by sim/post/make_sim_netlist.py (do not edit)',
           '* devices: layout/r1_adc_netlist.py (sha256 %s), netlist of record schematic/r1_adc_r5.spice (sha256 %s)'
           % (sha(N.__file__)[:16], sha(N.NETLIST)[:16]),
           '* decap shapes: %s' % ('layout/r1_adc_decap.json' if os.path.exists(N.DECAP_FILE) else 'module default (no decap.json)'),
           '* parasitics: %s' % (json.dumps(sources) if sources else 'none (device-mapped only)'),]
    if not args.no_merge:
        hdr.append('* identical parallel devices merged into m = count (%d -> %d slice, %d -> %d top devices; exact for net-name '
                   'parasitics; --no-merge writes every drawn device)' % (nsl0, len(sl), ntop0, len(top)))
    hdr += [
           '* requires cornerMOSlv/hv.lib, cornerCAP.lib, cornerRES.lib']
    L = list(hdr)
    names = ['a', 'b'] if split else ['']
    for ch in names:
        L.append('.subckt r1_adc_slice_lay%s %s' % ('_' + ch if ch else '', ' '.join(N.SLICE_PORTS)))
        L += [dev_line(d) for d in sl]
        L.append('* not drawn: comparator output loads (SAR flip-flop input model), ideal as in the netlist of record')
        L += ['Cld_%s %s gnd 3f' % (n, n) for n in CLOADS]
        L += sc[ch or 'a'].lines('ps')
        L.append('.ends')
    body = [dev_line(d) for d in top]
    for ch in 'ab':
        m = N.slice_map(ch)
        L_inst = 'Xslice_%s %s r1_adc_slice_lay%s' % (ch, ' '.join(m[p] for p in N.SLICE_PORTS), '_' + ch if split else '')
        body.append(L_inst)
    body += sc['top'].lines('pt')
    ports = [pname(p) for p in N.TOP_PORTS]
    for nm, extra in (('r1_adc_lay', []), ('r1_adc_lay_pr', ['vref', 'vrefl'])):
        L.append('.subckt %s %s' % (nm, ' '.join(ports + extra)))
        L += body
        L.append('.ends')
    L.append('')
    rep = {'tool': 'sim/post/make_sim_netlist.py', 'out': os.path.relpath(args.out, BLOCK), 'sources': sources,
           'layout_netlist_py_sha256': sha(N.__file__), 'netlist_of_record_sha256': sha(N.NETLIST),
           'decap_file': os.path.exists(N.DECAP_FILE), 'ndummy_per_slice': N.NDUMMY, 'merged_parallel': not args.no_merge,
           'drawn_devices': {'slice': nsl0, 'top': ntop0},
           'slice_devices': len(sl), 'top_devices': len(top), 'top_ports': len(ports),
           'scopes': {k: dict(v.stat) for k, v in sc.items()}, 'cross_scope_C_F': cross}
    return L, rep


def check(rep):
    """Cross-check against the netlist of record: total gate W x ng-independent W per model and MIM area per role."""
    sc = N.parse()
    ref = []
    N.flatten(sc, 'r1_adc5_core', {p: p for p in sc['r1_adc5_core']['ports']}, '', {}, ref, skip=('XSAR',))
    N.flatten(sc, 'r1_refbuf5', {p: p for p in sc['r1_refbuf5']['ports']}, 'xref',
              dict(ndec='4', ndecl='2', msf='32', mib='160', msfl='8', mibl='40', ncg='1', mt='1', lt='8u'), ref)
    N.flatten(sc, 'r1_reffilt5', {'vbg': 'vbg', 'gnd': 'gnd'}, 'xfilt', {}, ref)
    lay = N.slice_devices(0) * 2 + N.top_devices()
    def tot(ds):
        t = defaultdict(float)
        for d in ds:
            if d['kind'] in MODEL:
                t['W_um:' + d['kind'] + ':L%g' % r4(d['l'])] += d['w'] * d.get('m', 1)
            elif d['kind'] == 'cmim':
                t['mim_area_um2'] += d['w'] * d['l'] * d.get('m', 1)
            elif d['kind'] == 'rppd':
                t['rppd_sq'] += d['l'] / d['w'] * d.get('m', 1)
        return t
    a, b = tot(ref), tot(lay)
    keys = sorted(set(a) | set(b))
    rep['equivalence_vs_record'] = {k: [round(a.get(k, 0), 3), round(b.get(k, 0), 3)] for k in keys}
    rep['equivalence_note'] = ('[record, layout without dummies]; record MIM area excludes the ideal Cboot / clkgen capacitors '
                               '(layout: 4 x 11.49^2 x 2 slices + 5 x 2.53^2 um2)')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.join(HERE, 'r1_adc_lay0.spice'))
    ap.add_argument('--report', default='')
    ap.add_argument('--pex-slice', default='')
    ap.add_argument('--pex-slice-b', default='')
    ap.add_argument('--pex-top', default='')
    ap.add_argument('--pex-flat', default='')
    ap.add_argument('--prefix-a', default='xslice_a_')
    ap.add_argument('--prefix-b', default='xslice_b_')
    ap.add_argument('--no-merge', action='store_true', help='one instance per drawn device (the first r1_adc_lay0.spice, sha256 25d481a1...)')
    a = ap.parse_args()
    L, rep = build(a)
    open(a.out, 'w').write('\n'.join(L))
    check(rep)
    repf = a.report or a.out.replace('.spice', '_report.json')
    json.dump(rep, open(repf, 'w'), indent=1)
    print('wrote', os.path.relpath(a.out, BLOCK), len(L), 'lines;', os.path.relpath(repf, BLOCK))
    for k, v in rep['equivalence_vs_record'].items():
        print('  %-28s record %12.3f  layout %12.3f' % (k, v[0], v[1]))
