#!/usr/bin/env python3
"""Tabulate the G1_DUT npn13G2 sweep from logs/*_gummel.log (written by run_all.sh).
Prints Markdown tables: VBE at IC = 1 uA and 10 uA, beta at 1 uA / 10 uA / peak,
delta-VBE between IC = 8 uA and 1 uA against (kT/q) ln 8, per corner and temperature.
Runs on the host or in the container: python3 analyse.py > results.md
"""
import glob, os, re, math
here = os.path.dirname(os.path.abspath(__file__))
k, q = 1.380649e-23, 1.602176634e-19
corners = ['hbt_typ', 'hbt_bcs', 'hbt_wcs']
temps = [-196, -40, 27, 85, 125, 150, 175]
data = {}
for f in glob.glob(os.path.join(here, 'logs', '*_gummel.log')):
    m = re.match(r'(hbt_\w+)_T([pm])(\d+)C_gummel\.log', os.path.basename(f))
    c, sgn, t = m.group(1), m.group(2), int(m.group(3))
    T = -t if sgn == 'm' else t
    vals = {}
    for line in open(f):
        mm = re.match(r'^(\w+)\s*=\s*([-+0-9.eE]+)\s*$', line.strip())
        if mm:
            vals[mm.group(1)] = float(mm.group(2))
    data[(c, T)] = vals

def row(c, T):
    v = data.get((c, T), {})
    if not v:
        return None
    Tk = T + 273.15
    ideal = k * Tk / q * math.log(8)
    tag = ' (model extrapolated)' if T < -40 or T > 125 else ''
    return (f"| {c} | {T}{tag} | {v['vbe_1u']*1e3:.1f} | {v['vbe_10u']*1e3:.1f} | {v['beta_1u']:.0f} | {v['beta_10u']:.0f} | "
            f"{v['beta_max']:.0f} | {v['dvbe_8']*1e3:.2f} | {ideal*1e3:.2f} | {(v['dvbe_8']/ideal-1)*100:+.1f} |")

print('| corner | T (C) | VBE@1uA (mV) | VBE@10uA (mV) | beta@1uA | beta@10uA | beta peak | dVBE 8:1 (mV) | (kT/q)ln8 (mV) | dev. (%) |')
print('| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |')
for c in corners:
    for T in temps:
        r = row(c, T)
        if r:
            print(r)
missing = [(c, T) for c in corners for T in temps if (c, T) not in data]
if missing:
    print('\nmissing runs:', missing)
