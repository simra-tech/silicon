#!/usr/bin/env python3
"""Write the revision-F1 netlist (track T3, 2026-10-26) from the revision-F netlist schematic/r1_afe_revF.spice.
  python3 apply_revf1.py a1cc=<um> a1cx=<um> a1cp=<um> a1ccb=<um> b6l=<um> wcf1=<um> wcf2=<um> [a1cs=<um>]
OTA1 (XA1): Miller cap WCC, cross-coupled caps XCX1/XCX2 (inside r1_afe_ota, used only by XA1), CMFB pair width WCP,
switched Miller part WCCB, CM-sense caps WCS (optional); vbnc diode XMB6 length (r1_afe_ota); anti-alias caps
WCF1/WCF2. Values from screens r1afe-screen-g1 .. -g6 (README, "Revision F1 / Layout E4")."""
import os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
SCH = os.path.join(HERE, '..', 'schematic')
a = dict(x.split('=') for x in sys.argv[1:])
src = open(os.path.join(SCH, 'r1_afe_revF.spice')).read()
def sub(pat, rep, s, n=1):
    s2, k = re.subn(pat, rep, s, count=n, flags=re.M)
    if k != n:
        raise SystemExit('pattern %r matched %d times, expected %d' % (pat, k, n))
    return s2
head = ('* revision F1 (2026-10-26, track T3 revision F1 / layout E4; screens r1afe-screen-g1 .. -g6; revision F kept as\n'
        '*   r1_afe_revF.spice):\n'
        '*   OTA1: vbnc diode XMB6 L 2u -> %(b6l)su: more drain headroom for the CMFB sinks XMN3/4 at low input CM (the\n'
        '*         stage-1 CM loop ran out of range at input CM 0.5 V; layout E3 moved the stage-1 output CM to 0.06 V at tt)\n'
        '*   OTA1: Miller cap WCC 28u -> %(a1cc)su, cross caps XCX1/XCX2 20u -> %(a1cx)su square (back to revision E: pole matching),\n'
        '*         CMFB pair WCP 16u -> %(a1cp)su, switched Miller part WCCB 24u -> %(a1ccb)su (DM1 margin after layout at ffx, 6.9 uA)\n'
        '*   anti-alias caps: WCF1 28.9u -> %(wcf1)su, WCF2 40.7u -> %(wcf2)su\n' % a)
if 'a1cs' in a:
    head += '*   OTA1: CM-sense caps WCS 22u -> %su square (lead in the stage-1 CM loop)\n' % a['a1cs']
src = sub(r'^(\* revision F \(2026-10-26)', head + r'\1', src)
pa = src.split('.subckt r1_afe_ota2 ')
assert len(pa) == 2
pa[0] = sub(r'^(XCX1 cz1 outn cap_cmim) w=20u l=20u', r'\1 w=%su l=%su' % (a['a1cx'], a['a1cx']), pa[0])
pa[0] = sub(r'^(XCX2 cz2 outp cap_cmim) w=20u l=20u', r'\1 w=%su l=%su' % (a['a1cx'], a['a1cx']), pa[0])
pa[0] = sub(r'^(XMB6 vbnc vbnc vss vss sg13_hv_nmos w=1u) l=2u', r'\1 l=%su' % a['b6l'], pa[0])
src = '.subckt r1_afe_ota2 '.join(pa)
src = sub(r'^(XA1 .* r1_afe_ota .*)WCC=28u', r'\1WCC=%su' % a['a1cc'], src)
src = sub(r'^(XA1 .* r1_afe_ota .*)WCCB=24u', r'\1WCCB=%su' % a['a1ccb'], src)
src = sub(r'^(XA1 .* r1_afe_ota .*)WCP=16u', r'\1WCP=%su' % a['a1cp'], src)
if 'a1cs' in a:
    src = sub(r'^(XA1 .* r1_afe_ota .*)WCS=22u', r'\1WCS=%su' % a['a1cs'], src)
src = sub(r'WCF1=28\.9u', 'WCF1=%su' % a['wcf1'], src)
src = sub(r'WCF2=40\.7u', 'WCF2=%su' % a['wcf2'], src)
src = sub(r'^\* r1_afe -- R1 encoder analog front end, schematic-level SPICE source \(revision F, 2026-10-26;',
          '* r1_afe -- R1 encoder analog front end, schematic-level SPICE source (revision F1, 2026-10-26; revision F: r1_afe_revF.spice,', src)
open(os.path.join(SCH, 'r1_afe.spice'), 'w').write(src)
print('wrote schematic/r1_afe.spice (revision F1)', a)
