#!/usr/bin/env python3
"""Layout E5 (track T3): single-channel loop probing. sim/run_afe.py inserts the loop-gain probes (tb_afe_stb.cir) into
the subcircuits r1_afe_ch, r1_afe_ota and r1_afe_ota2, which both channel instances share, so both channels are
injected in phase and the bench measures the even-mode return ratio of the two coupled channels. This script appends
unprobed copies (suffix 'c': r1_afe_chc, r1_afe_otac, r1_afe_ota2c) at the end of the netlist and points the cosine
instance xcos at r1_afe_chc. The probe edits replace the first occurrence, i.e. the originals used by xsin, so the sine
channel is probed with the cosine channel's loops closed (single-point return ratio).
  python3 pex/single_probe.py <in.spice> <out.spice>"""
import re, sys
src = open(sys.argv[1]).read()
def body(name):
    a = src.index('.subckt %s ' % name); b = src.index('.ends', a) + len('.ends')
    return src[a:b]
copies = []
for name in ('r1_afe_ota', 'r1_afe_ota2', 'r1_afe_ch'):
    t = body(name).replace('.subckt %s ' % name, '.subckt %sc ' % name, 1)
    if name == 'r1_afe_ch':
        t = re.sub(r'(?m)( )r1_afe_ota2(\s|$)', r'\1r1_afe_ota2c\2', t)
        t = re.sub(r'(?m)( )r1_afe_ota(\s|$)', r'\1r1_afe_otac\2', t)
        assert 'r1_afe_otac' in t and 'r1_afe_ota2c' in t
    copies.append(t)
lines = src.split('\n'); n = 0
for i, l in enumerate(lines):
    if re.match(r'(?i)^xxcos\s|^xcos\s', l) and l.rstrip().endswith(' r1_afe_ch'):
        lines[i] = l.rstrip() + 'c'; n += 1
if n != 1:
    raise SystemExit('cosine instance not found (%d)' % n)
out = '\n'.join(lines)
out = out.rstrip() + '\n* single_probe.py: unprobed copies for the cosine channel\n' + '\n'.join(copies) + '\n'
open(sys.argv[2], 'w').write('* single_probe.py %s\n' % sys.argv[1].split('/')[-1] + out)
print('ok', n)
