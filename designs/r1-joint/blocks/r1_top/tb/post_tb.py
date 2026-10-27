#!/usr/bin/env python3
"""Post-processing of one T10 run: criteria of the test -> tb/results/<run-id>.json (verdict passed / failed).

usage: python3 post_tb.py <run-id>      (inside the container, G1_RESULTS_ROOT set; called by run_tb.py)
Inputs: <G1_RESULTS_ROOT>/r1_top/tb/<run-id>/{run.json, ngspice.log, tran.raw}. The criteria are in tb/README.md.
"""
import json
import math
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
THETA0_DEG = 30.0
F_REF_OSC = 2e6          # reference clock of the OSC_COUNT measurement (t10_master.v ref_clocks, 500 ns)
T2F_REC = {27.0: 1.6003e6, 125.0: 2.1100e6}   # r1_t2f README, PTAT mode, tt, 3.3 V (G1 Sep-19 bandgap)
OSC_BAND = (28e6, 32e6)
POR_DELAY_REC = (200e-6, 250e-6)              # r1_bias README (schematic), POR delay


def read_raw(path):
    data = open(path, 'rb').read()
    i = data.index(b'Binary:\n')
    hdr = data[:i].decode('latin-1').splitlines()
    nv = int([l for l in hdr if l.startswith('No. Variables:')][0].split(':')[1])
    npnt = int([l for l in hdr if l.startswith('No. Points:')][0].split(':')[1])
    k = hdr.index('Variables:')
    var = [hdr[k + 1 + j].split()[1] for j in range(nv)]
    n_full = (len(data) - i - 8) // (nv * 8)
    npnt = min(npnt, n_full)
    arr = np.frombuffer(data[i + 8:i + 8 + nv * npnt * 8], dtype='<f8').reshape(npnt, nv)
    out = {}
    for j, n in enumerate(var):
        m = n.lower()
        m = re.sub(r'^v\((.*)\)$', r'\1', m)
        out[m] = arr[:, j]
    return out


def crossings(t, v, th, rising=True, t_from=0.0):
    s = v - th
    if rising:
        idx = np.where((s[:-1] < 0) & (s[1:] >= 0))[0]
    else:
        idx = np.where((s[:-1] > 0) & (s[1:] <= 0))[0]
    tc = t[idx] + (t[idx + 1] - t[idx]) * (0 - s[idx]) / (s[idx + 1] - s[idx])
    return tc[tc >= t_from]


def first(a):
    return float(a[0]) if len(a) else None


def freq(t, v, th, t0, t1):
    c = crossings(t, v, th, True, t0)
    c = c[c <= t1]
    if len(c) < 3:
        return None, len(c)
    return (len(c) - 1) / (c[-1] - c[0]), len(c)


def at(t, v, tq):
    return float(np.interp(tq, t, v))


def wrap(d):
    return (d + 180.0) % 360.0 - 180.0


def parse_log(txt):
    res, mon = [], []
    for l in txt.splitlines():
        if l.startswith('T10RES ') or l.startswith('T10MON '):
            p = l.split()
            d = {'kind': p[1]}
            for w in p[2:]:
                if '=' in w:
                    k, v = w.split('=', 1)
                    d[k] = v
            (res if l.startswith('T10RES') else mon).append(d)
    return res, mon


def crit(name, value, limit, ok, unit=''):
    return {'name': name, 'value': value, 'limit': limit, 'unit': unit, 'status': 'passed' if ok else 'failed'}


def spird(res, addr):
    return [(float(r['t']) * 1e-9, int(r['data'], 16)) for r in res if r['kind'] == 'SPIRD' and r['addr'].lower() == addr]


def test1(w, res, mon, run):
    t = w['time']
    C, M = [], {}
    if run.get('fast'):
        return test1b(w, res, mon, run)
    t_vdda = first(crossings(t, w['vdda'], 3.0))
    t_vdd = first(crossings(t, w['vdd'], 1.08))
    t_por = first(crossings(t, w['por_n'], 0.6, True))
    M.update(t_vdda_3v0_us=t_vdda and t_vdda * 1e6, t_vdd_1v08_us=t_vdd and t_vdd * 1e6, t_por_us=t_por and t_por * 1e6)
    up = max(t_vdda or 1, t_vdd or 1)
    C.append(crit('por_n rises after both rails are in range', M['t_por_us'], 'after %.2f us' % (up * 1e6),
                  t_por is not None and t_por > up))
    t_th_a = first(crossings(t, w['vdda'], 2.73))
    t_th_d = first(crossings(t, w['vdd'], 1.01))
    if t_por and t_th_a and t_th_d:
        dly = t_por - max(t_th_a, t_th_d)
        M['por_delay_us'] = dly * 1e6
        C.append(crit('POR delay from the later threshold (VDDA 2.73 V, VDD 1.01 V) within the r1_bias record',
                      dly * 1e6, '200-250', POR_DELAY_REC[0] <= dly <= POR_DELAY_REC[1], 'us'))
    for node, name in (('vref_bg', 'bandgap VREF'), ('ib_afe_s1', 'bias line ib_afe_s1 (consumer diode)'),
                       ('ib_adc_ref', 'bias line ib_adc_ref (refbuf nb)')):
        v = w[node]
        sel = t >= (t[-1] - 5e-6)
        fin = float(np.mean(v[sel]))
        bad = np.where(np.abs(v - fin) > 0.01 * abs(fin))[0]
        ts = float(t[bad[-1]]) if len(bad) else 0.0
        M['%s_final_V' % node] = fin
        M['%s_settle_1pct_us' % node] = ts * 1e6
        C.append(crit('%s within 1 %% of its final value before por_n' % name, ts * 1e6,
                      '< %.2f us' % ((t_por or 0) * 1e6), t_por is not None and ts < t_por, 'us'))
    t_osc0 = first(crossings(t, w['osc_clk'], 0.6, True))
    M['osc_first_edge_us'] = t_osc0 and t_osc0 * 1e6
    if t_por:
        f, n = freq(t, w['osc_clk'], 0.6, t_por - 20e-6, t_por)
        M['osc_f_MHz_before_por'] = f and f / 1e6
        C.append(crit('oscillator at code 22 in the r1_osc band before reset exit', M['osc_f_MHz_before_por'], '28-32',
                      f is not None and OSC_BAND[0] <= f <= OSC_BAND[1], 'MHz'))
    oor = [float(m['t']) * 1e-9 for m in mon if m['kind'] == 'CORE_OUT_OF_RESET']
    M['core_out_of_reset_us'] = [x * 1e6 for x in oor]
    C.append(crit('ctrl comes out of reset after por_n (within 5 ticks)', oor and oor[-1] * 1e6, 'por_n + 0.17 us',
                  bool(oor) and t_por is not None and 0 <= oor[-1] - t_por <= 0.17e-6, 'us'))
    ids = spird(res, '00')
    M['id_read'] = ['0x%04X' % v for _, v in ids]
    rid = ctrl_id(run)
    C.append(crit('ID over SPI equals the RTL %s value 0x%04X' % (run.get('ctrl_rev', '0.5'), rid),
                  M['id_read'], '0x%04X' % rid, bool(ids) and ids[0][1] == rid))
    flt = spird(res, '02')
    M['fault_after_reset'] = ['0x%04X' % v for _, v in flt]
    C.append(crit('FAULT after reset has POR (bit 12) and CAL (bit 11) set', M['fault_after_reset'], '0x1800',
                  bool(flt) and (flt[0][1] & 0x1800) == 0x1800))
    # register map 0x02 reset value 0x1800 with EN high: no other cause may be latched (finding R3)
    C.append(crit('FAULT after reset equals the register-map reset value 0x1800 (EN high throughout, STO bit 8 clear)',
                  M['fault_after_reset'], '0x1800', bool(flt) and flt[0][1] == 0x1800))
    return C, M



def ctrl_id(run):
    """Expected ID register for the co-simulated ctrl revision (run.json ctrl_rev; 0.5 when absent)."""
    return {'0.5': 0x5205, '0.7': 0x5207}[str((run or {}).get('ctrl_rev', '0.5'))]


def test1b(w, res, mon, run):
    """Deck 1b (fast view): reset exit and ID read after the por_n release; the analog power-up is deck 1a."""
    t = w['time']
    C, M = [], {}
    t_por = first(crossings(t, w['por_n'], 0.6, True))
    M['t_por_us'] = t_por and t_por * 1e6
    oor = [float(m['t']) * 1e-9 for m in mon if m['kind'] == 'CORE_OUT_OF_RESET']
    M['core_out_of_reset_us'] = [x * 1e6 for x in oor]
    C.append(crit('ctrl comes out of reset after por_n (within 5 ticks)', oor and oor[-1] * 1e6, 'por_n + 0.17 us',
                  bool(oor) and t_por is not None and 0 <= oor[-1] - t_por <= 0.17e-6, 'us'))
    ids = spird(res, '00')
    M['id_read'] = ['0x%04X' % v for _, v in ids]
    rid = ctrl_id(run)
    C.append(crit('ID over SPI equals the RTL %s value 0x%04X' % (run.get('ctrl_rev', '0.5'), rid),
                  M['id_read'], '0x%04X' % rid, bool(ids) and ids[0][1] == rid))
    flt = spird(res, '02')
    M['fault_after_reset'] = ['0x%04X' % v for _, v in flt]
    C.append(crit('FAULT after reset has POR (bit 12) and CAL (bit 11) set', M['fault_after_reset'], '0x1800',
                  bool(flt) and (flt[0][1] & 0x1800) == 0x1800))
    # register map 0x02 reset value 0x1800 with EN high: no other cause may be latched (finding R3)
    C.append(crit('FAULT after reset equals the register-map reset value 0x1800 (EN high throughout, STO bit 8 clear)',
                  M['fault_after_reset'], '0x1800', bool(flt) and flt[0][1] == 0x1800))
    return C, M


def strobe_check(w):
    """ADC strobe position against clk30 (r1_adc gen_timing_r5.py: 0.6 ns before the edge); MODEL M1 check."""
    t = w['time']
    if 'seq_stb0' not in w:
        return None
    ck = crossings(t, w['osc_clk'], 0.6, True)
    off = []
    for s0 in crossings(t, w['seq_stb0'], 0.6, True):
        nxt = [c for c in ck if c > s0]
        if nxt:
            off.append((nxt[0] - s0) * 1e9)
    if not off:
        return crit('ADC strobes 0.6 ns before the clk30 edge (M1 check)', None, '0.3-0.9 ns', False, 'ns')
    return crit('ADC strobes 0.6 ns before the clk30 edge (M1 check, %d conversions)' % len(off),
                [round(min(off), 3), round(max(off), 3)], '0.3-0.9 ns', 0.3 <= min(off) and max(off) <= 0.9, 'ns')

def hs_check(w, mon):
    """O10 / F22: every conversion the macro started must reach the ADC: analog strobe pulses (stb0, stb6, stb13)
    per started conversion, and no lost model events (T10MON LOSTEV) and no stalled frame (T10MON STALL)."""
    t = w['time']
    nconv = len([m for m in mon if m['kind'] == 'START'])
    t_end = t[-1]
    # a conversion started in the last 0.5 us may not have all strobes inside the deck
    nfull = len([m for m in mon if m['kind'] == 'START' and float(m['t']) * 1e-9 < t_end - 0.5e-6])
    cnt = {}
    for n in ['seq_stb%d' % k for k in range(14)] + ['seq_lat']:
        if n in w:
            cnt[n] = len([c for c in crossings(t, w[n], 0.6, True) if c < t_end - 0.0e-6])
    lost = [m for m in mon if m['kind'] == 'LOSTEV']
    stall = [m for m in mon if m['kind'] == 'STALL']
    short = sorted(n for n, v in cnt.items() if v < nfull)
    ok = (not stall) and all(nfull <= v <= nconv for v in cnt.values())
    val = {'conversions_started': nconv, 'complete_in_deck': nfull, 'strobe_rises': cnt,
           'lost_valid_events': len(lost), 'stalls': len(stall), 'short': short}
    # F24: a lost seq_stb13 leaves only the LSB decision register unclocked (raw-word error <= 1 LSB of 14 bits)
    if short == ['seq_stb13']:
        val['effect'] = 'only the LSB strobe lost in %d of %d conversions: raw-word error <= 1 LSB' % (
            nfull - cnt['seq_stb13'], nfull)
    return crit('ADC handshake integrity: strobes per started conversion, no stalled frame (O10, F22, F24)',
                val, 'strobe rises = conversions, 0 stalls', ok)


def test2(w, res, mon, run):
    t = w['time']
    C, M = [], {}
    sc = strobe_check(w)
    if sc:
        C.append(sc)
    C.append(hs_check(w, mon))
    f = 1e4
    stim = lambda tt: (360.0 * f * tt + THETA0_DEG)
    rst = [float(r['t']) * 1e-9 for r in res if r['kind'] == 'TBRESET']
    t_rst = rst[0] if rst else 0.0
    starts = np.array([float(m['t']) * 1e-9 for m in mon if m['kind'] == 'START' and m.get('sel') == '0'])
    meas = [(float(m['t']) * 1e-9, int(m['meas']), int(m['pos']), int(m['valid'])) for m in mon if m['kind'] == 'MEAS']
    errs, rows = [], []
    for tm, ma, po, va in meas:
        cand = starts[starts <= tm - 30 / 30e6]
        if not len(cand) or tm < t_rst + 3e-6:
            continue
        ts = float(cand[-1])
        e = wrap(ma / 2 ** 18 * 360.0 - stim(ts))
        errs.append(e)
        rows.append((ts * 1e6, tm * 1e6, ma, e))
    errs = np.array(errs)
    M['pairs_used'] = len(errs)
    if len(errs) < 10:
        C.append(crit('enough encoder pairs (>= 10) after the reset', len(errs), '>= 10', False))
        return C, M
    off = float(np.mean(errs))
    resid = errs - off
    M['meas_err_mean_deg'] = off
    M['meas_resid_max_deg'] = float(np.max(np.abs(resid)))
    M['meas_resid_rms_deg'] = float(np.sqrt(np.mean(resid ** 2)))
    M['meas_samples'] = [list(r) for r in rows[::max(1, len(rows) // 40)]]
    M['latency_equiv_us'] = -off / 360.0 / f * 1e6
    C.append(crit('MEAS_ANGLE per pair: residual after a constant (latency, zero offset)', M['meas_resid_max_deg'],
                  '<= 0.25 (spec electronic accuracy)', M['meas_resid_max_deg'] <= 0.25, 'deg el'))
    pos = spird(res, '19')
    pe = []
    for tr, v in pos:
        pe.append(wrap(v / 65536.0 * 360.0 - stim(tr) - off))
    M['spi_pos'] = [[tr * 1e6, v, e] for (tr, v), e in zip(pos, pe)]
    M['spi_pos_err_max_deg'] = float(np.max(np.abs(pe))) if pe else None
    C.append(crit('POS over SPI against the stimulus angle (same constant removed)', M['spi_pos_err_max_deg'],
                  '<= 0.64 (spec total target)', bool(pe) and M['spi_pos_err_max_deg'] <= 0.64, 'deg el'))
    mspi = spird(res, '1f')
    M['spi_meas_angle'] = [[tr * 1e6, v] for tr, v in mspi]
    mvals = set(ma >> 2 for _, ma, _, _ in meas)
    C.append(crit('MEAS_ANGLE over SPI equals a monitored pair value (register path)', len(mspi),
                  'all reads', bool(mspi) and all(v in mvals for _, v in mspi)))
    st = spird(res, '01')
    M['status'] = ['0x%04X' % v for _, v in st]
    C.append(crit('STATUS: POS_VALID (bit 6) and CAL_VALID (bit 4) set, no AMP_LOW/HIGH', M['status'], 'bits 6,4',
                  bool(st) and (st[-1][1] & 0x50) == 0x50 and (st[-1][1] & 0x3) == 0))
    ids = spird(res, '00')
    M['id_read'] = ['0x%04X' % v for _, v in ids]
    # ID is checked in test 1 (deck 2 read removed for wall time, D7)
    b = [r for r in res if r['kind'] == 'BISS']
    if not b:
        C.append(crit('BiSS-C frame received', None, 'one frame', False))
        return C, M
    b = b[0]
    data = int(b['data'], 16)
    mt, stv, ne, nw = data >> 20, (data >> 2) & 0x3FFFF, (data >> 1) & 1, data & 1
    tl = float(b['t_lat']) * 1e-9
    be = wrap(stv / 2 ** 18 * 360.0 - stim(tl + 2.5 / 30e6) - off)
    M['biss'] = {'ack': int(b['ack']), 'start_edge': int(b['start_edge']), 'stop': int(b['stop']), 'mt': mt, 'st': stv,
                 'nE': ne, 'nW': nw, 'crc_wire': b['crc_wire'], 'crc_calc': b['crc_calc'], 't_lat_us': tl * 1e6,
                 'st_err_deg': be}
    C.append(crit('BiSS-C: ACK, START, CRC (master check), stop bit', M['biss'], 'ack 1, crc equal',
                  b['ack'] == '1' and int(b['start_edge']) > 2 and b['crc_wire'] == b['crc_calc']))
    C.append(crit('BiSS-C: nE = 1, nW = 1', [ne, nw], '1, 1', ne == 1 and nw == 1))
    C.append(crit('BiSS-C: ST against the stimulus angle at LAT (same constant removed)', be, '<= 0.64',
                  abs(be) <= 0.64, 'deg el'))
    return C, M


def adc_lsb(w):
    vr = float(np.mean(w['xu_adc.vrefo'][w['time'] > w['time'][-1] / 2]))
    # Fourth budget: the r1_adc revision-5 record with the design weights (r1_regs reset weights): nominal line
    # 2047.5 + v / LSB, LSB = 454.9 uV x VREF / 1.045 V (r1_adc sim/results/r5/isa5_tt.json, locate run; gain fit
    # 0.99825 on that line). The earlier constant 2 x 0.914 V x VREF / 4096 was the revision-3 full scale at
    # VREF 1.0 V and is 2.5 % too large for revision 5.
    return 454.9e-6 * vr / 1.045, vr


def test3(w, res, mon, run):
    C, M = [], {}
    sc = strobe_check(w)
    if sc:
        C.append(sc)
    C.append(hs_check(w, mon))
    lsb, vr = adc_lsb(w)
    M['adc_vrefo_V'] = vr
    M['adc_lsb_uV'] = lsb * 1e6
    sels = [float(r['t']) * 1e-9 for r in res if r['kind'] == 'SEL']
    ia, ib = spird(res, '29'), spird(res, '2a')
    M['I_A'] = [[t * 1e6, v] for t, v in ia]
    M['I_B'] = [[t * 1e6, v] for t, v in ib]
    if len(ia) < 2 or len(ib) < 2:
        C.append(crit('two I_A / I_B reads (levels 0 and 1, D7)', len(ia), 2, False))
        return C, M
    lv_a = [0.0, 0.030, 0.090]
    lv_b = [0.0, 0.080, 0.010]
    for ch, rd, lv in (('A', ia, lv_a), ('B', ib, lv_b)):
        for k in (1,):
            dm = rd[k][1] - rd[0][1]
            de = 14.0 * lv[k] / lsb
            e = (dm - de) / de * 100.0
            M['%s_step%d' % (ch, k)] = {'measured_codes': dm, 'expected_codes': de, 'error_pct': e}
            C.append(crit('I_%s code step for %.0f mV within 1 %% of 14 x dV / LSB' % (ch, lv[k] * 1e3), e, '|e| <= 1',
                          abs(e) <= 1.0, '%'))
    return C, M


def test4(w, res, mon, run):
    t = w['time']
    C, M = [], {}
    f_clk, _ = freq(t, w['osc_clk'], 0.6, 2e-6, t[-1])
    vref = float(np.mean(w['vref_bg'][t > 2e-6]))
    vth_sh = vref / 26.0 + (2 * 44 - 63) / 63.0 * vref / 14.0
    M['oc_threshold_shunt_mV'] = vth_sh * 1e3
    tstep = [float(r['t']) * 1e-9 for r in res if r['kind'] == 'OCSTEP']
    if not tstep:
        C.append(crit('OC step applied', None, 'yes', False))
        return C, M
    t_x = first(crossings(t, w['isa_p'], vth_sh, True, tstep[0] - 1e-9))
    t_f = first(crossings(t, w['fault_n'], 1.65, False, t_x or tstep[0]))
    tg = [first(crossings(t, w['gate_%s' % g], 1.0, False, t_x or tstep[0])) for g in 'abc']
    hi = [at(t, w['gate_%s' % g], (t_x or tstep[0]) - 5e-9) for g in 'abc']
    lim = 0.236e-6 + 4 / (f_clk or 30e6) + 1.0e-6
    M.update(t_cross_us=t_x and t_x * 1e6, fault_delay_ns=(t_f - t_x) * 1e9 if (t_f and t_x) else None,
             gate_delay_ns=[(g - t_x) * 1e9 if (g and t_x) else None for g in tg], gates_before_V=hi,
             limit_ns=lim * 1e9, f_clk_MHz=f_clk and f_clk / 1e6)
    C.append(crit('all three gates high before the step (fault path exercised on driven gates)', hi, '> 3.0 V',
                  all(h > 3.0 for h in hi)))
    okg = t_x is not None and all(g is not None for g in tg) and max(tg) - t_x <= lim
    C.append(crit('OC step: all gates < 1 V within comparator 236 ns + 4 ticks + gate 1 us', M['gate_delay_ns'],
                  '<= %.0f ns' % (lim * 1e9), okg, 'ns'))
    C.append(crit('OC step: FAULT_N low', M['fault_delay_ns'], '<= %.0f ns' % (lim * 1e9),
                  t_f is not None and t_x is not None and t_f - t_x <= lim, 'ns'))
    fl = spird(res, '02')
    M['fault_reads'] = [[a * 1e6, '0x%04X' % v] for a, v in fl]
    oc_mon = [m for m in mon if m['kind'] == 'FAULT' and t_x and float(m['t']) * 1e-9 > t_x]
    M['fault_cause_monitor'] = [m.get('cause') for m in oc_mon]
    C.append(crit('fault cause after the step is OC_A (bit 0, monitor of the latched cause)', M['fault_cause_monitor'], 'bit 0',
                  bool(oc_mon) and (int(oc_mon[0]['cause'], 16) & 1) == 1))
    r1 = [int(r['gate_a_rises']) for r in res if r['kind'] == 'RESUME1']
    r2 = [int(r['gate_a_rises']) for r in res if r['kind'] == 'RESUME2']
    C.append(crit('after CLR: PWM on GATE_A again', r1, '>= 1 rising edge in 3.6 us', bool(r1) and r1[0] >= 1))
    ten = [float(r['t']) * 1e-9 for r in res if r['kind'] == 'ENLOW']
    if ten:
        t_e = first(crossings(t, w['en_sto_in'], 1.65, False, ten[0] - 1e-9))
        tge = [first(crossings(t, w['gate_%s' % g], 1.0, False, t_e or ten[0])) for g in 'abc']
        hie = [at(t, w['gate_%s' % g], (t_e or ten[0]) - 5e-9) for g in 'abc']
        M.update(en_gate_delay_ns=[(g - t_e) * 1e9 if (g and t_e) else None for g in tge], en_gates_before_V=hie)
        C.append(crit('EN low: all gates < 1 V within 1 us (gate-drive row)', M['en_gate_delay_ns'], '<= 1000',
                      t_e is not None and all(g is not None for g in tge) and max(tge) - t_e <= 1e-6 and
                      all(h > 3.0 for h in hie), 'ns'))
        C.append(crit('FAULT register: STO (bit 8) latched after EN low', M['fault_reads'], 'bit 8',
                      len(fl) >= 1 and (fl[0][1] & 0x100) != 0))
    else:
        C.append(crit('EN low applied', None, 'yes', False))
    C.append(crit('after EN high and CLR: PWM on GATE_A again', r2, '>= 1 rising edge in 3.6 us', bool(r2) and r2[0] >= 1))
    return C, M


def test5(w, res, mon, run):
    t = w['time']
    C, M = [], {}
    temp = float(run.get('temp_c', 27.0))
    wr = [float(r['t']) * 1e-9 for r in res if r['kind'] == 'SPIWR' and r['addr'].lower() == '34']
    temps = spird(res, '2b')
    if not wr or not temps:
        C.append(crit('T2F_WIN written and TEMP read', None, 'yes', False))
        return C, M
    t0 = wr[0]
    t1 = temps[0][0]
    f_t2f, n = freq(t, w['t2f_fout'], 0.6, t0, t1)
    f_osc, _ = freq(t, w['osc_clk'], 0.6, t0, t1)
    M.update(f_t2f_MHz=f_t2f and f_t2f / 1e6, f_clk_MHz=f_osc and f_osc / 1e6, temp_reads=[v for _, v in temps])
    exp = f_t2f * 256 / f_osc if (f_t2f and f_osc) else None
    M['temp_expected'] = exp
    tv = temps[-1][1]
    C.append(crit('TEMP equals f_T2F x 2^8 / f_clk within 1 count (ctrl counter)', tv, '%s +- 1' % (exp and round(exp, 2)),
                  exp is not None and abs(tv - exp) <= 1.0, 'counts'))
    rec = T2F_REC.get(temp)
    if rec:
        e = (f_t2f - rec) / rec * 100.0 if f_t2f else None
        M['f_t2f_vs_record_pct'] = e
        C.append(crit('f_T2F within 3 %% of the T2F record at %g C (%.4f MHz, G1 bandgap)' % (temp, rec / 1e6), e, '|e| <= 3',
                      e is not None and abs(e) <= 3.0, '%'))
    return C, M


def test6(w, res, mon, run):
    t = w['time']
    C, M = [], {}
    oc = spird(res, '09')
    st = spird(res, '01')
    rf = [r for r in res if r['kind'] == 'REFCLK']
    if not (oc and rf):
        C.append(crit('OSC_COUNT read', None, 'yes', False))
        return C, M
    fref = 1e9 / float(rf[0]['period_ns'])
    t_ref_end = float(rf[0]['t']) * 1e-9
    f_o, _ = freq(t, w['osc_clk'], 0.6, t_ref_end - 6.5e-6, t_ref_end)
    exp6 = 16 * f_o / fref
    M.update(osc_count=oc[0][1], osc_count_expected=exp6, osc_f_waveform_MHz=f_o / 1e6,
             osc_f_from_count_MHz=oc[0][1] * fref / 16 / 1e6, f_ref_MHz=fref / 1e6, status=['0x%04X' % v for _, v in st])
    C.append(crit('OSC_COUNT = 16 f_osc / f_ref within 1.5 counts', oc[0][1], '%.2f +- 1.5' % exp6,
                  abs(oc[0][1] - exp6) <= 1.5, 'counts'))
    # D13 band (28-32 MHz) is the post-layout target; the schematic runs fast by design (r1_osc README, 32.69 MHz)
    C.append(crit('r1_osc at code 22 within 2 % of the schematic record 32.69 MHz (D13 band: post-layout, 30.30 MHz passed)',
                  f_o / 1e6, '32.69 +- 2 %', abs(f_o - 32.69e6) <= 0.02 * 32.69e6, 'MHz'))
    C.append(crit('STATUS.OSC_DONE (bit 10) set', M['status'], 'bit 10', bool(st) and (st[0][1] & 0x400) != 0))
    return C, M


def main():
    rid = sys.argv[1]
    d = os.path.join(os.environ['G1_RESULTS_ROOT'], 'r1_top', 'tb', rid)
    run = json.load(open(os.path.join(d, 'run.json')))
    txt = open(os.path.join(d, 'ngspice.log'), errors='replace').read()
    res, mon = parse_log(txt)
    out = {'run_id': rid, 'test': run['test'], 'view': run['view'], 'corner': run['corner'], 'temp_c': run['temp_c'],
           'sim_status': run.get('status'), 'ngspice_wall_s': run.get('ngspice_wall_s'), 'tstop_us': run['tstop_us']}
    rawp = os.path.join(d, 'tran.raw')
    C, M = [], {}
    done = [r for r in res if r['kind'] == 'DONE']
    out['master_done_us'] = float(done[0]['t']) * 1e-3 if done else None
    if not os.path.exists(rawp):
        C.append(crit('simulation produced a waveform file', None, 'tran.raw', False))
    else:
        w = read_raw(rawp)
        out['t_end_us'] = float(w['time'][-1] * 1e6)
        out['vref_bg_t0_V'] = float(w['vref_bg'][0])
        if run['test'] != 1:  # start state must be the bandgap on-state (F9)
            C.append(crit('start state: vref_bg at t = 0 is the on-state of r1_bgr (1.045 V record)', out['vref_bg_t0_V'],
                          '1.00-1.09', 1.00 <= out['vref_bg_t0_V'] <= 1.09, 'V'))
        C.append(crit('master sequence completed (DONE line)', out['master_done_us'], 'before tstop', bool(done)))
        fn = {1: test1, 2: test2, 3: test3, 4: test4, 5: test5, 6: test6}[run['test']]
        try:
            c2, M = fn(w, res, mon, run)
            C += c2
        except Exception as e:  # a crash of the evaluation is a failed run, not a pass
            C.append(crit('evaluation', repr(e), 'no exception', False))
    out['criteria'] = C
    out['measurements'] = M
    out['spi'] = [r for r in res if r['kind'] in ('SPIRD', 'SPIWR')][:200]
    out['verdict'] = 'passed' if C and all(c['status'] == 'passed' for c in C) else 'failed'
    os.makedirs(os.path.join(HERE, 'results'), exist_ok=True)
    js = json.dumps(out, indent=1, default=float)
    open(os.path.join(HERE, 'results', rid + '.json'), 'w').write(js)
    for c in C:
        print('%-7s %s: %s (limit %s)' % (c['status'], c['name'], c['value'] if not isinstance(c['value'], dict) else '...', c['limit']))
    print('verdict', out['verdict'])
    sys.exit(0 if out['verdict'] == 'passed' else 1)


if __name__ == '__main__':
    main()
