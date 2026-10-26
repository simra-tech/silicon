#!/usr/bin/env python3
"""r1_adc netlist handling for the layout (revision 5 netlist of record, unchanged): parse schematic/r1_adc_r5.spice,
flatten the transistor-level part into primitive devices, apply the layout mapping, write the LVS reference CDL.

Layout cells:
  r1_adc_slice  one slice = r1_th4 (track-and-hold, P and N split CDAC, 4 bootstrapped switches, drivers)
                + r1_cmp4 (decisions 1..13) + r1_cmp5n (decision 0). Placed twice (slice A, slice B), identical.
  r1_adc        two slices + r1_cmp4_clkgen + r1_cmp4_bias + r1_cmp5n_bias (shared, as in r1_adc5_core)
                + r1_refbuf5 (option 3c: ndec 4, ndecl 2, msf 32, mib 160, msfl 8, mibl 40, ncg 1, mt 1, lt 8u)
                + r1_reffilt5 (82 um).
Not laid out: r1_sar5_logic (XSPICE behavioural SAR registers; no standard cells in the netlist of record). Its nets
to the analog part are ports of r1_adc (SAR interface, prefix sar_).

Mapping (the only differences between this CDL and the netlist of record; listed in layout/README):
  * CDAC: every cap_cmim with m = k becomes k unit devices (3.78 um); C0 (2.67 um) and the bridge (4.23 um) as drawn.
    Dummy units (3.78 um, top and bottom plate on gnd) in a ring around each sub-array: extra devices, gnd-gnd.
  * ideal capacitors: r1_bootsw Cboot 200 fF -> cap_cmim 11.49 x 11.49 um (199.9 fF with the PDK 1.5 fF/um2 +
    0.04 fF/um model); r1_cmp4_clkgen CD0..CD4 10 fF -> cap_cmim 2.53 x 2.53 um (10.0 fF). The comparator output loads
    Cbp/Cbn 3 fF (model of the SAR flip-flop input) are not drawn; the post-layout decks keep them as ideal 3 fF.
  * multiplier devices (m > 1) are drawn as fewer devices with more fingers (same total W and L), see MSPLIT.
  * decoupling and filter MIM (r1_refbuf5 XCD, XCDL, XCG; r1_reffilt5 XCF) are drawn as the rectangles listed in
    DECAP (MIM.g: max 5625 um2 per MIM device; the 82 x 82 um filter is above it): same total area (+-0.3 %).
    Their TopMetal1 plate is on vss and the Metal5 plate on the signal, so the CDL lists them as (vss, signal).
  * LV PCell fingers are at most 10 um wide: wider fingers are split in the layout (same W and L; ng is not compared).
Usage: python3 r1_adc_netlist.py  -> writes r1_adc_lvs.cdl next to this file and prints device counts
"""
import math, os, re, json

HERE = os.path.dirname(os.path.abspath(__file__))
NETLIST = os.path.join(HERE, '..', 'schematic', 'r1_adc_r5.spice')
PRIM = {'sg13_lv_nmos': 'nmos', 'sg13_lv_pmos': 'pmos', 'sg13_hv_nmos': 'nmosHV', 'sg13_hv_pmos': 'pmosHV',
        'rppd': 'rppd', 'cap_cmim': 'cmim'}
MODEL = {'nmos': 'sg13_lv_nmos', 'pmos': 'sg13_lv_pmos', 'nmosHV': 'sg13_hv_nmos', 'pmosHV': 'sg13_hv_pmos'}
CU, C0S, CBS = 3.78, 2.67, 4.23
CBOOT_S, CCLK_S = 11.49, 2.53
BITS = list(range(13))

SLICE_PORTS = (['in0p', 'in0n', 'in1p', 'in1n', 'trk0', 'trk1'] + ['cp%d' % k for k in BITS] + ['cn%d' % k for k in BITS]
               + ['clk', 'clkb', 'clkn', 'clknb', 'op', 'on', 'onp', 'onn', 'vbp', 'vbn', 'vref', 'vrefl', 'top_p', 'top_n', 'vdd', 'gnd'])

# checklist e pins (r1_top/reports/integration_checklist_e.md, r1_adc)
NORTH = ([('adc_hold', 2.0), ('is_smp', 4.0), ('clk', 6.0), ('adc_start', 9.88), ('adc_sel', 24.28), ('adc_valid_a', 38.68)]
         + [('adc_raw_a[%d]' % k, round(53.08 + 14.4 * k, 2)) for k in range(14)] + [('adc_valid_b', 254.68)]
         + [('adc_raw_b[%d]' % k, round(269.08 + 14.4 * k, 2)) for k in range(12)]
         + [('adc_raw_b[12]', 431.0), ('adc_raw_b[13]', 433.0), ('por_n', 437.0)])
WEST = [('ain_sin_p', 110.0), ('ain_sin_n', 114.0), ('ain_cos_p', 130.0), ('ain_cos_n', 134.0), ('vcm2', 150.0), ('ibias', 165.0)]
EAST = [('ain_isa_p', 110.0), ('ain_isa_n', 114.0), ('ain_isb_p', 130.0), ('ain_isb_n', 134.0), ('vcm', 150.0)]
SOUTH = [('vdda', 50.0), ('vdd', 100.0), ('vss', 150.0), ('vref_in', 400.0)]
BOX = (439.0, 182.3)

# slice port -> top net, per slice (r1_adc5_core instance lines; vrefa = vrefb = vref of r1_refbuf5, gnd = vss)
def slice_map(ch):
    X = ch.upper()
    m = {'in0p': 'ain_sin_p' if ch == 'a' else 'ain_cos_p', 'in0n': 'ain_sin_n' if ch == 'a' else 'ain_cos_n',
         'in1p': 'ain_isa_p' if ch == 'a' else 'ain_isb_p', 'in1n': 'ain_isa_n' if ch == 'a' else 'ain_isb_n',
         'trk0': 'sar_trk%s0' % ch, 'trk1': 'sar_trk%s1' % ch, 'clk': 'sar_clk%s' % ch, 'clkb': 'sar_clk%sb' % ch,
         'clkn': 'sar_clkn%s' % ch, 'clknb': 'sar_clkn%sb' % ch, 'op': 'sar_o%sp' % ch, 'on': 'sar_o%sn' % ch,
         'onp': 'sar_o%snp' % ch, 'onn': 'sar_o%snn' % ch, 'vbp': 'vbp', 'vbn': 'vbn', 'vref': 'vref', 'vrefl': 'vrefl',
         'top_p': 'top%sp' % ch, 'top_n': 'top%sn' % ch, 'vdd': 'vdd', 'gnd': 'vss'}
    for k in BITS:
        m['cp%d' % k] = 'sar_cp%s%d' % (ch, k)
        m['cn%d' % k] = 'sar_cn%s%d' % (ch, k)
    return m

SAR_PORTS = sorted(set(v for ch in 'ab' for v in slice_map(ch).values() if v.startswith('sar_'))) + ['sar_mclk']
PROBES = ['topap', 'topan', 'topbp', 'topbn']     # CDAC top plates (labelled in the layout; simulation probes, no pad)
TOP_PORTS = ([n for n, _ in NORTH] + [n for n, _ in WEST] + [n for n, _ in EAST] + [n for n, _ in SOUTH] + PROBES
             + SAR_PORTS)
NDUMMY = 82           # dummy ring units per slice (34 x 12 ring = 88 slots, minus 6 gaps for the TV1 tab routes)
RSEG = {'xcbias_xrb': 4, 'xcbiasn_xrb': 4}    # rppd 1 x 160 um drawn as 4 series segments of 40 um

# multiplier split: device -> list of (w, ng) drawn devices (sum = m * w)
MSPLIT = {'xref_xmsf': [(80.0, 32)] * 4, 'xref_xmib': [(80.0, 40)] * 4, 'xref_xmsfl': [(80.0, 32)],
          'xref_xmibl': [(80.0, 40)]}
# decoupling / filter MIM as drawn: device -> list of (w, l); totals: XCD 4 x 70^2 = 19600, XCDL 2 x 70^2 = 9800,
# XCG 50^2 = 2500, XCF 82^2 = 6724 um2.  Filled in by the layout generator (decap.json) when present.
DECAP_FILE = os.path.join(HERE, 'r1_adc_decap.json')


def num(v):
    v = v.strip().lower()
    m = re.match(r'^([-+0-9.e]+)([a-z]*)$', v)
    if not m:
        raise ValueError(v)
    x = float(m.group(1)); s = m.group(2)
    mult = {'': 1.0, 'u': 1e-6, 'n': 1e-9, 'p': 1e-12, 'f': 1e-15, 'm': 1e-3, 'k': 1e3}[s[:1] if s[:3] != 'meg' else '']
    return x * mult


def parse(path=NETLIST):
    lines = []
    for raw in open(path).read().splitlines():
        if raw.startswith('+') and lines:
            lines[-1] += ' ' + raw[1:]
        else:
            lines.append(raw)
    subckts, cur = {}, None
    for ln in lines:
        s = ln.strip()
        if not s or s.startswith('*'):
            continue
        t = s.split()
        if t[0].lower() == '.subckt':
            ports = [x for x in t[2:] if '=' not in x]
            defs = dict(x.split('=') for x in t[2:] if '=' in x)
            cur = dict(name=t[1], ports=ports, defaults=defs, lines=[])
            subckts[t[1]] = cur
        elif t[0].lower() == '.ends':
            cur = None
        elif cur is not None and not t[0].startswith('.'):
            cur['lines'].append(t)
    return subckts


def resolve(v, scope):
    v = v.strip()
    if v.startswith('{') and v.endswith('}'):
        return resolve(scope[v[1:-1]], scope)
    return v


def flatten(sc, name, netmap, prefix, params, out, skip=()):
    sub = sc[name]
    scope = dict(sub['defaults']); scope.update(params)
    def net(n):
        if n in netmap:
            return netmap[n]
        return (prefix + '_' + n) if prefix else n
    for t in sub['lines']:
        inst = t[0]
        if inst in skip:
            continue
        iname = (prefix + '_' + inst.lower()) if prefix else inst.lower()
        c = inst[0].upper()
        if c == 'C':      # ideal capacitor
            out.append(dict(kind='cideal', name=iname, nets=[net(t[1]), net(t[2])], value=num(resolve(t[3], scope))))
            continue
        if c in 'ABR' and inst[0] in 'AB':
            continue
        nodes = [x for x in t[1:] if '=' not in x]
        kv = dict(x.split('=') for x in t[1:] if '=' in x)
        model = nodes[-1]; nodes = nodes[:-1]
        if model in PRIM:
            d = dict(kind=PRIM[model], name=iname, nets=[net(n) for n in nodes])
            d['w'] = num(resolve(kv['w'], scope)) * 1e6
            d['l'] = num(resolve(kv['l'], scope)) * 1e6
            d['ng'] = int(float(resolve(kv.get('ng', '1'), scope)))
            d['m'] = int(float(resolve(kv.get('m', '1'), scope)))
            out.append(d)
        else:
            s2 = sc[model]
            p2 = {k: resolve(v, scope) for k, v in kv.items()}
            nm = {s2['ports'][i]: net(n) for i, n in enumerate(nodes)}
            flatten(sc, model, nm, iname, p2, out)
    return out


def slice_raw():
    sc = parse()
    th = sc['r1_th4']
    # slice = r1_th4 + r1_cmp4 + r1_cmp5n with slice-level net names
    thmap = {'in0p': 'in0p', 'in0n': 'in0n', 'in1p': 'in1p', 'in1n': 'in1n', 'trk0': 'trk0', 'trk1': 'trk1',
             'top_p': 'top_p', 'top_n': 'top_n', 'vdd': 'vdd', 'vref': 'vref', 'vrefl': 'vrefl', 'gnd': 'gnd'}
    for k in BITS:
        thmap['cp%d' % k] = 'cp%d' % k; thmap['cn%d' % k] = 'cn%d' % k
    out = flatten(sc, 'r1_th4', thmap, '', {}, [])
    flatten(sc, 'r1_cmp4', {'inp': 'top_p', 'inn': 'top_n', 'clk': 'clk', 'clkb': 'clkb', 'outp': 'op', 'outn': 'on',
                            'vbp': 'vbp', 'vdd': 'vdd', 'gnd': 'gnd'}, 'xc4', {}, out)
    flatten(sc, 'r1_cmp5n', {'inp': 'top_p', 'inn': 'top_n', 'clk': 'clkn', 'clkb': 'clknb', 'outp': 'onp', 'outn': 'onn',
                             'vbn': 'vbn', 'vdd': 'vdd', 'gnd': 'gnd'}, 'xc5', {}, out)
    return out


def top_raw():
    sc = parse()
    out = []
    flatten(sc, 'r1_cmp4_clkgen', {'clk30': 'clk', 'mclk': 'sar_mclk', 'mclkb': 'mclkb', 'vdd': 'vdd', 'gnd': 'vss'}, 'xckg', {}, out)
    flatten(sc, 'r1_cmp4_bias', {'vbp': 'vbp', 'vdd': 'vdd', 'gnd': 'vss'}, 'xcbias', {}, out)
    flatten(sc, 'r1_cmp5n_bias', {'vbn': 'vbn', 'vdd': 'vdd', 'gnd': 'vss'}, 'xcbiasn', {}, out)
    flatten(sc, 'r1_refbuf5', {'vbg': 'vref_in', 'vref': 'vref', 'vrefl': 'vrefl', 'nb': 'ibias', 'vdda': 'vdda', 'gnd': 'vss'},
            'xref', dict(ndec='4', ndecl='2', msf='32', mib='160', msfl='8', mibl='40', ncg='1', mt='1', lt='8u'), out)
    flatten(sc, 'r1_reffilt5', {'vbg': 'vref_in', 'gnd': 'vss'}, 'xfilt', {}, out)
    return out


def r5(x):
    return round(round(x / 0.005) * 0.005, 4)


def cdac_units(side):
    """unit devices of one CDAC side (P or N) of a slice: dict(name, kind='cmim', w, l, nets=[top, bottom], bit, arr)."""
    s = side.lower()
    top, lsb = 'top_' + s, 'lsb_' + s
    b = lambda k: 'b%s%d' % (s, k)
    msb, lsbu = [], []
    for k, n in ((12, 16), (11, 8), (10, 4), (9, 2), (8, 1)):
        for u in range(n):
            msb.append(dict(kind='cmim', name='xdac%s_xc%d_u%d' % (s, k, u), w=CU, l=CU, nets=[top, b(k)], bit=k, arr='m'))
    msb.append(dict(kind='cmim', name='xdac%s_xcb' % s, w=CBS, l=CBS, nets=[top, lsb], bit='cb', arr='m'))
    for k, n in ((7, 64), (6, 32), (5, 16), (4, 8), (3, 4), (2, 2), (1, 1)):
        for u in range(n):
            lsbu.append(dict(kind='cmim', name='xdac%s_xc%d_u%d' % (s, k, u), w=CU, l=CU, nets=[lsb, b(k)], bit=k, arr='l'))
    lsbu.append(dict(kind='cmim', name='xdac%s_xc0' % s, w=C0S, l=C0S, nets=[lsb, b(0)], bit=0, arr='l'))
    return msb, lsbu


def slice_devices(ndummy=None):
    """layout device list of r1_adc_slice (MOS, cmim incl. CDAC units, Cboot); ndummy = {'m': n, 'l': n} dummies per side."""
    raw = slice_raw()
    out = []
    for d in raw:
        if d['kind'] == 'cideal':
            if 'cboot' in d['name']:
                out.append(dict(kind='cmim', name=d['name'], w=CBOOT_S, l=CBOOT_S, nets=d['nets'], orig=d['name']))
            # comparator output loads Cbp/Cbn (3 fF) are not drawn
            continue
        if d['kind'] == 'cmim' and '_xdac' in '_' + d['name']:
            continue          # replaced by the unit lists below
        out.append(dict(d, orig=d['name']))
    for side in 'PN':
        msb, lsbu = cdac_units(side)
        out += msb + lsbu
    for u in range(ndummy or 0):
        out.append(dict(kind='cmim', name='xdmy_u%d' % u, w=CU, l=CU, nets=['gnd', 'gnd'], bit='d', arr='d'))
    return out


def decap_shapes():
    if os.path.exists(DECAP_FILE):
        return json.load(open(DECAP_FILE))
    return {'xref_xcd': [[50.0, 98.0]] * 4, 'xref_xcdl': [[50.0, 98.0]] * 2, 'xref_xcg': [[25.51, 98.0]],
            'xfilt_xcf': [[34.305, 98.0], [34.305, 98.0]]}


def top_devices():
    raw = top_raw()
    out = []
    dec = decap_shapes()
    for d in raw:
        if d['kind'] == 'cideal':
            out.append(dict(kind='cmim', name=d['name'], w=CCLK_S, l=CCLK_S, nets=d['nets'], orig=d['name']))
            continue
        if d['name'] in dec:
            for k, (w, l) in enumerate(dec[d['name']]):
                # drawn with the TopMetal1 plate on vss and the Metal5 plate on the signal: terminals (top, bottom)
                out.append(dict(kind='cmim', name='%s_u%d' % (d['name'], k), w=w, l=l, nets=[d['nets'][1], d['nets'][0]],
                                orig=d['name']))
            continue
        if d['name'] in RSEG:
            n = RSEG[d['name']]
            a, b = d['nets'][0], d['nets'][1]
            mids = ['%s_s%d' % (d['name'], k) for k in range(1, n)]
            chain = [a] + mids + [b]
            for k in range(n):
                out.append(dict(d, name='%s_g%d' % (d['name'], k), l=d['l'] / n, nets=[chain[k], chain[k + 1], d['nets'][2]],
                                seg=k, orig=d['name']))
            continue
        if d['name'] in MSPLIT:
            for k, (w, ng) in enumerate(MSPLIT[d['name']]):
                out.append(dict(d, name='%s_s%d' % (d['name'], k), w=w, ng=ng, m=1, orig=d['name']))
            continue
        assert d.get('m', 1) == 1, d
        out.append(dict(d, orig=d['name']))
    return out


def cdl_line(d):
    w, l = d['w'], d['l']
    if d['kind'] in MODEL:
        return 'M%s %s %s w=%gu l=%gu m=1' % (d['name'], ' '.join(d['nets']), MODEL[d['kind']], round(w, 4), round(l, 4))
    if d['kind'] == 'rppd':
        return 'R%s %s rppd w=%gu l=%gu m=1 b=0' % (d['name'], ' '.join(d['nets']), round(w, 4), round(l, 4))
    return 'C%s %s cap_cmim w=%gu l=%gu m=1' % (d['name'], ' '.join(d['nets']), round(w, 4), round(l, 4))


def esc(n):
    return n.replace('[', '<').replace(']', '>')


def write_cdl(path=os.path.join(HERE, 'r1_adc_lvs.cdl'), ndummy=NDUMMY):
    sl = slice_devices(ndummy)
    top = top_devices()
    L = ['* LVS reference CDL for r1_adc (revision 5 netlist of record), written by layout/r1_adc_netlist.py from '
         'schematic/r1_adc_r5.spice', '* mapping: see the module docstring (CDAC units + dummies, Cboot / clkgen caps as MIM, '
         'multiplier and decoupling split); r1_sar5_logic (behavioural) not laid out: its nets are sar_* ports',
         '.subckt r1_adc_slice ' + ' '.join(SLICE_PORTS)]
    L += [cdl_line(d) for d in sl]
    L += ['.ends', '.subckt r1_adc ' + ' '.join(esc(p) for p in TOP_PORTS)]
    L += [cdl_line(d) for d in top]
    for ch in 'ab':
        m = slice_map(ch)
        L.append('Xslice_%s %s r1_adc_slice' % (ch, ' '.join(m[p] for p in SLICE_PORTS)))
    L += ['.ends', '']
    open(path, 'w').write('\n'.join(L))
    return path, sl, top


if __name__ == '__main__':
    from collections import Counter
    p, sl, top = write_cdl(ndummy=NDUMMY)
    print('wrote', p)
    print('slice', len(sl), Counter(d['kind'] for d in sl))
    print('top', len(top), Counter(d['kind'] for d in top))
    print('top ports', len(TOP_PORTS))
