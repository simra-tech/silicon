#!/usr/bin/env python3
"""Bounded CPU1 saved-data topology witness with fresh shared-resource gate."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[6]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--receipt', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert not a.receipt.exists() and not a.output.exists()
    assert os.environ['G1_CPUSET'] == '1' and os.environ['G1_CPUS'] == '1'
    a.receipt.mkdir(parents=True)
    (a.receipt / 'runner.py').write_bytes(Path(__file__).read_bytes())
    bulk = Path(os.environ['G1_RESULTS_ROOT'])
    gate = a.receipt / 'resources.json'
    command = [sys.executable, str(ROOT / '.private' / 'research/verification/check_resources.py'),
               '--output', str(gate), '--expected-growth-gib', '.03',
               '--external-root', str(bulk), '--external-growth-gib', '.10']
    with (a.receipt / 'resources.log').open('x') as log:
        assert subprocess.run(command, stdout=log, stderr=subprocess.STDOUT).returncode == 0
    resource = json.loads(gate.read_text())
    assert resource['status'] == 'passed' and resource['project_cpu_budget'] >= 44
    assert resource['ram_available_bytes'] >= 8 * 1024**3
    paths = dict(database=bulk / 'full-io-marker-lvs-original-20260923-r1/reports/io_marker_native.lvsdb',
                 ports=bulk / 'full-io-marker-ports-20260923-r2/summary.json',
                 original=bulk / 'fullchip-name-interface-20260923-r1/g1_chip_top_layout_name_only.cdl',
                 adapted=bulk / 'fullchip-tap-prefix-adapter-20260923-r1/fullchip_tap_prefix_only.cdl',
                 reader=HERE.parent / 'probe_tap_adapter.rb')
    hashes = {str(q): hashlib.sha256(q.read_bytes()).hexdigest() for q in list(paths.values()) + [HERE / 'audit_partition.rb']}
    def runtime_path(path):
        return str(path).replace(str(ROOT), '/work', 1) if str(path).startswith(str(ROOT) + '/') else str(path)
    command = ['flow/run.sh', 'klayout', '-b', '-r', runtime_path(HERE / 'audit_partition.rb')]
    for k, v in list(paths.items()) + [('output_dir', a.output)]:
        command += ['-rd', k + '=' + runtime_path(v)]
    sys.path.insert(0, str(ROOT / 'designs/g1-guardian/blocks/g1_top/sim'))
    from run_bounded import run_bounded
    with (a.receipt / 'run.log').open('x') as log:
        state = run_bounded(command, log, a.receipt / 'run.json', 120,
                            metadata=dict(inputs=hashes, command=command, CPU=1,
                                          reservation_GiB=8, memory_enforced=False))
    unchanged = all(hashlib.sha256(Path(q).read_bytes()).hexdigest() == h for q,h in hashes.items())
    print(json.dumps(dict(run=state, inputs_unchanged=unchanged), indent=2))
    assert unchanged and state['status'] == 'completed' and state['returncode'] == 0


if __name__ == '__main__':
    main()
