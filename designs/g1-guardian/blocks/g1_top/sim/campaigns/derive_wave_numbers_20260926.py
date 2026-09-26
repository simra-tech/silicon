#!/usr/bin/env python3
"""Derive VREF-ripple statistics and power-up latch windows from saved G1_TOP waveforms.

The waveform files (build/g1_top/waves_<tag>.txt, written by run_top.py / run_top_cdl.py with ngspice
`linearize` at the deck's output step, normally 20 ns) are gitignored. This script reduces them to the
numbers that the review needs and writes derived_wave_numbers_20260926.json next to itself, with the SHA256
of every waveform and log it read. It runs no simulator. All numbers are simulated.

  VREF ripple: v(vref) (hand-wired deck) or v(xchip.i_core_vref) (CDL deck) over [event - 2 us, event]
    (event 16 us for compact-timeline tags, 30 us otherwise; case osc: 24-36 us). Only runs whose log says
    '# run status completed' and whose waveform covers the window are used. The 20 ns linearized sampling
    under-samples edge-synchronous spikes, so pk-pk here can be below the in-simulator VREF_RIPPLE measure
    (taken on the solver's own time points); both are given where the log has the measure.
  Power-up latch windows (cases gA, gB, gA_pd, gB_pd, gS): intervals with the G1_GATE latch output
    (v(tripped) / v(xchip.i_core_tripped)) above 0.6 V, with GATE above 1 V, and with the core gate_core
    above 0.6 V where saved, before EN rises (12 us), plus the latch level after EN rise and at the end.

Usage (repository root): python3 designs/g1-guardian/blocks/g1_top/sim/campaigns/derive_wave_numbers_20260926.py
"""
import glob
import hashlib
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SIM = os.path.dirname(HERE)
ROOT = os.path.abspath(os.path.join(SIM, '..', '..', '..', '..', '..'))
BUILD = os.path.join(ROOT, 'build', 'g1_top')
LOGS = os.path.join(SIM, 'logs')
OUT = os.path.join(HERE, 'derived_wave_numbers_20260926.json')
T_EN_POWERUP = 12e-6


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def read(path):
    with open(path) as f:
        hdr = f.readline().split()
        rows = []
        for l in f:
            try:
                rows.append([float(x) for x in l.split()])
            except ValueError:
                pass
    return hdr, rows


def log_info(tag):
    p = os.path.join(LOGS, tag + '.log')
    if not os.path.exists(p):
        return None, None, None
    t = open(p, errors='replace').read()
    st = re.findall(r'^# run status (\S+)', t, re.M)
    if 'mismatched XSPICE' in t:      # digital macro not loaded: not valid evidence
        st = ['invalid-cosim']
    rip = re.search(r'^VREF_RIPPLE window=(\S+) pp_mV= *(\S+) +mean= *(\S+)', t, re.M)
    return (st[-1] if st else 'no status line'), p, (dict(window_us=rip.group(1), pp_mV=float(rip.group(2)), mean_V=float(rip.group(3))) if rip else None)


def col(hdr, names):
    for n in names:
        if n in hdr:
            return hdr.index(n)
    return None


def intervals(rows, i, thr, t1):
    out, start = [], None
    for r in rows:
        if r[0] > t1:
            break
        hi = r[i] > thr
        if hi and start is None:
            start = r[0]
        elif not hi and start is not None:
            out.append([round(start * 1e6, 4), round(r[0] * 1e6, 4)])
            start = None
    if start is not None:
        out.append([round(start * 1e6, 4), round(min(t1, rows[-1][0]) * 1e6, 4)])
    return out


def at(rows, i, t):
    best = min(rows, key=lambda r: abs(r[0] - t))
    return best[i]


def main():
    ripple, powerup = [], []
    for wave in sorted(glob.glob(os.path.join(BUILD, 'waves_*.txt'))):
        tag = os.path.basename(wave)[len('waves_'):-4]
        status, logp, rip_meas = log_info(tag)
        if status != 'completed':
            continue
        name = re.sub(r'^cdl_', '', tag).split('_pex')[0]
        is_icx = '_icx' in tag or tag.endswith('icx2ref')
        is_pu = name in ('gA', 'gB', 'gA_pd', 'gB_pd', 'gS')
        if not (is_icx or is_pu):
            continue
        hdr, rows = read(wave)
        if len(rows) < 2:
            continue
        src = dict(waveform=os.path.relpath(wave, ROOT), waveform_sha256=sha(wave),
                   log=os.path.relpath(logp, ROOT), log_sha256=sha(logp), rows=len(rows),
                   sample_step_ns=round((rows[1][0] - rows[0][0]) * 1e9, 3))
        if is_pu:
            it = col(hdr, ['v(tripped)', 'v(xchip.i_core_tripped)'])
            ig = col(hdr, ['v(gate)'])
            ic = col(hdr, ['v(gate_core)', 'v(xchip.gate_o)'])
            if it is None or ig is None:
                continue
            d = dict(tag=tag, case=name, **src,
                     latch_above_0p6V_before_EN_us=intervals(rows, it, 0.6, T_EN_POWERUP),
                     latch_max_before_EN_V=round(max(r[it] for r in rows if r[0] <= T_EN_POWERUP), 5),
                     gate_above_1V_before_EN_us=intervals(rows, ig, 1.0, T_EN_POWERUP),
                     gate_max_before_EN_V=round(max(r[ig] for r in rows if r[0] <= T_EN_POWERUP), 5),
                     latch_at_EN_rise_V=round(at(rows, it, T_EN_POWERUP), 5),
                     latch_end_V=round(rows[-1][it], 5), gate_end_V=round(rows[-1][ig], 4))
            if ic is not None:
                d['gate_core_above_0p6V_before_EN_us'] = intervals(rows, ic, 0.6, T_EN_POWERUP)
            powerup.append(d)
            continue
        iv = col(hdr, ['v(vref)', 'v(xchip.i_core_vref)'])
        if iv is None:
            continue
        t0, t1 = ((24e-6, 36e-6) if name == 'osc' else ((14e-6, 16e-6) if '_compact' in tag else (28e-6, 30e-6)))
        w = [r[iv] for r in rows if t0 <= r[0] <= t1]
        if len(w) < 10:
            continue
        m = sum(w) / len(w)
        sd = (sum((x - m) ** 2 for x in w) / len(w)) ** 0.5
        ripple.append(dict(tag=tag, case=name, interconnect='estimate' if tag.endswith('icx2ref') else 'extracted', **src,
                           window_us=[t0 * 1e6, t1 * 1e6], samples=len(w), mean_V=round(m, 6), std_mV=round(sd * 1e3, 4),
                           min_V=round(min(w), 6), max_V=round(max(w), 6), pp_mV=round((max(w) - min(w)) * 1e3, 3),
                           in_simulator_VREF_RIPPLE=rip_meas))
    out = dict(description=__doc__.strip().split('\n')[0], generator=os.path.relpath(__file__, ROOT),
               generator_sha256=sha(__file__), status='derived from simulated waveforms; not measured',
               vref_ripple=ripple, powerup_latch_windows=powerup)
    with open(OUT, 'w') as f:
        json.dump(out, f, indent=1)
        f.write('\n')
    print('wrote %s: %d ripple entries, %d power-up entries' % (os.path.relpath(OUT, ROOT), len(ripple), len(powerup)))


if __name__ == '__main__':
    main()
