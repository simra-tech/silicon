#!/usr/bin/env python3
"""T2 post-layout harness runner (2026-10-26): one ngspice job per call, the revision-5 rules (sim/r5/run_points5.py,
run_deck5.py, run_ngspice5.py): no resume, no resubmission, no frame skipping, exit 1 on any job that is not
"completed" (return code, abort / singular-matrix / no-convergence lines, missing output). Run records:
sim/post/runs/<id>/{deck.cir, ngspice.log, run.json}; segments: sim/post/results/<id>_segments.json; raw files:
<G1_RESULTS_ROOT>/r1_adc/<id>/.

usage: run_post.py --id ID --cpu N --deck points|isa --core rec|recfast|lay [--netlist sim/post/r1_adc_lay0.spice]
       [--ref ideal|opt3 (rec) | lay|lay-ideal (lay)] [--vref 1.045 | op:<run id>] [--points <json>] [--save codes|full]
       [--op-only] [--corner mos_tt --temp 27 --vdd 1.2] [--timing <inc in sim/r5>] [--tstop 3.31u] [--noise auto|tt|ss|none]
       [--ibias 5u] [--question ...] [--disposition ...]
Cores: rec = r1_adc5_core (netlist of record, full core), recfast = r1_adc5_core_fast (the r5 points-deck core),
lay = r1_adc5_core_lay (sim/post/r1_adc5_post.spice around the layout netlist --netlist).
Reference: rec/recfast: ideal (Vref on all four ports) or opt3 (r1_refbuf5 ndec 4 ndecl 2 + 10 pF filter + bandgap
model, as run_points5.py). lay: the buffer and the 10 pF filter are in the layout netlist; the deck gives the bandgap
model (Vbgi + TRNOISE, Rbg 190 kOhm into vref_in) and Ibref 5 uA into ibias. lay-ideal: the same plus ideal sources on
vrefa (= vref) and vrefla (= vrefl), bandgap DC without noise (base runs of the R2-4 metric, static windows).
"""
import argparse, datetime, hashlib, json, os, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
BLOCK = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.abspath(os.path.join(BLOCK, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(BLOCK, 'sim', 'r5'))
import run_ngspice5 as R5      # noqa: E402  (constants, sha256, frozen_check; main() is not called)
T = 1.0 / 30e6
F, T0 = 22 * T, 18 * T
PWL_SHIFT = 5e-9

ap = argparse.ArgumentParser()
for k, d in (('--id', None), ('--cpu', None), ('--deck', None), ('--core', None), ('--netlist', 'sim/post/r1_adc_lay0.spice'),
             ('--ref', ''), ('--vref', '1.045'), ('--points', ''), ('--save', 'codes'), ('--corner', 'mos_tt'), ('--temp', '27'),
             ('--vdd', '1.2'), ('--cm', '0.6'), ('--timing', ''), ('--tstop', ''), ('--tmax', '0.2n'), ('--noise', 'auto'),
             ('--ibias', '5u'), ('--bgr', '190k,82u'), ('--question', ''), ('--disposition', ''), ('--timeout', '36000'),
             ('--seed', '1'), ('--noopiter', 'auto'), ('--ideal-bgr', 'off50m'), ('--solver', 'klu'), ('--base-ibias', ''), ('--probe-extra', ''), ('--save-extra', ''), ('--rs', '')):
    ap.add_argument(k, required=d is None, default=d)
ap.add_argument('--op-only', action='store_true')
a = ap.parse_args()
root = os.environ['G1_RESULTS_ROOT']
vtag = {'1.2': '', '1.08': '_vdd108', '1.32': '_vdd132'}[a.vdd]
lay = a.core == 'lay'
ref = a.ref or ('lay' if lay else 'ideal')
assert (ref in ('lay', 'lay-ideal')) == lay, 'reference model does not match the core'
vref_src = a.vref
if a.vref.startswith('op:'):
    # op:<run> = v(vrefa) of an op-only run; op:<run>:<vec>+<vec> = mean of the named op vectors (2026-10-26: slice-port
    # nodes of the reference in an RC netlist, e.g. v(xadc.xl.vref__p8)+v(xadc.xl.vref__p9))
    f_ = a.vref[3:].split(':', 1)
    opd = os.path.join(root, 'r1_adc', f_[0], 'op.txt')
    vecs = f_[1].split('+') if len(f_) > 1 else ['v(vrefa)']
    vals = {l.split('=')[0].strip(): float(l.split('=')[1]) for l in open(opd) if '=' in l}
    a.vref = '%.6f' % (sum(vals[v] for v in vecs) / len(vecs))

# --- reference lines
cal = json.load(open(os.path.join(BLOCK, 'sim', 'results', 'r5', 'trnoise_cal.json')))
nz = a.noise if a.noise != 'auto' else ('ss' if a.corner == 'mos_ss' else 'tt')
rs, cw = a.bgr.split(',')
def bgr_src(noise):
    if noise == 'none':
        return 'Vbgi vbgi 0 DC 1.045'
    c = cal['corners']['ss125' if noise.startswith('ss') else 'tt27']
    nt = 47.3e-9          # off the clock grid (revision-5 failure 4)
    return ('Vbgi vbgw 0 DC 1.045 TRNOISE(%.4g %.4g 0 0)\nVbgf vbgi vbgw DC 0 TRNOISE(0 %.4g %.3g %.4g)'
            % (c['NA_V'] * (50e-9 / nt) ** 0.5, nt, nt, cal['alpha'], c['NAMP_V']))
if ref == 'ideal':
    lines = ['Vref vref 0 %s' % a.vref] + ['Vt%s %s vref 0' % (n, n) for n in ('vrefa', 'vrefb', 'vrefla', 'vreflb')]
elif ref == 'opt3':
    lines = ['Vdda vdda 0 3.3', bgr_src(nz), 'Rbg vbgi vbg %s' % rs, 'XCF vbg 0 r1_reffilt5 w=%s' % cw,
             'Ibref vdda nbr %s' % a.ibias, 'XREF vbg vref vrefl nbr vdda 0 r1_refbuf5 ndec=4 ndecl=2',
             'Vtvrefa vrefa vref 0', 'Vtvrefb vrefb vref 0', 'Vtvrefla vrefla vrefl 0', 'Vtvreflb vreflb vrefl 0']
elif ref == 'lay':
    lines = ['Vdda vdda 0 3.3', bgr_src(nz), 'Rbg vbgi vbg %s' % rs, 'Ibref vdda nbr %s' % a.ibias]
else:   # lay-ideal
    # --ideal-bgr off50m (default, 2026-10-26): bandgap DC 50 mV below the forced reference, so the error amplifier of the
    # laid-out buffer rails (ng low, followers off) instead of balancing at high open-loop gain against an ideal source;
    # with the bandgap at the forced value the first-conversion deck ran 14 x slower than the netlist of record (run
    # post-fc-tt-lay0). 'same': bandgap DC = 1.045 V (the first behaviour).
    bdc = 1.045 if a.ideal_bgr == 'same' else float(a.vref) - 0.05
    # --base-ibias (2026-10-26): bias current of the laid-out buffer in the base run. 0 = buffer off: no static current in
    # the reference wiring, so the forced value reaches the CDAC drivers unchanged. With the buffer biased, the 0.8 mA of
    # the sink XMIB flows from the forced main node through the wiring (RC netlist: 85-166 Ohm) and the slice-edge vref
    # moved by tens of mV (post-ref-tt-rc2-ideal: 100 LSB code difference)
    lines = ['Vdda vdda 0 3.3', 'Vbgi vbgi 0 DC %.6f' % bdc, 'Rbg vbgi vbg %s' % rs, 'Ibref vdda nbr %s' % (a.base_ibias or a.ibias),
             'Vrefi vrefa 0 %s' % a.vref, 'Vrefli vrefla 0 %s' % a.vref]
reflines = '\n'.join(lines)
cell = {'rec': 'r1_adc5_core', 'recfast': 'r1_adc5_core_fast', 'lay': 'r1_adc5_core_lay'}[a.core]
extra = 'vbg nbr vdda' if lay else ''
nets = ['.include schematic/r1_adc_r5.spice']
if lay:
    nets += ['.include %s' % a.netlist, '.include sim/post/r1_adc5_post.spice']
has_vdda = ref != 'ideal'
pfx = 'xadc.xl.' if lay else 'xadc.'
probe = ('v(vrefa) v(vrefb) v(vrefla) v(vreflb) v(topap) v(topan) v(topbp) v(topbn) v(%svbp) v(%svbn) i(vdd)' % (pfx, pfx)
         + (' v(xadc.xl.xslice_a.lsb_p) v(xadc.xl.xslice_a.lsb_n) v(xadc.xl.xref_ng)' if lay else
            ' v(xadc.xtha.lsb_p) v(xadc.xtha.lsb_n)' + (' v(xref.ng)' if ref == 'opt3' else ''))
         + (' v(vbg) i(vdda)' if has_vdda else '') + (' ' + a.probe_extra if a.probe_extra else ''))
# --solver sparse (2026-10-26, post-layout RC netlist): with the R networks, KLU reports a singular matrix in every OP
# method (floating top-plate and bottom-plate clusters of R-only nodes); Sparse 1.3 converges at the first gmin stepping
assert a.solver in ('klu', 'sparse'), a.solver
opts = 'reltol=1e-4 vntol=1e-6 abstol=1e-12 method=trap %s seed=%s' % (a.solver, a.seed)
# noopiter (layout cores, 2026-10-26): the rppd bias resistors are drawn as 4 series segments; their inner nodes start at
# 0 V, the first Newton attempt of the OP hits the r3 vmax limit and KLU reports a singular matrix before the dynamic gmin
# stepping that the netlist of record also needs. noopiter starts with the gmin stepping: same OP to the printed digit
# (scratch runs post-dbg-sing). KLU does not accept .nodeset.
if a.noopiter == 'yes' or (a.noopiter == 'auto' and lay):
    opts += ' noopiter'
subs = {'CORNER': a.corner, 'TEMP': a.temp, 'VDD': a.vdd, 'CM': a.cm, 'NETLISTS': '\n'.join(nets), 'REFLINES': reflines,
        'TMAX': a.tmax}
STB = ' '.join('stba%d' % k for k in range(14)) + '\n+ ' + ' '.join('stbb%d' % k for k in range(14))
if a.deck == 'points':
    P = json.load(open(os.path.join(BLOCK, a.points)))
    va, vb = P['a'], P['b']
    def pwl(v):
        pts = []
        for s, x in enumerate(v):
            if s:
                t = T0 + s * F - 550e-9 + PWL_SHIFT
                pts += ['%.6e %.7f' % (t, v[s - 1]), '%.6e %.7f' % (t + 10e-9, x)]
            else:
                pts.append('0 %.7f' % x)
        return '\n+ '.join(' '.join(pts[i:i + 8]) for i in range(0, len(pts), 8))
    tstop = a.tstop or '%.4fu' % ((T0 + (len(va) - 1) * F + 14 * T + 60e-9) * 1e6)
    save = ('v(rawa) v(rawb)' if a.save == 'codes' else
            'v(rawa) v(rawb) v(vrefa) v(vrefb) v(vrefla) v(vreflb) v(topap) v(topan) v(topbp) v(topbn) i(vdd) v(clk30) v(trka0) v(trkb0)')
    if has_vdda:
        save += ' i(vdda) v(vbg)'
    if a.save_extra:
        save += ' ' + a.save_extra
    if a.op_only:
        analysis, save, expect = 'op\nprint %s > @RAW@/op.txt' % probe, 'all', 'op.txt'
    else:
        analysis, expect = 'tran 1n %s 0 %s\nwrite @RAW@/codes.raw' % (tstop, a.tmax), 'codes.raw'
    if a.save == 'codes' and not a.op_only:
        opts += ' interp'
    subs.update(CAPLIB='cap_typ', TIMING=a.timing or 'r1_adc_timing_r5_n0_cq%s.inc' % vtag, TSTOP=tstop, PWLA=pwl(va),
                PWLB=pwl(vb), SAVE=save, ANALYSIS=analysis,
                INSTANCES='XADC sinp sinn cosp cosn isap isan isap isan trka0 trka1 trkb0 trkb1 clk30 wina winb lata latb\n+ %s\n'
                          '+ rawa rawb topap topan topbp topbn vdd vrefa vrefb vrefla vreflb 0 %s %s' % (STB, extra, cell))
    deck = 'sim/post/tb_post_points.cir'
elif a.deck == 'isa':
    tstop = a.tstop or '3.31u'
    subs.update(TIMING=a.timing or 'r1_adc_timing_r5_mux_n0_cq%s_pre33.inc' % vtag, TSTOP=tstop, CORECELL=cell, COREEXTRA=extra,
                ISAVE=('i(vdda) v(vbg) v(vrefla)' if has_vdda else 'v(vrefla)'),
                MEASA=('meas tran idda avg i(vdda) from=0.6u to=%s' % tstop) if has_vdda else '')
    expect = 'codes.raw'
    deck = 'sim/post/tb_post_isa.cir'
    if a.op_only:
        sys.exit('--op-only: use --deck points')
else:
    sys.exit('unknown --deck')
subs['OPTS'] = opts

# --- execute (copy of the run_ngspice5.py logic with the run records under sim/post/runs)
raw_dir = os.path.join(root, 'r1_adc', a.id)
run_dir = os.path.join(HERE, 'runs', a.id)
if os.path.exists(os.path.join(run_dir, 'run.json')) or os.path.exists(os.path.join(raw_dir, 'deck.cir')):
    sys.exit('run id exists: %s' % a.id)
os.makedirs(run_dir, exist_ok=True)
os.makedirs(raw_dir, exist_ok=True)
src = open(os.path.join(BLOCK, deck)).read()
if a.rs:
    # --rs R (isa deck, 2026-10-26 layout-B track, top-plate reset question): each of the 8 ADC inputs is driven through a
    # series resistor R from its E source (node <in>_s), so the top-plate voltage at the start of track and the charge drawn
    # from the source become visible; the inputs <in>_s are saved
    assert a.deck == 'isa', '--rs: isa deck only'
    for n in ('sinp', 'sinn', 'cosp', 'cosn', 'isap', 'isan', 'isbp', 'isbn'):
        e = {'sinp': 'Esp', 'sinn': 'Esn', 'cosp': 'Ecp', 'cosn': 'Ecn', 'isap': 'Eap', 'isan': 'Ean', 'isbp': 'Ebp', 'isbn': 'Ebn'}[n]
        assert ('\n%s %s ' % (e, n)) in src, (e, n)
        src = src.replace('\n%s %s ' % (e, n), '\nRs%s %s_s %s %s\n%s %s_s ' % (n, n, n, a.rs, e, n))
    src = src.replace('save v(rawa)', 'save v(sinp_s) v(sinn_s) v(isap_s) v(isan_s) v(sinp) v(sinn) v(isap) v(isan) v(rawa)', 1)
subs['RAW'] = raw_dir
for k, v in subs.items():
    src = src.replace('@%s@' % k, v)
src = src.replace('@RAW@', raw_dir)
assert '@' not in src.replace('@RAW', ''), [l for l in src.splitlines() if '@' in l][:3]
open(os.path.join(run_dir, 'deck.cir'), 'w').write(src.replace(root, '<G1_RESULTS_ROOT>'))
open(os.path.join(raw_dir, 'deck.cir'), 'w').write(src)
libs = ['schematic/r1_adc_r5.spice'] + ([a.netlist, 'sim/post/r1_adc5_post.spice'] if lay else [])
lib_hash = {p: R5.sha256(os.path.join(BLOCK, p)) for p in libs}
log_path = os.path.join(run_dir, 'ngspice.log')
env = dict(os.environ)
env.update({'G1_CPUSET': a.cpu, 'G1_CPUS': '1', 'G1_WORKDIR': os.path.relpath(BLOCK, REPO), 'G1_RESULTS_ROOT': root})
t0 = time.time()
started = datetime.datetime.utcnow().isoformat() + 'Z'
with open(log_path, 'w') as lf:
    p = subprocess.Popen([os.path.join(REPO, 'flow', 'run.sh'), 'ngspice', '-b', os.path.join(raw_dir, 'deck.cir')],
                         stdout=lf, stderr=subprocess.STDOUT, env=env, cwd=REPO)
    open(os.path.join(raw_dir, 'runner.pid'), 'w').write('%d\n' % p.pid)
    try:
        rc = p.wait(timeout=int(a.timeout)); status = 'completed' if rc == 0 else 'failed'
    except subprocess.TimeoutExpired:
        p.kill(); rc = None; status = 'timeout'
wall = time.time() - t0
log = open(log_path, errors='replace').read().replace(root, '<G1_RESULTS_ROOT>')
lines_ = log.splitlines()
errors = [l.strip() for l in lines_ if l.lower().startswith('error') or 'fatal' in l.lower()][:20]
bad = [l.strip() for l in lines_ if any(k in l.lower() for k in ('timestep too small', 'simulation(s) aborted', 'singular matrix',
       'did not converge', 'gmin stepping failed', 'source stepping failed'))][:20]
missing = [x for x in [expect] if not os.path.exists(os.path.join(raw_dir, x)) or os.path.getsize(os.path.join(raw_dir, x)) == 0]
if status == 'completed' and (bad or missing or [e for e in errors if not e.lower().startswith('error: no such vector')]):
    status = 'failed'
if len(lines_) > 2000:
    open(os.path.join(raw_dir, 'ngspice_full.log'), 'w').write(log)
    log = '\n'.join(lines_[:200] + ['... (%d lines cut; full log in the bulk run directory) ...' % (len(lines_) - 400)] + lines_[-200:]) + '\n'
open(log_path, 'w').write(log)
meas = {l.split('=')[0].strip(): l.split('=')[1].split()[0] for l in lines_ if l.strip().startswith(('idd ', 'idda ')) and '=' in l}
tsim = float(tstop.rstrip('u')) * 1e-6 if not a.op_only else 0.0
rj = {'run_id': a.id, 'block': 'r1_adc', 'harness': 'sim/post (T2 post-layout harness)', 'question': a.question,
      'command': 'G1_CPUSET=%s G1_CPUS=1 G1_WORKDIR=%s G1_RESULTS_ROOT=<G1_RESULTS_ROOT> flow/run.sh ngspice -b '
                 '<G1_RESULTS_ROOT>/r1_adc/%s/deck.cir (= sim/post/runs/%s/deck.cir with the bulk path filled in)'
                 % (a.cpu, os.path.relpath(BLOCK, REPO), a.id, a.id),
      'runner': 'sim/post/run_post.py', 'argv': [x.replace(root, '<G1_RESULTS_ROOT>') for x in sys.argv[1:]],
      'deck': 'sim/post/runs/%s/deck.cir' % a.id, 'deck_template': deck, 'core': cell, 'layout_netlist': a.netlist if lay else None,
      'ref_model': ref, 'vref_ideal_V': a.vref if ref in ('ideal', 'lay-ideal') else None, 'vref_source': vref_src,
      'base_ibias': (a.base_ibias or a.ibias) if ref == 'lay-ideal' else None, 'bgr_model': rs if ref != 'ideal' else None,
      'noise': (nz if ref in ('opt3', 'lay') else 'none'), 'ideal_bgr': a.ideal_bgr if ref == 'lay-ideal' else None, 'ref_ibias': a.ibias if ref != 'ideal' else None,
      'points_file': a.points or None, 'pwl_shift_ns': PWL_SHIFT * 1e9 if a.deck == 'points' else None,
      'corner': [a.corner, a.temp, a.vdd], 'options': opts, 'tmax': a.tmax, 'tstop': tstop if not a.op_only else None,
      'substitutions': {k: (v if k != 'RAW' else '<G1_RESULTS_ROOT>/r1_adc/%s' % a.id) for k, v in subs.items() if k not in ('PWLA', 'PWLB')},
      'tool': next((l.strip() for l in lines_ if 'ngspice-' in l and 'Circuit level' in l), R5.NGSPICE_VERSION),
      'ngspice_version': R5.NGSPICE_VERSION, 'container_image': R5.IMAGE_ID, 'pdk_commit': R5.PDK_COMMIT,
      'netlist_sha256': lib_hash, 'frozen_netlist_check': R5.frozen_check({os.path.basename(k): v for k, v in lib_hash.items() if k.startswith('schematic/')}),
      'raw_results': 'r1_adc/%s (under G1_RESULTS_ROOT)' % a.id, 'input_series_r': a.rs or None, 'started_utc': started, 'wall_s': round(wall, 1),
      'sim_us_per_wall_min': round(tsim * 1e6 / (wall / 60.0), 3) if tsim else None, 'returncode': rc, 'status': status,
      'errors': errors, 'failure_lines': bad, 'missing_outputs': missing, 'meas': meas, 'result': '',
      'disposition': a.disposition if status == 'completed' else 'failed (%s)' % status}
json.dump(rj, open(os.path.join(run_dir, 'run.json'), 'w'), indent=2)
os.makedirs(os.path.join(HERE, 'results'), exist_ok=True)
if a.deck == 'points':
    json.dump({'id': a.id, 'points': a.points, 'n_stag': 0, 'mc': 0, 'segments': [] if status != 'completed' else
               [{'run_id': a.id, 'first_slot': 0, 'slots': len(va)}], 'slots_total': len(va),
               'stopped': None if status == 'completed' else status, 'op_only': a.op_only},
              open(os.path.join(HERE, 'results', a.id + '_segments.json'), 'w'), indent=1)
print('%s %s wall %.0f s rc %s %s' % (a.id, status, wall, rc, meas))
sys.exit(0 if status == 'completed' else 1)
