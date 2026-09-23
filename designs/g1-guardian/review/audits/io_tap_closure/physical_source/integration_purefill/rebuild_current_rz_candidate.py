#!/usr/bin/env python3
"""One-command regeneration of the pinned current RZ100 physical candidate.

Run inside flow/run.sh with one allocated CPU and a fresh resource gate. This
only regenerates geometry and proofs; stock LVS/DRC and adoption are not run.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys

import current_projection_bindings as projection
import current_rz_bindings as binding

HERE = Path(__file__).resolve().parent
GIB = 1024 ** 3
REQUIRED_CHECKS = ('cpu_budget_positive', 'quota_growth_and_reserve',
                   'inodes_available', 'ram_available',
                   'coordinated_CPU_reservations_fit',
                   'external_allocation_growth', 'external_inodes')


def pinned(root, spec):
    relative, digest = spec
    path = root / relative
    if not path.is_file() or binding.sha(path) != digest:
        raise ValueError('pinned input missing or changed: ' + relative)
    return path


def gate_ok(path, cpu, now=None):
    gate = json.loads(path.read_text())
    now = now or datetime.now(timezone.utc)
    stamp = gate['utc'].replace('Z', '+0000')
    if stamp[-3] == ':':
        stamp = stamp[:-3] + stamp[-2:]
    sampled = datetime.strptime(stamp,
                                '%Y-%m-%dT%H:%M:%S.%f%z')
    if gate['status'] != 'passed' or not all(gate['checks'].get(k) is True for k in REQUIRED_CHECKS):
        raise ValueError('resource gate failed')
    if not 0 <= (now - sampled).total_seconds() <= 300:
        raise ValueError('resource gate is stale')
    if cpu not in gate['coordinated_allocation']['cpus']:
        raise ValueError('CPU absent from coordinated allocation')
    if gate['ram_available_bytes'] < 16 * GIB:
        raise ValueError('RAM reservation unavailable')
    external = gate['external_allocation']
    if external['available_bytes'] < 2 * GIB or external['inodes_free'] < 1000:
        raise ValueError('bulk growth or inodes unavailable')
    return gate


def plan(root, out):
    original = root / projection.ORIGINAL_GDS
    inputs = [original, pinned(root, binding.ORIGINAL_SOURCE),
              pinned(root, binding.PIN_PATHS), pinned(root, binding.PORT_OVERLAP),
              pinned(root, binding.PORT_REACH), pinned(root, binding.PUREFILL),
              pinned(root, binding.KEEPOUT), pinned(root, binding.CANDIDATE)]
    if binding.sha(original) != projection.ORIGINAL_SHA:
        raise ValueError('original native GDS changed')
    if out.exists() or out == root or out in root.parents:
        raise ValueError('output must be fresh and not contain pinned input root')
    pure = out / 'purefill'
    keep = out / 'keepout'
    text = out / 'port_text'
    commands = [
        [sys.executable, str(HERE / 'flatten_current_fill.py'), '--output', str(pure)],
        [sys.executable, str(HERE / 'prove_rz_recipe_records.py'), '--reference', str(inputs[5]), '--candidate', str(pure / 'pure_fill_flattened.gds'), '--expected-sha', binding.PUREFILL[1], '--output', str(out / 'purefill_record_identity.json')],
        [sys.executable, str(HERE / 'keepout_rz_fill.py'), '--input', str(pure / 'pure_fill_flattened.gds'), '--output', str(keep), '--input-record-proof', str(out / 'purefill_record_identity.json')],
        [sys.executable, str(HERE / 'prove_rz_recipe_records.py'), '--reference', str(inputs[6]), '--candidate', str(keep / 'rz_fill_keepout.gds'), '--expected-sha', binding.KEEPOUT[1], '--output', str(out / 'keepout_record_identity.json')],
        [sys.executable, str(HERE / 'normalize_rz_port_text.py'), '--input', str(keep / 'rz_fill_keepout.gds'), '--input-record-proof', str(out / 'keepout_record_identity.json'), '--paths', str(inputs[2]), '--ports', str(inputs[3]), '--reach', str(inputs[4]), '--gds', str(text / 'port_text_candidate.gds'), '--proof', str(text / 'transformation.json')],
        [sys.executable, str(HERE / 'prove_rz_port_text.py'), '--reference', str(keep / 'rz_fill_keepout.gds'), '--candidate', str(text / 'port_text_candidate.gds'), '--transformation', str(text / 'transformation.json'), '--output', str(out / 'text_identity.json')],
        [sys.executable, str(HERE / 'prove_rz_recipe_records.py'), '--reference', str(inputs[7]), '--candidate', str(text / 'port_text_candidate.gds'), '--expected-sha', binding.CANDIDATE[1], '--output', str(out / 'text_record_identity.json')],
    ]
    return commands


def check_outputs(out):
    names = ('purefill', 'keepout', 'text')
    files = (out / 'purefill/pure_fill_flattened.gds', out / 'keepout/rz_fill_keepout.gds',
             out / 'port_text/port_text_candidate.gds')
    reference = (binding.PUREFILL, binding.KEEPOUT, binding.CANDIDATE)
    for name, candidate, spec in zip(names, files, reference):
        proof = json.loads((out / (name + '_record_identity.json')).read_text())
        if proof['status'] != 'passed exact GDS record identity except timestamp payloads' or proof['reference_gds_sha256'] != spec[1] or proof['reproduced_gds_sha256'] != binding.sha(candidate) or not proof['all_nondate_records_byte_exact'] or proof['other_record_differences']:
            raise ValueError(name + ' GDS record identity failed')
    pure = json.loads((out / 'purefill/analysis.json').read_text())
    keep = json.loads((out / 'keepout/summary.json').read_text())
    text = json.loads((out / 'port_text/transformation.json').read_text())
    identity = json.loads((out / 'text_identity.json').read_text())
    if pure['status'] != 'passed exact pure-fill hierarchy projection; native LVS not run' or pure['GDS_sha256'] != binding.sha(files[0]):
        raise ValueError('purefill proof failed')
    if not keep['status'].startswith('passed narrowly scoped native RZ100 filler keepout') or keep['input_gds_sha256'] != binding.sha(files[0]) or keep['output_gds_sha256'] != binding.sha(files[1]):
        raise ValueError('keepout proof failed')
    if sum(v['removed_shapes'] for v in keep['removed'].values()) != 39:
        raise ValueError('keepout shape count changed')
    if text['input_gds_sha256'] != binding.sha(files[1]) or text['output_gds_sha256'] != binding.sha(files[2]) or len(text['text_occurrences_removed']) != 86 or len(text['root_external_labels']) != 22:
        raise ValueError('text transform failed')
    if identity['status'] != 'passed serialized exact all-layer nontext identity by recursive cell/instance induction' or identity['flattened_all_layer_nontext_XOR_dbu2'] != 0 or identity['candidate_GDS_sha256'] != binding.sha(files[2]):
        raise ValueError('text identity failed')
    return dict(status='passed exact pinned geometry regeneration; LVS/DRC not run in this command',
                stage_gds_sha256=dict(zip(names, map(binding.sha, files))),
                comparison='all nondate GDS records byte-exact to accepted artifacts',
                not_run=['stock LVS', 'DRC/density/antenna', 'PEX/current IR/EM', 'electrical or tape-out adoption'])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--input-root', type=Path, required=True)
    ap.add_argument('--output-root', type=Path, required=True)
    ap.add_argument('--resource-gate', type=Path)
    ap.add_argument('--plan', action='store_true', help='read-only command and binding check')
    args = ap.parse_args()
    root, out = args.input_root.resolve(), args.output_root.resolve()
    if not root.is_dir() or not root.is_absolute() or out == Path('/'):
        raise ValueError('invalid roots')
    commands = plan(root, out)
    if args.plan:
        print(json.dumps(dict(status='not run; command plan only', commands=commands), indent=2))
        return
    cpus = os.sched_getaffinity(0)
    if len(cpus) != 1 or not args.resource_gate:
        raise ValueError('one allocated CPU and fresh resource gate required')
    gate_ok(args.resource_gate, next(iter(cpus)))
    out.mkdir(parents=True)
    env = os.environ.copy()
    env['G1_RESULTS_ROOT'] = str(root)
    for command in commands:
        subprocess.run(command, env=env, check=True)
    result = check_outputs(out)
    (out / 'rebuild_summary.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
