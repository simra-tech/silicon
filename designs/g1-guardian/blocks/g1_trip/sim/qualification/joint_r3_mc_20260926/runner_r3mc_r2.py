#!/usr/bin/env python3
"""r2 (2026-09-26, written to bulk while the home quota was full): identical method and deck; adds
--summary-dir (per-seed summary.json outside the repository) and --resume (a leaf whose run.json is terminal and
whose probe.cir equals the deck this runner would write is analysed again instead of re-simulated; a
non-terminal leaf is moved to pNN.interrupted and re-simulated).

Joint calibrated mismatch screen of the on-chip TRIP chain (joint_r3_mc_20260926), one seed per process.

Blocks as on the chip: BGR586 (sources/bgr.spice = 586ffb58 with mm_ok=1 on all 1036 devices, 7de0fc30),
SENSE comp45+R100 (sources/sense.spice, bb933fda), TRIP with NF4 soft input pair and regenpair4 hard
comparator (sources/trip.spice, f5f0a90a). The deck is the probe of the passed seed-73133 NF4 run
(qualification/joint586-softinputpair4-nf4-roomcal-s73133-20260924-r1/c00/probe.cir); per probe only the
ngspice seed, .temp, the shunt source Vsh, the 16 DAC code bits, the include paths and the wave path change
(`--selftest` shows that seed 73133 reproduces the c00 and heldout-p27 decks of that run exactly, up to paths).

Method = the original joint586 runner (qualification/joint586-calibration-s73133-20260922-a/runner.py):
  calibration at 25 C, known shunt 25 mV: codes [0,0], [255,255], then the original binary rule
  (audit_bgr_calibration_tree.replay), hard nominal code 204; corrected codes = nominal + signed correction;
  guards with the corrected codes at 25, -40, 125 C: 27 mV (no trip), 33 mV (soft trip only),
  0.9*T_hard (soft only), 1.1*T_hard (both), T_hard = 204*1.04/5300 = 40.03 mV;
  residuals with the bracket-midpoint codes at 25, -40, 125 C: 24.5 mV (no trip), 25.5 mV (trip).
Solver/deck settings, sampling (measured-edge rule, 3 decisions per comparator, all must agree),
watchdog (1200 s per probe, run_bounded) as in the NF4 run.
Failures are classified: numerical (watchdog, return code, solver errors, missing marker, wave/sampling
failure, parameter-vector inconsistency) vs electrical (clean run, wrong decision or failed bracketing).

  cd designs/g1-guardian/blocks/g1_trip/sim && python3 qualification/joint_r3_mc_20260926/runner_r3mc.py --seed N --bulk DIR
  python3 qualification/joint_r3_mc_20260926/runner_r3mc.py --selftest
"""
import argparse, hashlib, json, math, re, sys
from pathlib import Path

SIM = Path('/work/designs/g1-guardian/blocks/g1_trip/sim')
HERE = SIM / 'qualification/joint_r3_mc_20260926'
sys.path.insert(0, str(SIM))
from audit_bgr_calibration_tree import replay                       # noqa: E402
from run_nominal_clock_probe import analyze_wave, run_bounded  # noqa: E402
from run_joint586_transients import phase_parameters                # noqa: E402
from run_bgr_substitution_draw_audit import read_group               # noqa: E402
from analyze_bgr_substitution_outcomes import warning_inventory      # noqa: E402
from wave_archive import archive_new_wave                            # noqa: E402

REF = SIM / 'qualification/joint586-softinputpair4-nf4-roomcal-s73133-20260924-r1'
RUN = 'joint_r3_mc_20260926'
SRC = {'sense.spice': 'bb933fdabf3fd8a5117bf47f33cd40657caf78ef424e6a9bfddda0f11190d782',
       'trip.spice': 'f5f0a90aff361fd782f29112217cbd647d18af593a930ade2d59dfbab5847a92',
       'bgr.spice': '7de0fc30697d1e81d40c3200a511faf0479cfd8b397bbaa3cec6dbc4fa758c61'}
TEMPLATE_SHA = None  # recorded in the README (sha of REF/c00/probe.cir)
T_HARD = 204 * 1.04 / 5300
GUARDS = [(.027, {'soft': False, 'hard': False}), (.033, {'soft': True, 'hard': False}),
          (.9 * T_HARD, {'soft': True, 'hard': False}), (1.1 * T_HARD, {'soft': True, 'hard': True})]
TEMPS = [25, -40, 125]
LSB_SHUNT_MV = 1.04 / 5300 * 1e3
NF4_FIELDS = ['@n.xt.xcs.xm%d.nsg13_lv_nmos[%s]' % (i, k) for i in [1, 2] for k in ['nf', 'as', 'ad', 'ps', 'pd', 'mult']]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def fmt(v):
    return repr(float(v)) if False else format(v, '.17g')


def make_deck(template, seed, codes, shunt, temp, wave):
    t = template
    old_prefix = 'qualification/' + REF.name + '/'
    n_inc = t.count('.include ' + old_prefix)
    assert n_inc == 3
    t = t.replace('.include ' + old_prefix, '.include qualification/' + RUN + '/sources/')
    t, n = re.subn(r'(?m)^setseed \d+$', 'setseed %d' % seed, t); assert n == 1
    t, n = re.subn(r'(?m)^\.temp .+$', '.temp %s' % format(float(temp), '.1f'), t); assert n == 1
    t, n = re.subn(r'(?m)^Vsh shp 0 dc .+$', 'Vsh shp 0 dc %s' % format(shunt, '.17g'), t); assert n == 1
    for ch, code in zip('sh', codes):
        for b in range(8):
            t, n = re.subn(r'(?m)^V%s%d %s%d 0 dc .+$' % (ch, b, ch, b),
                           'V%s%d %s%d 0 dc %s' % (ch, b, ch, b, '1.2' if code >> b & 1 else '0'), t); assert n == 1
    t, n = re.subn(r'(?m)^wrdata \S+/phase0\.dat ', 'wrdata %s ' % wave, t); assert n == 1
    return t


def section_of(log):
    s, = re.findall(r'^PHASE0_BEGIN\n(.*?)^PHASE0_END$', log, re.M | re.S)
    return s


def nf4_values(log, phase):
    sec, = re.findall(r'^NF4_' + phase + r'_BEGIN\n(.*?)^NF4_' + phase + r'_END$', log, re.M | re.S)
    rows = dict(re.findall(r'(@n\.xt\.xcs\.xm[12]\.nsg13_lv_nmos\[\w+\])\s*=\s*([-+0-9.eE]+)', sec))
    assert set(rows) == set(NF4_FIELDS)
    return rows


def selftest():
    tmpl = (REF / 'c00/probe.cir').read_text()
    for leaf, codes, shunt, temp in [('c00', [0, 0], .025, 25), ('heldout-p27', [131, 173], .0255, 125), ('c05', None, .025, 25)]:
        ref = (REF / leaf / 'probe.cir').read_text()
        if codes is None:
            codes = json.loads((REF / leaf / 'provenance.json').read_text())['codes']
        wave = 'qualification/' + REF.name + '/' + leaf + '/phase0.dat'
        d = make_deck(tmpl, 73133, codes, shunt, temp, wave).replace('qualification/' + RUN + '/sources/', 'qualification/' + REF.name + '/')
        print('selftest', leaf, codes, 'identical' if d == ref else 'DIFFERENT')
        assert d == ref
    for n, h in SRC.items():
        assert sha(HERE / 'sources' / n) == h == sha(REF / n), n
    print('selftest sources ok')


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--seed', type=int); p.add_argument('--bulk', type=Path); p.add_argument('--selftest', action='store_true')
    p.add_argument('--summary-dir', type=Path); p.add_argument('--resume', action='store_true')
    a = p.parse_args()
    if a.selftest:
        selftest(); return
    for n, h in SRC.items():
        assert sha(HERE / 'sources' / n) == h, n
    contract = json.loads((REF / 'contract.json').read_text())
    groups, sampling, nf4_ref = contract['groups'], contract['sampling'], contract['native_reported_geometry']
    template = (REF / 'c00/probe.cir').read_text()
    outrepo = (a.summary_dir or HERE) / ('s%d' % a.seed); outrepo.mkdir(parents=True, exist_ok=a.resume)
    bulk = a.bulk / ('s%d' % a.seed); bulk.mkdir(parents=True, exist_ok=a.resume)
    result = dict(seed=a.seed, status='running', bracket_status='not run', guards_status='not run', residual_status='not run',
                  numerical_failures=[], electrical_failures=[], probes=[], template_sha256=sha(REF / 'c00/probe.cir'),
                  runner_sha256=sha(Path(__file__)), sources_sha256=SRC, resumed=a.resume, reused_leaves=[])
    vector = {'sha': None}

    def persist():
        tmp = outrepo / 'summary.json.pending'; tmp.write_text(json.dumps(result, indent=2) + '\n'); tmp.replace(outrepo / 'summary.json')

    def probe(codes, shunt, temp, kind, expected=None):
        idx = len(result['probes']); leaf = bulk / ('p%02d' % idx)
        deck = make_deck(template, a.seed, codes, shunt, temp, str(leaf / 'phase0.dat'))
        reuse = False
        if a.resume and leaf.exists():
            st = json.loads((leaf / 'run.json').read_text()) if (leaf / 'run.json').exists() else {}
            if 'returncode' in st and (leaf / 'probe.cir').read_text() == deck:
                reuse = True
            else:
                leaf.rename(leaf.with_name(leaf.name + '.interrupted'))
        if not reuse:
            leaf.mkdir()
        # (run_nominal_clock_probe.validate_saved_nodes expects the pre-regenpair4 hard cell; the deck identity
        #  with the NF4 run is established by --selftest instead)
        if reuse:
            state = json.loads((leaf / 'run.json').read_text()); result['reused_leaves'].append(leaf.name)
        else:
            (leaf / 'probe.cir').write_text(deck)
            with (leaf / 'run.log').open('x') as s:
                state = run_bounded(['ngspice', '-b', str(leaf / 'probe.cir')], s, leaf / 'run.json', 1200, cwd=SIM, interval_s=1)
        log = (leaf / 'run.log').read_text()
        errors = [l for l in log.splitlines() if re.search(r'(?im)^Error|Timestep too small|analysis aborted|doAnalyses:|no such vector|no such parameter|not available|cannot parse', l)]
        e = dict(leaf='p%02d' % idx, kind=kind, codes=codes, shunt_V=shunt, temperature_C=temp, status='failed', class_='numerical',
                 wall_s=state['wall_s'], watchdog_status=state['status'], returncode=state['returncode'], errors=errors[:5],
                 deck_sha256=sha(leaf / 'probe.cir'), decisions={}, warnings=warning_inventory(log))
        if expected is not None:
            e['expected_decisions'] = expected
        try:
            assert state['status'] == 'completed' and state['returncode'] == 0 and not errors and 'JOINT_POPULATION_TRAN_END' in log
            sec = section_of(log)
            nb, na = nf4_values(sec, 'BEFORE'), nf4_values(sec, 'AFTER')
            assert nb == na == nf4_ref, 'NF4 native geometry changed'
            clean = re.sub(r'(?ms)^NF4_(BEFORE|AFTER)_BEGIN\n.*?^NF4_\1_END\n', '', sec)
            before = read_group(clean, 'NON_BGR_BEFORE', groups['NON_BGR']) + read_group(clean, 'BGR_BEFORE', groups['BGR'])
            params = phase_parameters(clean, groups, before)
            vs = hashlib.sha256(json.dumps(params['parameters_before']).encode()).hexdigest()
            if vector['sha'] is None:
                vector['sha'] = vs; result['parameter_vector_sha256'] = vs
                (outrepo / 'parameters_before.json.sha256').write_text(vs + '\n')
                (bulk / 'parameters_before.json').write_text(json.dumps(params['parameters_before']))
            assert vs == vector['sha'], 'mismatch draw differs between probes of one seed'
            data = [list(map(float, l.split())) for l in (leaf / 'phase0.dat').read_text().splitlines()[1:] if l.strip()]
            assert data and all(len(r) == 18 and all(math.isfinite(v) for v in r) for r in data)
            assert abs(data[-1][0] - 1.02e-6) < 1e-18
            an = analyze_wave([r[:13] for r in data], sampling)
            assert an['sampling_status'] == 'passed', an['sampling_status']
            dec = {k: v['measured_edge_decision'] for k, v in an['comparators'].items()}
            assert set(dec) == {'soft', 'hard'} and all(type(v) is bool for v in dec.values())
            e.update(status='passed', class_=None, decisions=dec, wave_rows=len(data),
                     differentials_mV={k: [x * 1e3 for x in v['measured_edge_sample_differentials_V']] for k, v in an['comparators'].items()})
            (leaf / 'analysis.json').write_text(json.dumps(an) + '\n')
        except (AssertionError, ValueError, OSError, KeyError, IndexError) as err:
            e['analysis_error'] = repr(err)[:500]
        if (leaf / 'phase0.dat').exists():
            archive_new_wave(leaf / 'phase0.dat')
        result['probes'].append(e)
        if e['status'] != 'passed':
            result['numerical_failures'].append(e['leaf'])
        elif expected is not None and e['decisions'] != expected:
            e['class_'] = 'electrical'; result['electrical_failures'].append(e['leaf'])
        persist()
        return e

    persist()
    probe([0, 0], .025, 25, 'calibration'); probe([255, 255], .025, 25, 'calibration')
    while True:
        recs = [dict(run=r['leaf'], codes=r['codes'], status=r['status'], decisions=r['decisions']) for r in result['probes'] if r['kind'] == 'calibration']
        tree = replay(recs); result['calibration'] = {k: v for k, v in tree.items() if k != 'all_attempts'}; persist()
        if 'next_required_codes' not in tree or tree['bracket_status'].startswith('failed'):
            break
        probe(tree['next_required_codes'], .025, 25, 'calibration')
    result['bracket_status'] = tree['bracket_status']
    if tree['bracket_status'] != 'passed selected probes':
        numeric = any(r['status'] != 'passed' for r in result['probes'])
        result['status'] = 'failed calibration (%s)' % ('numerical' if numeric else 'electrical')
        if not numeric:
            result['electrical_failures'].append('calibration: ' + tree['bracket_status'])
    else:
        nominal_code_25mV = .025 * 5300 / 1.04
        result['calibration_reach'] = {k: dict(bracket=v, crossing_code=sum(v) / 2, offset_before_cal_mV_shunt=(sum(v) / 2 - nominal_code_25mV) * LSB_SHUNT_MV,
                                               correction=tree['signed_correction_codes'][k], clipped=tree['clipped'][k],
                                               corrected_code=tree['corrected_codes'][k], residual_code=tree['fixed_residual_codes'][k],
                                               residual_after_cal_mV_shunt=(tree['fixed_residual_codes'][k] - sum(v) / 2) * LSB_SHUNT_MV)
                                       for k, v in tree['brackets'].items()}
        codes = [tree['corrected_codes'][k] for k in ['soft', 'hard']]
        ok = []
        for temp in TEMPS:
            for shunt, exp in GUARDS:
                e = probe(codes, shunt, temp, 'guard', exp); ok.append(e['status'] == 'passed' and e['decisions'] == exp)
        result['guards_status'] = 'passed' if all(ok) else 'failed'
        codes = [tree['fixed_residual_codes'][k] for k in ['soft', 'hard']]
        ok = []
        for temp in TEMPS:
            for shunt, high in [(.0245, False), (.0255, True)]:
                exp = {'soft': high, 'hard': high}
                e = probe(codes, shunt, temp, 'residual', exp); ok.append(e['status'] == 'passed' and e['decisions'] == exp)
        result['residual_status'] = 'passed' if all(ok) else 'failed'
        if result['guards_status'] == result['residual_status'] == 'passed':
            result['status'] = 'passed'
        elif result['numerical_failures']:
            result['status'] = 'failed (numerical%s)' % (' + electrical' if result['electrical_failures'] else '')
        else:
            result['status'] = 'failed (electrical)'
    result['total_core_seconds'] = sum(r['wall_s'] for r in result['probes'])
    persist()
    print(json.dumps({k: result[k] for k in ['seed', 'status', 'bracket_status', 'guards_status', 'residual_status', 'numerical_failures', 'electrical_failures']}))


if __name__ == '__main__':
    main()
