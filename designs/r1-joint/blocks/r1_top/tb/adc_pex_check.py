#!/usr/bin/env python3
"""Sixth budget (--view pex): ADC integration check of the extracted r1_adc B5 in the chip deck.

For every adc_valid_a rise: the 14 raw decisions of slice A (adc_raw_a13..0, saved with --save-extra) are weighted with
the r1_ctrl reset weights (r1_regs WNOM, 1/4 LSB) to a 12-bit code. The input is the differential voltage on the pins
of the selected channel (adc_sel high: current path outa_p - outa_n; low: encoder souts_p - souts_n) at the adc_start
rise (end of tracking). Expected code = 2047.5 + v / LSB, LSB = 454.9 uV x VREF / 1.045 V (post_tb.adc_lsb).
Writes results/<run-id>.adccheck.json. Usage: adc_pex_check.py <run-id>
"""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from post_tb import read_raw, crossings, adc_lsb  # noqa: E402

WNOM = [1, 2, 5, 10, 20, 39, 79, 158, 315, 508, 1016, 2032, 4065, 8130]   # w[i] for raw[i], 1/4 LSB
B5_GAIN = 1.0570


def main():
    rid = sys.argv[1]
    root = os.environ.get('G1_RESULTS_ROOT', '/work/results')
    w = read_raw(os.path.join(root, 'r1_top', 'tb', rid, 'tran.raw'))
    t = w['time']
    lsb, vr = adc_lsb(w)
    holds = crossings(t, w['adc_start'], 0.6, True)
    rows = []
    for tv in crossings(t, w['adc_valid_a'], 0.6, True):
        i = np.searchsorted(t, tv + 2e-9)
        if i >= len(t):
            continue
        bits = [1 if w['adc_raw_a%d' % k][i] > 0.6 else 0 for k in range(14)]
        code = sum(b * wk for b, wk in zip(bits, WNOM)) / 4.0
        if 'xu_adc.sar_trka0' in w:
            # track end of slice A (SAR track signals trka0 / trka1, falling edge), when saved
            te = sorted(list(crossings(t, w['xu_adc.sar_trka0'], 0.6, False)) + list(crossings(t, w['xu_adc.sar_trka1'], 0.6, False)))
            th = [h for h in te if h < tv]
        else:
            th = [h for h in holds if h < tv]
        if not th:
            continue
        th = th[-1]
        sel = float(np.interp(th, t, w['adc_sel'])) > 0.6 if 'adc_sel' in w else True
        p, n = ('outa_p', 'outa_n') if sel else ('souts_p', 'souts_n')
        v = float(np.interp(th, t, w[p]) - np.interp(th, t, w[n]))
        exp = 2047.5 + v / lsb
        rows.append({'t_valid_us': tv * 1e6, 't_start_us': th * 1e6, 'sel_current': sel, 'v_in_mV': v * 1e3,
                     'code': code, 'expected': exp, 'error_lsb': code - exp,
                     'error_lsb_b5_gain': (code - 2047.5) / B5_GAIN + 2047.5 - exp})
    out = {'run_id': rid, 'vref_adc_V': vr, 'lsb_uV': lsb * 1e6, 'weights': 'r1_ctrl 0.8 reset (WNOM)',
           'conversions': rows}
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results', rid + '.adccheck.json')
    json.dump(out, open(p, 'w'), indent=1)
    for r in rows:
        print('%.3f us sel_cur=%d vin %+.3f mV code %.2f exp %.2f err %+.2f LSB (B5 gain removed %+.2f)' % (
            r['t_valid_us'], r['sel_current'], r['v_in_mV'], r['code'], r['expected'], r['error_lsb'],
            r['error_lsb_b5_gain']))


if __name__ == '__main__':
    main()
