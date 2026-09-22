#!/usr/bin/env python3
"""One bounded, single-thread capacitance-only extraction from audited LVSDB."""
import argparse
import datetime
import json
import os
from pathlib import Path
import re
import subprocess
import time

from audit_unsimplified import sha, SOURCE
from run_pex_prepare import SUPPORT, HERE


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run-id', required=True)
    ap.add_argument('--resource-gate', type=Path, required=True)
    args = ap.parse_args()
    assert re.fullmatch('bgr-cpex-[a-z0-9-]+', args.run_id)
    assert len(os.sched_getaffinity(0)) == 1 and next(iter(os.sched_getaffinity(0))) in range(4)
    gate = json.loads(args.resource_gate.read_text())
    age = (datetime.datetime.now(datetime.timezone.utc) - datetime.datetime.fromisoformat(gate['utc'])).total_seconds()
    assert gate['status'] == 'passed' and 0 <= age < 1800 and gate['external_allocation']['expected_growth_gib'] >= 2
    bulk = Path(os.environ['G1_RESULTS_ROOT'])
    assert str(bulk) == gate['external_allocation']['root']
    base = bulk / 'bgr-pex-prepare-20260922-r2'
    prep = json.loads((base / 'summary.json').read_text())
    assert prep['status'] == 'passed extraction preparation' and prep['source_node_parameter_audit'] == 'passed'
    assert all(sha(Path(path)) == digest for path, digest in prep['inputs'].items())
    assert all(sha(SUPPORT / path) == digest for path, digest in prep['support_hashes'].items())
    assert sha(base / 'extraction.lvsdb') == prep['strict_lvs']['sha256']
    out = bulk / args.run_id
    out.mkdir(exist_ok=False)
    files = [base / 'summary.json', base / 'source_device_audit.json', base / 'extraction.lvsdb', SOURCE, Path(__file__)]
    bindings = {str(path): sha(path) for path in files}
    (out / Path(__file__).name).write_bytes(Path(__file__).read_bytes())
    cmd = ['kpex', '--threads', '1', '--pdk', 'ihp-sg13g2', '--lvsdb', str(base / 'extraction.lvsdb'),
           '--cell', 'g1_bgr', '--2.5D', '--mode', 'CC', '--out_dir', str(out / 'kpex')]
    result = {'status': 'running', 'inputs': bindings, 'resource_gate_sha256': sha(args.resource_gate), 'command': cmd,
              'watchdog_s': 300, 'kill_grace_s': 5, 'coverage': '1027 extracted + 9 geometrically verified grounded dummies',
              'prospective_augmentation': 'Original1036 canonicalsource plus only mapped extracted capacitors; zero-cap source byteidentical. No extracteddevice replacement.',
              'electrical_and_augmentation_mapping': 'not run', 'wire_resistance': 'not run; CC mode only', 'seed': 'not applicable'}
    def save():
        (out / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    save()
    start = time.monotonic()
    try:
        with (out / 'kpex.log').open('x') as log:
            process = subprocess.run(['timeout', '--kill-after=5', '300'] + cmd, stdout=log, stderr=subprocess.STDOUT)
        result['returncode'] = process.returncode
        assert process.returncode == 0
        candidates = list((out / 'kpex').rglob('*_k25d_pex_netlist.spice'))
        assert len(candidates) == 1
        raw = candidates[0]
        caps = [line for line in raw.read_text().splitlines() if line.startswith('Cext_')]
        assert len(caps) > 0
        result.update(status='passed capacitance generation', raw_pex_sha256=sha(raw), capacitor_count=len(caps), raw_pex=str(raw))
    except Exception as error:
        result.update(status='failed', error=repr(error))
    unchanged = all(sha(Path(path)) == digest for path, digest in bindings.items())
    unchanged &= all(sha(SUPPORT / path) == digest for path, digest in prep['support_hashes'].items())
    size = sum(path.stat().st_size for path in out.rglob('*') if path.is_file())
    result.update(inputs_support_unchanged=unchanged, output_bytes=size, wall_s=time.monotonic() - start,
                  finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    if not unchanged or size > 2 * 2**30:
        result['status'] = 'failed final input/output gate'
    save()
    print(json.dumps(result, indent=2))
    return 0 if result['status'] == 'passed capacitance generation' else 1


if __name__ == '__main__':
    raise SystemExit(main())
