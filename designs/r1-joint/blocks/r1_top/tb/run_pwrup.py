#!/usr/bin/env python3
"""Test 1a (track T10): power-up of the closed DC blocks and the oscillator, real netlists of record.

Subset deck: r1_bgr + r1_bias (with r1_por) + r1_osc (enable high, trim code 22) on ramped rails, the r1_bias
consumer loads of record (blocks/r1_bias/sim/r1_bias_loads.spice), the bgr vref load of the r1_bias decks (11 pF).
The POR release (about 240 us) is not simulated: its delay is the r1_bias record (bias-por-20261021-*, 197-247 us).
The ctrl reset exit and the ID read are deck 1b (run_tb.py --test 1 --fast --start op).

Run inside the container (from the repository root):
    G1_CPUSET=...; export G1_CPUSET; G1_RESULTS_ROOT=<G1_RESULTS_ROOT>; export G1_RESULTS_ROOT
    flow/run.sh python3 designs/r1-joint/blocks/r1_top/tb/run_pwrup.py --run-id ID
Exit code 0 only if every criterion passed.
"""
import argparse, datetime, hashlib, json, os, subprocess, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
sys.path.insert(0, HERE)
import post_tb as P  # noqa: E402

NETS = ['designs/r1-joint/blocks/r1_bgr/schematic/r1_bgr.spice',
        'designs/r1-joint/blocks/r1_bias/schematic/r1_bias_rev1d.spice',
        'designs/r1-joint/blocks/r1_bias/sim/r1_bias_loads.spice',
        'designs/r1-joint/blocks/r1_osc/schematic/r1_osc.spice']
OUTS = ['ib_afe_s1', 'ib_afe_s2', 'ib_afe_c1', 'ib_afe_c2', 'ib_is_a', 'ib_is_b', 'ib_sf_oa', 'ib_sf_na',
        'ib_sf_ob', 'ib_sf_nb', 'ib_adc_ref']
LOAD = {'ib_afe_s1': 'ld_afe_ota1', 'ib_afe_s2': 'ld_afe_ota2', 'ib_afe_c1': 'ld_afe_ota1', 'ib_afe_c2': 'ld_afe_ota2',
        'ib_is_a': 'ld_isense', 'ib_is_b': 'ld_isense', 'ib_sf_oa': 'ld_safe', 'ib_sf_na': 'ld_safe',
        'ib_sf_ob': 'ld_safe', 'ib_sf_nb': 'ld_safe', 'ib_adc_ref': 'ld_adcref'}
REC = {'vref': 1.0449, 'i10': 10.14e-6, 'i5': 5.07e-6}          # bgr-op-20261020-b, bias-op-20261021-d (tt, 27 C)
OSC_BAND = (28e6, 32e6)
OSC_SCH22 = 32.69e6   # r1_osc README: schematic revision 2, tt, code 22
POR_REC = 'POR delay 197-247 us over tt/ss/ff x {1, 10} ms ramps (r1_bias README, bias-por-20261021-*)'


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def deck(a, out):
    L = ['* T10 test 1a: power-up subset (r1_bgr + r1_bias/r1_por + r1_osc), run %s' % a.run_id,
         '.lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerHBT.lib hbt_typ',
         '.lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerMOShv.lib mos_tt',
         '.lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerMOSlv.lib mos_tt',
         '.lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerRES.lib res_typ',
         '.lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerCAP.lib cap_typ',
         '.lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerDIO.lib dio_tt']
    nets = NETS if a.part == 'all' else ([n for n in NETS if 'r1_osc' not in n] if a.part == 'dc' else [n for n in NETS if 'r1_osc' in n])
    L += ['.include /work/' + n for n in nets]
    L += ['.option ' + a.opts, '.temp %g' % a.temp, '.global sub!', 'Vsub sub! 0 0',
          '* rails: VDDA 0 -> 3.3 V in %g us from 1 us, VDD 0 -> 1.2 V in %g us from 2 us' % (a.ramp, a.ramp),
          'Vdda vdda 0 pwl(0 0 1u 0 %gu 3.3)' % (1 + a.ramp),
          'Vdd vdd 0 pwl(0 0 2u 0 %gu 1.2)' % (2 + a.ramp),
          'Vdl vdl 0 dc 1.0']
    if a.part in ('all', 'dc'):
        L += ['Xbgr vdda 0 vref iptat pbias pcasc vbe dvbe r1_bgr',
          '* bgr loads as in the r1_bias decks: iptat into 1.0 V, vref 11 pF (ADC r1_reffilt5 10 pF + 1 pF)',
          'Vload iptat 0 dc 1.0', 'Cvref vref 0 11p',
              'Xbias vdda vdd 0 pbias pcasc ' + ' '.join(OUTS) + ' por_n r1_bias',
              'Cpor por_n 0 0.2p']
        for o in OUTS:
            L += ['Vm_%s %s %s_l dc 0' % (o, o, o), 'XLD_%s %s_l vdl 0 %s' % (o, o, LOAD[o])]
    if a.part in ('all', 'osc'):
        L += ['* r1_osc: enable tie-high (chip XU_TIE_OSC), trim code 22 = 10110 (ctrl OSC_CFG reset value) at VDD level',
          'Btr4 tr4 0 V=v(vdd)', 'Btr3 tr3 0 V=0', 'Btr2 tr2 0 V=v(vdd)', 'Btr1 tr1 0 V=v(vdd)', 'Btr0 tr0 0 V=0',
          'Ben osc_en 0 V=v(vdd)',
          'Xosc osc_en tr0 tr1 tr2 tr3 tr4 osc_clk vdd 0 r1_osc',
          'Cosc osc_clk 0 20f']
    sv = ['v(vdda)', 'v(vdd)']
    if a.part in ('all', 'dc'):
        sv += ['v(vref)', 'v(pbias)', 'v(pcasc)', 'v(por_n)'] + ['i(vm_%s)' % o for o in OUTS]
    if a.part in ('all', 'osc'):
        sv += ['v(osc_clk)']
    L += ['.save ' + ' '.join(sv),
          '.control', 'tran %s %gu 0 %s uic' % (a.tstep, a.tstop, a.tmax), 'rusage all',
          'write %s/tran.raw' % out, '.endc', '.end']
    return '\n'.join(L) + '\n'


def settle(t, v, rel=0.01):
    fin = float(np.mean(v[t >= t[-1] - 5e-6]))
    bad = np.where(np.abs(v - fin) > rel * abs(fin))[0]
    return fin, (float(t[bad[-1]]) if len(bad) else 0.0)


def evaluate(w, a):
    t = w['time']
    C, M = [], {}
    up = 1e-6 + a.ramp * 1e-6
    if a.part == 'osc':
        return osc_eval(w, a, C, M)
    fin, ts = settle(t, w['vref'])
    M['vref_final_V'], M['vref_settle_1pct_us'] = fin, ts * 1e6
    C.append(P.crit('VREF settles within 1 %% (%.4g us after VDDA reaches 3.3 V)' % ((ts - up) * 1e6), ts * 1e6,
                    '< 200 us (before the earliest POR release, 197 us + ramp)', ts < 197e-6))
    C.append(P.crit('VREF final within 1 % of the bgr record 1.0449 V', fin, '1.0345-1.0553',
                    abs(fin - REC['vref']) <= 0.01 * REC['vref'], 'V'))
    worst = 0.0
    for o in OUTS:
        i = -w['i(vm_%s)' % o]
        if np.mean(i[t >= t[-1] - 5e-6]) < 0:
            i = -i
        f, s = settle(t, i)
        rec = REC['i10'] if o.startswith('ib_afe') else REC['i5']
        M[o] = {'final_uA': f * 1e6, 'settle_1pct_us': s * 1e6, 'record_uA': rec * 1e6}
        worst = max(worst, s)
        C.append(P.crit('%s within 3 %% of the r1_bias record %.2f uA' % (o, rec * 1e6), f * 1e6,
                        '%.2f +- 3 %%' % (rec * 1e6), abs(f - rec) <= 0.03 * rec, 'uA'))
    M['bias_settle_worst_us'] = worst * 1e6
    C.append(P.crit('all 11 bias outputs settle within 1 % before the earliest POR release', worst * 1e6, '< 197 us',
                    worst < 197e-6, 'us'))
    pmax = float(np.max(w['por_n'][t > 2e-6]))
    M['por_n_max_after_2us_V'] = pmax
    C.append(P.crit('por_n held low while the rails rise and settle (whole deck)', pmax, '< 0.12 V (10 % of VDD)',
                    pmax < 0.12, 'V'))
    if a.part == 'all':
        osc_eval(w, a, C, M)
    M['por_release'] = 'not simulated; ' + POR_REC
    return C, M


def osc_eval(w, a, C, M):
    t = w['time']
    f, n = P.freq(t, w['osc_clk'], 0.6, t[-1] - 5e-6, t[-1])
    M['osc_f_MHz'] = f and f / 1e6
    t0 = P.first(P.crossings(t, w['osc_clk'], 0.6, True))
    M['osc_first_edge_us'] = t0 and t0 * 1e6
    # The D13 band 28-32 MHz is a chip (post-layout) target: CF is sized with the extracted wiring, the schematic
    # alone runs fast by design (r1_osc README: schematic tt code 22 32.69 MHz, post-layout 30.30 MHz passed).
    C.append(P.crit('r1_osc at code 22 within 2 %% of the schematic record %.2f MHz (r1_osc revision 2)' % (OSC_SCH22 / 1e6),
                    M['osc_f_MHz'], '%.2f +- 2 %%' % (OSC_SCH22 / 1e6), f is not None and abs(f - OSC_SCH22) <= 0.02 * OSC_SCH22, 'MHz'))
    M['d13_band_28_32MHz'] = ('not applicable at schematic level (post-layout record 30.30 MHz passed); schematic value '
                              '%.2f MHz' % (f / 1e6 if f else float('nan')))
    M['por_release'] = 'not simulated; ' + POR_REC
    return C, M


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run-id', required=True)
    ap.add_argument('--part', default='dc', choices=('dc', 'osc', 'all'), help='dc: bgr + bias + POR; osc: r1_osc on the ramped VDD')
    ap.add_argument('--temp', type=float, default=27.0)
    ap.add_argument('--ramp', type=float, default=10.0, help='rail ramp time in us (r1_bias start-up record: 10 us)')
    ap.add_argument('--tstop', type=float, default=40.0)
    ap.add_argument('--tstep', default='1n')
    ap.add_argument('--tmax', default='1n')
    ap.add_argument('--opts', default='method=gear reltol=1e-4 abstol=1e-12 vntol=1e-6 chgtol=1e-15 gmin=1e-15 itl4=100 klu')
    ap.add_argument('--timeout', type=float, default=14400)
    ap.add_argument('--eval-only', action='store_true', help='re-evaluate an existing run (no simulation)')
    a = ap.parse_args()
    root = os.environ['G1_RESULTS_ROOT']
    if a.eval_only:
        out = os.path.join(root, 'r1_top', 'tb', a.run_id)
        w = P.read_raw(os.path.join(out, 'tran.raw'))
        C = [P.crit('simulation reached tstop', float(w['time'][-1] * 1e6), '%g us' % a.tstop, w['time'][-1] * 1e6 >= a.tstop * 0.999)]
        c2, M = evaluate(w, a)
        C += c2
        res = {'run_id': a.run_id, 'test': '1a', 'part': a.part, 'temp_c': a.temp, 'sim_status': 'completed',
               't_end_us': float(w['time'][-1] * 1e6), 'criteria': C, 'measurements': M, 're_evaluated': True}
        res['verdict'] = 'passed' if all(c['status'] == 'passed' for c in C) else 'failed'
        json.dump(res, open(os.path.join(HERE, 'results', a.run_id + '.json'), 'w'), indent=1, default=float)
        for c in C:
            print('%-7s %s: %s (limit %s)' % (c['status'], c['name'], c['value'], c['limit']))
        print('verdict', res['verdict'])
        sys.exit(0 if res['verdict'] == 'passed' else 1)
    out = os.path.join(root, 'r1_top', 'tb', a.run_id)
    rec_dir = os.path.join(HERE, 'runs', a.run_id)
    if os.path.exists(out) or os.path.exists(rec_dir):
        sys.exit('run id %s exists' % a.run_id)
    os.makedirs(out)
    os.makedirs(rec_dir)
    d = deck(a, out)
    open(os.path.join(out, 'deck.cir'), 'w').write(d)
    open(os.path.join(rec_dir, 'deck.cir'), 'w').write(d.replace(root, '<G1_RESULTS_ROOT>'))
    run = {'run_id': a.run_id, 'block': 'r1_top', 'track': 'T10', 'test': '1a',
           'description': 'power-up subset: r1_bgr + r1_bias (r1_por) + r1_osc on ramped rails, real netlists',
           'part': a.part, 'temp_c': a.temp, 'ramp_us': a.ramp, 'tstop_us': a.tstop, 'tstep': a.tstep, 'tmax': a.tmax,
           'options': a.opts, 'method_note': 'uic start from 0 V (no operating point)',
           'command': 'flow/run.sh python3 designs/r1-joint/blocks/r1_top/tb/run_pwrup.py ' + ' '.join(sys.argv[1:]),
           'bulk_dir': '<G1_RESULTS_ROOT>/r1_top/tb/' + a.run_id,
           'started_utc': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
           'pdk_commit': '84374023ee8b4b126bebbba67fcbada0a9c0ff0b',
           'inputs_sha256': {n: sha(os.path.join(REPO, n)) for n in NETS},
           'm6_vref_buffer': 'not in this deck (bgr vref loaded by 11 pF only)'}
    lf = open(os.path.join(out, 'ngspice.log'), 'w')
    p = subprocess.Popen(['ngspice', '-b', os.path.join(out, 'deck.cir')], stdout=lf, stderr=subprocess.STDOUT, cwd=HERE)
    try:
        rc = p.wait(timeout=a.timeout)
        run['status'] = 'completed' if rc == 0 else 'failed'
    except subprocess.TimeoutExpired:
        p.kill()
        rc = None
        run['status'] = 'timeout'
    lf.close()
    run['rc'] = rc
    txt = open(os.path.join(out, 'ngspice.log'), errors='replace').read()
    for k in ('Total analysis time', 'Transient analysis time', 'Accepted timepoints', 'Circuit Equations'):
        for l in txt.splitlines():
            if l.startswith(k):
                run[k.lower().replace(' ', '_')] = l.split('=')[-1].strip()
    if 'Timestep too small' in txt:
        run['abort'] = [l.strip() for l in txt.replace(' Reference value', '\n').splitlines() if 'Timestep too small' in l][:1]
    res = {'run_id': a.run_id, 'test': '1a', 'temp_c': a.temp, 'sim_status': run['status']}
    rawp = os.path.join(out, 'tran.raw')
    C, M = [], {}
    if not os.path.exists(rawp):
        C.append(P.crit('simulation produced a waveform file', None, 'tran.raw', False))
    else:
        w = P.read_raw(rawp)
        res['t_end_us'] = float(w['time'][-1] * 1e6)
        C.append(P.crit('simulation reached tstop', res['t_end_us'], '%g us' % a.tstop, res['t_end_us'] >= a.tstop * 0.999))
        try:
            c2, M = evaluate(w, a)
            C += c2
        except Exception as e:
            C.append(P.crit('evaluation', repr(e), 'no exception', False))
    res['criteria'], res['measurements'] = C, M
    res['verdict'] = 'passed' if C and all(c['status'] == 'passed' for c in C) else 'failed'
    run['verdict'] = res['verdict']
    json.dump(run, open(os.path.join(out, 'run.json'), 'w'), indent=1)
    json.dump(run, open(os.path.join(rec_dir, 'run.json'), 'w'), indent=1)
    os.makedirs(os.path.join(HERE, 'results'), exist_ok=True)
    json.dump(res, open(os.path.join(HERE, 'results', a.run_id + '.json'), 'w'), indent=1, default=float)
    for c in C:
        print('%-7s %s: %s (limit %s)' % (c['status'], c['name'], c['value'], c['limit']))
    print('verdict', res['verdict'])
    sys.exit(0 if res['verdict'] == 'passed' else 1)


if __name__ == '__main__':
    main()
