#!/usr/bin/env python3
"""Layout B4 trace of the late-decision R2-4 error (diagnostic). Runs the R2-4 metric exactly as
`sim/post/post_post.py ref` does (sim/r5/post_ref5.py with the same text patches: segment files, slice-port vectors,
static base correction), with one more patch: the sample time inside tick k (25 ns in the metric) is set to each value
of TIN. Purpose: separate a reference error that exists before the comparator decides (comparator integrating) from
the decision-dependent kickback of a decision that resolves differently in the buffer run and in the base run (it can
only appear after the comparator decides, and only at the first decision where the bits differ, which the metric
still includes: `j <= jmax`).
usage: trace_dec.py OUT.json <buffer run> <ideal base run> va,vb vla,vlb Ma,La,Mb,Lb
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
POST = os.path.dirname(HERE)
BLOCK = os.path.dirname(os.path.dirname(POST))
R5 = os.path.join(BLOCK, 'sim', 'r5')
out, rb, ri, pv, plv, sb = sys.argv[1:7]
TIN = [4, 7, 10, 13, 16, 19, 22, 25, 28, 31]
Ma, La, Mb, Lb = [float(x) for x in sb.split(',')]
videal = 0.5 * (Ma + Mb)
base = open(os.path.join(R5, 'post_ref5.py')).read()
old = 'os.path.join(HERE, "..", "results", "r5", rid + "_segments.json")'
base = base.replace(old, 'os.path.join(SEGDIR, rid + "_segments.json")')
va, vb = pv.split(','); vla, vlb = plv.split(',')
for k, v in {'"v(vref%s)" % sl': '{"a": "%s", "b": "%s"}[sl]' % (va, vb),
             '"v(vrefl%s)" % sl': '{"a": "%s", "b": "%s"}[sl]' % (vla, vlb)}.items():
    base = base.replace('db, ' + k, 'db, ' + v).replace('db[' + k, 'db[' + v)
o2 = 'dM, dL = v1m * VIDEAL - VIDEAL, v1l * VIDEAL - VIDEAL'
assert base.count(o2) == 1
base = base.replace(o2, 'dM, dL = v1m * VIDEAL - {"a": %r, "b": %r}[sl], v1l * VIDEAL - {"a": %r, "b": %r}[sl]' % (Ma, Mb, La, Lb))
o3 = 'tm = t0 + np.arange(ND) * T + 25e-9'
assert base.count(o3) == 1
per = {}
for tin in TIN:
    src = base.replace(o3, 'tm = t0 + np.arange(ND) * T + %de-9' % tin)
    tmp = out + '.tmp.json'
    sys.argv = ['post_ref5.py', rb, ri, tmp, str(videal)]
    g = {'__file__': os.path.join(R5, 'post_ref5.py'), '__name__': '__main__', 'SEGDIR': os.path.join(POST, 'results')}
    import io, contextlib
    with contextlib.redirect_stdout(io.StringIO()):
        exec(compile(src, 'post_ref5.py (trace)', 'exec'), g)
    per[tin] = json.load(open(tmp))
    os.remove(tmp)
res = dict(label='diagnostic (simulated runs %s / %s): R2-4 metric of post_post.py ref sampled at several times in each '
                 'tick (ns after the clk30 edge of decision k)' % (rb, ri), t_in_tick_ns=TIN, slices={})
for sl in 'ab':
    rows = []
    for r in per[25]['slices'][sl]['slots'][1:]:
        s = r['slot']
        dif = r['bits_differ_at']
        trace = {str(5 + i): [per[t]['slices'][sl]['slots'][s]['input_error_mid_eval_lsb_dec5_13'][i] for t in TIN]
                 for i in range(9) if r['input_error_mid_eval_lsb_dec5_13'][i] is not None}
        rows.append(dict(slot=s, vin_V=round(r['vin_est_ideal_V'], 4), first_differing_decision=dif[0] if dif else None, err_lsb=trace))
    def mx(sel, t):
        v = [abs(x['err_lsb'][k][TIN.index(t)]) for x in rows for k in x['err_lsb'] if sel(x, int(k))]
        return round(max(v), 3) if v else None
    same = lambda x, k: k != x['first_differing_decision']
    diff = lambda x, k: k == x['first_differing_decision']
    res['slices'][sl] = dict(rows=rows,
                             max_abs_metric_25ns=per[25]['slices'][sl]['max_abs_input_error_mid_eval_lsb'],
                             max_abs_25ns_decisions_equal=mx(same, 25), max_abs_25ns_at_first_differing_decision=mx(diff, 25),
                             max_abs_10ns_at_first_differing_decision=mx(diff, 10), max_abs_10ns_all=mx(lambda x, k: True, 10),
                             max_abs_25ns_excluding_differing_decision=mx(same, 25),
                             max_abs_16ns_at_first_differing_decision=mx(diff, 16))
    # corrected R2-4 value (recorded option, the limit is unchanged): 25 ns where the decisions agree, 16 ns (before the
    # comparator regenerates) at the first differing decision; decisions 5..13, slots 1..
    cv = [x for x in (res['slices'][sl]['max_abs_25ns_decisions_equal'], res['slices'][sl]['max_abs_16ns_at_first_differing_decision']) if x is not None]
    res['slices'][sl]['corrected_r24_lsb'] = max(cv)
res['corrected_r24_lsb'] = max(res['slices'][x]['corrected_r24_lsb'] for x in 'ab')
res['metric_as_defined_lsb'] = max(res['slices'][x]['max_abs_metric_25ns'] for x in 'ab')
json.dump(res, open(out, 'w'), indent=1)
for sl in 'ab':
    x = res['slices'][sl]
    print(sl, {k: v for k, v in x.items() if k != 'rows'})
    for r in x['rows']:
        k = r['first_differing_decision']
        if k is not None and str(k) in r['err_lsb']:
            print('  slot %d vin %+.3f dec %d:' % (r['slot'], r['vin_V'], k), r['err_lsb'][str(k)], ' dec k-1:', r['err_lsb'].get(str(k - 1)))
