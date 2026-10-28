#!/usr/bin/env python3
"""r1_afe netlist handling for the layout (revision E): parse schematic/r1_afe.spice, flatten one channel
(subckt r1_afe_ch) and the top level (r1_afe) into primitive devices, apply the layout unit split, and write
the LVS reference CDL.

Unit split (the only difference between the CDL and the revision-E netlist; values are preserved):
  * rppd longer than RMAX (78 um) -> n >= ceil(l / RMAX) straight series segments of equal length, n the
    smallest value that puts the segment length on the 0.005 um grid (RD2 935 um: 17 x 55 um). The total body length is unchanged. Each extra segment
    adds two head resistances (PDK Rzspec 35 Ohm.um / w, i.e. 70 Ohm per extra segment at w = 1 um);
    the post-layout netlist carries the split, so the effect is in the post-layout results.
  * cap_cmim with a side above CMAX (28 um) -> 4 parallel units of half the side (same total area,
    perimeter x2: +0.04 fF/um x perimeter in the PDK model; in the post-layout netlist).
  * MOS: total W and L as in the netlist; the finger count is re-cut so a finger is <= 10 um (HV PCell
    limit) and >= 0.5 um. LVS compares W and L only (the deck combines the fingers).
The LVS compare runs with --no_series_res, so every resistor segment is compared 1:1.
Plate orientation (revision E2): the PDK MIM device class has non-swappable terminals (mim_top, mim_btm), so the CDL
writes each cap_cmim with its top-plate net first, as laid out (orient()). The schematic order is "top, bottom" except:
  * CM-sense caps XCS1/XCS2 of both OTAs: bottom plate (Metal5, with its parasitic to the layers below) on the OTA
    output, top plate on vcms (revision E had the bottom plate on vcms);
  * output differential cap XCOD (4 units): units 1 and 2 (one diagonal of the 2 x 2 block) reversed, so each output
    carries the bottom plate of two units (revision E: all four on outn).
Electrically the same capacitor (the PDK model has 55 mOhm in series with PLUS only).
Usage (python3, no KLayout needed):  python3 r1_afe_netlist.py   -> writes r1_afe_lvs.cdl next to this file
"""
import math, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
NETLIST = os.path.join(HERE, '..', 'schematic', 'r1_afe.spice')
RMAX, CMAX = 78.0, 28.0
PRIM = {'sg13_hv_nmos': 'nmos', 'sg13_hv_pmos': 'pmos', 'rppd': 'rppd', 'cap_cmim': 'cmim'}
CH_PORTS = ['inp', 'inn', 'outp', 'outn', 'vcm1', 'vcm2', 'ib1', 'ib2', 'c1', 'c2', 'c3', 'c4', 'vdd', 'vss']


def num(v):
    v = v.strip().lower()
    m = re.match(r'^([-+0-9.e]+)([a-z]*)$', v)
    if not m:
        raise ValueError(v)
    x = float(m.group(1)); s = m.group(2)
    mult = {'': 1.0, 'u': 1e-6, 'n': 1e-9, 'p': 1e-12, 'f': 1e-15, 'm': 1e-3, 'k': 1e3}[s[:1] if s[:3] != 'meg' else '']
    return x * mult


def parse(path=None):
    path = path or NETLIST   # E9: NETLIST may be reassigned by the generator (-rd sch=<file>)
    lines = []
    for raw in open(path).read().splitlines():
        if raw.startswith('+') and lines:
            lines[-1] += ' ' + raw[1:]
        else:
            lines.append(raw)
    gparams, subckts, cur = {}, {}, None
    for ln in lines:
        s = ln.strip()
        if not s or s.startswith('*'):
            continue
        t = s.split()
        if t[0].lower() == '.param':
            for kv in t[1:]:
                k, v = kv.split('='); gparams[k] = v
        elif t[0].lower() == '.subckt':
            ports = [x for x in t[2:] if '=' not in x]
            defs = dict(x.split('=') for x in t[2:] if '=' in x)
            cur = dict(name=t[1], ports=ports, defaults=defs, lines=[])
            subckts[t[1]] = cur
        elif t[0].lower() == '.ends':
            cur = None
        elif cur is not None:
            cur['lines'].append(t)
    return gparams, subckts


def resolve(v, scope):
    v = v.strip()
    if v.startswith('{') and v.endswith('}'):
        return resolve(scope[v[1:-1]], scope)
    return v


def flatten(subckts, gparams, name, netmap, prefix, params, out):
    """append primitive devices of subckt `name` to out: dict(kind, name, nets, w, l, ng, path)."""
    sc = subckts[name]
    scope = dict(gparams); scope.update(sc['defaults']); scope.update(params)
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
            d = dict(kind=kind, name=iname, nets=[net(n) for n in nodes], path=(prefix, inst))
            d['w'] = num(resolve(kv['w'], scope)) * 1e6
            d['l'] = num(resolve(kv['l'], scope)) * 1e6
            d['ng'] = int(kv.get('ng', '1'))
            out.append(d)
        else:
            sub = subckts[model]
            p2 = {k: resolve(v, scope) for k, v in kv.items()}
            nm = {sub['ports'][i]: net(n) for i, n in enumerate(nodes)}
            flatten(subckts, gparams, model, nm, iname, p2, out)
    return out


def r5(x):
    return round(x / 0.005) * 0.005


def split_units(devs):
    """apply the layout unit split; returns a new list. Each output device has 'orig' = original name."""
    out = []
    for d in devs:
        if d['kind'] == 'rppd' and d['l'] > RMAX + 1e-9:
            n = int(math.ceil(d['l'] / RMAX - 1e-9))
            while abs(d['l'] / n / 0.005 - round(d['l'] / n / 0.005)) > 1e-6 and n < 60:
                n += 1          # smallest n with equal segments on the 0.005 um grid
            segs = [round(d['l'] / n, 4)] * n
            a, b, sub = d['nets']
            for k, L in enumerate(segs):
                na = a if k == 0 else '%s_n%d' % (d['name'], k)
                nb = b if k == n - 1 else '%s_n%d' % (d['name'], k + 1)
                out.append(dict(d, name='%s_s%d' % (d['name'], k), nets=[na, nb, sub], l=L, orig=d['name'], seg=k, nseg=n))
        elif d['kind'] == 'cmim' and d['w'] > CMAX + 1e-9:
            s = r5(d['w'] / 2)
            for k in range(4):
                out.append(dict(d, name='%s_u%d' % (d['name'], k), w=s, l=s, orig=d['name'], unit=k))
        elif d['kind'] in ('nmos', 'pmos'):
            ng = max(d['ng'], int(math.ceil(d['w'] / 10.0 - 1e-9)))
            ng = max(1, min(ng, int(d['w'] / 0.5 + 1e-9)))
            out.append(dict(d, ng=ng, orig=d['name'], ng_schematic=d['ng']))
        else:
            out.append(dict(d, orig=d['name']))
    return out


FLIP_ALL = ('xa1_xcs1', 'xa1_xcs2', 'xa2_xcs1', 'xa2_xcs2')   # bottom plate to the OTA output
FLIP_UNITS = {'xcod': (1, 2)}                                     # alternate units: balanced bottom plate
ORIENT = os.environ.get('R1AFE_ORIENT', 'e2')                     # 'e' = revision-E orientation (reference runs)


def orient(devs):
    if ORIENT == 'e':
        return devs
    out = []
    for d in devs:
        if d['kind'] == 'cmim' and (d['orig'] in FLIP_ALL or d.get('unit') in FLIP_UNITS.get(d['orig'], ())):
            d = dict(d, nets=[d['nets'][1], d['nets'][0]], flipped=True)
        out.append(d)
    return out


def channel_devices():
    gp, sc = parse()
    devs = flatten(sc, gp, 'r1_afe_ch', {p: p for p in CH_PORTS}, '', {}, [])
    return orient(split_units(devs))


def top_devices():
    """devices of r1_afe itself (divider) and the channel instances with their port nets."""
    gp, sc = parse()
    top = sc['r1_afe']
    devs, insts = [], []
    for t in top['lines']:
        nodes = [x for x in t[1:] if '=' not in x]
        model = nodes[-1]
        if model == 'r1_afe_ch':
            insts.append((t[0].lower(), dict(zip(CH_PORTS, nodes[:-1]))))
    sc2 = dict(sc)
    sc2['__t'] = dict(top, lines=[t for t in top['lines'] if [x for x in t[1:] if '=' not in x][-1] != 'r1_afe_ch'])
    tmp = flatten(sc2, gp, '__t', {p: p for p in top['ports']}, '', {}, [])
    return split_units(tmp), insts, top['ports']


def cdl_line(d):
    w, l = d['w'], d['l']
    if d['kind'] in ('nmos', 'pmos'):
        model = 'sg13_hv_nmos' if d['kind'] == 'nmos' else 'sg13_hv_pmos'
        return 'M%s %s %s w=%gu l=%gu m=1' % (d['name'], ' '.join(d['nets']), model, round(w, 4), round(l, 4))
    if d['kind'] == 'rppd':
        return 'R%s %s rppd w=%gu l=%gu m=1 b=0' % (d['name'], ' '.join(d['nets']), round(w, 4), round(l, 4))
    return 'C%s %s cap_cmim w=%gu l=%gu m=1' % (d['name'], ' '.join(d['nets']), round(w, 4), round(l, 4))


def write_cdl(path=os.path.join(HERE, 'r1_afe_lvs.cdl')):
    ch = channel_devices()
    top, insts, ports = top_devices()
    L = ['* LVS reference CDL for r1_afe (revision F netlist, layout revision E3), written by layout/r1_afe_netlist.py from schematic/r1_afe.spice',
         '* unit split and MIM plate orientation (see the module docstring): long rppd -> straight series segments, large cap_cmim -> 4 units; cap_cmim nets in top, bottom order as laid out',
         '.subckt r1_afe_ch ' + ' '.join(CH_PORTS)]
    L += [cdl_line(d) for d in ch]
    L += ['.ends', '.subckt r1_afe ' + ' '.join(ports)]
    L += [cdl_line(d) for d in top]
    for name, pm in insts:
        L.append('X%s %s r1_afe_ch' % (name, ' '.join(pm[p] for p in CH_PORTS)))
    L += ['.ends', '']
    open(path, 'w').write('\n'.join(L))
    return path, len(ch), len(top)


if __name__ == '__main__':
    p, nc, nt = write_cdl()
    ch = channel_devices()
    from collections import Counter
    print('wrote', p, 'channel devices', nc, Counter(d['kind'] for d in ch), 'top devices', nt)
