#!/usr/bin/env python3
"""T2 post-layout harness: post-processing (2026-10-26). Reuses the revision-5 post-processors unchanged where they
read raw files only, and runs them on the run records of sim/post.

  post_post.py win  OUT.json <run id> [points json]  static windows, any number of 25-point windows (frame 0 not used);
                                                     method of sim/r5/post_t2.py win (design weights, 1.95 conversions
                                                     per LSB, DNL from code counts)
  post_post.py ref  OUT.json <buffer run> <ideal base run> [va,vb vla,vlb]   R2-4 metric (optional: read the buffer
                                                     run's reference at these vectors, e.g. the slice-port nodes): sim/r5/post_ref5.py executed with the segment
                                                     files of sim/post/results (the only change); VIDEAL from the base
                                                     run's run.json
  post_post.py isa  OUT.json <run id> [pre json]     sim/r5/post_t2.py isa + comparison with the pre-layout result
                                                     (default sim/results/r5/isa5_tt.json): code differences, IDD, IDDA
  post_post.py first OUT.json <run id> ...           sim/r5/post_t2.py first
  post_post.py pre  OUT.json                         collect the pre-layout values (revision 5 results + the sim/post pre
                                                     runs that exist) with their source files -> sim/post/pre_values.json
"""
import json, os, subprocess, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
BLOCK = os.path.dirname(os.path.dirname(HERE))
R5 = os.path.join(BLOCK, 'sim', 'r5')
sys.path.insert(0, os.path.join(BLOCK, 'sim', 'r4'))
sys.path.insert(0, os.path.join(BLOCK, 'sim', 'r3'))
cmd, out, A = sys.argv[1], sys.argv[2], sys.argv[3:]
root = os.environ['G1_RESULTS_ROOT']


def runjson(rid):
    return json.load(open(os.path.join(HERE, 'runs', rid, 'run.json')))


def need_completed(rid):
    d = runjson(rid)
    if d['status'] != 'completed':
        sys.exit('run %s is %s: not post-processed' % (rid, d['status']))
    return d


if cmd == 'win':
    from p4common import load_segments
    import cal3
    rid = A[0]
    need_completed(rid)
    pf = A[1] if len(A) > 1 else os.path.join(HERE, 'points', 'win3.json')
    P = json.load(open(pf))
    WL = np.array(json.load(open(os.path.join(BLOCK, 'sim', 'results', 'r3', 'cdac3_mc50_tt_cp100_globalfit.json')))['nominal_design_weights_lsb'])
    WD = cal3.quantise(WL)
    C = json.load(open(os.path.join(BLOCK, 'sim', 'results', 'r5', 'mc_window_check.json')))['slices']['a']
    LSB = (C['code_3071_3072_V'] - C['code_2047_2048_V']) / 1024.0
    STEP = 0.5 * 466.488e-6
    M = LSB / STEP
    slots, ba, bb = load_segments(os.path.join(HERE, 'results', rid + '_segments.json'), root)
    nw = (len(P['a']) - 1) // 25
    res = {'tool': 'sim/post/post_post.py win', 'run': rid, 'points': os.path.relpath(pf, BLOCK), 'core': runjson(rid)['core'],
           'label': 'simulated, %s, ideal VREF %s V, design weights; DNL from code counts at %.2f conversions per LSB '
                    '(resolution about 0.5 LSB)' % (runjson(rid)['core'], runjson(rid)['vref_ideal_V'], M)}
    for sl, bits in (('a', ba), ('b', bb)):
        keep = slots >= 1
        v = np.array(P[sl])[slots[keep]]
        bt = bits[keep]
        wi = (slots[keep] - 1) // 25
        rs = {}
        for w in range(nw):
            o = np.argsort(v[wi == w])
            c = cal3.code(bt[wi == w][o], WD)
            codes, cnt = np.unique(c, return_counts=True)
            widths = {int(k): float(n) / M for k, n in zip(codes[1:-1], cnt[1:-1])}
            rs[str(w)] = {'vin_range_V': [float(v[wi == w].min()), float(v[wi == w].max())], 'codes': [int(c.min()), int(c.max())],
                          'code_sequence': [int(x) for x in c], 'monotonic': bool(np.all(np.diff(c) >= 0)),
                          'missing_inside': int(np.sum(np.diff(c) > 1)),
                          'missing_codes': [int(x) + 1 for x, y in zip(c[:-1], c[1:]) if y - x > 1],
                          'dnl_by_code': {k: round(x - 1, 3) for k, x in widths.items()},
                          'max_abs_dnl': float(max(abs(x - 1) for x in widths.values())) if widths else None}
        res[sl] = {'windows': rs, 'points_per_lsb': round(M, 3), 'max_abs_dnl': max(x['max_abs_dnl'] for x in rs.values()),
                   'monotonic': all(x['monotonic'] for x in rs.values()), 'missing_inside': sum(x['missing_inside'] for x in rs.values())}
    json.dump(res, open(out, 'w'), indent=1)
    for sl in 'ab':
        print(sl, {k: res[sl][k] for k in ('max_abs_dnl', 'monotonic', 'missing_inside')},
              [(w, x['codes'], x['max_abs_dnl']) for w, x in res[sl]['windows'].items()])
elif cmd == 'ref':
    rb, ri = A[0], A[1]
    need_completed(rb)
    di = need_completed(ri)
    videal = di['vref_ideal_V']
    if videal is None:
        # base run with ideal sources at the slice pins (make_sp_netlist.py, --ref lay): VIDEAL = mean MSB reference of A[4]
        Mv = [float(x) for x in A[4].split(',')]
        videal = 0.5 * (Mv[0] + Mv[2])
    src = open(os.path.join(R5, 'post_ref5.py')).read()
    old = 'os.path.join(HERE, "..", "results", "r5", rid + "_segments.json")'
    assert src.count(old) == 1
    src = src.replace(old, 'os.path.join(SEGDIR, rid + "_segments.json")')
    if len(A) > 2:
        # port vectors (2026-10-26, RC netlists): A[2] = 'va,vb' (MSB reference at slice A / B), A[3] = 'vla,vlb' (LSB
        # reference); the buffer run is read at these nodes instead of v(vrefa) / v(vrefb) / v(vrefla) / v(vreflb)
        va, vb = A[2].split(','); vla, vlb = A[3].split(',')
        rep = {'"v(vref%s)" % sl': '{"a": "%s", "b": "%s"}[sl]' % (va, vb), '"v(vrefl%s)" % sl': '{"a": "%s", "b": "%s"}[sl]' % (vla, vlb)}
        for k, v in rep.items():
            n0 = src.count('db, ' + k) + src.count('db[' + k)
            src = src.replace('db, ' + k, 'db, ' + v).replace('db[' + k, 'db[' + v)
            assert n0 >= 2, (k, n0)
    if len(A) > 4:
        # static base correction (2026-10-26, H12): A[4] = 'Ma,La,Mb,Lb' = effective MSB / LSB reference of the base run at
        # each slice, in the ground frame of the buffer run (base-run slice-port value + slice-ground shift buffer - base,
        # from op-only runs). Replaces VIDEAL in dM / dL; the base trajectory itself is unchanged (modelled correction)
        Ma, La, Mb, Lb = [float(x) for x in A[4].split(',')]
        old = 'dM, dL = v1m * VIDEAL - VIDEAL, v1l * VIDEAL - VIDEAL'
        assert src.count(old) == 1
        src = src.replace(old, 'dM, dL = v1m * VIDEAL - {"a": %r, "b": %r}[sl], v1l * VIDEAL - {"a": %r, "b": %r}[sl]'
                          % (Ma, Mb, La, Lb))
    sys.argv = ['post_ref5.py', rb, ri, out, str(videal)]
    g = {'__file__': os.path.join(R5, 'post_ref5.py'), '__name__': '__main__', 'SEGDIR': os.path.join(HERE, 'results')}
    exec(compile(src, 'post_ref5.py (segments: sim/post/results)', 'exec'), g)
    d = json.load(open(out))
    d['label'] = d['label'].replace('r1_adc5_core_fast', runjson(rb)['core']) + '; run by sim/post/post_post.py ref'
    if len(A) > 4:
        d['static_base_correction_V'] = {'a': {'msb': Ma, 'lsb': La}, 'b': {'msb': Mb, 'lsb': Lb}}
        d['label'] += '; static base correction (modelled, H12)'
    json.dump(d, open(out, 'w'), indent=1)
elif cmd in ('isa', 'first'):
    rid = A[0]
    for r in A if cmd == 'first' else [rid]:
        need_completed(r)
    rc = subprocess.call([sys.executable, os.path.join(R5, 'post_t2.py'), cmd, out] + (A if cmd == 'first' else [rid]))
    if rc:
        sys.exit(rc)
    d = json.load(open(out))
    d['label'] = d['label'].replace('r1_adc5_core_fast', runjson(rid)['core']).replace('r1_adc5_core full core', runjson(rid)['core'])
    if cmd == 'isa':
        pre = json.load(open(A[1] if len(A) > 1 else os.path.join(BLOCK, 'sim', 'results', 'r5', 'isa5_tt.json')))
        cmpr = []
        for fp, fq in zip(pre['frames'], d['frames']):
            cmpr.append({'frame': fp['frame'], 'input': fp['input'],
                         'code_pre': [fp['a']['code'], fp['b']['code']], 'code_post': [fq['a']['code'], fq['b']['code']],
                         'diff_lsb': [fq['a']['code'] - fp['a']['code'], fq['b']['code'] - fp['b']['code']]})
        d['compare_pre'] = {'pre_run': pre['run'], 'frames': cmpr,
                            'max_abs_code_diff_lsb': max(abs(x) for c in cmpr for x in c['diff_lsb']),
                            'idd_mA_pre_post': [pre['idd_mA'], d['idd_mA']], 'idda_mA_pre_post': [pre.get('idda_mA'), d.get('idda_mA')],
                            'gain_pre_post': [pre['gain_fit']['gain'], d['gain_fit']['gain']]}
        print(json.dumps(d['compare_pre'], indent=1))
    json.dump(d, open(out, 'w'), indent=1)
elif cmd == 'pre':
    r5 = lambda f: json.load(open(os.path.join(BLOCK, 'sim', 'results', 'r5', f)))
    pr = lambda f: json.load(open(os.path.join(HERE, 'results', f))) if os.path.exists(os.path.join(HERE, 'results', f)) else None
    def refrow(f, core, note=''):
        d = r5(f) if f.startswith('ref5') else pr(f)
        if d is None:
            return {'source': 'sim/post/results/' + f, 'status': 'not run'}
        return {'source': ('sim/results/r5/' if f.startswith('ref5') else 'sim/post/results/') + f, 'core': core,
                'runs': [d['run_buffer'], d['run_ideal']], 'videal_V': d['videal_V'],
                'worst_case_lsb': round(d['max_abs_input_error_mid_eval_lsb'], 3),
                'after_gain_fit_lsb': round(d['max_abs_error_after_gain_fit_lsb'], 3), 'idda_mA': round(d.get('idda_mA', float('nan')), 3),
                'pass_0p25': d['pass_0p25_r24'], 'note': note}
    fc = r5('firstconv5.json')['runs']
    isa = r5('isa5_tt.json')
    win = pr('win3_tt_rec.json')
    fcp = pr('firstconv_rec.json')
    out_d = {
        'label': 'pre-layout values (simulated, schematic level, ngspice 46, PDK 84374023) for the pre / post-layout table; '
                 'collected by sim/post/post_post.py pre',
        'a_static_window_tt': ({'source': 'sim/post/results/win3_tt_rec.json', 'run': win['run'], 'core': win['core'],
                                'vref_V': 1.045, 'max_abs_dnl_lsb': [win['a']['max_abs_dnl'], win['b']['max_abs_dnl']],
                                'monotonic': [win['a']['monotonic'], win['b']['monotonic']],
                                'missing_inside': [win['a']['missing_inside'], win['b']['missing_inside']]} if win else
                               {'source': 'sim/post/results/win3_tt_rec.json', 'status': 'not run (yet)'}),
        'a_static_window_ss125_ffm40_reference': {'source': ['sim/results/r5/win5_ss125.json', 'sim/results/r5/win5_ffm40.json'],
                                                  'core': 'r1_adc5_core_fast', 'max_abs_dnl_lsb': [r5('win5_ss125.json')['a']['max_abs_dnl'], r5('win5_ffm40.json')['a']['max_abs_dnl']],
                                                  'note': '2 windows (2048, 3072), not 1024'},
        'b_r24_tt': refrow('ref5_tt_opt3c_ib5.json', 'r1_adc5_core_fast', 'README value 0.209 LSB; base run at 1.0505 V'),
        'b_r24_tt_full_core': refrow('ref_tt_rec.json', 'r1_adc5_core', 'like-for-like with the layout (full core: transistor drivers r1_drv)'),
        'b_r24_ss125': refrow('ref5_ss125_opt3c.json', 'r1_adc5_core_fast', 'README value 0.163 LSB; base run at 1.0505 V'),
        'b_r24_ss125_full_core': refrow('ref_ss125_rec.json', 'r1_adc5_core', 'like-for-like with the layout'),
        'c_mux_tt': {'source': 'sim/results/r5/isa5_tt.json', 'run': isa['run'], 'core': 'r1_adc5_core',
                     'codes': [[f['a']['code'], f['b']['code']] for f in isa['frames']], 'max_abs_error_lsb': isa['max_abs_error_lsb'],
                     'gain': isa['gain_fit']['gain'], 'residual_after_gain_fit_lsb': isa['gain_fit']['max_abs_residual_lsb'],
                     'min_track_ns': isa['min_track_ns']},
        'd_first_conversion': {'source': 'sim/results/r5/firstconv5.json', 'core': 'r1_adc5_core_fast',
                               'tt_pre33': fc['t2-ff-tt-pre33'], 'ss125_pre33': fc['t2-ff-ss-pre33'],
                               'full_core': ({'source': 'sim/post/results/firstconv_rec.json', 'runs': fcp['runs']} if fcp else 'not run (yet)')},
        'e_supply_tt': {'source': 'sim/results/r5/isa5_tt.json', 'run': isa['run'], 'idd_mA': round(isa['idd_mA'], 4),
                        'idda_mA': round(isa['idda_mA'], 4), 'note': 'time average 0.6 us .. 3.31 us; SAR behavioural (no current)'},
    }
    json.dump(out_d, open(out, 'w'), indent=1)
    print(json.dumps(out_d, indent=1)[:2500])
else:
    sys.exit('unknown command')
