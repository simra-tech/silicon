#!/usr/bin/env python3
"""r1_afe simulation driver. Runs inside the pinned container (flow/run.sh), cwd = block sim/ directory.

Usage (repo root, host):
  G1_CPUSET=106-108 G1_CPUS=3 G1_WORKDIR=designs/r1-joint/blocks/r1_afe/sim \
  G1_RESULTS_ROOT=<bulk results root> flow/run.sh python3 run_afe.py <campaign> <run-id>

Each campaign expands into jobs (deck template + substitutions). Decks and raw logs are written to
$G1_RESULTS_ROOT/r1_afe/<run-id>/; parsed rows go to results/<run-id>.json and runs/<run-id>/run.json.
"""
import hashlib, json, os, re, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
BLOCK = os.path.dirname(HERE)
NETLIST = os.path.join(BLOCK, 'schematic', 'r1_afe.spice')
PDK_COMMIT_FILE = '/foss/pdks/ihp-sg13g2/COMMIT'
IMAGE_ID = 'sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2'  # verified by flow/run.sh

CORNERS = {  # name: (mos, res, cap, vdda, temp)
    'tt': ('mos_tt', 'res_typ', 'cap_typ', 3.3, 27),
    'ss': ('mos_ss', 'res_wcs', 'cap_wcs', 3.0, 125),
    'ff': ('mos_ff', 'res_bcs', 'cap_bcs', 3.6, -40),
}

def mm(c):  # mismatch sections of a corner
    mos, res, cap, v, t = CORNERS[c]
    return (mos + '_mismatch', res + '_mismatch', cap + '_mismatch', v, t)

def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()

def job(name, tmpl, corner, mismatch=False, edits=(), src=None, **kw):
    mos, res, cap, v, t = mm(corner) if mismatch else CORNERS[corner]
    subs = dict(MOS=mos, RES=res, CAP=cap, VDDA=v, TEMP=t, VCMI=2.5, ACVDD=0, NMC=1, SEED=1, LSB=LSB, CL='2.8p', KLIST='0 1 2 3 4 5', LLIST='1 2 3 4 5 6 7 8',
                DIO={'tt': 'dio_tt', 'ss': 'dio_ss', 'ff': 'dio_ff'}[corner])
    subs.update(kw)
    if tmpl == 'tb_afe_stb.cir':
        edits = tuple(edits) + STB_EDITS
    d = dict(name=name, template=tmpl, corner=corner, mismatch=mismatch, subs=subs, edits=list(edits))
    if src:
        d['src'] = src          # netlist file (relative to the block directory) instead of the revision-C netlist
    return d

NETLIST_REVB = 'schematic/r1_afe_revB.spice'

# revision C: ADC full scale +-1.0 V differential (D11), 12 bit
LSB = 2.0 / 4096

# loop-gain probes (tb_afe_stb.cir): (old, new) plain-text replacements, each applied once, in order
STB_EDITS = (
    ('XA1 x1p x1n ', 'Vpa1p x1p y1p dc 0 ac {vdp1}\nVpa1n x1n y1n dc 0 ac {vdn1}\nIpa1p 0 x1p dc 0 ac {idp1}\n'
                     'Ipa1n 0 x1n dc 0 ac {idn1}\nXA1 y1p y1n '),
    ('XA2 x2p x2n ', 'Vpa2p x2p y2p dc 0 ac {vdp2}\nVpa2n x2n y2n dc 0 ac {vdn2}\nIpa2p 0 x2p dc 0 ac {idp2}\n'
                     'Ipa2n 0 x2n dc 0 ac {idn2}\nXA2 y2p y2n '),
    ('XMC1 vcmfb vcms tc', 'Vpc vcms vcmsy dc 0 ac {vc1}\nIpc 0 vcms dc 0 ac {ic1}\nXMC1 vcmfb vcmsy tc'),  # OTA1
    ('XMC1 vcmfb vcms tc', 'Vpc vcms vcmsy dc 0 ac {vc2}\nIpc 0 vcms dc 0 ac {ic2}\nXMC1 vcmfb vcmsy tc'),  # OTA2
) + tuple(e for n in ('1', '2') for e in (       # output breaks: output stage + Miller Cc on the outpi/outni side
    ('XMN7 outp ', 'Vpop outpi outp dc 0 ac {vop%s}\nVpon outni outn dc 0 ac {von%s}\n'
                   'Ipop 0 outpi dc 0 ac {iop%s}\nIpon 0 outni dc 0 ac {ion%s}\nXMN7 outpi ' % (n, n, n, n)),
    ('XMN8 outn ', 'XMN8 outni '), ('XMP7 outp ', 'XMP7 outpi '), ('XMP8 outn ', 'XMP8 outni '),
    ('XCC1 cz1 outp ', 'XCC1 cz1 outpi '), ('XCC2 cz2 outn ', 'XCC2 cz2 outni '))) + (
    ('XCC1B cb1 outp ', 'XCC1B cb1 outpi '), ('XCC2B cb2 outn ', 'XCC2B cb2 outni '))   # OTA1 switched Miller part

def inst_edit(inst, **kw):
    """Edit: change instance parameters of one instance line (first line starting with '<inst> ') of the netlist."""
    line = [l for l in open(NETLIST).read().splitlines() if l.startswith(inst + ' ')][0]
    t = line.split()
    for k, v in kw.items():
        for i, x in enumerate(t):
            if x.startswith(k + '='):
                t[i] = '%s=%s' % (k, v); break
        else:
            t.append('%s=%s' % (k, v))
    return (line, ' '.join(t))

STB_LOOPS = {1: 'dm1', 2: 'cm1', 3: 'cmfb1', 4: 'dm2', 5: 'cm2', 6: 'cmfb2', 7: 'dm1in', 8: 'cm1in'}

# development variant that oscillated in revision B (run dev-revb-02): weaker OTA1 CMFB pair 8/2, sinks 32/4
REVB02 = (('WCP=32u LCP=1u WCT=48u WN3A=0.5u WN3B=16u LN3B=2u', 'WCP=8u LCP=2u WCT=48u WN3A=0.5u WN3B=32u LN3B=4u'),)

# compensation sweeps (development, loop gain only, x1 and x32, input CM 2.5 V)
SWEEPS = {
    'stbsweep1': {
        'base': (),
        'a1cc30': (lambda: (inst_edit('XA1', WCC='30u'),))(),
        'a1rz10': (lambda: (inst_edit('XA1', LRZ='10u'),))(),
        'a1cc26rz8': (lambda: (inst_edit('XA1', WCC='26u', LRZ='8u'),))(),
        'a2cp16': (lambda: (inst_edit('XA2', WCP='16u'),))(),
        'a1cp16': (lambda: (inst_edit('XA1', WCP='16u'),))(),
    },
    'stbsweep3': {
        'cs1_12_cs2_14': (lambda: (inst_edit('XA1', WCC='26u', LRZ='8u', WCS='12u'), inst_edit('XA2', WCS='14u')))(),
        'cs1_18_cs2_20': (lambda: (inst_edit('XA1', WCC='26u', LRZ='8u', WCS='18u'), inst_edit('XA2', WCS='20u')))(),
        'cs1_18_cs2_20_cp2_32': (lambda: (inst_edit('XA1', WCC='26u', LRZ='8u', WCS='18u'), inst_edit('XA2', WCS='20u', WCP='32u')))(),
        'cs1_24_cc28_rz9_cs2_26': (lambda: (inst_edit('XA1', WCC='28u', LRZ='9u', WCS='24u'), inst_edit('XA2', WCS='26u')))(),
    },
    'stbsweep4': {
        'v1': (lambda: (inst_edit('XA1', WCC='26u', LRZ='10u', WCS='12u'), inst_edit('XA2', WN3A='24u', WN3B='8u', WCS='10u', LRZ='6u')))(),
        'v2': (lambda: (inst_edit('XA1', WCC='26u', LRZ='12u', WCS='14u'), inst_edit('XA2', WN3A='24u', WN3B='8u', WCS='8u', WCC='18u', LRZ='6u')))(),
        'v3': (lambda: (inst_edit('XA1', WCC='28u', LRZ='11u', WCS='12u'), inst_edit('XA2', WN3A='28u', WN3B='6u', WCS='10u', WCP='32u', LRZ='6u')))(),
        'v4': (lambda: (inst_edit('XA1', WCC='26u', LRZ='10u', WCS='12u'), inst_edit('XA2', WN3A='24u', WN3B='8u', WCS='6u', WCP='32u', WCC='18u', LRZ='5u')))(),
    },
    'stbsweep5': {
        'w1': (lambda: (inst_edit('XA1', WCC='28u', LRZ='11u', WCS='14u', WN3A='32u'), inst_edit('XA2', WN3A='28u', WN3B='6u', WCS='14u', WCP='32u', LRZ='6u')))(),
        'w2': (lambda: (inst_edit('XA1', WCC='26u', LRZ='12u', WCS='14u', WN3A='24u'), inst_edit('XA2', WN3A='28u', WN3B='6u', WCS='14u', WCP='32u', WCC='18u', LRZ='6u')))(),
        'w3': (lambda: (inst_edit('XA1', WCC='28u', LRZ='11u', WCS='16u', WN3A='32u', WN3B='12u'), inst_edit('XA2', WN3A='28u', WN3B='6u', WCS='16u', WCP='32u', LRZ='6u')))(),
    },
    'stbsweep6': {
        'u1': (lambda: (inst_edit('XA1', WCC='26u', LRZ='12u', WCS='20u'), inst_edit('XA2', WN3A='28u', WN3B='6u', WCS='14u', WCP='32u', WCC='18u', LRZ='6u')))(),
        'u2': (lambda: (inst_edit('XA1', WCC='26u', LRZ='12u', WCS='26u'), inst_edit('XA2', WN3A='28u', WN3B='6u', WCS='14u', WCP='32u', WCC='18u', LRZ='6u')))(),
        'u3': (lambda: (inst_edit('XA1', WCC='30u', LRZ='13u', WCS='22u'), inst_edit('XA2', WN3A='28u', WN3B='6u', WCS='14u', WCP='32u', WCC='18u', LRZ='6u')))(),
    },
    'stbsweep2': {
        'base': (),
        'revb02': REVB02,
        'a1cc26rz8': (lambda: (inst_edit('XA1', WCC='26u', LRZ='8u'),))(),
    },
}

def campaign(c):
    J = []
    if c == 'ac':
        for k in CORNERS:
            for cm in (0.5, 2.5, 2.8):
                J.append(job('ac_%s_cm%.1f' % (k, cm), 'tb_afe_ac.cir', k, VCMI=cm))
    elif c == 'ac_mc':
        for k in CORNERS:
            for part in range(2):  # 2 x 10 samples per corner, different seeds
                J.append(job('acmc_%s_p%d' % (k, part), 'tb_afe_ac.cir', k, True, NMC=10, SEED=101 + part))
    elif c == 'settle_adc':
        for k in CORNERS:
            for code in (0, 5):
                for lv, tag in ((1, 'p100'), (0.5, 'p50'), (-1, 'm100'), (-0.5, 'm50'), (0.25, 'p25')):
                    J.append(job('settleadc_%s_x%d_%s' % (k, 2 ** code, tag), 'tb_afe_settle_adc.cir', k, CODE=code,
                                 AMP=round(lv * 0.7 / 2 ** code, 6), VCMI=2.45, CS='2.8p', VRST=0.0))
    elif c == 'revb_check':
        J.append(job('acmc_tt_p0', 'tb_afe_ac.cir', 'tt', True, NMC=10, SEED=101))
        J.append(job('noise_ss', 'tb_afe_noise.cir', 'ss'))
        J.append(job('ac_ss', 'tb_afe_ac.cir', 'ss'))
        J.append(job('tran_ss_x32', 'tb_afe_tran.cir', 'ss', CODE=5, AMP=round(0.7 / 32, 6), VCMI=2.45))
        J.append(job('noise_tt', 'tb_afe_noise.cir', 'tt'))
        J.append(job('acmc_tt_p1', 'tb_afe_ac.cir', 'tt', True, NMC=10, SEED=102))
    elif c == 'cmstab':
        for k in CORNERS:
            for code in (0, 5):
                J.append(job('tran_%s_x%d' % (k, 2 ** code), 'tb_afe_tran.cir', k, CODE=code, AMP=round(0.7 / 2 ** code, 6), VCMI=2.45))
    elif c == 'cmstab2':
        for k in ('tt', 'ss'):
            J.append(job('tran_%s_x32' % k, 'tb_afe_tran.cir', k, CODE=5, AMP=round(0.7 / 32, 6), VCMI=2.45))
        J.append(job('noise_ss', 'tb_afe_noise.cir', 'ss'))
    elif c == 'checkc':
        for k in CORNERS:
            J.append(job('noise_%s' % k, 'tb_afe_noise.cir', k))
        for k in ('tt', 'ss'):
            for lv, tag in ((1, 'p100'), (0.5, 'p50'), (-1, 'm100')):
                J.append(job('settleadc_%s_x32_%s' % (k, tag), 'tb_afe_settle_adc.cir', k, CODE=5,
                             AMP=round(lv * 0.7 / 32, 6), VCMI=2.45, CS='2.8p', VRST=0.0))
    elif c == 'settlesweep1':
        P = '.param LRO=11.55u WCOD=44.7u WCOS=18.3u'
        V = {'o0': (), 'o1': ((P, '.param LRO=11.55u WCOD=1u WCOS=40u'),),
             'o2': ((P, '.param LRO=11.55u WCOD=44.7u WCOS=40u'),),
             'o3': ((P, '.param LRO=5.77u WCOD=44.7u WCOS=57.7u'),),
             'o4': ((P, '.param LRO=11.55u WCOD=1u WCOS=40u'), inst_edit('XA2', W2P='160u', W2N='80u')),
             'o5': ((P, '.param LRO=5.77u WCOD=1u WCOS=57.7u'),)}
        for vn, ed in V.items():
            for code in (0, 5):
                J.append(job('st_%s_ss_x%d_p100' % (vn, 2 ** code), 'tb_afe_settle_adc.cir', 'ss', edits=ed, CODE=code,
                             AMP=round(0.7 / 2 ** code, 6), VCMI=2.45, CS='2.8p', VRST=0.0))
    elif c == 'settlesweep2':
        P = '.param LRO=11.55u WCOD=44.7u WCOS=18.3u'
        V = {'q1': ((P, '.param LRO=11.55u WCOD=44.7u WCOS=40u'), inst_edit('XA2', W2P='160u', W2N='80u')),
             'q2': ((P, '.param LRO=11.55u WCOD=44.7u WCOS=30u'), inst_edit('XA2', W2P='160u', W2N='80u')),
             'q3': ((P, '.param LRO=11.55u WCOD=1u WCOS=40u'), inst_edit('XA2', W2P='240u', W2N='120u')),
             'q4': ((P, '.param LRO=11.55u WCOD=44.7u WCOS=40u'), inst_edit('XA2', W2P='240u', W2N='120u'))}
        for vn, ed in V.items():
            for code in (0, 5):
                J.append(job('st_%s_ss_x%d_p100' % (vn, 2 ** code), 'tb_afe_settle_adc.cir', 'ss', edits=ed, CODE=code,
                             AMP=round(0.7 / 2 ** code, 6), VCMI=2.45, CS='2.8p', VRST=0.0))
    elif c == 'cmstep':
        for k in CORNERS:
            for code in (0, 5):
                J.append(job('cmstep_%s_x%d' % (k, 2 ** code), 'tb_afe_cmstep.cir', k, CODE=code, AMP=round(0.7 / 2 ** code, 6)))
        for k in ('tt', 'ss'):   # detection check: the revision-B variant that oscillated (dev-revb-02 OTA1 sizing)
            J.append(job('cmstep_revb02_%s_x32' % k, 'tb_afe_cmstep.cir', k, src=NETLIST_REVB, edits=REVB02, CODE=5,
                         AMP=round(0.7 / 32, 6)))
            J.append(job('cmstep_revb_%s_x32' % k, 'tb_afe_cmstep.cir', k, src=NETLIST_REVB, CODE=5, AMP=round(0.7 / 32, 6)))
    elif c == 'overload':
        for k in CORNERS:
            for code in (5, 0):
                J.append(job('ovl_%s_x%d' % (k, 2 ** code), 'tb_afe_overload.cir', k, CODE=code,
                             AMP=round(0.35 / 2 ** code, 6), VCMI=2.45))
    elif c == 'rsrc':
        for k in CORNERS:
            J.append(job('rsrc_%s' % k, 'tb_afe_rsrc.cir', k, VCMI=2.5))
    elif c == 'temp':
        for tc in (-40, 27, 125):
            J.append(job('temp_tt_%dC' % tc, 'tb_afe_ac.cir', 'tt', TEMP=tc, VCMI=2.5))
    elif c == 'fcsweep':
        P = '.param LU1=153.85u LS2=67.31u LRF2=76.9u WCF1=31.0u WCF2=43.6u'
        V = {'f0': (), 'f1': (inst_edit('XA1', WCC='26u', LRZ='12u'),),
             'f2': (inst_edit('XA1', WCC='26u', LRZ='12u', WPT='72u'),),
             'f3': ((P, P.replace('WCF1=31.0u', 'WCF1=29.0u')),),
             'f4': (inst_edit('XA1', WPT='72u'),)}
        for vn, ed in V.items():
            for k, cm in (('ss', 0.5), ('ss', 2.5), ('tt', 0.5)):
                J.append(job('fc_%s_%s_cm%.1f' % (vn, k, cm), 'tb_afe_ac.cir', k, edits=ed, VCMI=cm))
    elif c == 'ccsw':
        V = {'g1': (), 'g2': (inst_edit('XA1', WCC='20u', WCCB='22.4u'),)}
        for vn, ed in V.items():
            for k in CORNERS:
                for cm in (0.5, 2.5):
                    J.append(job('ccsw_%s_%s_cm%.1f' % (vn, k, cm), 'tb_afe_stb.cir', k, edits=ed, VCMI=cm, LLIST='1 2 4 5'))
                    J.append(job('ccswac_%s_%s_cm%.1f' % (vn, k, cm), 'tb_afe_ac.cir', k, edits=ed, VCMI=cm))
    elif c == 'ccsw2':
        V = {'h1': (inst_edit('XA1', WCC='22u', WCCB='20.4u'),),
             'h2': (inst_edit('XA1', WCC='20u', WCCB='22.4u', WCS='28u'),),
             'h3': (inst_edit('XA1', WCC='22u', WCCB='20.4u', WCS='28u'),)}
        for vn, ed in V.items():
            for k in CORNERS:
                for cm in (0.5, 2.5):
                    J.append(job('ccsw_%s_%s_cm%.1f' % (vn, k, cm), 'tb_afe_stb.cir', k, edits=ed, VCMI=cm, LLIST='1 2', KLIST='3 5'))
                    J.append(job('ccswac_%s_%s_cm%.1f' % (vn, k, cm), 'tb_afe_ac.cir', k, edits=ed, VCMI=cm))
    elif c == 'ccsw3':
        V = {'k1': (inst_edit('XA1', WCC='24u', WCCB='18u', WPT='96u'),),
             'k2': (inst_edit('XA1', WCC='22u', WCCB='20.4u', WPT='96u'),),
             'k3': (inst_edit('XA1', WCC='24u', WCCB='18u', WPT='72u'),)}
        for vn, ed in V.items():
            for k in CORNERS:
                for cm in (0.5, 2.5):
                    J.append(job('ccsw_%s_%s_cm%.1f' % (vn, k, cm), 'tb_afe_stb.cir', k, edits=ed, VCMI=cm, LLIST='1 2', KLIST='0 3 5'))
                    J.append(job('ccswac_%s_%s_cm%.1f' % (vn, k, cm), 'tb_afe_ac.cir', k, edits=ed, VCMI=cm))
    elif c == 'ccsw4':
        V = {'z1': (inst_edit('XA1', WCC='22u', WCCB='20.4u', WPT='72u'), inst_edit('XA2', WN3A='20u', WN3B='10u')),
             'z2': (inst_edit('XA1', WCC='24u', WCCB='18u', WPT='72u'), inst_edit('XA2', WN3A='20u', WN3B='10u'))}
        for vn, ed in V.items():
            for k in CORNERS:
                for cm in (0.5, 2.5):
                    J.append(job('ccsw_%s_%s_cm%.1f' % (vn, k, cm), 'tb_afe_stb.cir', k, edits=ed, VCMI=cm, LLIST='1 2 4 5', KLIST='0 3 5'))
                    J.append(job('ccswac_%s_%s_cm%.1f' % (vn, k, cm), 'tb_afe_ac.cir', k, edits=ed, VCMI=cm))
    elif c == 'stbval':
        J.append(job('toy', 'tb_stb_toy.cir', 'tt'))
    elif c == 'stbq':
        J.append(job('stb_tt_cm2.5', 'tb_afe_stb.cir', 'tt'))
    elif c == 'stb':
        for k in CORNERS:
            for cm in (0.5, 2.5, 2.8):   # revision-C first pass (20261020c) also ran 1.65 V and the input breaks 7, 8
                J.append(job('stb_%s_cm%.2f' % (k, cm), 'tb_afe_stb.cir', k, VCMI=cm, LLIST='1 2 3 4 5 6'))
        for k in CORNERS:   # hold phase: only wiring capacitance at the output
            J.append(job('stb_%s_cm2.50_hold' % k, 'tb_afe_stb.cir', k, VCMI=2.5, CL='1f', LLIST='1 2 3 4 5 6'))
    elif c.startswith('stbsweep'):
        V = SWEEPS[c]
        for vn, ed in V.items():
            for k in CORNERS:
                for cm in ((2.5, 0.5) if c >= 'stbsweep5' else (2.5,)):
                    J.append(job('sw_%s_%s_cm%.1f' % (vn, k, cm), 'tb_afe_stb.cir', k, edits=ed, KLIST='0 5', VCMI=cm,
                                 LLIST='1 2 4 5'))
    elif c == 'stb_revb':   # revision B as recorded, and the dev-revb-02 variant that oscillated in transients
        for k in CORNERS:
            J.append(job('stbrevb_%s_cm2.45' % k, 'tb_afe_stb.cir', k, src=NETLIST_REVB, VCMI=2.45, KLIST='0 5'))
            J.append(job('stbrevb02_%s_cm2.45' % k, 'tb_afe_stb.cir', k, src=NETLIST_REVB, edits=REVB02, VCMI=2.45, KLIST='0 5'))
    elif c == 'mcq':
        J.append(job('acmc_tt_q', 'tb_afe_ac.cir', 'tt', True, NMC=2, SEED=7))
    elif c == 'smoke_ac':
        J.append(job('ac_tt', 'tb_afe_ac.cir', 'tt'))
    elif c == 'tran':
        for k in CORNERS:
            for code in (0, 5):
                J.append(job('tran_%s_x%d' % (k, 2 ** code), 'tb_afe_tran.cir', k, CODE=code,
                             AMP=round(0.7 / 2 ** code, 6), VCMI=2.45))
    elif c == 'settleq':
        J.append(job('settle_tt_x1', 'tb_afe_settle.cir', 'tt', CODE=0, AMP=0.7, VCMI=2.45))
    elif c == 'noiseq':
        J.append(job('noise_tt', 'tb_afe_noise.cir', 'tt'))
        J.append(job('cm_tt', 'tb_afe_cm.cir', 'tt'))
        J.append(job('psrr_tt', 'tb_afe_psrr.cir', 'tt', ACVDD=1))
    elif c == 'quick':
        J.append(job('ac_tt', 'tb_afe_ac.cir', 'tt'))
        J.append(job('ac_ss', 'tb_afe_ac.cir', 'ss'))
        J.append(job('noise_tt', 'tb_afe_noise.cir', 'tt'))
        J.append(job('tran_ss_x32', 'tb_afe_tran.cir', 'ss', CODE=5, AMP=round(0.7 / 32, 6), VCMI=2.45))
        J.append(job('settle_ss_x1', 'tb_afe_settle.cir', 'ss', CODE=0, AMP=0.7, VCMI=2.45))
        J.append(job('ac_ff', 'tb_afe_ac.cir', 'ff'))
    elif c == 'quick2':
        for k in CORNERS:
            J.append(job('ac_%s' % k, 'tb_afe_ac.cir', k))
            J.append(job('tran_%s_x32' % k, 'tb_afe_tran.cir', k, CODE=5, AMP=round(0.7 / 32, 6), VCMI=2.45))
    elif c == 'tranq':
        for k in ('tt', 'ss'):
            J.append(job('tran_%s_x32' % k, 'tb_afe_tran.cir', k, CODE=5, AMP=round(0.7 / 32, 6), VCMI=2.45))
        J.append(job('ac_ss_cm2.5', 'tb_afe_ac.cir', 'ss', VCMI=2.5))
    elif c == 'settle':
        for k in CORNERS:
            for code in (0, 5):
                for lv, tag in ((1, 'p100'), (0.5, 'p50'), (-1, 'm100')):
                    J.append(job('settle_%s_x%d_%s' % (k, 2 ** code, tag), 'tb_afe_settle.cir', k, CODE=code,
                                 AMP=round(lv * 0.7 / 2 ** code, 6), VCMI=2.45))
    elif c == 'noise':
        for k in CORNERS:
            J.append(job('noise_%s' % k, 'tb_afe_noise.cir', k))
    elif c == 'cm':
        for k in CORNERS:
            J.append(job('cm_%s' % k, 'tb_afe_cm.cir', k))
    elif c == 'psrr':
        for k in CORNERS:
            J.append(job('psrr_%s' % k, 'tb_afe_psrr.cir', k, ACVDD=1))
        for part in range(2):
            J.append(job('psrrmc_tt_p%d' % part, 'tb_afe_psrr.cir', 'tt', True, ACVDD=1, NMC=10, SEED=201 + part))
    else:
        raise SystemExit('unknown campaign ' + c)
    return J

def render(j):
    head = open(os.path.join(HERE, 'common_head.inc')).read()
    codes = open(os.path.join(HERE, 'gain_codes.inc')).read()
    s = open(os.path.join(HERE, j['template'])).read().replace('@@HEAD@@', head).replace('@@CODES@@', codes)
    s = s.replace('../schematic/r1_afe.spice', j.get('netlist', NETLIST))
    for k, v in j['subs'].items():
        s = s.replace('@@%s@@' % k, str(v))
    left = re.findall(r'@@[A-Z0-9]+@@', s)
    if left:
        raise SystemExit('unsubstituted %s in %s' % (left, j['name']))
    return s

ROW = re.compile(r'^([A-Z]+ROW)\s+(.*)$')

THD = re.compile(r'THD:\s*([-+0-9.eE]+)\s*%')

def parse(log):
    rows = []
    for line in open(log, errors='replace'):
        t = THD.search(line)
        if t:
            rows.append({'tag': 'THDROW', 'thd_percent': float(t.group(1))})
            continue
        m = ROW.match(line.strip())
        if not m:
            continue
        d = {'tag': m.group(1)}
        for kv in m.group(2).split():
            if '=' in kv:
                k, v = kv.split('=', 1)
                try:
                    d[k] = float(v)
                except ValueError:
                    d[k] = v
        rows.append(d)
    return rows

def edited_netlist(j, out):
    src = open(os.path.join(BLOCK, j['src']) if j.get('src') else NETLIST).read()
    for old, new in j['edits']:
        if old not in src:
            raise SystemExit('netlist edit target not found: %r (%s)' % (old, j['name']))
        src = src.replace(old, new, 1)
    p = os.path.join(out, j['name'] + '_netlist.spice')
    open(p, 'w').write(src)
    return p

def stb_post(j, out):
    """Phase and gain margin from the loop-gain files of tb_afe_stb.cir (dB and continuous phase vs f)."""
    rows = []
    for code in range(6):
        for lp, name in STB_LOOPS.items():
            p = os.path.join(out, '%s_t%d' % (j['name'], 10 * code + lp))  # file id = 10 * code + loop
            if not os.path.exists(p):
                continue
            f, g, ph = [], [], []
            for l in open(p):
                a = l.split()
                try:
                    f.append(float(a[0])); g.append(float(a[1])); ph.append(float(a[3]))
                except (ValueError, IndexError):
                    pass
            if not f:
                continue
            off = 360.0 * round(ph[0] / 360.0)
            ph = [x - off for x in ph]
            pm, fu, gm, f180 = None, None, None, None
            for i in range(1, len(f)):
                if g[i - 1] >= 0 > g[i]:      # unity-gain crossing (falling); keep the worst
                    a = g[i - 1] / (g[i - 1] - g[i])
                    fx = f[i - 1] * (f[i] / f[i - 1]) ** a
                    m = 180 + ph[i - 1] + a * (ph[i] - ph[i - 1])
                    if pm is None or m < pm:
                        pm, fu = m, fx
                for lim in (-180.0, -540.0):
                    if (ph[i - 1] - lim) * (ph[i] - lim) < 0:   # phase crossing of -180 (mod 360); worst = smallest margin
                        a = (ph[i - 1] - lim) / (ph[i - 1] - ph[i])
                        gx = g[i - 1] + a * (g[i] - g[i - 1])
                        if gm is None or -gx < gm:
                            gm, f180 = -gx, f[i - 1] * (f[i] / f[i - 1]) ** a
            rows.append(dict(tag='STBROW', code=code, loop=name, t_dc_db=round(g[0], 2), f_unity=fu,
                             pm_deg=None if pm is None else round(pm, 2), gm_db=None if gm is None else round(gm, 2),
                             f_180=f180, ph_min_deg=round(min(ph), 1)))
    return rows

def readcols(p):
    """wrdata file of real vectors: columns x y x y ...; returns x and the list of y columns."""
    x, ys = [], []
    for l in open(p):
        a = l.split()
        try:
            v = [float(t) for t in a]
        except ValueError:
            continue
        if not v:
            continue
        x.append(v[0]); ys.append(v[1::2])
    return x, list(zip(*ys))

def settle_time(t, y, t0, t1, final, tol):
    """Last time in [t0, t1) at which |y - final| > tol, minus t0 (0 if never)."""
    last = None
    for ti, yi in zip(t, y):
        if t0 <= ti < t1 and abs(yi - final) > tol:
            last = ti
    return 0.0 if last is None else last - t0

def window(t, y, a, b):
    return [yi for ti, yi in zip(t, y) if a <= ti < b]

def cmstep_post(j, out):
    p = os.path.join(out, j['name'] + '_cm.txt')
    if not os.path.exists(p):
        return []
    t, (o1, oc, o1c) = readcols(p)
    rows = []
    ev = [('pin_cm_down', 10e-6, 20e-6), ('pin_cm_up', 20e-6, 30e-6), ('vcm2_up', 30e-6, 35e-6),
          ('vcm2_down', 35e-6, 40e-6), ('vdda_down', 40e-6, 45e-6), ('vdda_up', 45e-6, 50e-6)]
    pre = window(t, o1, 8e-6, 10e-6)
    rows.append(dict(tag='CMSROW', event='steady_before', o1cm_pp_mV=round(1e3 * (max(pre) - min(pre)), 3),
                     ocm_pp_mV=round(1e3 * (max(window(t, oc, 8e-6, 10e-6)) - min(window(t, oc, 8e-6, 10e-6))), 3)))
    for name, a, b in ev:
        f1 = sum(window(t, o1, b - 1e-6, b)) / len(window(t, o1, b - 1e-6, b))
        f2 = sum(window(t, oc, b - 1e-6, b)) / len(window(t, oc, b - 1e-6, b))
        w1, w2, wc = window(t, o1, a, b), window(t, oc, a, b), window(t, o1c, b - 2e-6, b)
        e1, e2 = window(t, o1, b - 2e-6, b), window(t, oc, b - 2e-6, b)
        rows.append(dict(tag='CMSROW', event=name,
                         o1cm_peak_dev_mV=round(1e3 * max(abs(x - f1) for x in w1), 2),
                         o1cm_settle_ns_5mV=round(1e9 * settle_time(t, o1, a, b, f1, 5e-3), 1),
                         ocm_peak_dev_mV=round(1e3 * max(abs(x - f2) for x in w2), 2),
                         ocm_settle_ns_2mV=round(1e9 * settle_time(t, oc, a, b, f2, 2e-3), 1),
                         o1cm_pp_last2us_mV=round(1e3 * (max(e1) - min(e1)), 3),
                         ocm_pp_last2us_mV=round(1e3 * (max(e2) - min(e2)), 3),
                         o1cm_cos_pp_last2us_mV=round(1e3 * (max(wc) - min(wc)), 3)))
    return rows

def overload_post(j, out):
    p = os.path.join(out, j['name'] + '_ovl.txt')
    if not os.path.exists(p):
        return []
    t, (vs, vc, o1, oc, o1d) = readcols(p)
    fin_s = sum(window(t, vs, 40e-6, 45e-6)) / len(window(t, vs, 40e-6, 45e-6))
    fin_c = sum(window(t, vc, 40e-6, 45e-6)) / len(window(t, vc, 40e-6, 45e-6))
    pre = sum(window(t, vs, 4e-6, 5e-6)) / len(window(t, vs, 4e-6, 5e-6))
    return [dict(tag='OVLROW', vout_before=round(pre, 6), vout_final=round(fin_s, 6), vout_final_cos=round(fin_c, 6),
                 rec_ns_1lsb=round(1e9 * settle_time(t, vs, 25e-6, 40e-6, fin_s, LSB), 1),
                 rec_ns_1pct=round(1e9 * settle_time(t, vs, 25e-6, 40e-6, fin_s, 0.016), 1),
                 rec_ns_1lsb_cos=round(1e9 * settle_time(t, vc, 25e-6, 40e-6, fin_c, LSB), 1),
                 vout_ovl_max=round(max(window(t, vs, 5e-6, 25e-6)), 4), vout_ovl_min=round(min(window(t, vs, 5e-6, 25e-6)), 4),
                 o1cm_min=round(min(window(t, o1, 5e-6, 40e-6)), 4), o1cm_max=round(max(window(t, o1, 5e-6, 40e-6)), 4),
                 ocm_min=round(min(window(t, oc, 5e-6, 40e-6)), 4), ocm_max=round(max(window(t, oc, 5e-6, 40e-6)), 4),
                 o1diff_ovl_max=round(max(window(t, o1d, 5e-6, 25e-6)), 4))]

def run_one(j, out):
    deck = os.path.join(out, j['name'] + '.cir')
    log = os.path.join(out, j['name'] + '.log')
    j['subs']['RAW'] = os.path.join(out, j['name'])
    if j.get('edits') or j.get('src'):
        j['netlist'] = edited_netlist(j, out)
    open(deck, 'w').write(render(j))
    t0 = time.time()
    with open(log, 'w') as f:
        rc = subprocess.call(['ngspice', '-b', deck], stdout=f, stderr=subprocess.STDOUT, cwd=HERE)
    rows = parse(log)
    if j['template'] == 'tb_afe_stb.cir':
        rows += stb_post(j, out)
    elif j['template'] == 'tb_afe_cmstep.cir':
        rows += cmstep_post(j, out)
    elif j['template'] == 'tb_afe_overload.cir':
        rows += overload_post(j, out)
    errs = [l.strip() for l in open(log, errors='replace') if re.search(r'(?i)error|singular|timestep too small|abort', l)][:10]
    root = os.environ['G1_RESULTS_ROOT']
    subs = {k: (v.replace(root, '$G1_RESULTS_ROOT') if isinstance(v, str) else v) for k, v in j['subs'].items()}
    return dict(name=j['name'], corner=j['corner'], mismatch=j['mismatch'], subs=subs, rc=rc, edits=j['edits'],
                seconds=round(time.time() - t0, 1), rows=rows, errors=errs,
                deck=os.path.relpath(deck, os.environ['G1_RESULTS_ROOT']),
                log=os.path.relpath(log, os.environ['G1_RESULTS_ROOT']))

def main():
    camp, rid = sys.argv[1], sys.argv[2]
    root = os.environ['G1_RESULTS_ROOT']
    out = os.path.join(root, 'r1_afe', rid)
    os.makedirs(out, exist_ok=False)
    jobs = campaign(camp)
    ncpu = int(os.environ.get('OMP_NUM_THREADS', '3'))
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=ncpu) as ex:
        res = list(ex.map(lambda j: run_one(j, out), jobs))
    ver = subprocess.check_output(['ngspice', '-v']).decode(errors='replace')
    ver = [l.strip('* ').strip() for l in ver.splitlines() if 'ngspice-' in l][:1]
    templates = sorted(set(j['template'] for j in jobs)) + ['common_head.inc', 'gain_codes.inc']
    os.makedirs(os.path.join(HERE, 'results'), exist_ok=True)
    os.makedirs(os.path.join(HERE, 'runs', rid), exist_ok=True)
    json.dump(res, open(os.path.join(HERE, 'results', rid + '.json'), 'w'), indent=1)
    runj = dict(run_id=rid, campaign=camp, date_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                command='G1_CPUSET=106-108 G1_CPUS=3 G1_WORKDIR=designs/r1-joint/blocks/r1_afe/sim '
                        'G1_RESULTS_ROOT=<bulk> flow/run.sh python3 run_afe.py %s %s' % (camp, rid),
                tools=dict(ngspice=ver[0] if ver else 'unknown', image_id=IMAGE_ID,
                           pdk_commit=open(PDK_COMMIT_FILE).read().strip()),
                inputs={**{'sim/' + t: sha(os.path.join(HERE, t)) for t in templates},
                        'schematic/r1_afe.spice': sha(NETLIST), 'sim/run_afe.py': sha(__file__),
                        **({NETLIST_REVB: sha(os.path.join(BLOCK, NETLIST_REVB))} if any(j.get('src') for j in jobs) else {})},
                netlist_edits={j['name']: j['edits'] for j in jobs if j.get('edits')} or None,
                raw='$G1_RESULTS_ROOT/r1_afe/%s/' % rid, jobs=len(jobs),
                failed_jobs=[r['name'] for r in res if r['rc'] != 0 or not r['rows']],
                wall_seconds=round(time.time() - t0, 1), summary='results/%s.json' % rid,
                question='', result='', disposition='')
    json.dump(runj, open(os.path.join(HERE, 'runs', rid, 'run.json'), 'w'), indent=1)
    print(json.dumps({k: runj[k] for k in ('run_id', 'jobs', 'failed_jobs', 'wall_seconds')}))

if __name__ == '__main__':
    main()
