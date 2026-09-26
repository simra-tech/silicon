#!/usr/bin/env python3
"""G1 full-chip schematic simulation driven by the chip CDL (ngspice 46 + Icarus Verilog d_cosim).

Run from the repository root inside the pinned container:

    G1_WORKDIR=designs/g1-guardian/blocks/g1_top/sim flow/run.sh python3 run_top_cdl.py [options] CASE [CASE ...]

The circuit is the top subckt g1_chip_top of blocks/g1_padring/netlist/g1_chip_top_1414.cdl (bound by SHA256
below), translated to ngspice syntax in the deck and instantiated once with its 22 pins on the board fixture of
run_top.py. Nothing is hand-wired inside the chip: every block, level shifter, pad cell, the DOSE/DUT macros and
the top-level decap/antenna/filler cells come from the CDL. Substitutions, each written to the deck header:

  * g1_digital (gate-level in the CDL) is replaced by a subckt of the same name and exact port list whose body is
    the XSPICE d_cosim instance of the real RTL (rtl/g1_dig_cosim_cdl.v = rtl/g1_dig_cosim_t2f.v plus the four
    outputs that are open in the chip) with adc/dac bridges. All digital inputs, including EN/SCLK/SDI from the
    real IOPadIn cells, use the single-threshold (VDD/2) receiver of the clock fix (README, Numerical notes 7).
  * --osc ideal (default): g1_osc is replaced by a subckt of the same ports holding the ideal clock of run_top.py
    (9.436194721 MHz, gated by the RTL osc_en, released at 0.1 us). --osc tl keeps the transistor-level oscillator.
  * --netlist pex: the block subckts g1_bgr, g1_sense, g1_trip, g1_gate, g1_t2f (and g1_osc with --osc tl) come
    from the extracted netlists of run_top.BLOCKSETS['c1414'] / T2F_NETLISTS (hash-bound; ports checked against
    the CDL's port list positionally through a name normalisation). Default --netlist sch: the CDL's own blocks.
  * --pads nodcn (default): every dantenna instance of the translated chip (IO cells and sg13g2_antennanp) is
    removed (run_top.py PADS_NODCN_WARNING reason). --pads pdk keeps them.
  * 0 V ammeters in series with the supply pins of the block instances (names as run_top.py's Vm_*).
  * Identical filler instances (decap/fill/Filler/Corner/bondpad/antenna cells on identical nets) are merged
    into one instance with m = count (exact for identical parallel subcircuits).

Stimulus, cases and measurement lines are those of run_top.build_deck (run with --t2f tl so that the T2F
measurement lines exist); the node names of the measurement lines are mapped to the chip hierarchy (NODE_MAP).
"""
import argparse
import collections
import gzip
import hashlib
import math
import os
import re
import subprocess
import sys
import time
import uuid

import run_top as RT
from run_bounded import run_bounded, atomic_json
from simulation_errors import solver_failure

HERE = RT.HERE
BLOCKS = RT.BLOCKS
ROOT = RT.ROOT
BUILD = RT.BUILD
CDL_REL = 'g1_padring/netlist/g1_chip_top_1414.cdl'
CDL_SHA256 = 'af5a4dbd0b17013b11d32f31221353a22b2676ea884e3487db3f14d9c5443a36'
WRAPPER = os.path.join(HERE, 'rtl/g1_dig_cosim_cdl.v')
TOP = 'g1_chip_top'
TOP_PINS = ('D_ELT D_STD EN FAULT_N GATE G_SHARED HBT_B HBT_C HBT_E SCLK SDI SDO SENSE_N SENSE_P TEMP_OUT '
            'TRIP_SET VDDA VREF VDD VSS IOVDD IOVSS').split()
# board net of each chip pin (run_top.py board names where they exist)
BOARD = {'D_ELT': 'd_elt', 'D_STD': 'd_std', 'EN': 'en_pad', 'FAULT_N': 'fault_n', 'GATE': 'gate',
         'G_SHARED': 'g_shared', 'HBT_B': 'hbt_b', 'HBT_C': 'hbt_c', 'HBT_E': 'hbt_e', 'SCLK': 'sclk_pad',
         'SDI': 'sdi_pad', 'SDO': 'sdo_pad', 'SENSE_N': 'sense_n', 'SENSE_P': 'sense_p', 'TEMP_OUT': 'temp_out_pad',
         'TRIP_SET': 'trip_set', 'VDDA': 'vdda', 'VREF': 'vref_pad', 'VDD': 'vdd', 'VSS': '0', 'IOVDD': 'iovdd',
         'IOVSS': '0'}
# test-structure / unused pins: 1 MOhm to board ground (defined DC level, no other board load)
PIN_PULLDOWN = ('D_ELT', 'D_STD', 'G_SHARED', 'HBT_B', 'HBT_C', 'HBT_E', 'TRIP_SET')
DIGITAL_PORTS = ('bgr_r4 clk_div_out clr_d cmp_clk cmp_hard cmp_soft en fast_en fault_n gate_en osc_clk osc_en por_n '
                 'sclk sdi sdo t2f_en t2f_mode trip trip_d trip_set_sel tripped VDD VSS ' +
                 ' '.join('dac_hard[%d]' % i for i in range(7, -1, -1)) + ' ' +
                 ' '.join('dac_soft[%d]' % i for i in range(7, -1, -1)) + ' ' +
                 ' '.join('osc_trim[%d]' % i for i in range(3, -1, -1)) + ' trip_cause[1] trip_cause[0]').split()
# CDL block subckt ports (checked against the CDL) and the run_top.py block key of each
CDL_BLOCKS = {'bgr': 'g1_bgr', 'sense': 'g1_sense', 'trip': 'g1_trip', 'osc': 'g1_osc', 'gate': 'g1_gate', 't2f': 'g1_t2f'}
# supply-pin ammeters: CDL instance -> {port position: ammeter name}; the net at that position is checked
METERS = {'Xi_core_u_bgr': {0: ('vm_bgr', 'VDDA')}, 'Xi_core_u_sense': {7: ('vm_sense', 'VDDA')},
          'Xi_core_u_trip': {21: ('vm_tripd', 'VDD'), 22: ('vm_tripa', 'VDDA')},
          'Xi_core_u_osc': {6: ('vm_osc', 'VDD')},
          'Xi_core_u_gate': {8: ('vm_gated', 'VDD'), 9: ('vm_gatea', 'VDDA')},
          'Xi_core_u_t2f': {0: ('vm_t2f', 'VDDA'), 1: ('vm_t2fd', 'VDD')},
          'Xi_core_u_ls_en': {2: ('vm_lsd', 'VDD'), 3: ('vm_ls', 'VDDA')},
          'Xi_core_u_ls_mode': {2: ('vm_lsd', 'VDD'), 3: ('vm_ls', 'VDDA')}}
FILLER_RE = re.compile(r'(decap_|fill_|Filler|Corner|bondpad|antennanp)', re.I)
PDK_DEVICES = {'sg13_lv_nmos': 4, 'sg13_lv_pmos': 4, 'sg13_hv_nmos': 4, 'sg13_hv_pmos': 4, 'npn13G2': 4,
               'cap_cmim': 2, 'rppd': 3, 'rhigh': 3, 'rsil': 3, 'ptap1': 2, 'ntap1': 2, 'dantenna': 2, 'dpantenna': 2}
PTAP_DEFAULT_R = 262.8   # PDK resistors_mod.lib ptap1 default


def san(tok):
    """CDL bus/bit names -> ngspice-safe names (dac_soft[0] -> dac_soft_0_, MN0<1> -> MN0_1_)."""
    return re.sub(r'[\[\]<>]', '_', tok)


def norm_port(p):
    """CDL block port name -> run_top.BLOCK_PORTS name (positional check only)."""
    p = p.lower()
    p = re.sub(r'^dac_(soft|hard)\[(\d)\]$', r'\1\2', p)
    p = re.sub(r'^trim\[(\d)\]$', r'trim\1', p)
    return {'clk': 'cmp_clk', 'iovdd': 'vdda'}.get(p, p)


def parse_cdl(path):
    """{subckt name: (ports, [body lines])} in file order (continuation lines joined)."""
    lines = []
    for raw in open(path):
        l = raw.rstrip('\n')
        if l.startswith('+') and lines:
            lines[-1] += ' ' + l[1:]
        else:
            lines.append(l)
    subs, cur = collections.OrderedDict(), None
    for l in lines:
        t = l.split()
        if not t or l.startswith('*'):
            continue
        k = t[0].lower()
        if k == '.subckt':
            cur = t[1]
            subs[cur] = ([x for x in t[2:] if '=' not in x], [])
        elif k == '.ends':
            cur = None
        elif cur is not None:
            subs[cur][1].append(l)
        else:
            raise SystemExit('CDL line outside a subckt: %s' % l)
    return subs


def inst_cell(tokens):
    """(nets, cell, params) of a CDL X line."""
    t = [x for x in tokens[1:] if x != '/']
    params = [x for x in t if '=' in x]
    pos = [x for x in t if '=' not in x]
    return pos[:-1], pos[-1], params


def io_ptap_values(iospi):
    """{(sg13g2 cell, instance): R} of the ptap1 resistors of the PDK sg13g2_io.spi."""
    out, cell = {}, None
    for l in open(iospi):
        t = l.split()
        if not t:
            continue
        if t[0].lower() == '.subckt':
            cell = t[1]
        elif t[0][0] in 'Xx' and 'ptap1' in t:
            r = [x for x in t if x.startswith('R=')]
            if r:
                out[(cell, t[0])] = r[0][2:]
    return out


class Translator:
    def __init__(self, nodcn, ptaps):
        self.nodcn, self.ptaps = nodcn, ptaps
        self.count = collections.Counter()

    def line(self, cell, l):
        t = l.split()
        c = t[0][0].upper()
        if c == 'X':
            nets, sub, params = inst_cell(t)
            self.count['X'] += 1
            return ' '.join([san(t[0])] + [san(n) for n in nets] + [sub] + params)
        if c == 'R' and any(x.startswith('$[') for x in t):
            model = [x for x in t if x.startswith('$[')][0][2:-1]
            sub = [x for x in t if x.startswith('$SUB=')][0][5:]
            params, seen = [], set()
            for x in t[4:]:
                if '=' in x and not x.startswith('$'):
                    k = x.split('=')[0].lower()
                    if k not in seen:
                        seen.add(k)
                        params.append(x)
            self.count['R ' + model] += 1
            return ' '.join(['X' + san(t[0]), san(t[1]), san(t[2]), san(sub), model] + params)
        models = [i for i, x in enumerate(t) if x in PDK_DEVICES]
        if c in 'MQCDR' and models:
            i = models[0]
            model = t[i]
            nets = [san(x) for x in t[1:i]]
            if len(nets) != PDK_DEVICES[model]:
                raise SystemExit('%s: %s has %d terminals, %s needs %d' % (cell, t[0], len(nets), model, PDK_DEVICES[model]))
            params = t[i + 1:]
            if model in ('dantenna', 'dpantenna'):
                if model == 'dantenna' and self.nodcn:
                    self.count['removed dantenna'] += 1
                    return '* removed (--pads nodcn): ' + l
                params = [x for x in params if x.split('=')[0].lower() in ('l', 'w', 'm')]
            if model == 'ptap1':
                base = cell.replace('G1_VSS_DERIVATIVE__', '')
                inst = t[0].replace('R_G1_TAP_SYNTAX_', '')
                r = self.ptaps.get((base, inst))
                self.count['ptap1 R from sg13g2_io.spi' if r else 'ptap1 R PDK default'] += 1
                params = ['R=%s' % (r or PTAP_DEFAULT_R)]
            if model == 'npn13G2' and HBT_SELFT0:
                params = params + ['selft=0']
                self.count['npn13G2 selft=0 (--hbt-selft0)'] += 1
            self.count[c + ' ' + model] += 1
            return ' '.join(['X' + san(t[0])] + nets + [model] + params)
        raise SystemExit('untranslated CDL line in %s: %s' % (cell, l))


def closure(subs, root, external):
    """Subckts reachable from root, children first; names in 'external' are defined elsewhere (not descended)."""
    order, seen = [], set()

    def visit(n):
        if n in seen or n in external or n in PDK_DEVICES:
            return
        if n not in subs:
            raise SystemExit('subckt %s used but not defined in the CDL' % n)
        seen.add(n)
        for l in subs[n][1]:
            if l.split()[0][0] in 'Xx':
                visit(inst_cell(l.split())[1])
        order.append(n)
    visit(root)
    return order


def ideal_osc(ports, fosc):
    """g1_osc replacement (--osc ideal): the run_top.py ideal clock, gated by en (RTL osc_en) released at T_OSC."""
    en, t0, t1, t2, t3, clk, vdd, vss = ports
    return ['* g1_osc replaced (--osc ideal): ideal %.10g MHz clock of run_top.py, gated by en; no supply current' % (fosc / 1e6),
            '.subckt g1_osc %s' % ' '.join(ports),
            'Vosc_i osc_i %s pulse(0 %g %g 1n 1n %g %g)' % (vss, RT.VDD_V, RT.T_OSC * 1e-6, 0.5 / fosc - 1e-9, 1.0 / fosc),
            'Ben_g en_g %s V = v(%s, %s) * min(1, max(0, (time - %gu) / 50n))' % (vss, en, vss, RT.T_OSC),
            'Bosc_clk %s %s V = v(osc_i, %s) * (0.5 + 0.5*tanh((v(en_g, %s) - %g)/0.05))' % (clk, vss, vss, vss, RT.VDD_V / 2),
            'Rosc_vdd %s %s 1e12' % (vdd, vss),
            '.ends']


def cosim_digital(ports, vvp_note):
    """g1_digital replacement with the CDL's exact port list: XSPICE d_cosim of rtl/g1_dig_cosim_cdl.v."""
    p = dict(zip([san(x) for x in DIGITAL_PORTS], ports))
    outs = (['d_cmp_clk'] + ['d_s%d' % i for i in range(7, -1, -1)] + ['d_h%d' % i for i in range(7, -1, -1)] +
            ['d_trip_d', 'd_clr_d', 'd_fast_en', 'd_osc_en'] + ['d_t%d' % i for i in range(3, -1, -1)] +
            ['d_trip', 'd_gate_en', 'd_cause1', 'd_cause0', 'd_sdo'] + ['d_sp%d' % i for i in range(15, -1, -1)] +
            ['d_inrush', 'd_softarmed', 'd_t2f_en', 'd_t2f_mode', 'd_bgr_r4', 'd_fault_n', 'd_trip_set_sel', 'd_clk_div_out'])
    an = ([p['cmp_clk']] + [p['dac_soft_%d_' % i] for i in range(7, -1, -1)] + [p['dac_hard_%d_' % i] for i in range(7, -1, -1)] +
          [p['trip_d'], p['clr_d'], p['fast_en'], p['osc_en']] + [p['osc_trim_%d_' % i] for i in range(3, -1, -1)] +
          [p['trip'], p['gate_en'], p['trip_cause_1_'], p['trip_cause_0_'], p['sdo']] + ['sp%d' % i for i in range(15, -1, -1)] +
          ['inrush_active', 'soft_armed', p['t2f_en'], p['t2f_mode'], p['bgr_r4'], p['fault_n'], p['trip_set_sel'], p['clk_div_out']])
    if POR_PIN:
        return ['* g1_digital replaced by the real RTL (XSPICE d_cosim, rtl/g1_dig_cosim_cdl_por.v, --por-pin): por_n from the',
                '* CDL sg13g2_tiehi through the single-threshold receiver; en/sclk/sdi/osc_clk as well',
                '.subckt g1_digital %s' % ' '.join(ports),
                'aclock [%s] [d_osc_clk] adc_clock' % p['osc_clk'],
                'ain [%s %s %s %s] [d_en d_sclk d_sdi d_por_n] adc_clock' % (p['en'], p['sclk'], p['sdi'], p['por_n']),
                'aadc [%s %s %s] [d_cmp_soft d_cmp_hard d_tripped] adc' % (p['cmp_soft'], p['cmp_hard'], p['tripped']),
                'adig [d_osc_clk d_en d_sclk d_sdi d_cmp_soft d_cmp_hard d_tripped d_por_n] [%s] rtl' % ' '.join(outs),
                'adac [%s] [%s] dac' % (' '.join(outs), ' '.join(an)),
                '.ends']
    return ['* g1_digital replaced by the real RTL (XSPICE d_cosim, %s); CDL port list kept; por_n: the wrapper ties' % vvp_note,
            '* por_n = 1 (the CDL drives it from sg13g2_tiehi); en/sclk/sdi/osc_clk through the single-threshold receiver',
            '.subckt g1_digital %s' % ' '.join(ports),
            'aclock [%s] [d_osc_clk] adc_clock' % p['osc_clk'],
            'ain [%s %s %s] [d_en d_sclk d_sdi] adc_clock' % (p['en'], p['sclk'], p['sdi']),
            'aadc [%s %s %s] [d_cmp_soft d_cmp_hard d_tripped] adc' % (p['cmp_soft'], p['cmp_hard'], p['tripped']),
            'adig [d_osc_clk d_en d_sclk d_sdi d_cmp_soft d_cmp_hard d_tripped] [%s] rtl' % ' '.join(outs),
            'adac [%s] [%s] dac' % (' '.join(outs), ' '.join(an)),
            '.ends']


HBT_SELFT0 = False   # --hbt-selft0 (set in main)
INTERCONNECT = False  # --interconnect extracted (set in main)
INTERCONNECT_FILE = os.path.join(HERE, 'postlayout/top_interconnect_20260925.spice')
INTERCONNECT_SHA256 = 'ddc88cc765e99a0e982c9b6bc24817bfe336ae686930b2c12a85d514fb2adcc2'
POR_PIN = False      # --por-pin (set in main)
PEX_BLOCKS = ()   # --pex-blocks: blocks that use the extracted netlist under --netlist sch (set in main)
KEEP_CDL = ()     # --keep-cdl: blocks that keep the CDL schematic subckt under --netlist pex (set in main)


def pex_swaps(netlist, osc):
    """{CDL subckt name: blocks/ path} of the extracted block netlists used with --netlist pex."""
    out = {}
    for k in ('bgr', 'sense', 'trip', 'gate', 'osc', 't2f'):
        if netlist != 'pex' and k not in PEX_BLOCKS:
            continue
        if (k == 'osc' and osc != 'tl') or k in KEEP_CDL:
            continue
        rel = RT.T2F_NETLISTS['t2f'] if k == 't2f' else RT.BLOCKSETS['c1414'][k]['pex']
        full = os.path.join(BLOCKS, rel)
        if rel in RT.BLOCKSET_SHA256 and RT.sha256(full) != RT.BLOCKSET_SHA256[rel]:
            raise SystemExit('netlist blocks/%s does not match its bound SHA256' % rel)
        name, ports = RT.BLOCK_PORTS[k]
        if RT.subckt_ports(full, name) != ports:
            raise SystemExit('blocks/%s: .subckt %s ports differ from %r' % (rel, name, ports))
        out[CDL_BLOCKS[k]] = rel
    return out


def chip_netlist(netlist, osc, nodcn, fosc):
    """Deck lines of the translated chip (subckts + g1_chip_top copy), the external includes, and a report."""
    path = os.path.join(BLOCKS, CDL_REL)
    if RT.sha256(path) != CDL_SHA256:
        raise SystemExit('%s does not match its bound SHA256 %s' % (CDL_REL, CDL_SHA256))
    subs = parse_cdl(path)
    if subs[TOP][0] != TOP_PINS:
        raise SystemExit('g1_chip_top pins differ: %r' % subs[TOP][0])
    if subs['g1_digital'][0] != DIGITAL_PORTS:
        raise SystemExit('g1_digital ports differ: %r' % subs['g1_digital'][0])
    for k, name in CDL_BLOCKS.items():
        got = [norm_port(p) for p in subs[name][0]]
        if got != RT.BLOCK_PORTS[k][1].split():
            raise SystemExit('CDL %s ports %r do not map onto %r' % (name, subs[name][0], RT.BLOCK_PORTS[k][1]))
    swaps = pex_swaps(netlist, osc)
    replaced = {'g1_digital'} | ({'g1_osc'} if osc != 'tl' else set())
    order = closure(subs, TOP, set(swaps) | replaced)
    tr = Translator(nodcn, io_ptap_values(RT.IOSPI))
    L = []
    for n in order:
        if n == TOP:
            continue
        ports = [san(p) for p in subs[n][0]]
        L.append('.subckt %s %s' % (n, ' '.join(ports)))
        L += [tr.line(n, l) for l in subs[n][1]]
        L.append('.ends %s' % n)
    L += cosim_digital([san(p) for p in subs['g1_digital'][0]], 'rtl/g1_dig_cosim_cdl.v')
    if osc != 'tl':
        L += ideal_osc([san(p) for p in subs['g1_osc'][0]], fosc)
    # deck-local copy of g1_chip_top: ammeters on block supply pins, identical filler instances merged
    body, meters, groups, merged = [], {}, collections.OrderedDict(), 0
    report_ic = {}
    for l in subs[TOP][1]:
        t = l.split()
        if t[0][0] not in 'Xx':
            raise SystemExit('g1_chip_top: non-instance line %s' % l)
        nets, cell, params = inst_cell(t)
        if FILLER_RE.search(cell) and not params:
            groups.setdefault((cell, tuple(nets)), []).append(t[0])
            continue
        for pos, (vm, rail) in METERS.get(t[0], {}).items():
            if nets[pos] != rail:
                raise SystemExit('%s pin %d is on %s, expected %s' % (t[0], pos, nets[pos], rail))
            meters[vm] = rail
            nets[pos] = '%s__%s' % (rail, vm)
        body.append(' '.join([san(t[0])] + [san(n) for n in nets] + [cell] + params))
    for (cell, nets), names in groups.items():
        merged += len(names) - 1
        body.append(' '.join([san(names[0])] + [san(n) for n in nets] + [cell] + (['m=%d' % len(names)] if len(names) > 1 else [])))
    for vm, rail in sorted(meters.items()):
        body.append('%s %s %s__%s dc 0' % (vm.capitalize(), rail, rail, vm))
    if INTERCONNECT:
        # extracted top-level routing (postlayout/README_top_interconnect_20260925.md): C-only subckt, each port on the
        # CDL top net of the same name (i_core_ prefix, pad nets upper case), sub on VSS
        ports = RT.subckt_ports(INTERCONNECT_FILE, 'g1_top_interconnect').split()
        topnets = set()
        for l in subs[TOP][1]:
            topnets.update(inst_cell(l.split())[0])
        topnets.update(subs[TOP][0])
        conn = []
        for p in ports:
            if p == 'sub':
                conn.append('VSS')
                continue
            if p in ('d_elt', 'd_std', 'g_shared', 'hbt_b', 'hbt_c', 'hbt_e', 'sense_n', 'sense_p'):
                net = p.upper()                      # chip pins (pad side of the core route)
            elif p in topnets:
                net = p                              # en_i, gate_o, fault_n_o, net
            else:
                net = 'i_core_' + p
            if net not in topnets:
                raise SystemExit('interconnect port %s: CDL top net %s not found' % (p, net))
            conn.append(san(net))
        body.append('Xtop_interconnect %s g1_top_interconnect' % ' '.join(conn))
        report_ic.update(ports=len(ports) - 1)
    L.append('* g1_chip_top: deck-local copy of the CDL top; %d filler/decap/antenna instances merged into %d (m=count);'
             % (sum(len(v) for v in groups.values()), len(groups)))
    L.append('* supply-pin ammeters %s' % ', '.join('%s on %s' % kv for kv in sorted(meters.items())))
    L.append('.subckt %s %s' % (TOP, ' '.join(subs[TOP][0])))
    L += body
    L.append('.ends %s' % TOP)
    # name clashes between the translated CDL and the included extracted netlists
    defined = set(order) | replaced
    for name, rel in swaps.items():
        for l in open(os.path.join(BLOCKS, rel)):
            t = l.split()
            if t and t[0].lower() == '.subckt' and t[1] in defined:
                raise SystemExit('name clash: %s from blocks/%s is also emitted from the CDL' % (t[1], rel))
    if INTERCONNECT:
        L.insert(0, '.include %s' % INTERCONNECT_FILE)
        L.insert(0, '* extracted top-level interconnect (--interconnect extracted): %s sha256 %s, %d nets, C only (no series R)'
                 % (os.path.relpath(INTERCONNECT_FILE, BLOCKS), RT.sha256(INTERCONNECT_FILE), report_ic['ports']))
    report = dict(subckts=len(order) - 1, interconnect=(RT.sha256(INTERCONNECT_FILE)[:8] if INTERCONNECT else None), devices=dict(tr.count), merged=merged, meters=sorted(meters), swaps=swaps,
                  replaced=sorted(replaced))
    return L, swaps, report


def node_map(osc, netlist):
    m = {'vref': 'xchip.i_core_vref', 'iptat': 'xchip.i_core_iptat', 'isense': 'xchip.i_core_isense',
         'vref_buf': 'xchip.i_core_vref_buf', 'vped': 'xchip.i_core_unused_vped', 'cmp_clk': 'xchip.i_core_cmp_clk',
         'cmp_soft': 'xchip.i_core_cmp_soft', 'cmp_hard': 'xchip.i_core_cmp_hard', 'trip_d': 'xchip.i_core_trip_d',
         'clr_d': 'xchip.i_core_clr_d', 'fast_en': 'xchip.i_core_fast_en', 'tripped': 'xchip.i_core_tripped',
         'en_core': 'xchip.en_i', 'gate_core': 'xchip.gate_o', 'fault_core': 'xchip.fault_n_o',
         'osc_clk': 'xchip.i_core_osc_clk', 'osc_en': 'xchip.i_core_osc_en',
         'osc_en_g': 'xchip.xi_core_u_osc.en_g' if osc != 'tl' else 'xchip.i_core_osc_en',
         'dig_trip': 'xchip.i_core_trip', 'dig_gate_en': 'xchip.i_core_gate_en', 'cause1': 'xchip.i_core_trip_cause_1_',
         'cause0': 'xchip.i_core_trip_cause_0_', 'sdo': 'xchip.i_core_sdo_o',
         'inrush_active': 'xchip.xi_core_u_digital.inrush_active', 'soft_armed': 'xchip.xi_core_u_digital.soft_armed',
         'temp_out': 'xchip.i_core_temp_out_o', 't2f_en33': 'xchip.i_core_t2f_en_33', 't2f_mode33': 'xchip.i_core_t2f_mode_33',
         'pbias': 'xchip.i_core_pbias', 'pcasc': 'xchip.i_core_pcasc'}
    for i in range(8):
        m['soft%d' % i] = 'xchip.i_core_dac_soft_%d_' % i
        m['hard%d' % i] = 'xchip.i_core_dac_hard_%d_' % i
    for i in range(4):
        m['trim%d' % i] = 'xchip.i_core_osc_trim_%d_' % i
    for i in range(16):
        m['sp%d' % i] = 'xchip.xi_core_u_digital.sp%d' % i
    return m


def rename(text, nmap):
    def v(mo):
        kind, name = mo.group(1), mo.group(2).strip().lower()
        if kind.lower() == 'i':
            return 'i(v.xchip.%s)' % name if name.startswith('vm_') else mo.group(0)
        if name in nmap:
            return 'v(%s)' % nmap[name]
        for pre, new in (('xtrip.', 'xchip.xi_core_u_trip.'), ('xsense.', 'xchip.xi_core_u_sense.')):
            if name.startswith(pre):
                return 'v(%s)' % (new + name[len(pre):])
        return mo.group(0)
    return re.sub(r'\b([vViI])\(([^(),]+)\)', v, text)


def build_cdl_deck(case, name, netlist, temp, corner, tag, tstop, osc, method, nodcn):
    """run_top.build_deck's stimulus/board/measurement lines around the CDL chip."""
    powerup = case.get('powerup', False)
    t2f = 'off' if powerup else 'tl'
    base = RT.build_deck(case, name, 'sch', 'tl', temp, corner, tag, tstop, osc, 'ideal', 'beh', method,
                         blockset='c1414', t2f=t2f)
    fosc = RT.BEH['c1414_sch']['fosc']
    chip, swaps, rep = chip_netlist(netlist, osc, nodcn, fosc)
    nmap = node_map(osc, netlist)
    lines = base.splitlines()
    i_sup = next(i for i, l in enumerate(lines) if l.startswith('* ---- supplies'))
    i_pads = next(i for i, l in enumerate(lines) if l.startswith('* ---- pads') or l.startswith('* ---- minimal'))
    i_ven = next(i for i, l in enumerate(lines) if l.startswith('Ven '))
    i_save = next(i for i, l in enumerate(lines) if l.startswith('.save '))
    head = lines[:i_sup]
    L = [head[0], '* CDL-driven full chip (run_top_cdl.py): blocks/%s sha256 %s, top %s instantiated once' % (CDL_REL, CDL_SHA256, TOP),
         '* case %s | block netlists %s (%s) | clock to the RTL %s | corner %s | %g degC | pads %s | method %s' % (
             name, netlist, 'CDL schematic subckts' if netlist == 'sch' else 'extracted: ' + ', '.join(sorted(swaps)),
             osc, corner, temp, 'nodcn' if nodcn else 'pdk', method)]
    for k, rel in sorted(swaps.items()):
        L.append('* %s <- blocks/%s (sha256 %s%s)' % (k, rel, RT.sha256(os.path.join(BLOCKS, rel)),
                                                     '' if rel in RT.BLOCKSET_SHA256 else '; not hash-bound in run_top.py'))
    L.append('* translated: %d subckts; devices %s; replaced %s; %d filler instances merged' % (
        rep['subckts'], ', '.join('%s %d' % kv for kv in sorted(rep['devices'].items())), ', '.join(rep['replaced']), rep['merged']))
    if HBT_SELFT0:
        L.append('* WARNING deviation --hbt-selft0: selft=0 on every npn13G2 instance of the translated CDL (VBIC self-heating '
                 'thermal node removed; numerical work-around, not a model-card change)')
    if nodcn:
        L.append('* WARNING deviation --pads nodcn: every dantenna instance of the translated chip removed '
                 '(IO cells and sg13g2_antennanp; %d instances); reason: run_top.py PADS_NODCN_WARNING'
                 % rep['devices'].get('removed dantenna', 0))
    L.append('* not in this deck (differences to run_top.py): the Cw_* wire capacitors (the CDL has none); the '
             'd_source RTL stimulus (the RTL reads the EN/SCLK/SDI IOPadIn outputs); fitted GATE/FAULT_N drivers')
    for l in head[1:]:
        if l.startswith('*'):
            continue
        if l.startswith('.include'):
            continue
        if l.startswith('.nodeset'):
            l = rename(RT.nodesets('exposed' if 'g1_sense' in swaps else 'hier'), nmap)
        L.append(l)
    for rel in swaps.values():
        L.append('.include %s' % os.path.join(BLOCKS, rel))
    L += lines[i_sup:i_pads]
    L += [l for l in lines[i_ven:i_save] if l.split()[:1] in (['Ven'], ['Vsclk'], ['Vsdi']) or
          (l.startswith('.model ') and not l.startswith('.model dsrc '))]
    L.append('* ---- the chip: g1_chip_top_1414.cdl, 22 pins on the board fixture')
    L += chip
    L.append('Xchip %s %s' % (' '.join(BOARD[p] for p in TOP_PINS), TOP))
    L.append('Cvref_ext vref_pad 0 {CVREF}')
    L.append('Csdo sdo_pad 0 20p')
    L.append('Ctemp_out temp_out_pad 0 20p')
    for p in PIN_PULLDOWN:
        L.append('Rpd_%s %s 0 1meg' % (p.lower(), BOARD[p]))
    tail = rename('\n'.join(lines[i_save:]), nmap).splitlines()
    if powerup:
        k = next(i for i, l in enumerate(tail) if not (l.startswith('.save') or l.startswith('+ ')))
        tail.insert(k, '+ v(xchip.net) v(xchip.i_core_osc_en) v(xchip.i_core_trip) v(xchip.en_i)')
        k = next(i for i, l in enumerate(tail) if l.startswith('echo "POWERUP'))
        tail[k + 1:k + 1] = [
            'meas tran t_vdd06 when v(vdd)=0.6 rise=1',
            'meas tran t_iovdd11 when v(iovdd)=1.1 rise=1',
            'meas tran t_por06 when v(xchip.net)=0.6 rise=1',
            'meas tran t_oscen when v(xchip.i_core_osc_en)=0.6 rise=1',
            'meas tran tripped_end find v(xchip.i_core_tripped) at=%gu' % case['tstop'],
            'meas tran gate_core_end find v(xchip.gate_o) at=%gu' % case['tstop'],
            'meas tran en_i_max_enlow max v(xchip.en_i) from=0 to=%gu' % (case['en'][0][0] - 0.1),
            'meas tran dig_trip_max max v(xchip.i_core_trip) from=0 to=%gu' % (case['en'][0][0] - 0.1),
            'echo "PORTIMING vdd_0p6_s=" $&t_vdd06 " iovdd_1p1_s=" $&t_iovdd11 " por_n_0p6_s=" $&t_por06 " osc_en_rise_s=" $&t_oscen " tripped_end=" $&tripped_end " gate_core_end=" $&gate_core_end " en_i_max_EN_low=" $&en_i_max_enlow " dig_trip_max_EN_low=" $&dig_trip_max']
    L += tail
    return '\n'.join(L) + '\n', swaps, rep


def check_instances(deck, swaps):
    """Every X instance of the deck resolves to a subckt (deck, included pex files or PDK device) with its port count."""
    text = deck + ''.join(open(os.path.join(BLOCKS, rel)).read() for rel in swaps.values())
    if INTERCONNECT:
        text += open(INTERCONNECT_FILE).read()
    defs, cur, bad = dict(PDK_DEVICES), None, []
    lines = []
    for raw in text.splitlines():
        if raw.startswith('+') and lines:
            lines[-1] += ' ' + raw[1:]
        else:
            lines.append(raw)
    for l in lines:
        t = l.split()
        if t and t[0].lower() == '.subckt':
            defs[t[1].lower()] = len([x for x in t[2:] if '=' not in x])
    defs = {k.lower(): v for k, v in defs.items()}
    n = 0
    for l in lines:
        t = l.split()
        if t and t[0][0] in 'Xx':
            pos = [x for x in t[1:] if '=' not in x]
            cell = pos[-1].lower()
            n += 1
            if cell not in defs:
                bad.append('undefined %s: %s' % (cell, l[:120]))
            elif defs[cell] != len(pos) - 1:
                bad.append('port count %d != %d: %s' % (len(pos) - 1, defs[cell], l[:120]))
    return n, bad


def validate_prefix(out, wave_path, requested_end_s, nmap):
    """run_top.validate_prefix with the mapped vector names."""
    expected = ['time'] + [rename(x, nmap) for x in
                           ['v(vref)', 'v(isense)', 'v(gate)', 'v(vdd)', 'v(vdda)', 'v(osc_clk)', 'v(cmp_clk)']]
    end = re.search(r'^DIAGNOSTIC_PREFIX_END_S\s+([-+0-9.eE]+)', out, re.M)
    tol = max(1e-15, requested_end_s * 1e-6)
    if not end or abs(float(end[1]) - requested_end_s) > tol:
        return False, 'requested endpoint not reported'
    try:
        with open(wave_path) as f:
            if f.readline().split() != expected:
                return False, 'missing or unexpected waveform columns'
            rows, prev = 0, None
            for line in f:
                vals = [float(v) for v in line.split()]
                if len(vals) != len(expected) or not all(math.isfinite(v) for v in vals):
                    return False, 'incomplete or nonfinite waveform row'
                prev = vals[0]
                rows += 1
    except (OSError, ValueError):
        return False, 'waveform missing or unreadable'
    if rows < 2 or abs(prev - requested_end_s) > tol:
        return False, 'saved waveform does not reach requested endpoint'
    return True, 'saved finite waveform reaches requested endpoint'


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('cases', nargs='+')
    ap.add_argument('--netlist', default='sch', choices=('sch', 'pex'))
    ap.add_argument('--osc', default='ideal', choices=('ideal', 'tl'))
    ap.add_argument('--pads', default='nodcn', choices=('nodcn', 'pdk'))
    ap.add_argument('--method', default=None, choices=('gear', 'trap'), help='default trap (gear for power-up cases)')
    ap.add_argument('--temp', type=float, default=27)
    ap.add_argument('--corner', default='tt', choices=tuple(RT.CORNERS))
    ap.add_argument('--timeline', choices=('baseline', 'compact'), default='baseline')
    ap.add_argument('--analysis', choices=('functional', 'prefix', 'op'), default='functional')
    ap.add_argument('--tstop', type=float, default=None)
    ap.add_argument('--timeout', type=float, default=300)
    ap.add_argument('--run-id', default=None)
    ap.add_argument('--image-id', default=None)
    ap.add_argument('--keep-cdl', default='', metavar='BLOCK[,...]',
                    help='with --netlist pex: blocks (bgr sense trip gate t2f) that keep the CDL schematic subckt')
    ap.add_argument('--maxstep-ns', type=float, default=None, help='maximum transient step (ns); default run_top.TMAX = 5 ns')
    ap.add_argument('--extra-options', default=None, help='diagnostic: extra .option line after the solver line')
    ap.add_argument('--pex-blocks', default='', metavar='BLOCK[,...]',
                    help='with --netlist sch: blocks (bgr sense trip gate t2f) that use their extracted netlist')
    ap.add_argument('--hbt-selft0', action='store_true',
                    help='diagnostic deviation: instance parameter selft=0 (no VBIC self-heating node) on every npn13G2 of the '
                         'translated CDL (not on included extracted netlists)')
    ap.add_argument('--por-pin', action='store_true',
                    help='RTL por_n driven by the CDL tiehi net (wrapper rtl/g1_dig_cosim_cdl_por.v) instead of tied to 1')
    ap.add_argument('--cdl', default=None, metavar='PATH',
                    help='alternative chip CDL (e.g. a regenerated canonical r3); requires --cdl-sha256, which is checked')
    ap.add_argument('--cdl-sha256', default=None, help='expected SHA256 of --cdl')
    ap.add_argument('--ser-start-us', type=float, default=None,
                    help='compact timeline: first serial frame at this time instead of 4.0 us (EN rises at 3.0 us)')
    ap.add_argument('--rtl-dir', default='rtl', choices=tuple(RT.RTL_DIRS), help='digital RTL copy (run_top.RTL_DIRS)')
    ap.add_argument('--interconnect', default='none', choices=('none', 'extracted'),
                    help='extracted: add the kpex top-level routing C (postlayout/top_interconnect_20260925.spice, hash-bound)')
    ap.add_argument('--t2f-off-write', action='store_true',
                    help='stimulus: serial write TEMP_CTRL (0x29, ECO register map 1.2) = 0 right after the first frame, so '
                         'G1_T2F sits in its EN-low state; label: T2F disabled by register write, sensor accuracy not exercised')
    ap.add_argument('--fault-mult', type=float, default=None, metavar='X',
                    help="fault-event load level as X x nominal 1 A (run_top.scale_fault: single fault level, timing unchanged)")
    ap.add_argument('--dry', action='store_true')
    a = ap.parse_args()
    if a.analysis == 'prefix' and a.tstop is None:
        ap.error('--analysis prefix requires --tstop US')
    global KEEP_CDL, PEX_BLOCKS, HBT_SELFT0
    HBT_SELFT0 = a.hbt_selft0
    global POR_PIN, WRAPPER, CDL_REL, CDL_SHA256
    if (a.cdl is None) != (a.cdl_sha256 is None):
        ap.error('--cdl and --cdl-sha256 go together')
    if a.cdl:
        CDL_REL, CDL_SHA256 = os.path.abspath(a.cdl), a.cdl_sha256
    RT.RTL_FILES = RT.make_rtl_files(a.rtl_dir)
    global INTERCONNECT
    INTERCONNECT = a.interconnect == 'extracted'
    if INTERCONNECT and RT.sha256(INTERCONNECT_FILE) != INTERCONNECT_SHA256:
        raise SystemExit('interconnect file does not match its bound SHA256')
    POR_PIN = a.por_pin
    if POR_PIN:
        WRAPPER = os.path.join(HERE, 'rtl/g1_dig_cosim_cdl_por.v')
    KEEP_CDL = tuple(x for x in a.keep_cdl.split(',') if x)
    PEX_BLOCKS = tuple(x for x in a.pex_blocks.split(',') if x)
    if any(k not in ('bgr', 'sense', 'trip', 'gate', 't2f') for k in PEX_BLOCKS):
        ap.error('--pex-blocks: blocks bgr sense trip gate t2f')
    if any(k not in ('bgr', 'sense', 'trip', 'gate', 't2f') for k in KEEP_CDL):
        ap.error('--keep-cdl: blocks bgr sense trip gate t2f')
    run_id = a.run_id or time.strftime('%Y%m%dT%H%M%SZ', time.gmtime()) + '_' + uuid.uuid4().hex[:8]
    if a.timeline == 'compact':
        if a.cases != ['c_mid'] and a.cases not in (['c'], ['c_fast'], ['e20']):
            ap.error('compact timeline: one of c_mid, c, c_fast, e20')
        RT.T_SER, RT.T_STEP = (a.ser_start_us or 4.0), 16.0
        RT.CASES = RT.make_cases()
        RT.CASES['c_mid']['tstop'] = 28
        for k in ('c', 'c_fast', 'e20'):
            RT.CASES[k]['tstop'] = 22
    if a.ser_start_us and a.timeline == 'baseline':
        RT.T_SER = a.ser_start_us     # first serial frame (eco4_cdl_c_mid_ser4 timing), event time unchanged
    RT.RTL_WRAPPER_T2F = WRAPPER      # rtl_files('tl') -> the CDL wrapper first, then the unchanged RTL
    os.makedirs(BUILD, exist_ok=True)
    env = dict(os.environ)
    env['LD_LIBRARY_PATH'] = '/foss/tools/iverilog/lib' + (':' + env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '')
    for name in a.cases:
        if name not in RT.CASES or name == 'osc':
            raise SystemExit('unknown or unsupported case %s' % name)
        case = dict(RT.CASES[name])
        if a.fault_mult is not None:
            try:
                case = RT.scale_fault(case, a.fault_mult)
            except ValueError as exc:
                ap.error(str(exc))
        if a.t2f_off_write:
            if a.rtl_dir != 'eco_20260925' or not case['frames']:
                ap.error('--t2f-off-write needs --rtl-dir eco_20260925 (TEMP_CTRL = 0x29) and a case with serial frames')
            case['frames'] = [case['frames'][0], (0x29, 0x00)] + list(case['frames'][1:])
            case['desc'] += '; T2F disabled by register write TEMP_CTRL=0 (stimulus), sensor accuracy not exercised'
            if 'quiet' not in case and not a.ser_start_us:     # the extra frame ends ~1 us before the event: supply window = last 1 us before it
                ev = case.get('event_us', RT.T_STEP)
                case['quiet'] = (ev - 1.0, ev)
        method = a.method or ('gear' if case.get('powerup') else 'trap')
        if a.maxstep_ns:
            case['tmax'] = a.maxstep_ns * 1e-9
        tag = 'cdl_%s_%s_%s_%gC_%s%s%s%s%s_%s_%s' % (
            name, a.netlist, a.corner, a.temp, method, '_osctl' if a.osc == 'tl' else '', '_padspdk' if a.pads == 'pdk' else '',
            ('_keep-' + '-'.join(KEEP_CDL) if KEEP_CDL else '') + ('_pexblk-' + '-'.join(PEX_BLOCKS) if PEX_BLOCKS else '') + ('_selft0' if HBT_SELFT0 else '') + ('_por' if POR_PIN else '') + ('_compact' if a.timeline == 'compact' else '') + (('_cdl' + CDL_SHA256[:8]) if a.cdl else '') + (('_rtl' + a.rtl_dir.replace('_', '')) if a.rtl_dir != 'rtl' else '') + (('_ser%g' % a.ser_start_us).replace('.', 'p') if a.ser_start_us else '') + ('_icx' if INTERCONNECT else '') + ('_t2foff' if a.t2f_off_write else '') + (('_fm%g' % a.fault_mult).replace('.', 'p') if a.fault_mult is not None else ''), (('_t%g' % a.tstop) if a.tstop else '') + (('_maxstep%gns' % a.maxstep_ns) if a.maxstep_ns else '') +
            (('_opt' + re.sub(r'[^A-Za-z0-9]+', '', a.extra_options.replace('-', 'm'))) if a.extra_options else ''), a.analysis, run_id)
        for d, ext in ((BUILD, '.cir'), (os.path.join(HERE, 'logs'), '.log'), (os.path.join(HERE, 'logs'), '.json')):
            if os.path.exists(os.path.join(d, tag + ext)):
                raise SystemExit('refusing to overwrite evidence: ' + tag)
        deck, swaps, rep = build_cdl_deck(case, name, a.netlist, a.temp, a.corner, tag, a.tstop, a.osc, method, a.pads == 'nodcn')
        nmap = node_map(a.osc, a.netlist)
        if a.analysis != 'functional':
            before, ctl = RT.diagnostic_deck(deck, a.analysis, a.tstop, tag).split('.control\n', 1)
            deck = before + '.control\n' + rename(ctl, nmap)
        if a.extra_options:
            deck = re.sub(r'^(\.option method=.*)$', lambda m: m.group(1) + '\n.option ' + a.extra_options, deck, count=1, flags=re.M)
        RT.validate_exports(deck)
        n, bad = check_instances(deck, swaps)
        print('instances checked: %d, problems: %d' % (n, len(bad)))
        for b in bad[:20]:
            print('  ' + b)
        if bad:
            raise SystemExit('instance check failed')
        print('translation: %s' % rep)
        deck_path = os.path.join(BUILD, tag + '.cir')
        with open(deck_path, 'w') as f:
            f.write(deck)
        if a.dry:
            print('wrote', deck_path)
            continue
        os.makedirs(os.path.join(HERE, 'decks'), exist_ok=True)
        with open(os.path.join(HERE, 'decks', tag + '.cir'), 'w') as f:
            f.write(deck)
        log_path = os.path.join(HERE, 'logs', tag + '.log')
        with open(log_path, 'w') as log:
            log.write('# G1 CDL-driven full-chip run %s  %s UTC\n# %s\n' % (tag, time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), case['desc']))
            log.write('# deck %s\n# CDL sha256 %s blocks/%s\n' % (os.path.relpath(deck_path, ROOT), RT.sha256(os.path.join(BLOCKS, CDL_REL)), CDL_REL))
            for k, rel in swaps.items():
                log.write('# %s <- sha256 %s blocks/%s\n' % (k, RT.sha256(os.path.join(BLOCKS, rel)), rel))
            log.write('# translation %s\n' % rep)
            log.write('# IO models sha256 %s %s (ptap1 values only)\n' % (RT.sha256(RT.IOSPI), RT.IOSPI))
            if os.path.exists(RT.PDK + '/COMMIT'):
                log.write('# PDK commit %s\n' % open(RT.PDK + '/COMMIT').read().strip())
            v = subprocess.run(['ngspice', '-v'], capture_output=True, text=True).stdout.splitlines()
            log.write('# %s\n' % next((l.strip('* ') for l in v if 'ngspice-' in l), 'ngspice version line not found'))
            log.write('# %s\n' % subprocess.run(['iverilog', '-V'], capture_output=True, text=True).stdout.splitlines()[0])
            vvp = RT.compile_rtl(log, 'tl', tag)
            if vvp not in deck or RT.verify_vvp(vvp):
                raise SystemExit('compiled RTL missing from deck or unloadable')
            log.flush()
            meta = dict(tag=tag, analysis=a.analysis, options=vars(a), runner='run_top_cdl.py',
                        runner_sha256=RT.sha256(__file__), run_top_sha256=RT.sha256(RT.__file__),
                        cdl_sha256=CDL_SHA256, swaps=swaps, translation=rep, image_id=a.image_id,
                        deck_sha256=RT.sha256(deck_path),
                        rtl_sha256={os.path.relpath(p, ROOT): RT.sha256(p) for p in RT.rtl_files('tl')})
            outcome = run_bounded(['ngspice', '-b', deck_path], log, os.path.join(HERE, 'logs', tag + '.json'),
                                  a.timeout, cwd=HERE, env=env, metadata=meta)
            log.write('\n# run status %s\n# ngspice exit %s, wall time %.0f s\n' % (outcome['status'], outcome['returncode'], outcome['wall_s']))
        out = open(log_path, errors='replace').read()
        keep = [l for l in out.splitlines() if re.match(r'^(QUIET|CLOCK|SUPPLY_uA|T2F|TRIP|NO_TRIP_EXPECTED|CHARGE|REARM|POWERUP|PORTIMING|DIAGNOSTIC_\w+)\b', l)]
        err = [l.strip() for l in out.splitlines() if 'Timestep too small' in l or ('rror' in l and 'measure' not in l)]
        failure = solver_failure(out)
        if re.search(r'mismatched XSPICE/co-simulator', out):
            outcome['status'] = 'failed'
            err.insert(0, 'COSIM FAILURE')
        if failure:
            outcome['solver_failure_diagnostic'] = failure.group(0)
        if a.analysis == 'prefix':
            ok, detail = validate_prefix(out, os.path.join(BUILD, 'waves_%s.txt' % tag), a.tstop * 1e-6, nmap)
            outcome['diagnostic_detail'] = detail
            outcome['diagnostic_acceptance'] = 'passed' if outcome['status'] == 'completed' and ok and not failure else (
                'not run to completion' if outcome['status'] in ('timeout', 'interrupted') else 'failed')
        atomic_json(os.path.join(HERE, 'logs', tag + '.json'), outcome)
        waves = os.path.join(BUILD, 'waves_%s.txt' % tag)
        if os.path.exists(waves):
            nrow = sum(1 for _ in open(waves)) - 1
            os.makedirs(os.path.join(HERE, 'results', 'waves'), exist_ok=True)
            RT.decimate(waves, os.path.join(HERE, 'results', 'waves', tag + '.txt'), max(1, nrow // 2000))
        with open(os.path.join(HERE, 'results_cdl.txt'), 'a') as f:
            f.write('== %s | %s; analysis=%s | wall %.0f s, ngspice exit %s, status %s\n' % (
                tag, case['desc'], a.analysis, outcome['wall_s'], outcome['returncode'], outcome['status']))
            for l in keep + err[:3]:
                f.write(l + '\n')
        print('== %s (%.0f s) %s' % (tag, outcome['wall_s'], outcome['status']))
        for l in keep + err[:3]:
            print(l)
        if outcome['status'] != 'completed':
            raise SystemExit(124 if outcome['status'] == 'timeout' else 1)


if __name__ == '__main__':
    main()
