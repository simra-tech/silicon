#!/usr/bin/env python3
"""Freeze completed preparation/control evidence, excluding running fullCCr3."""
import argparse
import datetime
import getpass
import gzip
import hashlib
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--resource-gate', type=Path, required=True)
    parser.add_argument('--proof-failure-json', type=Path, required=True)
    parser.add_argument('--inventory', type=Path, required=True)
    args = parser.parse_args()
    gate = json.loads(args.resource_gate.read_text())
    stamp = datetime.datetime.strptime(gate['utc'].replace('+00:00', ''), '%Y-%m-%dT%H:%M:%S.%f').replace(tzinfo=datetime.timezone.utc)
    assert gate['status'] == 'passed' and gate['expected_growth_gib'] >= .1
    assert 0 <= (datetime.datetime.now(datetime.timezone.utc) - stamp).total_seconds() < 1800
    bulk = Path(os.environ['G1_RESULTS_ROOT'])
    groups = {}
    for revision in (1, 2, 3):
        groups['prepare/r' + str(revision)] = bulk / ('bgr-pex-prepare-20260922-r' + str(revision))
    for revision in (1, 2):
        groups['cc_failure/r' + str(revision)] = bulk / ('bgr-cpex-20260922-r' + str(revision))
    groups.update({'controls/r1': bulk / 'bgr-cpex-controls-20260922-r1',
                   'union_pilot/geometry': bulk / 'bgr-union-pilot-geometry-20260922-r1',
                   'union_pilot/check': bulk / 'bgr-union-pilot-check-20260922-r1',
                   'union_full/geometry': bulk / 'bgr-union-full-geometry-20260922-r1'})
    for group, base in groups.items():
        status = json.loads((base / 'summary.json').read_text())['status']
        assert status != 'running', (group, status)
    replacements = [(str(ROOT).encode(), b'<repository>'), (str(bulk).encode(), b'<results-root>'),
                    (str(Path.home()).encode(), b'<home>')]
    sensitive = [old for old, _ in replacements] + [getpass.getuser().encode()]
    rows = []
    payload = []
    def add(group, relative, raw, binary=False, reconstructed=False):
        data = raw
        if not binary:
            for old, new in replacements:
                data = data.replace(old, new)
        assert all(token not in data for token in sensitive), (group, relative)
        if relative.endswith('.gz'):
            unpacked = gzip.decompress(data)
            assert all(token not in unpacked for token in sensitive), (group, relative, 'gzip payload')
        if relative.endswith('.json'):
            json.loads(data.decode())
        target = group + '/' + relative
        payload.append((target, data))
        rows.append({'source_group': group, 'source_relative': relative, 'export': target,
                     'original_sha256': sha(raw), 'export_sha256': sha(data), 'original_bytes': len(raw),
                     'export_bytes': len(data), 'host_prefix_redacted': data != raw,
                     'failed_script_reconstructed_from_hash_bound_diff': reconstructed})
    for group, base in groups.items():
        for path in sorted(base.rglob('*')):
            if not path.is_file():
                continue
            assert path.suffix != '.pyc'
            add(group, str(path.relative_to(base)), path.read_bytes(), path.suffix in ('.gds', '.oas', '.gz'))
    failure = json.loads(args.proof_failure_json.read_text())
    assert failure['status'] == 'failed' and failure['script_sha256'] == 'c09059ad9056d55c6474e6302871d2413d1d0de2254348e751531f89e159083b'
    add('proof_reporter_r1', 'failure.json', args.proof_failure_json.read_bytes())
    current = (HERE / 'prove_grounded_dummies.py').read_text()
    old = current.replace('import re\n', '').replace(
        "    header = re.search(r'(?m)^\\.subckt\\s+npn13G2\\s+c\\s+b\\s+e\\s+bn\\s*$', model)\n    assert header is not None\n    begin = header.start()\n",
        "    begin = model.index('.subckt npn13G2 c b e bn\\n')\n")
    assert sha(old.encode()) == failure['script_sha256']
    add('proof_reporter_r1', 'prove_grounded_dummies.py', old.encode(), reconstructed=True)
    total = sum(len(data) for _, data in payload)
    assert total < .1 * 2**30 and gate['effective_storage_free_bytes'] > total + 8 * 2**30
    out = HERE / 'evidence/pex-preparation-20260922-r1'
    out.mkdir(parents=True, exist_ok=False)
    for relative, data in payload:
        path = out / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        assert sha(path.read_bytes()) == sha(data)
    manifest = {'status': 'passed export/privacy/JSON gates', 'artifacts': rows, 'artifact_count': len(rows),
                'artifact_bytes': total, 'original_artifacts_unchanged': True,
                'redaction': 'Host path prefixes in text only; binaries byte-exact. Original and exported hashes retained.',
                'failed_proof_script': 'Exact inverse whitespace-parser diff reconstruction, SHA matches saved original failure receipt; not a rerun.',
                'fullCCr3': 'Excluded: live subsequent execution, not part of this completed milestone.',
                'script_sha256': sha(Path(__file__).read_bytes())}
    (out / 'export_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    names = ['PEX_CONTRACT_20260922.md', 'PEX_PREPARATION_RESULTS_20260922.md', 'GROUNDED_DUMMY_EXTRACTION_20260922.md',
             'audit_unsimplified.py', 'prepare_pex_view.py', 'run_pex_prepare.py', 'prove_grounded_dummies.py',
             'run_pex_prepare_r2.py', 'run_cpex.py', 'trace_kpex.py', 'prepare_capacitance_views.py',
             'prepare_capacitance_controls.py', 'return_wire_sensitivity.py', 'inspect_cpex_geometry.py',
             'test_capacitance_helpers.py', 'prepare_union_view.py', 'run_union_pilot.py', 'run_union_full_prepare.py',
             'export_pex_preparation.py']
    files = [HERE / name for name in names] + [path for path in out.rglob('*') if path.is_file()]
    inventory = {'groups': {'BGR_extraction_preparation_controls': [
        {'path': str(path.relative_to(ROOT)), 'sha256': sha(path.read_bytes()), 'bytes': path.stat().st_size}
        for path in sorted(files)]}}
    assert not args.inventory.exists()
    args.inventory.write_text(json.dumps(inventory, indent=2) + '\n')
    print(json.dumps({'status': manifest['status'], 'files': len(files), 'bytes': sum(path.stat().st_size for path in files)}, indent=2))


if __name__ == '__main__':
    main()
