#!/usr/bin/env python3
"""Layout E9b (track T3n): peak classification of the CM step waveforms (2026-10-28 rule, blocks/README.md): a step-edge
feed-through spike shorter than the loop time constant is not an overshoot; only loop-response peaks count (limit: at
most one loop-response overshoot per event).
  python3 sim/cmstep_classify.py <results json with STBROW rows> <raw run dir> <job name> [<job name> ...] --png <dir>
For each event of tb_afe_cmstep.cir and each signal (stage-1 CM o1cm, 5 mV band, loop cm1; output CM ocm, 2 mV band,
loop cm2): the out-of-band segments of y - final in the event window (final = mean of the last 1 us). Loop time constant
tau = 1 / (2 pi f_unity) of the CM loop from the stb row of the same job's corner, nominal bias, gain code of the job, at
the input CM after the event (0.5 V after pin_cm_down, else 2.5 V; the worst = shortest tau of both points is used if
the point is missing). A segment is feed-through when it starts within the edge time + tau of the edge and lasts
< tau; every other segment is a loop-response peak. The main excursion is the out-of-band segment with the largest |peak| (the level
transition or the disturbance); segments before it are feed-through (short, at the edge), the pre-edge level (the
settled level moved by the event) or a loop precursor (reported, not counted); loop overshoots = loop-response peaks
after the main excursion, consecutive segments on the same side of the final value merged. Writes one JSON object on stdout and one PNG per job with the feed-through
segments marked (orange) and the loop-response peaks marked (red)."""
import json, math, os, sys
args = [a for a in sys.argv[1:]]
png = None
if '--png' in args:
    i = args.index('--png'); png = args[i + 1]; del args[i:i + 2]
resf, raw, jobs = args[0], args[1], args[2:]
EV = [('pin_cm_down', 10e-6, 20e-6, 20e-9, '0.5'), ('pin_cm_up', 20e-6, 30e-6, 20e-9, '2.5'),
      ('vcm2_up', 30e-6, 35e-6, 5e-9, '2.5'), ('vcm2_down', 35e-6, 40e-6, 5e-9, '2.5'),
      ('vdda_down', 40e-6, 45e-6, 10e-9, '2.5'), ('vdda_up', 45e-6, 50e-6, 10e-9, '2.5')]
IB = {'tt': '10.14', 'ss': '11.81', 'ff': '9.00'}
R = json.load(open(resf))
def fu(corner, code, loop, cm):
    best = {}
    for j in R:
        v, _, tag = j['name'].rpartition('__')
        for c in ('0.5', '2.5'):
            if tag == 'stb_%s_ib%s_cm%s' % (corner, IB[corner], c):
                for r in j.get('rows', []):
                    if r.get('tag') == 'STBROW' and r['code'] == code and r['loop'] == loop and r.get('f_unity'):
                        best[c] = r['f_unity']
    if cm in best:
        return best[cm], 'cm%s' % cm
    if best:
        k = max(best, key=best.get); return best[k], 'cm%s (fallback, shortest tau)' % k
    return None, 'missing'
def readcols(p):
    t, ys = [], []
    for l in open(p):
        a = l.split()
        try:
            v = [float(x) for x in a]
        except ValueError:
            continue
        if v:
            t.append(v[0]); ys.append(v[1::2])
    return t, list(zip(*ys))
out = {}
for name in jobs:
    v, _, tag = name.rpartition('__')
    corner = tag.split('_')[1]; code = 5 if tag.endswith('x32') else 0
    t, (o1, oc, o1c) = readcols(os.path.join(raw, name + '_cm.txt'))
    res = {}
    for sig, y, tol, loop in (('o1cm', o1, 5e-3, 'cm1'), ('ocm', oc, 2e-3, 'cm2')):
        for ev, a, b, tedge, cm in EV:
            f_u, src = fu(corner, code, loop, cm)
            tau = 1 / (2 * math.pi * f_u) if f_u else None
            w = [(ti, yi) for ti, yi in zip(t, y) if a <= ti < b]
            fin = [yi for ti, yi in w if ti >= b - 1e-6]; fin = sum(fin) / len(fin)
            segs, cur = [], None
            for ti, yi in w:
                e = yi - fin
                if abs(e) > tol:
                    s = e > 0
                    if cur and cur['sign'] == s:
                        cur['t1'] = ti
                        if abs(e) > abs(cur['peak']):
                            cur['peak'], cur['tpk'] = e, ti
                    else:
                        cur = dict(sign=s, t0=ti, t1=ti, peak=e, tpk=ti); segs.append(cur)
                else:
                    cur = None
            pre = [yi for ti, yi in zip(t, y) if a - 50e-9 <= ti < a]
            e0 = sum(pre) / len(pre) - fin   # pre-edge level against the final value
            im = max(range(len(segs)), key=lambda k: abs(segs[k]['peak'])) if segs else -1   # main excursion
            rows = []
            for i, s in enumerate(segs):
                dur = s['t1'] - s['t0']
                short = tau is not None and (s['t0'] - a) <= tedge + tau and dur < tau
                if i == im:
                    cls = 'main'
                elif i == 0 and s['t0'] - a <= 2e-9 and abs(e0) > tol and (s['peak'] > 0) == (e0 > 0) and i < im:
                    cls = 'pre-edge level'
                elif short:
                    cls = 'feed-through'
                else:
                    cls = 'loop' if i > im else 'loop precursor'
                rows.append(dict(start_ns=round(1e9 * (s['t0'] - a), 1), dur_ns=round(1e9 * dur, 1),
                                 peak_mV=round(1e3 * s['peak'], 2), t_peak_ns=round(1e9 * (s['tpk'] - a), 1), cls=cls))
            # loop overshoots: loop-response peaks after the main excursion (transition or disturbance), consecutive
            # segments on the same side of the final value merged (a band re-entry without a crossing is one peak)
            lp = []
            for r in rows:
                if r['cls'] in ('main', 'loop'):
                    if lp and (lp[-1]['peak_mV'] > 0) == (r['peak_mV'] > 0):
                        continue
                    lp.append(r)
            nov = max(0, len(lp) - 1)
            res['%s %s' % (sig, ev)] = dict(band_mV=tol * 1e3, tau_ns=round(1e9 * tau, 2) if tau else None, tau_from='%s %s' % (loop, src),
                                            segments=rows, loop_peaks=len(lp), loop_overshoots=nov, pre_edge_mV=round(1e3 * e0, 2),
                                            feedthrough=sum(1 for r in rows if r['cls'] == 'feed-through'))
    out[name] = dict(worst_loop_overshoots=max(r['loop_overshoots'] for r in res.values()), events=res)
    if png:
        import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
        fig, ax = plt.subplots(2, 6, figsize=(24, 7))
        for i, (sig, y, tol) in enumerate((('o1cm', o1, 5e-3), ('ocm', oc, 2e-3))):
            for k, (ev, a, b, tedge, cm) in enumerate(EV):
                r = res['%s %s' % (sig, ev)]
                span = 600e-9
                ww = [(ti, yi) for ti, yi in zip(t, y) if a - 50e-9 <= ti < a + span]
                fin = [yi for ti, yi in zip(t, y) if b - 1e-6 <= ti < b]; fin = sum(fin) / len(fin)
                A = ax[i][k]
                A.plot([1e9 * (ti - a) for ti, _ in ww], [1e3 * (yi - fin) for _, yi in ww], lw=1, color='#333')
                A.axhspan(-1e3 * tol, 1e3 * tol, color='#ddd', alpha=0.6)
                for s in r['segments']:
                    c = {'feed-through': '#e08000', 'loop': '#c00000', 'main': '#2060c0', 'pre-edge level': '#888888', 'loop precursor': '#8040a0'}[s['cls']]
                    A.plot([s['t_peak_ns']], [s['peak_mV']], {'feed-through': 'x', 'loop': 'o', 'main': 's', 'pre-edge level': 'd', 'loop precursor': 'v'}[s['cls']], color=c, ms=8, mew=2)
                if r['tau_ns']:
                    A.axvline(tedge * 1e9 + r['tau_ns'], color='#e08000', ls=':', lw=1)
                A.set_title('%s %s: loop ovs %d, f-t %d' % (sig, ev, r['loop_overshoots'], r['feedthrough']), fontsize=9)
                A.set_xlabel('ns after edge', fontsize=8); A.set_ylabel('mV from final', fontsize=8); A.tick_params(labelsize=7)
        fig.suptitle('%s (simulated): square = main excursion, o = loop-response overshoot, x = feed-through (< tau, at the edge), diamond = pre-edge level; dotted = edge + tau; grey = band' % name, fontsize=10)
        fig.tight_layout(); os.makedirs(png, exist_ok=True); fig.savefig(os.path.join(png, name + '.png'), dpi=70); plt.close(fig)
print(json.dumps(out, indent=1))
