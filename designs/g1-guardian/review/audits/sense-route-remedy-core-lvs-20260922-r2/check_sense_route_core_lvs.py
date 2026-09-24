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
p.add_argument('--candidate-route-labels', action='store_true', help='Use exact candidate manifest instead of stale DEF for changed P/N route label locations')
p.add_argument('--prior-core-view', type=Path, help='Retained core view for independent nontext XOR and exact CDL parity')
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
shutil.copyfile(BLOCK / 'flow/lvs/core_only_gds.py', out / 'core_only_gds.py')
env = dict(os.environ, KLAYOUT_PATH=str(PDK / 'libs.tech/klayout'))
if a.candidate_route_labels:
    env['G1_CORE_ROUTE_MANIFEST'] = str(a.manifest.resolve())
runview = out / 'candidate_run'
for suffix, target in [('gds/g1_chip_top.gds', candidate),
                       ('def/g1_chip_top.def', BLOCK / 'flow/runs/assembly-1350/final/def/g1_chip_top.def')]:
    link = runview / 'final' / suffix
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(target)
cmd = ['bash', str(BLOCK / 'flow/lvs/run_core_lvs.sh'), str(runview), str(out / 'core')]
with (out / 'console.log').open('x') as stream:
    state = run_bounded(cmd, stream, out / 'run.json', 1800, cwd=ROOT,
                        env=env,
                        metadata={'candidate_sha256': manifest['candidate_sha256'],
                                  'scope': 'Existing core-only LVS procedure; excludes IO and sealring'},
                        interval_s=1)
passed = state['status'] == 'completed' and state['returncode'] == 0 and 'Comparison mode: PASS (netlists match).' in (out / 'console.log').read_text()
view_parity = None
if a.prior_core_view:
    prior = pya.Layout(); prior.read(str(a.prior_core_view / 'g1_core.gds'))
    current = pya.Layout(); current.read(str(out / 'core/g1_core.gds'))
    assert prior.dbu == current.dbu
    layers = {(ly.get_info(li).layer, ly.get_info(li).datatype) for ly in (prior, current) for li in ly.layer_indexes()}
    differences = []
    for layer in sorted(layers):
        first = pya.Region(prior.cell('g1_core').begin_shapes_rec(prior.layer(*layer)))
        second = pya.Region(current.cell('g1_core').begin_shapes_rec(current.layer(*layer)))
        delta = (first ^ second).merged()
        if not delta.is_empty():
            differences.append({'layer': layer, 'xor_area_um2': delta.area() * current.dbu**2})
    reference_sha = hashlib.sha256((out / 'core/g1_core.cdl').read_bytes()).hexdigest()
    old_reference_sha = hashlib.sha256((a.prior_core_view / 'g1_core.cdl').read_bytes()).hexdigest()
    view_parity = {'nontext_layer_differences': differences, 'reference_sha256': reference_sha,
                   'prior_reference_sha256': old_reference_sha,
                   'status': 'passed' if not differences and reference_sha == old_reference_sha else 'failed'}
    passed = passed and view_parity['status'] == 'passed'
result = {'status': 'passed' if passed else 'failed', 'watchdog_status': state['status'],
          'returncode': state['returncode'], 'wall_s': state['wall_s'],
          'candidate_sha256': manifest['candidate_sha256'], 'full_io_status': 'not run'}
result['candidate_route_labels'] = a.candidate_route_labels
result['prior_core_view_parity'] = view_parity
if state['status'] in ('timeout', 'interrupted', 'launch_failed'):
    result['status'] = 'not run'
assert hashlib.sha256(candidate.read_bytes()).hexdigest() == manifest['candidate_sha256']
(out / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result), flush=True)
sys.exit(0 if passed else 1)
