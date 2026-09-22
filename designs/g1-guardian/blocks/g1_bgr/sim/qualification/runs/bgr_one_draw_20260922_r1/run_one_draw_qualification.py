#!/usr/bin/env python3
"""One immutable draw and four controls, never a statistical campaign."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / 'g1_top/sim'))
from run_bounded import run_bounded
from simulation_errors import solver_failure

SOURCE = '586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b'
CASES = [('enabled', 44001, True, False), ('repeat', 44001, True, False),
         ('reverse', 44001, True, True), ('disabled', 44001, False, False),
         ('disabled_seed2', 44002, False, False)]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def transform(deck, seed, enabled, reverse):
    assert deck.count('seed=42001 ') == 1 and deck.count('dc temp -40 125 5\n') == 1
    changed = deck.replace('seed=42001 ', 'seed=%d ' % seed)
    if enabled:
        for corner in ['hbt_typ', 'mos_tt', 'res_typ']:
            assert changed.count(' '+corner+'\n') == 1
            changed = changed.replace(' '+corner+'\n', ' '+corner+'_mismatch\n')
        changed = changed.replace('.include pex_nominal.spice\n', '.include pex_mm.spice\n')
    if reverse:
        changed = changed.replace('dc temp -40 125 5\n', 'dc temp 125 -40 -5\n')
    return changed


def main():
    nominal = HERE / 'runs/bgr_loop24q4_hv06_nominal_20260922_r1'
    candidate = HERE / 'candidates/bgr_loop24_qref4_r253p465_hv06'
    inventory = json.loads((candidate / 'manifest.json').read_text())
    original = nominal / 'pex_nominal.spice'
    assert sha(original) == inventory['candidate_sha256'] == SOURCE
    parameters = inventory['fingerprint_parameters']
    assert len(parameters) == len(set(parameters)) == 2842
    deck = (nominal / 'nominal.cir').read_text()
    assert re.findall(r'^print (.+)$', deck, re.M) == parameters+parameters
    runtime = json.loads((nominal / 'manifest.json').read_text())
    pd = Path('/foss/pdks/ihp-sg13g2')
    assert (pd / 'COMMIT').read_text().strip() == runtime['pdk_commit']
    for key, folder, pattern in [('model_sha256', 'models', '*.lib'), ('osdi_sha256', 'osdi', '*.osdi')]:
        assert runtime[key] == {str(p.relative_to(pd)): sha(p) for p in sorted((pd / 'libs.tech/ngspice' / folder).glob(pattern))}
    text = original.read_text()
    mismatch = '\n'.join(s+' mm_ok=1' if s.startswith(('XM', 'XQ', 'XR')) else s for s in text.splitlines())+'\n'
    assert mismatch.replace(' mm_ok=1\n', '\n') == text
    out = HERE / 'runs/bgr_one_draw_20260922_r1'
    out.mkdir(exist_ok=False)
    contract = HERE / 'ONE_DRAW_QUALIFICATION_20260922.md'
    for p in [Path(__file__), contract, candidate / 'manifest.json']:
        shutil.copyfile(p, out / ('candidate_manifest.json' if p.name == 'manifest.json' else p.name))
    result = dict(status='running', source_sha256=SOURCE, parameters=parameters,
                  runner_sha256=sha(Path(__file__)), contract_sha256=sha(contract),
                  nominal_manifest_sha256=sha(nominal / 'manifest.json'),
                  nominal_deck_sha256=sha(nominal / 'nominal.cir'),
                  nominal_wave_sha256=sha(nominal / 'nominal.dat'),
                  init_sha256=sha(nominal / '.spiceinit'),
                  runtime={k: runtime[k] for k in ['image_id', 'pdk_commit', 'model_sha256', 'osdi_sha256']},
                  ngspice=subprocess.check_output(['ngspice', '--version'], universal_newlines=True),
                  cases=[], distinct_enabled_draws=1, population_yield='not run')
    def save():
        (out / 'manifest.json').write_text(json.dumps(result, indent=2)+'\n')
    save()
    arrays = []
    for name, seed, enabled, reverse in CASES:
        leaf = out / name
        leaf.mkdir()
        shutil.copyfile(nominal / '.spiceinit', leaf / '.spiceinit')
        shutil.copyfile(original, leaf / 'pex_nominal.spice')
        (leaf / 'pex_mm.spice').write_text(mismatch)
        (leaf / 'nominal.cir').write_text(transform(deck, seed, enabled, reverse))
        with (leaf / 'run.log').open('x') as log:
            state = run_bounded(['ngspice', '-b', 'nominal.cir'], log, leaf / 'run.json', 120, cwd=leaf, interval_s=1)
        log = (leaf / 'run.log').read_text()
        record = dict(name=name, seed=seed, mismatch=enabled, reverse=reverse,
                      status='failed', runtime_state=state, deck_sha256=sha(leaf / 'nominal.cir'),
                      warning_lines=[s for s in log.splitlines() if 'warning' in s.lower() or 'nan' in s.lower()],
                      solver_failure=solver_failure(log))
        try:
            assert state['status'] == 'completed' and state['returncode'] == 0 and not record['solver_failure']
            observed = re.findall(r'^(@[^\s]+)\s*=\s*(\S+)', log, re.M)
            assert [p[0] for p in observed] == parameters+parameters
            assert all(np.isfinite(float(p[1])) for p in observed)
            before, after = observed[:2842], observed[2842:]
            assert before == after
            d = np.loadtxt(str(leaf / 'nominal.dat'), skiprows=1)
            assert d.shape == (34, 12) and np.isfinite(d).all()
            assert np.array_equal(d[:, 0], np.arange(125, -41, -5) if reverse else np.arange(-40, 126, 5))
            if reverse:
                d = d[::-1]
            tc = float(np.ptp(d[:, 1])/d[13, 1]/165*1e6)
            record.update(status='passed', parameters_before=before, parameters_after=after,
                          waveform_sha256=sha(leaf / 'nominal.dat'), tc_ppm_C=tc,
                          tc_status='passed' if tc <= 50 else 'failed')
            arrays.append(d)
        except (AssertionError, ValueError, OSError, IndexError) as exc:
            record['analysis_error'] = repr(exc)
        result['cases'].append(record)
        save()
        if record['status'] != 'passed':
            result.update(status='failed; sequence stopped', not_run=[c[0] for c in CASES[len(result['cases']):]])
            save()
            raise SystemExit(1)
    a, b, r, off1, off2 = result['cases']
    diff = np.max(abs(arrays[0]-arrays[2]), axis=0)
    bounds = np.array([0, 1e-6, 1e-9, 1e-9]+[1e-6]*8)
    checks = dict(same_draw_parameters=a['parameters_before'] == b['parameters_before'] == r['parameters_before'],
                  repeat_full_wave_bytes=a['waveform_sha256'] == b['waveform_sha256'],
                  disabled_parameters=off1['parameters_before'] == off2['parameters_before'],
                  disabled_full_wave_bytes=off1['waveform_sha256'] == off2['waveform_sha256'] == result['nominal_wave_sha256'],
                  reverse_prospective_consistency=bool(np.all(diff <= bounds)))
    result.update(status='passed harness qualification' if all(checks.values()) else 'failed harness qualification',
                  checks=checks, reverse_exact_numeric_equality=bool(np.array_equal(arrays[0], arrays[2])),
                  reverse_max_differences=diff.tolist(), reverse_bounds=bounds.tolist(),
                  one_draw_tc_status=a['tc_status'], one_draw_tc_ppm_C=a['tc_ppm_C'])
    save()
    print(json.dumps({k: v for k, v in result.items() if k not in ['runtime', 'cases', 'parameters']}, indent=2))
    raise SystemExit(0 if all(checks.values()) else 1)


if __name__ == '__main__':
    main()
