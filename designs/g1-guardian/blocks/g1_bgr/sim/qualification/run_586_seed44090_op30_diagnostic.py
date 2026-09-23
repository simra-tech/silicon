#!/usr/bin/env python3
"""One bounded 30 C OP diagnostic of the frozen failed 44090 realization.

This is not a replacement Monte Carlo draw or a temperature-coefficient test.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

import numpy as np
import run_586_mc_screen as original

HERE = Path(__file__).resolve().parent
OLD = HERE / 'bgr586-screen80-b6-20260922-a/s44090'
REF = HERE / 'runs/bgr_one_draw_20260922_r1/manifest.json'
IMAGE = 'sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0'
PINNED = {'nominal.cir': '191973cc05e7be58ec7cc3ac241f6b9da8c6bc2d255f989b13151cab11c60af8',
          'pex_nominal.spice': '586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b',
          'pex_mm.spice': '7de0fc30697d1e81d40c3200a511faf0479cfd8b397bbaa3cec6dbc4fa758c61',
          '.spiceinit': '2d0942d5c44a3f8ebe1b33771ecc57c6a117889bdd2cee9174d5acd3c176785d',
          'run.log': '3eb6607a348e101332d5c407b5444c5d34f960e2d8e5f4a7df08c0a295635967'}
REQUIRED = ('cpu_budget_positive', 'quota_growth_and_reserve', 'inodes_available',
            'ram_available', 'coordinated_CPU_reservations_fit',
            'external_allocation_growth', 'external_inodes')


def realization(log, parameters):
    rows = re.findall(r'^(@[^\s]+)\s*=\s*(\S+)', log, re.M)
    assert len(rows) >= 2842 and [k for k, _ in rows[:2842]] == parameters
    assert all(np.isfinite(float(v)) for _, v in rows[:2842])
    return rows


def deck_at_30(deck):
    old = 'dc temp -40 125 5\n'
    new = 'dc temp 30 30 5\n'
    assert deck.count(old) == 1 and deck.count(new) == 0
    candidate = deck.replace(old, new)
    assert candidate.replace(new, old) == deck
    return candidate


def prepare():
    assert original.sha(Path(original.__file__)) == '582be3438387c58c4948e9e6f05772ade5ec18f17e620c0596b423ce5e1f1cf0'
    for name, digest in PINNED.items():
        assert original.sha(OLD / name) == digest, name
    manifest = json.loads(REF.read_text())
    assert manifest['status'] == 'passed harness qualification'
    parameters = manifest['parameters']
    assert len(parameters) == len(set(parameters)) == 2842
    prior = realization((OLD / 'run.log').read_text(), parameters)[:2842]
    deck = (OLD / 'nominal.cir').read_text()
    assert '.option seed=44090 gmin=1e-15 abstol=1e-14 reltol=1e-5 vntol=1e-7' in deck
    assert manifest['source_sha256'] == PINNED['pex_nominal.spice']
    pd = Path('/foss/pdks/ihp-sg13g2')
    assert (pd / 'COMMIT').read_text().strip() == manifest['runtime']['pdk_commit']
    for key, folder, pattern in [('model_sha256', 'models', '*.lib'), ('osdi_sha256', 'osdi', '*.osdi')]:
        assert manifest['runtime'][key] == {str(p.relative_to(pd)): original.sha(p)
                                           for p in sorted((pd / 'libs.tech/ngspice' / folder).glob(pattern))}
    assert subprocess.check_output(['ngspice', '--version'], universal_newlines=True) == manifest['ngspice']
    return manifest, prior, deck_at_30(deck)


def gate_ok(path):
    gate = json.loads(path.read_text())
    assert os.sched_getaffinity(0) == {0}
    assert gate['status'] == 'passed' and all(gate['checks'].get(k) is True for k in REQUIRED)
    utc = gate['utc']; stamp = utc.replace('Z', '+0000')
    if stamp[-3] == ':': stamp = stamp[:-3] + stamp[-2:]
    when = datetime.strptime(stamp, '%Y-%m-%dT%H:%M:%S.%f%z')
    assert 0 <= (datetime.now(timezone.utc) - when).total_seconds() <= 150
    assert gate['sample_seconds'] >= 30 and gate['reserve_gib'] >= 16
    assert gate['external_allocation']['reserve_gib'] >= 2
    assert 0 in gate['coordinated_allocation']['cpus']
    return original.sha(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--image-id', required=True)
    ap.add_argument('--resource-gate', type=Path)
    ap.add_argument('--prepare-only', action='store_true')
    ap.add_argument('--analyze-saved', action='store_true', help='audit completed saved run; no simulator launch')
    args = ap.parse_args()
    assert args.image_id == IMAGE
    manifest, prior, deck = prepare()
    assert args.output.is_absolute()
    assert not (args.prepare_only and args.analyze_saved)
    if args.prepare_only:
        assert not args.output.exists()
        print(json.dumps({'status': 'passed preparation; simulator not run',
                          'original_before_count': len(prior),
                          'original_deck_sha256': PINNED['nominal.cir'],
                          'diagnostic_deck_sha256': hashlib.sha256(deck.encode()).hexdigest(),
                          'analysis_delta': 'dc temp -40 125 5 -> dc temp 30 30 5; one 30 C operating point'}))
        return
    out = args.output
    if args.analyze_saved:
        assert out.is_dir() and not (out / 'saved_audit.json').exists()
        state = json.loads((out / 'run.json').read_text())
    else:
        assert not out.exists() and args.resource_gate is not None
        gate_sha = gate_ok(args.resource_gate)
        out.mkdir(parents=True)
        for name in ('pex_nominal.spice', 'pex_mm.spice', '.spiceinit'):
            shutil.copyfile(str(OLD / name), str(out / name))
        (out / 'nominal.cir').write_text(deck)
        proof = {'status': 'prepared frozen-vector 30 C OP diagnostic',
                 'image_id': IMAGE, 'source_sha256': PINNED['pex_nominal.spice'],
                 'original_input_sha256': PINNED, 'qualified_manifest_sha256': original.sha(REF),
                 'diagnostic_deck_sha256': original.sha(out / 'nominal.cir'),
                 'resource_gate_sha256': gate_sha, 'original_before_count': 2842,
                 'analysis_delta': 'only dc temp -40 125 5 -> dc temp 30 30 5',
                 'scope': '30 C OP convergence diagnostic only; not population/TC qualification'}
        (out / 'contract.json').write_text(json.dumps(proof, indent=2) + '\n')
        with (out / 'run.log').open('x') as log:
            state = original.run_bounded(['ngspice', '-b', 'nominal.cir'], log, out / 'run.json',
                                         120, cwd=out, interval_s=1)
    log = (out / 'run.log').read_text()
    observed = re.findall(r'^(@[^\s]+)\s*=\s*(\S+)', log, re.M)
    before = observed[:2842]
    before_exact = before == prior
    after = observed[2842:5684]
    after_full = len(after) == 2842 and [k for k, _ in after] == manifest['parameters']
    temp_dependent = ([{'parameter': k, 'before': v, 'after': w}
                       for (k, v), (_, w) in zip(before, after) if v != w]
                      if before_exact and after_full else None)
    data = out / 'nominal.dat'
    one_point = False
    if data.is_file():
        try:
            rows = np.loadtxt(str(data), skiprows=1, ndmin=2)
            one_point = bool(rows.shape == (1, 12) and np.isfinite(rows).all() and rows[0, 0] == 30)
        except (ValueError, OSError):
            pass
    held = all(original.sha(OLD / name) == digest for name, digest in PINNED.items())
    copied_held = all(original.sha(out / name) == PINNED[name]
                      for name in ('pex_nominal.spice', 'pex_mm.spice', '.spiceinit'))
    deck_held = original.sha(out / 'nominal.cir') == hashlib.sha256(deck.encode()).hexdigest()
    success = (state['status'] == 'completed' and state['returncode'] == 0 and
               before_exact and after_full and one_point and held and copied_held and deck_held)
    result = {'status': 'passed 30 C OP diagnostic only' if success else 'failed 30 C OP diagnostic',
              'seed': 44090, 'watchdog_s': 120, 'engine_status': state['status'],
              'engine_returncode': state['returncode'], 'wall_s': state['wall_s'],
              'before_count': len(before), 'before_exact_original2842': before_exact,
              'after_count': len(after), 'after_all2842_named': after_full,
              'temperature_dependent_parameter_differences': temp_dependent,
              'one_30C_waveform_row': one_point, 'original_inputs_held_after': held,
              'copied_models_and_initialization_held': copied_held, 'diagnostic_deck_held': deck_held,
              'last_reported_temperature_C': state.get('last_reported_sim_time_s'),
              'gmin_dynamic_starts': log.count('Starting dynamic gmin stepping'),
              'gmin_dynamic_failures': log.count('Dynamic gmin stepping failed'),
              'gmin_true_completions': log.count('True gmin stepping completed'),
              'log_sha256': original.sha(out / 'run.log'), 'contract_sha256': original.sha(out / 'contract.json'),
              'population_credit': 'not applicable', 'tc_status': 'not run',
              'saved_audit_only': args.analyze_saved,
              'original_wrapper_status': 'failed report serialization after completed engine' if args.analyze_saved else 'not applicable'}
    report = out / ('saved_audit.json' if args.analyze_saved else 'summary.json')
    assert not report.exists()
    report.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))
    raise SystemExit(0 if success else 1)


if __name__ == '__main__':
    main()
