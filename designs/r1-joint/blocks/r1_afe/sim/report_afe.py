#!/usr/bin/env python3
"""Reduce the revision-A/B/C campaign results to the README numbers and fill question/result/disposition in each
runs/<run-id>/run.json. Usage (block sim/ dir, host python3): python3 report_afe.py <suffix>
Raw spectra for the noise band integrals are read from $G1_RESULTS_ROOT (must be set)."""
import json, math, os, sys

G = ['x1', 'x2', 'x4', 'x8', 'x16', 'x32']
LSB = 2.4 / 4096      # revisions A and B (2.4 Vpp SAR full scale); revision C (suffix 20261020c, 20261020c2): 2.0 / 4096 (D11)
ROOT = os.environ['G1_RESULTS_ROOT']

REVC = lambda sfx: len(sfx) > 8 and sfx[8] in 'cdef'   # suffix yyyymmdd + revision letter (+ pass); C, D, E and F share the rev-C reductions
REVD = lambda sfx: len(sfx) > 8 and sfx[8] in 'def'

def load(c, sfx):
    p = 'results/r1afe-%s-%s.json' % (c, sfx)
    return json.load(open(p)) if os.path.exists(p) else None

def rows(res, tag):
    for j in res:
        for r in j['rows']:
            if r['tag'] == tag:
                yield j, r

def band(path, lo, hi):
    f, s = [], []
    for l in open(path):
        a = l.split()
        try:
            f.append(float(a[0])); s.append(float(a[1]))
        except (ValueError, IndexError):
            pass
    acc = 0.0
    for i in range(1, len(f)):
        if f[i] <= lo or f[i - 1] >= hi:
            continue
        acc += 0.5 * (s[i] ** 2 + s[i - 1] ** 2) * (f[i] - f[i - 1])
    return math.sqrt(acc)

def fill(rid, question, result, disposition):
    p = 'runs/%s/run.json' % rid
    if not os.path.exists(p):
        return
    d = json.load(open(p))
    d.update(question=question, result=result, disposition=disposition)
    json.dump(d, open(p, 'w'), indent=1)

def main(sfx):
    global LSB
    if REVC(sfx):
        LSB = 2.0 / 4096
    if REVD(sfx):
        LSB = 1.8 / 4096     # D16: ADC full scale +-0.9 V
    S = {'lsb_V': LSB}
    # ---------------- AC nominal
    ac = load('ac', sfx)
    if ac:
        t = {}
        for j, r in rows(ac, 'ACROW'):
            c = j['corner']; cm = j['subs']['VCMI']; k = G[int(r['code'])]
            t.setdefault(c, {}).setdefault(str(cm), {})[k] = dict(
                gain=10 ** (r['gs0'] / 20), f3_mhz=min(r['fs3'], r['fc3']) / 1e6, peak_db=max(r['pks'], r['pkc']),
                ph100k=r['ps100'], ph1m=r['ps1m'])
        op = {}
        for j, r in rows(ac, 'OPROW'):
            op.setdefault(j['corner'], []).append((r['ocms'], r['o1cm'], r['idd']))
        f3min = min(v['f3_mhz'] for c in t for cm in t[c] for v in t[c][cm].values())
        pk = max(v['peak_db'] for c in t for cm in t[c] for v in t[c][cm].values())
        steps = {}
        for c in t:
            for cm in t[c]:
                g1 = t[c][cm]['x1']['gain']
                for i, k in enumerate(G):
                    e = 100 * (t[c][cm][k]['gain'] / (g1 * 2 ** i) - 1)
                    steps[k] = max(steps.get(k, 0), abs(e))
        S['ac'] = dict(table=t, f3_min_mhz=f3min, peaking_max_db=pk, step_error_max_pct=steps,
                       ocm_range=[min(o[0] for c in op for o in op[c]), max(o[0] for c in op for o in op[c])],
                       idd_ma={c: [min(o[2] for o in op[c]) * 1e3, max(o[2] for o in op[c]) * 1e3] for c in op})
        fill('r1afe-ac-' + sfx, 'Gain at each step, -3 dB bandwidth (f_c >= 1 MHz), peaking, phase; tt/ss/ff; input CM 0.5/2.5/2.8 V; both channels',
             'f3 min %.3f MHz (all corners, CM, steps); peaking max %.3f dB; step-ratio error max %.2f %%; output CM %.3f-%.3f V' % (
                 f3min, pk, max(steps.values()), S['ac']['ocm_range'][0], S['ac']['ocm_range'][1]),
             'passed' if f3min >= 1.0 and pk < 1 else 'failed')
    # ---------------- AC MC
    mc = load('ac_mc', sfx)
    if mc:
        m = {}
        for j, r in rows(mc, 'ACROW'):
            if isinstance(r.get('fs3'), str):
                continue
            c = j['corner']; k = G[int(r['code'])]
            d = m.setdefault(c, {}).setdefault(k, dict(df3=[], dph=[], dg=[], dph1m=[], f3=[]))
            d['df3'].append(100 * (r['fs3'] / r['fc3'] - 1)); d['dph'].append(r['ps100'] - r['pc100'])
            d['dph1m'].append(r['ps1m'] - r['pc1m']); d['f3'].append(min(r['fs3'], r['fc3']) / 1e6)
            d['dg'].append(100 * (10 ** ((r['gs0'] - r['gc0']) / 20) - 1))
        out = {}
        for c in m:
            for k in m[c]:
                d = m[c][k]
                sd = lambda v: math.sqrt(sum((x - sum(v) / len(v)) ** 2 for x in v) / max(1, len(v) - 1))
                out.setdefault(c, {})[k] = dict(n=len(d['df3']), df3_maxabs_pct=max(abs(x) for x in d['df3']), df3_sd_pct=sd(d['df3']),
                                                dph100k_maxabs_deg=max(abs(x) for x in d['dph']), dph1m_maxabs_deg=max(abs(x) for x in d['dph1m']),
                                                dgain_maxabs_pct=max(abs(x) for x in d['dg']), f3_min_mhz=min(d['f3']))
        worst = max(v['df3_maxabs_pct'] for c in out for v in out[c].values())
        wph = max(v['dph100k_maxabs_deg'] for c in out for v in out[c].values())
        n = min(v['n'] for c in out for v in out[c].values())
        S['ac_mc'] = dict(table=out, df3_worst_pct=worst, dph100k_worst_deg=wph, n_per_corner=n)
        fill('r1afe-ac_mc-' + sfx, 'Pole matching between the two channels with mismatch (mm_ok=1), 20 samples at tt, ss, ff, every gain step',
             'worst |f3 mismatch| %.3f %%, worst |phase mismatch at 100 kHz| %.4f deg, n = %d per corner and step' % (worst, wph, n),
             'passed' if worst <= 1.0 else 'failed')
    # ---------------- noise
    nz = load('noise', sfx)
    if nz:
        t = {}
        for j, r in rows(nz, 'NZROW'):
            k = G[int(r['code'])]
            spec = os.path.join(ROOT, os.path.dirname(j['deck']), j['name'] + '_spec_code%d' % int(r['code']))
            bands = {}
            if os.path.exists(spec):
                for lo, hi in ((1, 1e3), (1e3, 1e5), (1e5, 2e6), (2e6, 1e7), (1e7, 1e8)):
                    bands['%g-%g' % (lo, hi)] = band(spec, lo, hi) * 1e6
            t.setdefault(j['corner'], {})[k] = dict(gain=r['gain'], out_uV=r['onoise_rms'] * 1e6, out_lsb=r['onoise_rms'] / LSB,
                                                    in_uV=r['in_rms'] * 1e6, in1k=r['in1k'] * 1e9, in10k=r['in10k'] * 1e9,
                                                    in100k=r['in100k'] * 1e9, in1m=r['in1m'] * 1e9, bands_out_uV=bands)
        x1 = max(t[c]['x1']['out_uV'] for c in t); x32 = max(t[c]['x32']['in_uV'] for c in t)
        S['noise'] = dict(table=t, x1_out_worst_uV=x1, x32_in_worst_uV=x32)
        fill('r1afe-noise-' + sfx, 'Noise at every step, 1 Hz-100 MHz; required x1 (output <= 0.41 LSB rms) and x32 (input <= 35 uV rms)',
             'x1 output worst %.0f uV rms (%.2f LSB of %.3f mV); x32 input-referred worst %.1f uV rms' % (x1, x1 * 1e-6 / LSB, LSB * 1e3, x32),
             ('x1: %s; x32 <= 35 uV: %s; x32 with >= 5 %% margin (<= 33.25 uV, rev D item 5): %s' % (
                 'passed' if x1 * 1e-6 / LSB <= 0.41 else 'failed', 'passed' if x32 <= 35 else 'failed',
                 'passed' if x32 <= 33.25 else 'failed')) if REVD(sfx) else
             ('passed' if x1 * 1e-6 / LSB <= 0.41 and x32 <= 35 else 'failed'))
    # ---------------- CM sweep
    cm = load('cm', sfx)
    if cm:
        t = {}
        for j, r in rows(cm, 'CMROW'):
            t.setdefault(j['corner'], {}).setdefault(G[int(r['code'])], {})[str(r['cm'])] = dict(
                gain=r['gain'], ocm=r['ocm'], offset=r['offset'], iafe_uA=r['iafe'] * 1e6, ipad_nA=r['ipad'] * 1e9)
        flat = {}
        for c in t:
            for k in t[c]:
                g = [t[c][k][x]['gain'] for x in ('0.5', '1.0', '1.65', '2.5', '2.8')]
                flat[c + '_' + k] = 100 * (max(g) - min(g)) / g[2]
        ipad = {c: {x: max(t[c][k][x]['ipad_nA'] for k in t[c]) for x in ('2.8', '3.0', '3.3')} for c in t}
        S['cm'] = dict(table=t, gain_variation_0p5_2p8_pct=flat, pad_current_nA=ipad)
        wf = max(flat.values())
        fill('r1afe-cm-' + sfx, 'Input CM 0-3.3 V with stock sg13g2_IOPadAnalog on all four pins: gain flatness inside 0.5-2.8 V; pad leakage up to 3.3 V',
             'gain variation inside 0.5-2.8 V max %.2f %%; pad current at 2.8/3.0 V worst %.2f/%.2f nA' % (
                 wf, max(ipad[c]['2.8'] for c in ipad), max(ipad[c]['3.0'] for c in ipad)),
             'passed against limits set in this step (gain within 2 %, pad current < 1 uA at 2.8 V; no specification limit)' if wf < 2.0 and max(ipad[c]['2.8'] for c in ipad) < 1000 else 'failed')
    # ---------------- PSRR
    ps = load('psrr', sfx)
    if ps:
        t = {}
        for j, r in rows(ps, 'PSROW'):
            key = j['corner'] + ('_mc' if j['mismatch'] else '')
            d = t.setdefault(key, {}).setdefault(G[int(r['code'])], dict(p20k=[], p1m=[], cm20k=[], cm1m=[]))
            d['p20k'] += [r['psrr_s_20k'], r['psrr_c_20k']]; d['p1m'] += [r['psrr_s_1m'], r['psrr_c_1m']]
            d['cm20k'].append(r['vdd2ocm_20k_db']); d['cm1m'].append(r['vdd2ocm_1m_db'])
        out = {k: {g: dict(psrr20k_min_db=min(v['p20k']), psrr1m_min_db=min(v['p1m']), vdd_to_ocm_20k_db=max(v['cm20k']),
                           vdd_to_ocm_1m_db=max(v['cm1m'])) for g, v in t[k].items()} for k in t}
        S['psrr'] = out
        if 'tt_mc' in out:
            w20 = min(out['tt_mc'][g]['psrr20k_min_db'] for g in out['tt_mc']); w1m = min(out['tt_mc'][g]['psrr1m_min_db'] for g in out['tt_mc'])
            fill('r1afe-psrr-' + sfx, 'Differential PSRR from VDDA at 20 kHz and 1 MHz (nominal corners and 20 mismatch samples at tt), x1 and x32',
                 'mismatch worst PSRR %.1f dB at 20 kHz, %.1f dB at 1 MHz (input-referred, A_dm / A_vdda)' % (w20, w1m),
                 'passed against a derived limit set after the run (>= 40 dB: 10 mVpp ripple below the x32 input noise; no specification limit)' if min(w20, w1m) >= 40 else 'failed')
    # ---------------- tran
    tr = load('tran', sfx)
    if tr:
        t = {}
        for j in tr:
            th = [r['thd_percent'] for r in j['rows'] if r['tag'] == 'THDROW']
            tw = [r for r in j['rows'] if r['tag'] == 'TRROW']
            if tw:
                r = tw[0]
                t[j['name']] = dict(thd_sin_pct=th[0] if th else None, thd_cos_pct=th[1] if len(th) > 1 else None,
                                    vdiff_pk=r['smax'], out_min=min(r['splo'], r['snlo']), out_max=max(r['sphi'], r['snhi']),
                                    ocm=r.get('ocm'), cm_pp_out=r.get('ocmpp'), cm_pp_stage1=r.get('o1cmpp'))
        worst = max(v['thd_sin_pct'] for v in t.values())
        S['tran'] = dict(table=t, thd_worst_pct=worst, thd_worst_db=20 * math.log10(worst / 100))
        fill('r1afe-tran-' + sfx, '100 kHz full-scale sine (%s Vpp differential out) at x1 and x32, tt/ss/ff: THD, swing, CM stability' % ('1.44' if REVD(sfx) else ('1.6' if REVC(sfx) else '2.0')),
             'THD worst %.3f %% (%.1f dB); outputs %.3f-%.3f V' % (worst, 20 * math.log10(worst / 100), min(v['out_min'] for v in t.values()), max(v['out_max'] for v in t.values())),
             'passed' if worst <= 0.1 else 'failed')
    # ---------------- settle
    for camp, pre, qtxt in (('settle', 'settle', 'Track-and-hold model (2 pF per side, reset to 0.6 V, 250 ns track at 2 MSPS)'),
                            ('settle_adc', 'settleadc', 'r1_adc-matched track-and-hold model (2.8 pF per side, top plate reset to 0 V, 250 ns track at 2 MSPS)')):
      st = load(camp, sfx)
      if st:
          e = {}
          for j in st:
              r = [x for x in j['rows'] if x['tag'] == 'STROW']
              tt = [x for x in j['rows'] if x['tag'] == 'STTROW']
              if r and not isinstance(r[-1]['err_s'], str):
                  e[j['name']] = dict(vout0=r[-1]['vout0'], err_mV=r[-1]['err_s'] * 1e3, err_lsb=r[-1]['lsb_s'],
                                      err_c_lsb=r[-1]['lsb_c'], track=[(x['t'], x['lsb_s']) for x in tt])
          lin = {}
          for c in ('tt', 'ss', 'ff'):
              for g in ('x1', 'x32'):
                  pts = [e[n] for n in e if n.startswith('%s_%s_%s_' % (pre, c, g))]
                  if len(pts) >= 3:                       # least-squares line err = k * vout + o over all levels
                      n = len(pts); sx = sum(q['vout0'] for q in pts); sy = sum(q['err_mV'] for q in pts)
                      sxx = sum(q['vout0'] ** 2 for q in pts); sxy = sum(q['vout0'] * q['err_mV'] for q in pts)
                      k = (n * sxy - sx * sy) / (n * sxx - sx ** 2); o = (sy - k * sx) / n
                      res = max(abs(q['err_mV'] - (k * q['vout0'] + o)) for q in pts)
                      lin['%s_%s' % (c, g)] = dict(gain_err_pct=k / 10, offset_mV=o, nonlinear_residual_lsb=res * 1e-3 / LSB,
                                                   err_fs_lsb=max(abs(q['err_lsb']) for q in pts), n_levels=n)
          S[camp] = dict(table=e, linear_fit=lin)
          wr = max(abs(v['nonlinear_residual_lsb']) for v in lin.values()) if lin else None
          we = max(abs(v['err_fs_lsb']) for v in lin.values()) if lin else None
          lim = 0.25 if REVC(sfx) else 0.5
          fill('r1afe-%s-%s' % (camp, sfx), qtxt + ': sampled error at end of track, linearity of the error',
               'error at full scale worst %.2f LSB; after removing a linear gain/offset fit, residual worst %.3f LSB (LSB %.3f mV)' % (we, wr, LSB * 1e3),
               ('total error: %s against %.2f LSB; non-linear residual: %s against %.2f LSB (the linear part is a gain error common to both channels)' % (
                   'passed' if we <= lim else 'failed', lim, 'passed' if wr <= lim else 'failed', lim)) if REVC(sfx) else
               ('passed (residual <= 0.5 LSB; the linear part is a gain error common to both channels)' if wr is not None and wr <= 0.5 else 'failed'))
    # ---------------- loop gain (revision C)
    for camp in ('stb', 'stb_revb'):
        st = load(camp, sfx)
        if not st:
            continue
        t, worst = {}, {}
        for j, r in rows(st, 'STBROW'):
            key = j['name']
            t.setdefault(key, {})['x%d_%s' % (2 ** int(r['code']), r['loop'])] = dict(
                t_dc_db=r['t_dc_db'], f_unity_mhz=None if r['f_unity'] is None else round(r['f_unity'] / 1e6, 2),
                pm_deg=r['pm_deg'], gm_db=r['gm_db'])
            grp = ('revb02_' if 'revb02' in key else ('revb_' if 'revb' in key else '')) + r['loop']
            pm = r['pm_deg'] if r['pm_deg'] is not None else 999.0
            if r.get('pm_valid') is False:
                pm = -999.0          # rev D: invalid Bode margin (right-half-plane pole) counts as a failure
            if grp not in worst or pm < worst[grp]['pm_deg']:
                worst[grp] = dict(pm_deg=pm, gm_db=r['gm_db'], where='%s x%d' % (key, 2 ** int(r['code'])))
            if r['gm_db'] is not None and (grp + '_gm' not in worst or r['gm_db'] < worst[grp + '_gm']['gm_db']):
                worst[grp + '_gm'] = dict(gm_db=r['gm_db'], where='%s x%d' % (key, 2 ** int(r['code'])))
        S[camp] = dict(table=t, worst=worst)
        if camp == 'stb':
            ok = all(worst[l]['pm_deg'] >= lim for l, lim in (('dm1', 55), ('dm2', 55), ('cm1', 60), ('cm2', 60)))
            fill('r1afe-stb-' + sfx, 'Loop gain (Tian double injection) of the stage-1 and stage-2 differential and common-mode loops, '
                 'broken at the OTA outputs (plus CMFB-node and OTA-input breaks as cross-checks); tt/ss/ff, input CM 0.5/1.65/2.5/2.8 V, '
                 'every gain step, track load (100 ohm + 2.8 pF) and hold load',
                 'worst PM: dm1 %.1f, cm1 %.1f, dm2 %.1f, cm2 %.1f deg; worst GM: dm1 %.1f, cm1 %.1f, dm2 %.1f, cm2 %.1f dB' % (
                     worst['dm1']['pm_deg'], worst['cm1']['pm_deg'], worst['dm2']['pm_deg'], worst['cm2']['pm_deg'],
                     worst['dm1_gm']['gm_db'], worst['cm1_gm']['gm_db'], worst['dm2_gm']['gm_db'], worst['cm2_gm']['gm_db']),
                 'passed (PM >= 55 deg differential, >= 60 deg common mode)' if ok else 'failed')
        else:
            fill('r1afe-stb_revb-' + sfx, 'Method check: the same loop-gain analysis on the revision-B netlist and on the dev-revb-02 '
                 'variant (OTA1 CMFB pair 8/2, sinks 32/4) that oscillated in transients; x1 and x32, input CM 2.45 V',
                 'revision B worst cm1 PM %.1f deg (%s), dm1 PM %.1f deg; dev-revb-02 worst cm1 PM %.1f deg (%s)' % (
                     worst['revb_cm1']['pm_deg'], worst['revb_cm1']['where'], worst['revb_dm1']['pm_deg'],
                     worst['revb02_cm1']['pm_deg'], worst['revb02_cm1']['where']),
                 'record: revision B below target (superseded); a negative CM phase margin predicts the observed oscillation')
    # ---------------- cross corners (revision D, item 6)
    sx = load('stbx', sfx)
    if sx:
        t, worst = {}, {}
        for j, r in rows(sx, 'STBROW'):
            k = j['corner']
            key = '%s_x%d' % (r['loop'], 2 ** int(r['code']))
            pm = r['pm_deg'] if r['pm_deg'] is not None else 999.0
            if r.get('pm_valid') is False:
                pm = -999.0          # invalid Bode margin (right-half-plane pole) counts as a failure
            t.setdefault(j['name'], {})[key] = dict(pm_valid=r.get('pm_valid'), pm_deg=r['pm_deg'], gm_db=r['gm_db'], f_unity_mhz=None if r['f_unity'] is None else round(r['f_unity'] / 1e6, 2))
            w = worst.setdefault(k, {})
            if r['loop'] not in w or pm < w[r['loop']]['pm_deg']:
                w[r['loop']] = dict(pm_deg=pm, gm_db=r['gm_db'], where='%s %s' % (j['name'], key))
        ok = all(worst[k][l]['pm_deg'] >= lim for k in worst for l, lim in (('dm1', 55), ('dm2', 55), ('cm1', 60), ('cm2', 60)))
        S['stbx'] = dict(table=t, worst=worst)
        fill('r1afe-stbx-' + sfx, 'Loop gain (Tian, output breaks dm1 cm1 dm2 cm2) at x1 and x32, input CM 0.5 and 2.5 V, at tt, ss (3.0 V, 125 C), '
             'ff (3.6 V, -40 C), the mixed MOS corners sf and fs (3.3 V, 27 C) and the cross terms ssx (ss, 3.6 V, -40 C) and ffx (ff, 3.0 V, 125 C)',
             '; '.join('%s: dm1 %.1f cm1 %.1f dm2 %.1f cm2 %.1f' % (k, worst[k]['dm1']['pm_deg'], worst[k]['cm1']['pm_deg'], worst[k]['dm2']['pm_deg'],
                                                                  worst[k]['cm2']['pm_deg']) for k in worst) + ' (worst PM, deg)',
             'passed (PM >= 55 deg differential, >= 60 deg common mode at every corner)' if ok else 'failed')
    # ---------------- CM step (revision C)
    cs = load('cmstep', sfx)
    if cs:
        t = {}
        for j in cs:
            t[j['name']] = {r['event']: {k: v for k, v in r.items() if k not in ('tag', 'event')} for r in j['rows'] if r['tag'] == 'CMSROW'}
        c_ok = [n for n in t if 'revb' not in n]
        mx = max(max(v.get('o1cm_pp_last2us_mV', v.get('o1cm_pp_mV', 0)) for v in t[n].values()) for n in c_ok)
        st1 = max(max(v.get('o1cm_settle_ns_5mV', 0) for k, v in t[n].items() if k.startswith('pin')) for n in c_ok)
        b02 = max(max(v.get('o1cm_pp_last2us_mV', v.get('o1cm_pp_mV', 0)) for v in t[n].values()) for n in t if 'revb02' in n)
        S['cmstep'] = dict(table=t, revc_max_cm_pp_mV=mx, revc_pin_step_settle_ns_max=st1, revb02_max_cm_pp_mV=b02)
        if REVD(sfx):
            ov1 = max(max(v.get('o1cm_overshoots_5mV', 0) for v in t[n].values()) for n in c_ok)
            ov2 = max(max(v.get('ocm_overshoots_2mV', 0) for v in t[n].values()) for n in c_ok)
            s2 = {n: {k: v.get('o1cm_settle_ns_2pct') for k, v in t[n].items() if 'o1cm_settle_ns_2pct' in v} for n in c_ok}
            S['cmstep'].update(revd_o1cm_overshoots_max=ov1, revd_ocm_overshoots_max=ov2, revd_o1cm_settle_ns_2pct=s2)
        fill('r1afe-cmstep-' + sfx, 'CM step test with a full-scale 100 kHz sine: input CM 2.45->0.6->2.45 V, vcm2 +50 mV, VDDA -0.2 V; '
             'tt/ss/ff, x1 and x32; same test on revision B and on the dev-revb-02 variant (detection check)',
             ('revision D' if REVD(sfx) else 'revision C') + ': stage-1 CM peak-to-peak in the last 2 us before each next event <= %.2f mV; pin-CM step settling (5 mV) <= %.0f ns; '
             'dev-revb-02 variant: sustained %.0f mVpp stage-1 CM oscillation' % (mx, st1, b02),
             'passed (no sustained oscillation: <= 1 mV pp; the test detects the known oscillating variant)' if mx <= 1 and b02 > 100 else 'failed')
    # ---------------- overload (revision C)
    ov = load('overload', sfx)
    if ov:
        t = {}
        for j, r in rows(ov, 'OVLROW'):
            t[j['name']] = {k: v for k, v in r.items() if k != 'tag'}
        w = max(v['rec_ns_1lsb'] for n, v in t.items() if 'x32' in n)
        S['overload'] = dict(table=t, x32_recovery_1lsb_ns_worst=w)
        fill('r1afe-overload-' + sfx, 'Input overload: +-1.0 V differential (2 Vpp) for 10 us each polarity at x32 (and x1), recovery to 1 LSB '
             'and 1 % of the final output after the input returns to +FS/2; tt/ss/ff',
             'x32 recovery to 1 LSB worst %.0f ns; see table for 1 %% and x1' % w, 'recorded (no specification limit)')
    # ---------------- source impedance (revision C)
    rs = load('rsrc', sfx)
    if rs:
        t = {}
        for j, r in rows(rs, 'ACROW'):
            t.setdefault(j['corner'], {}).setdefault(G[int(r['code'])], {})['%g' % r['mc']] = dict(
                gain=10 ** (r['gs0'] / 20), f3_mhz=r['fs3'] / 1e6)
        out = {}
        for c in t:
            for g in t[c]:
                g0 = t[c][g]['0.001']['gain']
                out.setdefault(c, {})[g] = {rv: dict(gain_change_pct=round(100 * (v['gain'] / g0 - 1), 3), f3_mhz=round(v['f3_mhz'], 3))
                                            for rv, v in t[c][g].items()}
        wx32 = min(out[c]['x32']['1000']['gain_change_pct'] for c in out)
        wx1 = min(out[c]['x1']['1000']['gain_change_pct'] for c in out)
        S['rsrc'] = dict(table=out)
        fill('r1afe-rsrc-' + sfx, 'Source impedance 0/100/300/1000 ohm in series with each input pin: gain and f3 at every step, tt/ss/ff',
             'gain change at 1 kOhm: x1 %.2f %%, x32 %.2f %% (worst corner); equal in both channels for equal source impedance' % (wx1, wx32),
             'recorded (no specification limit; the host gain calibration absorbs it if the head impedance is constant)')
    # ---------------- temperature (revision C)
    tp = load('temp', sfx)
    if tp:
        t = {}
        for j, r in rows(tp, 'ACROW'):
            t.setdefault(str(j['subs']['TEMP']), {})[G[int(r['code'])]] = dict(gain=10 ** (r['gs0'] / 20), f3_mhz=r['fs3'] / 1e6,
                                                                            ph100k=r['ps100'])
        f3m = min(v['f3_mhz'] for T in t for v in t[T].values())
        gd = {g: 100 * (max(t[T][g]['gain'] for T in t) - min(t[T][g]['gain'] for T in t)) / t['27'][g]['gain'] for g in G}
        S['temp'] = dict(table=t, f3_min_mhz=f3m, gain_spread_pct=gd)
        fill('r1afe-temp-' + sfx, 'Temperature -40/27/125 C at tt (3.3 V): gain and f3 at every step',
             'f3 min %.3f MHz; gain spread over temperature max %.2f %% (%s)' % (f3m, max(gd.values()), max(gd, key=gd.get)),
             'passed (f3 >= 1 MHz)' if f3m >= 1.0 else 'failed')
    json.dump(S, open('results/summary-%s.json' % sfx, 'w'), indent=1)
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != 'table'} if isinstance(v, dict) else v for k, v in S.items()}, indent=1))

if __name__ == '__main__':
    main(sys.argv[1])
