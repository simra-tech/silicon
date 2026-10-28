#!/usr/bin/env python3
"""Layout E9c at VDDA 2.90 V (track T3p): reduce the op and post runs of the 2.90 V subset against the 3.0 V record.
  python3 vdda290_reduce.py [--json results/r1afe-e9c-vdda290-summary.json]
Reads results/r1afe-op-e9c.json, r1afe-op-e9c-v290.json, r1afe-post-e9b.json (E9b rows, equal to E9c within 0.01 deg / 0.01 dB),
r1afe-post-e9c.json, r1afe-post-e9c-v290.json. Offsets: x32 output offset (code 5 'odiff') in mV, as drift_span.py."""
import json, sys, collections
def load(r):
    return json.load(open('results/%s.json' % r))
def op(rid):
    O = {}
    for j in load(rid):
        tag = j['name'].rpartition('__')[2]
        r = {int(x['code']): x for x in j.get('rows', []) if x.get('tag') == 'OPROW'}
        if tag.startswith('op_') and 5 in r and j.get('rc') == 0:
            O[tag] = r[5]['odiff'] * 1e3
    return O
rec, new = op('r1afe-op-e9c'), op('r1afe-op-e9c-v290')
out = collections.OrderedDict()
pairs = []
for t, v in new.items():
    base = t.replace('_v2.90', '')
    ref = base + '_v3.0' if base.startswith('op_tt_') else base
    pairs.append((t, ref, rec.get(ref), v))
out['offset'] = [dict(point=t, ref=r, v30=a, v290=b, diff=(round(b - a, 3) if a is not None else None)) for t, r, a, b in pairs]
out['n_op_new'] = len(new)
out['worst_abs_v290'] = max(abs(x) for x in new.values()) if new else None
out['worst_abs_v30_same_points'] = max(abs(p[2]) for p in pairs if p[2] is not None) if pairs else None
B = {'nominal': ('10.14', '11.81', '9.00'), '6.9': ('6.9', '6.9', '6.9'), '15.4': ('15.4', '15.4', '15.4')}
def spans(replace_ss):
    S = {}
    for b, (it, iss, iff) in B.items():
        for cm in ('0.5', '1.5', '2.0', '2.5', '2.8'):
            k = lambda c, i, s='': 'op_%s_ib%s_cm%s%s' % (c, i, cm, s)
            v290 = new.get(k('tt', it, '_v2.90'))
            ss290 = new.get(k('ss', iss, '_v2.90'))
            pts = dict(tt=rec.get(k('tt', it)), v30=v290, v36=rec.get(k('tt', it, '_v3.6')),
                       ss=ss290 if replace_ss else rec.get(k('ss', iss)), ff=rec.get(k('ff', iff)))
            if any(x is None for x in pts.values()):
                continue
            sp = lambda ks: round(max(pts[x] for x in ks) - min(pts[x] for x in ks), 3)
            S['%s cm%s' % (b, cm)] = dict(corners=sp(('tt', 'ss', 'ff')), supply=sp(('tt', 'v30', 'v36')), all=sp(tuple(pts)),
                                         pts={x: round(y, 3) for x, y in pts.items()})
    a = [s for d in S.values() for s in (d['corners'], d['supply'], d['all'])]
    return dict(spans=S, worst=max(a) if a else None, n=len(a), n_over_1p0=sum(s > 1.0 for s in a), n_over_1p6=sum(s > 1.6 for s in a))
out['drift_tt_only_replaced'] = spans(False)      # the 3.0 V tt point replaced by 2.90 V (task definition)
out['drift_tt_and_ss_replaced'] = spans(True)     # also the ss point (ss supply is 3.0 V in the record)
def stb(rid):
    R = {}
    for j in load(rid):
        tag = j['name'].rpartition('__')[2]
        st = [r for r in j.get('rows', []) if r['tag'] == 'STBROW']
        if st and j['rc'] == 0:
            e = {}
            for lp in ('dm1', 'cm1', 'dm2', 'cm2'):
                rr = [r for r in st if r['loop'] == lp]
                ok = [r['pm_deg'] for r in rr if r['pm_valid'] and r['pm_deg'] is not None]
                gm = [r['gm_db'] for r in rr if r['gm_db'] is not None]
                e[lp] = dict(pm_min=min(ok) if ok else None, gm_min=min(gm) if gm else None,
                             n_invalid=sum(not r['pm_valid'] for r in rr))
            R[tag] = e
    return R
def fc(rid):
    R = {}
    for j in load(rid):
        tag = j['name'].rpartition('__')[2]
        ac = [r for r in j.get('rows', []) if r['tag'] == 'ACROW' and not isinstance(r['fs3'], str)]
        if ac and j['rc'] == 0 and not j.get('mismatch'):
            oc = [r['ocms'] for r in j['rows'] if r['tag'] == 'OPROW'] + [r['ocmc'] for r in j['rows'] if r['tag'] == 'OPROW']
            R[tag] = dict(fc_MHz=round(min(min(r['fs3'], r['fc3']) for r in ac) / 1e6, 5), ocm=(min(oc), max(oc)) if oc else None)
    return R
def thd(rid):
    R = {}
    for j in load(rid):
        tag = j['name'].rpartition('__')[2]
        t = [r['thd_percent'] for r in j.get('rows', []) if r['tag'] == 'THDROW']
        if t:
            R[tag] = max(t)
    return R
out['stb_v30_e9b'], out['stb_v30_e9c'], out['stb_v290'] = stb('r1afe-post-e9b'), stb('r1afe-post-e9c'), stb('r1afe-post-e9c-v290')
out['ac_v30_e9b'], out['ac_v30_e9c'], out['ac_v290'] = fc('r1afe-post-e9b'), fc('r1afe-post-e9c'), fc('r1afe-post-e9c-v290')
out['thd_v33_e9b'], out['thd_v290'] = thd('r1afe-post-e9b'), thd('r1afe-post-e9c-v290')
if '--json' in sys.argv:
    json.dump(out, open(sys.argv[sys.argv.index('--json') + 1], 'w'), indent=1)
print(json.dumps({k: v for k, v in out.items() if k not in ('offset',)}, indent=1, default=str)[:12000])
