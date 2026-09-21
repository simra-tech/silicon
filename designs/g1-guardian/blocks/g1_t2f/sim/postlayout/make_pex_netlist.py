#!/usr/bin/env python3
"""Build the post-layout subcircuit g1_t2f_pex.spice from the kpex (KLayout-PEX 0.3.12, 2.5D engine,
--mode CC --blackbox true) outputs in ../../reports/pex/cc:

  g1_t2f_k25d_pex_netlist.spice   device view of the layout (kpex's SPICE writer stops with
                                  "Invalid parameter name: 'C'" at the first cap_cmim device, after all
                                  MOS, HBT and resistor devices have been written, see kpex_stdout.log)
  g1_t2f_k25d_pex_netlist.csv     the 340 extracted capacitances (Device;Net1;Net2;Capacitance [fF])

  python3 make_pex_netlist.py

Edits (format only, no circuit content changes):
- device instances become subcircuit calls of the PDK models: M$n -> XMn (D G S B order as written),
  Q$n -> XQn, R$n -> XRn ("$" is a comment character for ngspice); parameters lower-cased;
- HBT emitter geometry and resistor width/length get their "u" suffix (kpex writes micrometres
  without a unit; the model defaults are in metres); resistor "ps=0" is dropped;
- the two cap_cmim devices, blackboxed in the extraction (their MIM layers are unknown to the kpex
  2.5D technology file, see the README), are added back as the schematic devices C1/C2 (28 x 28 um,
  1.18 pF) between cap1/cap2 and vss; the extraction therefore carries the wiring and plate-tab
  parasitics of those nets but not a parasitic of the MIM plates themselves;
- parasitic node names ($12) become plain identifiers (n12); the substrate node VSUBS is mapped to
  vss (the block's p-substrate is the vss net);
- the port list is reduced to the nine schematic pins (kpex exports every named net).
"""
import csv, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
CC = os.path.join(HERE, '..', '..', 'reports', 'pex', 'cc')
SRC = os.path.join(CC, 'g1_t2f_k25d_pex_netlist.spice')
CSV = os.path.join(CC, 'g1_t2f_k25d_pex_netlist.csv')
DST = os.path.join(HERE, 'g1_t2f_pex.spice')
PORTS = 'vdd vdd12 vss pbias pcasc vref en mode fout'

lines = []
for raw in open(SRC):
    raw = raw.rstrip('\n')
    if raw.startswith('+') and lines:
        lines[-1] += ' ' + raw[1:].strip()
    else:
        lines.append(raw)


def node(tok):
    tok = tok.replace('\\', '')
    if tok == 'VSUBS':
        return 'vss'
    if tok.startswith('$'):
        return 'n' + tok[1:]
    return tok


out = ['* G1_T2F post-layout netlist: kpex 2.5D extraction (--mode CC --blackbox true) of layout/g1_t2f.gds,',
       '* reformatted for ngspice by sim/postlayout/make_pex_netlist.py (see its docstring; no circuit content changed).',
       '.subckt g1_t2f ' + PORTS]
n = {'M': 0, 'Q': 0, 'R': 0, 'C': 0}
for line in lines:
    t = line.split()
    if not t or line.startswith('*') or t[0].upper() in ('.SUBCKT', '.ENDS'):
        continue
    key = t[0]
    if key.startswith('M$'):
        out.append('XM%s %s %s %s' % (key[2:], ' '.join(node(x) for x in t[1:5]), t[5], ' '.join(p.lower() for p in t[6:])))
        n['M'] += 1
    elif key.startswith('Q$'):
        params = []
        for p in t[6:]:
            k, v = p.split('=')
            if k in ('we', 'le') and not re.search(r'[a-zA-Z]$', v):
                v += 'u'
            params.append('%s=%s' % (k, v))
        out.append('XQ%s %s %s %s' % (key[2:], ' '.join(node(x) for x in t[1:5]), t[5], ' '.join(params)))
        n['Q'] += 1
    elif key.startswith('R$'):
        w, model = t[4], t[5]
        params = ['w=%su' % w]
        for p in t[6:]:
            k, v = p.split('=')
            if k == 'ps':
                continue
            if k == 'l' and not re.search(r'[a-zA-Z]$', v):
                v += 'u'
            params.append('%s=%s' % (k, v))
        out.append('XR%s %s %s %s' % (key[2:], ' '.join(node(x) for x in t[1:4]), model, ' '.join(params)))
        n['R'] += 1
    else:
        raise SystemExit('unhandled line: ' + line)
out.append('XC1 cap1 vss cap_cmim w=28u l=28u m=1')
out.append('XC2 cap2 vss cap_cmim w=28u l=28u m=1')
total = 0.0
for row in list(csv.reader(open(CSV), delimiter=';'))[1:]:
    dev, a, b, c = row[0], node(row[1]), node(row[2]), float(row[3])
    if a == b:
        continue
    out.append('Cext_%s %s %s %gf' % (dev[1:], a, b, c))
    n['C'] += 1
    total += c
out.append('.ends g1_t2f')
open(DST, 'w').write('\n'.join(out) + '\n')
print('wrote', DST, n, 'total parasitic %.1f fF' % total)
