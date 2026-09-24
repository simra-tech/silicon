#!/usr/bin/env python3
"""Bounded transverse-context clip ladder; not whole-route extraction convergence."""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys
from sense_route_manifest import load_candidate_resistances

ROOT = Path(__file__).resolve().parents[4]
AUDIT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'designs/g1-guardian/blocks/g1_top/sim'))
from run_bounded import run_bounded

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--manifest', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
assert len(os.sched_getaffinity(0)) == 1
manifest, _ = load_candidate_resistances(a.manifest)
a.output.mkdir(parents=True, exist_ok=False)
out = a.output.resolve()
shutil.copyfile(__file__, out / 'runner.py')
rows = []
for width in (24, 48):
    leaf = out / ('width' + str(width))
    leaf.mkdir()
    commands = [
        ['prepare_fill_clip.py', '--output', str(leaf / 'clip'), '--gds', str((a.manifest.parent / 'g1_chip_top.gds').resolve()), '--route-manifest', str(a.manifest.resolve()), '--box', str(1022-width/2), '468', str(1022+width/2), '488'],
        ['run_fill_clip_pex.py', '--clip', str(leaf / 'clip'), '--output', str(leaf / 'pex')],
        ['analyze_fill_clip.py', '--input', str(leaf / 'pex'), '--output', str(leaf / 'analysis')],
        ['check_fill_clip_ac.py', str(leaf / 'analysis')],
    ]
    record = {'width_um': width, 'status': 'not run', 'steps': []}
    rows.append(record)
    for number, command in enumerate(commands):
        with (leaf / f'step{number}.log').open('x') as stream:
            state = run_bounded([sys.executable, str(AUDIT / command[0]), *command[1:]], stream,
                                leaf / f'step{number}.json', 600 if number == 1 else 120,
                                cwd=ROOT, interval_s=1)
        record['steps'].append({'step': command[0], 'status': state['status'], 'returncode': state['returncode'], 'wall_s': state['wall_s']})
        if state['returncode'] != 0:
            record['status'] = 'failed' if state['status'] == 'failed' else 'not run'
            break
    else:
        record['status'] = 'passed'
        record['reduction'] = json.loads((leaf / 'analysis/summary.json').read_text())
    (out / 'summary.json').write_text(json.dumps({'candidate_sha256': manifest['candidate_sha256'],
        'scope': 'Transverse-context sensitivity at fixed20um signal length. Extra conductors grounded as explicit diagnostic boundary conditions; not actual-net inference, longitudinal convergence or full route PEX.', 'rows': rows}, indent=2) + '\n')
    print(width, record['status'], flush=True)
    if record['status'] != 'passed':
        break
sys.exit(0 if len(rows) == 2 and all(row['status'] == 'passed' for row in rows) else 1)
