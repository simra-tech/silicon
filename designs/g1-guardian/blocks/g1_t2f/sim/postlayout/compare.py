#!/usr/bin/env python3
"""Post-layout vs schematic table (results/compare.md) from the summaries of run_postlayout.py
(results/*.csv) and of the schematic runs (../results/*.csv); when the superseded revision-1 post-layout
summaries exist (../../rev1/sim/postlayout/results/*.csv) they are added as a fourth column.
Host-side, no simulator needed."""
import csv, os, re

HERE = os.path.dirname(os.path.abspath(__file__))


def load(path):
    rows = {}
    if not os.path.exists(path):
        return rows
    for r in csv.DictReader(open(path)):
        d = {}
        for k, v in r.items():
            try:
                d[k] = float(v)
            except (TypeError, ValueError):
                d[k] = None
        rows[r['deck']] = d
    return rows


post = {}
for s in ('ftemp', 'supply'):
    post.update(load(os.path.join(HERE, 'results', f'{s}_summary.csv')))
sch = {}
for s in ('ftemp', 'supply', 'nom'):
    sch.update(load(os.path.join(HERE, '..', 'results', f'{s}_summary.csv')))
old = {}
for s in ('ftemp', 'supply'):
    old.update(load(os.path.join(HERE, '..', '..', 'rev1', 'sim', 'postlayout', 'results', f'{s}_summary.csv')))


def f(rows, deck):
    r = rows.get(deck)
    return r['freq'] if r and r.get('freq') else None


def sch_f(mode, t):
    """schematic frequency: ftemp suite, or the nominal suite at 27 C"""
    if t == 27:
        return f(sch, f'nom_{mode}_T27')
    return f(sch, f'ftemp_{mode}_T{t}')


def two_point(fx):
    a = (fx[100] - fx[25]) / 75.0
    b = fx[25] - a * 25.0
    return a, b


out = ['### Post-layout (kpex 2.5D CC, layout/g1_t2f.gds) vs schematic, nominal corner, 3.3 V / 1.2 V, bandgap in its schematic view'
       + ('; last column: revision 1 post-layout (superseded, rev1/sim/postlayout)' if old else '') + '\n',
       '| quantity | unit | schematic | post-layout | delta |' + (' revision 1 post-layout |' if old else ''),
       '| --- | --- | --- | --- | --- |' + (' --- |' if old else '')]
rows = []
def o(deck):
    r = old.get(deck)
    return r['freq'] if r and r.get('freq') else None
for t in (-40, 27, 125, 175):
    s, p = sch_f('ptat', t), f(post, f'ftemp_ptat_T{t}')
    rows.append((f'f PTAT {t} C', 'MHz', s / 1e6, p / 1e6, f'{(p / s - 1) * 100:+.2f} %', o(f'ftemp_ptat_T{t}') / 1e6 if o(f'ftemp_ptat_T{t}') else None))
for t in (-40, 27, 125, 175):
    s, p = sch_f('ref', t), f(post, f'ftemp_ref_T{t}')
    rows.append((f'f REF {t} C', 'MHz', s / 1e6, p / 1e6, f'{(p / s - 1) * 100:+.2f} %', o(f'ftemp_ref_T{t}') / 1e6 if o(f'ftemp_ref_T{t}') else None))
for t in (-40, 27, 125, 175):
    s = sch_f('ptat', t) / sch_f('ref', t)
    p = f(post, f'ftemp_ptat_T{t}') / f(post, f'ftemp_ref_T{t}')
    q = o(f'ftemp_ptat_T{t}') / o(f'ftemp_ref_T{t}') if o(f'ftemp_ptat_T{t}') and o(f'ftemp_ref_T{t}') else None
    rows.append((f'f_PTAT / f_REF {t} C', '', s, p, f'{(p / s - 1) * 100:+.2f} %', q))
# two-point fit through 25 / 100 C, residual at the other points
fs = {t: sch_f('ptat', t) for t in (-40, 25, 27, 100, 125, 175)}
fp = {t: f(post, f'ftemp_ptat_T{t}') for t in (-40, 25, 27, 100, 125, 175)}
fo = {t: o(f'ftemp_ptat_T{t}') for t in (-40, 25, 27, 100, 125, 175)} if old else {}
a_s, b_s = two_point(fs)
a_p, b_p = two_point(fp)
a_o, b_o = two_point(fo) if old and all(fo.values()) else (None, None)
rows.append(('PTAT slope of the 25/100 C line', 'kHz/C', a_s / 1e3, a_p / 1e3, f'{(a_p / a_s - 1) * 100:+.2f} %', a_o / 1e3 if a_o else None))
rows.append(('PTAT sensitivity (slope / f(25 C))', 'ppm/C', a_s / fs[25] * 1e6, a_p / fp[25] * 1e6, f'{(a_p / fp[25] - a_s / fs[25]) * 1e6:+.0f}', a_o / fo[25] * 1e6 if a_o else None))
for t in (-40, 27, 125, 175):
    rs = (fs[t] - b_s) / a_s - t
    rp = (fp[t] - b_p) / a_p - t
    ro = (fo[t] - b_o) / a_o - t if a_o else None
    rows.append((f'two-point (25/100 C) residual at {t} C', 'C', rs, rp, f'{rp - rs:+.2f}', ro))
# comparator overshoot (delay) at 27 C
rows.append(('cap peak - V_th, 27 C PTAT (I_PTAT t_d / C)', 'mV', (sch['nom_ptat_T27']['cap1_max'] - sch['nom_ptat_T27']['vth_avg']) * 1e3,
             (post['ftemp_ptat_T27']['cap1_max'] - post['ftemp_ptat_T27']['vth_avg']) * 1e3, '',
             (old['ftemp_ptat_T27']['cap1_max'] - old['ftemp_ptat_T27']['vth_avg']) * 1e3 if old else None))
rows.append(('current from 3.3 V, 27 C PTAT', 'uA', -sch['nom_ptat_T27']['i33_avg'] * 1e6, -post['ftemp_ptat_T27']['i33_avg'] * 1e6, '',
             -old['ftemp_ptat_T27']['i33_avg'] * 1e6 if old else None))
# supply
for m in ('ptat', 'ref'):
    vs = {v: f(sch, f'supply_{m}_vdd{v}_T27') for v in ('3.0', '3.3', '3.6')}
    vp = {v: f(post, f'supply_{m}_vdd{v}_T27') for v in ('3.0', '3.3', '3.6')}
    vo = {v: o(f'supply_{m}_vdd{v}_T27') for v in ('3.0', '3.3', '3.6')} if old else {}
    ss = (vs['3.6'] - vs['3.0']) / vs['3.3'] / 0.6 * 1e6
    sp = (vp['3.6'] - vp['3.0']) / vp['3.3'] / 0.6 * 1e6
    so = (vo['3.6'] - vo['3.0']) / vo['3.3'] / 0.6 * 1e6 if old and all(vo.values()) else None
    rows.append((f'supply sensitivity {m.upper()}, 3.0 .. 3.6 V, 27 C', 'ppm/V', ss, sp, f'{sp - ss:+.0f}', so))
    rows.append((f'  equivalent (f proportional to T, 300 K)', 'C/V', ss * 1e-6 * 300, sp * 1e-6 * 300, f'{(sp - ss) * 1e-6 * 300:+.2f}', so * 1e-6 * 300 if so is not None else None))
for q, u, s, p, d, *rest in rows:
    fmt = '%.4f' if u in ('MHz', '', 'kHz/C') else '%.2f' if u in ('C', 'C/V', 'mV', 'uA') else '%.0f'
    line = f'| {q} | {u} | {fmt % s} | {fmt % p} | {d} |'
    if old:
        line += (f' {fmt % rest[0]} |' if rest and rest[0] is not None else ' - |')
    out.append(line)
out.append('')
open(os.path.join(HERE, 'results', 'compare.md'), 'w').write('\n'.join(out) + '\n')
print('\n'.join(out))
