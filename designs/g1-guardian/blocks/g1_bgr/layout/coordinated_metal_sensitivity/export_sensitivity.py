#!/usr/bin/env python3
"""Portable conditional-OP evidence, including original preparation failures."""
import argparse
import datetime
import getpass
import hashlib
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--resource-gate', type=Path, required=True)
    ap.add_argument('--inventory', type=Path, required=True)
    a = ap.parse_args()
    gate = json.loads(a.resource_gate.read_text())
    utc = datetime.datetime.strptime(gate['utc'].replace('+00:00', ''), '%Y-%m-%dT%H:%M:%S.%f').replace(tzinfo=datetime.timezone.utc)
    assert gate['status'] == 'passed' and 0 <= (datetime.datetime.now(datetime.timezone.utc) - utc).total_seconds() < 1800
    bulk = Path(os.environ['G1_RESULTS_ROOT'])
    groups = {'preparation/r' + str(i): 'bgr-metal-sensitivity-prepare-20260922-r' + str(i) for i in (1, 2, 3)}
    groups.update({'zero_prelaunch_failure': 'bgr-metal-sensitivity-zero-20260922-r1',
                   'zero_control': 'bgr-metal-sensitivity-zero-20260922-r2',
                   'kpex': 'bgr-metal-sensitivity-kpex-20260922-r1',
                   'lef': 'bgr-metal-sensitivity-lef-20260922-r1'})
    replacements = [(str(ROOT).encode(), b'<repository>'), (str(bulk).encode(), b'<results-root>'),
                    (str(Path.home()).encode(), b'<home>'), (b'.' + b'private/', b'<private>/')]
    forbidden = [getpass.getuser().encode(), b'/' + b'home/', b'/opt/' + b'sim/', b'.' + b'private/']
    payload, rows = [], []
    for group, name in groups.items():
        folder = bulk / name
        status = json.loads((folder / 'summary.json').read_text())['status']
        assert not status.startswith('running')
        if group in ('kpex', 'lef'):
            assert status == 'passed conditional nonlinear OP completion and source controls'
            assert (folder / 'conditional_analysis.json').is_file()
        for path in sorted(folder.rglob('*')):
            if not path.is_file():
                continue
            assert path.suffix != '.pyc'
            original = path.read_bytes()
            data = original
            for old, new in replacements:
                data = data.replace(old, new)
            assert all(word not in data for word in forbidden), path
            if path.suffix == '.json':
                json.loads(data.decode())
            if path.suffix == '.jsonl':
                for line in data.decode().splitlines():
                    json.loads(line)
            target = group + '/' + str(path.relative_to(folder))
            payload.append((target, data))
            rows.append(dict(export=target, original_sha256=digest(original), export_sha256=digest(data),
                             original_bytes=len(original), export_bytes=len(data), host_prefix_redacted=data != original))
    total = sum(len(data) for _, data in payload)
    assert total < .10 * 2**30 and gate['effective_storage_free_bytes'] > total + 8 * 2**30
    out = HERE / 'evidence/conditional-op-20260922-r1'
    out.mkdir(parents=True, exist_ok=False)
    for relative, data in payload:
        path = out / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    manifest = dict(status='passed portable export/privacy/JSON checks', artifacts=rows, bytes=total,
                    exporter_sha256=digest(Path(__file__).read_bytes()),
                    scope='Two conditional full-metal nominal OP sensitivities; electrode overlap and substrate boundaries unresolved, no adoption.')
    (out / 'export_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    names = ['FIXTURE_CONTRACT_20260922.md', 'RESULTS_20260922.md', 'prepare_sensitivity.py',
             'audit_sensitivity_source.py', 'run_sensitivity.py', 'analyze_sensitivity.py', 'export_sensitivity.py']
    files = [HERE / name for name in names] + [p for p in out.rglob('*') if p.is_file()]
    for path in files:
        assert all(word not in path.read_bytes() for word in forbidden), path
    inventory = dict(groups={'BGR_conditional_nonlinear_metal_sensitivity': [
        dict(path=str(p.relative_to(ROOT)), sha256=digest(p.read_bytes()), bytes=p.stat().st_size)
        for p in sorted(files)]})
    assert not a.inventory.exists()
    a.inventory.write_text(json.dumps(inventory, indent=2) + '\n')
    print(json.dumps(dict(files=len(files), bytes=sum(p.stat().st_size for p in files), evidence_bytes=total), indent=2))


if __name__ == '__main__':
    main()
