#!/usr/bin/env python3
"""Focused original/normalized reference comparison with unchanged stock LVS."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import pya

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'designs/g1-guardian/blocks/g1_top/sim'))
from run_bounded import run_bounded

PDK = Path('/foss/pdks/ihp-sg13g2')
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--references', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
p.add_argument('--cell', choices=['sg13g2_Filler400', 'sg13g2_LevelUpInv', 'sg13g2_RCClampInverter'], required=True)
a = p.parse_args()
assert pya.__version__ == '0.30.9'
assert (PDK / 'COMMIT').read_text().strip() == '84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
assert len(os.sched_getaffinity(0)) == 1
gds = ROOT / 'designs/g1-guardian/blocks/g1_padring/layout/g1_chip_top.gds'
assert sha(gds) == '38c1d6d13bbfee4ed0e3c01477742c3d2d28317d9215d9e5bd9a35551285ae59'
a.output.mkdir(parents=True, exist_ok=False)
out = a.output.resolve()
shutil.copyfile(__file__, out / 'runner.py')
results = []
for variant in ('original', 'normalized'):
    reference = (a.references / (a.cell + '_' + variant + '.cdl')).resolve()
    leaf = out / variant
    leaf.mkdir()
    cmd = ['python3', str(PDK / 'libs.tech/klayout/tech/lvs/run_lvs.py'),
           '--layout', str(gds), '--netlist', str(reference), '--topcell', a.cell,
           '--run_mode', 'deep', '--run_dir', str(leaf / 'lvs'), '--top_lvl_pins', '--spice_comments']
    with (leaf / 'console.log').open('x') as stream:
        state = run_bounded(cmd, stream, leaf / 'run.json', 300, cwd=ROOT,
                            env=dict(os.environ, KLAYOUT_PATH=str(PDK / 'libs.tech/klayout')),
                            metadata={'layout_sha256': sha(gds), 'reference_sha256': sha(reference),
                                      'variant': variant, 'cell': a.cell}, interval_s=1)
    log = (leaf / 'console.log').read_text()
    explicit_pass = 'Comparison mode: PASS (netlists match).' in log
    result = {'variant': variant, 'status': 'passed' if state['status'] == 'completed' and explicit_pass else 'failed',
              'watchdog_status': state['status'], 'returncode': state['returncode'],
              'wall_s': state['wall_s'], 'explicit_comparison_pass': explicit_pass}
    if state['status'] in ('timeout', 'interrupted', 'launch_failed'):
        result['status'] = 'not run'
    results.append(result)
    (out / 'summary.json').write_text(json.dumps(results, indent=2) + '\n')
    for db in (leaf / 'lvs').glob('*.lvsdb'):
        xref = ROOT / 'designs/g1-guardian/blocks/g1_padring/flow/lvs/xref_summary.py'
        with (leaf / 'xref.txt').open('x') as stream:
            run_bounded(['klayout', '-b', '-rd', 'db=' + str(db), '-r', str(xref)],
                        stream, leaf / 'xref_run.json', 60, cwd=ROOT, interval_s=1)
    print(json.dumps(result), flush=True)
