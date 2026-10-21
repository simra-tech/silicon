#!/usr/bin/env python3
"""Write run.json for the layout-{gen,drc,ant,lvs}-<tag> run directories (host Python, standard library only).

  python3 designs/r1-joint/blocks/r1_ls/layout/write_runjson.py <tag>      (G1_RESULTS_ROOT set)

Records the command, tool versions (from the tool logs), PDK commit, input hashes and the result. DRC markers are
counted per rule from every .lyrdb in the DRC and antenna run directories; LVS status and device counts from the LVS
outputs. Paths are written relative to <G1_RESULTS_ROOT> or to the repository root, never as machine paths.
"""
import glob
import hashlib
import json
import os
import re
import sys
import time
import xml.etree.ElementTree as ET

# ---- block constants (the only lines that differ between the three T7 blocks)
BLOCK = 'r1_ls'
TOP = 'r1_ls'
GEN_FILES = ['r1_ls.gds', 'r1_ls.lef', 'r1_ls_lvs.cdl']
GENERATOR = 'r1_ls_layout.py'
NETLIST_OF_RECORD = 'schematic/g1_ls_up_copy.spice'
LVS_OPTS = '--run_mode=deep'
LVS_OPTS_NOTE = '--run_mode=deep (defaults)'
SOURCE_GDS = 'designs/g1-guardian/blocks/g1_ctrl/ls/layout/g1_ls_up.gds'

TAG = sys.argv[1]
ROOT = os.environ['G1_RESULTS_ROOT']
R = os.path.join(ROOT, BLOCK)
HERE = os.path.dirname(os.path.abspath(__file__))
BDIR = os.path.abspath(os.path.join(HERE, '..'))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
PDK = '84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
IMAGE = 'tapeoutbench-eda:latest sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2'
L = 'designs/r1-joint/blocks/%s/layout' % BLOCK


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def rel(p):
    return '<G1_RESULTS_ROOT>/' + os.path.relpath(p, ROOT)


gen, drc, ant, lvs = [os.path.join(R, 'layout-%s-%s' % (k, TAG)) for k in ('gen', 'drc', 'ant', 'lvs')]
inputs = dict(gds_sha256=sha(os.path.join(gen, GEN_FILES[0])), lvs_cdl_sha256=sha(os.path.join(gen, GEN_FILES[-1])),
              generator_sha256=sha(os.path.join(HERE, GENERATOR)),
              netlist_of_record='designs/r1-joint/blocks/%s/%s' % (BLOCK, NETLIST_OF_RECORD),
              netlist_of_record_sha256=sha(os.path.join(BDIR, NETLIST_OF_RECORD)))
if SOURCE_GDS:
    inputs['g1_source_gds'] = SOURCE_GDS
    inputs['g1_source_gds_sha256'] = sha(os.path.join(REPO, SOURCE_GDS))
common = dict(tag=TAG, written=time.strftime('%Y-%m-%dT%H:%M:%S'), pdk_commit=PDK, container=IMAGE,
              cpuset=os.environ.get('G1_CPUSET'), inputs=inputs)

kv = None
for p in glob.glob(os.path.join(drc, '*.log')) + glob.glob(os.path.join(lvs, '*.log')):
    m = re.search(r'KLayout (?:version detected: )?(\d+\.\d+\.\d+)', open(p, errors='replace').read())
    if m:
        kv = m.group(1)
        break


def drc_summary(d, nofail_note):
    counts = {}
    files = sorted(glob.glob(os.path.join(d, '*.lyrdb')))
    for p in files:
        for it in ET.parse(p).getroot().iter('item'):
            cat = it.find('category').text.strip().strip("'")
            counts[cat] = counts.get(cat, 0) + 1
    log = open(os.path.join(d, 'console.log'), errors='replace').read() if os.path.exists(os.path.join(d, 'console.log')) else ''
    ran = bool(files) or 'Passed' in log
    return dict(status=('passed' if ran and not counts else ('failed' if ran else 'not run')),
                total_markers=sum(counts.values()), markers_per_rule=counts, lyrdb=[rel(p) for p in files], note=nofail_note)


drc_res = drc_summary(drc, 'main + sg13g2_maximal rule tables; density waived at block level (--no_density)')
ant_res = drc_summary(ant, '--antenna_only')

con = open(os.path.join(lvs, 'console.log'), errors='replace').read() if os.path.exists(os.path.join(lvs, 'console.log')) else ''
st = 'passed' if 'PASS (netlists match)' in con else ('failed' if 'FAIL' in con else 'not run')
ext = glob.glob(os.path.join(lvs, '*_extracted.cir'))
dev = {}
nets = set()
if ext:
    for line in open(ext[0]):
        if line[:1] in 'MRQC' and not line.startswith('*'):
            f = line.split()
            model = [t for t in f if re.match(r'^(sg13_|rppd|rhigh|npn|cap_)', t)]
            m = re.search(r' m=(\d+)', line)
            k = model[0] if model else f[0][0]
            dev.setdefault(k, [0, 0])
            dev[k][0] += 1
            dev[k][1] += int(m.group(1)) if m else 1
            nets.update(f[1:5] if f[0][0] in 'MQ' else f[1:4])
lvs_res = dict(status=st, extracted_netlist=rel(ext[0]) if ext else None,
               extracted_devices_after_combination={k: v[0] for k, v in dev.items()},
               extracted_unit_count_from_m={k: v[1] for k, v in dev.items()}, extracted_nets=len(nets), options=LVS_OPTS_NOTE)

cmd_gen = 'sh %s/run_checks.sh %s  (generator %s, then the LVS CDL)' % (L, TAG, GENERATOR)
cmd_drc = ('flow/run.sh python3 $PDK_ROOT/$PDK/libs.tech/klayout/tech/drc/run_drc.py --path=/work/%s/%s --run_mode=deep --no_density --run_dir=<run dir>' % (L, GEN_FILES[0]))
cmd_ant = cmd_drc.replace('--no_density', '--antenna_only')
cmd_lvs = ('flow/run.sh python3 $PDK_ROOT/$PDK/libs.tech/klayout/tech/lvs/run_lvs.py --layout=/work/%s/%s --netlist=/work/%s/%s '
           '--topcell=%s %s --run_dir=<run dir>' % (L, GEN_FILES[0], L, GEN_FILES[-1], TOP, LVS_OPTS))
for d, q, cmd, res in ((gen, 'generate %s and the LVS CDL' % GEN_FILES[0], cmd_gen, dict(files=GEN_FILES)),
                       (drc, 'PDK DRC (main + maximal, density off) on %s: 0 markers?' % GEN_FILES[0], cmd_drc, drc_res),
                       (ant, 'PDK antenna check on %s: 0 markers?' % GEN_FILES[0], cmd_ant, ant_res),
                       (lvs, 'PDK LVS %s vs netlist of record (+ documented layout dummies): match?' % GEN_FILES[0], cmd_lvs, lvs_res)):
    j = dict(common, run_id=os.path.basename(d), question=q, command=cmd, tools=dict(klayout=kv), result=res,
             disposition=res.get('status', 'run'))
    json.dump(j, open(os.path.join(d, 'run.json'), 'w'), indent=1)
print(json.dumps(dict(drc=drc_res['status'], drc_total=drc_res['total_markers'], drc_rules=drc_res['markers_per_rule'],
                      ant=ant_res['status'], ant_total=ant_res['total_markers'], ant_rules=ant_res['markers_per_rule'],
                      lvs=st, devices=lvs_res['extracted_devices_after_combination'], nets=len(nets)), indent=1))
