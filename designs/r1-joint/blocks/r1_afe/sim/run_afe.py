#!/usr/bin/env python3
"""r1_afe simulation driver. Runs inside the pinned container (flow/run.sh), cwd = block sim/ directory.

Usage (repo root, host):
  G1_CPUSET=106-108 G1_CPUS=3 G1_WORKDIR=designs/r1-joint/blocks/r1_afe/sim \
  G1_RESULTS_ROOT=<bulk results root> flow/run.sh python3 run_afe.py <campaign> <run-id>

Each campaign expands into jobs (deck template + substitutions). Decks and raw logs are written to
$G1_RESULTS_ROOT/r1_afe/<run-id>/; parsed rows go to results/<run-id>.json and runs/<run-id>/run.json.
"""
import hashlib, json, os, re, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
BLOCK = os.path.dirname(HERE)
NETLIST = os.path.join(BLOCK, 'schematic', 'r1_afe.spice')
PDK_COMMIT_FILE = '/foss/pdks/ihp-sg13g2/COMMIT'
IMAGE_ID = 'sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2'  # verified by flow/run.sh

CORNERS = {  # name: (mos, res, cap, vdda, temp)
    'tt': ('mos_tt', 'res_typ', 'cap_typ', 3.3, 27),
    'ss': ('mos_ss', 'res_wcs', 'cap_wcs', 3.0, 125),
    'ff': ('mos_ff', 'res_bcs', 'cap_bcs', 3.6, -40),
}

def mm(c):  # mismatch sections of a corner
    mos, res, cap, v, t = CORNERS[c]
    return (mos + '_mismatch', res + '_mismatch', cap + '_mismatch', v, t)

def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()

def job(name, tmpl, corner, mismatch=False, **kw):
    mos, res, cap, v, t = mm(corner) if mismatch else CORNERS[corner]
    subs = dict(MOS=mos, RES=res, CAP=cap, VDDA=v, TEMP=t, VCMI=2.5, ACVDD=0, NMC=1, SEED=1,
                DIO={'tt': 'dio_tt', 'ss': 'dio_ss', 'ff': 'dio_ff'}[corner])
    subs.update(kw)
    return dict(name=name, template=tmpl, corner=corner, mismatch=mismatch, subs=subs)

def campaign(c):
    J = []
    if c == 'ac':
        for k in CORNERS:
            for cm in (0.5, 2.5, 2.8):
                J.append(job('ac_%s_cm%.1f' % (k, cm), 'tb_afe_ac.cir', k, VCMI=cm))
    elif c == 'ac_mc':
        for k in CORNERS:
            for part in range(2):  # 2 x 10 samples per corner, different seeds
                J.append(job('acmc_%s_p%d' % (k, part), 'tb_afe_ac.cir', k, True, NMC=10, SEED=101 + part))
    elif c == 'settle_adc':
        for k in CORNERS:
            for code in (0, 5):
                for lv, tag in ((1, 'p100'), (0.5, 'p50'), (-1, 'm100')):
                    J.append(job('settleadc_%s_x%d_%s' % (k, 2 ** code, tag), 'tb_afe_settle_adc.cir', k, CODE=code,
                                 AMP=round(lv * 0.7 / 2 ** code, 6), VCMI=2.45, CS='2.8p', VRST=0.0))
    elif c == 'revb_check':
        J.append(job('acmc_tt_p0', 'tb_afe_ac.cir', 'tt', True, NMC=10, SEED=101))
        J.append(job('noise_ss', 'tb_afe_noise.cir', 'ss'))
        J.append(job('ac_ss', 'tb_afe_ac.cir', 'ss'))
        J.append(job('tran_ss_x32', 'tb_afe_tran.cir', 'ss', CODE=5, AMP=round(0.7 / 32, 6), VCMI=2.45))
        J.append(job('noise_tt', 'tb_afe_noise.cir', 'tt'))
        J.append(job('acmc_tt_p1', 'tb_afe_ac.cir', 'tt', True, NMC=10, SEED=102))
    elif c == 'cmstab':
        for k in CORNERS:
            for code in (0, 5):
                J.append(job('tran_%s_x%d' % (k, 2 ** code), 'tb_afe_tran.cir', k, CODE=code, AMP=round(0.7 / 2 ** code, 6), VCMI=2.45))
    elif c == 'cmstab2':
        for k in ('tt', 'ss'):
            J.append(job('tran_%s_x32' % k, 'tb_afe_tran.cir', k, CODE=5, AMP=round(0.7 / 32, 6), VCMI=2.45))
        J.append(job('noise_ss', 'tb_afe_noise.cir', 'ss'))
    elif c == 'mcq':
        J.append(job('acmc_tt_q', 'tb_afe_ac.cir', 'tt', True, NMC=2, SEED=7))
    elif c == 'smoke_ac':
        J.append(job('ac_tt', 'tb_afe_ac.cir', 'tt'))
    elif c == 'tran':
        for k in CORNERS:
            for code in (0, 5):
                J.append(job('tran_%s_x%d' % (k, 2 ** code), 'tb_afe_tran.cir', k, CODE=code,
                             AMP=round(0.7 / 2 ** code, 6), VCMI=2.45))
    elif c == 'settleq':
        J.append(job('settle_tt_x1', 'tb_afe_settle.cir', 'tt', CODE=0, AMP=0.7, VCMI=2.45))
    elif c == 'noiseq':
        J.append(job('noise_tt', 'tb_afe_noise.cir', 'tt'))
        J.append(job('cm_tt', 'tb_afe_cm.cir', 'tt'))
        J.append(job('psrr_tt', 'tb_afe_psrr.cir', 'tt', ACVDD=1))
    elif c == 'quick':
        J.append(job('ac_tt', 'tb_afe_ac.cir', 'tt'))
        J.append(job('ac_ss', 'tb_afe_ac.cir', 'ss'))
        J.append(job('noise_tt', 'tb_afe_noise.cir', 'tt'))
        J.append(job('tran_ss_x32', 'tb_afe_tran.cir', 'ss', CODE=5, AMP=round(0.7 / 32, 6), VCMI=2.45))
        J.append(job('settle_ss_x1', 'tb_afe_settle.cir', 'ss', CODE=0, AMP=0.7, VCMI=2.45))
        J.append(job('ac_ff', 'tb_afe_ac.cir', 'ff'))
    elif c == 'quick2':
        for k in CORNERS:
            J.append(job('ac_%s' % k, 'tb_afe_ac.cir', k))
            J.append(job('tran_%s_x32' % k, 'tb_afe_tran.cir', k, CODE=5, AMP=round(0.7 / 32, 6), VCMI=2.45))
    elif c == 'tranq':
        for k in ('tt', 'ss'):
            J.append(job('tran_%s_x32' % k, 'tb_afe_tran.cir', k, CODE=5, AMP=round(0.7 / 32, 6), VCMI=2.45))
        J.append(job('ac_ss_cm2.5', 'tb_afe_ac.cir', 'ss', VCMI=2.5))
    elif c == 'settle':
        for k in CORNERS:
            for code in (0, 5):
                for lv, tag in ((1, 'p100'), (0.5, 'p50'), (-1, 'm100')):
                    J.append(job('settle_%s_x%d_%s' % (k, 2 ** code, tag), 'tb_afe_settle.cir', k, CODE=code,
                                 AMP=round(lv * 0.7 / 2 ** code, 6), VCMI=2.45))
    elif c == 'noise':
        for k in CORNERS:
            J.append(job('noise_%s' % k, 'tb_afe_noise.cir', k))
    elif c == 'cm':
        for k in CORNERS:
            J.append(job('cm_%s' % k, 'tb_afe_cm.cir', k))
    elif c == 'psrr':
        for k in CORNERS:
            J.append(job('psrr_%s' % k, 'tb_afe_psrr.cir', k, ACVDD=1))
        for part in range(2):
            J.append(job('psrrmc_tt_p%d' % part, 'tb_afe_psrr.cir', 'tt', True, ACVDD=1, NMC=10, SEED=201 + part))
    else:
        raise SystemExit('unknown campaign ' + c)
    return J

def render(j):
    head = open(os.path.join(HERE, 'common_head.inc')).read()
    codes = open(os.path.join(HERE, 'gain_codes.inc')).read()
    s = open(os.path.join(HERE, j['template'])).read().replace('@@HEAD@@', head).replace('@@CODES@@', codes)
    s = s.replace('../schematic/r1_afe.spice', NETLIST)
    for k, v in j['subs'].items():
        s = s.replace('@@%s@@' % k, str(v))
    left = re.findall(r'@@[A-Z0-9]+@@', s)
    if left:
        raise SystemExit('unsubstituted %s in %s' % (left, j['name']))
    return s

ROW = re.compile(r'^([A-Z]+ROW)\s+(.*)$')

THD = re.compile(r'THD:\s*([-+0-9.eE]+)\s*%')

def parse(log):
    rows = []
    for line in open(log, errors='replace'):
        t = THD.search(line)
        if t:
            rows.append({'tag': 'THDROW', 'thd_percent': float(t.group(1))})
            continue
        m = ROW.match(line.strip())
        if not m:
            continue
        d = {'tag': m.group(1)}
        for kv in m.group(2).split():
            if '=' in kv:
                k, v = kv.split('=', 1)
                try:
                    d[k] = float(v)
                except ValueError:
                    d[k] = v
        rows.append(d)
    return rows

def run_one(j, out):
    deck = os.path.join(out, j['name'] + '.cir')
    log = os.path.join(out, j['name'] + '.log')
    j['subs']['RAW'] = os.path.join(out, j['name'])
    open(deck, 'w').write(render(j))
    t0 = time.time()
    with open(log, 'w') as f:
        rc = subprocess.call(['ngspice', '-b', deck], stdout=f, stderr=subprocess.STDOUT, cwd=HERE)
    rows = parse(log)
    errs = [l.strip() for l in open(log, errors='replace') if re.search(r'(?i)error|singular|timestep too small|abort', l)][:10]
    return dict(name=j['name'], corner=j['corner'], mismatch=j['mismatch'], subs=j['subs'], rc=rc,
                seconds=round(time.time() - t0, 1), rows=rows, errors=errs,
                deck=os.path.relpath(deck, os.environ['G1_RESULTS_ROOT']),
                log=os.path.relpath(log, os.environ['G1_RESULTS_ROOT']))

def main():
    camp, rid = sys.argv[1], sys.argv[2]
    root = os.environ['G1_RESULTS_ROOT']
    out = os.path.join(root, 'r1_afe', rid)
    os.makedirs(out, exist_ok=False)
    jobs = campaign(camp)
    ncpu = int(os.environ.get('OMP_NUM_THREADS', '3'))
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=ncpu) as ex:
        res = list(ex.map(lambda j: run_one(j, out), jobs))
    ver = subprocess.check_output(['ngspice', '-v']).decode(errors='replace')
    ver = [l.strip('* ').strip() for l in ver.splitlines() if 'ngspice-' in l][:1]
    templates = sorted(set(j['template'] for j in jobs)) + ['common_head.inc', 'gain_codes.inc']
    os.makedirs(os.path.join(HERE, 'results'), exist_ok=True)
    os.makedirs(os.path.join(HERE, 'runs', rid), exist_ok=True)
    json.dump(res, open(os.path.join(HERE, 'results', rid + '.json'), 'w'), indent=1)
    runj = dict(run_id=rid, campaign=camp, date_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                command='G1_CPUSET=106-108 G1_CPUS=3 G1_WORKDIR=designs/r1-joint/blocks/r1_afe/sim '
                        'G1_RESULTS_ROOT=<bulk> flow/run.sh python3 run_afe.py %s %s' % (camp, rid),
                tools=dict(ngspice=ver[0] if ver else 'unknown', image_id=IMAGE_ID,
                           pdk_commit=open(PDK_COMMIT_FILE).read().strip()),
                inputs={**{'sim/' + t: sha(os.path.join(HERE, t)) for t in templates},
                        'schematic/r1_afe.spice': sha(NETLIST), 'sim/run_afe.py': sha(__file__)},
                raw='$G1_RESULTS_ROOT/r1_afe/%s/' % rid, jobs=len(jobs),
                failed_jobs=[r['name'] for r in res if r['rc'] != 0 or not r['rows']],
                wall_seconds=round(time.time() - t0, 1), summary='results/%s.json' % rid,
                question='', result='', disposition='')
    json.dump(runj, open(os.path.join(HERE, 'runs', rid, 'run.json'), 'w'), indent=1)
    print(json.dumps({k: runj[k] for k in ('run_id', 'jobs', 'failed_jobs', 'wall_seconds')}))

if __name__ == '__main__':
    main()
