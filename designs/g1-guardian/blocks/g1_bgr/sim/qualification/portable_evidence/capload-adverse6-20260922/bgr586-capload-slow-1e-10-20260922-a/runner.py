#!/usr/bin/env python3
"""Literal existing40us capacitance/load fixture with canonical586 substitution."""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import numpy as np
from run_586_required_ac import sha

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
sys.path.insert(0, str(HERE.parents[2]/'g1_trip/sim'))
from result_directory import allocate_run
from run_nominal_clock_probe import run_bounded
from analyze_bgr_substitution_outcomes import warning_inventory


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run-id', required=True)
    p.add_argument('--image-id', required=True)
    p.add_argument('--corner', choices=['nominal', 'slow', 'fast'], required=True)
    p.add_argument('--cap-F', type=float, choices=[1e-13, 1e-11, 1e-10], required=True)
    a = p.parse_args()
    ref = HERE/'runs/bgr_one_draw_20260922_r1'
    qualified = json.loads((ref/'manifest.json').read_text())
    source = ref/'enabled/pex_nominal.spice'
    assert sha(source) == qualified['source_sha256'] == '586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b'
    pd = Path('/foss/pdks/ihp-sg13g2')
    assert (pd/'COMMIT').read_text().strip() == qualified['runtime']['pdk_commit']
    assert a.image_id == 'sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0'
    for key, folder, pattern in [('model_sha256', 'models', '*.lib'), ('osdi_sha256', 'osdi', '*.osdi')]:
        assert qualified['runtime'][key] == {str(f.relative_to(pd)): sha(f) for f in sorted((pd/'libs.tech/ngspice'/folder).glob(pattern))}
    assert subprocess.check_output(['ngspice', '--version'], universal_newlines=True) == qualified['ngspice']
    old = HERE/'runs/bgr_capload9_20260921_01'
    tag = {'nominal': 'typ_tt_typ_27', 'slow': 'wcs_ss_wcs_-40', 'fast': 'bcs_ff_bcs_125'}[a.corner]+'_cap'+format(a.cap_F, 'g')
    deck = (old/(tag+'.cir')).read_text()
    assert 'tran 2n 40u\n' in deck and '.include pex_nominal.spice\n' in deck
    assert 'Cload vref 0 '+str(a.cap_F)+'\n' in deck
    out = allocate_run(HERE.parent, a.run_id, relative_parent='qualification/runs')
    shutil.copyfile(str(source), str(out/'pex_nominal.spice'))
    shutil.copyfile(str(old/'.spiceinit'), str(out/'.spiceinit'))
    shutil.copyfile(str(Path(__file__)), str(out/'runner.py'))
    (out/(tag+'.cir')).write_text(deck)
    provenance = {'arguments': sys.argv[1:], 'runner_sha256': sha(Path(__file__)), 'image_manifest': a.image_id,
                  'runtime': qualified['runtime'], 'ngspice': qualified['ngspice'], 'source_sha256': sha(source),
                  'reference_run': str(ref.relative_to(ROOT)), 'reference_manifest_sha256': sha(ref/'manifest.json'),
                  'historical_run': str(old.relative_to(ROOT)), 'historical_deck_sha256': sha(old/(tag+'.cir')),
                  'historical_deck_exact': True, 'spiceinit_sha256': sha(out/'.spiceinit'),
                  'scope': 'Exact historical40us100nAstep waveform/settings/loadcap/process/temperature; unchanged586source only. Mismatchdisabled. No recovery budget or new margin acceptance, futurephysicalCC not covered.'}
    (out/'provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
    with (out/'run.log').open('x') as logstream:
        state = run_bounded(['ngspice', '-b', tag+'.cir'], logstream, out/'run.json', 300, cwd=out, interval_s=1)
    log = (out/'run.log').read_text()
    errors = [line for line in log.splitlines() if re.search(r'(?im)^Error|Timestep too small|analysis aborted|doAnalyses:|no such vector|not available', line)]
    row = {'case': tag, 'status': 'failed', 'wall_s': state['wall_s'], 'watchdog_status': state['status'], 'returncode': state['returncode'],
           'errors': errors, 'warnings': warning_inventory(log), 'recovery_acceptance': 'not applicable; no recovery budget adopted'}
    try:
        assert state['status'] == 'completed' and state['returncode'] == 0 and not errors
        data = np.loadtxt(str(out/(tag+'.dat')), skiprows=1)
        assert data.ndim == 2 and data.shape[1] == 12 and np.isfinite(data).all() and abs(data[-1, 0]-40e-6) < 1e-12
        row.update(status='passed', waveform_sha256=sha(out/(tag+'.dat')), rows=len(data), vref_initial_V=float(data[0, 1]),
                   vref_final_V=float(data[-1, 1]), vref_min_V=float(data[:, 1].min()), vref_max_V=float(data[:, 1].max()),
                   relative_return_error_percent=float((data[-1, 1]/data[0, 1]-1)*100))
    except (AssertionError, ValueError, OSError, IndexError) as error:
        row['analysis_error'] = repr(error)
    (out/'summary.json').write_text(json.dumps([row], indent=2)+'\n')
    print(json.dumps({k: v for k, v in row.items() if k != 'warnings'}, indent=2))
    raise SystemExit(0 if row['status'] == 'passed' else 1)


if __name__ == '__main__':
    main()
