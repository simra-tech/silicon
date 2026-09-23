#!/usr/bin/env python3
"""Export exact source-only reference evidence; no host paths or staging."""
import argparse
import ast
import getpass
import hashlib
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--inventory', type=Path, required=True)
    a = ap.parse_args()
    assert not a.inventory.exists()
    bulk = Path(os.environ['G1_RESULTS_ROOT'])
    groups = dict(preparation='fullchip-source-reference-20260923-r1',
                  audit_failed_r1='fullchip-source-reference-audit-20260923-r1',
                  audit_passed_r2='fullchip-source-reference-audit-20260923-r2',
                  native_interface='fullchip-source-native-interface-20260923-r1')
    expected = dict(preparation='passed preparation only; independent mapping audit pending',
                    audit_failed_r1='failed independent source/reference mapping audit',
                    audit_passed_r2='passed independent saved source/reference mapping audit; not LVS',
                    native_interface='passed exact native instance/master/name/transform correspondence; not LVS')
    forbidden = [getpass.getuser().encode(), b'/' + b'home/', b'/opt/' + b'sim/', b'.' + b'private/']
    exports = []
    destination = HERE / 'evidence/current-reference-20260923-r1'
    assert not destination.exists()
    payload = []
    for label, directory in groups.items():
        folder = bulk / directory
        assert json.loads((folder / 'summary.json').read_text())['status'] == expected[label]
        for path in sorted(folder.rglob('*')):
            if not path.is_file() or '__pycache__' in path.parts:
                continue
            assert not path.is_symlink()
            data = path.read_bytes()
            assert all(token not in data for token in forbidden), str(path.relative_to(bulk))
            relative = Path(label) / path.relative_to(folder)
            payload.append((relative, data))
            exports.append(dict(source_run=directory, source_relative=str(path.relative_to(folder)),
                                exported_relative=str(relative), original_sha256=sha(data),
                                exported_sha256=sha(data), bytes=len(data), normalization='none; byte-identical'))
    assert sum(len(d) for _, d in payload) < .03 * 1024**3
    for relative, data in payload:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    (destination / 'export_manifest.json').write_text(json.dumps(dict(status='passed exact portable export', files=exports), indent=2) + '\n')
    rows = []
    for p in sorted(HERE.rglob('*')):
        if not p.is_file() or '__pycache__' in p.parts:
            continue
        data = p.read_bytes()
        assert all(token not in data for token in forbidden), str(p.relative_to(ROOT))
        if p.suffix == '.py':
            ast.parse(data.decode())
        if p.suffix == '.json':
            json.loads(data.decode())
        rows.append(dict(path=str(p.relative_to(ROOT)), sha256=sha(data), bytes=len(data)))
    result = dict(groups={'Current_fullchip_source_reference': rows}, count=len(rows),
                  bytes=sum(r['bytes'] for r in rows), hash_privacy_AST_JSON='passed',
                  fullchip_LVS='not run', known_IO_tap_comparison='failed prior result',
                  original_failed_audit='preserved')
    a.inventory.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'groups'}, indent=2))


if __name__ == '__main__':
    main()
