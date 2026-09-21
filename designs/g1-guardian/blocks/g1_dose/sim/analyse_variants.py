#!/usr/bin/env python3
"""Tabulate logs/pcell_*_off.log and logs/nw_*_off.log (from run_offcurrent_variants.sh) as Markdown.
python3 analyse_variants.py > results_variants.md"""
import glob, os, re
here = os.path.dirname(os.path.abspath(__file__))
corners = ['mos_tt', 'mos_ss', 'mos_ff']
temps = [-40, 27, 85, 125, 150, 175]
def load(prefix):
    data = {}
    for f in glob.glob(os.path.join(here, 'logs', prefix + '_*_off.log')):
        m = re.match(prefix + r'_(mos_\w+)_T([pm])(\d+)C_off\.log', os.path.basename(f))
        c, T = m.group(1), (-1 if m.group(2) == 'm' else 1) * int(m.group(3))
        vals = {}
        for line in open(f):
            mm = re.match(r'^(\w+)\s*=\s*([-+0-9.eE]+)\s*$', line.strip())
            if mm: vals[mm.group(1)] = float(mm.group(2))
        data[(c, T)] = vals
    return data
g = lambda x: f'{x:.3g}'
print('## g1_dose_pair_pcell: sg13_hv_nmos (w=3.98u l=0.45u, pad D_ELT) and sg13_lv_nmos (w=3.98u l=0.13u, pad D_STD), VGS = 0\n')
print('| corner | T (C) | ID_HV @0.1 V (A) | ID_LV @0.1 V (A) | ID_LV/ID_HV @0.1 V | ID_HV @1.2 V (A) | ID_LV @1.2 V (A) | ID_LV/ID_HV @1.2 V | ID_HV @3.3 V (A) |')
print('| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |')
d = load('pcell')
for c in corners:
    for T in temps:
        v = d.get((c, T), {})
        tag = ' (model extrapolated)' if T > 125 else ''
        if 'id_hv_v33' not in v:
            print(f'| {c} | {T}{tag} | run missing or failed | | | | | | |'); continue
        print(f"| {c} | {T}{tag} | {g(v['id_hv_v01'])} | {g(v['id_lv_v01'])} | {g(v['ratio_v01'])} | {g(v['id_hv_v12'])} | {g(v['id_lv_v12'])} | {g(v['ratio_v12'])} | {g(v['id_hv_v33'])} |")
print('\n## g1_dose_pair_nw: narrow sg13_lv_nmos (w=0.3u, pad D_ELT) and wide (w=3.98u, pad D_STD), l=0.13u, VGS = 0\n')
print('| corner | T (C) | ID_narrow @0.1 V (A) | ID_wide @0.1 V (A) | wide/narrow @0.1 V | ID_narrow @1.2 V (A) | ID_wide @1.2 V (A) | wide/narrow @1.2 V |')
print('| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |')
d = load('nw')
for c in corners:
    for T in temps:
        v = d.get((c, T), {})
        tag = ' (model extrapolated)' if T > 125 else ''
        if 'id_wide_v12' not in v:
            print(f'| {c} | {T}{tag} | run missing or failed | | | | | |'); continue
        print(f"| {c} | {T}{tag} | {g(v['id_narrow_v01'])} | {g(v['id_wide_v01'])} | {g(v['ratio_v01'])} | {g(v['id_narrow_v12'])} | {g(v['id_wide_v12'])} | {g(v['ratio_v12'])} |")
