#!/usr/bin/env python3
"""Pin-by-pin connectivity audit: chip CDL (what the layout connects) vs a generated G1_TOP deck.

For every pin of every block instance in the top subckt of the chip CDL (g1_chip_top), report the net it
sits on in the CDL and in the deck, and whether the two agree. Nets are matched without a name table:
the (CDL net, deck net) pairs seen on common pins must form a one-to-one correspondence, and the set of
common-instance pins on each net must be the same on both sides. Anything else is reported.

Deck side:
  * X instances are resolved against the .subckt port lists of the files the deck .include's (/work is
    mapped to the repository root); the PDK sg13g2_io cells fall back to the CDL's own definitions.
  * zero-volt V sources (current monitors) are treated as shorts.
  * g1_digital is reached through the XSPICE d_cosim instance: its input/output lists are matched by
    position to the ports of sim/rtl/g1_dig_cosim.v (vectors MSB first), the wrapper's named connections
    to g1_digital, and the adc/dac bridges to the analog net. Digital nets fed by a d_source are marked.

Status values: same | same, loads differ | differs | not in deck | not in CDL.  Every non-'same' line
carries an explanation: documented substitutions are listed in DOCUMENTED below (with the README /
deck section that states them); a 'differs' without one is printed as UNEXPLAINED and makes the exit
status 1.

--waves additionally runs interface level/timing checks on the waveform files of the deck's tag.

Usage (repository root, no external dependencies):
  python3 designs/g1-guardian/blocks/g1_top/sim/check_cdl_vs_deck.py [--deck D] [--cdl C] [--waves]
"""
import argparse
import collections
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
BLOCKS = os.path.join(REPO, 'designs', 'g1-guardian', 'blocks')
DEF_CDL = os.path.join(BLOCKS, 'g1_padring', 'netlist', 'g1_chip_top_1414.cdl')
DEF_TAG = 'c_mid_pex_c1414_tl_tt_27C_clockfix_compact_functional_c1414v1'
DEF_DECK = os.path.join(HERE, 'decks', DEF_TAG + '.cir')
WRAPPER = os.path.join(HERE, 'rtl', 'g1_dig_cosim.v')

# CDL instance -> deck instance ('ADIG' = the d_cosim digital macro). Unlisted CDL instances: not in deck.
INSTANCE_MAP = {
    'Xi_core_u_bgr': 'XBGR', 'Xi_core_u_sense': 'XSENSE', 'Xi_core_u_trip': 'XTRIP',
    'Xi_core_u_gate': 'XGATE', 'Xi_core_u_osc': 'XOSC', 'Xi_core_u_digital': 'ADIG',
    'Xpad08_sense_p': 'XPSP', 'Xpad09_sense_n': 'XPSN', 'Xpad18_vref': 'XPVREF',
    # run_top.py --t2f tl (absent otherwise: ABSENT below applies)
    'Xi_core_u_t2f': 'XT2F', 'Xi_core_u_ls_en': 'XLSEN', 'Xi_core_u_ls_mode': 'XLSMODE',
}
SKIP_CELLS = re.compile(r'(decap|fill_|Filler|Corner|bondpad|antennanp)', re.I)
# Why a CDL instance is absent from the deck (README 'Scope statement' / 'Numerical notes').
ABSENT = {
    'Xi_core_u_osc': 'ideal clock Bosc_clk at the block frequency (README numerical note 4)',
    'Xi_core_u_t2f': 'G1_T2F not in the breaker-path deck (README scope: TEMP_OUT not simulated)',
    'Xi_core_u_ls_en': 'T2F level shifter; T2F not in deck',
    'Xi_core_u_ls_mode': 'T2F level shifter; T2F not in deck',
    'Xi_core_u_ls_r4': 'BGR r4 shifter; deck ties bgr.r4 to 0 V (RTL reset BGR_R4 = 0)',
    'Xi_core_u_dose': 'dose macro, standalone pads, not on the breaker path',
    'Xi_core_u_dut': 'HBT test device, standalone pads, not on the breaker path',
    'Xi_core_u_digital_1': 'tiehi for por_n; wrapper ties por_n = 1',
    'Xpad10_gate': 'GATE pad = fitted 47 Ohm driver (README numerical note 3)',
    'Xpad11_fault_n': 'FAULT_N pad = fitted 500 Ohm driver (README numerical note 3)',
    'Xpad12_en': 'EN pad = ideal 3.3->1.2 V copy + d_source (README numerical notes 3, 7)',
    'Xpad14_sclk': 'SCLK pad = ideal copy + d_source (README numerical notes 3, 7)',
    'Xpad15_sdi': 'SDI pad = ideal copy + d_source (README numerical notes 3, 7)',
    'Xpad16_sdo': 'SDO pad not simulated (README: sdo not padded)',
    'Xpad17_temp_out': 'TEMP_OUT pad not simulated (README scope)',
    'Xpad13_trip_set': 'TRIP_SET pad path not built (README scope)',
}
ABSENT_RE = [
    (r'^Xpad0[1-7]_', 'supply pad not modelled; deck supplies are ideal sources through 0.5 Ohm + 1 nF (README board)'),
    (r'^Xpad(19|2[0-4])_', 'dose / HBT test-structure pad, not on the breaker path'),
]
# Documented substitutions for pins whose net differs or whose loads differ. key: 'cdlinst.pin' or net.
DOCUMENTED = {
    'IOVSS': 'deck ties IOVSS and VSS to node 0 (single board ground)',
    'VSS': 'deck ties IOVSS and VSS to node 0 (single board ground)',
    'IOVDD': 'deck: IOVDD and VDDA from one 3.3 V board rail through separate 0.5 Ohm (README board)',
    'Xi_core_u_bgr.r4': 'CDL: RTL bgr_r4 through g1_ls_up; deck: Vr4 0 V = RTL reset value (TEMP_CTRL.BGR_R4 = 0)',
    'Xi_core_u_bgr.pbias': 'CDL: bias to G1_T2F; T2F not in deck (BGR mirror output unloaded)',
    'Xi_core_u_bgr.pcasc': 'CDL: bias to G1_T2F; T2F not in deck (BGR mirror output unloaded)',
    'Xi_core_u_bgr.vref': 'CDL: vref also loads G1_T2F (mode switch MMX1); T2F not in deck',
    'Xi_core_u_digital.en': 'RTL en from d_source with the pad-PWL edge times (README numerical note 7); '
                            'CDL: EN pad p2c en_i, shared with g1_gate en_core',
    'Xi_core_u_digital.sclk': 'RTL sclk from d_source (README numerical note 7)',
    'Xi_core_u_digital.sdi': 'RTL sdi from d_source (README numerical note 7)',
    'Xi_core_u_digital.sdo': 'SDO pad not in deck; RTL sdo on a monitor dac only',
    'Xi_core_u_digital.por_n': 'CDL tiehi; wrapper ties por_n = 1\'b1 (same function)',
    'Xi_core_u_digital.osc_clk': 'CDL driven by g1_osc; deck by the ideal Bosc_clk (README numerical note 4)',
    'Xi_core_u_digital.osc_en': 'CDL to g1_osc.en; deck: only gates the ideal clock (Bosc)',
    'Xi_core_u_digital.bgr_r4': 'CDL to g1_ls_up -> bgr.r4; deck: wrapper-internal, bgr.r4 tied 0 V',
    'Xi_core_u_digital.t2f_en': 'CDL to g1_ls_up -> t2f.en; T2F not in deck',
    'Xi_core_u_digital.t2f_mode': 'CDL to g1_ls_up -> t2f.mode; T2F not in deck',
    'Xi_core_u_digital.clk_div_out': 'open in CDL; wrapper-internal in deck',
    'Xi_core_u_digital.fault_n': 'open in CDL (FAULT_N pad is driven by g1_gate fault_core); wrapper-internal',
    'Xi_core_u_digital.trip_set_sel': 'open in CDL (TRIP_SET path not built); wrapper-internal',
    'Xi_core_u_digital.trip': 'open in CDL; deck monitor dig_trip',
    'Xi_core_u_digital.gate_en': 'open in CDL; deck monitor dig_gate_en',
    'Xi_core_u_digital.trip_cause[1]': 'open in CDL; deck monitor cause1',
    'Xi_core_u_digital.trip_cause[0]': 'open in CDL; deck monitor cause0',
    'Xi_core_u_gate.en_core': 'CDL: EN pad p2c (en_i) also feeds g1_digital.en; deck: Ben_core copy (digital en from d_source)',
    'Xi_core_u_gate.gate_core': 'CDL: IOPadOut30mA c2p; deck: fitted Bgate_drv (README numerical note 3)',
    'Xi_core_u_gate.fault_core': 'CDL: IOPadOut4mA c2p; deck: fitted Bfault_drv (README numerical note 3)',
    'Xpad18_vref.padres': 'CDL: vref also loads G1_T2F; T2F not in deck',
    'Xi_core_u_digital.VDD': 'RTL co-simulation has no supply pin (digital supply current not simulated, README)',
    'Xi_core_u_digital.VSS': 'RTL co-simulation has no supply pin',
    'Xi_core_u_digital.osc_trim[3]': 'CDL to g1_osc.trim; osc not in deck (trim bits on monitor dac only)',
    'Xi_core_u_digital.osc_trim[2]': 'CDL to g1_osc.trim; osc not in deck (trim bits on monitor dac only)',
    'Xi_core_u_digital.osc_trim[1]': 'CDL to g1_osc.trim; osc not in deck (trim bits on monitor dac only)',
    'Xi_core_u_digital.osc_trim[0]': 'CDL to g1_osc.trim; osc not in deck (trim bits on monitor dac only)',
    'VDD': 'CDL VDD also supplies g1_osc and the digital macro (not transistor-level in the deck)',
    'Xi_core_u_sense.vref': 'CDL: vref also loads G1_T2F; T2F not in deck',
}


def join_lines(path):
    out = []
    for raw in open(path, errors='replace'):
        line = raw.rstrip('\n')
        if line.startswith('+') and out:
            out[-1] += ' ' + line[1:]
        else:
            out.append(line)
    return out


def subckt_defs(lines, into=None):
    """{name_lower: (name, [ports])} of every .subckt in the joined lines (parameters dropped)."""
    d = {} if into is None else into
    for l in lines:
        f = l.split()
        if len(f) > 1 and f[0].lower() == '.subckt':
            d.setdefault(f[1].lower(), (f[1], [p for p in f[2:] if '=' not in p]))
    return d


def device_fingerprint(lines, top):
    """Flattened {model: count x m} under subckt `top` (numeric R/C/L values = parasitics, counted apart)."""
    bodies, cur = {}, None
    for l in lines:
        f = l.split()
        if not f or f[0].startswith('*'):
            continue
        if f[0].lower() == '.subckt':
            cur = f[1].lower(); bodies[cur] = []
        elif f[0].lower() == '.ends':
            cur = None
        elif cur is not None:
            bodies[cur].append(f)
    memo = {}

    def walk(name):
        if name in memo:
            return memo[name]
        cnt = collections.Counter()
        for f in bodies.get(name, []):
            toks = [t for t in f if '=' not in t and t != '/']
            m = 1
            for t in f:
                if t.lower().startswith('m='):
                    try: m = int(float(t[2:]))
                    except ValueError: pass
            model = toks[-1].lower()
            if f[0][0].upper() == 'X' and model in bodies:
                for k, v in walk(model).items():
                    cnt[k] += v * m
            elif re.match(r'^[-+0-9.]', model):
                cnt['(parasitic %s)' % f[0][0].upper()] += 1
            else:
                cnt[model] += m
        memo[name] = cnt
        return cnt
    return walk(top.lower())


# ------------------------------------------------------------------ CDL
def parse_cdl(path, top='g1_chip_top'):
    lines = join_lines(path)
    defs = subckt_defs(lines)
    insts, inside = [], False
    for l in lines:
        f = l.split()
        if not f:
            continue
        if f[0].lower() == '.subckt':
            inside = f[1].lower() == top.lower()
            continue
        if f[0].lower() == '.ends':
            inside = False
            continue
        if inside and f[0][0] in 'Xx':
            toks = [t for t in f if '=' not in t]
            cell = toks[-1]
            nets = [t for t in toks[1:-1] if t != '/']
            if SKIP_CELLS.search(cell):
                continue
            ports = defs[cell.lower()][1]
            if len(ports) != len(nets):
                raise SystemExit('CDL %s: %d nets for %d ports of %s' % (f[0], len(nets), len(ports), cell))
            insts.append((f[0], cell, list(zip(ports, nets))))
    return lines, defs, insts


# ------------------------------------------------------------------ deck
class UF:
    def __init__(self): self.p = {}
    def find(self, a):
        a = a.lower(); self.p.setdefault(a, a)
        while self.p[a] != a:
            self.p[a] = self.p[self.p[a]]; a = self.p[a]
        return a
    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            # keep the shorter / plainer name as the representative (vdd over vdd_trip)
            keep, drop = sorted((ra, rb), key=lambda s: (len(s), s))
            self.p[drop] = keep


def wrapper_ports(path):
    """[(dir, name, [bit names MSB first])] of g1_dig_cosim and {g1_digital port: wrapper expr}."""
    src = re.sub(r'//[^\n]*', '', open(path).read())
    hdr = re.search(r'module\s+g1_dig_cosim\w*\s*\((.*?)\);', src, re.S).group(1)
    ports = []
    for m in re.finditer(r'(input|output)\s+wire\s*(\[(\d+):(\d+)\])?\s*(\w+)', hdr):
        d, _, hi, lo, n = m.groups()
        bits = [n] if hi is None else ['%s[%d]' % (n, i) for i in
                                        (range(int(hi), int(lo) - 1, -1) if int(hi) >= int(lo) else range(int(hi), int(lo) + 1))]
        ports.append((d, n, bits))
    inst = re.search(r'g1_digital\s*#\(.*?\)\s*u_dig\s*\((.*?)\);', src, re.S).group(1)
    named = dict(re.findall(r'\.(\w+)\s*\(\s*([^)]*?)\s*\)', inst))
    return ports, named


def parse_deck(path, cdl_defs):
    lines = join_lines(path)
    defs, uf, elems, insts = {}, UF(), [], []
    for l in lines:
        f = l.split()
        if f and f[0].lower() == '.include':
            inc = f[1].strip('"\'')
            if inc.startswith('/work/'):
                inc = os.path.join(REPO, inc[len('/work/'):])
            if os.path.exists(inc):
                subckt_defs(join_lines(inc), defs)
    for k, v in cdl_defs.items():              # PDK sg13g2_io cells: same port lists as the CDL copies
        defs.setdefault(k, v)
    bridges = {}                                # digital net -> (analog net, model, direction)
    adig = None
    models = {}
    in_control = False
    for l in lines:
        f = l.split()
        if not f or f[0].startswith('*'):
            continue
        if f[0].lower() == '.control': in_control = True
        if f[0].lower() == '.endc': in_control = False; continue
        if in_control or f[0].startswith('.'):
            if f[0].lower() == '.model':
                models[f[1].lower()] = f[2].split('(')[0].lower()
            continue
        c = f[0][0].upper()
        if c == 'X':
            toks = [t for t in f if '=' not in t]
            cell = toks[-1]
            nets = toks[1:-1]
            ports = defs[cell.lower()][1]
            if len(ports) != len(nets):
                raise SystemExit('deck %s: %d nets for %d ports of %s' % (f[0], len(nets), len(ports), cell))
            insts.append((f[0], cell, list(zip(ports, nets))))
        elif c == 'A':
            groups = re.findall(r'\[([^\]]*)\]', l)
            model = l.split(']')[-1].split()[0].lower() if groups else f[-1].lower()
            if len(groups) == 2:
                ins, outs = groups[0].split(), groups[1].split()
                if model == 'rtl':
                    adig = (f[0], ins, outs)
                else:
                    for a, d in zip(ins, outs):         # adc: analog -> digital, dac: digital -> analog
                        bridges.setdefault(a.lower(), []).append((d.lower(), model, 'in'))
                        bridges.setdefault(d.lower(), []).append((a.lower(), model, 'out'))
            elif len(groups) == 1:                      # d_source: [outs] model
                for d in groups[0].split():
                    bridges.setdefault(d.lower(), []).append(('(d_source %s)' % model, model, 'src'))
        elif c in 'VRCLBIE' and len(f) >= 3:
            n1, n2 = f[1], f[2]
            if (c == 'V' and re.match(r'(?i)^dc$', f[3] if len(f) > 3 else '') and len(f) > 4
                    and float(f[4]) == 0.0 and '0' not in (n1, n2)):
                uf.union(n1, n2)            # 0 V current monitor = short (a 0 V tie to ground stays a named net)
            elems.append((f[0], n1.lower(), n2.lower(), ' '.join(f[3:])[:40]))
    return defs, uf, elems, insts, adig, bridges, models


# ------------------------------------------------------------------ comparison
def deck_digital_pins(adig, bridges, models, uf):
    """{g1_digital port: (analog deck net or None, note)} through wrapper + d_cosim + bridges."""
    wports, named = wrapper_ports(WRAPPER)
    ins = [b for d, n, bits in wports if d == 'input' for b in bits]
    outs = [b for d, n, bits in wports if d == 'output' for b in bits]
    _, dins, douts = adig
    if len(ins) != len(dins) or len(outs) != len(douts):
        raise SystemExit('d_cosim port count mismatch: wrapper %d/%d vs deck %d/%d'
                         % (len(ins), len(outs), len(dins), len(douts)))
    wbit = dict(zip(ins + outs, [d.lower() for d in dins + douts]))
    res = {}
    for dport, expr in named.items():
        if re.match(r"^\d+'[bhd]", expr):
            res[dport] = [(dport, None, 'tied %s in wrapper' % expr)]
            continue
        wp = [p for p in wports if p[1] == expr]
        if not wp:
            res[dport] = [(dport, None, 'wrapper-internal wire (unconnected)')]
            continue
        rows = []
        for bit in wp[0][2]:
            pin = dport + bit[len(expr):]
            dnet = wbit[bit]
            ana = [(a, m) for a, m, _ in bridges.get(dnet, [])]
            if not ana:
                rows.append((pin, None, 'digital net %s unbridged' % dnet))
            elif ana[0][0].startswith('(d_source'):
                rows.append((pin, None, 'digital stimulus %s -> %s' % (ana[0][0], dnet)))
            else:
                rows.append((pin, uf.find(ana[0][0]), 'via %s %s' % (models.get(ana[0][1], ana[0][1]), ana[0][1])))
        res[dport] = rows
    return res


def short(lst, n=4):
    lst = [m.replace('Xi_core_u_', '').replace('Xpad', 'pad') for m in lst]
    return ', '.join(lst[:n]) + (' +%d more' % (len(lst) - n) if len(lst) > n else '')


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--cdl', default=DEF_CDL)
    ap.add_argument('--deck', default=DEF_DECK)
    ap.add_argument('--waves', action='store_true', help='also run the interface waveform checks for the deck tag')
    ap.add_argument('--no-fingerprint', action='store_true')
    ap.add_argument('--full', action='store_true', help='one row per pin also for instances absent from the deck')
    a = ap.parse_args()
    global WRAPPER
    # run_top.py names a non-default d_cosim wrapper in the deck (--t2f tl: rtl/g1_dig_cosim_t2f.v)
    with open(a.deck) as f:
        mw = re.search(r'^\* d_cosim wrapper: (rtl/\S+\.v)', f.read(), re.M)
    if mw:
        WRAPPER = os.path.join(HERE, mw.group(1))

    cdl_lines, cdl_defs, cinsts = parse_cdl(a.cdl)
    ddefs, uf, elems, dinsts, adig, bridges, models = parse_deck(a.deck, cdl_defs)
    dmap = {n: (cell, pins) for n, cell, pins in dinsts}
    dig = deck_digital_pins(adig, bridges, models, uf)

    # pin rows: (cdl inst, pin, cdl net, deck inst, deck net or None, note)
    rows = []
    for cn, cell, pins in cinsts:
        dn = INSTANCE_MAP.get(cn)
        if dn == 'ADIG':
            for p, net in pins:
                r = dig.get(re.sub(r'\[\d+\]$', '', p), [])
                hit = [x for x in r if x[0] == p]
                if hit:
                    rows.append((cn, p, net, 'adig', hit[0][1], hit[0][2]))
                else:
                    rows.append((cn, p, net, 'adig', None, 'not a g1_dig_cosim/g1_digital connection'))
        elif dn in dmap:
            dcell, dpins = dmap[dn]
            dp = dict((x.lower(), y) for x, y in dpins)
            for i, (p, net) in enumerate(pins):
                key = p.lower()
                if cell.lower().startswith('g1_vss_derivative__') and key == 'g1_explicit_substrate_vss':
                    rows.append((cn, p, net, dn, None, 'derivative substrate pin; deck substrate = global sub! = 0'))
                    continue
                # bus pins: CDL dac_soft[3] <-> deck soft3; positional equivalence is used when names differ
                if key not in dp and len(pins) == len(dpins):
                    dnet, dname = dpins[i][1], dpins[i][0]
                    rows.append((cn, p, net, dn, uf.find(dnet), 'deck pin %s (positional)' % dname))
                elif key in dp:
                    rows.append((cn, p, net, dn, uf.find(dp[key]), ''))
                else:
                    rows.append((cn, p, net, dn, None, 'pin absent from deck subckt'))
        else:
            for p, net in pins:
                why = ABSENT.get(cn) or next((w for r_, w in ABSENT_RE if re.match(r_, cn)), 'instance not in deck')
                rows.append((cn, p, net, None, None, why))

    # correspondence
    c2d, d2c = collections.defaultdict(set), collections.defaultdict(set)
    for cn, p, cnet, dn, dnet, _ in rows:
        if dnet is not None:
            c2d[cnet.lower()].add(dnet); d2c[dnet].add(cnet.lower())
    cmembers = collections.defaultdict(set)
    dmembers = collections.defaultdict(set)
    for cn, p, cnet, dn, dnet, _ in rows:
        if p.lower() == 'g1_explicit_substrate_vss':
            continue
        cmembers[cnet.lower()].add('%s.%s' % (cn, p))
        if dnet is not None:
            dmembers[dnet].add('%s.%s' % (cn, p))
    dextra = collections.defaultdict(set)
    for name, n1, n2, val in elems:
        for n in (n1, n2):
            dextra[uf.find(n)].add(name)
    for n, lst in bridges.items():
        for a_, m, d in lst:
            if d == 'in':
                dextra[uf.find(n)].add('bridge %s' % m)

    def present(member):
        inst, pin = member.split('.', 1)
        dn_ = INSTANCE_MAP.get(inst)
        if dn_ == 'ADIG':
            return pin not in ('VDD', 'VSS')
        return dn_ in dmap

    out, unexplained, nsame = [], 0, 0
    for cn, p, cnet, dn, dnet, note in rows:
        key = '%s.%s' % (cn, p)
        doc = DOCUMENTED.get(key) or DOCUMENTED.get(cnet)
        if dn is None:
            status = 'not in deck'
            expl = note
        elif dnet is None:
            status = 'not in deck'
            expl = note + ('; ' + doc if doc else '')
            if not doc and 'substrate' not in note:
                status += ' (UNEXPLAINED)'; unexplained += 1
        else:
            bij = len(c2d[cnet.lower()]) == 1 and len(d2c[dnet]) == 1
            c_common = {m for m in cmembers[cnet.lower()] if present(m)}
            missing = sorted(cmembers[cnet.lower()] - dmembers[dnet])
            extra = sorted(dmembers[dnet] - cmembers[cnet.lower()])
            miss_common = [m for m in missing if m in c_common]
            if bij and not miss_common and not extra:
                if missing:
                    status, expl = 'same, loads differ', 'CDL-only: ' + short(missing, 6)
                    if doc: expl += ' (' + doc + ')'
                else:
                    status, expl = 'same', note
                    nsame += 1
            else:
                why = []
                if not bij:
                    why.append('CDL net -> deck %s; deck net <- CDL %s'
                               % (sorted(c2d[cnet.lower()]), sorted(d2c[dnet])))
                if miss_common: why.append('CDL-only pins on common instances: ' + short(miss_common))
                if extra: why.append('deck-only pins: ' + short(extra))
                status = 'differs'
                expl = '; '.join(why)
                if doc:
                    expl = doc + ' [' + expl + ']'
                else:
                    status += ' (UNEXPLAINED)'; unexplained += 1
        out.append((key.replace('Xi_core_u_', '').replace('Xpad', 'pad'), cnet, dnet or '-', status, expl))

    w0 = max(len(r[0]) for r in out); w1 = max(len(r[1]) for r in out); w2 = max(len(r[2]) for r in out)
    print('# CDL  %s' % os.path.relpath(a.cdl, REPO))
    print('# deck %s' % os.path.relpath(a.deck, REPO))
    print('%-*s | %-*s | %-*s | %s' % (w0, 'block.pin', w1, 'CDL net', w2, 'deck net', 'status / explanation'))
    done = set()
    for r in out:
        inst = r[0].split('.')[0]
        if not a.full and r[3] == 'not in deck' and r[2] == '-' and all(
                x[3] == 'not in deck' and x[2] == '-' for x in out if x[0].split('.')[0] == inst):
            if inst in done:
                continue
            done.add(inst)
            pins = ' '.join('%s=%s' % (x[0].split('.', 1)[1], x[1]) for x in out if x[0].split('.')[0] == inst)
            print('%-*s | %s | - | not in deck -- %s' % (w0, inst + '.*', pins, r[4]))
            continue
        print('%-*s | %-*s | %-*s | %s%s' % (w0, r[0], w1, r[1], w2, r[2], r[3], (' -- ' + r[4]) if r[4] else ''))
    cnt = collections.Counter(r[3].split(' (')[0] for r in out)
    print('# summary: %s; unexplained: %d' % (', '.join('%s %d' % kv for kv in sorted(cnt.items())), unexplained))

    # deck driver of each common net that the CDL drives from an absent instance (context)
    print('# deck-only elements on nets shared with the CDL (sources, bridges, board parts):')
    for dnet in sorted(d2c):
        ex = sorted(x for x in dextra.get(dnet, ()) if not x.lower().startswith(('cw_', 'x')))
        if ex:
            print('#   %-12s %s' % (dnet, ', '.join(ex)))

    # wrapper vs CDL g1_digital port set
    wports, named = wrapper_ports(WRAPPER)
    cdig = [p for p in cdl_defs['g1_digital'][1] if p not in ('VDD', 'VSS')]
    cbase = sorted(set(re.sub(r'\[\d+\]$', '', p) for p in cdig))
    print('# g1_digital: CDL ports %d (bits), wrapper named connections %d; ports missing in wrapper: %s; extra: %s'
          % (len(cdig), len(named), sorted(set(cbase) - set(named)) or 'none', sorted(set(named) - set(cbase)) or 'none'))
    print('# d_cosim: wrapper inputs %s' % ' '.join(b for d, n, bits in wports if d == 'input' for b in bits))
    print('#          deck adig inputs %s' % ' '.join(adig[1]))

    if not a.no_fingerprint:
        print('# device fingerprint (flattened, x m; parasitic R/C counted apart), CDL vs deck netlist:')
        deck_files = {}
        for l in join_lines(a.deck):
            f = l.split()
            if f and f[0].lower() == '.include' and 'sg13g2_io' not in f[1]:
                p = f[1].replace('/work/', REPO + '/', 1)
                for name in ('g1_bgr', 'g1_sense', 'g1_trip', 'g1_gate', 'g1_osc'):
                    if name in subckt_defs(join_lines(p)):
                        deck_files[name] = p
        for name in ('g1_bgr', 'g1_sense', 'g1_trip', 'g1_gate'):
            fc = device_fingerprint(cdl_lines, name)
            fd = device_fingerprint(join_lines(deck_files[name]), name)
            dev_c = {k: v for k, v in fc.items() if not k.startswith('(')}
            dev_d = {k: v for k, v in fd.items() if not k.startswith('(')}
            diff = {k: (dev_c.get(k, 0), dev_d.get(k, 0)) for k in set(dev_c) | set(dev_d) if dev_c.get(k, 0) != dev_d.get(k, 0)}
            print('#   %-9s CDL %5d devices, deck %5d devices (+%d parasitic) %s' % (
                name, sum(dev_c.values()), sum(dev_d.values()), sum(v for k, v in fd.items() if k.startswith('(')),
                'identical model counts' if not diff else 'DIFF ' + str(sorted(diff.items()))))

    if a.waves:
        wave_checks(a.deck)
    return 1 if unexplained else 0


# ------------------------------------------------------------------ waveform checks
def load_table(path):
    import gzip
    op = gzip.open if path.endswith('.gz') else open
    with op(path, 'rt') as fh:
        hdr = fh.readline().split()
        cols = [[] for _ in hdr]
        for l in fh:
            v = l.split()
            if len(v) == len(hdr):
                for i, x in enumerate(v):
                    cols[i].append(float(x))
    return {h: c for h, c in zip(hdr, cols)}


def crossings(t, v, th, rise=True):
    out = []
    for i in range(1, len(v)):
        if (v[i - 1] < th <= v[i]) if rise else (v[i - 1] > th >= v[i]):
            out.append(t[i - 1] + (th - v[i - 1]) * (t[i] - t[i - 1]) / (v[i] - v[i - 1]))
    return out


def wave_checks(deck):
    tag = os.path.basename(deck)[:-4]
    wdir = os.path.join(HERE, 'results', 'waves')
    A = load_table(os.path.join(wdir, tag + '.txt'))
    sp = os.path.join(wdir, tag + '_state.txt')
    S = load_table(sp if os.path.exists(sp) else sp.replace('.txt', '_full.txt.gz'))
    t = A['time']; ts = S['time']
    print('# ---- waveform checks: %s (analog file %d points, state file %d points)' % (tag, len(t), len(ts)))
    tq0 = 1e-6

    print('# 1.2 V logic nets: min / max, samples in 0.15..1.05 V after 1 us (count, first times)')
    for tt, D, names in ((t, A, ['v(cmp_soft)', 'v(cmp_hard)', 'v(cmp_clk)', 'v(osc_clk)', 'v(trip_d)', 'v(tripped)',
                                   'v(en_core)', 'v(dig_trip)', 'v(inrush_active)']),
                         (ts, S, ['v(soft%d)' % i for i in range(8)] + ['v(hard%d)' % i for i in range(8)] +
                                 ['v(fast_en)', 'v(clr_d)', 'v(sdo)', 'v(en_core)'])):
        for n in names:
            if n not in D:
                continue
            v = D[n]
            sel = [(x, y) for x, y in zip(tt, v) if x >= tq0]
            mid = [x for x, y in sel if 0.15 < y < 1.05]
            print('#   %-18s min %+.3f max %.3f mid %d %s%s' % (
                n, min(y for _, y in sel), max(y for _, y in sel), len(mid),
                ' '.join('%.3f' % (x * 1e6) for x in mid[:4]),
                '  OVER 1.3 V' if max(y for _, y in sel) > 1.3 else ''))
    # DAC code lines: every change of the analog-read code
    for bus in ('soft', 'hard'):
        code_prev, changes = None, []
        for i, x in enumerate(ts):
            c = sum((1 << b) for b in range(8) if S['v(%s%d)' % (bus, b)][i] > 0.6)
            if c != code_prev:
                changes.append((x, c)); code_prev = c
        print('# DAC %s code changes (t us: code): %s' % (bus, ', '.join('%.4f:%d' % (x * 1e6, c) for x, c in changes[:12])))
    # clocks
    for n in ('v(osc_clk)', 'v(cmp_clk)'):
        r = [x for x in crossings(t, A[n], 0.6) if x > 5e-6]
        if len(r) > 2:
            per = (r[-1] - r[0]) / (len(r) - 1)
            print('# %s: %d rising edges after 5 us, mean f = %.4f MHz' % (n, len(r), 1e-6 / per))
    # DAC threshold vs expected transfer (pre-EN window: reset codes, no strobe kickback)
    import statistics as st
    def mean_win(n, a0, a1):
        return st.mean(y for x, y in zip(t, A[n]) if a0 <= x <= a1)
    vs0, vh0 = mean_win('v(xtrip.vth_soft)', 1e-6, 2.9e-6), mean_win('v(xtrip.vth_hard)', 1e-6, 2.9e-6)
    vrb = vh0 * 530 / (255 + 254)
    print('# pre-EN (1-2.9 us, codes 153/254, strobe stopped): vth_soft %.4f vth_hard %.4f -> vref_buf %.4f; '
          'expected vth_soft %.4f' % (vs0, vh0, vrb, vrb * (255 + 153) / 530))
    for n in ('v(xtrip.icmp)', 'v(xtrip.vth_soft)', 'v(xtrip.vth_hard)', 'v(isense)', 'v(vref)'):
        seg = [y for x, y in zip(t, A[n]) if 12e-6 <= x <= 15.9e-6]
        print('#   quiet 12-15.9 us %-18s mean %.4f  p-p %.4f' % (n, st.mean(seg), max(seg) - min(seg)))
    print('#   expected vth_hard(code 200) %.4f, vth_soft(153) %.4f, icmp = isense/2 %.4f' % (
        vrb * 455 / 530, vrb * 408 / 530, st.mean(y for x, y in zip(t, A['v(isense)']) if 12e-6 <= x <= 15.9e-6) / 2))
    # event timing
    ev = {}
    for n, th, rise in (('v(en_core)', 0.6, True), ('v(inrush_active)', 0.6, False), ('v(cmp_hard)', 0.6, True),
                        ('v(cmp_soft)', 0.6, True), ('v(trip_d)', 0.6, True), ('v(tripped)', 0.6, True),
                        ('v(gate)', 1.0, False), ('v(dig_trip)', 0.6, True)):
        c = crossings(t, A[n], th, rise)
        ev[n] = c
        print('# %-18s %s %.2f V at (us): %s' % (n, 'rise' if rise else 'fall', th, ' '.join('%.3f' % (x * 1e6) for x in c[:6])))
    for n in ('v(clr_d)', 'v(fast_en)'):
        r = crossings(ts, S[n], 0.6, True); f = crossings(ts, S[n], 0.6, False)
        print('# %-18s rise %s fall %s' % (n, ' '.join('%.3f' % (x * 1e6) for x in r[:6]), ' '.join('%.3f' % (x * 1e6) for x in f[:6])))


if __name__ == '__main__':
    sys.exit(main())
