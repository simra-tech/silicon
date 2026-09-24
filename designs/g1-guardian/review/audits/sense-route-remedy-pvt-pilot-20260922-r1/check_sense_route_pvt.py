#!/usr/bin/env python3
"""Frozen108-tuple baseline SENSE grid with exact-candidate nominal routeR sensitivity."""
import argparse
import hashlib
import itertools
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from sense_route_manifest import load_candidate_resistances

ROOT = Path(__file__).resolve().parents[4]
SENSE = ROOT / 'designs/g1-guardian/blocks/g1_sense/sim'
BASE = SENSE / 'qualification/corners-20260921-a'
sys.path.insert(0, str(ROOT / 'designs/g1-guardian/blocks/g1_top/sim'))
from run_bounded import run_bounded

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--manifest', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
p.add_argument('--tuple', help='Single frozen tuple for a runtime pilot')
p.add_argument('--shard', type=int, default=0)
p.add_argument('--shards', type=int, default=1)
a = p.parse_args()
assert len(os.sched_getaffinity(0)) == 1
assert 0 <= a.shard < a.shards
manifest, resistances = load_candidate_resistances(a.manifest)
assert Path('/foss/pdks/ihp-sg13g2/COMMIT').read_text().strip() == '84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
baseline = {row['name']: row for row in json.loads((BASE / 'summary.json').read_text())}
assert len(baseline) == 108 and all(row['status'] == 'passed' for row in baseline.values())
expected_corners = set(itertools.product(('tt', 'ss', 'ff'), ('typ', 'bcs', 'wcs'), (3.0, 3.3, 3.6), (-40, 27, 85, 125)))
assert {tuple(row['corner']) for row in baseline.values()} == expected_corners
names = sorted(baseline)
if a.tuple:
    assert a.tuple in names
    names = [a.tuple]
else:
    names = names[a.shard::a.shards]
a.output.mkdir(parents=True, exist_ok=False); out = a.output.resolve()
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
for path in (Path(__file__), Path(__file__).with_name('sense_route_manifest.py'), BASE / 'sense_substrate_tied.spice'):
    shutil.copyfile(path, out / path.name)
shutil.copyfile(a.manifest, out / 'candidate_manifest.json')
provenance = {'scope': 'Baseline schematic SENSE frozen108MOS/resistor/supply/temp tuples; idealVREF/PTAT/rails, no pads/BGR. Candidate geometryR is nominal at all corners; scale2 sensitivity not metal-process/temp bound. No resized SENSE candidate substitution.',
              'candidate_sha256': manifest['candidate_sha256'], 'R_P_ohm': resistances['P'], 'R_N_ohm': resistances['N'],
              'planned_tuples': names, 'shard': a.shard, 'shards': a.shards,
              'gain_limits_V_per_V': [19.9, 20.1], 'route_scales': [0, 1, 2],
              'source_netlist_sha256': sha(BASE / 'sense_substrate_tied.spice'), 'baseline_summary_sha256': sha(BASE / 'summary.json'),
              'source_deck_sha256': {name: sha(BASE / (name + '.cir')) for name in names},
              'ngspice_version': subprocess.check_output(['ngspice', '--version'], text=True)}
(out / 'provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
results = []
for name in names:
    for scale in (0, 1, 2):
        leaf = out / name / ('r' + str(scale)); leaf.mkdir(parents=True)
        shutil.copyfile(SENSE / '.spiceinit', leaf / '.spiceinit')
        deck = (BASE / (name + '.cir')).read_text().replace('.include qualification/corners-20260921-a/sense_substrate_tied.spice', '.include ../../sense_substrate_tied.spice')
        route = 'Vrp shp corep 0\nVrn cm coren 0' if scale == 0 else f'Rrp shp corep {resistances["P"]*scale:.12g}\nRrn cm coren {resistances["N"]*scale:.12g}'
        assert deck.count('XDUT shp cm vref') == 1
        deck = deck.replace('XDUT shp cm vref', route + '\nXDUT corep coren vref')
        deck = deck.replace('$&i(vdd)', '$&i(vdd) $&v(shp) $&v(cm) $&v(corep) $&v(coren)')
        (leaf / 'fixture.cir').write_text(deck)
        with (leaf / 'tool.log').open('x') as stream:
            state = run_bounded(['ngspice', '-b', 'fixture.cir'], stream, leaf / 'run.json', 120,
                                cwd=leaf, env=dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1'),
                                metadata={'deck_sha256': sha(leaf / 'fixture.cir'), 'corner': baseline[name]['corner'], 'R_scale': scale}, interval_s=1)
        log = (leaf / 'tool.log').read_text(); rows = {}; duplicates = []
        for line in log.splitlines():
            if line.startswith('ROW '):
                tokens = line.split(); key = tokens[1]; values = list(map(float, tokens[2:]))
                if key in rows: duplicates.append(key)
                rows[key] = values
        errors = [line for line in log.splitlines() if re.search(r'(?i)(^Error|fatal|timestep too small|doAnalyses:)', line)]
        complete = (state['status'] == 'completed' and state['returncode'] == 0 and not errors and not duplicates
                    and set(rows) == set(baseline[name]['rows']) and 'QUALIFICATION_END' in log
                    and all(len(values) == 11 and all(map(math.isfinite, values)) for values in rows.values()))
        record = {'name': name, 'corner': baseline[name]['corner'], 'scale': scale,
                  'status': 'passed' if complete else ('not run' if state['status'] in ('timeout', 'interrupted', 'launch_failed') else 'failed'),
                  'watchdog_status': state['status'], 'returncode': state['returncode'], 'wall_s': state['wall_s'],
                  'rows': rows, 'errors': errors, 'duplicate_rows': duplicates}
        if complete:
            gains = []; offsets = []
            for cm in (-0.1, 0, 0.3):
                zero = rows[f't0_c{cm}_s0'][0]; full = rows[f't0_c{cm}_s0.05'][0]
                gains.append((full-zero)/0.05)
                offsets.append({'true_cm_V': cm, 'zero_shunt_output_V': zero, 'input_referred_zero_error_from_ideal_pedestal_V': (zero-1.000755)/20})
            record.update(gain_min=min(gains), gain_max=max(gains), gain_status='passed' if min(gains)>=19.9 and max(gains)<=20.1 else 'failed', offsets=offsets)
            if scale == 0:
                deltas = [max(abs(rows[key][column]-baseline[name]['rows'][key][column]) for key in rows) for column in range(7)]
                record['baseline_printed_vector_max_abs_delta_by_column'] = deltas
                record['baseline_printed_vectors_exact'] = all(delta == 0 for delta in deltas)
        results.append(record)
        (out / 'summary.json').write_text(json.dumps(results, indent=2) + '\n')
        print(name, scale, record['status'], record.get('gain_status', 'not run'), round(state['wall_s'], 3), flush=True)
        if len(results) >= 3 and all(row['status'] != 'passed' for row in results[-3:]):
            raise RuntimeError('Three consecutive numerical/incomplete failures; stopping bounded batch')
assert len(results) == len(names)*3
