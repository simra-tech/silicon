#!/usr/bin/env python3
"""Reduce the revision-A campaign results to the README numbers and fill question/result/disposition in each
runs/<run-id>/run.json. Usage (block sim/ dir, host python3): python3 report_afe.py <suffix>
Raw spectra for the noise band integrals are read from $G1_RESULTS_ROOT (must be set)."""
import json, math, os, sys

G = ['x1', 'x2', 'x4', 'x8', 'x16', 'x32']
LSB = 2.4 / 4096
ROOT = os.environ['G1_RESULTS_ROOT']

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
    S = {}
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
        fill('r1afe-noise-' + sfx, 'Noise at every step, 1 Hz-100 MHz; required x1 (output <= 240 uV rms = 0.41 LSB) and x32 (input <= 35 uV rms)',
             'x1 output worst %.0f uV rms (%.2f LSB); x32 input-referred worst %.1f uV rms' % (x1, x1 * 1e-6 / LSB, x32),
             'passed' if x1 <= 240 and x32 <= 35 else 'failed')
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
        fill('r1afe-tran-' + sfx, '100 kHz full-scale sine (2.0 Vpp differential out) at x1 and x32, tt/ss/ff: THD, swing, CM stability',
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
                  a, b, h = (e.get('%s_%s_%s_%s' % (pre, c, g, s)) for s in ('p100', 'm100', 'p50'))
                  if a and b and h:
                      k = (a['err_mV'] - b['err_mV']) / (a['vout0'] - b['vout0'])          # gain-error part (mV per V)
                      o = (a['err_mV'] + b['err_mV']) / 2 - k * (a['vout0'] + b['vout0']) / 2
                      res = h['err_mV'] - (k * h['vout0'] + o)
                      lin['%s_%s' % (c, g)] = dict(gain_err_pct=k / 10, offset_mV=o, nonlinear_residual_lsb=res * 1e-3 / LSB,
                                                   err_fs_lsb=a['err_lsb'])
          S[camp] = dict(table=e, linear_fit=lin)
          wr = max(abs(v['nonlinear_residual_lsb']) for v in lin.values()) if lin else None
          we = max(abs(v['err_fs_lsb']) for v in lin.values()) if lin else None
          fill('r1afe-%s-%s' % (camp, sfx), qtxt + ': sampled error at end of track, linearity of the error',
               'error at +FS worst %.2f LSB; after removing a linear gain/offset fit, residual worst %.3f LSB' % (we, wr),
               'passed (residual <= 0.5 LSB; the linear part is a gain error common to both channels)' if wr is not None and wr <= 0.5 else 'failed')
    json.dump(S, open('results/summary-%s.json' % sfx, 'w'), indent=1)
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != 'table'} if isinstance(v, dict) else v for k, v in S.items()}, indent=1))

if __name__ == '__main__':
    main(sys.argv[1])
