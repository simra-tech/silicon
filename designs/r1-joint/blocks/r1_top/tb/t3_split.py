#!/usr/bin/env python3
"""Seventh budget (T10): test 3 current-word step from two half decks (deck-time split on the pex view).

Usage: t3_split.py <run-id level 0> <run-id level 1> <out-id>

The level-0 deck runs the full test 3 sequence and stops after the level-0 reads; the level-1 deck runs with
T10_T3_LEVEL0=1. Both decks start from the same operating point and reset, so the I_A / I_B words of the two decks
form the step of post_tb.py test 3 (14 x dV / LSB, 1 % limit). The LSB is the mean of the two decks. The step after
removal of the B5 layout gain 1.0570 is reported as well (r1_adc B5 record, D16 amendment).
Writes results/<out-id>.json.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from post_tb import read_raw, adc_lsb, B5_GAIN  # noqa: E402

LV = {'A': 0.030, 'B': 0.080}     # level 1 shunt voltage (level 0 = 0 V), as post_tb.py test 3


def words(rid):
    root = os.environ.get('G1_RESULTS_ROOT', '/work/results')
    d = os.path.join(root, 'r1_top', 'tb', rid)
    res = json.load(open(os.path.join(HERE, 'results', rid + '.json')))
    w = read_raw(os.path.join(d, 'tran.raw'))
    lsb, vr = adc_lsb(w)
    return res['measurements'], lsb, vr


def main():
    r0, r1, out = sys.argv[1:4]
    m0, lsb0, vr0 = words(r0)
    m1, lsb1, vr1 = words(r1)
    lsb = 0.5 * (lsb0 + lsb1)
    o = {'run_id': out, 'level0_run': r0, 'level1_run': r1, 'adc_vref_V': [vr0, vr1], 'lsb_uV': lsb * 1e6,
         'criteria': []}
    for ch, key in (('A', 'I_A'), ('B', 'I_B')):
        if not m0.get(key) or not m1.get(key):
            o['criteria'].append({'name': 'I_%s words in both decks' % ch, 'status': 'failed'})
            continue
        w0, w1 = m0[key][0][1], m1[key][0][1]
        dm = w1 - w0
        de = 14.0 * LV[ch] / lsb
        e = (dm - de) / de * 100.0
        ec = (dm / B5_GAIN - de) / de * 100.0
        o['I_%s' % ch] = {'level0_word': w0, 'level1_word': w1, 'measured_codes': dm, 'expected_codes': de,
                          'error_pct': e, 'error_pct_b5_gain_removed': ec}
        o['criteria'].append({'name': 'I_%s code step for %.0f mV within 1 %% of 14 x dV / LSB' % (ch, LV[ch] * 1e3),
                              'value': e, 'limit': '|e| <= 1', 'status': 'passed' if abs(e) <= 1 else 'failed'})
        o['criteria'].append({'name': 'I_%s step within 1 %% after the B5 layout gain %.4f is removed' % (ch, B5_GAIN),
                              'value': ec, 'limit': '|e| <= 1', 'status': 'passed' if abs(ec) <= 1 else 'failed'})
    json.dump(o, open(os.path.join(HERE, 'results', out + '.json'), 'w'), indent=1)
    for c in o['criteria']:
        print(c['status'], c['name'], c.get('value'))


if __name__ == '__main__':
    main()
