#!/usr/bin/env python3
"""Derive the LVS reference netlist from the frozen xschem netlist (sim/netlist/<top>.spice).

The KLayout SG13G2 LVS reader (libs.tech/klayout/tech/lvs/rule_decks/custom_reader.lvs) turns
M/R/C/Q element lines into devices but treats an `X` instance of `sg13_lv_nmos`, `rppd` or
`cap_cmim` as a subcircuit call, so xschem's `XM1 d g s b sg13_lv_nmos w=.. l=..` lines have to
become `MM1 d g s b sg13_lv_nmos w=.. l=..` etc.  Nothing else about the circuit changes:

  X<name> d g s b sg13_{lv,hv}_{n,p}mos w= l= ng= m= mm_ok=1  ->  M<name> d g s b model w= l= m=
  X<name> p m sub! rppd w= l= m= b= mm_ok=1                  ->  R<name> p m vss rppd w= l= b= m=
  X<name> a b cap_cmim w= l= m= mm_ok=1                       ->  C<name> a b cap_cmim w= l= m=
  X<name> anode cathode dantenna l= w=                        ->  D<name> anode cathode dantenna w= l=

`sub!` is xschem's global substrate node; in the layout the rppd body sits in the p substrate
that the guard rings tie to vss, so the body pin is written as vss (every subcircuit that
contains an rppd has vss as a port).  `mm_ok` and `ng` are simulator-only flags (the reader
takes w as the total width; the extractor sums parallel fingers).  Optionally the top-level
port names are mapped to the macro pin names of blocks/g1_padring/INTEGRATION.md.

Usage: python3 lvs_netlist.py <in.spice> <out.cdl> [top=<name>] [portmap=a:b,c:d,...]
"""
import re
import sys

MOS = ('sg13_lv_nmos', 'sg13_lv_pmos', 'sg13_hv_nmos', 'sg13_hv_pmos')


def convert(lines, top=None, portmap=None):
    out = []
    in_top = False
    joined = []
    # join continuation lines first
    for ln in lines:
        if ln.startswith('+') and joined:
            joined[-1] = joined[-1].rstrip('\n') + ' ' + ln[1:].strip() + '\n'
        else:
            joined.append(ln)
    for ln in joined:
        s = ln.strip()
        if not s or s.startswith('*') or s == '.end':
            continue
        low = s.lower()
        if low.startswith('.subckt'):
            toks = s.split()
            in_top = (top is not None and toks[1] == top)
            if in_top and portmap:
                toks = [toks[0], toks[1]] + [portmap.get(t, t) for t in toks[2:]]
            out.append(' '.join(toks))
            continue
        if low.startswith('.ends'):
            in_top = False
            out.append(s)
            continue
        toks = s.split()
        params = [t for t in toks if '=' in t]
        nets_model = [t for t in toks if '=' not in t]
        name = nets_model[0]
        model = nets_model[-1]
        nets = [('vss' if n == 'sub!' else n) for n in nets_model[1:-1]]
        if in_top and portmap:
            nets = [portmap.get(n, n) for n in nets]
        pd = dict(p.split('=', 1) for p in params)
        if name.startswith('X') and model in MOS:
            keep = ['w=%s' % pd['w'], 'l=%s' % pd['l'], 'm=%s' % pd.get('m', '1')]
            out.append('M%s %s %s %s' % (name[1:], ' '.join(nets), model, ' '.join(keep)))
        elif name.startswith('X') and model == 'rppd':
            keep = ['w=%s' % pd['w'], 'l=%s' % pd['l'], 'b=%s' % pd.get('b', '0'), 'm=%s' % pd.get('m', '1')]
            out.append('R%s %s rppd %s' % (name[1:], ' '.join(nets), ' '.join(keep)))
        elif name.startswith('X') and model == 'cap_cmim':
            keep = ['w=%s' % pd['w'], 'l=%s' % pd['l'], 'm=%s' % pd.get('m', '1')]
            out.append('C%s %s cap_cmim %s' % (name[1:], ' '.join(nets), ' '.join(keep)))
        elif name.startswith('X') and model in ('dantenna', 'dpantenna'):
            # antenna diode (reader: A = w*l, P = 2(w+l); extractor: the n+ (dantenna) / p+ (dpantenna) area)
            out.append('D%s %s %s w=%s l=%s' % (name[1:], ' '.join(nets), model, pd['w'], pd['l']))
        else:
            # subcircuit instance: keep as is (params dropped: none are used)
            out.append('%s %s %s' % (name, ' '.join(nets), model))
    return out


def main():
    src, dst = sys.argv[1], sys.argv[2]
    top = None
    portmap = {}
    for a in sys.argv[3:]:
        if a.startswith('top='):
            top = a[4:]
        elif a.startswith('portmap='):
            for kv in a[8:].split(','):
                k, v = kv.split(':')
                portmap[k] = v
    lines = open(src).read().splitlines(True)
    out = convert(lines, top, portmap)
    with open(dst, 'w') as f:
        f.write('* LVS reference netlist derived from %s by lvs_netlist.py (see docstring)\n' % re.sub(r'.*/', '', src))
        f.write('\n'.join(out) + '\n')
    print('wrote', dst, len(out), 'lines')


if __name__ == '__main__':
    main()
