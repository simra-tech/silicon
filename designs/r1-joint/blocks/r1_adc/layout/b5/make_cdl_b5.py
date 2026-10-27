#!/usr/bin/env python3
"""LVS reference of r1_adc layout B5 (analog part + SAR sub-macro r1_adc_sar).

  python3 make_cdl_b5.py <analog cdl> <sar cdl from pnl2cdl.py> <out cdl>

<analog cdl>: layout/r1_adc_lvs.cdl (written by r1_adc_layout.py from the netlist of record, unchanged).
<sar cdl>: r1_top/lvs/pnl2cdl.py on the release r1_adc_sar.pnl.v with the PDK sg13g2_stdcell.cdl (PDK standard
cells + subcircuit r1_adc_sar; bus pins a[k] -> a_k_).
Changes to the analog subcircuit r1_adc (format only, no device change): the 73 sar_* ports become internal nets;
new port cur_trk; one instance Xsar of r1_adc_sar joins the sar_* nets, the north pins, vdd and vss.
"""
import os
import re
import sys

an, sar, out = sys.argv[1:4]
A = open(an).read()
S = open(sar).read()
# SAR subcircuit pin order
m = re.search(r'^\.SUBCKT r1_adc_sar (.*?)$((?:\n\+.*$)*)', S, re.M | re.I)
pins = (m.group(1) + ' ' + m.group(2).replace('\n+', ' ')).split()


def top_net(p):
    """r1_adc_sar pin -> r1_adc net."""
    if p in ('VDD', 'VSS'):
        return p.lower()
    mm = re.match(r'^(adc_raw_[ab])_(\d+)_$', p)
    if mm:
        return '%s<%s>' % mm.groups()
    mm = re.match(r'^(c[pn])([ab])_(\d+)_$', p)
    if mm:
        return 'sar_%s%s%s' % mm.groups()
    if p in ('adc_hold', 'adc_sel', 'adc_start', 'adc_valid_a', 'adc_valid_b', 'clk', 'cur_trk', 'is_smp', 'por_n'):
        return p
    if p == 'mclk':
        return 'sar_mclk'
    if re.match(r'^(clk[ab]b?|clkn[ab]b?|trk[ab][01]|o[ab](p|n|np|nn))$', p):
        return 'sar_' + p
    raise ValueError(p)


conn = [top_net(p) for p in pins]
# analog r1_adc header: drop sar_* ports, add cur_trk
lines = A.split('\n')
i = [k for k, l in enumerate(lines) if l.startswith('.subckt r1_adc ')]
assert len(i) == 1
h = lines[i[0]].split()
ports = [p for p in h[2:] if not p.startswith('sar_')]
dropped = [p for p in h[2:] if p.startswith('sar_')]
assert len(dropped) == 73, len(dropped)
assert set(dropped) <= set(conn), sorted(set(dropped) - set(conn))
lines[i[0]] = '.subckt r1_adc ' + ' '.join(ports + ['cur_trk'])
j = [k for k in range(i[0], len(lines)) if lines[k].strip().lower() == '.ends'][0]
xs = 'Xsar ' + ' '.join(conn) + ' r1_adc_sar'
lines.insert(j, xs)
hdr = ('* r1_adc layout B5 LVS reference: analog part (netlist of record, layout/r1_adc_lvs.cdl) + r1_adc_sar\n'
       '* (release t2j-ll-h2312-h, PDK standard cells). Built by layout/b5/make_cdl_b5.py; format change only.\n')
_rr = os.environ.get('G1_RESULTS_ROOT')
S = S.replace(_rr, '<G1_RESULTS_ROOT>') if _rr else S
open(out, 'w').write(hdr + S + '\n' + '\n'.join(lines))
print('ports', len(ports) + 1, 'sar pins', len(pins), 'dropped', len(dropped))
