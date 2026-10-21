#!/usr/bin/env python3
"""Build the post-layout netlist of r1_afe (revision E + extracted capacitances), pure Python.

  python3 make_postlayout.py <kpex_full.spice | -> <out.spice> <report.json> [<kpex_channel.spice>]
With the 4th argument the channel parasitics come from the extraction of the channel cell alone (flat r1_afe_ch;
both channel instances are this cell) and the full-block extraction (or none, '-') gives only the top-level nets.

Netlist structure (keeps every node and instance name the testbenches and the loop-gain probe edits of
sim/run_afe.py use: XA1/XA2 lines, XMN7/XMP7/XCC1/XMC1 inside the OTA subcircuits, channel nodes x1p, m1p, ...):
  * devices = the LVS reference (layout/r1_afe_netlist.py): rppd split into the laid-out series segments,
    large MIMs as 4 units, MOS with the laid-out finger count (ng). The model cards are those of revision E.
  * r1_afe_ota / r1_afe_ota2: the laid-out devices, every internal node exported as an extra port (after the
    original ports), so that all parasitic capacitors can sit in the channel subcircuit.
  * r1_afe_ch: the OTA calls plus all other devices of the channel, flat; parasitic capacitors of the sine
    channel instance (the cosine channel is the same cell; its own extraction is reported for comparison).
  * r1_afe: divider devices, both channel instances, parasitic capacitors of the top-level nets.
Extracted capacitors (kpex 2.5D, mode CC) are mapped by net name (the layout labels are the CDL names):
  xsin_<net> -> channel scope <net>; xcos_<net> -> not used (counted); other names -> top scope; VSUBS -> vss.
  A capacitor between a channel-internal net and a top-only net (or an unnamed net) is put to vss in the scope
  of the named/internal net (counted in the report).
"""
import json, os, re, sys
from collections import defaultdict
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'layout'))
import r1_afe_netlist as N

OTA_PORTS = {'xa1': ['inp', 'inn', 'outp', 'outn', 'vcm', 'ibias', 'cen', 'cenb', 'vdd', 'vss'],
             'xa2': ['inp', 'inn', 'outp', 'outn', 'vcm', 'ibias', 'vdd', 'vss']}
OTA_NAME = {'xa1': 'r1_afe_ota', 'xa2': 'r1_afe_ota2'}


def val(s):
    m = re.match(r'^([-+0-9.eE]+)([a-zA-Z]*)$', s)
    mult = {'': 1, 'a': 1e-18, 'f': 1e-15, 'p': 1e-12, 'n': 1e-9, 'u': 1e-6}[m.group(2)[:1].lower()]
    return float(m.group(1)) * mult


def dev_line(d, nets, name):
    if d['kind'] in ('nmos', 'pmos'):
        model = 'sg13_hv_nmos' if d['kind'] == 'nmos' else 'sg13_hv_pmos'
        return 'X%s %s %s w=%gu l=%gu ng=%d m=1 mm_ok=1' % (name, ' '.join(nets), model, round(d['w'], 4), round(d['l'], 4), d['ng'])
    if d['kind'] == 'rppd':
        return 'X%s %s rppd w=%gu l=%gu m=1 b=0 mm_ok=1' % (name, ' '.join(nets), round(d['w'], 4), round(d['l'], 4))
    return 'X%s %s cap_cmim w=%gu l=%gu m=1 mm_ok=1' % (name, ' '.join(nets), round(d['w'], 4), round(d['l'], 4))


def main(pexf, outf, repf):
    gp, sc = N.parse()
    ch = N.channel_devices()
    topd, insts, ports = N.top_devices()
    # schematic port order of the OTA instances in the channel
    chlines = {t[0].lower(): t for t in sc['r1_afe_ch']['lines']}
    L = ['* r1_afe post-layout netlist (revision E devices as laid out + kpex 2.5D capacitances), written by',
         '* pex/make_postlayout.py from %s' % os.path.basename(pexf)]
    # --- OTA subcircuits with exported internal nodes
    ota_int = {}
    for a in ('xa1', 'xa2'):
        t = chlines[a]
        nodes = [x for x in t[1:] if '=' not in x][:-1]
        pmap = dict(zip(nodes, OTA_PORTS[a]))      # channel net -> ota port name
        devs = [d for d in ch if d['path'][0].startswith(a)]
        internal = sorted(set(n for d in devs for n in d['nets'] if n.startswith(a + '_')))
        ota_int[a] = internal
        loc = lambda n: pmap.get(n, n[len(a) + 1:] if n.startswith(a + '_') else n)
        L.append('.subckt %s %s %s' % (OTA_NAME[a], ' '.join(OTA_PORTS[a]), ' '.join(loc(n) for n in internal)))
        for d in devs:
            nm = d['name'][len(a) + 1:]          # 'xmn7' -> 'MN7' (dev_line adds 'X'): the schematic spelling,
            L.append(dev_line(d, [loc(n) for n in d['nets']], (nm[1:] if nm.startswith('x') else nm).upper()))  # probe edits match it
        L.append('.ends')
    return L, ch, topd, insts, ports, chlines, ota_int


def finish(pexf, outf, repf, chpexf=None):
    L, ch, topd, insts, ports, chlines, ota_int = main(pexf, outf, repf)
    chnets = set(n for d in ch for n in d['nets']) | set(N.CH_PORTS)
    sinmap = insts[[i for i, (nm, _) in enumerate(insts) if nm == 'xsin'][0]][1]
    top2port = {}
    for p, tn in sinmap.items():
        top2port.setdefault(tn, p)
    topnets = set(ports) | set(n for d in topd for n in d['nets'])
    # --- parse the kpex capacitors
    def readcaps(f, pre=''):
        out = []
        for ln in open(f):
            t = ln.split()
            if t and t[0].startswith('Cext'):
                a_, b_ = (t[i].replace('\\', '') for i in (1, 2))
                if pre:   # channel-only extraction: every net is a channel net (VSUBS stays substrate)
                    a_, b_ = (x if x in ('VSUBS', 'vss', 'VSS') else pre + x for x in (a_, b_))
                out.append((a_, b_, val(t[3])))
        return out
    cs = [] if pexf == '-' else readcaps(pexf)
    if chpexf:   # channel caps from the channel-only extraction; the full extraction only gives the top-level caps
        cs = [c for c in cs if not (c[0].startswith(('xsin_', 'xcos_')) or c[1].startswith(('xsin_', 'xcos_')))]
        cs += readcaps(chpexf, 'xsin_')
    chc, topc = defaultdict(float), defaultdict(float)
    stat = defaultdict(float)
    cos_tot = 0.0
    def norm(n):
        return 'vss' if n in ('VSUBS', 'vss', 'VSS') else n
    for a, b, c in cs:
        a, b = norm(a), norm(b)
        if a.startswith('xcos_') or b.startswith('xcos_'):
            cos_tot += c; continue
        ai, bi = a.startswith('xsin_'), b.startswith('xsin_')
        if ai or bi:
            def tochan(n):
                if n.startswith('xsin_'):
                    m = n[5:]
                    return m if m in chnets else None
                return top2port.get(n)
            ca, cb = tochan(a), tochan(b)
            if ca is None or cb is None:
                stat['lumped_to_vss_F'] += c
                ca = ca or 'vss'; cb = cb or 'vss'
            if ca != cb:
                chc[tuple(sorted((ca, cb)))] += c
            stat['channel_F'] += c
        else:
            if a.startswith('$') or b.startswith('$'):
                stat['unnamed_F'] += c
                a = 'vss' if a.startswith('$') else a; b = 'vss' if b.startswith('$') else b
            if a != b:
                topc[tuple(sorted((a, b)))] += c
            stat['top_F'] += c
    # --- channel subcircuit
    L.append('.subckt r1_afe_ch ' + ' '.join(N.CH_PORTS))
    for a in ('xa1', 'xa2'):
        t = chlines[a]
        nodes = [x for x in t[1:] if '=' not in x][:-1]
        L.append('%s %s %s %s' % (t[0], ' '.join(nodes), ' '.join(ota_int[a]), OTA_NAME[a]))
    for d in ch:
        if d['path'][0].startswith(('xa1', 'xa2')):
            continue
        L.append(dev_line(d, d['nets'], d['name']))
    for k, ((a, b), c) in enumerate(sorted(chc.items())):
        L.append('Cp%d %s %s %.4g' % (k, a, b, c))
    L.append('.ends')
    L.append('.subckt r1_afe ' + ' '.join(ports))
    for d in topd:
        L.append(dev_line(d, d['nets'], d['name']))
    for nm, pm in insts:
        L.append('X%s %s r1_afe_ch' % (nm[1:] if nm.startswith('x') else nm, ' '.join(pm[p] for p in N.CH_PORTS)))
    for k, ((a, b), c) in enumerate(sorted(topc.items())):
        L.append('Cq%d %s %s %.4g' % (k, a, b, c))
    L += ['.ends', '']
    open(outf, 'w').write('\n'.join(L))
    # per-net totals for the report
    tot = defaultdict(float)
    for (a, b), c in chc.items():
        tot['ch:' + a] += c; tot['ch:' + b] += c
    for (a, b), c in topc.items():
        tot['top:' + a] += c; tot['top:' + b] += c
    rep = dict(sources=dict(full=os.path.basename(pexf), channel=os.path.basename(chpexf) if chpexf else None), n_caps=len(cs), stats={k: v for k, v in stat.items()}, cos_channel_total_F=cos_tot,
               channel_caps=len(chc), top_caps=len(topc),
               net_total_fF={k: round(v * 1e15, 3) for k, v in sorted(tot.items(), key=lambda kv: -kv[1])})
    json.dump(rep, open(repf, 'w'), indent=1)
    print('post-layout netlist', outf, 'caps', len(cs), 'channel', len(chc), 'top', len(topc), dict(stat))


if __name__ == '__main__':
    finish(*sys.argv[1:5])
