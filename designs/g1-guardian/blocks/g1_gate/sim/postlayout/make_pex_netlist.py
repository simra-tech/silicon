#!/usr/bin/env python3
"""Turn the kpex (KLayout-PEX 0.3.12, 2.5D engine, --mode CC) SPICE output of a G1 analog macro into
an ngspice netlist that the block testbench can .include in place of the schematic netlist.

  python3 make_pex_netlist.py <kpex .spice> <out .spice> --block sense|gate

Format edits only (no circuit content is changed except where stated):
- device instances become subcircuit calls of the PDK models: M$n -> XMn (kpex writes the MOS
  terminals as S G D B, like the LVS deck's extracted netlist; the model is symmetric),
  R$n -> XRn; "$" is a comment character for ngspice, so every "$" in a name becomes "_";
- kpex writes the resistor width/length in micrometres without a unit ("2 rppd l=76.7"): "u" is
  appended; "ps=0" is dropped (PCell default 0.18u applies; with b=0 it does not enter the model);
- parasitic capacitors "Cext_n a b 28.78a" become "Cn a b 28.78e-18"; the substrate node VSUBS is
  the block's p-substrate = vss;
- the port order of the top subcircuit is rewritten to the schematic's order (the testbench
  instantiates it by position); kpex's hierarchy (one .SUBCKT per layout cell) is kept;
- SENSE only: kpex 0.3.12 has no capacitance model for the MIM layer ("<TODO>" in its technology
  description, the 2.5D engine aborts on it), so the extraction ran on a copy of the GDS without
  the MIM (36/0) and Vmim (129/0) layers. The Miller capacitor of each OTA is therefore missing from
  the kpex output and is ADDED BACK here as the schematic device (XCC cz out cap_cmim w=23u l=23u):
  cz is identified as the terminal of the nulling resistor RZ (rppd w=1 l=6.2) that no MOS touches.
  The Metal5/TopMetal1 plates are still in the GDS, so their fringe/overlap parasitics are included
  (as plain metal, i.e. without the MIM dielectric);
- SENSE only: the extraction ran on the flattened GDS (kpex 0.3.12 extracts parasitics of the top
  cell's own shapes only; with the g1_ota cells in place it wrote no capacitor on any OTA-internal
  net). The OTA-internal nets that the testbench nodesets need (tail fn fp mir out1 vbnc vbpc cz)
  and the top nets vn vp vped_ref are renamed from kpex's $-numbers by device connectivity to
  xota_tail, xbuf_fn, ... (three OTAs told apart by the gate nets of their L = 2 um input pairs).
"""
import re
import sys

args = sys.argv[1:]
block = 'sense'
if '--block' in args:
    i = args.index('--block'); block = args[i + 1]; del args[i:i + 2]
src, dst = args

PORTS = {'sense': 'sense_p sense_n vref iptat isense vped vref_buf vdd vss',
         'gate': 'trip_d clr_d fast_en hard_cmp en_core gate_core fault_core tripped vdd vdda vss'}[block]

# join continuation lines
lines = []
for raw in open(src):
    raw = raw.rstrip('\n')
    if raw.startswith('+') and lines:
        lines[-1] += ' ' + raw[1:].strip()
    else:
        lines.append(raw)


def node(tok):
    tok = tok.replace('\\', '')
    if tok == 'VSUBS':
        return 'vss'
    tok = tok.replace('$', '_').replace('.', '_')
    if tok.startswith('_'):
        tok = 'n' + tok
    return tok


def value(tok):
    m = re.match(r'^([-+0-9.eE]+)a$', tok)
    return '%ge-18' % float(m.group(1)) if m else tok


# ---- parse into subcircuits --------------------------------------------------------------------
subckts = {}      # name -> {'ports': [...], 'M': [...], 'R': [...], 'C': [...], 'X': [...]}
order = []
cur = None
for line in lines:
    t = line.split()
    if not t or line.startswith('*'):
        continue
    key = t[0]
    if key.upper() == '.SUBCKT':
        cur = {'name': t[1], 'ports': [node(p) for p in t[2:]], 'M': [], 'R': [], 'C': [], 'X': []}
        subckts[t[1]] = cur; order.append(t[1])
    elif key.upper() == '.ENDS':
        cur = None
    elif cur is None:
        continue
    elif key.startswith('M$'):
        params = [p.lower() for p in t[6:] if not p.lower().startswith('rfmode')]
        cur['M'].append({'id': key[2:], 'nets': [node(x) for x in t[1:5]], 'model': t[5], 'params': params})
    elif key.startswith('R$'):
        # R$51 n1 n2 bn <w in um> <model> l=<um> ps=0 b=0 m=1
        w, model = t[4], t[5]
        params = ['w=%su' % w]
        for p in t[6:]:
            k, v = p.split('=')
            if k == 'ps':
                continue
            if k == 'l' and not re.search(r'[a-zA-Z]$', v):
                v += 'u'
            params.append('%s=%s' % (k, v))
        cur['R'].append({'id': key[2:], 'nets': [node(x) for x in t[1:4]], 'model': model, 'params': params,
                         'w': float(w), 'l': float(t[6].split('=')[1])})
    elif key.startswith('Cext'):
        cur['C'].append((key[5:], node(t[1]), node(t[2]), value(t[3])))
    elif key.startswith('X$'):
        cur['X'].append({'id': key[2:], 'nets': [node(x) for x in t[1:-1]], 'ref': t[-1]})
    else:
        raise SystemExit('unhandled line: ' + line)


def rename(sc, mapping):
    """rename nets inside subcircuit sc according to mapping {old: new}."""
    def m(n):
        return mapping.get(n, n)
    sc['ports'] = [m(n) for n in sc['ports']]
    for d in sc['M'] + sc['R'] + sc['X']:
        d['nets'] = [m(n) for n in d['nets']]
    sc['C'] = [(i, m(a), m(b), v) for (i, a, b, v) in sc['C']]


notes = []
PORTSET = set(PORTS.split())


def canon_names(sc):
    """kpex merges the labels of a flattened net into one name ("inn|out|vped"): rename such nets
    to the schematic port name among the parts (or the first part when there is no port)."""
    mapping = {}
    names = set(sc['ports'])
    for d in sc['M'] + sc['R'] + sc['X']:
        names.update(d['nets'])
    for (i, a, b, v) in sc['C']:
        names.update((a, b))
    for n in names:
        if '|' in n:
            parts = n.split('|')
            hit = [q for q in parts if q in PORTSET]
            mapping[n] = hit[0] if hit else parts[0]
    rename(sc, mapping)
    return mapping


if block == 'sense':
    top = subckts['g1_sense']
    canon_names(top)
    nets_of = {}                                        # helper: device lists by net
    def L_of(d):
        return [p for p in d['params'] if p.startswith('l=')][0]
    # vn / vp: the far terminals of the two unit resistors on sense_n / sense_p
    for r in top['R']:
        a, b = r['nets'][:2]
        if 'sense_n' in (a, b):
            vn = b if a == 'sense_n' else a
        if 'sense_p' in (a, b):
            vp = b if a == 'sense_p' else a
    rename(top, {vn: 'vn', vp: 'vp'})
    # the three OTAs: group the L=2 PMOS fingers by their tail (source) net
    # (kpex lists interdigitated fingers with alternating S/D orientation: the tail is the net that
    # both gate nets of a pair share)
    cand = {}
    for d in top['M']:
        s, g, dn, b = d['nets']
        if d['model'] == 'sg13_hv_pmos' and L_of(d) == 'l=2u':
            cand.setdefault(s, {})[g] = dn
            cand.setdefault(dn, {})[g] = s
    tails = {t: gates for t, gates in cand.items() if len(gates) == 2}
    mapping = {}
    inst_of_gate = {'vn': 'xota', 'vp': 'xota', 'vped': 'xbuf', 'vref': 'xref', 'vref_buf': 'xref'}
    for tail, gates in tails.items():
        inst = [inst_of_gate[g] for g in gates if g in inst_of_gate][0]
        mapping[tail] = inst + '_tail'
        for g, dn in gates.items():
            side = 'fn' if g in ('vn', 'vped', 'vref_buf') else 'fp'     # inn side = fn, inp side = fp
            mapping[dn] = inst + '_' + side
            if inst == 'xbuf' and g not in ('vped',):
                mapping[g] = 'vped_ref'
        fn = [dn for g, dn in gates.items() if mapping[dn].endswith('_fn')][0]
        fp = [dn for g, dn in gates.items() if mapping[dn].endswith('_fp')][0]
        # NMOS cascodes: source fn -> drain mir, gate vbnc ; source fp -> drain out1
        for d in top['M']:
            s, g, dn, b = d['nets']
            if d['model'] == 'sg13_hv_nmos' and fn in (s, dn) and 'vss' not in (s, dn):
                mapping[s if dn == fn else dn] = inst + '_mir'; mapping[g] = inst + '_vbnc'
            if d['model'] == 'sg13_hv_nmos' and fp in (s, dn) and 'vss' not in (s, dn):
                mapping[s if dn == fp else dn] = inst + '_out1'
        mir = [k for k, v in mapping.items() if v == inst + '_mir'][0]
        out1 = [k for k, v in mapping.items() if v == inst + '_out1'][0]
        for d in top['M']:
            s, g, dn, b = d['nets']
            if d['model'] == 'sg13_hv_pmos' and mir in (s, dn) and 'vdd' not in (s, dn) and g != mir:
                mapping[g] = inst + '_vbpc'
        # cz: the RZ terminal that is not out1
        for r in top['R']:
            if abs(r['w'] - 1.0) < 1e-6 and out1 in r['nets'][:2]:
                cz = [n for n in r['nets'][:2] if n != out1][0]
                mapping[cz] = inst + '_cz'
                top.setdefault('X_extra', []).append('XCC_%s %s_cz %s cap_cmim w=23u l=23u m=1' % (
                    inst, inst, {'xota': 'isense', 'xbuf': 'vped', 'xref': 'vref_buf'}[inst]))
    rename(top, mapping)
    notes.append('flat netlist: OTA internal nets renamed by connectivity to <inst>_<net>: ' +
                 ', '.join('%s<-%s' % (v, k) for k, v in sorted(mapping.items(), key=lambda kv: kv[1])))
    notes.append('top nets renamed: vp<-%s vn<-%s' % (vp, vn))

# ---- write ------------------------------------------------------------------------------------
out = ['* G1_%s post-layout netlist: kpex 2.5D extraction (--mode CC), reformatted for ngspice by' % block.upper(),
       '* sim/postlayout/make_pex_netlist.py (see its docstring). source: %s' % src.split('/')[-1]]
for n in notes:
    out.append('* ' + n)
counts = {}
topname = order[0]
for name in order:
    sc = subckts[name]
    ports = PORTS.split() if name == topname else sc['ports']
    out.append('.subckt %s %s' % (name, ' '.join(ports)))
    for d in sc['M']:
        out.append('XM%s %s %s %s' % (d['id'], ' '.join(d['nets']), d['model'], ' '.join(d['params'])))
    for d in sc['R']:
        out.append('XR%s %s %s %s' % (d['id'], ' '.join(d['nets']), d['model'], ' '.join(d['params'])))
    for x in sc['X']:
        out.append('%s %s %s' % (x.get('name', 'X' + x['id']), ' '.join(x['nets']), x['ref']))
    for e in sc.get('X_extra', []):
        out.append(e)
    for (i, a, b, v) in sc['C']:
        if a != b:
            out.append('C%s %s %s %s' % (i, a, b, v))
    out.append('.ends %s' % name)
    counts[name] = {'M': len(sc['M']), 'R': len(sc['R']), 'C': len(sc['C']), 'X': len(sc['X'])}
with open(dst, 'w') as fh:
    fh.write('\n'.join(out) + '\n')
print('wrote', dst, counts)
