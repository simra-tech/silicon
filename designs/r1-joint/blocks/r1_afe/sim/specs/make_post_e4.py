#!/usr/bin/env python3
"""Revision F1 / layout E4 (track T3): write the post-layout campaign spec for one RC netlist, critical jobs first.
  python3 specs/make_post_e4.py <label> <netlist ($G1_RESULTS_ROOT/...)> <out.json>
Corner-matched r1_bias currents (tt 10.14, ss 11.81, ff 9.00, ssx 6.94, ffx 15.36 uA) and the PVT extremes 6.9 / 15.4 uA
at tt and ffx. Differences to make_post_e3.py: operating points (stage-1 output CM) first; settling at 3 levels with the
0 V CDAC top-plate reset and, as information, with a 0.6 V reset; pole matching from 2 x 10 MC samples at ss."""
import json, sys
label, net, out = sys.argv[1:4]
J = []
def stb(k, ib, cm, cl='2.8p', sfx=''):
    J.append(dict(tag='stb_%s_ib%s_cm%.1f%s' % (k, ib[:-1], cm, sfx), tmpl='tb_afe_stb.cir', corner=k,
                  subs=dict(VCMI=cm, KLIST='0 5', LLIST='1 2 4 5', IB=ib, CL=cl)))
def ac(k, ib, cm):
    J.append(dict(tag='ac_%s_ib%s_cm%.1f' % (k, ib[:-1], cm), tmpl='tb_afe_ac.cir', corner=k, subs=dict(VCMI=cm, IB=ib)))
def op(k, ib, cm):
    J.append(dict(tag='op_%s_ib%s_cm%.1f' % (k, ib[:-1], cm), tmpl='tb_afe_op.cir', corner=k, subs=dict(VCMI=cm, IB=ib)))
def settle(k, ib, code, vrst=0.0):
    for lv, tg in ((1, 'p100'), (-1, 'm100'), (0.5, 'p50')):
        J.append(dict(tag='settle%s_%s_x%d_%s' % ('' if vrst == 0 else '_vrst06', k, 2 ** code, tg), tmpl='tb_afe_settle_adc.cir',
                      corner=k, subs=dict(CODE=code, AMP=round(lv * 0.7 / 2 ** code, 6), VCMI=2.45, CS='2.8p', VRST=vrst, IB=ib)))
for k, ib in (('tt', '10.14u'), ('ss', '11.81u'), ('ffx', '6.9u'), ('ff', '9.00u')):
    op(k, ib, 0.5)
op('tt', '10.14u', 2.5)
ac('tt', '10.14u', 0.5); ac('ss', '11.81u', 0.5); ac('ffx', '6.9u', 0.5)
stb('ffx', '6.9u', 0.5); stb('tt', '15.4u', 0.5); stb('tt', '6.9u', 0.5); stb('ffx', '15.36u', 0.5)
J.append(dict(tag='noise_ss_ib11.81', tmpl='tb_afe_noise.cir', corner='ss', subs=dict(IB='11.81u')))
for code in (5, 0):
    J.append(dict(tag='tran_tt_x%d' % 2 ** code, tmpl='tb_afe_tran.cir', corner='tt',
                  subs=dict(CODE=code, AMP=round(0.7 / 2 ** code, 6), VCMI=2.45, IB='10.14u')))
settle('tt', '10.14u', 5); settle('ss', '11.81u', 5); settle('tt', '10.14u', 0); settle('tt', '10.14u', 5, vrst=0.6)
for k, ib in (('ss', '11.81u'), ('ssx', '6.94u'), ('tt', '10.14u'), ('ff', '9.00u')):
    for cm in (0.5, 2.5):
        stb(k, ib, cm)
stb('ffx', '6.9u', 2.5); stb('tt', '15.4u', 2.5); stb('ffx', '15.36u', 2.5); stb('tt', '6.9u', 2.5)
for p in range(2):
    J.append(dict(tag='acmc_ss_p%d' % p, tmpl='tb_afe_ac.cir', corner='ss', mismatch=True, subs=dict(NMC=10, SEED=101 + p, IB='11.81u')))
ac('ss', '11.81u', 2.5); ac('tt', '10.14u', 2.5); ac('ffx', '6.9u', 2.5); ac('ffx', '15.36u', 0.5); ac('ssx', '6.94u', 0.5)
ac('ff', '9.00u', 0.5); ac('tt', '15.4u', 0.5); ac('tt', '6.9u', 0.5)
settle('ss', '11.81u', 0)
for k, ib in (('ssx', '6.94u'), ('ff', '9.00u')):
    stb(k, ib, 2.5, cl='1f', sfx='_hold')
spec = dict(question='Post-layout campaign of revision F1 on layout E4, netlist %s: loops (PM >= 63 deg, GM >= 10 dB) at tt/ss/ff/ssx/ffx '
                     'with the corner-matched r1_bias currents and 6.9/15.4 uA at tt and ffx, f_c >= 1.0 MHz at ss, output CM 0.600 +- 0.030 V, '
                     'stage-1 output CM (DC point), pole matching (20 MC at ss), noise x32 ss <= 35 uV, settling residual <= 0.25 LSB '
                     '(0 V reset; 0.6 V reset as information), THD <= 0.1 %%; critical jobs first' % label,
            variants={label: dict(netlist=net)}, jobs=J)
json.dump(spec, open(out, 'w'), indent=1)
print(len(J), 'jobs ->', out)
