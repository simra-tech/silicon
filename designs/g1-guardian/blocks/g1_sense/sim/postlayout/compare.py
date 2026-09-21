#!/usr/bin/env python3
"""Schematic vs post-layout table for G1_SENSE: reads the schematic run logs logs/sense_<tag>.log and
postlayout/results_postlayout.txt (kpex CC netlist) and writes postlayout/results/compare.md.
Run from sim/: python3 postlayout/compare.py"""
import re, os
def parse(path, prefix):
    return parse_lines(open(path), prefix)


def parse_lines(lines, prefix):
    runs, cur = {}, None
    for line in lines:
        line = line.rstrip('\n')
        if line.startswith('== '):
            cur = line[3:].strip().replace(prefix, '', 1); runs[cur] = {}
            continue
        if cur is None or not line or line.startswith('#'):
            continue
        for k, v in re.findall(r'([A-Za-z_0-9%>\-]+)=\s*([-+0-9.eE]+)', line):
            key = line.split(':')[0].split()[0] + '.' + k
            runs[cur][key] = float(v)
    return runs
pl = parse('postlayout/results_postlayout.txt', 'pl_')
sch = {}
for tag in pl:
    log = 'logs/sense_%s.log' % tag
    if os.path.exists(log):
        lines = [l for l in open(log) if re.match(r'^(OP|DC|AC|PSRR|CM gain|STEP)', l)]
        sch.update(parse_lines(['== sense_' + tag] + lines, 'sense_'))
rows = [('gain (5-45 mV fit)', 'DC.gain', 1, '%.4f'), ('pedestal ISENSE(0) [V]', 'DC.ped', 1, '%.5f'),
        ('ISENSE(50 mV) [V]', 'DC.vo50', 1, '%.5f'), ('vref_buf [V]', 'OP.vref_buf', 1, '%.5f'),
        ('-3 dB bandwidth [MHz]', 'AC.f3dB', 1e-6, '%.3f'), ('step 10-90 % [ns]', 'STEP.trise10_90', 1e9, '%.1f'),
        ('step to 1 % [ns] (first crossing)', 'STEP.t_to_99pct', 1e9, '%.1f'), ('step overshoot [mV]', 'STEP.overshoot_mV', 1, '%.1f'),
        ('step: last time outside +-1 % band [ns] (post-layout deck only)', 'SETTLE_BAND.t_last_outside_1pct', 1e9, '%.1f'),
        ('PSRR 1 kHz [dB]', 'PSRR_dB(out/vdd).1k', 1, '%.1f'), ('PSRR 1 MHz [dB]', 'PSRR_dB(out/vdd).1M', 1, '%.1f'),
        ('CM gain 1 kHz [dB]', 'CM.1k', 1, '%.1f'), ('CM gain 1 MHz [dB]', 'CM.1M', 1, '%.1f'),
        ('supply current [uA]', 'OP.idd_uA', 1, '%.0f')]
out = ['# G1_SENSE schematic vs post-layout (kpex 2.5D CC), simulated', '',
       '| run | quantity | schematic | post-layout | delta |', '| --- | --- | --- | --- | --- |']
for tag in sorted(pl):
    if tag not in sch:
        out.append('| %s | (no schematic run with this tag) | | | |' % tag); continue
    for name, key, scale, fmt in rows:
        a, b = sch[tag].get(key), pl[tag].get(key)
        fa = (fmt % (a * scale)) if a is not None else 'not run / not converged'
        fb = (fmt % (b * scale)) if b is not None else 'not run / not converged'
        d = (fmt % ((b - a) * scale)) if (a is not None and b is not None) else ''
        out.append('| %s | %s | %s | %s | %s |' % (tag, name, fa, fb, d))
os.makedirs('postlayout/results', exist_ok=True)
open('postlayout/results/compare.md', 'w').write('\n'.join(out) + '\n')
print('\n'.join(out))
