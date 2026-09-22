#!/usr/bin/env python3
"""Two frozen source-only nominal load controls; no sweep or retry options."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / 'g1_top/sim'))
from run_bounded import run_bounded
from simulation_errors import solver_failure

PDK = Path('/foss/pdks/ihp-sg13g2')
BASE = '72417e072003d2ce28a108c47ef6ac86927ce6c6f89f3a614f360165a31c9d77'
CAND = '586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def analyze(path):
    d = np.loadtxt(str(path), skiprows=1)
    assert d.ndim == 2 and d.shape[1] == 12 and np.isfinite(d).all()
    t = d[:, 0]
    assert t[0] == 0 and np.all(np.diff(t) > 0) and abs(t[-1]-40e-6) < 1e-15
    before = d[(t >= 4e-6) & (t <= 4.9e-6)]
    plateau = d[(t >= 19e-6) & (t <= 19.9e-6)]
    returned = d[t >= 35e-6]
    assert min(len(before), len(plateau), len(returned)) > 10
    pre = before[:, 1:3].mean(axis=0)
    load = plateau[:, 1:3].mean(axis=0)
    residual = np.max(abs(returned[:, 1:3]-pre), axis=0)
    checks = dict(endpoint_level=.9 < d[-1, 1] < 1.2 and d[-1, 2] > 1e-6,
                  vref_return_1mV=residual[0] <= .001,
                  iptat_return_0p1percent=residual[1]/abs(pre[1]) <= .001)
    return dict(status='passed' if all(checks.values()) else 'failed',
                checks={k: bool(v) for k, v in checks.items()}, rows=len(d),
                first_saved_s=float(t[0]), last_saved_s=float(t[-1]),
                pre_load_mean_V_A=pre.tolist(), loaded_mean_V_A=load.tolist(),
                final_V_A=d[-1, 1:3].tolist(), final5us_max_return_error_V_A=residual.tolist(),
                sampled_min_V_A=d[:, 1:3].min(axis=0).tolist(),
                sampled_max_V_A=d[:, 1:3].max(axis=0).tolist(),
                sampled_supply_peak_A=float(max(-d[:, 3])),
                finite_step_V_per_A=float((load[0]-pre[0])/100e-9),
                full_wave_sha256=sha(path))


def main():
    old = HERE / 'runs/bgr_stress3_20260921_01'
    startup = HERE / 'runs/bgr_loop24q4_hv06_startup2_20260922_r3'
    candidate = HERE / 'candidates/bgr_loop24_qref4_r253p465_hv06/bgr_loop24_qref4_r253p465_hv06.spice'
    prior = json.loads((old / 'manifest.json').read_text())
    runtime = json.loads((startup / 'manifest.json').read_text())
    assert sha(old / 'pex_nominal.spice') == BASE and sha(candidate) == CAND
    assert sha(old / 'load.cir') == next(c['deck_sha256'] for c in prior['cases'] if c['name'] == 'load')
    assert (PDK / 'COMMIT').read_text().strip() == runtime['pdk_commit']
    assert sha(startup / '.spiceinit') == runtime['spiceinit_sha256']
    for key, folder, pattern in [('model_sha256', 'models', '*.lib'), ('osdi_sha256', 'osdi', '*.osdi')]:
        assert runtime[key] == {str(p.relative_to(PDK)): sha(p) for p in sorted((PDK / 'libs.tech/ngspice' / folder).glob(pattern))}
    out = HERE / 'runs/bgr_matched_load_20260922_r1'
    out.mkdir(exist_ok=False)
    contract = HERE / 'MATCHED_LOAD_CONTROL_20260922.md'
    for p in [Path(__file__), contract]:
        shutil.copyfile(p, out / p.name)
    record = dict(status='running', source_hashes=dict(baseline=BASE, candidate=CAND),
                  deck_sha256=sha(old / 'load.cir'), init_sha256=sha(startup / '.spiceinit'),
                  runner_sha256=sha(Path(__file__)), contract_sha256=sha(contract),
                  runtime={k: runtime[k] for k in ['image_id', 'pdk_commit', 'model_sha256', 'osdi_sha256']},
                  ngspice=subprocess.check_output(['ngspice', '--version'], universal_newlines=True),
                  watchdog_s_per_leaf=300, seed_scope='not applicable: mismatch disabled', cases=[])
    def save():
        (out / 'manifest.json').write_text(json.dumps(record, indent=2)+'\n')
    save()
    for label, source in [('baseline', old / 'pex_nominal.spice'), ('candidate', candidate)]:
        leaf = out / label
        leaf.mkdir()
        for p, name in [(source, 'pex_nominal.spice'), (old / 'load.cir', 'load.cir'), (startup / '.spiceinit', '.spiceinit')]:
            shutil.copyfile(p, leaf / name)
        assert sha(leaf / 'pex_nominal.spice') == record['source_hashes'][label]
        assert sha(leaf / 'load.cir') == record['deck_sha256']
        with (leaf / 'run.log').open('x') as log:
            state = run_bounded(['ngspice', '-b', 'load.cir'], log, leaf / 'run.json', 300, cwd=leaf, interval_s=1)
        text = (leaf / 'run.log').read_text()
        result = dict(name=label, status='failed', runtime_state=state,
                      warning_lines=[s for s in text.splitlines() if 'warning' in s.lower() or 'nan' in s.lower()],
                      solver_failure=solver_failure(text))
        try:
            assert state['status'] == 'completed' and state['returncode'] == 0 and not result['solver_failure']
            result['analysis'] = analyze(leaf / 'load.dat')
            result['status'] = result['analysis']['status']
        except (OSError, AssertionError, ValueError, IndexError) as exc:
            result['analysis_error'] = repr(exc)
        record['cases'].append(result)
        save()
        if result['status'] != 'passed':
            record.update(status='failed; sequence stopped', unstarted='candidate not run' if label == 'baseline' else 'not applicable')
            save()
            raise SystemExit(1)
    record['status'] = 'passed scoped numerical and diagnostic-return checks'
    save()
    print(json.dumps({k: v for k, v in record.items() if k != 'runtime'}, indent=2))


if __name__ == '__main__':
    main()
