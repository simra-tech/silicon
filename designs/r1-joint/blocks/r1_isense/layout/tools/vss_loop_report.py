#!/usr/bin/env python3
"""Loop gain through vss (layout revision c, track T4, 2026-10-21). Host python3, standard library.

  python3 vss_loop_report.py <raw dir: actual> <raw dir: output-stage sources ideal> [corners] > table

Inputs: the wrdata files <corner>_t<10*level+loop> (columns f dB f phase) of two stb runs made with
layout/tools/vss_tools.py variant ... probe=1 loops=1,2,8,9: the actual extraction, and the same extraction with the
output-stage source ports tied to the deck ground (vss loop removed).
  T1   main loop (1 dm_out / 2 cm_out), vss loop present          (actual run)
  T1o  main loop with the vss loop removed                         (ideal run)
  T2   Tian return ratio in the output-stage source wires, main loop closed (8 dm_vso / 9 cm_vso, actual run)
Local loop gain through vss with the main loop open, from Blackman's identity (1 + T1)(1 + T2|main open) =
(1 + T2)(1 + T1|vss open):   L = (1 + T1o)(1 + T2)/(1 + T1) - 1   (T1|vss open ~ T1o). Evaluated at the first
frequency point (100 Hz). L > 0 (phase near 0) with |L| > 1 is the positive local loop that puts the right-half-plane
pole into T1 (the stb validity flag)."""
import cmath, math, os, sys

LEVELS = ['0 mV', '+100 mV', '-20 mV']


def first(path):
    for line in open(path):
        p = line.split()
        try:
            return float(p[0]), float(p[1]), float(p[3])
        except (ValueError, IndexError):
            continue


def cval(path):
    f, db, ph = first(path)
    return f, 10 ** (db / 20.0) * cmath.exp(1j * math.radians(ph))


def db(z):
    return 20 * math.log10(abs(z)) if abs(z) > 0 else float('-inf')


def main():
    act, ide = sys.argv[1], sys.argv[2]
    corners = sys.argv[3].split(',') if len(sys.argv) > 3 else ['tt']
    print('| corner | level | mode | T1 (dB / deg) | T1, vss loop removed | T2 Tian in the output-stage return | L through vss, main loop open (dB / deg) |')
    print('| --- | --- | --- | --- | --- | --- | --- |')
    for c in corners:
        for li, lev in enumerate(LEVELS):
            for mode, l1, l2 in (('DM', 1, 8), ('CM', 2, 9)):
                p1 = os.path.join(act, '%s_t%d' % (c, 10 * li + l1))
                p0 = os.path.join(ide, '%s_t%d' % (c, 10 * li + l1))
                p2 = os.path.join(act, '%s_t%d' % (c, 10 * li + l2))
                if not all(os.path.exists(p) for p in (p1, p0, p2)):
                    print('| %s | %s | %s | not run | | | |' % (c, lev, mode)); continue
                f, t1 = cval(p1); _, t1o = cval(p0); _, t2 = cval(p2)
                L = (1 + t1o) * (1 + t2) / (1 + t1) - 1
                fm = lambda z: '%+.1f / %+.0f' % (db(z), math.degrees(cmath.phase(z)))
                print('| %s | %s | %s | %s | %s | %s | %s |' % (c, lev, mode, fm(t1), fm(t1o), fm(t2), fm(L)))


main()
