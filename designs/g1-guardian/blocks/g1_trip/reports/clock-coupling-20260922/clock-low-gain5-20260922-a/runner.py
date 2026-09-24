#!/usr/bin/env python3
"""Single-change, bounded replay for incremental clock coupling or local gain."""
import argparse
import hashlib
import json
import math
import re
import shutil
import subprocess
import sys
from pathlib import Path
from result_directory import allocate_run
from wave_archive import archive_new_wave

SIM = Path(__file__).resolve().parent
ROOT = SIM.parents[4]
sys.path.insert(0, str(SIM.parents[1] / 'g1_top/sim'))
from run_bounded import run_bounded
from simulation_errors import solver_failure

CAP_FF = 5.233872140
REFERENCES = ('clock-coupling-host-low-20260922-a', 'clock-coupling-host-high-20260922-a')
PDK = '84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
IMAGE = 'sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def changed_deck(original, reference, run_id, mode):
    """An exact baseline replay except the one prospectively declared component."""
    assert reference != run_id and original.count('.control\n') == 1
    renamed = original.replace(reference, run_id)
    if mode == 'coupling':
        line = 'Cinterface isense clk %.12gf\n' % CAP_FF
        assert 'Cinterface' not in renamed
        changed = renamed.replace('.control\n', line + '.control\n')
        assert changed.replace(line, '') == renamed
    else:
        assert mode in ('gain5', 'gain10')
        match = re.search(r'^Vsh shp 0 dc (\S+)$', renamed, re.M)
        assert match and len(re.findall(r'^Vsh ', renamed, re.M)) == 1
        delta = float(mode[4:]) * 1e-6
        line = 'Vsh shp 0 dc %.17g' % (float(match[1]) + delta)
        changed = renamed[:match.start()] + line + renamed[match.end():]
        assert changed.replace(line, match[0], 1) == renamed
    assert changed.count('CL isense 0 300f\n') == 1
    return changed


def read_wave(path):
    with path.open() as stream:
        columns = stream.readline().split()
        rows = [list(map(float, line.split())) for line in stream if line.strip()]
    assert columns == ['time', 'v(clk)', 'v(xt.icmp)', 'v(xt.vth_soft)',
                       'v(xt.vth_hard)', 'v(cmp_soft)', 'v(cmp_hard)', 'v(isense)']
    assert rows and all(len(row) == 8 and all(math.isfinite(x) for x in row) for row in rows)
    assert all(b[0] > a[0] for a, b in zip(rows, rows[1:]))
    assert abs(rows[-1][0] - .52e-6) < 1e-15
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference', choices=REFERENCES, required=True)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--mode', choices=('coupling', 'gain5', 'gain10'), required=True)
    parser.add_argument('--image-id', required=True)
    args = parser.parse_args()
    assert args.image_id == IMAGE
    reference = SIM / 'qualification' / args.reference
    previous = json.loads((reference / 'provenance.json').read_text())
    parity = json.loads((reference / 'host_parity.json').read_text())
    baseline = json.loads((reference / 'summary.json').read_text())
    assert parity['status'] == 'passed' and all(parity['checks'].values())
    assert len(baseline) == 1 and baseline[0]['solver_status'] == 'passed'
    baseline = baseline[0]
    assert len(baseline['fingerprints']) == 27 and previous['seed'] == 71001
    pd = Path('/foss/pdks/ihp-sg13g2')
    models = {str(f.relative_to(pd)): sha(f) for f in (pd / 'libs.tech/ngspice/models').rglob('*') if f.is_file()}
    version = subprocess.check_output(['ngspice', '--version'], universal_newlines=True)
    assert (pd / 'COMMIT').read_text().strip() == previous['pdk_commit'] == PDK
    assert previous['model_sha256'] == models and previous['ngspice_version'] == version
    assert previous['image_id_observed_by_host'] == IMAGE
    assert previous['transient_endpoint_us'] == .52
    original = (reference / (baseline['case'] + '.cir')).read_text()
    out = allocate_run(SIM, args.run_id)
    inputs = [reference / name for name in ['sense.spice', 'trip.spice', 'bgr.spice',
              baseline['case'] + '.cir', 'provenance.json', 'summary.json', 'host_parity.json']]
    frozen = {str(path.relative_to(ROOT)): sha(path) for path in inputs}
    for name in ['sense.spice', 'trip.spice', 'bgr.spice']:
        shutil.copyfile(reference / name, out / name)
    shutil.copyfile(Path(__file__), out / 'runner.py')
    contract = SIM / 'CLOCK_COUPLING_DIAGNOSTIC_20260922.md'
    interval = ROOT / 'designs/g1-guardian/review/audits/interface-clock-interval-20260922-r1/manifest.json'
    shutil.copyfile(contract, out / contract.name)
    provenance = dict(previous)
    provenance.update(run_id=args.run_id, reference=args.reference, mode=args.mode,
        runner_arguments=sys.argv[1:], runner_sha256=sha(Path(__file__)),
        reference_input_sha256=frozen, contract_sha256=sha(contract),
        interval_manifest_sha256=sha(interval), init_sha256=sha(SIM / '.spiceinit'),
        coupling_fF=CAP_FF if args.mode == 'coupling' else 0,
        shunt_delta_uV=0 if args.mode == 'coupling' else int(args.mode[4:]),
        watchdog_timeout_s=300, git_head=subprocess.check_output(
            ['git', '-c', 'safe.directory=/work', 'rev-parse', 'HEAD'], cwd=ROOT, universal_newlines=True).strip(),
        scope='Incremental mutual-only diagnostic; original ground load retained. Not full RC or physical adoption.')
    deck = out / (baseline['case'] + '.cir')
    deck.write_text(changed_deck(original, args.reference, args.run_id, args.mode))
    provenance['deck_sha256'] = sha(deck)
    (out / 'provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
    with (out / 'run.log').open('x') as log:
        state = run_bounded(['ngspice', '-b', str(deck.relative_to(SIM))], log,
            out / 'run.json', 300, cwd=SIM, metadata={'mode': args.mode, 'deck_sha256': sha(deck)}, interval_s=1)
    log = (out / 'run.log').read_text()
    fingerprints = re.findall(r'^(@[^=]+) = (\S+)', log, re.M)
    checks = dict(solver_completed=state['status'] == 'completed' and state['returncode'] == 0,
        solver_log_clean=not solver_failure(log), end_marker='QUALIFICATION_END' in log,
        all27_parameters_exact=[list(x) for x in fingerprints] == baseline['fingerprints'],
        reference_inputs_unchanged=all(sha(ROOT / path) == digest for path, digest in frozen.items()),
        source_copies_exact=all(sha(out / name) == sha(reference / name) for name in ['sense.spice', 'trip.spice', 'bgr.spice']))
    wave = out / (baseline['case'] + '.dat')
    error = None
    try:
        rows = read_wave(wave)
        checks['finite_complete_waveform'] = True
    except (OSError, ValueError, AssertionError) as exc:
        rows = []
        checks['finite_complete_waveform'] = False
        error = type(exc).__name__
    report = dict(status='passed' if all(checks.values()) else 'failed', checks=checks,
        case=baseline['case'], reference=args.reference, mode=args.mode,
        fingerprints=fingerprints, rows=len(rows), error=error,
        waveform_sha256=sha(wave) if wave.exists() else None,
        solver_status=state['status'], wall_s=state['wall_s'],
        electrical_acceptance='not run; requires paired local-gain and coupling evaluation',
        physical_measurement='not applicable (numerical diagnostic)')
    (out / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
    if wave.exists():
        archive_new_wave(wave)
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report['status'] == 'passed' else 1)


if __name__ == '__main__':
    main()
