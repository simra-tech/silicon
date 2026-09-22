#!/usr/bin/env python3
"""One distinct 240s exact-input recovery of the retained typ/ff/typ 3V failure."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import numpy as np
from run_586_pvt import sha, transform

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
sys.path.insert(0, str(HERE.parents[2]/'g1_trip/sim'))
from result_directory import allocate_run
from run_nominal_clock_probe import run_bounded
from analyze_bgr_substitution_outcomes import warning_inventory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--image-id', required=True)
    args = parser.parse_args()
    old = HERE/'runs/bgr586-pvt-typ-ff-typ-v30-20260922-a'
    oldrow, = json.loads((old/'summary.json').read_text())
    prov = json.loads((old/'provenance.json').read_text())
    assert oldrow['status'] == 'failed' and oldrow['watchdog_status'] == 'timeout'
    assert json.loads((old/'run.json').read_text())['timeout_s'] == 120
    qualified = HERE/'runs/bgr_one_draw_20260922_r1'
    qm = json.loads((qualified/'manifest.json').read_text())
    assert prov['reference_manifest_sha256'] == sha(qualified/'manifest.json')
    assert prov['parameter_order'] == qm['parameters'] and len(qm['parameters']) == 2842
    assert sha(old/'pex_nominal.spice') == prov['source_sha256'] == qm['source_sha256'] == '586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b'
    assert (old/'nominal.cir').read_text() == transform((qualified/'disabled/nominal.cir').read_text(), 'typ', 'ff', 'typ', 3.0)
    pd = Path('/foss/pdks/ihp-sg13g2')
    assert (pd/'COMMIT').read_text().strip() == qm['runtime']['pdk_commit']
    assert args.image_id == prov['image_manifest'] == 'sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0'
    assert subprocess.check_output(['ngspice', '--version'], universal_newlines=True) == qm['ngspice']
    for key, folder, pattern in [('model_sha256', 'models', '*.lib'), ('osdi_sha256', 'osdi', '*.osdi')]:
        assert qm['runtime'][key] == {str(f.relative_to(pd)): sha(f) for f in sorted((pd/'libs.tech/ngspice'/folder).glob(pattern))}
    oldlog = (old/'run.log').read_text()
    oldparams = re.findall(r'^(@[^\s]+)\s*=\s*(\S+)', oldlog, re.M)
    assert [k for k, v in oldparams] == qm['parameters']
    out = allocate_run(HERE.parent, args.run_id, relative_parent='qualification/runs')
    for name in ['nominal.cir', 'pex_nominal.spice', '.spiceinit']:
        (out/name).write_bytes((old/name).read_bytes())
    (out/'runner.py').write_text(Path(__file__).read_text())
    provenance = dict(prov, arguments=sys.argv[1:], runner_sha256=sha(Path(__file__)), original_failed_run=str(old.relative_to(ROOT)),
                      original_receipts_sha256={name: sha(old/name) for name in ['nominal.cir', 'pex_nominal.spice', '.spiceinit', 'summary.json', 'provenance.json', 'run.log', 'run.json']},
                      sole_change='Fresh output directory and watchdog120s to240s; all simulator input bytes exact. Original failure retained.', watchdog_s=240)
    (out/'provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
    with (out/'run.log').open('x') as stream:
        state = run_bounded(['ngspice', '-b', 'nominal.cir'], stream, out/'run.json', 240, cwd=out, interval_s=1)
    log = (out/'run.log').read_text()
    result = dict(status='failed', tc_status='not run', runtime=state, warnings=warning_inventory(log), original_failure_retained=True)
    try:
        assert state['status'] == 'completed' and state['returncode'] == 0
        errors = re.findall(r'^.*(?:Error|Timestep too small|analysis aborted|no such vector|no such parameter|not available).*$', log, re.M)
        assert not errors, errors
        observed = re.findall(r'^(@[^\s]+)\s*=\s*(\S+)', log, re.M)
        assert [k for k, v in observed] == qm['parameters']*2
        assert observed[:2842] == observed[2842:] == oldparams
        assert all(np.isfinite(float(v)) for k, v in observed)
        data = np.loadtxt(str(out/'nominal.dat'), skiprows=1)
        assert data.shape == (34, 12) and np.isfinite(data).all() and np.array_equal(data[:, 0], np.arange(-40, 126, 5))
        tc = float(np.ptp(data[:, 1])/data[13, 1]/165*1e6)
        # The failed job did not export nominal.dat; its logged BEFORE inventory
        # is the available numerical prefix, not a fabricated DC wave comparison.
        result.update(status='passed exact-input recovery', tc_status='passed' if tc <= 50 else 'failed', tc_ppm_C=tc,
                      parameters_before=observed[:2842], parameters_after=observed[2842:], original_before_exact=True,
                      overlapping_dc_wave_parity='not run; original watchdog left no exported waveform', waveform_sha256=sha(out/'nominal.dat'),
                      vref25_V=float(data[13, 1]), rows=len(data))
    except (AssertionError, ValueError, OSError, IndexError) as error:
        result['analysis_error'] = repr(error)
    (out/'summary.json').write_text(json.dumps([result], indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ['parameters_before', 'parameters_after', 'warnings']}, indent=2))
    raise SystemExit(0 if result['status'].startswith('passed') else 1)


if __name__ == '__main__':
    main()
