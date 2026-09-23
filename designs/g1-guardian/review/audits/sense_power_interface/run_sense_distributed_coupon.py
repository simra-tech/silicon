#!/usr/bin/env python3
"""Bounded passive-only implementation control; no SENSE source/model mutation."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from analyze_sense_distributed_coupon import audit, inspect_log, parse_waveform


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepared', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); assert not args.output.exists()
    assert len(os.sched_getaffinity(0)) == 1
    contract = json.loads((args.prepared/'contract.json').read_text())
    assert contract['status'] == 'prepared conditional passive coupon; no simulation run'
    assert contract['actual_SENSE_weights'] == 'not selected'
    assert contract['prospective_gates']['child_watchdog_s'] == 30
    assert [r['name'] for r in contract['cases']] == ['direct-zero-r', 'adapter-zero-r', 'distributed-r', 'unequal-voltage', 'wrong-current-sign']
    assert Path('/foss/pdks/ihp-sg13g2/COMMIT').read_text().strip() == '84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    version = subprocess.check_output(['ngspice', '--version'], text=True)
    assert 'ngspice-46' in version
    args.output.mkdir(parents=True)
    for name in ('contract.json', 'source.py'): shutil.copyfile(args.prepared/name, args.output/name)
    (args.output/'runner.py').write_bytes(Path(__file__).read_bytes())
    analyzer = Path(__file__).with_name('analyze_sense_distributed_coupon.py')
    (args.output/'analyzer.py').write_bytes(analyzer.read_bytes())
    (args.output/'ngspice-version.txt').write_text(version)
    result = dict(status='running conditional passive controls', contract_sha256=sha(args.prepared/'contract.json'),
                  script_sha256=sha(Path(__file__)), analyzer_sha256=sha(analyzer), cases=[],
                  source_models_changed=False, actual_SENSE_contact_weights='not selected')
    stopped = False
    for case in contract['cases']:
        name = case['name']; target = args.output/name; target.mkdir()
        source = args.prepared/name/'coupon.cir'; assert sha(source) == case['deck_sha256']
        shutil.copyfile(source, target/'coupon.cir')
        if stopped:
            result['cases'].append(dict(name=name, status='not run', reason='earlier execution/control failed'))
            continue
        command = ['timeout', '--kill-after=2', '30', 'ngspice', '-b', 'coupon.cir']
        start = time.monotonic()
        with (target/'simulator.log').open('x') as log:
            run = subprocess.run(command, cwd=str(target), stdout=log, stderr=subprocess.STDOUT)
        record = dict(name=name, returncode=run.returncode, wall_s=time.monotonic()-start,
                      command=command, log_sha256=sha(target/'simulator.log'), status='failed')
        path = target/'waveform.dat'
        try:
            assert run.returncode == 0 and path.exists(), 'No completed waveform'
            log_gate = inspect_log((target/'simulator.log').read_text(errors='replace'))
            record['simulator_log'] = log_gate
            assert log_gate['status'] == 'passed', 'Simulator fatal/error text, independent of exit status'
            rows = parse_waveform(path, case['columns'])
            check = audit(rows, direct=name == 'direct-zero-r'); record['control'] = check
            if name == 'wrong-current-sign':
                accepted = check.get('signed_current_residual_A', 0) > 1e-12 and check.get('power_residual_W', 0) > 1e-12
            else: accepted = check['status'] == 'passed'
            record['status'] = 'passed expected diagnostic disposition' if accepted else 'failed'
        except Exception as exc:
            record['error'] = repr(exc)
        record['output_bytes'] = sum(p.stat().st_size for p in args.output.rglob('*') if p.is_file())
        if record['output_bytes'] > 20*2**20: record.update(status='failed', growth_exceeded=True)
        stopped = record['status'] == 'failed'; result['cases'].append(record)
        (args.output/'run.json').write_text(json.dumps(result, indent=2)+'\n')
    with (args.output/'analysis.log').open('x') as log:
        analysis = subprocess.run([sys.executable, str(analyzer), '--coupon', str(args.output),
                                   '--output', str(args.output/'analysis.json')], stdout=log, stderr=subprocess.STDOUT)
    result.update(status='passed conditional passive implementation controls' if analysis.returncode == 0 and not stopped else 'failed conditional passive implementation controls',
                  analysis_returncode=analysis.returncode,
                  not_run=['Actual SENSE contact allocation', 'Full11512 source-model/wave parity',
                           'Intrinsic geometry/model applicability', 'Metal R/field/electrical adoption'])
    (args.output/'run.json').write_text(json.dumps(result, indent=2)+'\n'); print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['status'].startswith('passed') else 1)


if __name__ == '__main__': main()
