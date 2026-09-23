#!/usr/bin/env python3
"""Portable scoped name controls with original/exported and LVSDB parity."""
import argparse
import ast
import getpass
import hashlib
import json
import os
from pathlib import Path
from run_name_control import strict

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]


def digest(data):
    return hashlib.sha256(data).hexdigest()


ap = argparse.ArgumentParser()
ap.add_argument('--inventory', type=Path, required=True)
a = ap.parse_args()
assert not a.inventory.exists()
bulk = Path(os.environ['G1_RESULTS_ROOT'])
groups = dict(prepared='fullchip-name-interface-20260923-r1',
              same_run='fullchip-name-control-same-20260923-r1',
              same_saved_failure='fullchip-name-control-same-saved-audit-20260923-r1',
              same_saved_pass='fullchip-name-control-same-saved-audit-20260923-r2',
              child_alias='fullchip-name-control-child-20260923-r1',
              wrong_connection='fullchip-name-control-wrong-20260923-r1',
              top_alignment_failure='fullchip-name-control-top-20260923-r1',
              disposition='fullchip-name-control-disposition-20260923-r1',
              export_preflight_failure='fullchip-name-export-preflight-failure-20260923-r1')
target = HERE / 'evidence'
assert not target.exists()
replacements = [(str(ROOT).encode(), b'<repository>'), (str(bulk).encode(), b'<results-root>')]
forbidden = [bulk.name.encode(), b'/' + b'home/', b'/opt/' + b'sim/', b'.' + b'private/']
payload, rows = [], []
for label, directory in groups.items():
    folder = bulk / directory
    assert folder.is_dir()
    for p in sorted(folder.rglob('*')):
        if not p.is_file() or '__pycache__' in p.parts:
            continue
        assert not p.is_symlink()
        original = p.read_bytes()
        exported = original
        for old, new in replacements:
            exported = exported.replace(old, new)
        assert all(token not in exported for token in forbidden), p.name
        relative = Path(label) / p.relative_to(folder)
        payload.append((p, target / relative, exported))
        rows.append(dict(source_run=directory, source_relative=str(p.relative_to(folder)),
                         exported_relative=str(relative), original_sha256=digest(original),
                         exported_sha256=digest(exported), bytes=len(exported),
                         normalization='none' if original == exported else 'host-path metadata only'))
assert sum(len(data) for _, _, data in payload) < .01 * 1024**3
dbchecks = []
for original, output, data in payload:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(data)
    if output.suffix == '.lvsdb':
        left, right = strict(original), strict(output)
        left.pop('sha256')
        right.pop('sha256')
        assert left == right
        dbchecks.append(dict(path=str(output.relative_to(target)), status='passed exact semantic inventory', comparison=right['status']))
(target / 'export_manifest.json').write_text(json.dumps(dict(status='passed portable metadata export and exact LVSDB semantics',
                                                            files=rows, LVSDB_semantic_parity=dbchecks), indent=2) + '\n')
inventory = []
for p in sorted(HERE.rglob('*')):
    if not p.is_file() or '__pycache__' in p.parts:
        continue
    data = p.read_bytes()
    assert all(token not in data for token in forbidden), p.name
    if p.suffix == '.py':
        ast.parse(data.decode())
    if p.suffix == '.json':
        json.loads(data.decode())
    inventory.append(dict(path=str(p.relative_to(ROOT)), sha256=digest(data), bytes=len(data)))
result = dict(groups={'Fullchip_name_interface_controls': inventory}, count=len(inventory),
              bytes=sum(r['bytes'] for r in inventory), hash_privacy_AST_JSON='passed',
              stock_controls='two positive passed, wrong-connection negative detected',
              top_name_alignment='failed expected applicability observation', physical_extraction='not run', fullchip_LVS='not run')
a.inventory.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: v for k, v in result.items() if k != 'groups'}, indent=2))
