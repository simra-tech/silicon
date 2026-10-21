#!/usr/bin/env python3
"""r1_isense netlist handling for the layout (revision 2): parse schematic/r1_isense.spice (netlist of record,
sha256 af013b95...), flatten one channel (subckt r1_isense_ch, with its two r1_ls level shifters) into primitive
devices, apply the layout unit split, and write the LVS reference CDL (r1_isense_lvs.cdl).

Derived from designs/r1-joint/blocks/r1_afe/layout/r1_afe_netlist.py (track T3, copied 2026-10-21, not imported).
Unit split (the only difference between the CDL and the netlist of record; values are preserved):
  * rhigh longer than RHMAX (40 um): n straight series segments of equal length (RCA/RCB 150 um -> 4 x 37.5 um,
    the same unit as the hold resistors RH1/RH2). Each extra segment adds two head resistances; the post-layout
    netlist carries the split.
  * rppd longer than RMAX (40 um): the same (RDG1/RDG2 50 um -> 2 x 25 um).
  * MOS: total W = w * m and L as in the netlist; the finger count is re-cut so a finger is <= 10 um (HV PCell
    limit). Devices named in SPLIT are drawn as 2 (or 4) sub-devices for common-centroid placement; LVS combines
    parallel fingers and compares W and L only.
  * rppd units of the gain network (RIN, RF, RP) and every cap_cmim: unchanged (one layout unit per netlist device).
The LVS compare runs with --no_series_res, so every resistor segment is compared 1:1.
Usage (python3, no KLayout needed):  python3 r1_isense_netlist.py   -> writes r1_isense_lvs.cdl next to this file
"""
import math, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
NETLIST = os.path.join(HERE, '..', 'schematic', 'r1_isense.spice')
RMAX, RHMAX = 40.0, 40.0
PRIM = {'sg13_hv_nmos': 'nmos', 'sg13_hv_pmos': 'pmos', 'sg13_lv_nmos': 'nmoslv', 'sg13_lv_pmos': 'pmoslv',
        'rppd': 'rppd', 'rhigh': 'rhigh', 'cap_cmim': 'cmim'}
MODEL = {v: k for k, v in PRIM.items()}
CH_PORTS = ['isp', 'isn', 'outp', 'outn', 'vref', 'vcm', 'ibias', 'az_lv', 'azh_lv', 'vdda', 'vdd', 'vss']
# common-centroid split: device -> number of sub-devices (each W/n)
SPLIT = {'xm1': 2, 'xm2': 2, 'xa1': 2, 'xa2': 2}


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
            cur = dict(name=t[1], ports=[x for x in t[2:] if '=' not in x], lines=[])
            subckts[t[1]] = cur
        elif t[0].lower() == '.ends':
            cur = None
        elif cur is not None:
            cur['lines'].append(t)
    return subckts


def flatten(subckts, name, netmap, prefix, out):
    sc = subckts[name]

    def net(n):
        if n in netmap:
            return netmap[n]
        return (prefix + '_' + n) if prefix else n
    for t in sc['lines']:
        inst = t[0]
        nodes = [x for x in t[1:] if '=' not in x]
        kv = dict(x.split('=') for x in t[1:] if '=' in x)
        model = nodes[-1]; nodes = nodes[:-1]
        iname = (prefix + '_' + inst.lower()) if prefix else inst.lower()
        if model in PRIM:
            kind = PRIM[model]
            m = int(kv.get('m', '1'))
            d = dict(kind=kind, name=iname, nets=[net(n) for n in nodes])
            d['w'] = num(kv['w']) * 1e6 * (m if kind in ('nmos', 'pmos', 'nmoslv', 'pmoslv') else 1)
            d['l'] = num(kv['l']) * 1e6
            d['ng'] = int(kv.get('ng', '1')) * m
            d['m'] = m
            if kind in ('rppd', 'rhigh', 'cmim') and m != 1:
                raise SystemExit('m != 1 on %s' % iname)
            out.append(d)
        else:
            sub = subckts[model]
            nm = {sub['ports'][i]: net(n) for i, n in enumerate(nodes)}
            flatten(subckts, model, nm, iname, out)
    return out


def split_units(devs):
    out = []
    for d in devs:
        if d['kind'] in ('rppd', 'rhigh') and d['l'] > (RMAX if d['kind'] == 'rppd' else RHMAX) + 1e-9:
            lim = RMAX if d['kind'] == 'rppd' else RHMAX
            n = int(math.ceil(d['l'] / lim - 1e-9))
            while abs(d['l'] / n / 0.005 - round(d['l'] / n / 0.005)) > 1e-6 and n < 60:
                n += 1
            a, b, sub = d['nets']
            for k in range(n):
                na = a if k == 0 else '%s_n%d' % (d['name'], k)
                nb = b if k == n - 1 else '%s_n%d' % (d['name'], k + 1)
                out.append(dict(d, name='%s_s%d' % (d['name'], k), nets=[na, nb, sub], l=round(d['l'] / n, 4),
                                orig=d['name'], seg=k, nseg=n))
        elif d['kind'] in ('nmos', 'pmos', 'nmoslv', 'pmoslv'):
            ns = SPLIT.get(d['name'], 1)
            w = d['w'] / ns
            ng = max(1, d['ng'] // ns, int(math.ceil(w / 10.0 - 1e-9)))
            for k in range(ns):
                nm = d['name'] if ns == 1 else '%s_h%d' % (d['name'], k)
                out.append(dict(d, name=nm, w=round(w, 4), ng=ng, orig=d['name'], ng_schematic=d['ng'], half=k))
        else:
            out.append(dict(d, orig=d['name']))
    return out


def channel_devices():
    sc = parse()
    return split_units(flatten(sc, 'r1_isense_ch', {p: p for p in CH_PORTS}, '', []))


def top_info():
    sc = parse()
    top = sc['r1_isense']
    insts = []
    for t in top['lines']:
        nodes = [x for x in t[1:] if '=' not in x]
        if nodes[-1] == 'r1_isense_ch':
            insts.append((t[0].lower(), dict(zip(CH_PORTS, nodes[:-1]))))
    return insts, top['ports']


def cdl_line(d):
    w, l = round(d['w'], 4), round(d['l'], 4)
    if d['kind'] in ('nmos', 'pmos', 'nmoslv', 'pmoslv'):
        return 'M%s %s %s w=%gu l=%gu m=1' % (d['name'], ' '.join(d['nets']), MODEL[d['kind']], w, l)
    if d['kind'] in ('rppd', 'rhigh'):
        return 'R%s %s %s w=%gu l=%gu m=1 b=0' % (d['name'], ' '.join(d['nets']), d['kind'], w, l)
    return 'C%s %s cap_cmim w=%gu l=%gu m=1' % (d['name'], ' '.join(d['nets']), w, l)


def write_cdl(path=os.path.join(HERE, 'r1_isense_lvs.cdl')):
    ch = channel_devices()
    insts, ports = top_info()
    L = ['* LVS reference CDL for r1_isense (revision 2), written by layout/r1_isense_netlist.py from schematic/r1_isense.spice',
         '* unit split only (see the module docstring): long rhigh/rppd -> straight series segments, MOS finger re-cut;',
         '* r1_ls instances flattened into r1_isense_ch (prefix xls1_/xls2_). Layout dummies are poly only (no devices).',
         '.subckt r1_isense_ch ' + ' '.join(CH_PORTS)]
    L += [cdl_line(d) for d in ch]
    L += ['.ends', '.subckt r1_isense ' + ' '.join(ports)]
    for name, pm in insts:
        L.append('X%s %s r1_isense_ch' % (name, ' '.join(pm[p] for p in CH_PORTS)))
    L += ['.ends', '']
    open(path, 'w').write('\n'.join(L))
    return path, len(ch)


if __name__ == '__main__':
    p, nc = write_cdl()
    ch = channel_devices()
    from collections import Counter
    print('wrote', p, 'channel devices', nc, Counter(d['kind'] for d in ch))
    for d in ch:
        if d['kind'] in ('nmos', 'pmos', 'nmoslv', 'pmoslv'):
            print('%-12s %-7s w=%-6g l=%-5g ng=%-3d nets=%s' % (d['name'], d['kind'], d['w'], d['l'], d['ng'], d['nets']))
