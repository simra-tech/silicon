#!/usr/bin/env python3
"""G1_TOP breaker-path chip-level deck generator and runner (ngspice 46 + Icarus Verilog d_cosim).

Run from the repository root inside the pinned container:

    G1_WORKDIR=designs/g1-guardian/blocks/g1_top/sim flow/run.sh python3 run_top.py [options] CASE [CASE ...]
    G1_WORKDIR=designs/g1-guardian/blocks/g1_top/sim flow/run.sh python3 run_top.py --list

Options: --netlist sch|pex   schematic or kpex post-layout block netlists (default sch)
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
CORNERS = {
    'tt': dict(mos='mos_tt', res='res_typ', cap='cap_typ', hbt='hbt_typ'),
    'ss': dict(mos='mos_ss', res='res_wcs', cap='cap_wcs', hbt='hbt_wcs'),
    'ff': dict(mos='mos_ff', res='res_bcs', cap='cap_bcs', hbt='hbt_bcs'),
}
RTL_FILES = [os.path.join(HERE, 'rtl/g1_dig_cosim.v')] + [
    os.path.join(BLOCKS, 'g1_ctrl/rtl', f) for f in
    ('g1_sync2.v', 'g1_serial.v', 'g1_trip_timer.v', 'g1_regfile.v', 'g1_digital_top.v', 'g1_digital.v')] + [
    os.path.join(BLOCKS, 'g1_seu/rtl', f) for f in ('g1_tmr_reg.v', 'g1_seu_chain.v', 'g1_seu.v')]

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
TEDGE = 2e-9        # edge time of the EN / SCLK / SDI board signals


def edge(t, v0, v1, vio, tedge=None):
    tedge = TEDGE if tedge is None else tedge
    """PWL points of one edge from v0 to v1 (0 or vio) starting at t, with corners at the two bridge
    thresholds scaled to the pad level."""
    # corners 10 mV outside the bridge band, so that the bridge sees a defined 0 at one analog point and a
    # defined 1 at the next (no unknown state, which the RTL would count as a second clock edge)
    lo, hi = (BR_LO - 0.01) * vio / 1.2, (BR_HI + 0.01) * vio / 1.2
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
    return sclk, sdi, t * 1e6   # end time (us)


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


def nodesets(netlist):
    """Operating-point help for the three G1_SENSE OTA loops (from blocks/g1_sense/sim/tb_sense.cir);
    the post-layout netlist is flat, so its OTA-internal nodes are named xota_tail etc."""
    sep = '.' if netlist == 'sch' else '_'
    ns = ['v(vref_buf)=1.04', 'v(vped)=1.0008', 'v(isense)=1.5', 'v(xsense.vp)=0.047', 'v(xsense.vn)=0.047', 'v(iptat)=0.76']
    for o in ('xota', 'xbuf', 'xref'):
        ns += ['v(xsense.%s%sout1)=2.51' % (o, sep), 'v(xsense.%s%smir)=2.51' % (o, sep),
               'v(xsense.%s%stail)=1.6' % (o, sep), 'v(xsense.%s%sfn)=0.2' % (o, sep), 'v(xsense.%s%sfp)=0.2' % (o, sep)]
    return '.nodeset ' + ' '.join(ns)


def build_deck(case, name, netlist, front, temp, corner, tag, tstop_override=None, osc='ideal', inpads='ideal', outpads='beh', method='gear'):
    c = dict(case)
    event_us=c.get('event_us',T_STEP)
    tstop = tstop_override if tstop_override else c['tstop']
    tstep = c.get('tstep', 20e-9)
    powerup = c.get('powerup', False)
    en_tr = c.get('en', [(T_EN, 1)])
    K = CORNERS[corner]
    nl = {k: os.path.join(BLOCKS, v) for k, v in NETLISTS[netlist].items()}
    vio = 3.3
    B = BEH[netlist]
    # supplies: DC for functional cases (operating point start), PWL ramps for the power-up cases
    if powerup:
        r33, r12 = c['ramp33'], c['ramp12']
        v33 = pwl([(0, 0), (r33[0] * 1e-6, 0), (r33[1] * 1e-6, 3.3)])
        v12 = pwl([(0, 0), (r12[0] * 1e-6, 0), (r12[1] * 1e-6, 1.2)])
    else:
        v33, v12 = 'dc 3.3', 'dc 1.2'
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
    vvp = os.path.join(BUILD, 'g1_dig_cosim.vvp')
    rpd = c.get('rpd')

    L = []
    A = L.append
    A('* G1_TOP breaker path, chip level: %s' % c['desc'])
    A('* case %s | block netlists %s | front end %s | clock to the RTL %s | corner %s (%s %s %s %s) | %g degC | run_top.py' %
      (name, netlist, front, osc, corner, K['mos'], K['res'], K['cap'], K['hbt'], temp))
    A('.param VDDA=3.3 VDD=1.2 IOVDD=3.3 RSH=25m RGND=10m INOM=%g CVREF=%g' % (INOM, CVREF))
    A('.lib %s/cornerMOSlv.lib %s' % (MODELS, K['mos']))
    A('.lib %s/cornerMOShv.lib %s' % (MODELS, K['mos']))
    A('.lib %s/cornerRES.lib %s' % (MODELS, K['res']))
    A('.lib %s/cornerCAP.lib %s' % (MODELS, K['cap']))
    A('.lib %s/cornerHBT.lib %s' % (MODELS, K['hbt']))
    A('.lib %s/cornerDIO.lib dio_tt' % MODELS)
    A('.include %s' % IOSPI)
    if front == 'tl':
        for k in ('bgr', 'sense', 'trip', 'osc', 'gate'):
            if (k == 'trip' and c.get('notrip')) or (k == 'osc' and osc != 'tl'):
                continue
            A('.include %s' % nl[k])
    else:
        A('.include %s' % nl['gate'])
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
        A(nodesets(netlist))
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
            A('Ben_core en_core 0 V = v(en_pad)*1.2/3.3')
            A('Bsclk_core sclk_core 0 V = v(sclk_pad)*1.2/3.3')
            A('Bsdi_core sdi_core 0 V = v(sdi_pad)*1.2/3.3')
        if outpads == 'model':
            A('XPG gate gate_core vdd 0 iovdd 0 sg13g2_IOPadOut30mA')
            A('XPF fault_n fault_core vdd 0 iovdd 0 sg13g2_IOPadOut4mA')
        else:
            A('* GATE / FAULT_N output pads as behavioural drivers fitted to the g1_gate block results with the PDK pad')
            A('* models (30 mA pad: 5 nF + 10 Ohm, fall 90-10 % 606 ns, arming 0-90 % 677 ns -> 47 Ohm driver; 4 mA pad:')
            A('* 20 pF, ~500 Ohm). Reason: README, "Numerical notes" (pad models and the StrongARM comparators need')
            A('* incompatible integration settings). The driver switches within 1 ns of gate_core / fault_core and')
            A('* draws its current from IOVDD.')
            A('Bgate_drv gate_drv 0 V = v(iovdd)*(0.5 + 0.5*tanh((v(gate_core) - 0.6)/0.05))')
            A('Rgate_drv gate_drv gate 47')
            A('Bgate_i iovdd 0 I = max(0, (v(gate_drv) - v(gate))/47)')
            A('Bfault_drv fault_drv 0 V = v(iovdd)*(0.5 + 0.5*tanh((v(fault_core) - 0.6)/0.05))')
            A('Rfault_drv fault_drv fault_n 500')
    else:
        A('* ---- minimal chip context (README, case osc): no pad models, no G1_GATE; the 3.3 V pad inputs are scaled to 1.2 V')
        A('Cvref_ext vref 0 1p')
        A('Ben_core en_core 0 V = v(en_pad)*1.2/3.3')
        A('Bsclk_core sclk_core 0 V = v(sclk_pad)*1.2/3.3')
        A('Bsdi_core sdi_core 0 V = v(sdi_pad)*1.2/3.3')
        A('Bgate gate 0 V = 3.3*(0.5 + 0.5*tanh((v(en_core) - 0.6)/0.05))')
        A('Vfault fault_n 0 dc 3.3')
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
            A('Vcs_tie cmp_soft 0 dc %g' % (1.2 if c.get('cmp_soft_high') else 0.0))
            A('Vch_tie cmp_hard 0 dc 0')
            A('Rtripa_dummy vdda_trip 0 1e12')
            A('Rtripd_dummy vdd_trip 0 1e12')
            A('Bicmp icmp 0 V = v(isense)/2')
            A('Vvths vth_soft 0 dc %g' % (B['vref'] * (255 + 153) / 530.0))
            A('Vvthh vth_hard 0 dc %g' % (B['vref'] * (255 + 254) / 530.0))
            icmp, vths, vthh = 'v(icmp)', 'v(vth_soft)', 'v(vth_hard)'
        A('Cw_soft cmp_soft 0 20f')
        A('Cw_hard cmp_hard 0 20f')
        A('Vm_osc vdd vdd_osc dc 0')
        if osc == 'tl':
            A('XOSC osc_en_g trim0 trim1 trim2 trim3 osc_clk vdd_osc 0 g1_osc')
            A('Cw_clk osc_clk 0 100f')
        else:
            A('* the clock delivered to the digital macro is an ideal source at the block-simulated G1_OSC frequency;')
            A('* G1_OSC is not in this deck (README, "Numerical notes": with the transistor-level oscillator on the')
            A('* chip supply the event-driven solver aborts; case osc runs it in the chip context without G1_TRIP)')
            A('Rosc_dummy vdd_osc 0 1e12')
            A('Vosc_i osc_i 0 pulse(0 1.2 %g 1n 1n %g %g)' % (T_OSC * 1e-6, 0.5 / B['fosc'] - 1e-9, 1.0 / B['fosc']))
            A('Bosc_clk osc_clk 0 V = v(osc_i) * (0.5 + 0.5*tanh((v(osc_en_g) - 0.6)/0.05))')
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
        A('Bcs cs 0 V = ' + ' + '.join('%d*(0.5 + 0.5*tanh((v(soft%d) - 0.6)/0.05))' % (1 << i, i) for i in range(8)))
        A('Bch ch 0 V = ' + ' + '.join('%d*(0.5 + 0.5*tanh((v(hard%d) - 0.6)/0.05))' % (1 << i, i) for i in range(8)))
        A('* comparator decisions as smooth (2 mV wide) functions of the input difference, sampled by ideal flip-flops')
        A('Bcmps cmps_a 0 V = 0.6 + 0.6*tanh((v(icmp) - v(vth_soft))/2m)')
        A('Bcmph cmph_a 0 V = 0.6 + 0.6*tanh((v(icmp) - v(vth_hard))/2m)')
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
        A('* G1_OSC: ideal square wave at the block-simulated frequency, gated by the enable')
        A('Vosc_i osc_i 0 pulse(0 1.2 %g 1n 1n %g %g)' % (T_OSC * 1e-6, 0.5 / B['fosc'] - 1e-9, 1.0 / B['fosc']))
        A('Bosc_clk osc_clk 0 V = v(osc_i) * (0.5 + 0.5*tanh((v(osc_en_g) - 0.6)/0.05))')
        A('Vm_osc vdd vdd_osc dc 0')
        A('Rosc_dummy vdd_osc 0 1e12')
        icmp, vths, vthh = 'v(icmp)', 'v(vth_soft)', 'v(vth_hard)'
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
    A('.model adc_clock adc_bridge(in_low=0.6 in_high=0.6 rise_delay=1e-12 fall_delay=1e-12)')
    A('.model dac dac_bridge(out_low=0 out_high=1.2 out_undef=0.6 t_rise=0.3n t_fall=0.3n)')
    A('.model rtl d_cosim simulation="ivlng" sim_args=["%s"]' % vvp)
    A('aclock [osc_clk] [d_osc_clk] adc_clock')
    A('aadc [cmp_soft cmp_hard tripped] [d_cmp_soft d_cmp_hard d_tripped] adc')
    outs = (['d_cmp_clk'] + ['d_s%d' % i for i in range(7, -1, -1)] + ['d_h%d' % i for i in range(7, -1, -1)] +
            ['d_trip_d', 'd_clr_d', 'd_fast_en', 'd_osc_en'] + ['d_t%d' % i for i in range(3, -1, -1)] +
            ['d_trip', 'd_gate_en', 'd_cause1', 'd_cause0', 'd_sdo'] + ['d_sp%d' % i for i in range(15, -1, -1)] + ['d_inrush', 'd_softarmed'])
    A('adig [d_osc_clk d_en d_sclk d_sdi d_cmp_soft d_cmp_hard d_tripped] [%s] rtl' % ' '.join(outs))
    an = (['cmp_clk'] + ['soft%d' % i for i in range(7, -1, -1)] + ['hard%d' % i for i in range(7, -1, -1)] +
          ['trip_d', 'clr_d', 'fast_en', 'osc_en'] + ['trim%d' % i for i in range(3, -1, -1)] +
          ['dig_trip', 'dig_gate_en', 'cause1', 'cause0', 'sdo'] + ['sp%d' % i for i in range(15, -1, -1)] + ['inrush_active', 'soft_armed'])
    A('adac [%s] [%s] dac' % (' '.join(outs), ' '.join(an)))
    A('.save v(gate) v(gfet) v(tripped) v(isense) v(cmp_soft) v(cmp_hard) v(trip_d) v(clr_d) v(fast_en) v(osc_clk) v(cmp_clk)')
    A('+ v(vref) v(iptat) v(en_core) v(shp) v(shn) v(fault_n) v(gate_core) v(vdda) v(vdd) v(iovdd) v(iprof) v(osc_en_g)')
    A('+ %s %s %s v(dig_trip) v(cause1) v(cause0) v(sclk_pad) v(sdi_pad) v(sdo)' % (icmp, vths, vthh))
    A('+ ' + ' '.join('v(soft%d)' % i for i in range(8)) + ' ' + ' '.join('v(hard%d)' % i for i in range(8)))
    A('+ ' + ' '.join('v(sp%d)' % i for i in range(16)) + ' v(inrush_active) v(soft_armed)')
    A('+ i(vim) i(vma) i(vmi) i(v12) i(vm_bgr) i(vm_sense) i(vm_tripa) i(vm_tripd) i(vm_osc) i(vm_gatea) i(vm_gated)')
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
        A('* quiet operating values after the register write(s)')
        A('meas tran vref_q find v(vref) at=%gu' % tq)
        A('meas tran isense_q find v(isense) at=%gu' % tq)
        A('meas tran icmp_q find %s at=%gu' % (icmp, tq))
        A('meas tran vths_q find %s at=%gu' % (vths, tq))
        A('meas tran vthh_q find %s at=%gu' % (vthh, tq))
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
        A('echo "QUIET vref=" $&vref_q " isense=" $&isense_q " icmp=" $&icmp_q " vth_soft=" $&vths_q " vth_hard=" $&vthh_q " iload_A=" $&iload_q " gate=" $&gate_q " code_soft=" $&code_soft " code_hard=" $&code_hard " fast_en=" $&fastq " inrush_active=" $&inrush_q " t_inrush_off_us=" $&t_inrush_off_us " soft_armed_end=" $&softarmed_end')
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
            sign = '-' if src == 'v12' else ''
            A('let i_%s = %si(%s)' % (nm, sign, src))
            A('meas tran ia_%s avg i_%s from=%gu to=%gu' % (nm, nm, quiet[0], quiet[1]))
            A('let ua_%s = ia_%s*1e6' % (nm, nm))
        A('echo "SUPPLY_uA window=%g-%gus VDDA=" $&ua_vdda " IOVDD=" $&ua_iovdd " VDD=" $&ua_vdd " | bgr=" $&ua_bgr " sense=" $&ua_sense " trip_3v3=" $&ua_tripa " trip_1v2=" $&ua_tripd " osc=" $&ua_osc " gate_3v3=" $&ua_gatea " gate_1v2=" $&ua_gated' % (quiet[0], quiet[1]))
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
            A('meas tran t_g_rearm when v(gate)=2.97 rise=1 from=%gu' % t_on)
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


def compile_rtl(log):
    os.makedirs(BUILD, exist_ok=True)
    vvp = os.path.join(BUILD, 'g1_dig_cosim.vvp')
    cmd = ['iverilog', '-g2005', '-Wall', '-Wno-timescale', '-o', vvp] + RTL_FILES
    r = subprocess.run(cmd, capture_output=True, text=True)
    log.write('# %s\n%s%s' % (' '.join(cmd), r.stdout, r.stderr))
    if r.returncode != 0:
        raise SystemExit('iverilog failed:\n' + r.stdout + r.stderr)
    for f in RTL_FILES:
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
    ap.add_argument('--inpads', default='ideal', choices=('ideal', 'model'), help='EN/SCLK/SDI input pads: ideal level copies (default) or the PDK sg13g2_IOPadIn models')
    ap.add_argument('--outpads', default=None, choices=('beh', 'model'), help='GATE/FAULT_N pads: behavioural drivers fitted to the g1_gate results (default for the transistor-level front end) or the PDK models (default for the behavioural front end and the power-up cases)')
    ap.add_argument('--method', default=None, choices=('gear', 'trap'), help='integration method (default: trap for the transistor-level front end, gear otherwise)')
    ap.add_argument('--accuracy', choices=('baseline', 'tight'), default='baseline',
                    help='tight comparator qualification: reltol1e-5, abstol1e-14, vntol1e-7; baseline remains unchanged')
    ap.add_argument('--maxstep-ns', type=float, default=None, help='explicit transient maximum step in ns for numerical qualification')
    ap.add_argument('--timeline',choices=('baseline','compact'),default='baseline',help='compact c_mid only: serial4us,fault16us,stop28us; SEU fill not qualified')
    ap.add_argument('--checkpoint-us',type=float,nargs='+',default=[],help='save partial observations then resume within the same running simulator; not restart checkpoints')
    ap.add_argument('--dry', action='store_true')
    ap.add_argument('--tedge', type=float, default=None, help='edge time of EN/SCLK/SDI (s), default 2 ns')
    ap.add_argument('--event-shift-ns', type=float, default=0,
                    help='baseline c_mid/hard_pulse fault-only phase shift0..500ns')
    ap.add_argument('--list', action='store_true')
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
    run_id = a.run_id or time.strftime('%Y%m%dT%H%M%SZ', time.gmtime()) + '_' + uuid.uuid4().hex[:8]
    global TEDGE, T_SER, T_STEP, CASES
    if a.timeline == 'compact':
        if a.cases != ['c_mid'] or a.analysis != 'functional':
            ap.error('compact timeline supports c_mid functional only')
        T_SER,T_STEP=4.0,16.0
        CASES=make_cases()
        CASES['c_mid']['tstop']=28
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
        if a.event_shift_ns and a.tstop is not None:
            ap.error('fault phase shift preserves the baseline endpoint')
        if a.accuracy == 'tight':
            case['tol'] = 'reltol=1e-5 abstol=1e-14 vntol=1e-7 chgtol=1e-14'
        if a.maxstep_ns is not None:
            case['tmax'] = a.maxstep_ns * 1e-9
        front = a.front or case.get('front', 'tl')
        osc = a.osc or case.get('osc', 'ideal')
        tag = '%s_%s_%s_%s_%gC' % (name, a.netlist, front, a.corner, a.temp) + ('_osctl' if osc == 'tl' and name != 'osc' else '') + ('_inpads' if a.inpads == 'model' else '') + ('_outpads' if a.outpads == 'model' and front == 'tl' else '') + ('_%s' % a.method if a.method else '')
        tag += '_clockfix'
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
        tag += '_' + a.analysis + '_' + run_id
        for directory, ext in ((BUILD, '.cir'), (os.path.join(HERE, 'logs'), '.log'), (os.path.join(HERE, 'logs'), '.json'), (os.path.join(HERE, 'decks'), '.cir')):
            if os.path.exists(os.path.join(directory, tag + ext)):
                raise SystemExit('refusing to overwrite evidence: ' + tag)
        outpads = a.outpads or ('beh' if front == 'tl' and not case.get('powerup') else 'model')
        inpads = a.inpads if a.inpads != 'ideal' or not case.get('inpads') else case['inpads']
        method = a.method or ('trap' if front == 'tl' and not case.get('powerup') else 'gear')
        deck = build_deck(case, name, a.netlist, front, a.temp, a.corner, tag, a.tstop, osc, inpads, outpads, method)
        if a.analysis != 'functional':
            deck = diagnostic_deck(deck, a.analysis, a.tstop, tag)
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
            for k, v in NETLISTS[a.netlist].items():
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
            compile_rtl(log)
            log.flush()
            inputs = set(RTL_FILES)
            for source in NETLISTS[a.netlist].values():
                directory = os.path.dirname(os.path.join(BLOCKS, source))
                inputs.update(os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.spice'))
            meta = dict(tag=tag, analysis=a.analysis, options=vars(a),
                        effective=dict(front=front, osc=osc, inpads=inpads, outpads=outpads, method=method,
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
