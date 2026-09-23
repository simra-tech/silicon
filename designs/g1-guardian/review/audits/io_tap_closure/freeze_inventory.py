#!/usr/bin/env python3
"""Freeze exact owned IO audit files for coordinator review; never stage/commit."""
import argparse
import ast
import getpass
import hashlib
import json
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument('--inventory', type=Path, required=True)
a = ap.parse_args()
assert not a.inventory.exists()
folder = Path(__file__).resolve().parent
root = Path.cwd().resolve()
rows = []
for p in sorted(folder.rglob('*')):
    if not p.is_file() or '__pycache__' in p.parts or p.suffix == '.pyc':
        continue
    assert not p.is_symlink()
    data = p.read_bytes()
    forbidden = [getpass.getuser().encode(), b'/' + b'home/', b'/opt/' + b'sim/', b'.' + b'private/']
    assert all(token not in data for token in forbidden), str(p)
    if p.suffix == '.py':
        ast.parse(data.decode())
    if p.suffix == '.json':
        json.loads(data.decode())
    rows.append(dict(path=str(p.relative_to(root)), sha256=hashlib.sha256(data).hexdigest(), bytes=len(data)))
result = dict(groups={'IO_tap_source_applicability': rows}, count=len(rows),
              bytes=sum(row['bytes'] for row in rows), privacy_AST_JSON='passed',
              strict_IO_LVS='failed prior result; not rerun',
              original_failed_helpers='retained')
a.inventory.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: v for k, v in result.items() if k != 'groups'}, indent=2))
