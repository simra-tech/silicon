#!/usr/bin/env python3
"""Test 2 stage separation (track T10, fourth budget): name the stage that loses position accuracy.

Usage: G1_RESULTS_ROOT=... python3 enc_stage_check.py <run-id>

For every encoder conversion (T10HS SEQ sel=0) of a test-2 deck the script compares four stages against the
stimulus angle at the hold instant (first adc_hold rise at or before the conversion start):
  1. AFE (analog): angle of the held AFE outputs (souts, soutc differential, 100 ns after the hold) and their amplitude
  2. ADC (analog + SAR): code from the raw decisions (T10HS VA1/VB1 raw word, design weights of r1_regs) against
     the expected code 2047.5 + v_AFE / LSB (LSB of the r1_adc revision-5 record, post_tb.adc_lsb)
  3. ctrl weight path: sin/cos codes of r1_gate (T10MON ENC, the RAW_SIN / RAW_COS register source) against the
     codes of stage 2
  4. ctrl angle (CORDIC): MEAS angle (T10MON MEAS after the pair, 18 bit) against atan2 of the stage-3 codes
A constant phase (AFE and pipeline latency) is removed per stage; the residual is in degrees electrical.
Writes results/<run-id>.stages.json (summary, under 1 MB).
"""
import json
import math
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import post_tb as P  # noqa: E402

W = [1, 2, 5, 10, 20, 39, 79, 158, 315, 508, 1016, 2032, 4065, 8130]   # r1_regs WNOM, w[0] .. w[13]


def code_of(raw):
    s = sum(W[i] for i in range(14) if (raw >> i) & 1)
    return min(4095, (s + 2) >> 2)


def wrap(d):
    return (d + 180.0) % 360.0 - 180.0


def resid(errs):
    e = np.array(errs, float)
    if not len(e):
        return None
    off = math.degrees(math.atan2(np.mean(np.sin(np.radians(e))), np.mean(np.cos(np.radians(e)))))
    r = np.array([wrap(x - off) for x in e])
    return {'n': int(len(e)), 'const_deg': off, 'resid_max_deg': float(np.max(np.abs(r))),
            'resid_rms_deg': float(np.sqrt(np.mean(r ** 2)))}


def main():
    rid = sys.argv[1]
    d = os.path.join(os.environ['G1_RESULTS_ROOT'], 'r1_top', 'tb', rid)
    log = open(os.path.join(d, 'ngspice.log'), errors='replace').read()
    w = P.read_raw(os.path.join(d, 'tran.raw'))
    t = w['time']
    lsb, vr = P.adc_lsb(w)
    f, th0 = 1e4, P.THETA0_DEG
    stim = lambda tt: 360.0 * f * tt + th0
    seq = [(float(a) * 1e-9, int(b), int(n)) for a, b, n in
           re.findall(r'T10HS SEQ t0=([0-9.]+) per=[0-9.]+ sel=(\d) n=(\d+)', log)]
    va = {int(n): int(r) for _, n, r in re.findall(r'T10HS VA1 t=([0-9.]+) n=(\d+) raw=(\d+)', log)}
    vb = {int(n): int(r) for _, n, r in re.findall(r'T10HS VB1 t=([0-9.]+) n=(\d+) raw=(\d+)', log)}
    enc = [(float(a) * 1e-9, int(s), int(c), int(m)) for a, s, c, m in
           re.findall(r'T10MON ENC t=([0-9.]+) sin=(\d+) cos=(\d+) pos=\d+ meas=(\d+)', log)]
    meas = [(float(a) * 1e-9, int(m)) for a, m in re.findall(r'T10MON MEAS t=([0-9.]+) meas=(\d+)', log)]
    hold = P.crossings(t, w['adc_hold'], 0.6, True) if 'adc_hold' in w else np.array([])
    rst = re.findall(r'T10RES TBRESET t=([0-9.]+)', log)
    t_ok = float(rst[0]) * 1e-9 + 3e-6 if rst else 3e-6
    rows, e_afe, e_adc_s, e_adc_c, e_code, amp = [], [], [], [], [], []
    for t0, sel, n in seq:
        if sel != 0 or t0 < t_ok:
            continue
        hb = hold[hold <= t0 + 1e-9]
        th = float(hb[-1]) if len(hb) else t0
        tq = th + 100e-9
        vs = float(np.interp(tq, t, w['souts_p']) - np.interp(tq, t, w['souts_n']))
        vc = float(np.interp(tq, t, w['soutc_p']) - np.interp(tq, t, w['soutc_n']))
        ang_afe = math.degrees(math.atan2(vs, vc))
        e_afe.append(wrap(ang_afe - stim(th)))
        amp.append(math.hypot(vs, vc))
        row = {'n': n, 't_hold_us': th * 1e6, 'stim_deg': wrap(stim(th)), 'v_sin': vs, 'v_cos': vc,
               'afe_err_deg': e_afe[-1]}
        if n in va and n in vb:
            cs, cc = code_of(va[n]), code_of(vb[n])
            xs, xc = 2047.5 + vs / lsb, 2047.5 + vc / lsb
            e_adc_s.append(cs - xs)
            e_adc_c.append(cc - xc)
            row.update({'code_sin': cs, 'code_cos': cc, 'exp_sin': xs, 'exp_cos': xc})
            # stage 3: first ENC line after the valid of this conversion
            ec = [e for e in enc if e[0] > t0 and e[0] < t0 + 733e-9]
            if ec:
                te, es, ecc, _ = ec[0]
                # the meas field of the ENC line is the previous pair; MEAS (meas_stb) of this pair follows
                mm = [m for m in meas if te <= m[0] < te + 733e-9]
                em = mm[0][1] if mm else None
                if em is None:
                    rows.append(row)
                    continue
                row.update({'enc_sin': es, 'enc_cos': ecc, 'meas': em})
                e_code.append((es - cs, ecc - cc))
                row['cordic_err_deg'] = wrap(em / 2 ** 18 * 360.0 -
                                             math.degrees(math.atan2(es - 2048, ecc - 2048)))
                row['code_angle_err_deg'] = wrap(math.degrees(math.atan2(cs - 2047.5, cc - 2047.5)) - stim(th))
        rows.append(row)
    cod = [r['cordic_err_deg'] for r in rows if 'cordic_err_deg' in r]
    cae = [r['code_angle_err_deg'] for r in rows if 'code_angle_err_deg' in r]
    out = {'run_id': rid, 'lsb_uV': lsb * 1e6, 'vrefo_V': vr, 'conversions': len(rows),
           'stage1_afe_angle': resid(e_afe),
           'stage1_afe_amplitude_V': [float(np.min(amp)), float(np.max(amp))] if amp else None,
           'stage2_adc_code_err_lsb': {'sin_max': float(np.max(np.abs(e_adc_s))) if e_adc_s else None,
                                       'cos_max': float(np.max(np.abs(e_adc_c))) if e_adc_c else None,
                                       'sin_mean': float(np.mean(e_adc_s)) if e_adc_s else None,
                                       'cos_mean': float(np.mean(e_adc_c)) if e_adc_c else None},
           'stage2_code_angle': resid(cae),
           'stage3_ctrl_code_minus_raw_code': {'max_abs': int(max(max(abs(a), abs(b)) for a, b in e_code))
                                               if e_code else None, 'pairs': len(e_code)},
           'stage4_cordic_err_deg': {'max_abs': float(np.max(np.abs(cod))) if cod else None, 'n': len(cod)},
           'rows': rows[:60]}
    p = os.path.join(HERE, 'results', rid + '.stages.json')
    json.dump(out, open(p, 'w'), indent=1)
    s = {k: v for k, v in out.items() if k != 'rows'}
    print(json.dumps(s, indent=1))


if __name__ == '__main__':
    main()
