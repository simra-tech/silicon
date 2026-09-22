#!/usr/bin/env python3
"""Bounded, sequential completion of the declared reduced-front phase campaign."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

from run_bounded import atomic_json

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--image-id', required=True)
    args = ap.parse_args()
    contract_path = HERE / 'campaigns/fault_phase_server_20260922_contract_r2.json'
    contract = json.loads(contract_path.read_text())
    for case in contract['cases']:
        pilot = HERE / f'campaigns/phase_pilot_{case}_20260922_r2.json'
        if json.loads(pilot.read_text())['status'] != 'passed':
            ap.error('both corrected endpoint pilots must pass')
    run_id = 'phase_' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dt%H%M%Sz') + '_' + uuid.uuid4().hex[:8]
    out = HERE / 'campaigns' / run_id
    out.mkdir(exist_ok=False)
    scripts = ['run_top.py', 'run_bounded.py', 'simulation_errors.py', 'check_campaign.py', Path(__file__).name]
    identity = {name: sha(HERE / name) for name in scripts}
    for name in scripts:
        shutil.copyfile(HERE / name, out / name)
    shutil.copyfile(contract_path, out / 'contract.json')
    result = dict(status='running', contract_sha256=sha(contract_path),
                  source_sha256=identity, cases=[], image_id=args.image_id,
                  scope=contract['scope'])
    atomic_json(out / 'summary.json', result)
    for phase in contract['event_shifts_ns']:
        if phase == contract['pilot_shift_ns']:
            continue
        if any(sha(HERE / name) != digest for name, digest in identity.items()):
            result.update(status='failed', error='runner source changed during batch')
            atomic_json(out / 'summary.json', result)
            raise SystemExit(1)
        suffix = run_id + '_p' + str(phase).replace('.', 'p')
        command = [sys.executable, str(HERE / 'run_top.py'), *contract['cases'],
                   '--netlist', 'pex', '--front', 'beh', '--outpads', 'beh',
                   '--threads', '1', '--event-shift-ns', str(phase), '--timeout', '300',
                   '--run-id', suffix, '--image-id', args.image_id]
        with (out / (suffix + '.log')).open('x') as log:
            completed = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, cwd=HERE)
        records = []
        for case in contract['cases']:
            tag = f'{case}_pex_beh_tt_27C_clockfix' + (f'_phase{phase:g}ns' if phase else '')
            tag += '_threads1_functional_' + suffix
            dest = out / f'{case}_p{phase:g}.json'
            checker = subprocess.run([sys.executable, str(HERE / 'check_campaign.py'), tag,
                                      '--output', str(dest)], capture_output=True, text=True)
            (out / f'{case}_p{phase:g}_checker.log').write_text(checker.stdout + checker.stderr)
            assessment = json.loads(dest.read_text()) if dest.exists() else dict(status='not run')
            records.append(dict(case=case, phase_ns=phase, tag=tag, launch_returncode=completed.returncode,
                                acceptance=assessment['status'], checker_returncode=checker.returncode,
                                assessment_sha256=sha(dest) if dest.exists() else None))
        result['cases'] += records
        failed = completed.returncode or any(r['acceptance'] != 'passed' or r['checker_returncode'] for r in records)
        result['status'] = 'failed' if failed else 'running'
        atomic_json(out / 'summary.json', result)
        print(json.dumps(records), flush=True)
        if failed:
            raise SystemExit(1)
    result.update(status='passed', completed_new_cases=len(result['cases']),
                  pilot_cases=2, total_declared_cases=16)
    atomic_json(out / 'summary.json', result)
    print(out, flush=True)


if __name__ == '__main__':
    main()
