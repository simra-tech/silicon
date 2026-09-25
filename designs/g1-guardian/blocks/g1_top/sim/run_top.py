#!/usr/bin/env python3
"""G1_TOP breaker-path chip-level deck generator and runner (ngspice 46 + Icarus Verilog d_cosim).

Run from the repository root inside the pinned container:

    G1_WORKDIR=designs/g1-guardian/blocks/g1_top/sim flow/run.sh python3 run_top.py [options] CASE [CASE ...]
    G1_WORKDIR=designs/g1-guardian/blocks/g1_top/sim flow/run.sh python3 run_top.py --list

Options: --netlist sch|pex   schematic or kpex post-layout block netlists (default sch)
         --blockset legacy|c1414  Sep-19 block netlists (default) or those of the frozen 1414 um chip (BLOCKSETS)
         --front tl|beh      analog front end transistor-level (default) or behavioural (long runs, see README)
         --temp T            degC (default 27)      --corner tt|ss|ff (default tt)
         --osc ideal|tl      clock to the RTL: ideal source at the block frequency (default) or the transistor-level
                             oscillator output (aborts the solver in most cases, README)
         --tstop US          override the case's end time     --dry  write the deck only

The deck (README "Simulated"): external 25 mOhm shunt + 10 mOhm ground return; a behavioural load
current source (waveform library below) cut by a switch on the external FET gate node (5 nF + 10 Ohm);
SENSE_P / SENSE_N / VREF analog pads, EN / SCLK / SDI input pads, GATE (30 mA) and FAULT_N (4 mA)
output pads as the PDK sg13g2_io SPICE models; G1_BGR -> G1_SENSE -> G1_TRIP -> G1_GATE at transistor
level with G1_OSC as the system clock; the digital macro as the real RTL (g1_digital, blocks/g1_ctrl/rtl
and blocks/g1_seu/rtl) co-simulated through the XSPICE d_cosim code model and the Icarus shim (ivlng).

Timeline of every functional case: supplies on from t = 0 (DC operating point), oscillator enabled at
0.1 us, EN pad high at T_EN, serial write frames from T_SER (always INRUSH = 0 so that the trip paths are
live before the load event; every other register keeps its reset value unless the case says
otherwise), load event at T_STEP. Register defaults (G1_REGISTER_MAP.md): DAC_SOFT 0x99, DAC_HARD 0xFE,
SOFT_TIME 0x0027 (~1 ms), HARD_N 4, MODE 0x03. Power-up cases ramp the supplies instead.
Decks: decks/ (copy) and build/g1_top/ (run location, gitignored). Logs: logs/. Decimated waveforms: results/waves/.
One summary block per run is appended to results_top.txt.
"""
import argparse
import hashlib
import gzip
import os
import re
import subprocess
import time
import uuid
import math
from run_bounded import run_bounded, atomic_json
from simulation_errors import solver_failure

HERE = os.path.dirname(os.path.abspath(__file__))                 # blocks/g1_top/sim
BLOCKS = os.path.abspath(os.path.join(HERE, '..', '..'))           # blocks/
ROOT = os.path.abspath(os.path.join(BLOCKS, '..', '..', '..'))     # repository root (/work in the container)
BUILD = os.path.join(ROOT, 'build', 'g1_top')
PDK = os.environ.get('PDK_ROOT', '/foss/pdks') + '/' + os.environ.get('PDK', 'ihp-sg13g2')
MODELS = PDK + '/libs.tech/ngspice/models'
IOSPI = PDK + '/libs.ref/sg13g2_io/spice/sg13g2_io.spi'

NETLISTS = {
    'sch': {
        'bgr': 'g1_bgr/xschem/g1_bgr.spice',
        'sense': 'g1_sense/sim/netlist/g1_sense.spice',
        'trip': 'g1_trip/sim/netlist/g1_trip.spice',
        'osc': 'g1_osc/sim/netlist/g1_osc.spice',
        'gate': 'g1_gate/sim/netlist/g1_gate.spice',
    },
    'pex': {
        'bgr': 'g1_bgr/sim/postlayout/g1_bgr_pex.spice',
        'sense': 'g1_sense/sim/postlayout/g1_sense_pex.spice',
        'trip': 'g1_trip/sim/postlayout/g1_trip_pex.spice',
        'osc': 'g1_osc/sim/postlayout/g1_osc_pex.spice',
        'gate': 'g1_gate/sim/postlayout/g1_gate_pex.spice',
    },
}
# --blockset c1414: the analog blocks of the frozen 1414 um native-lineage chip
# (soft-inputpair4-parent-20260924-r3 candidate.gds, SHA256 60730627...). Per block and view the entry names
# the netlist; None means that view does not exist for this chip, so the other view is used and a WARNING is
# written to the deck header and the log. Subckt names and pin orders equal the legacy ones (checked by
# resolve_netlists), so no wrapper subckt is needed.
#   bgr   BGR586 canonical source 586ffb58 (1,036 devices, as the chip CDL g1_bgr). The supply-routing
#         context cells in the GDS add metal only. The file carries the 329 historical Sep-19 kpex
#         capacitors. --netlist pex uses the kpex 2.5D CC extraction of the chip's BGR layout bank.gds
#         (e3ecfc62; LVS-clean; g1_bgr586_pex.spice 01227a3d, 978 capacitors, 10.1 pF), added 2026-09-24 13:50.
#   sense R100 (comp45 + RZ = 100 um): schematic candidate bb933fda; own-native partial-field C netlist
#         ffb14762 (byte copy of the sense-comp45-rz100-actual-source-20260923-r1 output; OTA internal
#         nodes exposed as __pex_<inst>_<node> ports; unbound VSUBS capacitors excluded).
#   trip  NF4 soft input pair (W24/L0.68, ng=4) + regenpair4 hard comparator, schematic f5f0a90a; its
#         extracted netlist is used from g1_trip/sim/postlayout/g1_trip_nf4_pex.spice once it exists.
#   osc   R0.95 CPEX 8efd7a09 (no R0.95 schematic netlist exists). The ideal clock runs at its loaded
#         nominal trim-8 frequency 9.436194721 MHz (g1_osc/sim/qualification/fulltree_r095_load_20260924).
#   gate  retained Sep-19 netlists.
BLOCKSETS = {
    'legacy': {k: {'sch': NETLISTS['sch'][k], 'pex': NETLISTS['pex'][k]} for k in NETLISTS['sch']},
    'c1414': {
        'bgr': {'sch': 'g1_bgr/layout/coordinated_full_closure/evidence/pex-preparation-20260922-r1/controls/r1/baseline_586.spice',
                'pex': 'g1_bgr/sim/postlayout/g1_bgr586_pex.spice'},
        'sense': {'sch': 'g1_trip/sim/qualification/joint586-softinputpair4-nf4-roomcal-s73133-20260924-r1/sense.spice',
                  'pex': 'g1_sense/sim/postlayout/g1_sense_r100_partialc.spice'},
        'trip': {'sch': 'g1_trip/sim/qualification/joint586-softinputpair4-nf4-roomcal-s73133-20260924-r1/trip.spice',
                 'pex': 'g1_trip/sim/postlayout/g1_trip_nf4_pex.spice'},
        'osc': {'sch': None,
                'pex': 'g1_osc/sim/qualification/fulltree_r095_load_20260924/common/osc.spice'},
        'gate': {'sch': NETLISTS['sch']['gate'], 'pex': NETLISTS['pex']['gate']},
    },
}
# bound SHA256 of the c1414 netlists: a changed file is refused rather than silently simulated
BLOCKSET_SHA256 = {
    'g1_bgr/layout/coordinated_full_closure/evidence/pex-preparation-20260922-r1/controls/r1/baseline_586.spice':
        '586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b',
    'g1_trip/sim/qualification/joint586-softinputpair4-nf4-roomcal-s73133-20260924-r1/sense.spice':
        'bb933fdabf3fd8a5117bf47f33cd40657caf78ef424e6a9bfddda0f11190d782',
    'g1_sense/sim/postlayout/g1_sense_r100_partialc.spice':
        'ffb14762659eaf02b6a62e9edea3caa0e143cbc7881378b329d6ab9945a6554b',
    'g1_trip/sim/qualification/joint586-softinputpair4-nf4-roomcal-s73133-20260924-r1/trip.spice':
        'f5f0a90aff361fd782f29112217cbd647d18af593a930ade2d59dfbab5847a92',
    'g1_osc/sim/qualification/fulltree_r095_load_20260924/common/osc.spice':
        '8efd7a09faf173da8604a219f73fd3ea5ec2508618d8361a050770c099d8b1c5',
    'g1_bgr/sim/postlayout/g1_bgr586_pex.spice':
        '01227a3d8d8210d10d2d1ee6933842351140b8825fe29282f0327936a3064ad5',
    'g1_trip/sim/postlayout/g1_trip_nf4_pex.spice':
        'ba86b7b2a530abae365d539297909e033b24a54597f9cc75d8dff273c30d401c',
}
# --t2f tl: G1_T2F at transistor level as the chip carries it (baseline revision, not rev1; block map of
# g1_padring/reports/signoff-1414-20260924/README.md: sim form sim/postlayout/g1_t2f_pex.spice 441edabc) behind
# two g1_ls_up level shifters (schematic netlist; the CDL's g1_ls_up source), wired as g1_chip_top_1414.cdl.
T2F_NETLISTS = {'t2f': 'g1_t2f/sim/postlayout/g1_t2f_pex.spice', 'ls_up': 'g1_ctrl/ls/sim/netlist/g1_ls_up.spice'}
BLOCKSET_SHA256.update({
    'g1_t2f/sim/postlayout/g1_t2f_pex.spice': '441edabc0484c9de1e035d585369f37d460afe32370e73935044693bbfd0c78a',
    'g1_ctrl/ls/sim/netlist/g1_ls_up.spice': '5567c8079e57ced973d3e47dad6a7afe1776987de3962f9be397c6a8d0549b56',
})
RTL_WRAPPER_T2F = os.path.join(HERE, 'rtl/g1_dig_cosim_t2f.v')
# subckt name and port order the deck instantiates (legacy headers)
BLOCK_PORTS = {
    'bgr': ('g1_bgr', 'vdd vss r4 vref iptat pbias pcasc vbe dvbe'),
    'sense': ('g1_sense', 'sense_p sense_n vref iptat isense vped vref_buf vdd vss'),
    'trip': ('g1_trip', 'isense vref cmp_clk soft0 soft1 soft2 soft3 soft4 soft5 soft6 soft7 hard0 hard1 hard2 '
                        'hard3 hard4 hard5 hard6 hard7 cmp_soft cmp_hard vdd vdda vss'),
    'osc': ('g1_osc', 'en trim0 trim1 trim2 trim3 osc_clk vdd vss'),
    'gate': ('g1_gate', 'trip_d clr_d fast_en hard_cmp en_core gate_core fault_core tripped vdd vdda vss'),
    't2f': ('g1_t2f', 'vdd vdd12 vss pbias pcasc vref en mode fout'),
    'ls_up': ('g1_ls_up', 'in out vdd vdda vss'),
}


def resolve_t2f():
    """T2F and level-shifter netlist paths (relative to BLOCKS), hash- and port-checked."""
    for k, rel in T2F_NETLISTS.items():
        full = os.path.join(BLOCKS, rel)
        if sha256(full) != BLOCKSET_SHA256[rel]:
            raise SystemExit('netlist blocks/%s does not match its bound SHA256 %s' % (rel, BLOCKSET_SHA256[rel]))
        name, ports = BLOCK_PORTS[k]
        if subckt_ports(full, name) != ports:
            raise SystemExit('blocks/%s: .subckt %s ports differ from the deck instance %r' % (rel, name, ports))
    return dict(T2F_NETLISTS)


def subckt_ports(path, name):
    """Port list of '.subckt <name>' in a SPICE file (continuation lines joined, parameters dropped)."""
    lines = open(path).read().splitlines()
    for i, line in enumerate(lines):
        f = line.split()
        if len(f) > 1 and f[0].lower() == '.subckt' and f[1] == name:
            ports = f[2:]
            j = i + 1
            while j < len(lines) and lines[j].startswith('+'):
                ports += lines[j][1:].split()
                j += 1
            return ' '.join(x for x in ports if '=' not in x)
    return None


# --view-override block=view[,block=view...]: per-block view applied after --netlist/--blockset (set in main)
VIEW_OVERRIDE = {}


def parse_view_override(text):
    """'bgr=sch,trip=pex' -> {'bgr': 'sch', 'trip': 'pex'}; blocks of BLOCKSETS, views sch|pex."""
    out = {}
    for item in filter(None, (x.strip() for x in (text or '').split(','))):
        k, sep, v = item.partition('=')
        if not sep or k not in BLOCKSETS['legacy'] or v not in ('sch', 'pex') or k in out:
            raise ValueError('bad --view-override item %r (block=sch|pex, blocks %s)' % (item, ','.join(BLOCKSETS['legacy'])))
        out[k] = v
    return out


def resolve_netlists(blockset, netlist):
    """(netlist paths relative to BLOCKS, warnings, G1_SENSE internal-node naming) for a blockset and view.
    VIEW_OVERRIDE replaces the view of individual blocks; the SHA256 and port checks apply unchanged."""
    paths, warnings, style = {}, [], 'hier'
    netlist0 = netlist
    for k, views in BLOCKSETS[blockset].items():
        netlist = VIEW_OVERRIDE.get(k, netlist0)
        other = 'sch' if netlist == 'pex' else 'pex'
        if k in VIEW_OVERRIDE and VIEW_OVERRIDE[k] != netlist0:
            warnings.append('OVERRIDE %s: %s view instead of --netlist %s (--view-override)' % (k, netlist, netlist0))
        rel = views[netlist]
        if rel is None:
            warnings.append('WARNING %s: no %s netlist exists for blockset %s; using the %s netlist' % (k, netlist, blockset, other))
        elif not os.path.exists(os.path.join(BLOCKS, rel)):
            if blockset == 'legacy':
                raise SystemExit('missing netlist blocks/' + rel)
            warnings.append('WARNING %s: %s netlist blocks/%s does not exist; using the %s netlist' % (k, netlist, rel, other))
            rel = None
        used = netlist if rel else other
        rel = rel or views[other]
        paths[k] = rel
        full = os.path.join(BLOCKS, rel)
        if rel in BLOCKSET_SHA256 and sha256(full) != BLOCKSET_SHA256[rel]:
            raise SystemExit('netlist blocks/%s does not match its bound SHA256 %s' % (rel, BLOCKSET_SHA256[rel]))
        name, ports = BLOCK_PORTS[k]
        found = subckt_ports(full, name)
        if found != ports:
            raise SystemExit('blocks/%s: .subckt %s ports %r differ from the deck instance %r' % (rel, name, found, ports))
        if k == 'sense':
            style = 'hier' if used == 'sch' else ('flat' if blockset == 'legacy' else 'exposed')
    if blockset == 'c1414':
        if paths['bgr'].endswith('baseline_586.spice'):
            warnings.append('NOTE bgr: BGR586 source carries 329 historical Sep-19 kpex capacitors, not an extraction of the BGR586 layout')
        else:
            warnings.append('NOTE bgr: BGR586 kpex 2.5D CC extraction of bank.gds (chip BGR layout), 978 capacitors')
        if style == 'exposed':
            warnings.append('NOTE sense: R100 own-native partial-field C (unbound VSUBS excluded; physical field acceptance not established)')
        if paths['trip'].endswith('/trip.spice'):
            warnings.append('NOTE trip: NF4 schematic netlist (no parasitics)')
    return paths, warnings, style


CORNERS = {
    'tt': dict(mos='mos_tt', res='res_typ', cap='cap_typ', hbt='hbt_typ'),
    'ss': dict(mos='mos_ss', res='res_wcs', cap='cap_wcs', hbt='hbt_wcs'),
    'ff': dict(mos='mos_ff', res='res_bcs', cap='cap_bcs', hbt='hbt_bcs'),
}
# --rtl-dir: which copy of the digital macro RTL the co-simulation compiles. 'rtl' is the chip of record
# (default); 'eco_20260925' is the pin-compatible RTL-only ECO (blocks/g1_ctrl/ECO_20260925.md).
RTL_DIRS = {'rtl': ('g1_ctrl/rtl', 'g1_seu/rtl'),
            'eco_20260925': ('g1_ctrl/rtl_eco_20260925', 'g1_seu/rtl_eco_20260925')}


def make_rtl_files(rtl_dir='rtl'):
    ctrl, seu = RTL_DIRS[rtl_dir]
    return [os.path.join(HERE, 'rtl/g1_dig_cosim.v')] + [
        os.path.join(BLOCKS, ctrl, f) for f in
        ('g1_sync2.v', 'g1_serial.v', 'g1_trip_timer.v', 'g1_regfile.v', 'g1_digital_top.v', 'g1_digital.v')] + [
        os.path.join(BLOCKS, seu, f) for f in ('g1_tmr_reg.v', 'g1_seu_chain.v', 'g1_seu.v')]


RTL_FILES = make_rtl_files('rtl')

# ---------------------------------------------------------------- common timeline (us) and constants
INOM = 1.0          # nominal load current, A (25 mV across the 25 mOhm shunt = DAC code 128)
T_OSC = 0.1         # oscillator enable released (testbench gate on the RTL's osc_en, which is 1 from reset)
T_EN = 3.0          # EN pad rises
T_SER = 18.0        # first serial frame (>= 128 osc_clk after EN: 12.8 us nominal, 14.2 us at -20 %)
F_SCLK = 4.0e6      # serial clock, Hz (rule: f_SCLK <= f_OSC)
T_STEP = 30.0       # load event
CVREF = 10e-9       # board capacitor on the VREF pin (README, 'Numerical notes' and 'Board assumptions')
TMAX = 5e-9         # maximum analog time step: the transistor-level oscillator frequency is step-size
                    # dependent above this (README, "Numerical notes")
# behavioural front end (--front beh): parameters taken from the block results, see README
BEH = {
    'sch': dict(vref=1.0399, vped=0.9992, gain=19.99, f3db=4.19e6, fosc=9.919e6),
    'pex': dict(vref=1.0400, vped=0.9992, gain=19.99, f3db=4.19e6, fosc=8.994e6),
}
# c1414: legacy front-end fit retained; clock = R0.95 CPEX, full clock-tree load, nominal, trim code 8 (reset)
BEH['c1414_sch'] = dict(BEH['sch'], fosc=9.436194721e6)
BEH['c1414_pex'] = dict(BEH['pex'], fosc=9.436194721e6)


def frame_bits(addr, data):
    """Command bit7 selects read: 24 clocks (turnaround/data), or16 for write."""
    if not 0<=addr<=255 or not 0<=data<=255:raise ValueError('serial command/data outside byte range')
    command=[(addr >> (7-i)) & 1 for i in range(8)]
    return command + ([0]*16 if addr&0x80 else [(data >> (7-i)) & 1 for i in range(8)])


# Digital pad inputs (EN, SCLK, SDI) are 3.3 V PWL sources with 2 ns edges. The RTL reads them through
# ideal 1.2 V copies whose PWL corners sit just outside the adc_bridge band (0.55 / 0.65 V), so that the
# bridge changes state at an existing analog time point without passing through the unknown state
# (README, "Numerical notes").
BR_LO, BR_HI = 0.55, 0.65
# --vdd / --vdda (main sets these; defaults leave every deck byte-identical). VDDA and IOVDD share the board rail.
VDD_V, VDDA_V = 1.2, 3.3
TEDGE = 2e-9        # edge time of the EN / SCLK / SDI board signals


def edge(t, v0, v1, vio, tedge=None):
    tedge = TEDGE if tedge is None else tedge
    """PWL points of one edge from v0 to v1 (0 or vio) starting at t, with corners at the two bridge
    thresholds scaled to the pad level."""
    # corners 10 mV outside the bridge band, so that the bridge sees a defined 0 at one analog point and a
    # defined 1 at the next (no unknown state, which the RTL would count as a second clock edge)
    lo, hi = (BR_LO - 0.01) * vio / VDD_V, (BR_HI + 0.01) * vio / VDD_V
    if v1 > v0:
        return [(t, 0.0), (t + 0.45 * tedge, lo), (t + 0.55 * tedge, hi), (t + tedge, vio)]
    return [(t, vio), (t + 0.45 * tedge, hi), (t + 0.55 * tedge, lo), (t + tedge, 0.0)]


def serial_pwl(frames, t0_us, fsclk, vio, tedge=None):
    tedge = TEDGE if tedge is None else tedge
    """PWL points (s, V) for SCLK and SDI: SPI mode 0, SDI set at the start of each bit period, SCLK
    high in its second half (SDI sampled on the rising edge); frames back to back."""
    T = 1.0 / fsclk
    t = t0_us * 1e-6
    sclk = [(0.0, 0.0), (t, 0.0)]
    sdi = [(0.0, 0.0), (t, 0.0)]
    sdi_lvl = 0
    for addr, data in frames:
        for b in frame_bits(addr, data):
            if b != sdi_lvl:
                sdi += edge(t, vio * sdi_lvl, vio * b, vio, tedge)
                sdi_lvl = b
            sclk.append((t + T / 2, 0.0))
            sclk += edge(t + T / 2, 0.0, vio, vio, tedge)
            sclk += edge(t + T, vio, 0.0, vio, tedge)
            t += T
    if sdi_lvl:
        sdi += edge(t, vio, 0.0, vio, tedge)
    dedup = lambda pts: [p for i, p in enumerate(pts) if i == 0 or p != pts[i - 1]]
    return dedup(sclk), dedup(sdi), t * 1e6   # end time (us); exact repeated points removed


def digital_events(pts, vio):
    """(time, state) list of a PWL: an event at the time the ramp crosses vio/2."""
    ev = []
    for (t0, v0), (t1, v1) in zip(pts, pts[1:]):
        if (v0 < vio / 2) != (v1 < vio / 2) and v1 != v0:
            ev.append((t0 + (vio / 2 - v0) / (v1 - v0) * (t1 - t0), 1 if v1 > v0 else 0))
    return ev


def write_stim(path, en_pts, sclk_pts, sdi_pts, vio):
    """XSPICE d_source stimulus file: columns d_en d_sclk d_sdi, one line per event time (strong 0/1)."""
    ev = {}
    for col, pts in enumerate((en_pts, sclk_pts, sdi_pts)):
        for t, st in digital_events(pts, vio):
            ev.setdefault(round(t, 15), [None, None, None])[col] = st
    state = [0, 0, 0]
    lines = ['* d_en d_sclk d_sdi (generated by run_top.py)', '0.0 0s 0s 0s']
    for t in sorted(ev):
        for i in range(3):
            if ev[t][i] is not None:
                state[i] = ev[t][i]
        lines.append('%.12g %s' % (t, ' '.join('%ds' % x for x in state)))
    with open(path, 'w') as f:
        f.write('\n'.join(lines) + '\n')


def pwl(points):
    return 'pwl(' + ' '.join('%.12g %.9g' % (t, v) for t, v in points) + ')'


def step_profile(mult, t_rise_ns, t_back_us=None, t_fall_ns=None):
    """INOM from t = 0; step to mult*INOM at T_STEP with the given rise time; optionally back to INOM."""
    pts = [(0, INOM), (T_STEP * 1e-6, INOM), (T_STEP * 1e-6 + t_rise_ns * 1e-9, mult * INOM)]
    if t_back_us is not None:
        tf = (t_fall_ns if t_fall_ns is not None else t_rise_ns) * 1e-9
        pts += [(t_back_us * 1e-6, mult * INOM), (t_back_us * 1e-6 + tf, INOM)]
    return pts


def burst_profile(mult, t_on_us, t_off_us, n, t_edge_ns):
    pts = [(0, INOM)]
    t = T_STEP * 1e-6
    te = t_edge_ns * 1e-9
    for _ in range(n):
        pts += [(t, INOM), (t + te, mult * INOM), (t + t_on_us * 1e-6, mult * INOM), (t + t_on_us * 1e-6 + te, INOM)]
        t += (t_on_us + t_off_us) * 1e-6
    return pts


# ---------------------------------------------------------------- case library
INRUSH0 = (0x08, 0x00)      # INRUSH = 0: no inrush mask (the host's first action after EN)
SOFT_SHORT = (0x04, 0x01)   # SOFT_TIME_L = 0x01: window 256 osc_clk (~25.6 us) for the transistor-level soft-path cases


def make_cases():
    C = {}
    C['q'] = dict(desc='quiescent: nominal load, armed, no event; supply currents averaged over 32-44 us',
                  load=step_profile(1.0, 20), tstop=44, frames=[INRUSH0], expect='no trip', quiet=(32, 44))
    C['c'] = dict(desc='(c) fast step to 3x nominal (20 ns rise): hard trip through the digital path, HARD_N = 4',
                  load=step_profile(3.0, 20), tstop=36, frames=[INRUSH0], expect='hard trip')
    C['c_mid'] = dict(desc='in-range hard trip: code 200 (~39.25mV), 1.8A/45mV fault in 20ns; HARD_N=4',
                      load=step_profile(1.8, 20), tstop=42,
                      frames=[INRUSH0, (0x03, 200)], expect='hard trip')
    C['c_fast'] = dict(desc='(c-fast) as (c) with MODE.FAST_EN = 1 written over the serial interface (0x0B = 0x23): analog fast path cmp_hard -> G1_GATE latch',
                       load=step_profile(3.0, 20), tstop=36, frames=[INRUSH0, (0x0B, 0x23)], expect='hard trip')
    C['e'] = dict(desc='(e) latch-up signature: step to 4x nominal with 100 ns rise: hard trip',
                  load=step_profile(4.0, 100), tstop=36, frames=[INRUSH0], expect='hard trip')
    C['e20'] = dict(desc='(e-20ns) latch-up signature with a 20 ns rise: step to 4x nominal in 20 ns: hard trip (the 100 ns-rise variant stalls the solver, README)',
                    load=step_profile(4.0, 20), tstop=36, frames=[INRUSH0], expect='hard trip')
    C['f'] = dict(desc='(f) hard trip on a 3x step (load profile back to 1x at 36 us), EN low 40-42 us: GATE re-arms, load current resumes',
                  load=step_profile(3.0, 20, t_back_us=36), tstop=50, frames=[INRUSH0],
                  en=[(T_EN, 1), (40.0, 0), (42.0, 1)], expect='hard trip, then re-arm')
    C['f_mid'] = dict(desc='in-range hard trip at45mV, load returns36us, EN low40-42us clears both latches and restores nominal load',
                     load=step_profile(1.8, 20, t_back_us=36), tstop=50,
                     frames=[INRUSH0, (0x03, 200)], en=[(T_EN, 1), (40.0, 0), (42.0, 1)],
                     expect='hard trip, then re-arm')
    C['hard_pulse'] = dict(desc='in-range45mV pulse200ns shorter than four hard decisions; no trip with FAST_EN=0',
                          load=step_profile(1.8, 20, t_back_us=T_STEP+.2), tstop=44,
                          frames=[INRUSH0, (0x03, 200)], expect='no trip')
    C['hard_pulse400'] = dict(desc='distinct in-range45mV pulse400ns; exercises sampled comparator across phases but shorter than four cmp_clk decisions; FAST_EN=0',
                             load=step_profile(1.8, 20, t_back_us=T_STEP+.4), tstop=44,
                             frames=[INRUSH0, (0x03, 200)], expect='no trip')
    C['inrush_pulse'] = dict(desc='in-range45mV pulse30-35us while INRUSH=1 (512cycles) masks digital decisions; FAST_EN=0',
                            load=step_profile(1.8, 20, t_back_us=35), tstop=68,
                            frames=[(0x08, 1), (0x03, 200)], expect='no trip')
    C['clear_read'] = dict(desc='in-range45mV hard trip, load returns35us; serial STATUS/TRIP_CNT readback, CLEAR command, repeat readback and re-arm',
                          load=step_profile(1.8, 20, t_back_us=35), tstop=72,
                          frames=[INRUSH0,(0x03,200)], expect='hard trip, then serial clear',
                          late_frames=(36,[(0x8D,0),(0x8F,0),(0x90,0),(0x0C,1),(0x8D,0),(0x8F,0)]))
    C['retry_read'] = dict(desc='held45mV fault40us, HOLD_TIME=0 means8192cycles, one automaticretry then giveup; serialSTATUS/STATUS2/TRIP_CNT',
                          load=[(0,1),(40e-6,1),(40.02e-6,1.8)], event_us=40,tstop=1140,tstep=100e-9,
                          frames=[INRUSH0,(0x03,200),(0x0B,7),(0x09,0),(0x0A,1)],
                          expect='hard trip, one retry, then latched giveup',front='beh',
                          late_frames=(1100,[(0x8D,0),(0x8E,0),(0x8F,0),(0x90,0)]))
    # long-window cases at the register default SOFT_TIME = 0x27 (~1 ms): behavioural front end (README)
    C['a'] = dict(desc='(a) step to 1.5x nominal for 100 us then back (1 us edges), SOFT_TIME default (~1 ms): must not trip',
                  load=step_profile(1.5, 1000, t_back_us=T_STEP + 100), tstop=250, frames=[INRUSH0], expect='no trip',
                  front='beh', tstep=100e-9)
    C['b'] = dict(desc='(b) step to 1.5x nominal held, SOFT_TIME default 0x27 = 9984 osc_clk: soft trip at about 1 ms',
                  load=step_profile(1.5, 1000), tstop=1250, frames=[INRUSH0], expect='soft trip ~1 ms',
                  front='beh', tstep=100e-9)
    C['d'] = dict(desc='(d) GPU-like load: 100 us bursts to 1.4x nominal at 50 % duty (1 us edges), 5 periods, SOFT_TIME default: no trip',
                  load=burst_profile(1.4, 100, 100, 5, 1000), tstop=1050, frames=[INRUSH0], expect='no trip',
                  front='beh', tstep=100e-9)
    # the same three at transistor level with the window shortened 39x (SOFT_TIME = 0x0001 = 256 osc_clk) and the
    # load timing scaled with it (2.5 us pulse / bursts against a ~25.6 us window: same 1:10 ratio)
    C['a_s'] = dict(desc='(a-tl) transistor level, SOFT_TIME = 0x0001 (256 osc_clk ~ 25.6 us): 1.5x for 2.5 us then back (100 ns edges): must not trip',
                    load=step_profile(1.5, 100, t_back_us=T_STEP + 2.5), tstop=48, frames=[INRUSH0, SOFT_SHORT], expect='no trip')
    C['b_s'] = dict(desc='(b-tl) transistor level, SOFT_TIME = 0x0001 (256 osc_clk ~ 25.6 us): 1.5x held: soft trip after 256 samples',
                    load=step_profile(1.5, 100), tstop=64, frames=[INRUSH0, SOFT_SHORT], expect='soft trip ~26 us')
    C['d_s'] = dict(desc='(d-tl) transistor level, SOFT_TIME = 0x0001: 1.4x bursts 2.5 us on / 2.5 us off (100 ns edges), 5 periods: no trip',
                    load=burst_profile(1.4, 2.5, 2.5, 5, 100), tstop=60, frames=[INRUSH0, SOFT_SHORT], expect='no trip')
    C['osc'] = dict(desc='(osc) transistor-level G1_OSC clocking the digital macro on the chip VDD, with G1_BGR and G1_SENSE (no G1_TRIP, no G1_GATE, no pad models); cmp_soft tied high so SOFT_PEAK counts once INRUSH = 0 is written',
                    load=step_profile(1.0, 20), tstop=36, frames=[INRUSH0], expect='no trip', notrip=True, osc='tl', quiet=(24, 36),
                    minimal=True, cmp_soft_high=True)
    for order in ('A', 'B'):
        for rpd in ('none', '10k'):
            if order == 'A':
                ramp33, ramp12 = (1.0, 3.0), (5.0, 7.0)
                d = '(g-A) power-up: IOVDD/VDDA ramp 1-3 us, VDD 5-7 us, EN low until 12 us'
            else:
                ramp33, ramp12 = (5.0, 7.0), (1.0, 3.0)
                d = '(g-B) power-up: VDD ramp 1-3 us, IOVDD/VDDA 5-7 us, EN low until 12 us'
            C['g%s%s' % (order, '' if rpd == 'none' else '_pd')] = dict(
                desc=d + ('; 10 kOhm external pull-down on GATE' if rpd == '10k' else '; GATE loaded by 5 nF + 10 Ohm only'),
                load=[(0, INOM)], tstop=16, frames=[], en=[(12.0, 1)], ramp33=ramp33, ramp12=ramp12,
                rpd=(10e3 if rpd == '10k' else None), expect='GATE high while VDD is absent (IO-cell property, R8)',
                powerup=True, tstep=20e-9, front='beh', inpads='model', tmax=20e-9)
    return C


CASES = make_cases()


def shift_fault_phase(case, name, shift_ns, timeline='baseline'):
    """Shift only an in-range held/short fault, preserving serial configuration."""
    if not math.isfinite(shift_ns) or not 0 <= shift_ns <= 500:
        raise ValueError('fault phase shift must be finite and within0..500ns')
    if shift_ns == 0:
        return dict(case)
    if name not in ('c_mid', 'hard_pulse', 'hard_pulse400') or timeline != 'baseline':
        raise ValueError('fault phase shift supports baseline c_mid/hard_pulse/hard_pulse400 only')
    result = dict(case)
    dt = shift_ns * 1e-9
    result['load'] = [(t + dt if t >= T_STEP * 1e-6 else t, v)
                      for t, v in case['load']]
    result['event_us'] = T_STEP + shift_ns / 1000
    # Preserve the integer-grid endpoint. ngspice linearize may extrapolate
    # beyond a fractional-grid stop, so only the fault itself changes phase.
    result['desc'] += '; fault phase shifted by%gns with serial preamble unchanged' % shift_ns
    return result


def scale_fault(case, mult):
    """--fault-mult: set the case's single fault level (every load point other than INOM) to mult x INOM;
    point times unchanged. Refused if the profile has no or more than one fault level."""
    if not math.isfinite(mult) or not 0 < mult <= 10:
        raise ValueError('--fault-mult must be finite, within 0..10')
    levels = sorted({v for t, v in case['load'] if v != INOM})
    if len(levels) != 1:
        raise ValueError('--fault-mult needs exactly one fault level in the load profile (found %r)' % levels)
    result = dict(case)
    result['load'] = [(t, mult * INOM if v != INOM else v) for t, v in case['load']]
    result['fault_mult'] = (levels[0] / INOM, mult)
    return result


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        h.update(f.read())
    return h.hexdigest()

def validate_exports(deck):
    """Reject missing explicitly saved voltage/current vectors before simulation."""
    saved=set();in_save=False
    for line in deck.splitlines():
        if line.startswith('.save '):
            saved.update(line.split()[1:]);in_save=True
        elif in_save and line.startswith('+ '):saved.update(line.split()[1:])
        else:in_save=False
    if 'all' in saved:return
    exported=set()
    for line in deck.splitlines():
        if line.startswith(('wrdata ','linearize ')):
            exported.update(re.findall(r'\b[vi]\([^()]+\)',line))
    missing=exported-saved
    if missing:raise ValueError('exported vectors absent from .save: '+', '.join(sorted(missing)))


def nodesets(style):
    """Operating-point help for the three G1_SENSE OTA loops (from blocks/g1_sense/sim/tb_sense.cir);
    style 'hier': xsense.xota.tail; 'flat' (legacy kpex netlist): xsense.xota_tail; 'exposed' (c1414 R100
    partial-C netlist, OTA internals brought out as ports): xsense.__pex_xota_tail."""
    fmt = {'hier': 'xsense.%s.%s', 'flat': 'xsense.%s_%s', 'exposed': 'xsense.__pex_%s_%s'}[style]
    ns = ['v(vref_buf)=1.04', 'v(vped)=1.0008', 'v(isense)=1.5', 'v(xsense.vp)=0.047', 'v(xsense.vn)=0.047', 'v(iptat)=0.76']
    for o in ('xota', 'xbuf', 'xref'):
        ns += ['v(%s)=2.51' % (fmt % (o, 'out1')), 'v(%s)=2.51' % (fmt % (o, 'mir')),
               'v(%s)=1.6' % (fmt % (o, 'tail')), 'v(%s)=0.2' % (fmt % (o, 'fn')), 'v(%s)=0.2' % (fmt % (o, 'fp'))]
    return '.nodeset ' + ' '.join(ns)


def osc_tl(A, supply_r=None, decap=None, rx='bridge'):
    """Transistor-level G1_OSC on the chip VDD. Diagnostic options (defaults leave the deck unchanged):
    supply_r/decap: explicit series R and local decoupling on the OSC supply pin (testbench elements);
    rx='schmitt': an analog receiver with +-50 mV hysteresis between osc_clk and the clock adc_bridge."""
    if supply_r or decap:
        A('* diagnostic testbench element: series R %s Ohm + local decap %s F on the OSC supply pin' % (supply_r or 0, decap or 0))
        A('Vm_osc vdd vdd_osc_m dc 0')
        A('Rosc_sup vdd_osc_m vdd_osc %g' % (supply_r or 1e-3))
        if decap:
            A('Cosc_sup vdd_osc 0 %g' % decap)
    else:
        A('Vm_osc vdd vdd_osc dc 0')
    A('XOSC osc_en_g trim0 trim1 trim2 trim3 osc_clk vdd_osc 0 g1_osc')
    A('Cw_clk osc_clk 0 100f')
    if rx == 'schmitt':
        A('* diagnostic clock receiver: behavioural comparator with +-50 mV hysteresis around 0.6 V, 10 ps output RC;')
        A('* the adc_bridge sees only its fast full-swing output (not a circuit element of G1)')
        A('Bosc_rx osc_rx_i 0 V = 0.6 + 0.6*tanh((v(osc_clk) - 0.6 + 0.1*(v(osc_rx) - 0.6)/1.2)/0.005)')
        A('Rosc_rx osc_rx_i osc_rx 1k')
        A('Cosc_rx osc_rx 0 10f')


NODCN_WARNING = ('WARNING deviation --inpads nodcn: SENSE_P/SENSE_N use g1_IOPadAnalog_nodcn, a deck-local copy of the PDK '
                 'sg13g2_IOPadAnalog without its dantenna-based parts (sg13g2_DCNDiode and the SecondaryProtection '
                 'dantenna D1); clamps, DCPDiode, SecondaryProtection 587 Ohm + dpantenna, ptap resistors and padres kept; '
                 'VREF pad and PDK file unchanged. Reason: the PDK darea diode model switches formula at -3nVt '
                 '(measured current step 1e-16->4e-11 A at 78 mV/27 C, 2e-14->2e-10 A at 93 mV/85 C, 1e-12->4e-10 A '
                 'at 104 mV/125 C), which stalls the transient; removed leakage < 1 nA per pad at 125 C behind the '
                 '1 Ohm Kelvin trace (README, Numerical notes).')


def pad_analog_nodcn():
    """Deck-local copy of sg13g2_IOPadAnalog (PDK sg13g2_io.spi) without the dantenna-based parts."""
    return ['* ---- deck-local pad copy for --inpads nodcn (PDK sg13g2_io.spi untouched)',
            '.subckt g1_IOPadAnalog_nodcn pad padres vdd vss iovdd iovss',
            'XI0 iovdd iovss pad sg13g2_Clamp_P20N0D',
            '* XI5 iovss pad iovdd sg13g2_DCNDiode   (removed: dantenna x2)',
            'XI2 pad iovdd iovss sg13g2_DCPDiode',
            '* XI3 padres iovss pad iovdd sg13g2_SecondaryProtection   (replaced below without its dantenna D1)',
            'XI3R pad padres sub! rppd R=586.899 l=2u w=1u',
            'XI3P iovss sub! ptap1 R=46.556',
            'XI3D padres iovdd dpantenna l=4.98u w=640n m=1',
            'XI4 iovss pad sg13g2_Clamp_N20N0D',
            'XR0 vss sub! ptap1 R=22.579',
            'XR1 iovss sub! ptap1 R=214.8m',
            '.ends']


PADS_NODCN = False    # --pads nodcn (set in main)
PADS_NODCN_WARNING = ('WARNING deviation --pads nodcn: every PDK pad instance of this deck (XP*: SENSE_P/N, VREF, and '
                      'EN/SCLK/SDI/GATE/FAULT_N where pad models are used) is replaced by a deck-local copy g1nd_<cell> of '
                      'the sg13g2_io.spi hierarchy with every dantenna instance removed (DCNDiode junctions, '
                      'SecondaryProtection D1, Clamp_N*/LevelDown gate antenna diodes); level shifters, drivers, clamps, '
                      'dpantenna diodes and ptap resistors are kept; PDK file unchanged. Reason: the PDK darea diode model '
                      'switches formula at -3nVt (current step 1e-16->4e-11 A at 78 mV/27 C, 1e-12->4e-10 A at 104 mV/125 C), '
                      'which stalls the transient; removed leakage < 1 nA per pad at 125 C.')


def nodcn_io_lib():
    """Deck-local copy of the PDK sg13g2_io.spi hierarchy, cells renamed g1nd_<cell>, all dantenna instances removed."""
    lines = open(IOSPI).read().splitlines()
    cells = {l.split()[1] for l in lines if l.lower().startswith('.subckt')}
    out = ['* ---- deck-local copy of %s for --pads nodcn: cells renamed g1nd_*, dantenna instances removed' % IOSPI]
    for l in lines:
        t = l.split()
        if not t or l.startswith('*'):
            continue
        if t[0].lower() == '.subckt':
            out.append(' '.join(['.subckt', 'g1nd_' + t[1]] + t[2:]))
        elif t[0][0] in 'Xx':
            refs = [i for i, w in enumerate(t) if '=' not in w]
            ref = refs[-1]
            if t[ref] == 'dantenna':
                out.append('* removed (--pads nodcn): ' + l)
                continue
            if t[ref] in cells:
                t[ref] = 'g1nd_' + t[ref]
            out.append(' '.join(t))
        else:
            out.append(l)
    return out


def build_deck(case, name, netlist, front, temp, corner, tag, tstop_override=None, osc='ideal', inpads='ideal', outpads='beh', method='gear',
               osc_rx='bridge', osc_supply_r=None, osc_decap=None, blockset='legacy', t2f='off', interconnect='estimate', sense_route_r=False):
    c = dict(case)
    event_us=c.get('event_us',T_STEP)
    tstop = tstop_override if tstop_override else c['tstop']
    tstep = c.get('tstep', 20e-9)
    powerup = c.get('powerup', False)
    en_tr = c.get('en', [(T_EN, 1)])
    K = CORNERS[corner]
    rel, bs_warnings, sense_style = resolve_netlists(blockset, netlist)
    nl = {k: os.path.join(BLOCKS, v) for k, v in rel.items()}
    vio = VDDA_V
    B = BEH[netlist if blockset == 'legacy' else '%s_%s' % (blockset, netlist)]
    # supplies: DC for functional cases (operating point start), PWL ramps for the power-up cases
    if powerup:
        r33, r12 = c['ramp33'], c['ramp12']
        v33 = pwl([(0, 0), (r33[0] * 1e-6, 0), (r33[1] * 1e-6, VDDA_V)])
        v12 = pwl([(0, 0), (r12[0] * 1e-6, 0), (r12[1] * 1e-6, VDD_V)])
    else:
        v33, v12 = 'dc %g' % VDDA_V, 'dc %g' % VDD_V
    # the board signals EN / SCLK / SDI are placed mid-way between two rising edges of the (ideal) RTL clock
    # and SCLK runs at f_osc / 2, so that their edges never fall into the fine-step window that follows every
    # clock edge (README, "Numerical notes"); f_SCLK <= f_OSC as the register map requires
    tper = 1.0 / B['fosc']
    grid = lambda t_us: (T_OSC * 1e-6 + (round((t_us * 1e-6 - T_OSC * 1e-6) / tper)) * tper + 0.5 * tper) * 1e6
    fsclk = 0.5 / tper if osc != 'tl' else F_SCLK
    if osc != 'tl':
        en_tr = [(grid(t), lv) for t, lv in en_tr]
        t_ser = grid(T_SER)
    else:
        t_ser = T_SER
    if c['frames']:
        sclk_pts, sdi_pts, t_ser_end = serial_pwl(c['frames'], t_ser, fsclk, vio)
    else:
        sclk_pts, sdi_pts, t_ser_end = [(0, 0)], [(0, 0)], 0.0
    if c.get('late_frames'):
        late_start,late_frames=c['late_frames']
        late_start=grid(late_start) if osc!='tl' else late_start
        if late_start<=t_ser_end:raise ValueError('late serial sequence overlaps initial configuration')
        late_clk,late_data,_=serial_pwl(late_frames,late_start,fsclk,vio)
        sclk_pts+=late_clk[1:];sdi_pts+=late_data[1:]
    en_pts, lvl = [(0, 0)], 0
    for t, lv in en_tr:
        en_pts += edge(t * 1e-6, vio * lvl, vio * lv, vio)
        lvl = lv
    stim_path = os.path.join(BUILD, 'stim_%s.txt' % tag)
    write_stim(stim_path, en_pts, sclk_pts, sdi_pts, vio)
    t_cfg = t_ser_end + 1.0     # the register write lands a few osc_clk after the 16th edge
    quiet = c.get('quiet', (t_cfg + 2.0, event_us) if not powerup else None)
    t2f_on = t2f == 'tl'
    if t2f_on and (front != 'tl' or c.get('minimal') or powerup):
        raise SystemExit('--t2f tl needs the transistor-level front end and a functional (non-power-up, non-osc) case')
    vvp = rtl_vvp_path(tag)     # per-run compiled RTL (no race between concurrent launches)
    rpd = c.get('rpd')

    L = []
    A = L.append
    A('* G1_TOP breaker path, chip level: %s' % c['desc'])
    if c.get('fault_mult') and c['fault_mult'][0] != c['fault_mult'][1]:   # equal level: deck unchanged
        A('* --fault-mult %g: fault level %g x INOM replaced by %g x INOM (%g mV across RSH), timing unchanged' %
          (c['fault_mult'][1], c['fault_mult'][0], c['fault_mult'][1], c['fault_mult'][1] * INOM * 25))
    A('* case %s | block netlists %s | front end %s | clock to the RTL %s | corner %s (%s %s %s %s) | %g degC | run_top.py' %
      (name, netlist, front, osc, corner, K['mos'], K['res'], K['cap'], K['hbt'], temp))
    if blockset != 'legacy' or VIEW_OVERRIDE:
        A('* blockset %s (run_top.py BLOCKSETS)%s; ideal-clock frequency %.10g MHz' % (
          blockset, (' view override ' + ','.join('%s=%s' % kv for kv in sorted(VIEW_OVERRIDE.items()))) if VIEW_OVERRIDE else '', B['fosc'] / 1e6))
        for k in ('bgr', 'sense', 'trip', 'osc', 'gate'):
            A('* netlist %s: blocks/%s' % (k, rel[k]))
    for w in bs_warnings:
        A('* ' + w)
    if inpads == 'nodcn':
        A('* ' + NODCN_WARNING)
    if (VDD_V, VDDA_V) != (1.2, 3.3):
        A('* supplies --vdd %g V --vdda %g V (VDDA = IOVDD rail); bridge thresholds VDD/2, dac_bridge high = VDD,' % (VDD_V, VDDA_V))
        A('* EN/SCLK/SDI level copies pad x VDD/VDDA, GATE/FAULT_N drivers on IOVDD; measurement thresholds VDD/2')
    A('.param VDDA=%g VDD=%g IOVDD=%g RSH=25m RGND=10m INOM=%g CVREF=%g' % (VDDA_V, VDD_V, VDDA_V, INOM, CVREF))
    A('.lib %s/cornerMOSlv.lib %s' % (MODELS, K['mos']))
    A('.lib %s/cornerMOShv.lib %s' % (MODELS, K['mos']))
    A('.lib %s/cornerRES.lib %s' % (MODELS, K['res']))
    A('.lib %s/cornerCAP.lib %s' % (MODELS, K['cap']))
    A('.lib %s/cornerHBT.lib %s' % (MODELS, K['hbt']))
    A('.lib %s/cornerDIO.lib dio_tt' % MODELS)
    A('.include %s' % IOSPI)
    if PADS_NODCN:
        A('* ' + PADS_NODCN_WARNING)
        L.extend(nodcn_io_lib())
    if front == 'tl':
        for k in ('bgr', 'sense', 'trip', 'osc', 'gate'):
            if (k == 'trip' and c.get('notrip')) or (k == 'osc' and osc != 'tl'):
                continue
            A('.include %s' % nl[k])
    else:
        A('.include %s' % nl['gate'])
        if osc == 'tl':
            A('.include %s' % nl['osc'])
    if t2f_on:
        for k, v in resolve_t2f().items():
            A('.include %s' % os.path.join(BLOCKS, v))
    A('.temp %g' % temp)
    A('.global sub!')
    A('Vsub sub! 0 dc 0')
    A('* solver (README, "Numerical notes"): gear integration and loose absolute tolerances are what the PDK IO-pad')
    A('* models need when XSPICE events fall on their switching edges (with abstol 1e-9 / vntol 1e-5 the diode')
    A('* internal nodes stop converging: "timestep too small"); the DAC mux-tree nodes need rshunt; XSPICE forces')
    A('* trtol = 1, which the comparator decisions need at this reltol; default gmin (1e-13 stalls the pads)')
    # tolerances (README, "Numerical notes"): the transistor-level comparators need chgtol <= 1e-13 to resolve the
    # StrongARM regeneration; the behavioural front end runs with the loose set the pad models prefer
    tol_default = 'reltol=0.001 abstol=1e-10 vntol=1e-6 chgtol=1e-14' if front == 'tl' else 'reltol=0.002 abstol=1e-8 vntol=1e-4 chgtol=1e-12'
    A('.option method=%s itl4=100 %s rshunt=1e12' % (method, c.get('tol', tol_default)))
    if not powerup and front == 'tl':
        A(nodesets(sense_style))
    A('* ---- supplies: one 3.3 V board rail feeds VDDA (pin 7) and IOVDD (pin 3), PLAN D14; 1.2 V VDD (pin 1)')
    A('V33 rail33 0 %s' % v33)
    A('Vma rail33 vdda_s dc 0')
    A('Vmi rail33 iovdd_s dc 0')
    A('Rsa vdda_s vdda 0.5')
    A('Cda vdda 0 1n')
    A('Rsi iovdd_s iovdd 0.5')
    A('Cdi iovdd 0 1n')
    A('V12 vdd_s 0 %s' % v12)
    A('Rsd vdd_s vdd 0.5')
    A('Cdd vdd 0 1n')
    A('* ---- board: load current profile (1 V = 1 A) x switch on the FET gate node, shunt, Kelvin traces, FET gate')
    A('Vprof iprof 0 %s' % pwl(c['load']))
    A('Bload 0 ldi I = v(iprof) * (0.5 + 0.5*tanh((v(gfet) - 1.5)/0.15))')
    A('Vim ldi shp dc 0')
    A('Rsh shp shn {RSH}')
    A('Rgnd shn 0 {RGND}')
    A('Rkp shp sense_p 1')
    A('Rkn shn sense_n 1')
    A('Rg gate gfet 10')
    A('Cgate gfet 0 5n')
    if rpd:
        A('Rpd gate 0 %g' % rpd)
    A('Cfault fault_n 0 20p')
    minimal = c.get('minimal', False)
    if not minimal:
        A('* ---- pads (PDK sg13g2_io SPICE models): SENSE_P/N on the bare pad terminal, VREF on the padres terminal')
        A('* (587 Ohm secondary protection, padframe/README.md); the VREF bond pad carries the board capacitor CVREF')
        if inpads == 'nodcn':
            L.extend(pad_analog_nodcn())
            A('XPSP sense_p sense_p_res vdd 0 iovdd 0 g1_IOPadAnalog_nodcn')
            A('XPSN sense_n sense_n_res vdd 0 iovdd 0 g1_IOPadAnalog_nodcn')
        else:
            A('XPSP sense_p sense_p_res vdd 0 iovdd 0 sg13g2_IOPadAnalog')
            A('XPSN sense_n sense_n_res vdd 0 iovdd 0 sg13g2_IOPadAnalog')
        A('XPVREF vref_pad vref vdd 0 iovdd 0 sg13g2_IOPadAnalog')
        A('Cvref_ext vref_pad 0 {CVREF}')
        if inpads == 'model':
            A('XPEN en_pad en_core vdd 0 iovdd 0 sg13g2_IOPadIn')
            A('XPSCLK sclk_pad sclk_core vdd 0 iovdd 0 sg13g2_IOPadIn')
            A('XPSDI sdi_pad sdi_core vdd 0 iovdd 0 sg13g2_IOPadIn')
        else:
            A('* digital input pads (EN, SCLK, SDI) as ideal 3.3 V -> 1.2 V level copies: the sg13g2_IOPadIn SPICE')
            A('* models abort the event-driven solver at their input edges with the charge tolerance the comparators')
            A('* need (README, "Numerical notes"); the pads are functionally verified in blocks/g1_gate (EN pad)')
            A('Ben_core en_core 0 V = v(en_pad)*%g/%g' % (VDD_V, VDDA_V))
            A('Bsclk_core sclk_core 0 V = v(sclk_pad)*%g/%g' % (VDD_V, VDDA_V))
            A('Bsdi_core sdi_core 0 V = v(sdi_pad)*%g/%g' % (VDD_V, VDDA_V))
        if outpads == 'model':
            A('XPG gate gate_core vdd 0 iovdd 0 sg13g2_IOPadOut30mA')
            A('XPF fault_n fault_core vdd 0 iovdd 0 sg13g2_IOPadOut4mA')
        else:
            A('* GATE / FAULT_N output pads as behavioural drivers fitted to the g1_gate block results with the PDK pad')
            A('* models (30 mA pad: 5 nF + 10 Ohm, fall 90-10 % 606 ns, arming 0-90 % 677 ns -> 47 Ohm driver; 4 mA pad:')
            A('* 20 pF, ~500 Ohm). Reason: README, "Numerical notes" (pad models and the StrongARM comparators need')
            A('* incompatible integration settings). The driver switches within 1 ns of gate_core / fault_core and')
            A('* draws its current from IOVDD.')
            A('Bgate_drv gate_drv 0 V = v(iovdd)*(0.5 + 0.5*tanh((v(gate_core) - %g)/0.05))' % (VDD_V / 2))
            A('Rgate_drv gate_drv gate 47')
            A('Bgate_i iovdd 0 I = max(0, (v(gate_drv) - v(gate))/47)')
            A('Bfault_drv fault_drv 0 V = v(iovdd)*(0.5 + 0.5*tanh((v(fault_core) - %g)/0.05))' % (VDD_V / 2))
            A('Rfault_drv fault_drv fault_n 500')
    else:
        A('* ---- minimal chip context (README, case osc): no pad models, no G1_GATE; the 3.3 V pad inputs are scaled to 1.2 V')
        A('Cvref_ext vref 0 1p')
        A('Ben_core en_core 0 V = v(en_pad)*%g/%g' % (VDD_V, VDDA_V))
        A('Bsclk_core sclk_core 0 V = v(sclk_pad)*%g/%g' % (VDD_V, VDDA_V))
        A('Bsdi_core sdi_core 0 V = v(sdi_pad)*%g/%g' % (VDD_V, VDDA_V))
        A('Bgate gate 0 V = %g*(0.5 + 0.5*tanh((v(en_core) - %g)/0.05))' % (VDDA_V, VDD_V / 2))
        A('Vfault fault_n 0 dc %g' % VDDA_V)
        A('Vgc gate_core 0 dc 0')
        A('Vtr tripped 0 dc 0')
    A('Ven en_pad 0 %s' % pwl(en_pts))
    A('Vsclk sclk_pad 0 %s' % pwl(sclk_pts))
    A('Vsdi sdi_pad 0 %s' % pwl(sdi_pts))
    A('Cw_en en_core 0 20f')
    A('Cw_sclk sclk_core 0 20f')
    A('Cw_sdi sdi_core 0 20f')
    A('* the RTL reads EN / SCLK / SDI as a digital stimulus (XSPICE d_source) with the same edge times as the pad')
    A('* PWLs (event at the middle of each edge); the pad models still drive en_core for G1_GATE (README, "Numerical notes")')
    A('.model dsrc d_source(input_file="%s")' % stim_path)
    A('adsrc [d_en d_sclk d_sdi] dsrc')
    # oscillator enable: the RTL drives osc_en = 1 from reset; the testbench holds it low for T_OSC so the
    # relaxation oscillator starts from a defined state (as in blocks/g1_osc/sim/tb_osc.cir)
    A('* ---- oscillator enable gate (testbench): RTL osc_en, released at %g us' % T_OSC)
    A('Bosc osc_en_g 0 V = v(osc_en) * min(1, max(0, (time - %gu) / 50n))' % T_OSC)
    if front == 'tl':
        A('* ---- analog chain at transistor level (per-block supply pins through 0 V sources for the current table)')
        A('Vr4 r4 0 dc 0')
        A('Vm_bgr vdda vdda_bgr dc 0')
        A('XBGR vdda_bgr 0 r4 vref iptat pbias pcasc vbe dvbe g1_bgr')
        A('Vm_sense vdda vdda_sense dc 0')
        A('XSENSE sense_p sense_n vref iptat isense vped vref_buf vdda_sense 0 g1_sense')
        A('Cw_isense isense 0 300f')
        A('Vm_tripa vdda vdda_trip dc 0')
        A('Vm_tripd vdd vdd_trip dc 0')
        if not c.get('notrip'):
            A('XTRIP isense vref_buf cmp_clk soft0 soft1 soft2 soft3 soft4 soft5 soft6 soft7 hard0 hard1 hard2 hard3 hard4 hard5 hard6 hard7 cmp_soft cmp_hard vdd_trip vdda_trip 0 g1_trip')
            icmp, vths, vthh = 'v(xtrip.icmp)', 'v(xtrip.vth_soft)', 'v(xtrip.vth_hard)'
        else:
            A('* this case has no G1_TRIP (README): comparator outputs tied low, its supply pins left open')
            A('Vcs_tie cmp_soft 0 dc %g' % (VDD_V if c.get('cmp_soft_high') else 0.0))
            A('Vch_tie cmp_hard 0 dc 0')
            A('Rtripa_dummy vdda_trip 0 1e12')
            A('Rtripd_dummy vdd_trip 0 1e12')
            A('Bicmp icmp 0 V = v(isense)/2')
            A('Vvths vth_soft 0 dc %g' % (B['vref'] * (255 + 153) / 530.0))
            A('Vvthh vth_hard 0 dc %g' % (B['vref'] * (255 + 254) / 530.0))
            icmp, vths, vthh = 'v(icmp)', 'v(vth_soft)', 'v(vth_hard)'
        A('Cw_soft cmp_soft 0 20f')
        A('Cw_hard cmp_hard 0 20f')
        if osc == 'tl':
            osc_tl(A, osc_supply_r, osc_decap, osc_rx)
        else:
            A('* the clock delivered to the digital macro is an ideal source at the block-simulated G1_OSC frequency;')
            A('* G1_OSC is not in this deck (README, "Numerical notes": with the transistor-level oscillator on the')
            A('* chip supply the event-driven solver aborts; case osc runs it in the chip context without G1_TRIP)')
            A('Vm_osc vdd vdd_osc dc 0')
            A('Rosc_dummy vdd_osc 0 1e12')
            A('Vosc_i osc_i 0 pulse(0 %g %g 1n 1n %g %g)' % (VDD_V, T_OSC * 1e-6, 0.5 / B['fosc'] - 1e-9, 1.0 / B['fosc']))
            A('Bosc_clk osc_clk 0 V = v(osc_i) * (0.5 + 0.5*tanh((v(osc_en_g) - %g)/0.05))' % (VDD_V / 2))
            A('Cw_clk osc_clk 0 100f')

    else:
        A('* ---- behavioural front end (README "Behavioural front end"): parameters from the %s block results' % netlist)
        A('* VREF and the bandgap: fixed %g V (the VREF pad model stays connected)' % B['vref'])
        A('Vvref vref 0 dc %g' % B['vref'])
        A('Vm_bgr vdda vdda_bgr dc 0')
        A('Rbgr_dummy vdda_bgr 0 1e12')
        A('* G1_SENSE: ISENSE = VPED + GAIN x (SENSE_P - SENSE_N), single pole at the simulated -3 dB bandwidth')
        A('Bis isense_b 0 V = %g + %g*(v(sense_p) - v(sense_n))' % (B['vped'], B['gain']))
        A('Ris isense_b isense 1k')
        A('Cis isense 0 %g' % (1.0 / (2 * 3.141592653589793 * B['f3db'] * 1e3)))
        A('Vm_sense vdda vdda_sense dc 0')
        A('Rsense_dummy vdda_sense 0 1e12')
        A('* G1_TRIP: conditioning divider (25 kOhm source, 1 pF hold), DAC taps VREF x (255 + code)/530, ideal clocked comparators')
        A('Bic icmp_b 0 V = v(isense)/2')
        A('Ric icmp_b icmp 25k')
        A('Cic icmp 0 1p')
        A('Bvths vth_soft 0 V = %g*(255 + v(cs))/530' % B['vref'])
        A('Bvthh vth_hard 0 V = %g*(255 + v(ch))/530' % B['vref'])
        A('Bcs cs 0 V = ' + ' + '.join('%d*(0.5 + 0.5*tanh((v(soft%d) - %g)/0.05))' % (1 << i, i, VDD_V / 2) for i in range(8)))
        A('Bch ch 0 V = ' + ' + '.join('%d*(0.5 + 0.5*tanh((v(hard%d) - %g)/0.05))' % (1 << i, i, VDD_V / 2) for i in range(8)))
        A('* comparator decisions as smooth (2 mV wide) functions of the input difference, sampled by ideal flip-flops')
        A('Bcmps cmps_a 0 V = %g + %g*tanh((v(icmp) - v(vth_soft))/2m)' % (VDD_V / 2, VDD_V / 2))
        A('Bcmph cmph_a 0 V = %g + %g*tanh((v(icmp) - v(vth_hard))/2m)' % (VDD_V / 2, VDD_V / 2))
        A('.model dffm d_dff(clk_delay=1n set_delay=1n reset_delay=1n ic=0 rise_delay=0.5n fall_delay=0.5n)')
        A('.model dinv d_inverter(rise_delay=0.2n fall_delay=0.2n)')
        A('Vzero zero_a 0 dc 0')
        A('acmpa [cmps_a cmph_a zero_a] [d_cmps_a d_cmph_a d_zero] adc')
        A('acinv d_cmp_clk d_cmp_clk_n dinv')
        A('* d_dff ports: data clk set reset out nout (set/reset tied to a digital 0: a null port reads as unknown)')
        A('acs d_cmps_a d_cmp_clk d_zero d_zero d_cmps_q null dffm')
        A('ach d_cmph_a d_cmp_clk_n d_zero d_zero d_cmph_q null dffm')
        A('acmpd [d_cmps_q d_cmph_q] [cmp_soft cmp_hard] dac')
        A('Vm_tripa vdda vdda_trip dc 0')
        A('Vm_tripd vdd vdd_trip dc 0')
        A('Rtripa_dummy vdda_trip 0 1e12')
        A('Rtripd_dummy vdd_trip 0 1e12')
        if osc == 'tl':
            A('* G1_OSC at transistor level on the chip VDD (diagnostic: --front beh --osc tl)')
            osc_tl(A, osc_supply_r, osc_decap, osc_rx)
        else:
            A('* G1_OSC: ideal square wave at the block-simulated frequency, gated by the enable')
            A('Vosc_i osc_i 0 pulse(0 %g %g 1n 1n %g %g)' % (VDD_V, T_OSC * 1e-6, 0.5 / B['fosc'] - 1e-9, 1.0 / B['fosc']))
            A('Bosc_clk osc_clk 0 V = v(osc_i) * (0.5 + 0.5*tanh((v(osc_en_g) - %g)/0.05))' % (VDD_V / 2))
            A('Vm_osc vdd vdd_osc dc 0')
            A('Rosc_dummy vdd_osc 0 1e12')
        icmp, vths, vthh = 'v(icmp)', 'v(vth_soft)', 'v(vth_hard)'
    if t2f_on:
        A('* ---- G1_T2F at transistor level (--t2f tl), wired as g1_chip_top_1414.cdl: pbias/pcasc/vref from G1_BGR,')
        A('* en/mode from the RTL t2f_en/t2f_mode (reset 1/0) through g1_ls_up, vdd12 = VDD; fout into 1 pF.')
        A('* The TEMP_OUT pad (sg13g2_IOPadOut16mA) is out of scope: fout sees a 1 pF lumped load only.')
        A('Vm_t2f vdda vdda_t2f dc 0')
        A('Vm_t2fd vdd vdd_t2f dc 0')
        A('Vm_ls vdda vdda_ls dc 0')
        A('Vm_lsd vdd vdd_ls dc 0')
        A('XLSEN t2f_en12 t2f_en33 vdd_ls vdda_ls 0 g1_ls_up')
        A('XLSMODE t2f_mode12 t2f_mode33 vdd_ls vdda_ls 0 g1_ls_up')
        A('XT2F vdda_t2f vdd_t2f 0 pbias pcasc vref t2f_en33 t2f_mode33 temp_out g1_t2f')
        A('Ctemp_out temp_out 0 1p')
    A('Vm_gatea vdda vdda_gate dc 0')
    A('Vm_gated vdd vdd_gate dc 0')
    if not minimal:
        A('XGATE trip_d clr_d fast_en cmp_hard en_core gate_core fault_core tripped vdd_gate vdda_gate 0 g1_gate')
        A('Cw_tripped tripped 0 20f')
    else:
        A('Rgatea_dummy vdda_gate 0 1e12')
        A('Rgated_dummy vdd_gate 0 1e12')
    A('* ---- digital macro: the real RTL through XSPICE d_cosim (Icarus Verilog shim ivlng)')
    A('.model adc adc_bridge(in_low=%g in_high=%g rise_delay=1e-12 fall_delay=1e-12)' % (BR_LO, BR_HI))
    # A band on a clock produces 0 -> U -> 1. Icarus treats both changes as
    # posedges, so the divider can count twice. Use one receiver threshold
    # for the clock only; retain unknown-state handling on the data inputs.
    A('.model adc_clock adc_bridge(in_low=%g in_high=%g rise_delay=1e-12 fall_delay=1e-12)' % (VDD_V / 2, VDD_V / 2))
    A('.model dac dac_bridge(out_low=0 out_high=%g out_undef=%g t_rise=0.3n t_fall=0.3n)' % (VDD_V, VDD_V / 2))
    A('.model rtl d_cosim simulation="ivlng" sim_args=["%s"]' % vvp)
    if osc == 'tl' and osc_rx == 'schmitt':
        A('aclock [osc_rx] [d_osc_clk] adc_clock')
    else:
        A('aclock [osc_clk] [d_osc_clk] adc_clock')
    A('aadc [cmp_soft cmp_hard tripped] [d_cmp_soft d_cmp_hard d_tripped] adc')
    outs = (['d_cmp_clk'] + ['d_s%d' % i for i in range(7, -1, -1)] + ['d_h%d' % i for i in range(7, -1, -1)] +
            ['d_trip_d', 'd_clr_d', 'd_fast_en', 'd_osc_en'] + ['d_t%d' % i for i in range(3, -1, -1)] +
            ['d_trip', 'd_gate_en', 'd_cause1', 'd_cause0', 'd_sdo'] + ['d_sp%d' % i for i in range(15, -1, -1)] + ['d_inrush', 'd_softarmed'] +
            (['d_t2f_en', 'd_t2f_mode'] if t2f_on else []))
    if t2f_on:
        A('* d_cosim wrapper: rtl/g1_dig_cosim_t2f.v (g1_dig_cosim.v plus outputs t2f_en, t2f_mode)')
    A('adig [d_osc_clk d_en d_sclk d_sdi d_cmp_soft d_cmp_hard d_tripped] [%s] rtl' % ' '.join(outs))
    an = (['cmp_clk'] + ['soft%d' % i for i in range(7, -1, -1)] + ['hard%d' % i for i in range(7, -1, -1)] +
          ['trip_d', 'clr_d', 'fast_en', 'osc_en'] + ['trim%d' % i for i in range(3, -1, -1)] +
          ['dig_trip', 'dig_gate_en', 'cause1', 'cause0', 'sdo'] + ['sp%d' % i for i in range(15, -1, -1)] + ['inrush_active', 'soft_armed'] +
          (['t2f_en12', 't2f_mode12'] if t2f_on else []))
    A('adac [%s] [%s] dac' % (' '.join(outs), ' '.join(an)))
    A('.save v(gate) v(gfet) v(tripped) v(isense) v(cmp_soft) v(cmp_hard) v(trip_d) v(clr_d) v(fast_en) v(osc_clk) v(cmp_clk)')
    A('+ v(vref) v(iptat) v(en_core) v(shp) v(shn) v(fault_n) v(gate_core) v(vdda) v(vdd) v(iovdd) v(iprof) v(osc_en_g)')
    A('+ %s %s %s v(dig_trip) v(cause1) v(cause0) v(sclk_pad) v(sdi_pad) v(sdo)' % (icmp, vths, vthh))
    A('+ ' + ' '.join('v(soft%d)' % i for i in range(8)) + ' ' + ' '.join('v(hard%d)' % i for i in range(8)))
    A('+ ' + ' '.join('v(sp%d)' % i for i in range(16)) + ' v(inrush_active) v(soft_armed)')
    has_vm_osc = any(l.split()[:1] == ['Vm_osc'] for l in L)
    A('+ i(vim) i(vma) i(vmi) i(v12) i(vm_bgr) i(vm_sense) i(vm_tripa) i(vm_tripd)%s i(vm_gatea) i(vm_gated)' % (' i(vm_osc)' if has_vm_osc else ''))
    if t2f_on:
        A('+ v(temp_out) v(t2f_en33) v(t2f_mode33) v(pbias) v(pcasc) i(vm_t2f) i(vm_t2fd) i(vm_ls) i(vm_lsd)')
    if front == 'tl':
        A('+ v(vref_buf) v(vped)')
    # ---- control
    A('.control')
    A('set filetype=ascii')
    A('set wr_singlescale')
    A('set wr_vecnames')
    A('tran %g %gu 0 %g' % (tstep, tstop, c.get('tmax', TMAX)))
    bits = lambda prefix, n: ' + '.join('%d*(v(%s%d) gt 0.6)' % (1 << i, prefix, i) for i in range(n))
    if not powerup:
        tq = t_cfg + 1.0
        A('* quiet operating values after the register write(s): window averages over the last 2 us before the load')
        A('* event (comparator kickback averaged out); single-instant samples at t_cfg + 1 us kept as *_inst')
        tw0, tw1 = event_us - 2.0, min(event_us, tstop)
        A('meas tran vref_q avg v(vref) from=%gu to=%gu' % (tw0, tw1))
        A('meas tran isense_q avg v(isense) from=%gu to=%gu' % (tw0, tw1))
        A('meas tran icmp_q avg %s from=%gu to=%gu' % (icmp, tw0, tw1))
        A('meas tran vths_q avg %s from=%gu to=%gu' % (vths, tw0, tw1))
        A('meas tran vthh_q avg %s from=%gu to=%gu' % (vthh, tw0, tw1))
        A('meas tran vref_i find v(vref) at=%gu' % tq)
        A('meas tran isense_i find v(isense) at=%gu' % tq)
        A('meas tran icmp_i find %s at=%gu' % (icmp, tq))
        A('meas tran vths_i find %s at=%gu' % (vths, tq))
        A('meas tran vthh_i find %s at=%gu' % (vthh, tq))
        A('meas tran iload_q find i(vim) at=%gu' % tq)
        A('meas tran gate_q find v(gate) at=%gu' % tq)
        A('meas tran fastq find v(fast_en) at=%gu' % tq)
        A('meas tran t_inrush_off when v(inrush_active)=0.6 fall=1 from=%gu' % T_EN)
        A('meas tran inrush_q find v(inrush_active) at=%gu' % tq)
        A('meas tran softarmed_end find v(soft_armed) at=%gu' % tstop)
        A('let cs_v = ' + bits('soft', 8))
        A('let ch_v = ' + bits('hard', 8))
        A('meas tran code_soft find cs_v at=%gu' % tq)
        A('meas tran code_hard find ch_v at=%gu' % tq)
        A('let t_inrush_off_us = t_inrush_off*1e6')
        A('echo "QUIET window_us=%g-%g vref=" $&vref_q " isense=" $&isense_q " icmp=" $&icmp_q " vth_soft=" $&vths_q " vth_hard=" $&vthh_q " vref_inst=" $&vref_i " isense_inst=" $&isense_i " icmp_inst=" $&icmp_i " vth_soft_inst=" $&vths_i " vth_hard_inst=" $&vthh_i " iload_A=" $&iload_q " gate=" $&gate_q " code_soft=" $&code_soft " code_hard=" $&code_hard " fast_en=" $&fastq " inrush_active=" $&inrush_q " t_inrush_off_us=" $&t_inrush_off_us " soft_armed_end=" $&softarmed_end' % (tw0, tw1))
        A('* clocks: 20 oscillator periods and 10 strobe periods after the configuration')
        A('meas tran tosc1 when v(osc_clk)=0.6 rise=1 from=%gu' % t_cfg)
        A('meas tran tosc2 when v(osc_clk)=0.6 rise=21 from=%gu' % t_cfg)
        A('let fosc_mhz = 20e-6/(tosc2 - tosc1)')
        A('meas tran tcc1 when v(cmp_clk)=0.6 rise=1 from=%gu' % t_cfg)
        A('meas tran tcc2 when v(cmp_clk)=0.6 rise=11 from=%gu' % t_cfg)
        A('let fcmp_mhz = 10e-6/(tcc2 - tcc1)')
        A('echo "CLOCK f_osc_MHz=" $&fosc_mhz " f_cmp_MHz=" $&fcmp_mhz " (RTL clock: %s)"' % ('transistor-level G1_OSC' if osc == 'tl' else 'ideal source at the block-simulated frequency'))
        A('* supply currents averaged over the quiet armed window')
        for nm, src in (('vdda', 'vma'), ('iovdd', 'vmi'), ('vdd', 'v12'), ('bgr', 'vm_bgr'), ('sense', 'vm_sense'),
                        ('tripa', 'vm_tripa'), ('tripd', 'vm_tripd'), ('osc', 'vm_osc'), ('gatea', 'vm_gatea'), ('gated', 'vm_gated')):
            if src == 'vm_osc' and not has_vm_osc:
                continue
            sign = '-' if src == 'v12' else ''
            A('let i_%s = %si(%s)' % (nm, sign, src))
            A('meas tran ia_%s avg i_%s from=%gu to=%gu' % (nm, nm, quiet[0], quiet[1]))
            A('let ua_%s = ia_%s*1e6' % (nm, nm))
        A('echo "SUPPLY_uA window=%g-%gus VDDA=" $&ua_vdda " IOVDD=" $&ua_iovdd " VDD=" $&ua_vdd " | bgr=" $&ua_bgr " sense=" $&ua_sense " trip_3v3=" $&ua_tripa " trip_1v2=" $&ua_tripd%s " gate_3v3=" $&ua_gatea " gate_1v2=" $&ua_gated' % (quiet[0], quiet[1], ' " osc=" $&ua_osc' if has_vm_osc else ''))
        if t2f_on:
            A('* G1_T2F: output frequency (rising 0.6 V crossings) and supply currents over the quiet window')
            nr = max(2, int((quiet[1] - quiet[0]) * 1.0))   # rising edges counted: >= 1 MHz assumed (block: 1.54 MHz)
            A('meas tran t2f_t1 when v(temp_out)=0.6 rise=1 from=%gu to=%gu' % (quiet[0], quiet[1]))
            A('meas tran t2f_t2 when v(temp_out)=0.6 rise=%d from=%gu to=%gu' % (nr + 1, quiet[0], quiet[1]))
            A('let t2f_mhz = %de-6/(t2f_t2 - t2f_t1)' % nr)
            for nm, src in (('t2f', 'vm_t2f'), ('t2fd', 'vm_t2fd'), ('ls', 'vm_ls'), ('lsd', 'vm_lsd')):
                A('meas tran ia_%s avg i(%s) from=%gu to=%gu' % (nm, src, quiet[0], quiet[1]))
                A('let ua_%s = ia_%s*1e6' % (nm, nm))
            A('echo "T2F window=%g-%gus f_MHz=" $&t2f_mhz " periods=%d vdda_t2f_uA=" $&ua_t2f " vdd12_t2f_uA=" $&ua_t2fd " vdda_ls_uA=" $&ua_ls " vdd_ls_uA=" $&ua_lsd' % (quiet[0], quiet[1], nr))
        A('* trip evaluation after the load event at T_STEP')
        A('let tstep_s = %gu' % event_us)
        A('meas tran tripped_max max v(tripped) from=%gu to=%gu' % (t_cfg, tstop))
        A('meas tran tripped_pre max v(tripped) from=%gu to=%gu' % (t_cfg, event_us))
        if c.get('expect') != 'no trip':
            A('meas tran t_tripped when v(tripped)=0.6 rise=1 from=%gu' % event_us)
            A('meas tran t_trip_d when v(trip_d)=0.6 rise=1 from=%gu' % event_us)
            A('meas tran t_gate1v when v(gate)=1.0 fall=1 from=%gu' % event_us)
            A('meas tran t_gate03 when v(gate)=0.33 fall=1 from=%gu' % event_us)
        A('meas tran gate_min min v(gate) from=%gu to=%gu' % (event_us, tstop))
        A('meas tran gate_end find v(gate) at=%gu' % tstop)
        A('meas tran ipk max i(vim) from=%gu to=%gu' % (event_us, tstop))
        A('meas tran i_end find i(vim) at=%gu' % tstop)
        A('meas tran isense_pk max v(isense) from=%gu to=%gu' % (event_us, tstop))
        A('meas tran cause1e find v(cause1) at=%gu' % tstop)
        A('meas tran cause0e find v(cause0) at=%gu' % tstop)
        A('meas tran fault_end find v(fault_n) at=%gu' % tstop)
        A('let sp_v = ' + bits('sp', 16))
        A('meas tran soft_peak find sp_v at=%gu' % tstop)
        A('let cause = 2*(cause1e gt 0.6) + (cause0e gt 0.6)')
        if c.get('expect') != 'no trip':
            A('let dt_gate1v_us = (t_gate1v - tstep_s)*1e6')
            A('let dt_gate03_us = (t_gate03 - tstep_s)*1e6')
            A('let dt_tripped_us = (t_tripped - tstep_s)*1e6')
            A('let dt_trip_d_us = (t_trip_d - tstep_s)*1e6')
            A('echo "TRIP tripped_max=" $&tripped_max " tripped_before_event=" $&tripped_pre " t_tripped_us=" $&dt_tripped_us " t_trip_d_us=" $&dt_trip_d_us " t_gate_1V_us=" $&dt_gate1v_us " t_gate_0.33V_us=" $&dt_gate03_us " gate_min=" $&gate_min " gate_end=" $&gate_end " ipk_A=" $&ipk " i_end_A=" $&i_end " isense_pk=" $&isense_pk " cause=" $&cause " fault_n_end=" $&fault_end " soft_peak=" $&soft_peak')
        else:
            A('echo "NO_TRIP_EXPECTED tripped_max=" $&tripped_max " gate_min=" $&gate_min " gate_end=" $&gate_end " ipk_A=" $&ipk " i_end_A=" $&i_end " cause=" $&cause " fault_n_end=" $&fault_end " soft_peak=" $&soft_peak')
        A('let qi = integ(i(vim))')
        A('meas tran q_step find qi at=%gu' % event_us)
        A('meas tran q_end find qi at=%gu' % tstop)
        A('let q_passed = q_end - q_step')
        A('echo "CHARGE after_event_As=" $&q_passed')
        if any(t for t, lv in en_tr if lv == 0):
            t_off = [t for t, lv in en_tr if lv == 0][0]
            t_on = [t for t, lv in en_tr if lv == 1 and t > t_off][0]
            A('meas tran g_enlow find v(gate) at=%gu' % (t_on - 0.1))
            A('meas tran t_g_rearm when v(gate)=%g rise=1 from=%gu' % (0.9 * VDDA_V, t_on))
            A('meas tran i_rearm find i(vim) at=%gu' % tstop)
            A('meas tran tripped_rearm find v(tripped) at=%gu' % tstop)
            A('let dt_rearm_us = (t_g_rearm - %gu)*1e6' % t_on)
            A('echo "REARM gate_while_EN_low=" $&g_enlow " EN_high_to_GATE_90pct_us=" $&dt_rearm_us " gate_end=" $&gate_end " iload_end_A=" $&i_rearm " tripped_end=" $&tripped_rearm')
    else:
        t_en0 = en_tr[0][0]
        A('meas tran gmax_ramps max v(gate) from=0 to=%gu' % (t_en0 - 0.1))
        A('meas tran gc_max max v(gate_core) from=0 to=%gu' % (t_en0 - 0.1))
        A('meas tran g_end find v(gate) at=%gu' % tstop)
        A('meas tran t_g1r when v(gate)=1.0 rise=1 from=0 to=%gu' % (t_en0 - 0.1))
        A('meas tran t_g1f when v(gate)=1.0 fall=1 from=0 to=%gu' % (t_en0 - 0.1))
        A('let t_high_us = (t_g1f - t_g1r)*1e6')
        A('meas tran ipk_ramps max i(vim) from=0 to=%gu' % (t_en0 - 0.1))
        A('let qi = integ(i(vim))')
        A('meas tran q_ramps find qi at=%gu' % (t_en0 - 0.1))
        A('meas tran tripped_ramps max v(tripped) from=0 to=%gu' % (t_en0 - 0.1))
        A('meas tran en_core_max max v(en_core) from=0 to=%gu' % (t_en0 - 0.1))
        A('echo "POWERUP GATE_max_EN_low=" $&gmax_ramps " gate_core_max=" $&gc_max " en_core_max=" $&en_core_max " GATE_above_1V_from_us=" $&t_g1r " to_us=" $&t_g1f " duration_us=" $&t_high_us " load_peak_A=" $&ipk_ramps " charge_As=" $&q_ramps " tripped_max=" $&tripped_ramps " GATE_after_EN=" $&g_end')
    waves = 'v(gate) v(gfet) v(tripped) v(isense) v(cmp_soft) v(cmp_hard) v(cmp_clk) v(trip_d) v(osc_clk) v(vref) v(en_core) v(shp) v(fault_n) v(vdda) v(vdd) v(iprof) %s %s %s v(dig_trip) v(inrush_active) i(vim) i(vma) i(vmi) i(v12)' % (icmp, vths, vthh)
    state_signals = 'v(en_core) v(inrush_active) v(dig_trip) v(fast_en) v(cause1) v(cause0) ' + ' '.join('v(%s%d)' % (p, i) for p in ('soft', 'hard') for i in range(8))
    state_signals += ' v(soft_armed) ' + ' '.join('v(sp%d)' % i for i in range(16))
    state_signals += ' v(sclk_pad) v(sdi_pad) v(sdo) v(clr_d)'
    # linearize selects a new plot containing only its requested vectors.
    # Preserve configuration/cause from the original transient before switching.
    A('wrdata %s %s' % (os.path.join(BUILD, 'state_%s.txt' % tag), state_signals))
    A('linearize ' + waves)
    A('wrdata %s %s' % (os.path.join(BUILD, 'waves_%s.txt' % tag), waves))
    A('.endc')
    A('.end')
    if interconnect == 'extracted':
        if front != 'tl':
            raise SystemExit('--interconnect extracted needs the transistor-level front end')
        apply_interconnect(L, None if powerup else quiet, sense_route_r)
    elif sense_route_r:
        raise SystemExit('--sense-route-r needs --interconnect extracted')
    if VDD_V != 1.2:
        # digital-signal measurement thresholds (osc_clk, cmp_clk, DAC/cause bits, latches, T2F out) at VDD/2
        k = L.index('.control')
        L[k:] = [re.sub(r'(\)=|\bgt )0\.6\b', lambda m: m.group(1) + '%g' % (VDD_V / 2), l) for l in L[k:]]
    return '\n'.join(L) + '\n'


def diagnostic_deck(deck, analysis, tstop, tag):
    """Use only observations valid inside this prefix; no post-event verdicts."""
    before, control = deck.split('.control\n', 1)
    lines = ['.control', 'set filetype=ascii', 'set numdgt=15', 'set wr_singlescale', 'set wr_vecnames']
    signals = 'v(vref) v(isense) v(gate) v(vdd) v(vdda) v(osc_clk) v(cmp_clk)'
    if analysis == 'op':
        lines += ['op', 'print ' + signals, 'echo DIAGNOSTIC_OP_RETURNED']
    else:
        tran = next(line for line in control.splitlines() if line.startswith('tran '))
        lines += [tran, 'let observed_end = time[length(time)-1]',
                  'echo DIAGNOSTIC_PREFIX_END_S $&observed_end',
                  'wrdata %s %s' % (os.path.join(BUILD, 'waves_%s.txt' % tag), signals)]
        # Preserve configuration observables separately; the primary prefix
        # schema stays compatible with prior diagnostic evidence.
        state_signals = 'v(en_core) v(inrush_active) v(dig_trip) v(fast_en) ' + \
                        ' '.join('v(%s%d)' % (p, i) for p in ('soft', 'hard') for i in range(8))
        lines += ['wrdata %s %s' % (os.path.join(BUILD, 'state_%s.txt' % tag), state_signals)]
        if re.search(r'^XT2F ', before, re.M):
            lines += ['wrdata %s v(temp_out) v(t2f_en33) v(t2f_mode33) i(vma) i(vm_t2f) i(vm_t2fd) i(vm_ls) i(vm_lsd) '
                      'i(vm_bgr) i(vm_sense)' % os.path.join(BUILD, 't2f_%s.txt' % tag)]
    lines += ['rusage all', '.endc', '.end']
    return before + '\n'.join(lines) + '\n'


def validate_prefix(out, wave_path, requested_end_s):
    """Accept only a reached endpoint with a complete, finite saved signal set.

    Equal printed times are allowed: old ASCII precision rounds fine timesteps.
    Missing/truncated files and NaN/Inf values are rejected even with exit zero.
    """
    end = re.search(r'^DIAGNOSTIC_PREFIX_END_S\s+([-+0-9.eE]+)', out, re.M)
    tolerance = max(1e-15, requested_end_s * 1e-6)
    if not end or abs(float(end[1]) - requested_end_s) > tolerance:
        return False, 'requested endpoint not reported'
    expected = ['time', 'v(vref)', 'v(isense)', 'v(gate)', 'v(vdd)',
                'v(vdda)', 'v(osc_clk)', 'v(cmp_clk)']
    previous = None
    rows = 0
    try:
        with open(wave_path) as waveform:
            if waveform.readline().split() != expected:
                return False, 'missing or unexpected waveform columns'
            for line in waveform:
                values = [float(value) for value in line.split()]
                if len(values) != len(expected) or not all(math.isfinite(v) for v in values):
                    return False, 'incomplete or nonfinite waveform row'
                if previous is None and abs(values[0]) > tolerance:
                    return False, 'waveform does not start at zero'
                if previous is not None and values[0] < previous:
                    return False, 'waveform time decreases'
                previous = values[0]
                rows += 1
    except (OSError, ValueError):
        return False, 'waveform missing or unreadable'
    if rows < 2 or abs(previous - requested_end_s) > tolerance:
        return False, 'saved waveform does not reach requested endpoint'
    return True, 'saved finite waveform reaches requested endpoint'


def rtl_files(t2f='off'):
    return ([RTL_WRAPPER_T2F] + RTL_FILES[1:]) if t2f == 'tl' else RTL_FILES


# --interconnect extracted: top-level routing between the macros (kpex 2.5D CC, fill removed), C-only subckt
# g1_top_interconnect of sim/postlayout/top_interconnect_20260925.spice (README_top_interconnect_20260925.md).
# It replaces the deck's Cw_* wiring estimates on the nets it covers (no double count).
TOP_INTERCONNECT = os.path.join(HERE, 'postlayout', 'top_interconnect_20260925.spice')
TOP_INTERCONNECT_SHA256 = 'ddc88cc765e99a0e982c9b6bc24817bfe336ae686930b2c12a85d514fb2adcc2'
ICX_REMOVED = ('Cw_isense', 'Cw_soft', 'Cw_hard', 'Cw_en', 'Cw_sclk', 'Cw_sdi', 'Cw_tripped', 'Cw_clk')
# CDL port -> (deck node, fallback when the node is not in this deck); fallbacks are static levels at reset
ICX_MAP = dict(
    [('isense', ('isense', None)), ('vref', ('vref', None)), ('vref_buf', ('vref_buf', None)), ('iptat', ('iptat', None)),
     ('pbias', ('pbias', None)), ('pcasc', ('pcasc', None)), ('cmp_soft', ('cmp_soft', None)), ('cmp_hard', ('cmp_hard', None)),
     ('cmp_clk', ('cmp_clk', None)), ('osc_clk', ('osc_clk', None)), ('osc_en', ('osc_en', 'vdd')),
     ('trip_d', ('trip_d', '0')), ('clr_d', ('clr_d', '0')), ('fast_en', ('fast_en', '0')), ('tripped', ('tripped', '0')),
     ('en_i', ('en_core', None)), ('sclk_i', ('sclk_core', None)), ('sdi_i', ('sdi_core', None)), ('sdo_o', ('sdo', '0')),
     ('gate_o', ('gate_core', '0')), ('fault_n_o', ('fault_core', '0')),
     ('t2f_en_12', ('t2f_en12', 'vdd')), ('t2f_en_33', ('t2f_en33', 'vdda')), ('t2f_mode_12', ('t2f_mode12', '0')),
     ('t2f_mode_33', ('t2f_mode33', '0')), ('temp_out_o', ('temp_out', '0')),
     ('sense_p', ('sense_p', None)), ('sense_n', ('sense_n', None)), ('bgr_r4_33', ('r4', '0')), ('bgr_r4_12', (None, '0')),
     ('net', (None, 'vdd'))] +
    [('dac_soft_%d_' % k, ('soft%d' % k, None)) for k in range(8)] + [('dac_hard_%d_' % k, ('hard%d' % k, None)) for k in range(8)] +
    [('osc_trim_%d_' % k, ('trim%d' % k, None)) for k in range(4)] +
    [(p, (None, '0')) for p in ('d_elt', 'd_std', 'g_shared', 'hbt_b', 'hbt_c', 'hbt_e')] + [('sub', ('0', None))])
SENSE_ROUTE_R = {'sense_p': 171.0, 'sense_n': 106.0}   # README: series R of the SENSE_P / SENSE_N pad routes (upper bound)


def apply_interconnect(L, quiet, sense_route_r):
    """Edit the deck lines in place for --interconnect extracted (and --sense-route-r)."""
    if sha256(TOP_INTERCONNECT) != TOP_INTERCONNECT_SHA256:
        raise SystemExit('%s does not match its bound SHA256 %s' % (TOP_INTERCONNECT, TOP_INTERCONNECT_SHA256))
    ports = subckt_ports(TOP_INTERCONNECT, 'g1_top_interconnect').split()
    if set(ports) != set(ICX_MAP):
        raise SystemExit('g1_top_interconnect ports differ from ICX_MAP: %s' % sorted(set(ports) ^ set(ICX_MAP)))
    removed = [l for l in L if l.split()[:1] and l.split()[0] in ICX_REMOVED]
    L[:] = [l for l in L if not (l.split()[:1] and l.split()[0] in ICX_REMOVED)]
    k = L.index('.control')
    nodes = set()
    for l in L[:k]:
        f = l.split()
        if f and f[0][0] in 'aA':
            nodes.update(x.strip('[]').lower() for x in f[1:])
        elif f and f[0][0] in 'BbEeGg':
            nodes.update(x.lower() for x in f[1:3])
        elif f and f[0][0].isalpha():
            nodes.update(x.lower() for x in f[1:] if '=' not in x)
    conn, notes = [], []
    for p in ports:
        node, fb = ICX_MAP[p]
        if sense_route_r and p in SENSE_ROUTE_R:
            conn.append(p + '_i')     # created below by the XSENSE rename
            continue
        if node is None or (node != '0' and node not in nodes):
            notes.append('%s->%s' % (p, fb))
            node = fb
        conn.append(node)
    hdr = ['* ---- top-level interconnect (--interconnect extracted): %s sha256 %s' % (os.path.relpath(TOP_INTERCONNECT, ROOT), TOP_INTERCONNECT_SHA256),
           '* C-only subckt g1_top_interconnect, sub = 0; removed wiring estimates: ' + (' | '.join(removed) or 'none'),
           '* ports without a deck node tied to their static reset level: ' + (', '.join(notes) or 'none')]
    inst = hdr + ['XICX ' + ' '.join(conn) + ' g1_top_interconnect']
    if sense_route_r:
        xs = [i for i, l in enumerate(L) if l.startswith('XSENSE sense_p sense_n ')]
        if len(xs) != 1:
            raise SystemExit('--sense-route-r: XSENSE sense_p sense_n instance not found')
        L[xs[0]] = L[xs[0]].replace('XSENSE sense_p sense_n ', 'XSENSE sense_p_i sense_n_i ', 1)
        inst += ['* --sense-route-r: series R of the unequal SENSE pad routes (README: SENSE_P 171 Ohm, SENSE_N 106 Ohm);',
                 '* the route C of g1_top_interconnect sits on the block side (sense_p_i / sense_n_i)',
                 'Rroute_p sense_p sense_p_i %g' % SENSE_ROUTE_R['sense_p'], 'Rroute_n sense_n sense_n_i %g' % SENSE_ROUTE_R['sense_n']]
    last_inc = max(i for i, l in enumerate(L[:k]) if l.startswith('.include'))
    L.insert(last_inc + 1, '.include %s' % TOP_INTERCONNECT)
    k = L.index('.control')
    s = next(i for i, l in enumerate(L) if l.startswith('.save '))
    L[s:s] = inst
    if quiet:
        w = next(i for i, l in enumerate(L) if i > L.index('.control') and l.startswith('wrdata '))
        L[w:w] = ['* VREF ripple over the quiet window (VREF-osc_clk coupling of the extracted routing)',
                  'meas tran vref_rmax max v(vref) from=%gu to=%gu' % quiet, 'meas tran vref_rmin min v(vref) from=%gu to=%gu' % quiet,
                  'meas tran vref_ravg avg v(vref) from=%gu to=%gu' % quiet, 'let vref_pp_mv = (vref_rmax - vref_rmin)*1e3',
                  'echo "VREF_RIPPLE window=%g-%gus pp_mV=" $&vref_pp_mv " mean=" $&vref_ravg " max=" $&vref_rmax " min=" $&vref_rmin' % quiet]


def rtl_vvp_path(tag):
    """Per-run compiled-RTL path. All lower case: ngspice lower-cases the d_cosim sim_args string, so a path
    containing the tag's upper-case letters (27C, gA) cannot be opened ("Unable to open input file")."""
    p = os.path.join(BUILD, 'cosim_%s.vvp' % hashlib.sha256(tag.encode()).hexdigest()[:24])
    assert p == p.lower(), 'compiled-RTL path must be lower case for ngspice: ' + p
    return p


def verify_vvp(vvp):
    """None if the compiled RTL is loadable-looking (non-empty file, vvp header, root module present), else why."""
    try:
        with open(vvp, 'rb') as f:
            head = f.read(4096)
        size = os.path.getsize(vvp)
    except OSError as exc:
        return 'unreadable: %s' % exc
    if size < 1000 or not head.startswith(b'#!') or b'vvp' not in head.split(b'\n', 1)[0]:
        return 'not a complete vvp file (size %d, header %r)' % (size, head[:60])
    if b'g1_dig_cosim' not in open(vvp, 'rb').read():
        return 'root module g1_dig_cosim* not found'
    return None


def compile_rtl(log, t2f='off', tag=None):
    """Compile the RTL to build/g1_top/<tag>.vvp (per run; written under a temporary name and moved into place
    atomically), so that concurrent launches never load a file another launch is rewriting."""
    import fcntl
    os.makedirs(BUILD, exist_ok=True)
    vvp = rtl_vvp_path(tag) if tag else os.path.join(BUILD, 'g1_dig_cosim_t2f.vvp' if t2f == 'tl' else 'g1_dig_cosim.vvp')
    tmp = '%s.tmp%d' % (vvp, os.getpid())
    files = rtl_files(t2f)
    cmd = ['iverilog', '-g2005', '-Wall', '-Wno-timescale', '-o', tmp] + files
    with open(os.path.join(BUILD, '.rtl_compile.lock'), 'a') as lock:   # serialise compiles across launches
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            r = subprocess.run(cmd, capture_output=True, text=True)
            log.write('# %s\n%s%s' % (' '.join(cmd), r.stdout, r.stderr))
            if r.returncode != 0:
                log.write('# run status failed (rtl compile: iverilog exit %d)\n' % r.returncode)
                raise SystemExit('iverilog failed (exit %d):\n%s%s' % (r.returncode, r.stdout, r.stderr))
            why = verify_vvp(tmp)
            if why:
                log.write('# run status failed (rtl compile: %s)\n' % why)
                raise SystemExit('compiled RTL %s rejected before ngspice: %s' % (tmp, why))
            os.replace(tmp, vvp)
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)
    log.write('# compiled RTL %s (tag %s) sha256 %s\n' % (os.path.relpath(vvp, ROOT), tag, sha256(vvp)))
    for f in files:
        log.write('# rtl sha256 %s %s\n' % (sha256(f), os.path.relpath(f, ROOT)))
    return vvp


def decimate(src, dst, every):
    with open(src) as f, open(dst, 'w') as g:
        for i, line in enumerate(f):
            if i == 0 or (i - 1) % every == 0:
                g.write(line)


def checkpoint_deck(deck, times_us, stop_us, tag):
    """Save observations in one live simulator process; these are not restart states."""
    times = sorted(set(times_us))
    if any(not math.isfinite(t) or not 0 < t < stop_us for t in times):
        raise ValueError('checkpoint times must be finite, positive and before endpoint')
    match = re.search(r'^tran .+$', deck, re.M)
    if not match:
        raise ValueError('checkpoints require transient analysis')
    vectors = ' '.join('v(%s)' % n for n in
        ['vref','isense','gate','gfet','gate_core','tripped','vdd','vdda','iovdd','osc_clk','cmp_clk','cmp_soft','cmp_hard','dig_trip','inrush_active','en_core','cause0','cause1'] +
        ['soft%d' % i for i in range(8)] + ['hard%d' % i for i in range(8)])
    vectors += ' i(vim) i(vma) i(vmi) i(v12)'
    control = ['stop when time = %gu' % t for t in times] + [match[0]]
    for t in times:
        control += ['wrdata %s %s' % (os.path.join(BUILD,'checkpoint_%s_%gus.txt' % (tag,t)),vectors),'resume']
    return deck[:match.start()] + '\n'.join(control) + deck[match.end():]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('cases', nargs='*')
    ap.add_argument('--netlist', default='sch', choices=('sch', 'pex'))
    ap.add_argument('--t2f', default='off', choices=('off', 'tl'),
                    help='G1_T2F behind two g1_ls_up at transistor level (baseline PEX, chip CDL wiring, fout into 1 pF; TEMP_OUT pad not modelled)')
    ap.add_argument('--view-override', default=None, metavar='BLOCK=VIEW[,...]',
                    help='per-block view after --netlist/--blockset resolution, e.g. bgr=sch,trip=pex (blocks bgr sense trip osc gate)')
    ap.add_argument('--interconnect', default='estimate', choices=('estimate', 'extracted'),
                    help='top-level wiring: Cw_* estimates (default) or the extracted g1_top_interconnect C (postlayout/top_interconnect_20260925.spice)')
    ap.add_argument('--sense-route-r', action='store_true',
                    help='with --interconnect extracted: series 171/106 Ohm on the SENSE_P/SENSE_N pad routes')
    ap.add_argument('--fault-mult', type=float, default=None, metavar='X',
                    help="fault-event load level as X x nominal 1 A (replaces the case's single fault level, timing unchanged)")
    ap.add_argument('--vdd', type=float, default=1.2, help='VDD (V), default 1.2')
    ap.add_argument('--vdda', type=float, default=3.3, help='VDDA = IOVDD board rail (V), default 3.3')
    ap.add_argument('--blockset', default='legacy', choices=tuple(BLOCKSETS),
                    help='analog block netlists: legacy (Sep-19 paths, default) or c1414 (frozen 1414 um chip: BGR586, SENSE R100, TRIP NF4, OSC R0.95)')
    ap.add_argument('--front', default=None, choices=('tl', 'beh'), help='override the case default')
    ap.add_argument('--osc', default=None, choices=('tl', 'ideal'), help='clock delivered to the RTL: ideal source at the block frequency (default) or the transistor-level oscillator (case osc)')
    ap.add_argument('--temp', type=float, default=27)
    ap.add_argument('--corner', default='tt', choices=tuple(CORNERS))
    ap.add_argument('--analysis', choices=('functional', 'prefix', 'op'), default='functional')
    ap.add_argument('--timeout', type=float, default=300, help='wall seconds per ngspice process (default 300)')
    ap.add_argument('--threads', type=int, choices=(1, 2, 4, 8), default=None,
                    help='explicit ngspice model-evaluation threads; unset retains simulator default')
    ap.add_argument('--solver', choices=('sparse', 'klu'), default='sparse',
                    help='linear solver qualification; default preserves SPARSE baseline')
    ap.add_argument('--image-id', default=None, help='EDA image content digest recorded by the launcher')
    ap.add_argument('--run-id', default=None, help='unique evidence suffix, auto generated if omitted')
    ap.add_argument('--tstop', type=float, default=None, help='override end time (us)')
    ap.add_argument('--pads', default='pdk', choices=('pdk', 'nodcn'), help='nodcn: all PDK pad instances (XP*) use a deck-local dantenna-free copy of sg13g2_io.spi (documented deviation, PADS_NODCN_WARNING)')
    ap.add_argument('--inpads', default='ideal', choices=('ideal', 'model', 'nodcn'), help='EN/SCLK/SDI input pads: ideal level copies (default) or the PDK sg13g2_IOPadIn models; nodcn: ideal EN/SCLK/SDI and SENSE_P/N analog pads without the dantenna diodes (documented deviation, NODCN_WARNING)')
    ap.add_argument('--outpads', default=None, choices=('beh', 'model'), help='GATE/FAULT_N pads: behavioural drivers fitted to the g1_gate results (default for the transistor-level front end) or the PDK models (default for the behavioural front end and the power-up cases)')
    ap.add_argument('--method', default=None, choices=('gear', 'trap'), help='integration method (default: trap for the transistor-level front end, gear otherwise)')
    ap.add_argument('--accuracy', choices=('baseline', 'tight'), default='baseline',
                    help='tight comparator qualification: reltol1e-5, abstol1e-14, vntol1e-7; baseline remains unchanged')
    ap.add_argument('--maxstep-ns', type=float, default=None, help='explicit transient maximum step in ns for numerical qualification')
    ap.add_argument('--timeline',choices=('baseline','compact'),default='baseline',help='compact c_mid only: serial4us,fault16us,stop28us; SEU fill not qualified')
    ap.add_argument('--checkpoint-us',type=float,nargs='+',default=[],help='save partial observations then resume within the same running simulator; not restart checkpoints')
    ap.add_argument('--rtl-dir', default='rtl', choices=tuple(RTL_DIRS),
                    help='digital macro RTL copy for the co-simulation: rtl (chip of record, default) or eco_20260925 '
                         '(blocks/g1_ctrl/ECO_20260925.md); a non-default choice adds _rtl<name> to the run tag')
    ap.add_argument('--dry', action='store_true')
    ap.add_argument('--tedge', type=float, default=None, help='edge time of EN/SCLK/SDI (s), default 2 ns')
    ap.add_argument('--event-shift-ns', type=float, default=0,
                    help='baseline c_mid/hard_pulse fault-only phase shift0..500ns')
    ap.add_argument('--list', action='store_true')
    ap.add_argument('--extra-options', default=None, help='diagnostic: extra .option line placed after the solver line (e.g. "chgtol=1e-12")')
    ap.add_argument('--osc-rx', choices=('bridge', 'schmitt'), default='bridge', help='diagnostic: clock receiver between the transistor-level osc_clk and the adc_bridge')
    ap.add_argument('--osc-supply-r', type=float, default=None, help='diagnostic: series R (Ohm) on the OSC supply pin')
    ap.add_argument('--osc-decap', type=float, default=None, help='diagnostic: local decap (F) on the OSC supply pin')
    ap.add_argument('--save-extra', nargs='+', default=[], help='diagnostic: extra vectors saved and written right after tran (e.g. v(xtrip.xch.xn))')
    ap.add_argument('--decimate', type=int, default=0, help='keep every n-th linearised point in results/waves (0: auto, about 2000 rows)')
    a = ap.parse_args()
    if a.timeout <= 0 or (a.tstop is not None and a.tstop <= 0):
        ap.error('timeout and tstop must be positive')
    if a.maxstep_ns is not None and a.maxstep_ns <= 0:
        ap.error('maxstep must be positive')
    if a.analysis == 'prefix' and a.tstop is None:
        ap.error('--analysis prefix requires --tstop US')
    if a.run_id and not re.fullmatch(r'[A-Za-z0-9_-]+', a.run_id):
        ap.error('--run-id must contain only letters, digits, underscore or hyphen')
    global VIEW_OVERRIDE, VDD_V, VDDA_V, BR_LO, BR_HI
    if not (0.5 <= a.vdd <= 2.0 and 1.5 <= a.vdda <= 4.0):
        ap.error('--vdd 0.5..2.0 V, --vdda 1.5..4.0 V')
    VDD_V, VDDA_V = a.vdd, a.vdda
    if VDD_V != 1.2:
        BR_LO, BR_HI = VDD_V / 2 - 0.05, VDD_V / 2 + 0.05
    vtag = lambda v: ('%g' % v if '.' in '%g' % v else '%g.0' % v).replace('.', 'p')
    supply_tag = '' if (VDD_V, VDDA_V) == (1.2, 3.3) else '_vdd%s_vdda%s' % (vtag(VDD_V), vtag(VDDA_V))
    try:
        VIEW_OVERRIDE = parse_view_override(a.view_override)
    except ValueError as exc:
        ap.error(str(exc))
    run_id = a.run_id or time.strftime('%Y%m%dT%H%M%SZ', time.gmtime()) + '_' + uuid.uuid4().hex[:8]
    global TEDGE, T_SER, T_STEP, CASES, RTL_FILES
    RTL_FILES = make_rtl_files(a.rtl_dir)
    global PADS_NODCN
    PADS_NODCN = (a.pads == 'nodcn')
    if a.timeline == 'compact':
        if len(a.cases) != 1 or a.cases[0] not in ('c_mid', 'c', 'c_fast', 'e20', 'osc') or a.analysis != 'functional':
            ap.error('compact timeline supports one of c_mid, c, c_fast, e20, osc (functional) only')
        T_SER,T_STEP=4.0,16.0
        CASES=make_cases()
        CASES['c_mid']['tstop']=28
        for k in ('c', 'c_fast', 'e20'):
            CASES[k]['tstop'] = 22
        CASES['osc']['tstop'] = 16
        CASES['osc']['quiet'] = (10, 16)
    if a.tedge:
        TEDGE = a.tedge
    if a.list:
        for k, v in CASES.items():
            print('%-6s %-4s tstop %6g us  %s' % (k, v.get('front', 'tl'), v['tstop'], v['desc']))
        return
    os.makedirs(BUILD, exist_ok=True)
    os.makedirs(os.path.join(HERE, 'logs'), exist_ok=True)
    os.makedirs(os.path.join(HERE, 'results', 'waves'), exist_ok=True)
    env = dict(os.environ)
    env['LD_LIBRARY_PATH'] = '/foss/tools/iverilog/lib' + (':' + env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '')
    for name in a.cases:
        if name not in CASES:
            raise SystemExit('unknown case %s (use --list)' % name)
        try:
            case = shift_fault_phase(CASES[name], name, a.event_shift_ns, a.timeline)
        except ValueError as exc:
            ap.error(str(exc))
        if a.fault_mult is not None:
            try:
                case = scale_fault(case, a.fault_mult)
            except ValueError as exc:
                ap.error(str(exc))
        if a.event_shift_ns and a.tstop is not None:
            ap.error('fault phase shift preserves the baseline endpoint')
        if a.accuracy == 'tight':
            case['tol'] = 'reltol=1e-5 abstol=1e-14 vntol=1e-7 chgtol=1e-14'
        if a.maxstep_ns is not None:
            case['tmax'] = a.maxstep_ns * 1e-9
        front = a.front or case.get('front', 'tl')
        osc = a.osc or case.get('osc', 'ideal')
        tag = '%s_%s%s_%s_%s_%gC' % (name, a.netlist, '' if a.blockset == 'legacy' else '_' + a.blockset, front, a.corner, a.temp) + supply_tag + (('_fm' + vtag(a.fault_mult)) if a.fault_mult is not None else '') + ('_icx' if a.interconnect == 'extracted' else '') + ('_srr' if a.sense_route_r else '') + ('_ovr-' + '-'.join(k + v for k, v in sorted(VIEW_OVERRIDE.items())) if VIEW_OVERRIDE else '') + ('_t2ftl' if a.t2f == 'tl' else '') + ('_osctl' if osc == 'tl' and name != 'osc' else '') + ('_inpads' if a.inpads == 'model' else '') + ('_nodcn' if a.inpads == 'nodcn' else '') + ('_padsnodcn' if a.pads == 'nodcn' else '') + ('_outpads' if a.outpads == 'model' and front == 'tl' else '') + ('_%s' % a.method if a.method else '')
        tag += '_clockfix'
        if a.rtl_dir != 'rtl':
            tag += '_rtl' + a.rtl_dir.replace('_', '')
        if a.event_shift_ns:
            tag += '_phase%gns' % a.event_shift_ns
        if a.timeline != 'baseline':tag += '_compact'
        if a.accuracy != 'baseline':
            tag += '_' + a.accuracy
        if a.maxstep_ns is not None:
            tag += '_maxstep%gns' % a.maxstep_ns
        if a.threads is not None:
            tag += '_threads%d' % a.threads
        if a.solver == 'klu':
            tag += '_klu'
        if a.tstop:
            tag += '_t%g' % a.tstop
        if a.extra_options:
            tag += '_opt' + re.sub(r'[^A-Za-z0-9]+', '', a.extra_options.replace('-', 'm'))
        if a.osc_rx != 'bridge':
            tag += '_rx' + a.osc_rx
        if a.osc_supply_r or a.osc_decap:
            tag += '_oscsup%gR%gF' % (a.osc_supply_r or 0, a.osc_decap or 0)
        tag += '_' + a.analysis + '_' + run_id
        for directory, ext in ((BUILD, '.cir'), (os.path.join(HERE, 'logs'), '.log'), (os.path.join(HERE, 'logs'), '.json'), (os.path.join(HERE, 'decks'), '.cir')):
            if os.path.exists(os.path.join(directory, tag + ext)):
                raise SystemExit('refusing to overwrite evidence: ' + tag)
        outpads = a.outpads or ('beh' if front == 'tl' and not case.get('powerup') else 'model')
        inpads = a.inpads if a.inpads != 'ideal' or not case.get('inpads') else case['inpads']
        method = a.method or ('trap' if front == 'tl' and not case.get('powerup') else 'gear')
        deck = build_deck(case, name, a.netlist, front, a.temp, a.corner, tag, a.tstop, osc, inpads, outpads, method,
                          a.osc_rx, a.osc_supply_r, a.osc_decap, blockset=a.blockset, t2f=a.t2f,
                          interconnect=a.interconnect, sense_route_r=a.sense_route_r)
        rel, bs_warnings, _ = resolve_netlists(a.blockset, a.netlist)
        if inpads == 'nodcn':
            bs_warnings = list(bs_warnings) + [NODCN_WARNING]
        if a.pads == 'nodcn':
            bs_warnings = list(bs_warnings) + [PADS_NODCN_WARNING]
            deck = re.sub(r'^(XP\w* .*) (sg13g2_IOPad\w+)$', r'\1 g1nd_\2', deck, flags=re.M)
        for w in bs_warnings:
            print(w)
        if a.analysis != 'functional':
            deck = diagnostic_deck(deck, a.analysis, a.tstop, tag)
        if a.extra_options:
            deck = re.sub(r'^(\.option method=.*)$', lambda m: m.group(1) + '\n.option ' + a.extra_options, deck, count=1, flags=re.M)
        if a.save_extra:
            ex = ' '.join(a.save_extra)
            deck = re.sub(r'^(\.save .*(?:\n\+ .*)*)', lambda m: m.group(1) + '\n+ ' + ex, deck, count=1, flags=re.M)
            deck = re.sub(r'^(tran .*)$', lambda m: m.group(1) + '\nwrdata %s %s' % (os.path.join(BUILD, 'diag_%s.txt' % tag), ex), deck, count=1, flags=re.M)
        if a.checkpoint_us:
            try:deck = checkpoint_deck(deck,a.checkpoint_us,a.tstop or case['tstop'],tag)
            except ValueError as exc:ap.error(str(exc))
        if a.threads is not None:
            deck = deck.replace('.control\n', '.control\nset num_threads=%d\n' % a.threads, 1)
        if a.solver == 'klu':
            deck = deck.replace('.control\n', '.option klu\n.control\n', 1)
        validate_exports(deck)
        deck_path = os.path.join(BUILD, tag + '.cir')
        with open(deck_path, 'w') as f:
            f.write(deck)
        if a.dry:
            print('wrote', deck_path)
            continue
        os.makedirs(os.path.join(HERE, 'decks'), exist_ok=True)
        with open(os.path.join(HERE, 'decks', tag + '.cir'), 'w') as f:      # copy kept as evidence
            f.write(deck)
        log_path = os.path.join(HERE, 'logs', tag + '.log')
        with open(log_path, 'w') as log:
            log.write('# G1_TOP run %s  %s UTC\n# %s\n' % (tag, time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), case['desc']))
            log.write('# deck %s\n' % os.path.relpath(deck_path, ROOT))
            log.write('# supplies VDD %g V, VDDA = IOVDD %g V\n' % (VDD_V, VDDA_V))
            if a.interconnect == 'extracted':
                log.write('# interconnect extracted %s sha256 %s%s\n' % (os.path.relpath(TOP_INTERCONNECT, ROOT), sha256(TOP_INTERCONNECT),
                                                                       ' + sense route R 171/106 Ohm' if a.sense_route_r else ''))
            if case.get('fault_mult'):
                log.write('# fault-mult %g (case fault level %g x INOM)\n' % (case['fault_mult'][1], case['fault_mult'][0]))
            log.write('# blockset %s%s\n' % (a.blockset, (' view-override ' + a.view_override) if VIEW_OVERRIDE else ''))
            for w in bs_warnings:
                log.write('# %s\n' % w)
            for k, v in list(rel.items()) + (list(T2F_NETLISTS.items()) if a.t2f == 'tl' else []):
                p = os.path.join(BLOCKS, v)
                if front == 'tl' or k == 'gate':
                    log.write('# netlist sha256 %s blocks/%s\n' % (sha256(p), v))
            log.write('# IO models sha256 %s %s\n' % (sha256(IOSPI), IOSPI))
            if os.path.exists(PDK + '/COMMIT'):
                log.write('# PDK commit %s\n' % open(PDK + '/COMMIT').read().strip())
            v = subprocess.run(['ngspice', '-v'], capture_output=True, text=True).stdout.splitlines()
            log.write('# %s\n' % next((l.strip('* ') for l in v if 'ngspice-' in l), 'ngspice version line not found'))
            log.write('# %s\n' % subprocess.run(['iverilog', '-V'], capture_output=True, text=True).stdout.splitlines()[0])
            iv_version = subprocess.run(['iverilog', '-V'], capture_output=True, text=True).stdout.splitlines()[0]
            vvp_run = compile_rtl(log, a.t2f, tag)
            if vvp_run not in deck or verify_vvp(vvp_run):
                log.write('# run status failed (rtl not loadable before ngspice)\n')
                raise SystemExit('compiled RTL %s missing from deck sim_args or unloadable; ngspice not started' % vvp_run)
            log.flush()
            inputs = set(rtl_files(a.t2f))
            if a.t2f == 'tl':
                inputs.update(os.path.join(BLOCKS, v) for v in T2F_NETLISTS.values())
            if a.blockset == 'legacy':
                for source in rel.values():
                    directory = os.path.dirname(os.path.join(BLOCKS, source))
                    inputs.update(os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.spice'))
            else:
                inputs.update(os.path.join(BLOCKS, source) for source in rel.values())
            meta = dict(tag=tag, analysis=a.analysis, options=vars(a),
                        effective=dict(interconnect=a.interconnect, sense_route_r=a.sense_route_r, fault_mult=a.fault_mult, vdd=VDD_V, vdda=VDDA_V, blockset=a.blockset, view_override=VIEW_OVERRIDE, netlists=rel, blockset_warnings=bs_warnings, front=front, osc=osc, inpads=inpads, outpads=outpads, method=method,
                                       threads=a.threads, solver=a.solver),
                        git_revision=subprocess.check_output(['git', '-c', 'safe.directory=' + ROOT,
                                                              'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                        ngspice_version=next((l.strip('* ') for l in v if 'ngspice-' in l), None),
                        iverilog_version=iv_version, image_id=a.image_id,
                        pdk_commit=open(PDK + '/COMMIT').read().strip() if os.path.exists(PDK + '/COMMIT') else None,
                        spiceinit_sha256=sha256(os.path.join(HERE, '.spiceinit')),
                        runner_sha256=sha256(__file__), helper_sha256=sha256(os.path.join(HERE, 'run_bounded.py')),
                        deck_sha256=sha256(deck_path), input_sha256={os.path.relpath(p, ROOT): sha256(p)
                        for p in sorted(inputs)},
                        io_sha256=sha256(IOSPI))
            outcome = run_bounded(['ngspice', '-b', deck_path], log,
                                  os.path.join(HERE, 'logs', tag + '.json'), a.timeout,
                                  cwd=HERE, env=env, metadata=meta)
            dt = outcome['wall_s']
            returncode = outcome['returncode']
            log.write('\n# run status %s\n# ngspice exit %s, wall time %.0f s\n' % (outcome['status'], returncode, dt))
        out = open(log_path, errors='replace').read()
        lines = [l for l in out.splitlines() if re.match(r'^(QUIET|CLOCK|SUPPLY_uA|TRIP|CHARGE|REARM|POWERUP|DIAGNOSTIC_\w+)\b', l)]
        err = [l.strip() for l in out.splitlines() if 'Timestep too small' in l or ('rror' in l and 'measure' not in l)]
        err = [re.sub(r'.*doAnalyses', 'doAnalyses', e) for e in err]
        outcome['functional_acceptance'] = 'not assessed'
        outcome['diagnostic_acceptance'] = 'not applicable'
        failure = solver_failure(out)
        cosim_bad = re.search(r'mismatched XSPICE/co-simulator[^\n]*', out)
        if cosim_bad:
            # the digital macro did not load: codes 0 / no trip would be meaningless, never count as completed
            with open(log_path, 'a') as lg:
                lg.write('# run status failed (cosim)\n')
            outcome['status'] = 'failed'
            outcome['cosim_failure'] = cosim_bad.group(0)
            err.insert(0, 'COSIM FAILURE: ' + cosim_bad.group(0))
        if failure:
            outcome['solver_failure_diagnostic'] = failure.group(0)
        if a.analysis != 'functional':
            bad = failure or re.search(r'No such vector', out, re.I)
            if a.analysis == 'op':
                values = re.findall(r'^v\((?:vref|isense|gate|vdd|vdda|osc_clk|cmp_clk)\) = (\S+)', out, re.M)
                try:
                    finite_op = len(values) == 7 and all(math.isfinite(float(v)) for v in values)
                except ValueError:
                    finite_op = False
                valid = bool(re.search(r'^No\. of Data Rows\s*:\s*1\s*$', out, re.M) and finite_op)
            else:
                end = re.search(r'^DIAGNOSTIC_PREFIX_END_S\s+([-+0-9.eE]+)', out, re.M)
                outcome['observed_end_s'] = float(end[1]) if end else None
                valid, detail = validate_prefix(out, os.path.join(BUILD, 'waves_%s.txt' % tag), a.tstop * 1e-6)
                outcome['diagnostic_detail'] = detail
            outcome['diagnostic_acceptance'] = 'passed' if outcome['status'] == 'completed' and valid and not bad else ('not run to completion' if outcome['status'] in ('timeout', 'interrupted') else 'failed')
        outcome['observation_checkpoints'] = []
        for t in sorted(set(a.checkpoint_us)):
            cp = os.path.join(BUILD,'checkpoint_%s_%gus.txt' % (tag,t))
            item = dict(requested_s=t*1e-6,status='not run')
            if os.path.exists(cp):
                with open(cp) as f:
                    header=f.readline().split();rows=[list(map(float,line.split())) for line in f if line.strip()]
                valid=bool(rows) and abs(rows[-1][0]-t*1e-6)<1e-12 and all(len(row)==len(header) and all(map(math.isfinite,row)) for row in rows)
                item.update(status='passed' if valid else 'failed',observed_s=rows[-1][0] if rows else None,sha256=sha256(cp),scope='partial saved observations, not functional acceptance or a restart state')
                dst=os.path.join(HERE,'results','waves',os.path.basename(cp))
                decimate(cp,dst,max(1,len(rows)//2000));item['review_copy']=os.path.relpath(dst,ROOT)
            outcome['observation_checkpoints'].append(item)
        atomic_json(os.path.join(HERE, 'logs', tag + '.json'), outcome)
        waves = os.path.join(BUILD, 'waves_%s.txt' % tag)
        if os.path.exists(waves):
            n = sum(1 for _ in open(waves)) - 1
            every = a.decimate or max(1, n // 2000)
            decimate(waves, os.path.join(HERE, 'results', 'waves', tag + '.txt'), every)
        state_wave = os.path.join(BUILD, 'state_%s.txt' % tag)
        if os.path.exists(state_wave):
            decimate(state_wave, os.path.join(HERE, 'results', 'waves', tag + '_state.txt'), every if os.path.exists(waves) else 1)
        outcome['full_waveforms']={}
        for source,kind in [(waves,'analog'),(state_wave,'state')]:
            if os.path.exists(source):
                with open(source,'rb') as f:data=f.read()
                archive=os.path.join(HERE,'results','waves',tag+'_'+kind+'_full.txt.gz')
                with open(archive,'xb') as f:f.write(gzip.compress(data,mtime=0))
                outcome['full_waveforms'][kind]=dict(path=os.path.relpath(archive,ROOT),sha256=hashlib.sha256(data).hexdigest(),gzip_sha256=sha256(archive))
        atomic_json(os.path.join(HERE,'logs',tag+'.json'),outcome)
        with open(os.path.join(HERE, 'results_top.txt'), 'a') as f:
            f.write('== %s | %s; analysis=%s | wall %.0f s, ngspice exit %s\n' % (tag, case['desc'], a.analysis, dt, returncode))
            for l in lines + err[:3]:
                f.write(l + '\n')
        print('== %s (%.0f s)' % (tag, dt))
        for l in lines + err[:3]:
            print(l)
        if outcome['status'] != 'completed' or outcome['diagnostic_acceptance'] == 'failed':
            raise SystemExit(124 if outcome['status'] == 'timeout' else 1)


if __name__ == '__main__':
    main()
