#!/usr/bin/env python3
"""Full exact-union extraction view, gated by completed small CC parity."""
import argparse
import collections
import datetime
import json
import os
from pathlib import Path
import subprocess
import time

import pya

from audit_unsimplified import audit, sha, SOURCE
from run_pex_prepare import HERE, ROOT, SUPPORT
from run_stock import strict


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--resource-gate', type=Path, required=True)
    args = ap.parse_args()
    assert len(os.sched_getaffinity(0)) == 1 and next(iter(os.sched_getaffinity(0))) in range(4)
    gate = json.loads(args.resource_gate.read_text())
    age = (datetime.datetime.now(datetime.timezone.utc) - datetime.datetime.fromisoformat(gate['utc'])).total_seconds()
    assert gate['status'] == 'passed' and 0 <= age < 1800 and gate['external_allocation']['expected_growth_gib'] >= 2
    bulk = Path(os.environ['G1_RESULTS_ROOT'])
    assert str(bulk) == gate['external_allocation']['root']
    geometry = bulk / 'bgr-union-full-geometry-20260922-r1'
    pilot = bulk / 'bgr-union-pilot-check-20260922-r1/summary.json'
    pilot_data = json.loads(pilot.read_text())
    assert pilot_data['status'] == 'passed strictLVS and exactCC representation parity' and all(pilot_data['checks'].values())
    preparation = json.loads((geometry / 'summary.json').read_text())
    assert preparation['status'] == 'passed exact-union preparation' and preparation['all_text_exact']
    assert all(row['xor_polygons'] == 0 for row in preparation['layers'])
    golden = bulk / 'bgr-assembly-20260922-r5/bank.gds'
    assert sha(golden) == preparation['source_sha256'] == '0083eabb0f730b2cb27eeb0bda1ac8f173a21e03e2aa5a329b01ef5cba21b3ed'
    proof = bulk / 'bgr-pex-prepare-20260922-r1/dummy_proof_r2.json'
    assert sha(proof) == '0d146e08578604904e2cde5cb0af641d6c5b8ffbe1ed9d8a0c566ee6edf7ba67'
    assert all(sha(Path(path)) == digest for path, digest in json.loads(proof.read_text())['bindings'].items())
    cdl = bulk / 'bgr-pex-prepare-20260922-r2/extraction_only_1027.cdl'
    assert sha(cdl) == 'fa8393ca88ec44f38ba9387f30697b78ab18f7085a73664fc5ac2574a539ec4f'
    gds = geometry / 'union.gds'
    assert sha(gds) == preparation['union_sha256']
    out = bulk / 'bgr-pex-prepare-20260922-r3'
    out.mkdir(exist_ok=False)
    wrapper = ROOT / 'flow/pex/export_lvsdb.lvs'
    files = [SOURCE, golden, gds, geometry / 'summary.json', pilot, proof, cdl, wrapper,
             Path(__file__), HERE / 'audit_unsimplified.py', HERE / 'run_stock.py', HERE / 'prepare_union_view.py']
    inputs = {str(path): sha(path) for path in files}
    support = {str(path.relative_to(SUPPORT)): sha(path) for path in SUPPORT.rglob('*') if path.is_file()}
    for path in files[6:]:
        (out / path.name).write_bytes(path.read_bytes())
    receipt = {'status': 'running', 'inputs': inputs, 'support_hashes': support, 'steps': [],
               'coverage': '1027 extracted + 9 geometrically verified grounded dummies', 'electrical_source_count': 1036,
               'resource_gate_sha256': sha(args.resource_gate), 'capacitance_electrical': 'not run', 'seed': 'not applicable'}
    def save():
        (out / 'summary.json').write_text(json.dumps(receipt, indent=2) + '\n')
    save()
    begin = time.monotonic()
    try:
        cmd = ['klayout', '-b', '-r', str(wrapper)]
        for arg in ['input=' + str(gds), 'topcell=g1_bgr', 'schematic=' + str(cdl), 'report=' + str(out / 'extraction.lvsdb'),
                    'export_netlist=' + str(out / 'extracted.cir'), 'target_netlist=' + str(out / 'stock_written.cir'),
                    'log=' + str(out / 'extraction_detail.log'), 'thr=1', 'run_mode=deep', 'no_simplify=true',
                    'combine_devices=false', 'purge=false', 'purge_nets=false', 'top_lvl_pins=true',
                    'no_series_res=true', 'no_parallel_res=true']:
            cmd += ['-rd', arg]
        start = time.monotonic()
        with (out / 'export_lvs.log').open('x') as log:
            process = subprocess.run(['timeout', '--kill-after=5', '180'] + cmd, stdout=log, stderr=subprocess.STDOUT)
        receipt['steps'].append({'name': 'export_lvs', 'command': cmd, 'watchdog_s': 180, 'returncode': process.returncode, 'wall_s': time.monotonic() - start})
        assert process.returncode == 0
        log = (out / 'export_lvs.log').read_text()
        assert 'Congratulations! Netlists match.' in log and "Netlists don't match" not in log
        receipt['strict_lvs'] = strict(out / 'extraction.lvsdb')
        assert receipt['strict_lvs']['status'] == 'passed'
        children = receipt['strict_lvs']['circuits'][0]['children']
        assert children['device'] == {'Match': 1027} and children['net'] == {'Match': 55} and children['pin'] == {'Match': 9}
        receipt['source_node_parameter_audit'] = audit(out / 'extraction.lvsdb', out / 'source_device_audit.json', proof)['status']
        assert receipt['source_node_parameter_audit'] == 'passed'
        receipt['status'] = 'passed extraction preparation'
    except Exception as error:
        receipt.update(status='failed', error=repr(error))
    unchanged = all(sha(Path(path)) == digest for path, digest in inputs.items()) and all(sha(SUPPORT / path) == digest for path, digest in support.items())
    size = sum(path.stat().st_size for path in out.rglob('*') if path.is_file())
    receipt.update(inputs_support_unchanged=unchanged, output_bytes=size, wall_s=time.monotonic() - begin,
                   finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    if not unchanged or size > 2 * 2**30:
        receipt['status'] = 'failed final input/output gate'
    save()
    print(json.dumps({key: value for key, value in receipt.items() if key not in ('inputs', 'support_hashes')}, indent=2))
    return 0 if receipt['status'] == 'passed extraction preparation' else 1


if __name__ == '__main__':
    raise SystemExit(main())
