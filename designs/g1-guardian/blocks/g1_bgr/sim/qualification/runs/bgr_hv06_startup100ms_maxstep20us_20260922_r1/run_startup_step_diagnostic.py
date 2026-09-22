#!/usr/bin/env python3
"""One declared maximum-step refinement of a retained failed startup fixture."""
import hashlib
import json
import math
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
sys.path.insert(0, str(HERE.parents[2] / 'g1_top/sim'))
from run_bounded import run_bounded

SOURCE_SHA = '586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b'
NAME = 'typ_tt_typ_27_0.1'
PDK = Path('/foss/pdks/ihp-sg13g2')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def refined_deck(original):
    before = 'tran 0.0002 0.30000000000000004 uic\n'
    after = 'tran 0.0002 0.30000000000000004 0 20u uic\n'
    assert original.count(before) == 1
    changed = original.replace(before, after)
    assert changed.replace(after, before) == original
    return changed


def main():
    old = HERE / 'runs/bgr_loop24q4_hv06_startup2_20260922_r3'
    out = HERE / 'runs/bgr_hv06_startup100ms_maxstep20us_20260922_r1'
    previous = json.loads((old / 'manifest.json').read_text())
    case = next(c for c in previous['cases'] if c['name'] == NAME)
    assert case['status'] == 'failed' and not case['timed_out']
    assert sha(old / 'pex_nominal.spice') == SOURCE_SHA
    assert sha(old / (NAME + '.cir')) == case['deck_sha256']
    assert previous['pdk_commit'] == (PDK / 'COMMIT').read_text().strip() == '84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    for key, folder, pattern in [('model_sha256', 'models', '*.lib'), ('osdi_sha256', 'osdi', '*.osdi')]:
        assert previous[key] == {str(p.relative_to(PDK)): sha(p) for p in sorted((PDK / 'libs.tech/ngspice' / folder).glob(pattern))}
    assert previous['spiceinit_sha256'] == sha(old / '.spiceinit')
    out.mkdir(exist_ok=False)
    for name in ['pex_nominal.spice', '.spiceinit']:
        shutil.copyfile(old / name, out / name)
    shutil.copyfile(__file__, out / Path(__file__).name)
    contract = HERE / 'STARTUP_STEP_DIAGNOSTIC_20260922.md'
    shutil.copyfile(contract, out / contract.name)
    (out / (NAME + '.cir')).write_text(refined_deck((old / (NAME + '.cir')).read_text()))
    record = dict(status='running', reference_run=old.name, source_sha256=SOURCE_SHA,
                  reference_manifest_sha256=sha(old / 'manifest.json'),
                  reference_deck_sha256=case['deck_sha256'], deck_sha256=sha(out / (NAME + '.cir')),
                  runner_sha256=sha(Path(__file__)), contract_sha256=sha(contract),
                  image_id=previous['image_id'], pdk_commit=previous['pdk_commit'],
                  model_sha256=previous['model_sha256'], osdi_sha256=previous['osdi_sha256'],
                  init_sha256=sha(out / '.spiceinit'), maxstep_s=20e-6, watchdog_s=300,
                  ngspice=subprocess.check_output(['ngspice', '--version'], universal_newlines=True),
                  seed_scope='not applicable: deterministic nominal model; original seed option unchanged',
                  scope='Single numerical maximum-step diagnostic. Original failed attempt retained; no tolerance/model/stimulus/source change, no automatic ladder or reliability adoption.')
    def save():
        (out / 'manifest.json').write_text(json.dumps(record, indent=2) + '\n')
    save()
    with (out / 'run.log').open('x') as log:
        state = run_bounded(['ngspice', '-b', NAME + '.cir'], log, out / 'run.json', 300,
                            cwd=out, metadata={'deck_sha256': record['deck_sha256']}, interval_s=1)
    record.update(status='failed', solver_status=state['status'], solver_returncode=state['returncode'], wall_s=state['wall_s'])
    try:
        def rows(path):
            return [list(map(float, line.split())) for line in path.read_text().splitlines()[1:] if line.strip()]
        data = rows(out / (NAME + '.dat'))
        terminal = rows(out / (NAME + '_terminals.dat'))
        log = (out / 'run.log').read_text()
        errors = re.findall(r'(?im)^.*(?:Timestep too small|analysis aborted|doAnalyses:|^Error).*$', log)
        record.update(saved_rows=len(data), first_saved_time_s=data[0][0] if data else None,
                      last_saved_time_s=data[-1][0] if data else None, numerical_errors=errors,
                      warning_lines=[line for line in log.splitlines() if 'warning' in line.lower() or 'nan' in line.lower()],
                      waveform_sha256=sha(out / (NAME + '.dat')), terminal_waveform_sha256=sha(out / (NAME + '_terminals.dat')))
        assert state['status'] == 'completed' and state['returncode'] == 0 and not errors
        assert data and len(data) == len(terminal)
        assert all(len(r) == 12 and all(map(math.isfinite, r)) for r in data)
        assert all(len(r) == len(previous['terminal_nodes']) + 1 and all(map(math.isfinite, r)) for r in terminal)
        assert [r[0] for r in data] == [r[0] for r in terminal]
        assert all(b[0] > a[0] for a, b in zip(data, data[1:]))
        assert 0 < data[0][0] <= 2e-6 and abs(data[-1][0] - .3) < 1e-9
        indices = {name: i+1 for i, name in enumerate(previous['terminal_nodes'])}
        extrema = []
        for device in previous['devices']:
            for pair in device['pairs']:
                p, n = [device['terminals'][key] for key in pair]
                values = [(r[indices[p]] if p != '0' else 0) - (r[indices[n]] if n != '0' else 0) for r in terminal]
                extrema.append(dict(instance=device['instance'], model=device['model'], pair=pair,
                                    minimum_V=min(values), maximum_V=max(values)))
        record.update(numerical_status='passed', vref_end_V=data[-1][1], iptat_end_A=data[-1][2],
                      sampled_current_peak_A=max(-r[3] for r in data), external_terminal_extrema=extrema,
                      initial_unsaved_interval_s=[0, data[0][0]],
                      startup_level_status='passed' if .9 < data[-1][1] < 1.2 and data[-1][2] > 1e-6 else 'failed',
                      hbt_vce_status='passed' if all(max(abs(r['minimum_V']), abs(r['maximum_V'])) <= 1.6 for r in extrema if r['pair'] == 'ce') else 'failed')
        if record['startup_level_status'] == record['hbt_vce_status'] == 'passed':
            record['status'] = 'passed scoped numerical/level/HBT screen'
    except (AssertionError, OSError, ValueError, IndexError) as exc:
        record['analysis_error'] = repr(exc)
    save()
    print(json.dumps({k: v for k, v in record.items() if k not in ['model_sha256', 'osdi_sha256', 'external_terminal_extrema']}, indent=2))
    raise SystemExit(0 if record['status'].startswith('passed') else 1)


if __name__ == '__main__':
    main()
