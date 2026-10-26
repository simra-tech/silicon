#!/usr/bin/env python3
"""Revision F / layout E3 (track T3): write the post-layout campaign spec for one RC netlist.
  python3 specs/make_post_e3.py <label> <netlist ($G1_RESULTS_ROOT/...)> <out.json> [part]
Corner-matched r1_bias currents (r1_bias README: tt 10.14, ss 11.81, ff 9.00, ssx 6.94, ffx 15.36 uA) and the PVT
extremes 6.9 / 15.4 uA at tt and ffx (ffx 15.4 uA = the corner-matched 15.36 uA). part: 'loops' (stb + ac + op),
'perf' (pole matching, noise, settling, THD) or 'all'."""
import json, sys
label, net, out = sys.argv[1:4]
part = sys.argv[4] if len(sys.argv) > 4 else 'all'
PTS = [('ffx', '6.9u'), ('tt', '15.4u'), ('ffx', '15.36u'), ('ss', '11.81u'), ('ssx', '6.94u'), ('tt', '10.14u'),
       ('ff', '9.00u'), ('tt', '6.9u')]          # most critical first (screens f2-f5)
J = []
if part in ('loops', 'all'):
    for k, ib in PTS:
        for cm in (0.5, 2.5):
            J.append(dict(tag='stb_%s_ib%s_cm%.1f' % (k, ib[:-1], cm), tmpl='tb_afe_stb.cir', corner=k,
                          subs=dict(VCMI=cm, KLIST='0 5', LLIST='1 2 4 5', IB=ib, CL='2.8p')))
    for k, ib in PTS:
        for cm in ((0.5, 2.5) if k in ('tt', 'ss') and ib in ('10.14u', '11.81u') else (2.5, 0.5) if k == 'ffx' else (2.5,)):
            J.append(dict(tag='ac_%s_ib%s_cm%.1f' % (k, ib[:-1], cm), tmpl='tb_afe_ac.cir', corner=k, subs=dict(VCMI=cm, IB=ib)))
    for k, ib in (('ssx', '6.94u'), ('ff', '9.00u')):     # hold phase: wiring load only (slow on the RC netlist: last)
        J.append(dict(tag='stb_%s_ib%s_cm2.5_hold' % (k, ib[:-1]), tmpl='tb_afe_stb.cir', corner=k,
                      subs=dict(VCMI=2.5, KLIST='0 5', LLIST='1 2 4 5', IB=ib, CL='1f')))
if part in ('perf', 'all'):
    for k, ib in (('ss', '11.81u'),):                     # time budget: ss only, 2 x 5 samples
        for p in range(2):
            J.append(dict(tag='acmc_%s_p%d' % (k, p), tmpl='tb_afe_ac.cir', corner=k, mismatch=True,
                          subs=dict(NMC=5, SEED=101 + p, IB=ib)))
    J.append(dict(tag='noise_ss_ib11.81', tmpl='tb_afe_noise.cir', corner='ss', subs=dict(IB='11.81u')))
    for code in (0, 5):
        J.append(dict(tag='tran_tt_x%d' % 2 ** code, tmpl='tb_afe_tran.cir', corner='tt',
                      subs=dict(CODE=code, AMP=round(0.7 / 2 ** code, 6), VCMI=2.45, IB='10.14u')))
    for k, ib in (('tt', '10.14u'), ('ss', '11.81u')):
        for code in (0, 5):
            for lv, tg in ((1, 'p100'), (-1, 'm100'), (0.5, 'p50')):     # 3 levels (time budget)
                J.append(dict(tag='settle_%s_x%d_%s' % (k, 2 ** code, tg), tmpl='tb_afe_settle_adc.cir', corner=k,
                              subs=dict(CODE=code, AMP=round(lv * 0.7 / 2 ** code, 6), VCMI=2.45, CS='2.8p', VRST=0.0, IB=ib)))
spec = dict(question='Post-layout campaign (%s) of revision F on layout E3, netlist %s: loops (PM >= 63 deg, GM >= 10 dB), '
                     'f_c >= 1.0 MHz, output CM 0.600 +- 0.030 V, pole matching <= 1 %%, noise x32 ss <= 35 uV, settling '
                     'residual <= 0.25 LSB, THD <= 0.1 %%; corner-matched r1_bias currents and 6.9/15.4 uA extremes' % (part, label),
            variants={label: dict(netlist=net)}, jobs=J)
json.dump(spec, open(out, 'w'), indent=1)
print(len(J), 'jobs ->', out)
