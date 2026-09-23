#!/usr/bin/env python3
"""Bounded in-memory representation diagnostic, never a native LVS pass."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
sys.path.insert(0, str(ROOT / 'designs/g1-guardian/blocks/g1_top/sim'))
from run_bounded import run_bounded


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--resource-gate', type=Path, required=True)
    ap.add_argument('--variant', choices=('original', 'adapter'), required=True)
    ap.add_argument('--diagnostic', choices=('comparison', 'scope'), default='comparison')
    ap.add_argument('--physical-interface', action='store_true')
    ap.add_argument('--output', type=Path, required=True)
    a = ap.parse_args()
    assert not a.output.exists()
    a.output.mkdir(parents=True)
    gate = json.loads(a.resource_gate.read_text())
    age = (datetime.datetime.now(datetime.timezone.utc) - datetime.datetime.fromisoformat(gate['utc'])).total_seconds()
    assert gate['status'] == 'passed' and gate['project_cpu_budget'] >= 45 and 0 <= age < 1800
    assert set(os.sched_getaffinity(0)) == {1}
    assert gate['ram_available_bytes'] > 8 * 1024**3
    bulk = Path(os.environ['G1_RESULTS_ROOT'])
    original = bulk / 'fullchip-name-interface-20260923-r1/g1_chip_top_layout_name_only.cdl'
    adapted = bulk / 'fullchip-tap-prefix-adapter-20260923-r1/fullchip_tap_prefix_only.cdl'
    database = bulk / 'fullchip-native-strict-lvs-20260923-r2/reports/sealed_native.lvsdb'
    proof = bulk / 'fullchip-api-flatten-proof-20260923-r3/summary.json'
    assert sha(proof) == '6fa352a04e0830fdd9df9a88cfcfae505ff718446c2eeab9cc7c4ecf55e143c3'
    pdata = json.loads(proof.read_text())
    assert pdata['script_sha256'] == sha(HERE / 'audit_api_flatten.py')
    assert pdata['status'].startswith('passed exact primitive/terminal-graph')
    assert pdata['complete_bijective_terminal_graph'] and pdata['all_binary64_parameters_exact']
    assert pdata['terminal_connections'] == 245160 and pdata['after_nets'] == 30929
    assert pdata['database_sha256'] == sha(database)
    worker = HERE / ('compare_saved_flat.rb' if a.diagnostic == 'comparison' else 'probe_substrate_scope.rb')
    cap = 180 if a.diagnostic == 'comparison' else 120
    inputs = {str(p): sha(p) for p in [original, adapted, database, proof, worker,
                                      HERE / 'probe_tap_adapter.rb', Path(__file__)]}
    interface = bulk/'fullchip-saved-interface-probe-20260923-r1/probe/summary.json'
    if a.physical_interface:
        assert a.diagnostic == 'comparison'
        assert sha(interface) == 'e7f9c8eef1ca1631aaa9fd7c2fdbc142bf5f7c3fe33afb1dc4eefc831c308177'
        for p in (interface, HERE/'physical_interface_metadata.rb'):
            inputs[str(p)] = sha(p)
    command = ['klayout', '-b', '-r', str(worker), '-rd', 'original=' + str(original),
               '-rd', 'adapted=' + str(adapted), '-rd', 'database=' + str(database),
               '-rd', 'variant=' + a.variant, '-rd', 'output_dir=' + str(a.output / 'diagnostic')]
    if a.physical_interface:
        command.extend(['-rd', 'physical_interface='+str(interface)])
    (a.output / 'runner_snapshot.py').write_bytes(Path(__file__).read_bytes())
    (a.output / 'worker_snapshot.rb').write_bytes(worker.read_bytes())
    result = dict(status='running diagnostic', inputs=inputs, command=command, watchdog_seconds=cap,
                  memory_reservation_GiB=8, memory_enforced=False, resource_gate_sha256=sha(a.resource_gate),
                  native_LVS='not run', electrical_simulation='not applicable', variant=a.variant, diagnostic=a.diagnostic)
    result['physical_interface_metadata_only'] = a.physical_interface
    (a.output / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    with (a.output / 'console.log').open('x') as log:
        run = run_bounded(command, log, a.output / 'run.json', cap, cwd=ROOT, interval_s=3)
    report = a.output / 'diagnostic/summary.json'
    parsed = json.loads(report.read_text()) if report.exists() else None
    unchanged = all(sha(Path(p)) == h for p, h in inputs.items())
    observed = parsed is not None and ('engine_equivalent' in parsed if a.diagnostic == 'comparison'
                                      else parsed.get('status','').startswith('passed source scope observation'))
    complete = run['status'] == 'completed' and run['returncode'] == 0 and observed and unchanged
    result.update(status='completed diagnostic; inspect strict outcome' if complete else 'failed diagnostic harness or timeout',
                  run=run, inputs_unchanged=unchanged, diagnostic_report=parsed,
                  output_bytes=sum(p.stat().st_size for p in a.output.rglob('*') if p.is_file()))
    (a.output / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('inputs', 'diagnostic_report')}, indent=2))
    raise SystemExit(0 if complete else 1)


if __name__ == '__main__':
    main()
