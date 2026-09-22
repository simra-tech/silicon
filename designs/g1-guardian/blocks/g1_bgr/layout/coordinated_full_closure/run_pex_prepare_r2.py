#!/usr/bin/env python3
"""Approved extraction-only dummy exclusion, never an electrical source edit."""
import argparse
import collections
import datetime
import json
import os
from pathlib import Path
import re
import subprocess
import time

import pya

from audit_unsimplified import audit, sha, SOURCE
from run_stock import strict
from run_pex_prepare import SUPPORT, HERE, ROOT


def dump(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run-id', required=True)
    ap.add_argument('--resource-gate', type=Path, required=True)
    args = ap.parse_args()
    assert re.fullmatch('bgr-pex-[a-z0-9-]+', args.run_id)
    assert len(os.sched_getaffinity(0)) == 1 and next(iter(os.sched_getaffinity(0))) in range(4)
    gate = json.loads(args.resource_gate.read_text())
    age = (datetime.datetime.now(datetime.timezone.utc) - datetime.datetime.fromisoformat(gate['utc'])).total_seconds()
    assert gate['status'] == 'passed' and 0 <= age < 1800 and gate['external_allocation']['expected_growth_gib'] >= 2
    bulk = Path(os.environ['G1_RESULTS_ROOT'])
    assert str(bulk) == gate['external_allocation']['root']
    base = bulk / 'bgr-assembly-20260922-r5'
    prior = bulk / 'bgr-pex-prepare-20260922-r1'
    proof_path = prior / 'dummy_proof_r2.json'
    assert sha(proof_path) == '0d146e08578604904e2cde5cb0af641d6c5b8ffbe1ed9d8a0c566ee6edf7ba67'
    proof = json.loads(proof_path.read_text())
    assert proof['status'] == 'passed'
    assert all(sha(Path(path)) == digest for path, digest in proof['bindings'].items())
    for kind in ('drc', 'lvs'):
        assert json.loads((bulk / ('bgr-assembly-20260922-r5-' + kind) / 'summary.json').read_text())['status'] == 'passed'
    out = bulk / args.run_id
    out.mkdir(exist_ok=False)
    wrapper = ROOT / 'flow/pex/export_lvsdb.lvs'
    paths = [SOURCE, base / 'bank.gds', base / 'bank.cdl', prior / 'flat.gds', prior / 'flat_parity.json', proof_path,
             wrapper, Path(__file__), HERE / 'audit_unsimplified.py', HERE / 'run_stock.py', HERE / 'run_pex_prepare.py',
             HERE / 'GROUNDED_DUMMY_EXTRACTION_20260922.md']
    inputs = {str(path): sha(path) for path in paths}
    support = {str(path.relative_to(SUPPORT)): sha(path) for path in SUPPORT.rglob('*') if path.is_file()}
    for path in paths[6:]:
        (out / path.name).write_bytes(path.read_bytes())
    receipt = {'status': 'running', 'inputs': inputs, 'support_hashes': support, 'steps': [],
               'resource_gate_sha256': sha(args.resource_gate), 'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'coverage': '1027 extracted + 9 geometrically verified grounded dummies', 'electrical_source_count': 1036,
               'original_1036_reference_lvs': 'failed; retained', 'capacitance_electrical': 'not run', 'seed': 'not applicable'}
    dump(out / 'summary.json', receipt)
    start = time.monotonic()
    try:
        text = (base / 'bank.cdl').read_text()
        # Stock CDL uses Q/R/M device notation; source uses XQ/XR/XM.
        source_lines = [line for line in SOURCE.read_text().splitlines() if line.startswith(('XM', 'XQ', 'XR'))]
        assert [line for line in text.splitlines() if line.startswith(('M', 'Q', 'R'))] == [line[1:] for line in source_lines]
        omitted = {line.split()[0][1:]: line[1:] for line in proof['source_lines']}
        selected = [line for line in text.splitlines() if line.split() and line.split()[0] in omitted]
        assert len(selected) == 9 and {line.strip() for line in selected} == set(omitted.values())
        derived = ''.join(line for line in text.splitlines(keepends=True) if not line.split() or line.split()[0] not in omitted)
        assert len([line for line in derived.splitlines() if line.startswith(('M', 'Q', 'R'))]) == 1027
        reference = out / 'extraction_only_1027.cdl'
        reference.write_text(derived)
        receipt['derived_reference'] = {'sha256': sha(reference), 'removed_exact_lines': selected,
            'canonical_source_unchanged': sha(SOURCE) == '586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b',
            'electrical_use': 'prohibited; source1036 including internal dummy substrate/thermal models retained'}
        cmd = ['klayout', '-b', '-r', str(wrapper)]
        for arg in ['input=' + str(prior / 'flat.gds'), 'topcell=g1_bgr', 'schematic=' + str(reference),
                    'report=' + str(out / 'extraction.lvsdb'), 'export_netlist=' + str(out / 'extracted.cir'),
                    'target_netlist=' + str(out / 'stock_written.cir'), 'log=' + str(out / 'extraction_detail.log'),
                    'thr=1', 'run_mode=deep', 'no_simplify=true', 'combine_devices=false', 'purge=false',
                    'purge_nets=false', 'top_lvl_pins=true', 'no_series_res=true', 'no_parallel_res=true']:
            cmd += ['-rd', arg]
        t = time.monotonic()
        with (out / 'export_lvs.log').open('x') as log:
            result = subprocess.run(['timeout', '--kill-after=5', '180'] + cmd, stdout=log, stderr=subprocess.STDOUT)
        receipt['steps'].append({'name': 'export_lvs', 'command': cmd, 'watchdog_s': 180, 'returncode': result.returncode, 'wall_s': time.monotonic() - t})
        assert result.returncode == 0
        log = (out / 'export_lvs.log').read_text()
        assert 'Congratulations! Netlists match.' in log and "Netlists don't match" not in log
        receipt['strict_lvs'] = strict(out / 'extraction.lvsdb')
        assert receipt['strict_lvs']['status'] == 'passed'
        db = pya.LayoutVsSchematic()
        db.read(str(out / 'extraction.lvsdb'))
        circuits = list(db.netlist().each_circuit())
        assert len(circuits) == 1
        counts = collections.Counter(dev.device_class().name for dev in circuits[0].each_device())
        receipt['uncombined_device_classes'] = dict(counts)
        assert sum(value for key, value in counts.items() if 'mos' in key) == 336 and counts['npn13G2'] == 292
        assert counts['rppd'] + counts['rhigh'] == 399 and sum(counts.values()) == 1027
        assert sum(1 for _ in circuits[0].each_pin()) == 9
        receipt['source_node_parameter_audit'] = audit(out / 'extraction.lvsdb', out / 'source_device_audit.json', proof_path)['status']
        assert receipt['source_node_parameter_audit'] == 'passed'
        receipt['status'] = 'passed extraction preparation'
    except Exception as error:
        receipt.update(status='failed', error=repr(error))
    unchanged = all(sha(Path(path)) == digest for path, digest in inputs.items())
    unchanged &= all(sha(SUPPORT / path) == digest for path, digest in support.items())
    size = sum(path.stat().st_size for path in out.rglob('*') if path.is_file())
    receipt.update(inputs_support_unchanged=unchanged, output_bytes=size, wall_s=time.monotonic() - start,
                   finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    if not unchanged or size > 2 * 2**30:
        receipt['status'] = 'failed final input/output gate'
    dump(out / 'summary.json', receipt)
    print(json.dumps({key: value for key, value in receipt.items() if key not in ('inputs', 'support_hashes')}, indent=2))
    return 0 if receipt['status'] == 'passed extraction preparation' else 1


if __name__ == '__main__':
    raise SystemExit(main())
