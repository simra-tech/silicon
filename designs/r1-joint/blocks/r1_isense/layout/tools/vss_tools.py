#!/usr/bin/env python3
"""vss network tools for r1_isense layout revision c (track T4, 2026-10-21). Host python3 + numpy/scipy.

Device groups (by terminal nets of the extracted MOS lines 'XM<id> d g s b model ...'):
  out    output stage XMOA/XMOB (gate x1a/x1b)
  cmfb   CMFB sinks and the fast-pair loads (gate vcmfb: XMC1S/XMC2S/XMFD; gate vcmd: XMFE)
  sink   stage-1 sinks XMS1/XMS2 (gate vbf, drain f1/f2)
  bias   bias mirrors (gate ibias: XMBN/XMB2/XMB3/XMB5; XMBNC diode; XMBF)
  gm     slow-CMFB mirror XMGD/XMGM (gate vgd)
  ls     level shifters (gate az_lv/azh_lv or xls* nets)
  rpa    vss end of the RPA arm (rppd XRPA1)

Commands:
  map    <pex rc dir> [op log]          vss map: R from every group's source ports to the vss pin, mutual R between
                                        groups, and (with an op log that prints v(xa.vss__*)) the DC current per group
                                        and the voltage each group's current makes at the other groups' ports
  opdeck <stb deck> <out deck>          op deck (normal state, vin = 0) printing all xa.vss* node voltages
  variant <post netlist> <deck in> <deck out> <netlist out> [ideal=g1,g2] [probe=1] [loops=1,2,8,9]
                                        idealise groups (their vss source ports -> the vss pin) in the netlist and
                                        the deck's r1_isense_ch_stb copy; probe=1 inserts Tian probes in the output-
                                        stage return (loops 8 dm_vso / 9 cm_vso: series source between the XMOx
                                        sources and their network node) and replaces the control block
"""
import json, os, re, sys

GROUPS = ['out', 'cmfb', 'sink', 'bias', 'gm', 'ls', 'rpa']


def net_of(n):
    return re.sub(r'__[pi]\d+$', '', n)


def group_of(f):
    """f: split MOS line. Returns the group name or None."""
    d, g, s = net_of(f[1]), net_of(f[2]), net_of(f[3])
    if g in ('x1a', 'x1b'):
        return 'out'
    if g in ('vcmfb', 'vcmd'):
        return 'cmfb'
    if g == 'vbf' and {d, s} & {'f1', 'f2'}:
        return 'sink'
    if g == 'ibias' or (g == 'vbnc' and d == 'vbnc') or (g == 'vbf' and {d, s} & {'vbfs'}):
        return 'bias'
    if g == 'vgd':
        return 'gm'
    if g in ('az_lv', 'azh_lv') or g.startswith('xls') or d.startswith('xls') or g in ('azb', 'azhb') and 'vss' in (d, s):
        return 'ls'
    return None


def is_vss(n, vnets=('vss',)):
    return net_of(n) in vnets and n != net_of(n)


def device_ports(lines, vnets=('vss', 'vss_o', 'vss_sw')):
    """group -> list of (port node, device line id, drain net) for MOS S/D nodes on a vss net, plus the rpa end"""
    out = {}
    for ln in lines:
        f = ln.split()
        if ln.startswith('XM') and len(f) > 5:
            gname = group_of(f)
            for k in (1, 3):
                if net_of(f[k]) in vnets:
                    out.setdefault(gname or 'other', []).append((f[k], f[0], net_of(f[1] if k == 3 else f[3])))
        elif ln.startswith('XR') and len(f) > 4:
            for k in (1, 2):
                if net_of(f[k]) in vnets and 'rpa' in net_of(f[3 - k]):
                    out.setdefault('rpa', []).append((f[k], f[0], net_of(f[3 - k])))
    return out


# ------------------------------------------------------------------------------------------------------------------
STAR_A = {'vss': 0.08, 'vss_o': 7.9, 'vss_sw': 11.0}     # layout c channel A star wiring (make_post.py STAR)


def cmd_map(rc, oplog=None, nets=('vss',)):
    import numpy as np
    import scipy.sparse as sp
    import scipy.sparse.linalg as sla
    D = json.load(open(os.path.join(rc, 'r1_isense_ch_pex_rnets.json')))
    lines = open(os.path.join(rc, 'r1_isense_ch_pex.spice')).read().splitlines()
    ports = device_ports(lines, vnets=nets)
    els = []
    mains = []
    for n in nets:
        if n in D['rnets']:
            els += D['rnets'][n]['elements']
            mains.append(D['rnets'][n]['main'])
    if len(nets) > 1:
        # layout c: the channel ports join at the star (block-level wiring, estimated) -> ground node 'gstar'
        els = els + [[m, 'gstar', STAR_A.get(m, 1e-4)] for m in mains]
        mains = ['gstar']
    nodes = sorted({x for a, b, _ in els for x in (a, b)})
    idx = {n: i for i, n in enumerate(nodes)}
    N = len(nodes)
    r, c, v = [], [], []
    for a, b, R in els:
        g = 1.0 / R; i, j = idx[a], idx[b]
        r += [i, j, i, j]; c += [i, j, j, i]; v += [g, g, -g, -g]
    G = sp.csr_matrix((v, (r, c)), shape=(N, N)).tocsc()
    ground = [idx[m] for m in mains if m in idx]
    free = [i for i in range(N) if i not in ground]
    fpos = {i: k for k, i in enumerate(free)}
    Gf = G[free][:, free].tocsc()
    lu = sla.splu(Gf)

    def solve(inj):           # inj: {node: A into node}; returns node voltages (V) with the pin(s) at 0
        b = np.zeros(len(free))
        for n, a in inj.items():
            if idx[n] in fpos:
                b[fpos[idx[n]]] += a
        x = lu.solve(b)
        vv = np.zeros(N)
        vv[free] = x
        return vv
    res = dict(nets=list(nets), n_elements=len(els), n_nodes=N, groups={})
    # R to the pin: per port (unit current into the port)
    for gname, lst in sorted(ports.items()):
        rs = []
        for p, did, dn in lst:
            if p not in idx:
                rs.append((p, did, dn, 0.0)); continue
            vv = solve({p: 1.0})
            rs.append((p, did, dn, float(vv[idx[p]])))
        res['groups'][gname] = dict(ports=[dict(node=p, dev=did, other=dn, r_ohm=round(x, 3)) for p, did, dn, x in rs],
                                    r_min=round(min(x for *_, x in rs), 3), r_max=round(max(x for *_, x in rs), 3))
    # mutual R: unit current spread over group a's ports (equal split) -> mean voltage at group b's ports
    gl = sorted(ports)
    M = {}
    for a in gl:
        pa = [p for p, *_ in ports[a] if p in idx]
        vv = solve({p: 1.0 / len(pa) for p in pa}) if pa else np.zeros(N)
        M[a] = {b: round(float(np.mean([vv[idx[p]] for p, *_ in ports[b] if p in idx] or [0.0])), 4) for b in gl}
    res['mutual_r_ohm'] = M
    if oplog:
        txt = open(oplog).read()
        vals = {}
        for m in re.finditer(r'^v\(xa\.(\S+?)\)\s*=\s*(\S+)', txt, re.M):
            vals[m.group(1)] = float(m.group(2))
        if 'vssq' in vals:                     # layout c post netlist: quiet pin node renamed vssq, star node vstar
            vals['vss'] = vals['vssq']
            vals['gstar'] = vals.get('vstar', 0.0)
        vn = np.array([vals.get(n, 0.0) for n in nodes])
        Iinj = G @ vn                          # current injected into each node by devices (A)
        gi = {}
        for gname, lst in ports.items():
            ps = sorted({p for p, *_ in lst})
            gi[gname] = dict(i_uA=round(float(sum(Iinj[idx[p]] for p in ps if p in idx)) * 1e6, 3),
                             v_uV_mean=round(float(np.mean([vals.get(p, 0.0) for p in ps])) * 1e6, 2),
                             v_uV_max=round(float(max(vals.get(p, 0.0) for p in ps)) * 1e6, 2))
        res['op'] = gi
        tot = float(sum(Iinj[i] for i in range(N) if i not in ground))
        res['op_total_uA'] = round(tot * 1e6, 3)
        # per-segment currents: the elements carrying the largest current; and per-group current sharing
        cur = [(abs((vn[idx[a]] - vn[idx[b]]) / R), a, b, R) for a, b, R in els]
        cur.sort(reverse=True)
        res['top_segments'] = [dict(i_uA=round(i * 1e6, 2), a=a, b=b, r_ohm=round(R, 4)) for i, a, b, R in cur[:25]]
        # voltage that each group's own DC current makes at the other groups' ports (superposition)
        S = {}
        for a in gl:
            ps = sorted({p for p, *_ in ports[a] if p in idx})
            vv = solve({p: Iinj[idx[p]] for p in ps})
            S[a] = {b: round(float(np.mean([vv[idx[p]] for p, *_ in ports[b] if p in idx] or [0.0])) * 1e6, 2) for b in gl}
        res['v_uV_by_source_group'] = S
    return res


def cmd_opdeck(deck, out):
    t = open(deck).read()
    a = t.index('.control')
    body = t[:a]
    nodes = sorted(set(re.findall(r'\b(vss(?:_o|_sw)?__[pi]\d+)\b', body)))
    nodes += [n for n in ('vssq', 'vss_o', 'vss_sw', 'vstar') if re.search(r'\s%s\s' % n, body)]
    c = ['.control', 'op']
    for i in range(0, len(nodes), 20):
        c.append('print ' + ' '.join('v(xa.%s)' % n for n in nodes[i:i + 20]))
    c += ['print i(vnn) i(vin)', '.endc', '.end']
    open(out, 'w').write(body + '\n'.join(c) + '\n')
    print('opdeck', out, len(nodes), 'nodes')


# ------------------------------------------------------------------------------------------------------------------
def idealise_lines(lines, ideal, vnets=('vss', 'vss_o', 'vss_sw')):
    out, n = [], 0
    for ln in lines:
        f = ln.split()
        if ln.startswith('XM') and len(f) > 5:
            gname = group_of(f)
            if gname in ideal:
                for k in (1, 3):
                    if is_vss(f[k], vnets) or f[k] in ('vss_o', 'vss_sw'):
                        f[k] = 'vss'; n += 1
                ln = ' '.join(f)
        elif ln.startswith('XR') and 'rpa' in ideal and len(f) > 4:
            for k in (1, 2):
                if is_vss(f[k], vnets) and 'rpa' in net_of(f[3 - k]):
                    f[k] = 'vss'; n += 1
            ln = ' '.join(f)
        out.append(ln)
    return out, n


def in_sub(lines, name):
    a = [i for i, l in enumerate(lines) if l.startswith('.subckt %s ' % name)][0]
    b = [i for i in range(a, len(lines)) if lines[i].startswith('.ends')][0]
    return a, b


LOOPDEF = {   # loop id: (v params on, i params on, v expr, i expr)
    1: ({'vo_p': 1, 'vo_n': -1}, {'io_p': 1, 'io_n': -1}, '(%s.v(xa.outpi)-%s.v(xa.outni))/2', '(%s.i(v.xa.vpop)-%s.i(v.xa.vpon))/2'),
    2: ({'vo_p': 1, 'vo_n': 1}, {'io_p': 1, 'io_n': 1}, '(%s.v(xa.outpi)+%s.v(xa.outni))/2', '(%s.i(v.xa.vpop)+%s.i(v.xa.vpon))/2'),
    8: ({'vz_p': 1, 'vz_n': -1}, {'jz_p': 1, 'jz_n': -1}, '(%s.v(xa.vsoa)-%s.v(xa.vsob))/2', '(%s.i(v.xa.vpva)-%s.i(v.xa.vpvb))/2'),
    9: ({'vz_p': 1, 'vz_n': 1}, {'jz_p': 1, 'jz_n': 1}, '(%s.v(xa.vsoa)+%s.v(xa.vsob))/2', '(%s.i(v.xa.vpva)+%s.i(v.xa.vpvb))/2'),
}
ALLP = ['vo_p', 'vo_n', 'io_p', 'io_n', 'vi_p', 'vi_n', 'ii_p', 'ii_n', 'vc', 'ic', 'va_p', 'va_n', 'ja_p', 'ja_n',
        'vz_p', 'vz_n', 'jz_p', 'jz_n']


def control(loops, levels=('0', '0.1', '-0.02')):
    c = ['.control', 'let li = 0', 'foreach vs %s' % ' '.join(levels), '  foreach lp %s' % ' '.join(str(l) for l in loops)]
    for run in (0, 1):
        for l in loops:
            c.append('    if $lp = %d' % l)
            c += ['      alterparam %s=%g' % kv for kv in LOOPDEF[l][run].items()]
            c.append('    end')
        c += ['    reset', '    alter vin dc = $vs', '    ac dec 20 100 1g']
        c += ['    alterparam %s=0' % p for p in ALLP]
    for l in loops:
        ve, ie = LOOPDEF[l][2], LOOPDEF[l][3]
        c += ['    if $lp = %d' % l, '      let v1 = ' + ve % ('ac1', 'ac1'), '      let i1 = ' + ie % ('ac1', 'ac1'),
              '      let v2 = ' + ve % ('ac2', 'ac2'), '      let i2 = ' + ie % ('ac2', 'ac2'), '    end']
    c += ['    let tl = -1/(1-1/(2*(i1*v2-v1*i2)+v1+i2))', '    let tdb = db(tl)', '    let tph = 180/pi*cph(tl)',
          '    let fid = 10*li + $lp', '    wrdata @@OUT@@_t$&fid tdb tph', '    echo "STBFILE level=$vs loop=$lp"',
          '    destroy all', '  end', '  let li = li + 1', 'end', '.endc', '.end']
    return c


def probe_out(lines, vnets=('vss', 'vss_o', 'vsso')):
    """move the XMOx source ports to vsoa/vsob; return (lines, probe lines)"""
    a, b = in_sub(lines, 'r1_isense_ch_stb')
    portA, portB = [], []
    for i in range(a, b):
        f = lines[i].split()
        if lines[i].startswith('XM') and len(f) > 5 and group_of(f) == 'out':
            side = 'a' if net_of(f[1]) in ('outpi', 'outp') or net_of(f[3]) in ('outpi', 'outp') else 'b'
            for k in (1, 3):
                if net_of(f[k]) in vnets:
                    (portA if side == 'a' else portB).append(f[k]); f[k] = 'vso' + side
            lines[i] = ' '.join(f)
    assert portA and portB, (portA, portB)
    pa, pb = sorted(set(portA))[0], sorted(set(portB))[0]
    P = ['* ---- Tian probes in the output-stage return (vss path; layout revision c tools/vss_tools.py)',
         'Vpva vsoa %s dc 0 ac {vz_p}' % pa, 'Vpvb vsob %s dc 0 ac {vz_n}' % pb,
         'Ipva 0 vsoa dc 0 ac {jz_p}', 'Ipvb 0 vsob dc 0 ac {jz_n}']
    lines[b:b] = P
    return lines, dict(portA=sorted(set(portA)), portB=sorted(set(portB)))


def own_return(lines, r):
    """model check (b extraction): the XMOx sources leave the vss network and return through their own resistor
    r (ohm) to the vss pin (vsso), as the planned vss_o strap of layout c"""
    out = []
    for ln in lines:
        f = ln.split()
        if ln.startswith('XM') and len(f) > 5 and group_of(f) == 'out':
            for k in (1, 3):
                if is_vss(f[k]) or f[k] == 'vss':
                    f[k] = 'vsso'
            ln = ' '.join(f)
        out.append(ln)
    return out[:-1] + ['Rvsso vsso vss %s' % r] + out[-1:]


def cmd_variant(post, deck_in, deck_out, net_out, opts):
    ideal = [x for x in opts.get('ideal', '').split(',') if x]
    L = open(post).read().splitlines()
    a, b = in_sub(L, 'r1_isense_ch')
    body, n1 = idealise_lines(L[a:b], ideal)
    if opts.get('oret'):
        body = own_return(body + [L[b]], opts['oret'])[:-1]
    L[a:b] = body
    open(net_out, 'w').write('\n'.join(L) + '\n')
    T = open(deck_in).read().replace(post, net_out)
    if '.subckt r1_isense_ch_stb' in T:
        TL = T.splitlines()
        a, b = in_sub(TL, 'r1_isense_ch_stb')
        body, n2 = idealise_lines(TL[a:b], ideal)
        if opts.get('oret'):
            body = own_return(body + [TL[b]], opts['oret'])[:-1]
        TL[a:b] = body
        info = {}
        if opts.get('probe') == '1':
            TL, info = probe_out(TL)
            TL = [l + ' vz_p=0 vz_n=0 jz_p=0 jz_n=0' if l.startswith('.param vo_p=0') else l for l in TL]
        if opts.get('loops'):
            k = TL.index('.control')
            TL = TL[:k] + control([int(x) for x in opts['loops'].split(',')], opts.get('levels', '0,0.1,-0.02').split(','))
        T = '\n'.join(TL) + '\n'
        print('variant', ideal, 'netlist lines changed', n1, 'deck lines changed', n2, info)
    if opts.get('rcom'):
        # common vss impedance between the channel pin and the deck ground (top-level trunk, item 4)
        T2 = re.sub(r'^(X(?:A|DUT) .*) 0 (r1_isense_ch(?:_stb)?)$', r'\1 vstar \2', T, flags=re.M)
        assert T2 != T
        extra = 'Rcom vstar 0 %s' % opts['rcom']
        if opts.get('ib'):
            # the other channel's DC vss current through the same common impedance (static)
            extra += '\nIchb 0 vstar dc %s' % opts['ib']
        T = T2.replace('\n.control', '\n' + extra + '\n.control', 1)
    open(deck_out, 'w').write(T)


NAMES = {'out': 'output stage XMOA/XMOB', 'cmfb': 'CMFB sinks XMC1S/XMC2S, XMFD, XMFE', 'sink': 'stage-1 sinks XMS1/XMS2',
         'bias': 'bias XMBN/XMB2/XMB3/XMB5/XMBNC/XMBF', 'gm': 'slow-CMFB mirror XMGD/XMGM', 'ls': 'level shifters (HV + 1.2 V NMOS)',
         'rpa': 'RPA arm vss end (Kelvin tap vss_k)', 'other': 'other'}


def cmd_md(js, title):
    d = json.load(open(js))
    gl = sorted(d['groups'])
    o = ['### %s' % title, '',
         'Networks: %s (%d elements, %d nodes). R to pin: unit current into one source port, all other ports open. '
         'DC current and port voltage from the op run (tt, normal state, 0 mV). Simulated / extracted, not measured.' % (
             ', '.join(d['nets']), d['n_elements'], d['n_nodes']), '',
         '| Group | Devices | Ports | R to pin, min - max (ohm) | DC current (uA) | Port voltage mean / max (uV) |',
         '| --- | --- | --- | --- | --- | --- |']
    for g in gl:
        v = d['groups'][g]; op = d.get('op', {}).get(g, {})
        o.append('| %s | %s | %d | %.2f - %.2f | %s | %s / %s |' % (g, NAMES.get(g, g), len(v['ports']), v['r_min'], v['r_max'],
                 op.get('i_uA', '-'), op.get('v_uV_mean', '-'), op.get('v_uV_max', '-')))
    if 'v_uV_by_source_group' in d:
        S = d['v_uV_by_source_group']
        o += ['', 'Voltage (uV, mean over the ports of the column group) made by the DC current of the row group alone (superposition):', '',
              '| from \\ at | ' + ' | '.join(gl) + ' |', '| --- |' + ' --- |' * len(gl)]
        for a in gl:
            o.append('| %s | ' % a + ' | '.join('%.1f' % S[a][b] for b in gl) + ' |')
        o += ['', 'Total vss current of the channel: %.1f uA. Largest segment currents:' % d['op_total_uA'], '',
              '| I (uA) | R (ohm) | nodes |', '| --- | --- | --- |']
        for s in d['top_segments'][:8]:
            o.append('| %.1f | %.4g | %s - %s |' % (s['i_uA'], s['r_ohm'], s['a'], s['b']))
    print('\n'.join(o))


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'md':
        cmd_md(sys.argv[2], sys.argv[3]); sys.exit(0)
    if cmd == 'map':
        nets = ('vss',)
        args = [x for x in sys.argv[2:] if not x.startswith('nets=')]
        for x in sys.argv[2:]:
            if x.startswith('nets='):
                nets = tuple(x[5:].split(','))
        r = cmd_map(args[0], args[1] if len(args) > 1 else None, nets)
        json.dump(r, sys.stdout, indent=1)
    elif cmd == 'opdeck':
        cmd_opdeck(sys.argv[2], sys.argv[3])
    elif cmd == 'variant':
        opts = dict(x.split('=', 1) for x in sys.argv[6:])
        cmd_variant(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], opts)
