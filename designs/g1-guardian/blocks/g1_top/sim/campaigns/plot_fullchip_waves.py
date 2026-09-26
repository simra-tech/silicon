#!/usr/bin/env python3
"""Plot saved G1_TOP full-chip waveforms, one PNG per run, plus a JSON index.

Reads the decimated waveforms that run_top.py / run_top_cdl.py write to
sim/results/waves/<tag>.txt (ngspice wrdata with wr_vecnames; first column time; gitignored),
falling back to build/g1_top/waves_<tag>.txt. The run log sim/logs/<tag>.log supplies the
header (description), the run status and the measures (trip times, power-up numbers). Only
runs whose log ends in '# run status completed' are plotted. Runs no simulator; every number
shown is simulated.

Functional (load-event) runs get, on a shared time axis:
  (a) load current I(Vim) with the commanded profile (shunt voltage = I x 25 mOhm)
  (b) logic lanes: EN, cmp_soft, cmp_hard, trip_d (RTL decision), tripped (G1_GATE latch)
  (c) GATE pad with the 1 V and 0.33 V thresholds; GATE < 1 V time from the log measures
  (d) VREF (internal VREF net)
  (e) supplies VDDA (= IOVDD rail) and VDD
and, for runs that trip, a right-hand column zoomed to +-3 us around 'tripped', which adds the
comparator input icmp against vth_soft / vth_hard.
Power-up runs (gA, gB, gA_pd, gB_pd, gS) get VDD / VDDA=IOVDD / EN, GATE, tripped, load current.

The status column of the index comes from the Markdown records given with --record: a table
row whose backticked log names match the tag (with '...' as wildcard; the most specific
pattern wins, and a row that names a non-tt corner only matches that corner).

Usage (repository root):
  python3 designs/g1-guardian/blocks/g1_top/sim/campaigns/plot_fullchip_waves.py \
      --glob 'cdl_*_r3full*' --out designs/g1-guardian/blocks/g1_top/sim/figures/fullchip_r3full \
      [--glob 'gS_pex_*eco4_gS'] [--exclude REGEX] [--record FILE.md ...]
"""
import argparse
import fnmatch
import glob
import hashlib
import io
import json
import os
import re
import sys

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.gridspec import GridSpec  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SIM = os.path.dirname(HERE)
ROOT = os.path.abspath(os.path.join(SIM, '..', '..', '..', '..', '..'))
WAVES = os.path.join(SIM, 'results', 'waves')
BUILD = os.path.join(ROOT, 'build', 'g1_top')
LOGS = os.path.join(SIM, 'logs')
DEFAULT_RECORDS = [os.path.join(SIM, 'FULLCHIP_CDL_R3_20260926.md'),
                   os.path.join(HERE, 'RESULTS_20260925.md')]
POWERUP = ('gA', 'gB', 'gA_pd', 'gB_pd', 'gS')
RSH = 0.025
WIDTH_PX, DPI, MAX_BYTES = 1600, 110, 250_000

# reference categorical palette (slots 1-3, 7, 8), text inks
C1, C2, C3, C7, C8 = '#2a78d6', '#eb6834', '#1baf7a', '#4a3aa7', '#e34948'
INK, INK2, MUTED, GRID = '#0b0b0b', '#52514e', '#8a8983', '#e4e3df'

SIG = {  # role -> candidate column names (hand-wired deck, CDL deck)
    'gate': ['v(gate)'], 'gfet': ['v(gfet)'],
    'tripped': ['v(tripped)', 'v(xchip.i_core_tripped)'],
    'cmp_soft': ['v(cmp_soft)', 'v(xchip.i_core_cmp_soft)'],
    'cmp_hard': ['v(cmp_hard)', 'v(xchip.i_core_cmp_hard)'],
    'trip_d': ['v(trip_d)', 'v(xchip.i_core_trip_d)'],
    'vref': ['v(vref)', 'v(xchip.i_core_vref)'],
    'en': ['v(en_core)', 'v(xchip.en_i)'],
    'vdda': ['v(vdda)'], 'vdd': ['v(vdd)'], 'iprof': ['v(iprof)'],
    'icmp': ['v(icmp)', 'v(xchip.xi_core_u_trip.icmp)'],
    'vth_soft': ['v(vth_soft)', 'v(xchip.xi_core_u_trip.vth_soft)'],
    'vth_hard': ['v(vth_hard)', 'v(xchip.xi_core_u_trip.vth_hard)'],
    'dig_trip': ['v(dig_trip)', 'v(xchip.i_core_trip)'],
    'iload': ['i(vim)'],
}


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def rel(p):
    return '${REPO}/' + os.path.relpath(p, ROOT)


def read_wave(path):
    with open(path) as f:
        hdr = f.readline().split()
    d = np.loadtxt(path, skiprows=1, ndmin=2)
    return {name: d[:, i] for i, name in enumerate(hdr) if i < d.shape[1]}


def get(w, role):
    for n in SIG[role]:
        if n in w:
            return w[n]
    return None


def num(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def parse_log(path):
    t = open(path, errors='replace').read()
    lines = t.splitlines()
    st = re.findall(r'^# run status (.+)$', t, re.M)
    info = dict(status=st[-1].strip() if st else 'no status line',
                desc=lines[1].lstrip('# ').strip() if len(lines) > 1 else '')
    if 'mismatched XSPICE' in t:
        info['status'] = 'invalid (mismatched XSPICE)'
    wall = re.search(r'^# ngspice exit \S+, wall time (\S+) s', t, re.M)
    info['wall_s'] = num(wall.group(1)) if wall else None
    for key in ('TRIP', 'REARM', 'POWERUP', 'CLOCK', 'VREF_RIPPLE'):
        m = re.findall(r'^%s (.*)$' % key, t, re.M)
        if m:
            info[key] = {k: num(v) if num(v) is not None else v
                         for k, v in re.findall(r'(\S+?)=\s*([^\s=]*)(?=\s|$)', m[-1])}
    for key in ('t_tripped', 't_trip_d', 't_gate1v', 't_gate03'):
        m = re.findall(r'^%s\s*=\s*(\S+)' % key, t, re.M)
        if m:
            info[key] = num(m[-1])
    return info


def load_records(paths):
    rows = []
    for p in paths:
        if not os.path.exists(p):
            continue
        header = None
        for line in open(p, errors='replace'):
            if not line.startswith('|'):
                header = None
                continue
            cells = [c.strip() for c in line.strip().strip('|').split('|')]
            if header is None:
                header = [c.lower() for c in cells]
                continue
            if set(''.join(cells)) <= set('-: '):
                continue
            names = re.findall(r'`([^`]+)`', cells[-1]) if cells else []
            if not names:
                continue
            col = lambda k: next((cells[i] for i, h in enumerate(header) if h.startswith(k) and i < len(cells)), '')
            status = ' ; '.join(x for x in (col('status'), col('verdict')) if x)
            rows.append(dict(record=os.path.basename(p), row=cells[0].replace('**', ''),
                             status=status.replace('**', ''), text=line, patterns=names))
    return rows


def match_record(tag, rows):
    corner = re.search(r'_(tt|ss|ff|sf|fs)_(-?\d+)C_', tag)
    cn = corner.group(0).strip('_') if corner else 'tt_27C'
    best = None
    for r in rows:
        row_corners = set(re.findall(r'(ss|ff)[ _]?(?:−|-)?(\d+) ?°?C', r['text']))
        tag_c = (cn.split('_')[0], cn.split('_')[1].lstrip('-').rstrip('C'))
        if row_corners and tag_c not in row_corners:
            continue
        if not row_corners and cn != 'tt_27C':
            continue
        for p in r['patterns']:
            p = re.sub(r'\.log$', '', p.strip())
            parts = p.split('…')
            rx = '^(cdl_)?' + '.*'.join(re.escape(x) for x in parts) + '(_functional_[A-Za-z0-9]+)?$'
            if re.match(rx, tag):
                score = sum(len(x) for x in parts)
                if best is None or score > best[0]:
                    best = (score, r)
    return best[1] if best else None


def meta(tag):
    name = re.sub(r'^cdl_', '', tag).split('_pex')[0]
    m = re.search(r'_(tt|ss|ff|sf|fs)_(-?\d+)C_', tag)
    corner, temp = (m.group(1), int(m.group(2))) if m else ('tt', 27)
    case = name
    if '_osctl_' in tag:
        case += ' (osc tl)'
    fm = re.search(r'_fm(\d)p(\d+)_', tag)
    if fm:
        case += ' fault x%s.%s' % fm.groups()
    if 't2foff' in tag:
        case += ', T2F off'
    bits = []
    if tag.startswith('cdl_'):
        c = re.search(r'_cdl([0-9a-f]{8})_', tag)
        bits.append('CDL chip netlist %s' % (c.group(1) if c else '?'))
        bits.append('PEX blocks')
        if '_icx' in tag:
            bits.append('extracted top interconnect')
        bits.append('stock pads' if 'padspdk' in tag else 'pads nodcn')
    else:
        bits.append('hand-wired chip deck (%s)' % ('c1414' if 'c1414' in tag else 'run_top'))
        if 'ovr-bgrsch' in tag:
            bits.append('BGR schematic')
        bits.append('pads nodcn' if 'nodcn' in tag else 'stock pads')
    r = re.search(r'_rtleco(\d+)_', tag)
    if r:
        bits.append('ECO RTL %s cosim' % r.group(1))
    if '_por_' in tag:
        bits.append('por_n from CDL tie-high')
    ms = re.search(r'_maxstep([\d.]+)ns', tag)
    bits.append('maxstep %s ns' % ms.group(1) if ms else 'case default step')
    if 'optreltol' in tag:
        bits.append('reltol 5e-4' if '5em4' in tag else 'loose tolerances')
    if '_gear' in tag or tag.startswith('gS_'):
        bits.append('gear')
    return name, case, corner, temp, ', '.join(bits)


def logic_lanes(ax, t, lanes, xlim):
    ticks = []
    for k, (label, v, vmax, color) in enumerate(lanes):
        if v is None:
            continue
        base = len(lanes) - 1 - k
        ax.plot(t, base + 0.8 * np.clip(v / vmax, -0.1, 1.2), color=color, lw=1.1)
        ax.axhline(base, color=GRID, lw=0.6, zorder=0)
        ticks.append((base + 0.4, label))
    ax.set_yticks([a for a, _ in ticks])
    ax.set_yticklabels([b for _, b in ticks], fontsize=8)
    ax.set_ylim(-0.3, len(lanes) - 0.05)
    ax.set_xlim(*xlim)


def style(ax, ylabel=None):
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    for s in ('left', 'bottom'):
        ax.spines[s].set_color(MUTED)
    ax.tick_params(colors=INK2, labelsize=8)
    ax.grid(True, color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=8.5, color=INK2)


def label_panel(ax, s):
    ax.text(0.003, 0.97, s, transform=ax.transAxes, fontsize=9, fontweight='bold', color=INK,
            va='top', ha='left', bbox=dict(fc='white', ec='none', alpha=0.8, pad=1))


def vlines(axes, times):
    for ax in axes:
        for x, color, ls in times:
            if x is not None:
                ax.axvline(x, color=color, ls=ls, lw=0.9, zorder=1)


def plot_functional(fig, w, info, us):
    t = w['time'] * 1e6
    trip = info.get('t_tripped')
    trips = trip is not None and (info.get('TRIP', {}).get('tripped_max') or 0) > 0.6
    iprof = get(w, 'iprof')
    event = None
    if trips and isinstance(info.get('TRIP', {}).get('t_tripped_us'), float):
        event = trip * 1e6 - info['TRIP']['t_tripped_us']
    elif iprof is not None:
        ch = np.where(np.abs(np.diff(iprof)) > 1e-3)[0]
        if len(ch):
            event = t[ch[0]]
    zc = trip * 1e6 if trips else event
    ncol = 2 if zc is not None else 1
    gs = GridSpec(5, ncol, figure=fig, width_ratios=[1.75, 1] if ncol == 2 else [1],
                  height_ratios=[1, 1.25, 1, 0.8, 0.8], hspace=0.12, wspace=0.16,
                  left=0.075, right=0.985, top=0.9, bottom=0.07)
    ax = [fig.add_subplot(gs[0, 0])]
    ax += [fig.add_subplot(gs[i, 0], sharex=ax[0]) for i in range(1, 5)]
    xlim = (t[0], t[-1])
    en, tr, td = get(w, 'en'), get(w, 'tripped'), get(w, 'trip_d')
    lanes = [('EN (core)', en, 1.2, INK2), ('cmp_soft', get(w, 'cmp_soft'), 1.2, C3),
             ('cmp_hard', get(w, 'cmp_hard'), 1.2, C2), ('trip_d (RTL)', td, 1.2, C7),
             ('tripped (latch)', tr, 1.2, C8)]
    marks = [(event, INK2, ':'), (trip * 1e6 if trips else None, C8, '--')]

    def panels(axs, sl, zoom):
        tt = t[sl]
        a = axs[0]
        a.plot(tt, get(w, 'iload')[sl], color=C1, lw=1.4, label='I(Vim) load')
        if iprof is not None:
            a.plot(tt, iprof[sl], color=MUTED, lw=1.0, ls='--', label='commanded profile')
        style(a, 'load current (A)\nshunt = I x 25 mΩ' if not zoom else None)
        if not zoom:
            a.legend(fontsize=7.5, loc='upper right', frameon=False, ncol=2)
        b = axs[1]
        logic_lanes(b, tt, [(l, None if v is None else v[sl], m, c) for l, v, m, c in lanes], (tt[0], tt[-1]))
        style(b)
        b.grid(False)
        c = axs[2]
        c.plot(tt, w['v(gate)'][sl], color=C1, lw=1.4)
        for y, s in ((1.0, '1 V'), (0.33, '0.33 V')):
            c.axhline(y, color=MUTED, ls='--', lw=0.8)
            c.text(tt[0] + 0.005 * (tt[-1] - tt[0]), y + 0.08, s, fontsize=7.5, color=INK2)
        style(c, 'GATE pad (V)' if not zoom else None)
        if trips and info.get('t_gate1v') is not None:
            tg = info['t_gate1v'] * 1e6
            c.plot([tg], [1.0], 'o', ms=5, color=C8, mec='white', mew=1.0, zorder=5)
            T = info['TRIP']
            txt = ('GATE < 1 V at +%.3f µs\n< 0.33 V at +%.3f µs (from event)' %
                   (T.get('t_gate_1V_us'), T.get('t_gate_0.33V_us')))
            if 'REARM' in info and not zoom:
                R = info['REARM']
                c.text(0.09, 0.40, 're-arm (log measures): GATE %.3g V while EN low;\nGATE 90 %% %.3f µs after EN high; %.2f A at the end'
                       % (R.get('gate_while_EN_low'), R.get('EN_high_to_GATE_90pct_us'), R.get('iload_end_A')),
                       transform=c.transAxes, ha='left', va='center', fontsize=7.5, color=INK, bbox=dict(fc='white', ec=GRID, pad=2))
            if tt[0] <= tg <= tt[-1]:
                right = tg > tt[0] + 0.45 * (tt[-1] - tt[0])
                c.annotate(txt, (tg, 1.0), xytext=(-12 if right else 12, 22), textcoords='offset points', fontsize=7.5,
                           ha='right' if right else 'left',
                           color=INK, arrowprops=dict(arrowstyle='-', color=MUTED, lw=0.7))
        d = axs[3]
        if zoom:
            for role, col, lab in (('icmp', C1, 'icmp'), ('vth_soft', C3, 'vth_soft'), ('vth_hard', C2, 'vth_hard')):
                v = get(w, role)
                if v is not None:
                    d.plot(tt, v[sl], color=col, lw=1.1, label=lab)
            lo, hi = d.get_ylim()
            d.set_ylim(lo, hi + 0.35 * (hi - lo))
            d.legend(fontsize=7, loc='upper right', frameon=False, ncol=3)
            style(d)
            label_panel(d, 'comparator in (V)')
        else:
            d.plot(tt, get(w, 'vref')[sl], color=C7, lw=0.9)
            style(d, 'VREF (V)\n20 ns samples')
        e = axs[4]
        if zoom:
            e.plot(tt, get(w, 'vref')[sl], color=C7, lw=0.9)
            style(e)
            label_panel(e, 'VREF (V)')
        else:
            e.plot(tt, get(w, 'vdda')[sl], color=C2, lw=1.2, label='VDDA = IOVDD rail')
            e.plot(tt, get(w, 'vdd')[sl], color=C1, lw=1.2, label='VDD')
            e.set_ylim(-0.1, 3.8)
            e.legend(fontsize=7.5, loc='center right', frameon=False, ncol=2)
            style(e, 'supplies (V)')
        e.set_xlabel('time (µs)', fontsize=8.5, color=INK2)
        for a2 in axs[:-1]:
            plt.setp(a2.get_xticklabels(), visible=False)
        vlines(axs, marks)

    panels(ax, slice(None), False)
    ax[0].set_xlim(*xlim)
    for a, s in zip(ax, ('(a)', '(b)', '(c)', '(d)', '(e)')):
        a.text(-0.005, 1.015, s, transform=a.transAxes, fontsize=9, fontweight='bold', color=INK, ha='right', va='bottom')
    if event is not None:
        ax[0].text(event, 1.02, ' load event %.2f µs' % event, transform=ax[0].get_xaxis_transform(),
                   fontsize=7.5, color=INK2)
    else:
        ax[0].text(0.5, 1.02, 'no load event in this case', transform=ax[0].transAxes, fontsize=7.5,
                   color=INK2, ha='center')
    if zc is not None:
        tz = zc
        sl = (t >= tz - 3) & (t <= tz + 3)
        z = [fig.add_subplot(gs[0, 1])]
        z += [fig.add_subplot(gs[i, 1], sharex=z[0]) for i in range(1, 5)]
        panels(z, sl, True)
        z[0].set_xlim(tz - 3, tz + 3)
        z[0].set_title(('zoom: tripped ± 3 µs (tripped at %.3f µs)' if trips else
                        'zoom: load event ± 3 µs (no trip; event at %.3f µs)') % tz, fontsize=9, color=INK)
        for a in ax:
            a.axvspan(tz - 3, tz + 3, color='#f1efe8', zorder=0)
    return event


def plot_powerup(fig, w, info, us):
    t = w['time'] * 1e6
    gs = GridSpec(4, 1, figure=fig, height_ratios=[1, 1, 0.9, 0.8], hspace=0.12,
                  left=0.075, right=0.985, top=0.89, bottom=0.07)
    ax = [fig.add_subplot(gs[0])]
    ax += [fig.add_subplot(gs[i], sharex=ax[0]) for i in range(1, 4)]
    a = ax[0]
    a.plot(t, get(w, 'vdda'), color=C2, lw=1.4, label='VDDA = IOVDD (one 3.3 V rail)')
    a.plot(t, get(w, 'vdd'), color=C1, lw=1.4, label='VDD (1.2 V)')
    style(a, 'supplies (V)')
    a.legend(fontsize=7.5, loc='center right', frameon=False)
    b = ax[1]
    b.plot(t, w['v(gate)'], color=C1, lw=1.4, label='GATE pad')
    b.axhline(1.0, color=MUTED, ls='--', lw=0.8)
    b.text(t[0] + 0.1, 1.08, '1 V (load FET threshold)', fontsize=7.5, color=INK2)
    style(b, 'GATE pad (V)')
    P = info.get('POWERUP', {})
    gm = P.get('GATE_max_EN_low')
    if isinstance(gm, float):
        msg = 'GATE max while EN low: %.4g V' % gm
        g0, g1 = P.get('GATE_above_1V_from_us'), P.get('to_us')
        if isinstance(g0, float) and isinstance(g1, float):
            msg += '; GATE > 1 V from %.2f to %.2f µs' % (g0 * 1e6 if g0 < 1e-3 else g0, g1 * 1e6 if g1 < 1e-3 else g1)
        b.text(0.995, 0.93, msg + ' (log measures, simulated)',
               transform=b.transAxes, fontsize=8, ha='right', va='top', color=INK,
               bbox=dict(fc='white', ec=GRID, pad=2))
    c = ax[2]
    logic_lanes(c, t, [('EN (core)', get(w, 'en'), 1.2, INK2), ('trip (RTL)', get(w, 'dig_trip'), 1.2, C7),
                       ('tripped (latch)', get(w, 'tripped'), 1.2, C8)], (t[0], t[-1]))
    style(c)
    c.grid(False)
    d = ax[3]
    d.plot(t, get(w, 'iload'), color=C1, lw=1.4)
    style(d, 'load current (A)')
    d.set_xlabel('time (µs)', fontsize=8.5, color=INK2)
    for a2 in ax[:-1]:
        plt.setp(a2.get_xticklabels(), visible=False)
    ax[0].set_xlim(t[0], t[-1])
    for a, s in zip(ax, ('(e1)', '(e2)', '(e3)', '(e4)')):
        a.text(-0.005, 1.015, s, transform=a.transAxes, fontsize=9, fontweight='bold', color=INK, ha='right', va='bottom')
    return None


def save_png(fig, path):
    buf = io.BytesIO()
    fig.savefig(buf, dpi=DPI, format='png', facecolor='white')
    data = buf.getvalue()
    if len(data) > MAX_BYTES:
        from PIL import Image
        im = Image.open(io.BytesIO(data)).convert('RGB')
        for colors in (128, 64, 32):
            b2 = io.BytesIO()
            im.quantize(colors=colors, method=Image.MEDIANCUT).save(b2, format='PNG', optimize=True)
            data = b2.getvalue()
            if len(data) <= MAX_BYTES:
                break
    with open(path, 'wb') as f:
        f.write(data)
    return len(data)


def find_wave(tag):
    for p in (os.path.join(WAVES, tag + '.txt'), os.path.join(BUILD, 'waves_%s.txt' % tag)):
        if os.path.exists(p):
            return p
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--glob', action='append', required=True,
                    help='run-tag glob (no .log / .txt), repeatable, e.g. "cdl_*_r3x"')
    ap.add_argument('--out', required=True, help='output directory for PNGs and index.json')
    ap.add_argument('--exclude', default=None, help='regex; matching tags are skipped')
    ap.add_argument('--record', action='append', default=None,
                    help='Markdown record(s) to take the status from (default: FULLCHIP_CDL_R3_20260926.md, '
                         'campaigns/RESULTS_20260925.md)')
    ap.add_argument('--include-incomplete', action='store_true', help='also plot runs without "completed"')
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    rows = load_records(a.record or DEFAULT_RECORDS)
    tags = set()
    for g in a.glob:
        for p in glob.glob(os.path.join(LOGS, g + '.log')):
            tags.add(os.path.basename(p)[:-4])
    index, skipped = [], []
    for tag in sorted(tags):
        if a.exclude and re.search(a.exclude, tag):
            continue
        logp = os.path.join(LOGS, tag + '.log')
        info = parse_log(logp)
        if info['status'] != 'completed' and not a.include_incomplete:
            skipped.append((tag, 'log status: %s' % info['status']))
            continue
        wave = find_wave(tag)
        if wave is None:
            skipped.append((tag, 'no waveform file'))
            continue
        w = read_wave(wave)
        name, case, corner, temp, deck = meta(tag)
        rec = match_record(tag, rows)
        fig = plt.figure(figsize=(WIDTH_PX / DPI, 11.2 if name not in POWERUP else 8.6))
        if name in POWERUP:
            event = plot_powerup(fig, w, info, 1e6)
        else:
            event = plot_functional(fig, w, info, 1e6)
        desc = info['desc']
        fm = re.search(r'_fm(\d+)p(\d+)_', tag)
        if fm:
            mult = float('%s.%s' % fm.groups())
            desc = 'near-threshold variant of ' + desc.replace('in-range hard trip: ', '')
            desc = re.sub(r'[\d.]+A/[\d.]+mV fault', '%.2fA/%.2fmV fault (--fault-mult %g)' % (mult, mult * RSH * 1e3, mult), desc)
        clk = info.get('CLOCK')
        if clk and isinstance(clk.get('f_osc_MHz'), float):
            deck += ', clock %s %.4f MHz' % ('transistor-level G1_OSC' if 'transistor' in open(logp, errors='replace').read().split('CLOCK f_osc')[-1][:200] else 'ideal', clk['f_osc_MHz'])
        fig.suptitle('%s  |  %s, %d °C  |  %s' % (case, corner, temp, desc),
                     x=0.01, ha='left', y=0.985, fontsize=10.5, color=INK, fontweight='bold')
        fig.text(0.01, 0.955, 'deck: %s' % deck, fontsize=8.5, color=INK2, ha='left')
        wsha, lsha = sha(wave), sha(logp)
        fig.text(0.01, 0.012, 'SIMULATED (ngspice, IHP SG13G2 open PDK). tag %s | waveform sha256 %s | log sha256 %s'
                 % (tag, wsha[:12], lsha[:12]), fontsize=6.8, color=MUTED, ha='left')
        fig.text(0.01, 0.945 - 0.2 / fig.get_figheight(), 'record status: %s' % ((rec['status'][:140]) if rec else 'not in record'),
                 fontsize=8.5, color=INK2, ha='left')
        png = os.path.join(a.out, tag + '.png')
        size = save_png(fig, png)
        plt.close(fig)
        entry = dict(tag=tag, case=case, corner=corner, temp_C=temp, deck=deck, description=desc,
                     log_status=info['status'], wall_s=info['wall_s'],
                     record=(rec['record'] if rec else None), record_row=(rec['row'] if rec else None),
                     status=(rec['status'] if rec else 'not in record'),
                     png=os.path.basename(png), png_bytes=size,
                     waveform=rel(wave), waveform_sha256=wsha, log=rel(logp), log_sha256=lsha,
                     event_us=(round(event, 4) if event is not None else None),
                     measures_simulated={k: info[k] for k in ('TRIP', 'REARM', 'POWERUP', 'CLOCK') if k in info})
        index.append(entry)
        print('%-9s %6.0f kB  %s  [%s]' % ('ok', size / 1e3, tag, entry['status'][:60]))
    for tag, why in skipped:
        print('skipped   %s: %s' % (tag, why))
    out = dict(generator=rel(os.path.abspath(__file__)), generator_sha256=sha(os.path.abspath(__file__)),
               globs=a.glob, exclude=a.exclude, note='all numbers simulated', runs=index,
               skipped=[dict(tag=t, reason=r) for t, r in skipped])
    with open(os.path.join(a.out, 'index.json'), 'w') as f:
        json.dump(out, f, indent=1)
    return 0


if __name__ == '__main__':
    sys.exit(main())
