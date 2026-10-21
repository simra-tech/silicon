#!/usr/bin/env python3
"""Write run.json for the layout-{gen,drc,lvs}-<tag> run directories (host Python, standard library only).

  python3 designs/r1-joint/blocks/r1_osc/layout/write_runjson.py <tag>      (G1_RESULTS_ROOT set)

Records the command, tool versions (from the tool logs), PDK commit, input hashes and the result. DRC markers are
counted per rule from every .lyrdb in the DRC run directory; LVS status and device/net counts from the LVS outputs.
Paths are written relative to <G1_RESULTS_ROOT> or to the repository root, never as machine paths.
"""
import glob
import hashlib
import json
import os
import re
import sys
import time
import xml.etree.ElementTree as ET

TAG = sys.argv[1]
ROOT = os.environ['G1_RESULTS_ROOT']
R = os.path.join(ROOT, 'r1_osc')
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
PDK = '84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
IMAGE = 'tapeoutbench-eda:latest sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2'


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def rel(p):
    return '<G1_RESULTS_ROOT>/' + os.path.relpath(p, ROOT)


gen = os.path.join(R, 'layout-gen-' + TAG)
drc = os.path.join(R, 'layout-drc-' + TAG)
lvs = os.path.join(R, 'layout-lvs-' + TAG)
ant = os.path.join(R, 'layout-ant-' + TAG)
inputs = dict(gds_sha256=sha(os.path.join(gen, 'r1_osc.gds')), lvs_cdl_sha256=sha(os.path.join(gen, 'r1_osc_lvs.cdl')),
              generator_sha256=sha(os.path.join(HERE, 'r1_osc_layout.py')),
              netlist_of_record='designs/r1-joint/blocks/r1_osc/schematic/r1_osc.spice',
              netlist_of_record_sha256=sha(os.path.join(HERE, '..', 'schematic', 'r1_osc.spice')))
meta = json.load(open(os.path.join(gen, 'r1_osc_layout_meta.json')))
common = dict(tag=TAG, written=time.strftime('%Y-%m-%dT%H:%M:%S'), pdk_commit=PDK, container=IMAGE,
              cpuset=os.environ.get('G1_CPUSET'), inputs=inputs)

# KLayout version from the DRC/LVS logs
kv = None
for p in glob.glob(os.path.join(drc, '*.log')) + glob.glob(os.path.join(lvs, '*.log')):
    m = re.search(r'KLayout (\d+\.\d+\.\d+)', open(p, errors='replace').read())
    if m:
        kv = m.group(1)
        break

# DRC and antenna (same counting)


def drc_count(dd, what):
    counts = {}
    for p in glob.glob(os.path.join(dd, '*.lyrdb')):
        t = ET.parse(p).getroot()
        for it in t.iter('item'):
            cat = it.find('category').text.strip().strip("'")
            counts[cat] = counts.get(cat, 0) + 1
    ran = bool(glob.glob(os.path.join(dd, '*.lyrdb')))
    return counts, dict(status=('passed' if ran and not counts else ('failed' if ran else 'not run')),
                        total_markers=sum(counts.values()), markers_per_rule=counts,
                        lyrdb=[rel(p) for p in sorted(glob.glob(os.path.join(dd, '*.lyrdb')))], what=what)


counts, drc_res = drc_count(drc, 'main + sg13g2_maximal rule tables, density off')
drc_res['density'] = 'waived at block level (run with --no_density); checked at chip level after fill'
acounts, ant_res = drc_count(ant, 'PDK antenna deck (--antenna_only)')

# LVS
con = open(os.path.join(lvs, 'console.log'), errors='replace').read() if os.path.exists(os.path.join(lvs, 'console.log')) else ''
st = 'passed' if 'PASS (netlists match)' in con else ('failed' if 'FAIL' in con else 'not run')
ext = glob.glob(os.path.join(lvs, '*_extracted.cir'))
dev = {}
nets = set()
if ext:
    for line in open(ext[0]):
        if line[:1] in 'MRQCD' and not line.startswith('*'):
            f = line.split()
            model = [t for t in f if re.match(r'^(sg13_|rppd|rhigh|npn|cap_cmim|dpantenna)', t)]
            m = re.search(r' m=(\d+)', line)
            k = model[0] if model else f[0][0]
            dev.setdefault(k, [0, 0])
            dev[k][0] += 1
            dev[k][1] += int(m.group(1)) if m else 1
            nodes = f[1:5] if f[0][0] in 'MQ' else (f[1:3] if f[0][0] in 'CD' else f[1:4])
            nets.update(nodes)
lvs_res = dict(status=st, extracted_netlist=rel(ext[0]) if ext else None,
               extracted_devices_after_combination={k: v[0] for k, v in dev.items()},
               extracted_unit_count_from_m={k: v[1] for k, v in dev.items()}, extracted_nets=len(nets),
               options='--run_mode=deep (defaults: series/parallel resistor simplification on, tap extraction on)')

cmd_gen = 'G1_WORKDIR=designs/r1-joint/blocks/r1_osc/layout flow/run.sh klayout -b -r r1_osc_layout.py'
cmd_drc = ('flow/run.sh python3 $PDK_ROOT/$PDK/libs.tech/klayout/tech/drc/run_drc.py '
           '--path=/work/designs/r1-joint/blocks/r1_osc/layout/r1_osc.gds --topcell=r1_osc --run_mode=deep --no_density --run_dir=<run dir>')
cmd_lvs = ('flow/run.sh python3 $PDK_ROOT/$PDK/libs.tech/klayout/tech/lvs/run_lvs.py '
           '--layout=/work/designs/r1-joint/blocks/r1_osc/layout/r1_osc.gds '
           '--netlist=/work/designs/r1-joint/blocks/r1_osc/layout/r1_osc_lvs.cdl --topcell=r1_osc --run_mode=deep --run_dir=<run dir>')
cmd_ant = cmd_drc.replace('--no_density', '--antenna_only')
for d, q, cmd, res in ((ant, 'PDK antenna deck on r1_osc.gds: 0 markers?', cmd_ant, ant_res), (gen, 'generate r1_osc.gds and the LVS CDL', cmd_gen, dict(meta=meta)),
                       (drc, 'PDK DRC (main + maximal rule tables, density off) on r1_osc.gds: 0 markers?', cmd_drc, drc_res),
                       (lvs, 'PDK LVS r1_osc.gds vs netlist of record (+ 44 dummy MIM units): match?', cmd_lvs, lvs_res)):
    j = dict(common, run_id=os.path.basename(d), question=q, command=cmd, tools=dict(klayout=kv), result=res,
             disposition=res.get('status', 'run') if isinstance(res, dict) else 'run')
    json.dump(j, open(os.path.join(d, 'run.json'), 'w'), indent=1)
print(json.dumps(dict(drc=drc_res['status'], drc_total=drc_res['total_markers'], drc_rules=counts, ant=ant_res['status'], ant_rules=acounts, lvs=st,
                      devices=lvs_res['extracted_devices_after_combination'], nets=len(nets)), indent=1))
