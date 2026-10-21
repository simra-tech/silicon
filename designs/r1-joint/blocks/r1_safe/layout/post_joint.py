#!/usr/bin/env python3
"""Pre- and post-layout runs of the r1_safe joint deck (sim/gen_tb_safe_joint3.py, path fixture, code 44, k = 32).
Host Python; ngspice runs in the pinned container through flow/run.sh. Run from the repository root:

  G1_CPUSET=116-119; export G1_CPUSET; G1_RESULTS_ROOT=<G1_RESULTS_ROOT>; export G1_RESULTS_ROOT
  python3 designs/r1-joint/blocks/r1_safe/layout/post_joint.py <run id> <comparator PEX netlist> [corners]

Variants per corner: 'pre' = r1_safe_cmp of the netlist of record; 'post' = the four comparators replaced by the
extracted comparator (layout/pex_cmp.py, subckt renamed r1_safe_cmp_pex). Everything else is the same deck.
r1_isense: the committed netlist (git HEAD) is copied into the run directory and included from there, so the run does
not depend on the working tree of the r1_isense track. Analysis: sim/analyze_joint3.py (centre error against the
ideal 70.1 mV shunt-referred threshold, delays from the shunt step). Writes <run dir>/{pre,post}/..., run.json.
"""
import hashlib
import json
import os
import subprocess
import sys
import time

RUN, PEX = sys.argv[1], sys.argv[2]
CORNERS = (sys.argv[3] if len(sys.argv) > 3 else 'tt,ss_cold').split(',')
ROOT = os.environ['G1_RESULTS_ROOT']
REPO = subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], universal_newlines=True).strip()
BLK = 'designs/r1-joint/blocks/r1_safe'
RD = os.path.join(ROOT, 'r1_safe', RUN)
os.makedirs(RD, exist_ok=False)
CORN = {'tt': dict(mos='mos_tt', res='res_typ', cap='cap_typ', temp=27, vdd=1.2, vdda=3.3),
        'ss_cold': dict(mos='mos_ss', res='res_wcs', cap='cap_wcs', temp=-40, vdd=1.08, vdda=3.0),
        'ff_hot': dict(mos='mos_ff', res='res_bcs', cap='cap_bcs', temp=125, vdd=1.32, vdda=3.6)}


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


# pinned r1_isense netlist (HEAD) and the extracted comparator
isense = os.path.join(RD, 'r1_isense_HEAD.spice')
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], universal_newlines=True).strip()
open(isense, 'w').write(subprocess.check_output(
    ['git', 'show', 'HEAD:designs/r1-joint/blocks/r1_isense/schematic/r1_isense.spice'], universal_newlines=True))
pex = os.path.join(RD, 'r1_safe_cmp_pex.spice')
open(pex, 'w').write(open(PEX).read().replace('.subckt r1_safe_cmp ', '.subckt r1_safe_cmp_pex '))
# base deck from the block generator
base = os.path.join(RD, 'tb_safe_joint3_base.cir')
env = dict(os.environ, R1_THR='44', R1_CREF='0', R1_OUT=base)
subprocess.check_call(['python3', os.path.join(REPO, BLK, 'sim', 'gen_tb_safe_joint3.py')], env=env)
B = open(base).read()
B = B.replace('.include /work/designs/r1-joint/blocks/r1_isense/schematic/r1_isense.spice', '.include ' + isense)
assert '.include ' + isense in B
jobs = []
for var in ('pre', 'post'):
    os.makedirs(os.path.join(RD, var), exist_ok=True)
    for c in CORNERS:
        k = CORN[c]
        d = B
        if var == 'post':
            d = d.replace(' r1_safe_cmp\n', ' r1_safe_cmp_pex\n')
            d = d.replace('.include /work/designs/r1-joint/blocks/r1_safe/schematic/r1_safe.spice',
                          '.include /work/designs/r1-joint/blocks/r1_safe/schematic/r1_safe.spice\n.include ' + pex)
            assert d.count('r1_safe_cmp_pex\n') == 4
        for a, b in (('@@MOS@@', k['mos']), ('@@RES@@', k['res']), ('@@CAP@@', k['cap']), ('@@TEMP@@', str(k['temp'])),
                     ('@@VDDA@@', str(k['vdda'])), ('@@VDD@@', str(k['vdd'])),
                     ('@@OUT@@', os.path.join(RD, var, c))):
            d = d.replace(a, b)
        p = os.path.join(RD, var, 'tb_%s.cir' % c)
        open(p, 'w').write(d)
        jobs.append((var, c, p))
t0 = time.time()
procs = []
for var, c, p in jobs:
    lg = open(p[:-4] + '.log', 'w')
    envj = dict(os.environ, G1_CPUS='1', G1_WORKDIR=BLK + '/sim')     # sim/.spiceinit loads the PSP/OSDI models
    procs.append((var, c, p, subprocess.Popen(['flow/run.sh', 'ngspice', '-b', p], cwd=REPO, stdout=lg,
                                              stderr=subprocess.STDOUT, env=envj), time.time()))
info = {}
for var, c, p, pr, ts in procs:
    rc = pr.wait()
    info['%s_%s' % (var, c)] = dict(rc=rc, wall_s=round(time.time() - ts, 1), deck_sha256=sha(p))
summ = {}
for var in ('pre', 'post'):
    subprocess.call(['python3', os.path.join(REPO, BLK, 'sim', 'analyze_joint3.py'), os.path.join(RD, var),
                     os.path.join(RD, var)])
    sp = os.path.join(RD, var, 'summary.json')
    summ[var] = json.load(open(sp)) if os.path.exists(sp) else None
ng = ''
for var, c, p, pr, ts in procs:
    t = open(p[:-4] + '.log', errors='replace').read()
    if 'ngspice-' in t:
        ng = t[t.index('ngspice-'):].split()[0]
        break
run = dict(run_id=RUN, date_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), git_head=head,
           cpuset=os.environ.get('G1_CPUSET'), pdk_commit='84374023ee8b4b126bebbba67fcbada0a9c0ff0b',
           container='tapeoutbench-eda:latest (checked by flow/run.sh)', tools=dict(ngspice=ng),
           question='Post-layout (extracted comparator RC) vs pre-layout on the same joint deck: code-44 shunt-referred '
                    'threshold centre (schematic 70.1 mV, within 0.05 LSB?) and OC trip delay at 10 % overdrive',
           command='python3 %s/layout/post_joint.py %s <comparator PEX netlist> %s' % (BLK, RUN, ','.join(CORNERS)),
           inputs=dict(netlist_of_record=BLK + '/schematic/r1_safe.spice',
                       netlist_of_record_sha256=sha(os.path.join(REPO, BLK, 'schematic', 'r1_safe.spice')),
                       r1_isense_HEAD_sha256=sha(isense), comparator_pex_sha256=sha(pex),
                       generator=BLK + '/sim/gen_tb_safe_joint3.py'),
           corners={c: CORN[c] for c in CORNERS}, jobs=info, result=summ)
json.dump(run, open(os.path.join(RD, 'run.json'), 'w'), indent=1)
print(json.dumps(info, indent=1))
