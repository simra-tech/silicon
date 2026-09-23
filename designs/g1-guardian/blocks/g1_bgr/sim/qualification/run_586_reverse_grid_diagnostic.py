#!/usr/bin/env python3
"""Exact-seed reverse-temperature BGR586 diagnostic; no population credit."""
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
REF = HERE / 'runs/bgr_one_draw_20260922_r1/manifest.json'
IMAGE = 'sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0'
SOURCE = '586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b'
SHARED = {'pex_nominal.spice': SOURCE,
          'pex_mm.spice': '7de0fc30697d1e81d40c3200a511faf0479cfd8b397bbaa3cec6dbc4fa758c61',
          '.spiceinit': '2d0942d5c44a3f8ebe1b33771ecc57c6a117889bdd2cee9174d5acd3c176785d'}
CASES = {
    44090: ('bgr586-screen80-b6-20260922-a/s44090',
            {'nominal.cir': '191973cc05e7be58ec7cc3ac241f6b9da8c6bc2d255f989b13151cab11c60af8',
             'run.log': '3eb6607a348e101332d5c407b5444c5d34f960e2d8e5f4a7df08c0a295635967'}),
    44089: ('bgr586-screen80-b5-20260922-a/s44089',
            {'nominal.cir': 'f8b7749673916d29b2748799e0a9231dcb89b633b1866798efe0768d312789ee',
             'run.log': '199362448fbe5e8089fa94d6ce0719c3de4b30d2f0ee7a280d5ebe9cb42047fc',
             'nominal.dat': '09a3a66c098b459dc9876b4d94560f9a6b2e437439c4e22734ddc02b5620f620'})}
REQUIRED = ('cpu_budget_positive', 'quota_growth_and_reserve', 'inodes_available',
            'ram_available', 'coordinated_CPU_reservations_fit',
            'external_allocation_growth', 'external_inodes')


def deck_reverse(deck):
    before, after = 'dc temp -40 125 5\n', 'dc temp 125 -40 -5\n'
    assert deck.count(before) == 1 and deck.count(after) == 0
    result = deck.replace(before, after)
    assert result.replace(after, before) == deck
    return result


def parse_parameters(log):
    return re.findall(r'^(@[^\s]+)\s*=\s*(\S+)', log, re.M)


def preflight(seed):
    relative, expected = CASES[seed]
    old = HERE / relative
    for name, digest in dict(SHARED, **expected).items():
        assert original.sha(old / name) == digest, name
    assert original.sha(Path(original.__file__)) == '582be3438387c58c4948e9e6f05772ade5ec18f17e620c0596b423ce5e1f1cf0'
    manifest = json.loads(REF.read_text())
    assert manifest['status'] == 'passed harness qualification' and manifest['source_sha256'] == SOURCE
    names = manifest['parameters']
    assert len(names) == len(set(names)) == 2842
    old_pairs = parse_parameters((old / 'run.log').read_text())
    assert len(old_pairs) >= 2842 and [k for k, _ in old_pairs[:2842]] == names
    assert all(np.isfinite(float(v)) for _, v in old_pairs[:2842])
    if seed == 44089:
        assert len(old_pairs) == 5684 and old_pairs[:2842] == old_pairs[2842:]
    deck = (old / 'nominal.cir').read_text()
    assert '.option seed=%s gmin=1e-15 abstol=1e-14 reltol=1e-5 vntol=1e-7' % seed in deck
    pd = Path('/foss/pdks/ihp-sg13g2')
    assert (pd / 'COMMIT').read_text().strip() == manifest['runtime']['pdk_commit']
    for key, folder, pattern in [('model_sha256', 'models', '*.lib'), ('osdi_sha256', 'osdi', '*.osdi')]:
        assert manifest['runtime'][key] == {str(p.relative_to(pd)): original.sha(p)
                                           for p in sorted((pd / 'libs.tech/ngspice' / folder).glob(pattern))}
    assert subprocess.check_output(['ngspice', '--version'], universal_newlines=True) == manifest['ngspice']
    return old, expected, manifest, old_pairs[:2842], deck_reverse(deck)


def gate_ok(path):
    gate = json.loads(path.read_text())
    assert os.sched_getaffinity(0) == {0}
    assert gate['status'] == 'passed' and all(gate['checks'].get(k) is True for k in REQUIRED)
    stamp = gate['utc'].replace('Z', '+0000')
    if stamp[-3] == ':': stamp = stamp[:-3] + stamp[-2:]
    when = datetime.strptime(stamp, '%Y-%m-%dT%H:%M:%S.%f%z')
    assert 0 <= (datetime.now(timezone.utc) - when).total_seconds() <= 150
    assert gate['sample_seconds'] >= 30 and gate['reserve_gib'] >= 16
    assert gate['external_allocation']['reserve_gib'] >= 2
    assert 0 in gate['coordinated_allocation']['cpus']
    return original.sha(path)


def finite_wave(path):
    if not path.is_file(): return None
    try:
        array = np.loadtxt(str(path), skiprows=1, ndmin=2)
        return array if array.shape == (34, 12) and np.isfinite(array).all() else None
    except (ValueError, OSError): return None


def compare_rows(a, b):
    assert a.shape == b.shape
    delta = np.abs(a - b)
    return {'bit_exact': bool(np.array_equal(a, b)),
            'different_cells': int(np.count_nonzero(a != b)),
            'max_abs_by_column': [float(v) for v in np.max(delta, axis=0)]}


def audit(out, seed, old, expected, manifest, before, deck, state, saved_only):
    log = (out / 'run.log').read_text()
    pairs = parse_parameters(log)
    new_before, new_after = pairs[:2842], pairs[2842:5684]
    before_exact = new_before == before
    after_exact = len(new_after) == 2842 and new_after == before
    wave = finite_wave(out / 'nominal.dat')
    reverse_grid = np.arange(125, -41, -5)
    full_grid = wave is not None and bool(np.array_equal(wave[:, 0], reverse_grid))
    aligned = wave[::-1] if full_grid else None
    comparison = None
    if aligned is not None:
        if seed == 44089:
            forward = finite_wave(old / 'nominal.dat')
            assert forward is not None and np.array_equal(forward[:, 0], np.arange(-40, 126, 5))
            comparison = compare_rows(aligned, forward)
        else:
            op = Path(os.environ['G1_RESULTS_ROOT']) / 'bgr586-s44090-op30-diagnostic-20260923-r1'
            assert original.sha(op / 'saved_audit.json') == '4f76c6a3a9bd2043715cce11ff52b9b73cd26b4f98b92a19870b761f099e077e'
            assert original.sha(op / 'nominal.dat') == '78761b899640da47a76396b721da9400d234ae4332c5730f7413712bfc8be882'
            point = np.loadtxt(str(op / 'nominal.dat'), skiprows=1, ndmin=2)
            comparison = compare_rows(aligned[14:15], point)
    original_held = all(original.sha(old / name) == digest for name, digest in dict(SHARED, **expected).items())
    copied_held = all(original.sha(out / name) == digest for name, digest in SHARED.items())
    deck_held = original.sha(out / 'nominal.cir') == hashlib.sha256(deck.encode()).hexdigest()
    numeric = (state['status'] == 'completed' and state['returncode'] == 0 and
               before_exact and after_exact and full_grid and original_held and copied_held and deck_held)
    tc = float(np.ptp(aligned[:, 1]) / aligned[13, 1] / 165 * 1e6) if numeric else None
    result = {'status': 'passed reverse-grid numerical diagnostic only' if numeric else 'failed reverse-grid numerical diagnostic',
              'seed': seed, 'watchdog_s': 120, 'engine_status': state['status'],
              'engine_returncode': state['returncode'], 'wall_s': state['wall_s'],
              'original_before_count': len(before), 'reverse_before_count': len(new_before),
              'reverse_after_count': len(new_after), 'all2842_before_exact': before_exact,
              'all2842_after_exact': after_exact, 'finite34_reverse_grid': full_grid,
              'original_inputs_held': original_held, 'copied_source_and_init_held': copied_held,
              'one_line_deck_change_only': deck_held,
              'comparison': comparison, 'diagnostic_tc_ppm_C_original_formula': tc,
              'diagnostic_tc_under_50ppm': bool(tc <= 50) if tc is not None else None,
              'gmin_dynamic_starts': log.count('Starting dynamic gmin stepping'),
              'gmin_dynamic_failures': log.count('Dynamic gmin stepping failed'),
              'gmin_true_completions': log.count('True gmin stepping completed'),
              'model_vmax_warning_count': log.count('voltage is greater than specified by vmax'),
              'temperature_limiting_nan_count': log.count('temperature limiting function received NaN'),
              'log_sha256': original.sha(out / 'run.log'),
              'wave_sha256': original.sha(out / 'nominal.dat') if (out / 'nominal.dat').is_file() else None,
              'contract_sha256': original.sha(out / 'contract.json'),
              'saved_audit_only': saved_only,
              'original_population_status': 'unchanged: 44090 failed original sweep; 44089 original forward passed',
              'population_credit': 'not applicable', 'tc_qualification': 'not run'}
    report = out / ('saved_audit.json' if saved_only else 'summary.json')
    assert not report.exists()
    report.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))
    return numeric


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seed', type=int, choices=sorted(CASES), required=True)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--image-id', required=True)
    ap.add_argument('--resource-gate', type=Path)
    ap.add_argument('--prepare-only', action='store_true')
    ap.add_argument('--analyze-saved', action='store_true')
    args = ap.parse_args()
    assert args.image_id == IMAGE and args.output.is_absolute()
    assert not (args.prepare_only and args.analyze_saved)
    old, expected, manifest, before, deck = preflight(args.seed)
    out = args.output
    if args.prepare_only:
        assert not out.exists()
        print(json.dumps({'status': 'passed preparation; simulator not run', 'seed': args.seed,
                          'all2842_original_before_bound': True,
                          'original_deck_sha256': expected['nominal.cir'],
                          'reverse_deck_sha256': hashlib.sha256(deck.encode()).hexdigest(),
                          'analysis_delta': 'dc temp -40 125 5 -> dc temp 125 -40 -5'}))
        return
    if args.analyze_saved:
        assert out.is_dir()
        state = json.loads((out / 'run.json').read_text())
    else:
        assert not out.exists() and args.resource_gate is not None
        gate_sha = gate_ok(args.resource_gate)
        out.mkdir(parents=True)
        for name in SHARED: shutil.copyfile(str(old / name), str(out / name))
        (out / 'nominal.cir').write_text(deck)
        contract = {'status': 'prepared exact-seed reverse-grid diagnostic', 'seed': args.seed,
                    'image_id': IMAGE, 'qualified_manifest_sha256': original.sha(REF),
                    'original_input_sha256': dict(SHARED, **expected),
                    'reverse_deck_sha256': original.sha(out / 'nominal.cir'),
                    'resource_gate_sha256': gate_sha,
                    'analysis_delta': 'only dc temp -40 125 5 -> dc temp 125 -40 -5',
                    'scope': 'direction-method diagnostic only; original population unchanged'}
        (out / 'contract.json').write_text(json.dumps(contract, indent=2) + '\n')
        with (out / 'run.log').open('x') as stream:
            state = original.run_bounded(['ngspice', '-b', 'nominal.cir'], stream,
                                         out / 'run.json', 120, cwd=out, interval_s=1)
    success = audit(out, args.seed, old, expected, manifest, before, deck, state, args.analyze_saved)
    raise SystemExit(0 if success else 1)


if __name__ == '__main__': main()
