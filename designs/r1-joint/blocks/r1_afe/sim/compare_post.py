#!/usr/bin/env python3
"""Pre-layout vs post-layout table of the 'post' campaign (layout track, revision E).

  python3 compare_post.py <label>=<run-id> [<label>=<run-id> ...] > ../reports/<name>.json

Reads results/<run-id>.json of each run and reduces: f_c (min over steps, tt, input CM 0.5/2.5 V), pole matching
(20 MC at tt, worst |f3 sine/cosine - 1| over steps), stage-1 loop margins (DM1, CM1 worst PM over x1/x32 and CM
0.5/2.5 V at tt and ffx; stage-2 for information), settling into the r1_adc T/H model (5 levels, tt and ss, x1 and
x32: total error and non-linear residual after a linear fit), noise (x32 input-referred and x1 output, ss and tt).
"""
import json, math, sys
LSB = 1.8 / 4096
G = ['x1', 'x2', 'x4', 'x8', 'x16', 'x32']

def rows(res, tag):
    for j in res:
        for r in j['rows']:
            if r['tag'] == tag:
                yield j, r

def reduce(res):
    out = {}
    for k in ('tt', 'ss', 'ff'):
        f3 = [min(r['fs3'], r['fc3']) / 1e6 for j, r in rows(res, 'ACROW') if j['corner'] == k and not j['mismatch'] and not isinstance(r['fs3'], str)]
        if f3:
            out['fc_min_%s_MHz' % k] = round(min(f3), 4)
        df3 = [100 * (r['fs3'] / r['fc3'] - 1) for j, r in rows(res, 'ACROW') if j['corner'] == k and j['mismatch'] and not isinstance(r['fs3'], str)]
        if len(df3) > 1:
            sd = math.sqrt(sum((x - sum(df3) / len(df3)) ** 2 for x in df3) / (len(df3) - 1))
            out['pole_match_%s_worst_pct' % k] = round(max(abs(x) for x in df3), 4)
            out['pole_match_%s_n' % k] = len(df3)
            out['pole_match_%s_sd_pct' % k] = round(sd, 4)
        # output common mode, all gain codes (OPROW of the ac deck, nominal runs; layout revision E2)
        oc = [v for j, r in rows(res, 'OPROW') if j['corner'] == k and not j['mismatch'] for v in (r.get('ocms'), r.get('ocmc'))
              if isinstance(v, (int, float))]
        if oc:
            out['out_cm_%s_V' % k] = [round(min(oc), 4), round(max(oc), 4)]
    th = [r['thd_percent'] for j, r in rows(res, 'THDROW') if isinstance(r.get('thd_percent'), (int, float))]
    if th:
        out['thd_worst_pct'] = round(max(th), 4)
    for k in ('tt', 'ffx'):
        for lp in ('dm1', 'cm1', 'dm2', 'cm2'):
            v = [(r['pm_deg'], r['gm_db']) for j, r in rows(res, 'STBROW') if j['corner'] == k and r['loop'] == lp and r['pm_valid'] and r['pm_deg'] is not None]
            out['pm_%s_%s_deg' % (lp, k)] = min(x[0] for x in v) if v else None
            g = [x[1] for x in v if x[1] is not None]
            out['gm_%s_%s_dB' % (lp, k)] = min(g) if g else None
    e = {}
    for j in res:
        r = [x for x in j['rows'] if x['tag'] == 'STROW']
        if j['name'].startswith('settleadc_') and r and not isinstance(r[-1]['err_s'], str):
            e[j['name']] = (r[-1]['vout0'], r[-1]['err_s'] * 1e3, r[-1]['lsb_s'])
    tot, resid, offs = {}, {}, {}
    for c in ('tt', 'ss'):
        for g in ('x1', 'x32'):
            pts = [v for n, v in e.items() if n.startswith('settleadc_%s_%s_' % (c, g))]
            if len(pts) < 3:
                continue
            n = len(pts); sx = sum(p[0] for p in pts); sy = sum(p[1] for p in pts)
            sxx = sum(p[0] ** 2 for p in pts); sxy = sum(p[0] * p[1] for p in pts)
            kk = (n * sxy - sx * sy) / (n * sxx - sx ** 2); o = (sy - kk * sx) / n
            resid['%s_%s' % (c, g)] = round(max(abs(p[1] - (kk * p[0] + o)) for p in pts) * 1e-3 / LSB, 4)
            tot['%s_%s' % (c, g)] = round(max(abs(p[2]) for p in pts), 3)
            offs['%s_%s' % (c, g)] = round(o, 4)     # mV: offset term of the linear fit (E2: P/N balance check)
    out['settle_total_err_lsb'] = tot
    out['settle_residual_lsb'] = resid
    out['settle_offset_mV'] = offs
    out['settle_total_err_worst_lsb'] = max(tot.values()) if tot else None
    out['settle_residual_worst_lsb'] = max(resid.values()) if resid else None
    for j, r in rows(res, 'NZROW'):
        k = G[int(r['code'])]
        if k == 'x32':
            out['noise_x32_in_%s_uV' % j['corner']] = round(r['in_rms'] * 1e6, 2)
        if k == 'x1':
            out['noise_x1_out_%s_uV' % j['corner']] = round(r['onoise_rms'] * 1e6, 1)
    out['failed_jobs'] = [j['name'] for j in res if j['rc'] != 0 or not j['rows']]
    return out

if __name__ == '__main__':
    T = {}
    for a in sys.argv[1:]:
        lab, rid = a.split('=')
        T[lab] = dict(run_id=rid, **reduce(json.load(open('results/%s.json' % rid))))
    print(json.dumps(T, indent=1))
