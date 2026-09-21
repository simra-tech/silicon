#!/usr/bin/env python3
"""Post-layout (kpex 2.5D CC netlist) versus schematic: reads the summary CSVs of both runs and writes
results/compare.md. Run after run_postlayout.py all:  python3 compare.py"""
import csv, os

HERE = os.path.dirname(os.path.abspath(__file__))
SCH = os.path.join(HERE, '..', 'results')
POST = os.path.join(HERE, 'results')


def load(path):
    with open(path) as fh:
        return {r['deck']: r for r in csv.DictReader(fh)}


def g(rows, deck, key, scale=1.0):
    v = rows.get(deck, {}).get(key, '')
    return float(v) * scale if v not in ('', None) else None


def fmt(v, digits):
    return '-' if v is None else f'{v:.{digits}f}'


rows = []
# (label, unit, schematic file/deck/key, post file/deck/key, digits, scale)
NOM = 'temp_hbt_typ_mos_tt_res_typ_3.3'
spec = [
    ('V_REF -40 C', 'V', 'temp', NOM, 'vm40', 5, 1),
    ('V_REF 27 C', 'V', 'temp', NOM, 'v27', 5, 1),
    ('V_REF 85 C', 'V', 'temp', NOM, 'v85', 5, 1),
    ('V_REF 125 C', 'V', 'temp', NOM, 'v125', 5, 1),
    ('V_REF 175 C (model extrapolated)', 'V', 'temp', NOM, 'v175', 5, 1),
    ('TC box -40..125 C', 'ppm/C', 'temp', NOM, 'tc_ind', 2, 1),
    ('TC box -40..175 C', 'ppm/C', 'temp', NOM, 'tc_full', 2, 1),
    ('I_PTAT 27 C', 'uA', 'temp', NOM, 'ip27', 4, 1e6),
    ('I_PTAT 175 C', 'uA', 'temp', NOM, 'ip175', 4, 1e6),
    ('delta-V_BE 27 C', 'mV', 'temp', NOM, 'dvbe27', 3, 1e3),
    ('total current 27 C', 'uA', 'temp', NOM, 'itot27', 3, 1e6),
    ('V_REF 27 C, hbt_bcs', 'V', 'temp', 'temp_hbt_bcs_mos_tt_res_typ_3.3', 'v27', 5, 1),
    ('V_REF 27 C, hbt_wcs', 'V', 'temp', 'temp_hbt_wcs_mos_tt_res_typ_3.3', 'v27', 5, 1),
    ('TC box -40..125 C, hbt_bcs', 'ppm/C', 'temp', 'temp_hbt_bcs_mos_tt_res_typ_3.3', 'tc_ind', 2, 1),
    ('TC box -40..125 C, hbt_wcs', 'ppm/C', 'temp', 'temp_hbt_wcs_mos_tt_res_typ_3.3', 'tc_ind', 2, 1),
    ('start-up 1 ms ramp, 27 C: t(V_REF = 0.93 V)', 'ms', 'startup', 'startup_hbt_typ_mos_tt_res_typ_T27_3.0', 't_90', 4, 1e3),
    ('start-up: V_REF at 3 ms', 'V', 'startup', 'startup_hbt_typ_mos_tt_res_typ_T27_3.0', 'vref_end', 5, 1),
    ('start-up: max V_REF', 'V', 'startup', 'startup_hbt_typ_mos_tt_res_typ_T27_3.0', 'vref_max', 5, 1),
    ('PSRR DC (1 Hz), 27 C', 'dB', 'psrr', 'psrr_hbt_typ_mos_tt_res_typ_T27_3.3', 'psrr_dc', 1, 1),
    ('PSRR 1 kHz, 27 C', 'dB', 'psrr', 'psrr_hbt_typ_mos_tt_res_typ_T27_3.3', 'psrr_1k', 1, 1),
    ('PSRR 100 kHz, 27 C', 'dB', 'psrr', 'psrr_hbt_typ_mos_tt_res_typ_T27_3.3', 'psrr_100k', 1, 1),
    ('PSRR 1 MHz, 27 C', 'dB', 'psrr', 'psrr_hbt_typ_mos_tt_res_typ_T27_3.3', 'psrr_1m', 1, 1),
    ('PSRR 1 kHz, -40 C', 'dB', 'psrr', 'psrr_hbt_typ_mos_tt_res_typ_T-40_3.3', 'psrr_1k', 1, 1),
    ('PSRR 1 kHz, 175 C', 'dB', 'psrr', 'psrr_hbt_typ_mos_tt_res_typ_T175_3.3', 'psrr_1k', 1, 1),
]
out = ['| quantity | unit | schematic | post-layout (kpex CC) | delta |', '| --- | --- | --- | --- | --- |']
for label, unit, suite, deck, key, digits, scale in spec:
    s = g(load(os.path.join(SCH, suite + '_summary.csv')), deck, key, scale)
    p = g(load(os.path.join(POST, suite + '_summary.csv')), deck, key, scale)
    d = None if s is None or p is None else p - s
    out.append(f'| {label} | {unit} | {fmt(s, digits)} | {fmt(p, digits)} | {fmt(d, digits)} |')
with open(os.path.join(POST, 'compare.md'), 'w') as fh:
    fh.write('\n'.join(out) + '\n')
print('\n'.join(out))
