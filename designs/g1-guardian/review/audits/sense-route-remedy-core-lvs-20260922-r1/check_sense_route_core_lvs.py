#!/usr/bin/env python3
"""Bounded exact-candidate core LVS using the existing independent core reference."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import pya
from sense_route_manifest import load_candidate_resistances

ROOT = Path(__file__).resolve().parents[4]
BLOCK = ROOT / 'designs/g1-guardian/blocks/g1_padring'
PDK = Path('/foss/pdks/ihp-sg13g2')
sys.path.insert(0, str(ROOT / 'designs/g1-guardian/blocks/g1_top/sim'))
from run_bounded import run_bounded

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--manifest', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
assert pya.__version__ == '0.30.9'
assert len(os.sched_getaffinity(0)) == 1
assert (PDK / 'COMMIT').read_text().strip() == '84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
manifest, _ = load_candidate_resistances(a.manifest)
candidate = (a.manifest.parent / 'g1_chip_top.gds').resolve()
a.output.mkdir(parents=True, exist_ok=False)
out = a.output.resolve()
for source in (Path(__file__), Path(__file__).with_name('sense_route_manifest.py')):
    shutil.copyfile(source, out / source.name)
shutil.copyfile(a.manifest, out / 'candidate_manifest.json')
runview = out / 'candidate_run'
for suffix, target in [('gds/g1_chip_top.gds', candidate),
                       ('def/g1_chip_top.def', BLOCK / 'flow/runs/assembly-1350/final/def/g1_chip_top.def')]:
    link = runview / 'final' / suffix
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(target)
cmd = ['bash', str(BLOCK / 'flow/lvs/run_core_lvs.sh'), str(runview), str(out / 'core')]
with (out / 'console.log').open('x') as stream:
    state = run_bounded(cmd, stream, out / 'run.json', 1800, cwd=ROOT,
                        env=dict(os.environ, KLAYOUT_PATH=str(PDK / 'libs.tech/klayout')),
                        metadata={'candidate_sha256': manifest['candidate_sha256'],
                                  'scope': 'Existing core-only LVS procedure; excludes IO and sealring'},
                        interval_s=1)
passed = state['status'] == 'completed' and state['returncode'] == 0 and 'Comparison mode: PASS (netlists match).' in (out / 'console.log').read_text()
result = {'status': 'passed' if passed else 'failed', 'watchdog_status': state['status'],
          'returncode': state['returncode'], 'wall_s': state['wall_s'],
          'candidate_sha256': manifest['candidate_sha256'], 'full_io_status': 'not run'}
if state['status'] in ('timeout', 'interrupted', 'launch_failed'):
    result['status'] = 'not run'
assert hashlib.sha256(candidate.read_bytes()).hexdigest() == manifest['candidate_sha256']
(out / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result), flush=True)
sys.exit(0 if passed else 1)
