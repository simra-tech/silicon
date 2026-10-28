#!/usr/bin/env python3
"""Revision F2 / layout E8 (track T3l): post-layout campaign specs for one RC netlist (nothing inherited from E7).
  python3 specs/make_post_e8.py <label> <netlist ($G1_RESULTS_ROOT/...)> <outdir>
writes <outdir>/post_e8.json (main set), supl_e8.json (supply-network method, DC loop gain through the supply path) and
cmstep_e8.json (CM step of the method). Corner-matched r1_bias currents: tt 10.14, ss 11.81, ff 9.00, ssx 6.94, ffx 15.36 uA;
sf/fs at the tt value 10.14 uA (assumed: r1_bias has no record at the mixed MOS corners); PVT extremes 6.9 / 15.4 uA.
Order: DC points first (offset and drift, D22), then the long loop jobs (ff, ssx, hold states, MC), then the rest.
Offset/drift set: input CM 0.5, 1.5, 2.0, 2.5, 2.8 V; per CM tt 3.3 V, tt 3.0 V, tt 3.6 V, ss (3.0 V, 125 C), ff (3.6 V, -40 C)
at the corner-matched bias and at 6.9 and 15.4 uA (CM 2.0 V at the nominal bias only); ffx at 6.9 / 15.36 uA at CM 0.5,
1.5, 2.5, 2.8 V. Loops: tt, ss, ff, sf, fs, ssx, ffx at CM 0.5 and 2.5 V (x1, x32; DM1, DM2, CM1, CM2), the bias extremes
at tt and ffx, hold states (C_L 1 fF) at the seven corners at CM 2.5 V."""
import json, os, sys
label, net, outdir = sys.argv[1:4]
CB = {'tt': '10.14u', 'ss': '11.81u', 'ff': '9.00u', 'ssx': '6.94u', 'ffx': '15.36u', 'sf': '10.14u', 'fs': '10.14u'}
J = []
def op(k, ib, cm, v=None):
    t = 'op_%s_ib%s_cm%.1f%s' % (k, ib[:-1], cm, '' if v is None else '_v%.1f' % v)
    s = dict(VCMI=cm, IB=ib)
    if v is not None:
        s['VDDA'] = v
    J.append(dict(tag=t, tmpl='tb_afe_op.cir', corner=k, subs=s))
def stb(k, ib, cm, cl='2.8p', sfx=''):
    J.append(dict(tag='stb_%s_ib%s_cm%.1f%s' % (k, ib[:-1], cm, sfx), tmpl='tb_afe_stb.cir', corner=k,
                  subs=dict(VCMI=cm, KLIST='0 5', LLIST='1 2 4 5', IB=ib, CL=cl)))
def ac(k, ib, cm):
    J.append(dict(tag='ac_%s_ib%s_cm%.1f' % (k, ib[:-1], cm), tmpl='tb_afe_ac.cir', corner=k, subs=dict(VCMI=cm, IB=ib)))
def settle(k, ib, code, vrst=0.0):
    for lv, tg in ((1, 'p100'), (-1, 'm100'), (0.5, 'p50')):
        J.append(dict(tag='settle%s_%s_x%d_%s' % ('' if vrst == 0 else '_vrst06', k, 2 ** code, tg), tmpl='tb_afe_settle_adc_rs.cir',
                      corner=k, subs=dict(CODE=code, AMP=round(lv * 0.7 / 2 ** code, 6), VCMI=2.45, CS='2.8p', VRST=vrst, IB=ib)))
# 1. DC: offset and drift
for cm in (0.5, 1.5, 2.0, 2.5, 2.8):
    for tag_ib in ('nom', '6.9u', '15.4u'):
        if cm == 2.0 and tag_ib != 'nom':
            continue
        ibt = CB['tt'] if tag_ib == 'nom' else tag_ib
        op('tt', ibt, cm); op('tt', ibt, cm, 3.0); op('tt', ibt, cm, 3.6)
        op('ss', CB['ss'] if tag_ib == 'nom' else tag_ib, cm); op('ff', CB['ff'] if tag_ib == 'nom' else tag_ib, cm)
for cm in (0.5, 1.5, 2.5, 2.8):
    op('ffx', '6.9u', cm); op('ffx', '15.36u', cm)
# 2. long jobs first
stb('ff', CB['ff'], 0.5); stb('ff', CB['ff'], 2.5); stb('ff', CB['ff'], 2.5, cl='1f', sfx='_hold')
stb('ssx', CB['ssx'], 0.5); stb('ssx', CB['ssx'], 2.5); stb('ssx', CB['ssx'], 2.5, cl='1f', sfx='_hold')
for p in range(2):
    J.append(dict(tag='acmc_ss_p%d' % p, tmpl='tb_afe_ac.cir', corner='ss', mismatch=True, subs=dict(NMC=10, SEED=101 + p, IB=CB['ss'])))
# 3. other loops
for k in ('tt', 'ss', 'sf', 'fs', 'ffx'):
    stb(k, CB[k], 0.5); stb(k, CB[k], 2.5)
for k in ('tt', 'ss', 'sf', 'fs', 'ffx'):
    stb(k, CB[k], 2.5, cl='1f', sfx='_hold')
for ib in ('6.9u', '15.4u'):
    stb('tt', ib, 0.5); stb('tt', ib, 2.5)
stb('ffx', '6.9u', 0.5); stb('ffx', '6.9u', 2.5)
# 4. AC (f_c, pole matching, output CM), noise, THD, settling
for (k, ib, cm) in (('ss', CB['ss'], 0.5), ('ss', CB['ss'], 2.5), ('tt', CB['tt'], 0.5), ('tt', CB['tt'], 2.5), ('ffx', '6.9u', 0.5),
                    ('ffx', '6.9u', 2.5), ('ffx', '15.36u', 0.5), ('ssx', CB['ssx'], 0.5), ('ff', CB['ff'], 0.5), ('tt', '15.4u', 0.5), ('tt', '6.9u', 0.5)):
    ac(k, ib, cm)
J.append(dict(tag='noise_ss_ib11.81', tmpl='tb_afe_noise.cir', corner='ss', subs=dict(IB=CB['ss'])))
for code in (5, 0):
    J.append(dict(tag='tran_tt_x%d' % 2 ** code, tmpl='tb_afe_tran.cir', corner='tt', subs=dict(CODE=code, AMP=round(0.7 / 2 ** code, 6), VCMI=2.45, IB=CB['tt'])))
settle('ss', CB['ss'], 0); settle('ss', CB['ss'], 5); settle('tt', CB['tt'], 5); settle('tt', CB['tt'], 0); settle('tt', CB['tt'], 5, vrst=0.6)
q = ('Post-layout campaign of revision F2 on layout E8, netlist %s (nothing inherited): x32 offset <= 5 mV and drift span <= 1 mV '
     '(D22) over CM 0.5-2.8 V, tt/ss/ff, 3.0/3.3/3.6 V at the nominal bias and 6.9/15.4 uA; loops PM >= 63 deg, GM >= 10 dB with '
     'validity at tt/ss/ff/sf/fs/ssx/ffx and hold states; f_c >= 1.0 MHz at ss; pole matching <= 1 %% (nominal, 20 MC at ss); output CM '
     '0.600 +- 0.030 V; noise x32 ss <= 35 uV; settling <= 0.25 LSB incl. ss x1; THD <= 0.1 %%' % label)
json.dump(dict(question=q, variants={label: dict(netlist=net)}, jobs=J), open(os.path.join(outdir, 'post_e8.json'), 'w'), indent=1)
# supply-network method: Tian probes in the vss / vdd entry wires of the sine channel (as supl_e6.json)
rx = [['r1_afe', 'vdd__xsin vss__xsin r1_afe_ch', 'vdd_ys vss_ys r1_afe_ch\nVps vss__xsin vss_ys dc 0 ac {vs1}\nIps 0 vss__xsin dc 0 ac {is1}\nVpd vdd__xsin vdd_ys dc 0 ac {vs2}\nIpd 0 vdd__xsin dc 0 ac {is2}']]
S = []
for k in ('tt', 'ss', 'ff'):
    for cm in (0.5, 2.5):
        S.append(dict(tag='supl_%s_ib%s_cm%.1f' % (k, CB[k][:-1], cm), tmpl='tb_afe_supl.cir', corner=k,
                      subs=dict(VCMI=cm, KLIST='0 5', LLIST='1 2 3', IB=CB[k], CL='2.8p')))
json.dump(dict(question='Layout E8, supply-network method (2026-10-28 amendment): DC loop gain through the supply path of the sine '
                        'channel (Tian probes in its vss and vdd entry wires) on netlist %s; <= -20 dB at tt, ss, ff' % label,
               variants={label: dict(netlist=net, rx=rx)}, jobs=S), open(os.path.join(outdir, 'supl_e8.json'), 'w'), indent=1)
C = [dict(tag='cmstep_tt_x1', tmpl='tb_afe_cmstep.cir', corner='tt', subs=dict(CODE=0, AMP=0.7, IB=CB['tt']))]
for k in ('tt', 'ss', 'ff'):
    C.append(dict(tag='cmstep_%s_x32' % k, tmpl='tb_afe_cmstep.cir', corner=k, subs=dict(CODE=5, AMP=0.021875, IB=CB[k])))
json.dump(dict(question='Layout E8, supply-network method: CM step transient (input CM 2.45 -> 0.6 V and back, vcm2 +50 mV, VDDA '
                        '-0.2 V, full-scale 100 kHz sine) on netlist %s; at most one loop-response overshoot per event (feed-through '
                        'spikes shorter than the loop time constant do not count, 2026-10-28 rule)' % label,
               variants={label: dict(netlist=net)}, jobs=C), open(os.path.join(outdir, 'cmstep_e8.json'), 'w'), indent=1)
print(len(J), len(S), len(C), 'jobs ->', outdir)
