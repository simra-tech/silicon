#!/usr/bin/env python3
"""Block qualification 2026-09-27: summarise step 1 logs, the window MC and the kick MC.
  python3 analyze.py <blockqual bulk dir>      -> text summary on stdout
Step 1 DAC metrics use the same endpoint-fit formulas as sim/postlayout/run_postlayout.sh dac()."""
import glob, json, os, re, statistics as S, sys
B = sys.argv[1]
print('# step 1: comparator delay (tb_trip_cmp_pex.cir), settle (tb_trip_settle.cir), DAC (tb_trip_dac_pex.cir)')
for f in sorted(glob.glob(B + '/step1/*.cir.log')):
    tag = os.path.basename(f)[:-8]; log = open(f, errors='replace').read()
    print('==', tag)
    for l in log.splitlines():
        if re.match(r'(VTH|DELAY|SETTLE|DACH)', l): print(l.strip())
    v = {int(m.group(1)): (float(m.group(2)), float(m.group(3)), float(m.group(4))) for m in re.finditer(
        r"DACS code= +(\d+) +out= +(-?[0-9.e+-]+) +err_LSB= +(-?[0-9.e+-]+) +iref_uA= +(-?[0-9.e+-]+)", log)}
    if v:
        if len(v) == 256:
            t = [v[k][0] for k in range(256)]; lsb = (t[255] - t[0]) / 255
            inl = [(t[k] - t[0]) / lsb - k for k in range(256)]; dnl = [(t[k + 1] - t[k]) / lsb - 1 for k in range(255)]
            print("DACS 256 codes: code0=%.5f V code128=%.5f V code255=%.5f V LSB=%.4f mV I(VREF)=%.2f uA" % (t[0], t[128], t[255], lsb * 1e3, v[128][2]))
            print("DACS endpoint fit: INL max |%.3f| LSB (code %d), DNL max |%.3f| LSB (code %d); absolute error vs 1.04*(255+code)/530: min %.3f max %.3f LSB"
                  % (max(inl, key=abs), max(range(256), key=lambda k: abs(inl[k])), max(dnl, key=abs), max(range(255), key=lambda k: abs(dnl[k])) + 1,
                     min(x[1] for x in v.values()), max(x[1] for x in v.values())))
        else: print('DACS: %d of 256 codes found' % len(v))
    if not re.search(r'^(DELAY|SETTLE|DACS)', log, re.M): print('NO RESULT LINES (see .err)')
print('\n# window (win_pex.py), ns; w_fall = soft reset - hard evaluate, w_rise = hard reset - soft evaluate')
groups = {}
for f in sorted(glob.glob(B + '/win/*/*.cir.log')):
    grp = os.path.basename(os.path.dirname(f)); m = re.search(r'^WIN (\S+) (.*)$', open(f, errors='replace').read(), re.M)
    if not m: print(grp, 'NO WIN LINE'); continue
    d = {k: float(x) for k, x in re.findall(r'(\w+)=(\S+)', m.group(2))}
    if grp.startswith('ctl'):
        print('%-10s %s' % (grp, ' '.join('%s=%.4g' % (k, d[k] * (1e9 if k[0] in 'wehs' and 'min' not in k and 'max' not in k else 1)) for k in d)))
    else: groups.setdefault(grp.split('_')[0], []).append((grp, d))
for g, rows in sorted(groups.items()):
    print('== %s: %d seeds' % (g, len(rows)))
    for k in ('w_fall', 'w_rise', 'ev_soft', 'ev_hard', 'h_tr', 'h_tf', 's_tr', 's_tf'):
        x = [r[1][k] * 1e9 for r in rows]
        print('  %-8s min %7.3f  max %7.3f  mean %7.3f  sigma %6.3f  (min seed %s)' % (k, min(x), max(x), S.mean(x), S.stdev(x) if len(x) > 1 else 0,
              min(rows, key=lambda r: r[1][k])[0]))
    for k in ('s_min', 'h_min'): print('  %-8s min %.4f V' % (k, min(r[1][k] for r in rows)))
    for k in ('s_max', 'h_max'): print('  %-8s max %.4f V' % (k, max(r[1][k] for r in rows)))
    print('  per seed w_fall/w_rise ns: ' + ' '.join('%s:%.2f/%.2f' % (r[0].split('_s')[1], r[1]['w_fall'] * 1e9, r[1]['w_rise'] * 1e9) for r in rows))
print('\n# kick screen points (kick_rt.py points), tt 1.2 V 27 C, mos_tt_mismatch, hard 200 / soft 153, 212 ns; ud = LSB of icmp below the DC threshold')
pts = {}
for f in glob.glob(B + '/kickpts/results.jsonl'):
    for l in open(f):
        r = json.loads(l); c = r['cond']
        pts.setdefault(c[0], {})['%s%+d' % (c[5], r['ud'])] = 'ERR' if r.get('error') else ('T' if r['trip'] else 'n') + ('*' if r['mixed'] else '')
keys = ['hard+10', 'hard-10', 'soft+10', 'soft-10']; exp = {'hard+10': 'n', 'hard-10': 'T', 'soft+10': 'n', 'soft-10': 'T'}
full = [s for s in pts if all(k in pts[s] for k in keys)]
print('seeds with all 4 points: %d; points run: %d' % (len(full), sum(len(v) for v in pts.values())))
for k in keys:
    v = [pts[s][k] for s in pts if k in pts[s]]
    print('  %-8s expected %s: %d runs, %d as expected, %d mixed' % (k, exp[k], len(v), sum(x.rstrip('*') == exp[k] for x in v), sum('*' in x for x in v)))
for s in sorted(pts): print('  %s %s' % (s, ' '.join('%s:%s' % (k, pts[s].get(k, '-')) for k in keys)))
