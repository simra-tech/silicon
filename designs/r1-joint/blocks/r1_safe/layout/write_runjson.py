#!/usr/bin/env python3
"""Write run.json for the r1_safe layout-{gen,drc,ant,lvs,lvsx}-<tag> run directories (host Python, stdlib only).

  python3 designs/r1-joint/blocks/r1_safe/layout/write_runjson.py <tag>      (G1_RESULTS_ROOT set)

Records the command, KLayout version (from the tool logs), PDK commit, input hashes and the result. DRC markers are
counted per rule from every .lyrdb; LVS outcome from the console log, device and net counts from the extracted
netlist. Paths are relative to <G1_RESULTS_ROOT> or to the repository root.
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
R = os.path.join(ROOT, 'r1_safe')
HERE = os.path.dirname(os.path.abspath(__file__))
PDK = '84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
IMAGE = 'tapeoutbench-eda:latest sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2'


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def rel(p):
    return '<G1_RESULTS_ROOT>/' + os.path.relpath(p, ROOT)


D = {k: os.path.join(R, 'layout-%s-%s' % (k, TAG)) for k in ('gen', 'drc', 'ant', 'lvs', 'lvsx')}
gen = D['gen']
inputs = dict(gds_sha256=sha(os.path.join(gen, 'r1_safe.gds')), lvs_cdl_sha256=sha(os.path.join(gen, 'r1_safe_lvs.cdl')),
              generator_sha256={f: sha(os.path.join(HERE, f)) for f in
                                ('r1_safe_layout.py', 'r1_safe_parts.py', 'r1_safe_lib.py', 'r1_safe_cmp_cell.py',
                                 'make_cdl.py')},
              netlist_of_record='designs/r1-joint/blocks/r1_safe/schematic/r1_safe.spice',
              netlist_of_record_sha256=sha(os.path.join(HERE, '..', 'schematic', 'r1_safe.spice')))
meta = json.load(open(os.path.join(gen, 'r1_safe_layout_meta.json')))
common = dict(tag=TAG, written=time.strftime('%Y-%m-%dT%H:%M:%S'), pdk_commit=PDK, container=IMAGE,
              cpuset=os.environ.get('G1_CPUSET'), inputs=inputs)
kv = None
for p in glob.glob(os.path.join(R, 'layout-*-' + TAG, '**', '*.log'), recursive=True):
    m = re.search(r'KLayout (\d+\.\d+\.\d+)', open(p, errors='replace').read())
    if m:
        kv = m.group(1)
        break


def drc_res(d, note):
    counts = {}
    dbs = sorted(glob.glob(os.path.join(d, '*.lyrdb')))
    for p in dbs:
        for it in ET.parse(p).getroot().iter('item'):
            cat = it.find('category').text.strip().strip("'")
            counts[cat] = counts.get(cat, 0) + 1
    return dict(status='passed' if dbs and not counts else ('failed' if dbs else 'not run'),
                total_markers=sum(counts.values()), markers_per_rule=counts, lyrdb=[rel(p) for p in dbs], note=note)


def lvs_res(d, sub, con):
    c = open(con, errors='replace').read() if os.path.exists(con) else ''
    crash = 'Signal number: 11' in c
    st = 'passed' if 'PASS (netlists match)' in c else ('failed' if ('FAIL' in c or crash) else 'not run')
    ext = glob.glob(os.path.join(d, sub, '*_extracted.cir'))
    dev, nets = {}, set()
    if ext:
        for line in open(ext[0]):
            if line[:1] in 'MRQC':
                f = line.split()
                model = [t for t in f if re.match(r'^(sg13_|rppd|rhigh|npn)', t)]
                k = model[0] if model else f[0][0]
                dev[k] = dev.get(k, 0) + 1
                nets.update(f[1:5] if f[0][0] in 'MQ' else f[1:4])
    return dict(status=st, tool_crash_signal_11=crash, extracted_netlist=rel(ext[0]) if ext else None,
                extracted_devices_top_level_lines=dev, note='device/net totals of the comparison are in the README')


pins = open(os.path.join(gen, 'pin_check.log')).read() if os.path.exists(os.path.join(gen, 'pin_check.log')) else ''
res = {
    'gen': ('generate r1_safe.gds, LEF, LVS CDL; pin check (LEF pins = CDL ports)',
            'G1_WORKDIR=designs/r1-joint/blocks/r1_safe/layout flow/run.sh klayout -b -r r1_safe_layout.py '
            '-rd out=<run dir> -rd cmp=1; python3 make_cdl.py <run dir>/r1_safe_lvs.cdl; python3 check_pins.py',
            dict(meta=meta, pin_check='passed' if 'pins equal CDL ports' in pins else 'failed', status='run')),
    'drc': ('PDK DRC main + maximal (density off) on r1_safe.gds: 0 markers?',
            'flow/run.sh python3 $PDK_ROOT/$PDK/libs.tech/klayout/tech/drc/run_drc.py --path=<gds> --run_mode=deep '
            '--no_density --run_dir=<run dir>',
            drc_res(D['drc'], 'density waived at block level; checked at chip level after fill')),
    'ant': ('PDK antenna rules on r1_safe.gds: 0 markers?',
            'flow/run.sh python3 $PDK_ROOT/$PDK/libs.tech/klayout/tech/drc/run_drc.py --path=<gds> --run_mode=deep '
            '--antenna_only --run_dir=<run dir>', drc_res(D['ant'], '')),
    'lvs': ('PDK LVS (stock deck) r1_safe.gds vs netlist of record: match?',
            'flow/run.sh python3 $PDK_ROOT/$PDK/libs.tech/klayout/tech/lvs/run_lvs.py --layout=<gds> --netlist=<cdl> '
            '--topcell=r1_safe --run_mode=deep --run_dir=<run dir>',
            lvs_res(D['lvs'], '', os.path.join(D['lvs'], 'console.log'))),
    'lvsx': ('PDK LVS with comparer search limits max_depth(8), max_branch_complexity(100) (diagnostic deck copy): '
             'match?', 'see run_checks.sh (copy of the PDK lvs directory, two lines added after align)',
             lvs_res(D['lvsx'], 'out', os.path.join(D['lvsx'], 'console.log'))),
}
for k, (q, cmd, r) in res.items():
    j = dict(common, run_id=os.path.basename(D[k]), question=q, command=cmd, tools=dict(klayout=kv), result=r,
             disposition=r.get('status'))
    json.dump(j, open(os.path.join(D[k], 'run.json'), 'w'), indent=1)
print(json.dumps({k: dict(status=v[2].get('status'), markers=v[2].get('total_markers'),
                          markers_per_rule=v[2].get('markers_per_rule')) for k, v in res.items()}, indent=1))
