#!/usr/bin/env python3
"""Bounded strict saved-netlist comparison with explicit reference provenance."""
import argparse
import datetime
import json
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[6]
sys.path.insert(0, str(ROOT / 'designs/g1-guardian/blocks/g1_top/sim'))
from run_bounded import run_bounded
from prepare_saved_workers import sha


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('workers', 'database', 'flatten-proof', 'interface-proof', 'dummy-proof', 'resource-gate', 'output'):
        p.add_argument('--' + key, type=Path, required=True)
    p.add_argument('--variant', choices=['original', 'adapter'], required=True)
    p.add_argument('--exclude-dummies', action='store_true')
    p.add_argument('--minimum-budget', type=int, default=44)
    a = p.parse_args()
    assert not a.output.exists() and set(os.sched_getaffinity(0)) == {1}
    gate = json.loads(a.resource_gate.read_text())
    age = (datetime.datetime.now(datetime.timezone.utc) - datetime.datetime.fromisoformat(gate['utc'])).total_seconds()
    assert gate['status'] == 'passed' and gate['project_cpu_budget'] >= a.minimum_budget and 0 <= age < 1800
    assert gate['ram_available_bytes'] >= 8 * 1024**3
    bulk = Path(os.environ['G1_RESULTS_ROOT'])
    original = bulk / 'fullchip-name-interface-20260923-r1/g1_chip_top_layout_name_only.cdl'
    adapted = bulk / 'fullchip-tap-prefix-adapter-20260923-r1/fullchip_tap_prefix_only.cdl'
    assert sha(original) == 'f4ce6848bd7dd179d2ef4cbd8a4ea6bf9788bcfa1ff4b93fabae8bf18b6378f9'
    assert sha(adapted) == '7395c32d170a787dbc81fd10c67148301d168e51f5ac38de3f0866efe5894006'
    manifest = json.loads((a.workers / 'summary.json').read_text())
    assert manifest['status'].startswith('passed exact') and manifest['stage'] == 'compare'
    assert manifest['database_sha256'] == sha(a.database)
    assert manifest['flatten_proof_sha256'] == sha(a.flatten_proof)
    assert manifest['interface_proof_sha256'] == sha(a.interface_proof)
    inputs = [original, adapted, a.database, a.flatten_proof, a.interface_proof, a.dummy_proof,
              a.workers / 'summary.json', Path(__file__)]
    for worker in manifest['workers']:
        path = a.workers / worker['file']
        assert sha(path) == worker['prepared_sha256']
        inputs.append(path)
    dummy = json.loads(a.dummy_proof.read_text())
    assert dummy['status'] == 'passed independent three-dummy source/native-terminal proof'
    assert len(dummy['source_occurrences']) == len(dummy['physical_instances']) == 3
    assert 'ae62bf68aa001144c08a37c58ac3553c6e5f2013a6824b340218e84962066aca' in dummy['inputs'].values()
    assert all(set(r['terminal_nodes'].values()) == {'VDD'} for r in dummy['source_occurrences'])
    lifecycle = bulk / 'fullchip-pin-id-controls-20260923-r4/summary.json'
    assert sha(lifecycle) == '048708774b10584925c6423b81c76382b108648fd2597e838a9fc15103c7233f'
    inputs.append(lifecycle)
    command = ['klayout', '-b', '-r', str(a.workers / 'compare_saved_flat.rb'),
               '-rd', 'original=' + str(original), '-rd', 'adapted=' + str(adapted),
               '-rd', 'database=' + str(a.database), '-rd', 'variant=' + a.variant,
               '-rd', 'physical_interface=' + str(a.interface_proof), '-rd', 'output_dir=' + str(a.output / 'diagnostic')]
    if a.exclude_dummies:
        folder = bulk / 'io-three-dummy-reference-20260923-r1'
        preparation = json.loads((folder / 'summary.json').read_text())
        arm = 'original' if a.variant == 'original' else 'tap_prefix'
        row, = [r for r in preparation['references'] if r['variant'] == arm]
        reference = folder / row['output_name']
        base = original if a.variant == 'original' else adapted
        assert sha(reference) == row['output_sha256'] and sha(base) == row['input_sha256']
        raw = reference.read_bytes(); offset = row['byte_offset']
        assert raw[:offset] + (row['removed_definition_line'] + '\n').encode() + raw[offset:] == base.read_bytes()
        assert row['source_occurrences'] == dummy['source_occurrences']
        command.extend(['-rd', 'comparison_reference=' + str(reference)])
        inputs.extend([reference, folder / 'summary.json'])
    hashes = {str(q): sha(q) for q in inputs}
    a.output.mkdir(parents=True)
    (a.output / 'source.py').write_bytes(Path(__file__).read_bytes())
    result = dict(status='running saved comparison', inputs=hashes, command=command,
                  resource_gate_sha256=sha(a.resource_gate), variant=a.variant,
                  exclusion='three independently proved all-VDD physical dummies' if a.exclude_dummies else 'none',
                  watchdog_s=180, reservation_GiB=8, memory_enforced=False,
                  native_extraction='not run in this diagnostic', canonical_source_changes='not applicable')
    output = a.output / 'summary.json'
    output.write_text(json.dumps(result, indent=2) + '\n')
    with (a.output / 'console.log').open('x') as log:
        run = run_bounded(command, log, a.output / 'run.json', 180, cwd=ROOT, interval_s=3)
    report = a.output / 'diagnostic/summary.json'
    parsed = json.loads(report.read_text()) if report.exists() else None
    unchanged = all(sha(Path(q)) == h for q, h in hashes.items())
    complete = run['status'] == 'completed' and run['returncode'] == 0 and parsed is not None and 'engine_equivalent' in parsed and unchanged
    result.update(status='completed diagnostic; inspect strict outcome' if complete else 'failed diagnostic harness or timeout',
                  run=run, inputs_unchanged=unchanged, diagnostic_report=parsed,
                  strict_comparison=parsed['status'] if complete else 'not completed',
                  fullchip_acceptance='not established by diagnostic', output_bytes=sum(q.stat().st_size for q in a.output.rglob('*') if q.is_file()))
    output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('inputs', 'diagnostic_report')}, indent=2))
    raise SystemExit(0 if complete else 1)


if __name__ == '__main__':
    main()
