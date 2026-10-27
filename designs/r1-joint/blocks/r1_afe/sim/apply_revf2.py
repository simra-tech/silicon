#!/usr/bin/env python3
"""Write the revision-F2 netlist (track T3, layout E5, 2026-10-27) from the revision-F1 netlist schematic/r1_afe_revF1.spice.
  python3 apply_revf2.py a1cp=<um> [a1cs=<um>]
OTA1 (XA1) only: CMFB pair width WCP (CM1 loop gain) and CM-sense caps WCS (lead in the CM1 loop). Values from the
screens r1afe-screen-h1 / -h2 on the extracted E4-dev13x netlist (README, "Layout E5")."""
import os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
SCH = os.path.join(HERE, '..', 'schematic')
a = dict(x.split('=') for x in sys.argv[1:])
src = open(os.path.join(SCH, 'r1_afe_revF1.spice')).read()
def sub(pat, rep, s, n=1):
    s2, k = re.subn(pat, rep, s, count=n, flags=re.M)
    if k != n:
        raise SystemExit('pattern %r matched %d times, expected %d' % (pat, k, n))
    return s2
head = ('* revision F2 (2026-10-27, track T3 layout E5; screen r1afe-screen-h1 on the extracted E4-dev13x netlist;\n'
        '*   revision F1 kept as r1_afe_revF1.spice): OTA1 CMFB pair WCP 8u -> %(a1cp)su (lower CM1 loop gain; CM1 PM at\n'
        '*   ffx 6.9 uA CM 2.5 V x32 after layout)\n' % a)
if 'a1cs' in a:
    head += '*   OTA1 CM-sense caps WCS 22u -> %su square\n' % a['a1cs']
src = sub(r'^(\* revision F1 \(2026-10-26)', head + r'\1', src)
src = sub(r'^(XA1 .* r1_afe_ota .*)WCP=8u', r'\1WCP=%su' % a['a1cp'], src)
if 'a1cs' in a:
    src = sub(r'^(XA1 .* r1_afe_ota .*)WCS=22u', r'\1WCS=%su' % a['a1cs'], src)
src = sub(r'^\* r1_afe -- R1 encoder analog front end, schematic-level SPICE source \(revision F1, 2026-10-26;',
          '* r1_afe -- R1 encoder analog front end, schematic-level SPICE source (revision F2, 2026-10-27; revision F1: r1_afe_revF1.spice,', src)
open(os.path.join(SCH, 'r1_afe.spice'), 'w').write(src)
print('wrote schematic/r1_afe.spice (revision F2)', a)
