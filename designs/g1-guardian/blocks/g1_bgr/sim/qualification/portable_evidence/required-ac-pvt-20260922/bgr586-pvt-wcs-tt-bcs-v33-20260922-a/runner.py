#!/usr/bin/env python3
"""One independent process/supply sweep of unchanged586 and full2842 inventory."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
sys.path.insert(0, str(HERE.parents[2]/'g1_trip/sim'))
from result_directory import allocate_run
from run_nominal_clock_probe import run_bounded
from analyze_bgr_substitution_outcomes import warning_inventory


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def transform(deck, hbt, mos, res, vdd):
    changes = [('/cornerHBT.lib hbt_typ\n', '/cornerHBT.lib hbt_'+hbt+'\n'),
               ('/cornerMOShv.lib mos_tt\n', '/cornerMOShv.lib mos_'+mos+'\n'),
               ('/cornerRES.lib res_typ\n', '/cornerRES.lib res_'+res+'\n'),
               ('Vdd vdd 0 3.3\n', 'Vdd vdd 0 '+str(vdd)+'\n')]
    result = deck
    for old, new in changes:
        assert result.count(old) == 1
        result = result.replace(old, new)
    reverse = result
    for old, new in reversed(changes):
        assert reverse.count(new) == 1
        reverse = reverse.replace(new, old)
    assert reverse == deck
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run-id', required=True)
    p.add_argument('--image-id', required=True)
    p.add_argument('--hbt', choices=['typ', 'bcs', 'wcs'], required=True)
    p.add_argument('--mos', choices=['tt', 'ff', 'ss'], required=True)
    p.add_argument('--res', choices=['typ', 'bcs', 'wcs'], required=True)
    p.add_argument('--vdd', type=float, choices=[3.0, 3.3, 3.6], required=True)
    a = p.parse_args()
    ref = HERE/'runs/bgr_one_draw_20260922_r1'
    qualified = json.loads((ref/'manifest.json').read_text())
    leaf = ref/'disabled'
    original = (leaf/'nominal.cir').read_text()
    assert qualified['status'] == 'passed harness qualification'
    source = leaf/'pex_nominal.spice'
    assert sha(source) == qualified['source_sha256'] == '586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b'
    previous = [row for row in qualified['cases'] if row['name'] == 'disabled']
    assert len(previous) == 1 and previous[0]['status'] == 'passed' and previous[0]['deck_sha256'] == sha(leaf/'nominal.cir')
    parameters = qualified['parameters']
    assert len(parameters) == len(set(parameters)) == 2842
    assert (a.hbt, a.mos, a.res, a.vdd) != ('typ', 'tt', 'typ', 3.3), 'Reuse qualified nominal literally'
    pd = Path('/foss/pdks/ihp-sg13g2')
    assert (pd/'COMMIT').read_text().strip() == qualified['runtime']['pdk_commit']
    assert a.image_id == 'sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0'
    for key, folder, pattern in [('model_sha256', 'models', '*.lib'), ('osdi_sha256', 'osdi', '*.osdi')]:
        assert qualified['runtime'][key] == {str(f.relative_to(pd)): sha(f) for f in sorted((pd/'libs.tech/ngspice'/folder).glob(pattern))}
    assert subprocess.check_output(['ngspice', '--version'], universal_newlines=True) == qualified['ngspice']
    deck = transform(original, a.hbt, a.mos, a.res, a.vdd)
    out = allocate_run(HERE.parent, a.run_id, relative_parent='qualification/runs')
    for name in ['pex_nominal.spice', '.spiceinit']:
        shutil.copyfile(str(leaf/name), str(out/name))
    shutil.copyfile(str(Path(__file__)), str(out/'runner.py'))
    (out/'nominal.cir').write_text(deck)
    provenance = {'arguments': sys.argv[1:], 'runner_sha256': sha(Path(__file__)), 'image_manifest': a.image_id,
                  'runtime': qualified['runtime'], 'ngspice': qualified['ngspice'], 'source_sha256': sha(source),
                  'reference_run': str(ref.relative_to(ROOT)), 'reference_manifest_sha256': sha(ref/'manifest.json'),
                  'reference_deck_sha256': sha(leaf/'nominal.cir'), 'deck_sha256': sha(out/'nominal.cir'),
                  'declared_changes': {'hbt': a.hbt, 'mos': a.mos, 'res': a.res, 'vdd_V': a.vdd},
                  'parameter_order': parameters, 'mismatch_enabled': False,
                  'scope': 'Unchanged586 source/seed44001, mismatchdisabled; qualified34point-40..125C DC deck except threeprocesssections/supply. All2842beforeafter exact within each condition, no crossprocess equality claim. Historical TC<=50ppm/C retained. Standalone1pF/ideal1VIPTAT, not futurephysicalCC/actualdownstream/yield.'}
    (out/'provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
    with (out/'run.log').open('x') as logstream:
        state = run_bounded(['ngspice', '-b', 'nominal.cir'], logstream, out/'run.json', 120, cwd=out, interval_s=1)
    log = (out/'run.log').read_text()
    errors = [line for line in log.splitlines() if re.search(r'(?im)^Error|Timestep too small|analysis aborted|no such vector|no such parameter|not available', line)]
    result = {'condition': provenance['declared_changes'], 'status': 'failed', 'tc_status': 'not run', 'wall_s': state['wall_s'],
              'watchdog_status': state['status'], 'returncode': state['returncode'], 'errors': errors, 'warnings': warning_inventory(log)}
    try:
        assert state['status'] == 'completed' and state['returncode'] == 0 and not errors
        observed = re.findall(r'^(@[^\s]+)\s*=\s*(\S+)', log, re.M)
        assert [key for key, value in observed] == parameters+parameters
        assert all(np.isfinite(float(value)) for key, value in observed)
        assert observed[:2842] == observed[2842:]
        data = np.loadtxt(str(out/'nominal.dat'), skiprows=1)
        assert data.shape == (34, 12) and np.isfinite(data).all() and np.array_equal(data[:, 0], np.arange(-40, 126, 5))
        tc = float(np.ptp(data[:, 1])/data[13, 1]/165*1e6)
        result.update(status='passed', tc_status='passed' if tc <= 50 else 'failed', tc_ppm_C=tc,
                      vref25_V=float(data[13, 1]), parameters_before=observed[:2842], parameters_after=observed[2842:],
                      waveform_sha256=sha(out/'nominal.dat'))
    except (AssertionError, ValueError, OSError, IndexError) as error:
        result['analysis_error'] = repr(error)
    (out/'summary.json').write_text(json.dumps([result], indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ['warnings', 'parameters_before', 'parameters_after']}, indent=2))
    raise SystemExit(0 if result['status'] == 'passed' else 1)


if __name__ == '__main__':
    main()
