#!/usr/bin/env python3
"""Tabulate logs/*_off.log (written by run_offcurrent.sh) as Markdown:
ID at VGS = 0 for the standard and the ELT device at VDS = 0.1 V and 1.2 V, and the ratio ID_STD/ID_ELT.
python3 analyse_offcurrent.py > results.md
"""
import glob, os, re
here = os.path.dirname(os.path.abspath(__file__))
corners = ['mos_tt', 'mos_ss', 'mos_ff']
temps = [-196, -40, 27, 85, 125, 150, 175]
data = {}
for f in glob.glob(os.path.join(here, 'logs', '*_off.log')):
    m = re.match(r'(mos_\w+)_T([pm])(\d+)C_off\.log', os.path.basename(f))
    c, T = m.group(1), (-1 if m.group(2) == 'm' else 1) * int(m.group(3))
    vals = {}
    for line in open(f):
        mm = re.match(r'^(\w+)\s*=\s*([-+0-9.eE]+)\s*$', line.strip())
        if mm:
            vals[mm.group(1)] = float(mm.group(2))
    data[(c, T)] = vals
def fmt(x):
    return f'{x:.3g}'
print('| corner | T (C) | ID_STD @0.1 V (A) | ID_ELT @0.1 V (A) | ratio @0.1 V | ID_STD @1.2 V (A) | ID_ELT @1.2 V (A) | ratio @1.2 V |')
print('| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |')
for c in corners:
    for T in temps:
        v = data.get((c, T))
        if not v or 'id_std_v12' not in v:
            print(f'| {c} | {T} | run missing or failed | | | | | |')
            continue
        tag = ' (model extrapolated)' if T < -40 or T > 125 else ''
        print(f"| {c} | {T}{tag} | {fmt(v['id_std_v01'])} | {fmt(v['id_elt_v01'])} | {v['ratio_v01']:.3f} | "
              f"{fmt(v['id_std_v12'])} | {fmt(v['id_elt_v12'])} | {v['ratio_v12']:.3f} |")
