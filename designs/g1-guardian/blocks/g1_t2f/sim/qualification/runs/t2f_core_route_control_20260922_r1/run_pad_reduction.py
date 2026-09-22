#!/usr/bin/env python3
"""Bounded unchanged-model TEMP pad reductions; no electrical qualification."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
PDK = Path('/foss/pdks/ihp-sg13g2')
SOURCE = HERE/'runs/t2f_output_pad_nominal10p_20260922_r1'
WAVE = HERE/'runs/t2f_joint_temp7_20260921_01/ptat_T25.dat'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run-id', required=True)
    ap.add_argument('--image-id', required=True)
    ap.add_argument('--case', choices=['replay-pad', 'core-route'], required=True)
    args = ap.parse_args()
    assert Path(args.run_id).name == args.run_id
    assert (PDK/'COMMIT').read_text().strip() == '84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    out = HERE/'runs'/args.run_id
    out.mkdir(exist_ok=False)
    shutil.copy(__file__, out/Path(__file__).name)
    for name in ['.spiceinit', 'io.spi', 'bgr.spice', 't2f.spice']:
        shutil.copy(SOURCE/name, out/name)
    original = (SOURCE/'pad.cir').read_text()
    manifest = {'command': sys.argv, 'case': args.case, 'image_id': args.image_id,
                'pdk_commit': (PDK/'COMMIT').read_text().strip(),
                'ngspice': subprocess.check_output(['ngspice', '--version'], text=True),
                'source_run': SOURCE.name, 'source_deck_sha256': sha(SOURCE/'pad.cir'),
                'sources_sha256': {name: sha(out/name) for name in ['.spiceinit', 'io.spi', 'bgr.spice', 't2f.spice']},
                'model_sha256': {str(p.relative_to(PDK)): sha(p) for p in sorted((PDK/'libs.tech/ngspice/models').glob('*.lib'))},
                'status': 'not run', 'watchdog_seconds': 300,
                'scope': 'Numerical reduction only; unchanged PDK models and original numerical settings. '
                         'Replay uses an ideal prescribed core waveform, eliminating physical output impedance and feedback. '
                         'Core-route control removes pad and external load while retaining the exact estimated route.'}
    if args.case == 'replay-pad':
        with WAVE.open() as stream:
            next(stream)
            rows = [list(map(float, line.split()))[:2] for line in stream if line.strip()]
        assert rows[0][0] == 0 and rows[-1][0] == 32e-6
        assert all(len(r) == 2 and all(map(math.isfinite, r)) for r in rows)
        intervals = [b[0]-a[0] for a, b in zip(rows, rows[1:])]
        assert all(dt > 0 for dt in intervals), 'PWL times must strictly increase'
        slopes = [(b[1]-a[1])/dt for a, b, dt in zip(rows, rows[1:], intervals)]
        assert all(map(math.isfinite, slopes))
        manifest['replay'] = {'source_waveform': str(WAVE.relative_to(HERE)), 'sha256': sha(WAVE),
                              'points': len(rows), 'minimum_dt_s': min(intervals),
                              'maximum_abs_slew_V_s': max(map(abs, slopes)),
                              'finite_edges_status': 'passed', 'no_decimation': True}
        selected = [line for line in original.splitlines()
                    if line.startswith(('.lib ', '.option ', '.global ', '.temp ', 'Vsub '))]
        deck = '* Prescribed saved-core-wave actual TEMP pad reduction\n'+'\n'.join(selected)+'\n.include io.spi\n'
        deck += 'Vpad12 pad_vdd 0 1.2\nVpad33 pad_iovdd 0 3.3\n'
        deck += 'Rroute fout pad_c2p 210.936\nCroute_near fout 0 11.72035f\nCroute_far pad_c2p 0 11.72035f\n'
        deck += 'Xpad temp_pad pad_c2p pad_vdd 0 pad_iovdd 0 sg13g2_IOPadOut16mA\nCexternal temp_pad 0 10p\n'
        deck += 'Vreplay fout 0 PWL(\n'+''.join('+ %.17g %.17g\n' % tuple(r) for r in rows)+'+ )\n'
        vectors = 'v(fout) v(pad_c2p) v(temp_pad) v(xpad.net1) v(xpad.net2) i(vpad33) i(vpad12) i(vreplay)'
        deck += '.control\nset num_threads=1\nset numdgt=15\nset wr_singlescale\nset wr_vecnames\n'
        deck += 'save '+vectors+'\ntran 2n 32u\nwrdata reduction.dat '+vectors+'\nquit\n.endc\n.end\n'
        columns = 9
    else:
        assert original.count('Xpad temp_pad pad_c2p pad_vdd 0 pad_iovdd 0 sg13g2_IOPadOut16mA') == 1
        deck = '\n'.join(line for line in original.splitlines()
                         if not line.startswith(('Xpad ', 'Cexternal ')))+'\n'
        deck = deck.replace(' v(temp_pad)', '').replace('wrdata pad.dat', 'wrdata reduction.dat')
        columns = 8
    assert '@@' not in deck
    assert 'method=gear' in deck and 'abstol=1e-13 reltol=1e-4 vntol=1e-6' in deck
    (out/'reduction.cir').write_text(deck)
    manifest['deck_sha256'] = sha(out/'reduction.cir')
    def save():
        (out/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    save()
    start = time.monotonic()
    with (out/'reduction.log').open('w') as log, (out/'reduction.stderr').open('w') as err:
        try:
            rc = subprocess.run(['ngspice', '-b', 'reduction.cir'], cwd=out, stdout=log, stderr=err, timeout=300).returncode
            timed = False
        except subprocess.TimeoutExpired:
            rc, timed = None, True
    manifest.update(solver_exit=rc, timed_out=timed, wall_seconds=time.monotonic()-start,
                    status='not run' if timed else 'failed')
    logs = (out/'reduction.log').read_text()+'\n'+(out/'reduction.stderr').read_text()
    manifest['numerical_errors'] = re.findall(r'(?im)^.*(?:Timestep too small|analysis aborted|simulation\(s\) aborted|^Error).*$', logs)
    try:
        with (out/'reduction.dat').open() as stream:
            next(stream)
            data = [list(map(float, line.split())) for line in stream if line.strip()]
        manifest['saved_rows'] = len(data)
        manifest['last_saved_time_s'] = data[-1][0] if data else None
        assert rc == 0 and not timed and not manifest['numerical_errors']
        assert data and all(len(r) == columns and all(map(math.isfinite, r)) for r in data)
        assert abs(data[-1][0]-32e-6) < 1e-12
        manifest.update(status='passed', waveform_sha256=sha(out/'reduction.dat'))
    except (AssertionError, OSError, ValueError, StopIteration) as exc:
        manifest['analysis_error'] = str(exc)
    save()
    print(json.dumps({k: v for k, v in manifest.items() if k not in ['model_sha256', 'ngspice']}, indent=2))


if __name__ == '__main__':
    main()
