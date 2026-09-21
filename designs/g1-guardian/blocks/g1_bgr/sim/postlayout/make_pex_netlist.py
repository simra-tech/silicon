#!/usr/bin/env python3
"""Turn the kpex (KLayout-PEX 0.3.12, 2.5D engine) SPICE output into an ngspice subcircuit that the
block testbench can .include in place of xschem/g1_bgr.spice.

  python3 make_pex_netlist.py <kpex .spice> <out .spice>

The post-layout netlist used is the capacitance-only (--mode CC) extraction, reports/pex/cc. The RC run
(reports/pex/rc) is kept as evidence only: kpex 0.3.12 splits every net into a resistor tree with
per-terminal "P" nodes, but leaves the device instances on the unsplit net node, so only the nine port
nets (whose label sits on the tree) are connected to their devices through the tree; every internal net's
tree floats and the operating point is singular. The Rext handling below is therefore only exercised when
an RC netlist is converted for experiments.

Edits (format only, no circuit content changes):
- device instances become subcircuit calls of the PDK models: M$n -> XMn (kpex already writes SPICE
  D G S B order), Q$n -> XQn, R$n -> XRn; "$" is a comment character for ngspice;
- kpex writes the HBT emitter geometry and the resistor width/length in micrometres without a unit
  (we=0.07 le=0.9, "0.5 rhigh l=49"): a "u" suffix is appended (model defaults are in metres);
- resistor "ps=0" is dropped (the PCell default 0.18u applies; with b=0 it does not enter the model);
- parasitic node names (\\$12, vss.$94.19) are rewritten to plain identifiers; the substrate node
  VSUBS of the capacitors is mapped to vss (the block's p-substrate is the vss net);
- the parasitic resistors lose the trailing model token "R"; those below R_MERGE (1 Ohm; kpex writes
  0.0 for same-layer node splits and 0.1 .. 0.6 Ohm for short metal pieces) are removed and their two
  nodes merged: at the block's microampere currents they are below 1 uV, and left in place the
  10 .. 1000 S conductances next to gmin = 1e-15 made the operating point matrix singular at 125 C;
- capacitor values with the atto suffix are written as e-18 numbers;
- the subcircuit port list is reduced to the schematic pins (kpex exports every named net); the
  second, empty .SUBCKT block kpex appends is dropped.
"""
import re
import sys

PORTS = 'vdd vss r4 vref iptat pbias pcasc vbe dvbe'
R_MERGE = 1.0     # Ohm: parasitic resistors below this are shorted (RC netlists only, see above)
src, dst = sys.argv[1], sys.argv[2]

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


def nd(tok):
    """node name after merging the zero-resistance splits"""
    return find(node(tok))


# nodes joined by zero-valued parasitic resistors are merged (union-find)
_parent = {}


def find(n):
    _parent.setdefault(n, n)
    while _parent[n] != n:
        _parent[n] = _parent[_parent[n]]
        n = _parent[n]
    return n


def union(a, b):
    ra, rb = find(a), find(b)
    if ra == rb:
        return
    # keep the plain net name (no parasitic suffix) as the representative when there is one
    if ('_' in rb and rb.count('_') >= 2) or ra in PORTS.split():
        _parent[rb] = ra
    else:
        _parent[ra] = rb


for line in lines:
    t = line.split()
    if t and t[0].startswith('Rext') and float(t[3]) < R_MERGE:
        union(node(t[1]), node(t[2]))


def value(tok):
    m = re.match(r'^([-+0-9.eE]+)a$', tok)
    return '%ge-18' % float(m.group(1)) if m else tok


out = ['* G1_BGR post-layout netlist: kpex 2.5D extraction (--mode CC) of layout/g1_bgr.gds, reformatted for ngspice',
       '* by sim/postlayout/make_pex_netlist.py (see its docstring; no circuit content changed).',
       '* source: %s' % src.split('/')[-1]]
n_dev = {'M': 0, 'Q': 0, 'R': 0, 'C': 0, 'Rp': 0}
done = False
for line in lines:
    if done:
        break
    t = line.split()
    if not t or line.startswith('*'):
        continue
    key = t[0]
    if key.upper() == '.SUBCKT':
        out.append('.subckt g1_bgr ' + PORTS)
    elif key.upper() == '.ENDS':
        out.append('.ends g1_bgr')
        done = True
    elif key.startswith('M$'):
        params = [p.lower() for p in t[6:]]
        out.append('XM%s %s %s %s' % (key[2:], ' '.join(nd(x) for x in t[1:5]), t[5], ' '.join(params)))
        n_dev['M'] += 1
    elif key.startswith('Q$'):
        params = []
        for p in t[6:]:
            k, v = p.split('=')
            if k in ('we', 'le') and not re.search(r'[a-zA-Z]$', v):
                v += 'u'
            params.append('%s=%s' % (k, v))
        out.append('XQ%s %s %s %s' % (key[2:], ' '.join(nd(x) for x in t[1:5]), t[5], ' '.join(params)))
        n_dev['Q'] += 1
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
        out.append('XR%s %s %s %s' % (key[2:], ' '.join(nd(x) for x in t[1:4]), model, ' '.join(params)))
        n_dev['R'] += 1
    elif key.startswith('Cext'):
        a, b = nd(t[1]), nd(t[2])
        if a == b:
            continue      # capacitor between merged nodes
        out.append('%s %s %s %s' % (key, a, b, value(t[3])))
        n_dev['C'] += 1
    elif key.startswith('Rext'):
        v = float(t[3])
        if v < R_MERGE:
            n_dev['Rp_merged'] = n_dev.get('Rp_merged', 0) + 1
            continue      # nodes merged (see above)
        out.append('%s %s %s %g' % (key, nd(t[1]), nd(t[2]), v))
        n_dev['Rp'] += 1
    else:
        raise SystemExit('unhandled line: ' + line)
with open(dst, 'w') as fh:
    fh.write('\n'.join(out) + '\n')
print('wrote', dst, n_dev)
