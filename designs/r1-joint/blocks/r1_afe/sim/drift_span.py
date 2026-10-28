#!/usr/bin/env python3
"""Layout E9 (track T3m): D22 drift spans of the x32 output offset (mV) from the op_* rows of a result file.
  python3 sim/drift_span.py results/<run>.json [variant]
Per bias (nominal = corner-matched tt 10.14 / ss 11.81 / ff 9.00 uA; 6.9 uA; 15.4 uA) and input CM: span over the corners
(tt 3.3 V, ss, ff), over the supply (tt 3.0 / 3.3 / 3.6 V) and over all five points; worst |offset| over every op_* row
(the ffx rows included). Limits (D22): span <= 1 mV, |offset| <= 5 mV."""
import json, sys
f = sys.argv[1]; var = sys.argv[2] if len(sys.argv) > 2 else None
O = {}
for j in json.load(open(f)):
    v, _, tag = j['name'].rpartition('__')
    if var and v != var:
        continue
    r = {int(x['code']): x for x in j.get('rows', []) if x.get('tag') == 'OPROW'}
    if j['name'].rpartition('__')[2].startswith('op_') and 5 in r and 'odiff' in r[5] and j.get('rc') == 0:
        O[tag] = r[5]['odiff'] * 1e3
B = {'nominal': ('10.14', '11.81', '9.00'), '6.9': ('6.9', '6.9', '6.9'), '15.4': ('15.4', '15.4', '15.4')}
out = {'spans': {}, 'worst_abs': max(abs(x) for x in O.values()) if O else None, 'n_op': len(O),
       'min': min(O.values()) if O else None, 'max': max(O.values()) if O else None}
for b, (it, iss, iff) in B.items():
    for cm in ('0.5', '1.5', '2.0', '2.5', '2.8'):
        k = lambda c, i, s='': 'op_%s_ib%s_cm%s%s' % (c, i, cm, s)
        pts = dict(tt=O.get(k('tt', it)), v30=O.get(k('tt', it, '_v3.0')), v36=O.get(k('tt', it, '_v3.6')),
                   ss=O.get(k('ss', iss)), ff=O.get(k('ff', iff)))
        if any(x is None for x in pts.values()):
            continue
        sp = lambda ks: round(max(pts[x] for x in ks) - min(pts[x] for x in ks), 3)
        out['spans']['%s cm%s' % (b, cm)] = dict(corners=sp(('tt', 'ss', 'ff')), supply=sp(('tt', 'v30', 'v36')),
                                                  all=sp(tuple(pts)), pts={x: round(y, 3) for x, y in pts.items()})
allsp = [s for d in out['spans'].values() for s in (d['corners'], d['supply'], d['all'])]
out['worst_span'] = max(allsp) if allsp else None
out['n_spans_over_1mV'] = sum(1 for s in allsp if s > 1.0)
out['n_spans_over_1p6mV'] = sum(1 for s in allsp if s > 1.6)   # D29 allocation 1.6 mV
out['n_spans'] = len(allsp)
print(json.dumps(out, indent=1))
