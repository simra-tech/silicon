#!/usr/bin/env python3
"""SENSE route-C sensitivity with the declared25mohm shunt and explicit lead assumptions."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import numpy as np
from sense_route_manifest import load_candidate_resistances

ROOT = Path(__file__).resolve().parents[4]
SENSE = ROOT / 'designs/g1-guardian/blocks/g1_sense/sim'
sys.path.insert(0, str(ROOT / 'designs/g1-guardian/blocks/g1_top/sim'))
from run_bounded import run_bounded
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--manifest', type=Path, required=True)
p.add_argument('--local-capacitance', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
manifest, resistances = load_candidate_resistances(a.manifest)
assert len(os.sched_getaffinity(0)) == 1
assert Path('/foss/pdks/ihp-sg13g2/COMMIT').read_text().strip() == '84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
base = SENSE / 'qualification/corners-20260921-a/tt_typ_3.3V_27C.cir'
net = base.parent / 'sense_substrate_tied.spice'
a.output.mkdir(parents=True, exist_ok=False); out = a.output.resolve()
for path in (Path(__file__), Path(__file__).with_name('sense_route_manifest.py'), net):
    shutil.copyfile(path, out / path.name)
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
local = json.loads(a.local_capacitance.read_text())['results']['actual_fill']['modes']['floating']
ground = {row['net']: row['ground_C_fF_estimate'] for row in manifest['routes']}
models = {'R_only': [0, 0, 0], 'local_clip_C': [local['P_ground_equivalent_fF'], local['N_ground_equivalent_fF'], local['mutual_fF']],
          'whole_route_C_estimate': [ground['P'], ground['N'], 0]}
provenance = {'scope': 'Simulated TT27C3.3V baseline schematic SENSE, ideal VREF/PTAT and rails.25mohm physical-shunt fixture at1A, idealKelvin leads for0ohm;1/10ohm eachlead diagnostic assumptions, not specifiedboardimpedance or bounds. Lumpedmidpoint routeRC; localclip C is not fullrouteC, whole-routegroundC is LEFestimate without coupling. No pads/package/actualBGR/PVT/fullPEX qualification.',
              'candidate_sha256': manifest['candidate_sha256'], 'models_fF_P_N_mutual': models,
              'inputs_sha256': {str(path.relative_to(ROOT)): sha(path) for path in (base, net, a.manifest.resolve(), a.local_capacitance.resolve())},
              'ngspice_version': subprocess.check_output(['ngspice', '--version'], text=True)}
(out / 'provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
rows = []
for lead in (0, 1, 10):
    for mode, (cp, cn, cm) in models.items():
        leaf = out / f'lead{lead}_{mode}'; leaf.mkdir(); shutil.copyfile(SENSE / '.spiceinit', leaf / '.spiceinit')
        deck = base.read_text().split('.control', 1)[0].replace('.include qualification/corners-20260921-a/sense_substrate_tied.spice', '.include ../sense_substrate_tied.spice')
        deck = deck.replace('Vcm cm 0 dc 0', 'Vcm cm 0 dc -0.0125 ac 0').replace('Vsh shp cm dc 0', 'Ish cm shuntp dc 1 ac 40\nRsh shuntp cm 0.025')
        elements = []
        for branch, start in [('P', 'shuntp'), ('N', 'cm')]:
            elements.append(f'Rlead{branch} {start} lead{branch} {lead}' if lead else f'Vlead{branch} {start} lead{branch} 0')
            half = resistances[branch] / 2
            elements += [f'Rroute{branch}a lead{branch} mid{branch} {half:.17g}', f'Rroute{branch}b mid{branch} core{branch} {half:.17g}']
        for name, first, second, value in [('P', 'midP', '0', cp), ('N', 'midN', '0', cn), ('PN', 'midP', 'midN', cm)]:
            if value:
                elements.append(f'Croute{name} {first} {second} {value:.17g}f')
        deck = deck.replace('XDUT shp cm vref', '\n'.join(elements) + '\nXDUT coreP coreN vref')
        deck += '''.control
set numdgt=17
set num_threads=1
set wr_singlescale
set wr_vecnames
alter Iib dc=4.13e-6
op
echo OP $&v(isense) $&v(coreP) $&v(coreN)
ac dec 40 1k 100meg
let hre=real(v(isense))
let him=imag(v(isense))
wrdata differential.dat hre him
alter @Ish[acmag]=0
alter @Vcm[acmag]=1
ac dec 40 1k 100meg
let hre=real(v(isense))
let him=imag(v(isense))
wrdata common_mode.dat hre him
echo ROUTE_AC_COMPLETE
quit 0
.endc
.end
'''
        (leaf / 'fixture.cir').write_text(deck)
        with (leaf / 'tool.log').open('x') as stream:
            state = run_bounded(['ngspice', '-b', 'fixture.cir'], stream, leaf / 'run.json', 90,
                                cwd=leaf, env=dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1'),
                                metadata={'deck_sha256': sha(leaf / 'fixture.cir')}, interval_s=1)
        log = (leaf / 'tool.log').read_text()
        errors = [line for line in log.splitlines() if re.search(r'(?i)(^Error|fatal|timestep too small|doAnalyses:)', line)]
        record = {'lead_ohm_each': lead, 'mode': mode, 'watchdog_status': state['status'], 'wall_s': state['wall_s'], 'errors': errors,
                  'status': 'passed' if state['returncode'] == 0 and 'ROUTE_AC_COMPLETE' in log and not errors else 'failed'}
        if record['status'] == 'passed':
            for drive in ('differential', 'common_mode'):
                values = np.loadtxt(leaf / (drive + '.dat'), skiprows=1)
                assert values.shape == (201, 3) and np.isfinite(values).all(), values.shape
                assert np.all(np.diff(values[:, 0]) > 0)
                record[drive] = {'frequency_Hz': values[:, 0].tolist(), 'real_V_per_V': values[:, 1].tolist(), 'imag_V_per_V': values[:, 2].tolist()}
        rows.append(record)
        (out / 'summary.json').write_text(json.dumps(rows, indent=2) + '\n')
        print(lead, mode, record['status'], flush=True)
        if record['status'] != 'passed':
            sys.exit(1)
comparisons = []
for row in rows:
    baseline = next(item for item in rows if item['lead_ohm_each'] == row['lead_ohm_each'] and item['mode'] == 'R_only')
    result = {'lead_ohm_each': row['lead_ohm_each'], 'mode': row['mode']}
    for drive in ('differential', 'common_mode'):
        f = np.array(row[drive]['frequency_Hz'])
        h = np.array(row[drive]['real_V_per_V']) + 1j*np.array(row[drive]['imag_V_per_V'])
        control = np.array(baseline[drive]['real_V_per_V']) + 1j*np.array(baseline[drive]['imag_V_per_V'])
        mask = f <= 10e6
        result[drive] = {'gain_magnitude_at_1kHz': float(abs(h[0])), 'max_complex_delta_through_10MHz_V_per_V': float(np.max(abs(h[mask]-control[mask]))),
                         'max_relative_complex_delta_through_10MHz': float(np.max(abs((h[mask]-control[mask])/control[mask]))),
                         'sampled_magnitudes_V_per_V': {str(target): float(abs(h[np.argmin(abs(f-target))])) for target in (1e3, 1e6, 2e6, 10e6, 100e6)}}
        if drive == 'differential':
            below = np.where(abs(h) < abs(h[0])/np.sqrt(2))[0]
            result['first_sample_below_3dB_Hz'] = None if not len(below) else float(f[below[0]])
    comparisons.append(result)
(out / 'comparisons.json').write_text(json.dumps(comparisons, indent=2) + '\n')
