#!/usr/bin/env python3
"""Required586 noise/local-stability controls using unchanged historical decks."""
import argparse
import cmath
import hashlib
import json
import math
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


def probe_source(text, probe):
    lines, changed = [], []
    for line in text.splitlines():
        fields = line.split()
        if line.startswith('XM') and fields[2] == probe:
            changed.append({'instance': fields[0], 'original_line': line})
            fields[2] = 'gate_probe'
            line = ' '.join(fields)
        if line.lower().startswith('.ends'):
            lines += ['Vprobe gate_probe '+probe+' dc 0 ac {pv}', 'Iprobe vss gate_probe dc 0 ac {pi}']
        lines.append(line)
    assert changed
    result = '\n'.join(lines)+'\n'
    # Verify every non-probe source line and original terminal/device parameter.
    original = {r['instance']: r['original_line'] for r in changed}
    recovered = []
    for line in result.splitlines():
        if line.startswith(('Vprobe ', 'Iprobe ')):
            continue
        recovered.append(original.get(line.split()[0], line) if line.split() else line)
    assert '\n'.join(recovered)+'\n' == text
    return result, changed


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run-id', required=True)
    p.add_argument('--image-id', required=True)
    p.add_argument('--kind', choices=['noise', 'pbias', 'pcasc'], required=True)
    p.add_argument('--corner', choices=['nominal', 'slow', 'fast'], default='nominal')
    a = p.parse_args()
    assert a.kind != 'noise' or a.corner == 'nominal'
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
    out = allocate_run(HERE.parent, a.run_id, relative_parent='qualification/runs')
    shutil.copyfile(str(Path(__file__)), str(out/'runner.py'))
    shutil.copyfile(str(HERE/'.spiceinit'), str(out/'.spiceinit'))
    shutil.copyfile(str(source), str(out/'baseline586.spice'))
    original_source = source.read_text()
    assert [sum(line.startswith(prefix) for line in original_source.splitlines()) for prefix in ['XM', 'XR', 'XQ']] == [336, 399, 301]
    old = HERE/'runs'/('bgr_noise_20260921_01' if a.kind == 'noise' else 'bgr_local_stability_20260921_01')
    oldmanifest = json.loads((old/'manifest.json').read_text())
    assert sha(out/'.spiceinit') == sha(old/'.spiceinit')
    snapshots = {}
    if a.kind == 'noise':
        shutil.copyfile(str(source), str(out/'pex.spice'))
        decks = [('noise', (old/'noise.cir').read_text())]
        # Literal deck parity: source include filename remains the same.
        changed = []
    else:
        tag = {'nominal': 'typ_tt_typ_3.3_27', 'slow': 'wcs_ss_wcs_3.0_-40', 'fast': 'bcs_ff_bcs_3.6_125'}[a.corner]
        stem = a.kind+'_'+tag
        modified, changed = probe_source(original_source, a.kind)
        (out/(stem+'.spice')).write_text(modified)
        decks = [(stem+'_'+injection, (old/(stem+'_'+injection+'.cir')).read_text()) for injection in ['voltage', 'current']]
    provenance = {'arguments': sys.argv[1:], 'runner_sha256': sha(Path(__file__)), 'image_manifest': a.image_id,
                  'runtime': qualified['runtime'], 'ngspice': qualified['ngspice'], 'source_sha256': sha(source),
                  'qualified_source_run': str(ref.relative_to(ROOT)), 'qualified_manifest_sha256': sha(ref/'manifest.json'),
                  'historical_fixture_run': str(old.relative_to(ROOT)), 'historical_manifest_sha256': sha(old/'manifest.json'),
                  'primitive_counts': {'MOS': 336, 'R': 399, 'HBT': 301}, 'changed_probe_gate_pins': changed,
                  'scope': 'Unchanged586 nominal mismatch-disabled source; historical1pF VREF/ideal1V IPTAT fixture. Literal historical analysis/stimulus/settings, source substitution only. Local Tian diagnostic does not prove global stability; no new gain/phase or noise budget. Future physicalCC not covered; no modelvalidity/physical adoption.'}
    (out/'provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
    rows, data = [], {}
    for name, deck in decks:
        assert deck == (old/(name+'.cir')).read_text()
        (out/(name+'.cir')).write_text(deck)
        with (out/(name+'.log')).open('x') as logstream:
            state = run_bounded(['ngspice', '-b', name+'.cir'], logstream, out/(name+'.run.json'), 120, cwd=out, interval_s=1)
        log = (out/(name+'.log')).read_text()
        errors = [line for line in log.splitlines() if re.search(r'(?im)^Error|Timestep too small|analysis aborted|no such vector|not available', line)]
        row = {'name': name, 'status': 'failed', 'wall_s': state['wall_s'], 'watchdog_status': state['status'], 'returncode': state['returncode'],
               'deck_sha256': sha(out/(name+'.cir')), 'historical_deck_exact': True, 'errors': errors, 'warnings': warning_inventory(log)}
        try:
            assert state['status'] == 'completed' and state['returncode'] == 0 and not errors
            if a.kind == 'noise':
                psrr = np.loadtxt(str(out/'psrr.dat'), skiprows=1)
                noise = np.loadtxt(str(out/'noise.dat'), skiprows=1)
                match = re.search(r'onoise_total\s*=\s*([-+0-9.eE]+)', log)
                assert match and np.isfinite(psrr).all() and np.isfinite(noise).all() and abs(noise[-1, 0]-1e7) < 1 and abs(psrr[-1, 0]-1e8) < 1
                row.update(noise_1Hz_10MHz_rms_V=float(match.group(1)), psrr_1Hz_dB=float(np.interp(1, psrr[:, 0], psrr[:, 1])),
                           psrr_1kHz_dB=float(np.interp(1000, psrr[:, 0], psrr[:, 1])))
            else:
                values = np.loadtxt(str(out/(name+'.dat')), skiprows=1)
                assert values.ndim == 2 and values.shape[1] == 5 and np.isfinite(values).all() and values[-1, 0] >= .999e9
                data[name.rsplit('_', 1)[1]] = values
            row['status'] = 'passed'
        except (AssertionError, ValueError, OSError, IndexError) as error:
            row['analysis_error'] = repr(error)
        rows.append(row)
        (out/'summary.json').write_text(json.dumps(rows, indent=2)+'\n')
        if row['status'] != 'passed':
            break
    if a.kind != 'noise' and len(data) == 2:
        points = []
        for voltage, current in zip(data['voltage'], data['current']):
            assert voltage[0] == current[0]
            aa, bb, cc, dd = complex(*current[1:3]), complex(*voltage[1:3]), complex(*current[3:5]), complex(*voltage[3:5])
            delta = aa*dd-bb*cc
            gain = (2*delta-aa+dd)/(1+aa-dd-2*delta)
            points.append({'frequency_Hz': float(voltage[0]), 'T_real': gain.real, 'T_imag': gain.imag, 'T_magnitude': abs(gain),
                           'T_phase_deg': math.degrees(cmath.phase(gain)), 'return_difference_magnitude': abs(1+gain)})
        (out/'return_ratio.json').write_text(json.dumps(points, indent=2)+'\n')
        result = {'status': 'passed numerical local diagnostic', 'minimum_return_difference_magnitude': min(p['return_difference_magnitude'] for p in points),
                  'maximum_return_ratio_magnitude': max(p['T_magnitude'] for p in points), 'global_stability_status': 'not run',
                  'gain_phase_margin_acceptance': 'not applicable to unqualified single-loop reduction'}
        (out/'analysis.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'run': a.run_id, 'cases': [{k: v for k, v in row.items() if k != 'warnings'} for row in rows]}, indent=2))
    raise SystemExit(0 if len(rows) == len(decks) and all(r['status'] == 'passed' for r in rows) else 1)


if __name__ == '__main__':
    main()
