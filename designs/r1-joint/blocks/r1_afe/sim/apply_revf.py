#!/usr/bin/env python3
"""Write the revision-F netlist of record (track T3, 2026-10-26) from the revision-E netlist schematic/r1_afe_revE.spice.
  python3 apply_revf.py a1cc=<um> a1cx=<um> a2cc=<um> a2cx=<um> a2rz=<um> [a1cp=<um>] [a1ccb=<um>] [wcf1=<um>] [wcf2=<um>]
OTA1 (XA1): Miller cap WCC and cross-coupled caps XCX1/XCX2 (square sides); OTA2 (XA2): Miller cap WCC, Miller zero
resistor LRZ, new cross-coupled caps XCX1 (cz1 -> outn) and XCX2 (cz2 -> outp) inside r1_afe_ota2 (used only by XA2).
Optional: OTA1 CMFB pair width WCP (XA1), OTA1 switched Miller part WCCB (XA1), anti-alias caps WCF1/WCF2. The values come from screens r1afe-screen-f2/-f3 (see README, Revision F)."""
import os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
SCH = os.path.join(HERE, '..', 'schematic')
a = dict(x.split('=') for x in sys.argv[1:])
src = open(os.path.join(SCH, 'r1_afe_revE.spice')).read()
def sub(pat, rep, s, n=1):
    s2, k = re.subn(pat, rep, s, count=n, flags=re.M)
    if k != n:
        raise SystemExit('pattern %r matched %d times, expected %d' % (pat, k, n))
    return s2
head = ('* revision F (2026-10-26, track T3 revision F / layout E3; screens r1afe-screen-f2, -f3 on the schematic and on the\n'
        '*   E3-dev2 RC netlist; revision E kept as r1_afe_revE.spice):\n'
        '*   OTA1: Miller cap WCC 25u -> %(a1cc)su square and cross-coupled caps XCX1/XCX2 15u -> %(a1cx)su square: the DM\n'
        '*         compensation (WCC^2 - WCX^2) stays about the same, the CM compensation (WCC^2 + WCX^2) grows, for the\n'
        '*         stage-1 CM loop at the low bias extreme (ffx, 6.9 uA)\n'
        '*   OTA2: new cross-coupled caps XCX1 (cz1 -> outn), XCX2 (cz2 -> outp) %(a2cx)su square, Miller cap WCC 18u -> %(a2cc)su\n'
        '*         (DM compensation kept, CM compensation x3) and Miller Rz LRZ 10u -> %(a2rz)su (stage-2 DM gain margin >= 10 dB)\n' % a)
if 'a1cp' in a:
    head += '*   OTA1: CMFB pair XMC1/XMC2 width WCP 32u -> %su (lower stage-1 CM loop gain: CM1 margin at low bias)\n' % a['a1cp']
if 'a1ccb' in a:
    head += '*   OTA1: switched Miller part WCCB 24u -> %su square (x1-x4 only; stage-1 DM loop at x1, ffx, 6.9 uA)\n' % a['a1ccb']
if 'wcf1' in a or 'wcf2' in a:
    head += '*   anti-alias caps: WCF1 31.0u -> %su, WCF2 43.6u -> %su (f_c at ss after the compensation change)\n' % (a.get('wcf1', '31.0'), a.get('wcf2', '43.6'))
src = sub(r'^(\* revision E \(2026-10-21)', head + r'\1', src)
src = sub(r'^(XCX1 cz1 outn cap_cmim) w=15u l=15u', r'\1 w=%su l=%su' % (a['a1cx'], a['a1cx']), src)
src = sub(r'^(XCX2 cz2 outp cap_cmim) w=15u l=15u', r'\1 w=%su l=%su' % (a['a1cx'], a['a1cx']), src)
# OTA2 cross caps: after the second XCC2 line (r1_afe_ota2)
parts = src.split('.subckt r1_afe_ota2 ')
assert len(parts) == 2
parts[1] = sub(r'^(XCC2 cz2 outn cap_cmim w=\{WCC\} l=\{WCC\} m=1 mm_ok=1)$',
               r'\1\n* cross-coupled Miller caps (revision F): add to the Miller cap for CM, subtract for DM\n'
               r'XCX1 cz1 outn cap_cmim w=%su l=%su m=1 mm_ok=1\nXCX2 cz2 outp cap_cmim w=%su l=%su m=1 mm_ok=1'
               % (a['a2cx'], a['a2cx'], a['a2cx'], a['a2cx']), parts[1])
src = '.subckt r1_afe_ota2 '.join(parts)
src = sub(r'^(XA1 .* r1_afe_ota .*)WCC=25u', r'\1WCC=%su' % a['a1cc'], src)
if 'a1ccb' in a:
    src = sub(r'^(XA1 .* r1_afe_ota .*)WCCB=24u', r'\1WCCB=%su' % a['a1ccb'], src)
if 'a1cp' in a:
    src = sub(r'^(XA1 .* r1_afe_ota .*)WCP=32u', r'\1WCP=%su' % a['a1cp'], src)
src = sub(r'^(XA2 .* r1_afe_ota2 .*)WCC=18u LRZ=10u', r'\1WCC=%su LRZ=%su' % (a['a2cc'], a['a2rz']), src)
if 'wcf1' in a:
    src = sub(r'WCF1=31\.0u', 'WCF1=%su' % a['wcf1'], src)
if 'wcf2' in a:
    src = sub(r'WCF2=43\.6u', 'WCF2=%su' % a['wcf2'], src)
src = sub(r'^\* r1_afe -- R1 encoder analog front end, schematic-level SPICE source \(revision D, 2026-10-20;',
          '* r1_afe -- R1 encoder analog front end, schematic-level SPICE source (revision F, 2026-10-26; revision E: r1_afe_revE.spice, revision D, 2026-10-20;', src)
open(os.path.join(SCH, 'r1_afe.spice'), 'w').write(src)
print('wrote schematic/r1_afe.spice (revision F)', a)
