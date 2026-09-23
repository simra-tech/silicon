#!/usr/bin/env python3
"""Portable exact clips, local field evidence and retained failed context gate."""
import argparse
import ast
import getpass
import gzip
import hashlib
import io
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
SOURCES = ['SENSE_FEED_FIELD_PROPOSAL_20260923.md',
    'SENSE_FEED_FIELD_PILOT_FREEZE_20260923.md', 'SENSE_FEED_FIELD_REVIEW_20260923.md',
    'prepare_sense_feed_field_inventory.py', 'prepare_sense_feed_field_clips.py',
    'sense_feed_field_math.py', 'test_sense_feed_field_math.py',
    'run_sense_feed_field_pilot.py', 'export_sense_feed_field_evidence.py']


def sha(data): return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bulk-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--group', action='append', required=True)
    parser.add_argument('--receipt', action='append', default=[])
    args = parser.parse_args()
    args.bulk_root = args.bulk_root.resolve(); args.output = args.output.resolve()
    assert not args.output.exists() and HERE in args.output.parents
    pairs = []; omitted = []
    for name in args.group:
        assert Path(name).name == name
        base = args.bulk_root/name; assert base.is_dir()
        for path in sorted(base.rglob('*')):
            if not path.is_file(): continue
            assert not path.is_symlink()
            relative = Path(name)/path.relative_to(base)
            # Backend binary scratch is not necessary to reproduce the four tiny clips.
            if path.suffix in ('.oas', '.lvsdb') or path.name.endswith(('.gds.gz', '.rdb.gz')):
                raw = path.read_bytes()
                omitted.append(dict(path=str(relative), sha256=sha(raw), bytes=len(raw),
                    reason='Backend scratch; exact input clip, command, capacitor graph and native membership retained'))
            elif path.suffix in ('.json', '.py', '.log', '.gds', '.cir', '.spice', '.csv', '.txt'):
                pairs.append((path, relative))
            else:
                raise AssertionError('Unclassified pilot artifact: '+str(relative))
    for spec in args.receipt:
        name, value = spec.split('=', 1); assert Path(name).name == name
        for filename in ('check.json', 'check.log'):
            pairs.append((Path(value)/filename, Path('receipts')/name/filename))
    assert len({str(rel) for _, rel in pairs}) == len(pairs)
    args.output.mkdir(parents=True); records = []
    for source, relative in pairs:
        assert source.is_file() and not source.is_symlink()
        raw = source.read_bytes(); binary = source.suffix == '.gds'; portable = raw
        if not binary:
            text = raw.decode()
            for old, new in [(str(args.bulk_root), '${BULK}'), (str(REPO), '${REPO}'),
                             ('/work/', '${REPO}/'), ('.private/research/verification/', '${RECEIPTS}/')]:
                text = text.replace(old, new)
            assert getpass.getuser() not in text and '/home/' not in text and '/opt/sim/' not in text, relative
            portable = text.encode()
            if source.suffix == '.py': ast.parse(text)
            if source.suffix == '.json': json.loads(text)
        compressed = not binary and len(portable) > 262144
        if compressed:
            buffer = io.BytesIO()
            with gzip.GzipFile(fileobj=buffer, mode='wb', mtime=0) as stream: stream.write(portable)
            data = buffer.getvalue(); relative = Path(str(relative)+'.gz')
        else: data = portable
        destination = args.output/relative; destination.parent.mkdir(parents=True, exist_ok=True)
        assert not destination.exists(); destination.write_bytes(data)
        records.append(dict(path=str(destination.relative_to(REPO)), original_sha256=sha(raw),
            portable_decoded_sha256=sha(portable), exported_sha256=sha(data), bytes=len(data),
            compressed=compressed, binary_exact=binary, path_only_sanitized=raw != portable))
    manifest = dict(status='passed portable export; original context gate FAILED, no adoption',
        artifacts=records, omitted=omitted, groups=args.group,
        transformation='Path-prefix-only text sanitization; optional deterministic gzip; GDS exact')
    (args.output/'export_manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    paths = sorted([HERE/name for name in SOURCES]+[p for p in args.output.rglob('*') if p.is_file()])
    rows = [dict(path=str(p.relative_to(REPO)), sha256=sha(p.read_bytes()), bytes=p.stat().st_size) for p in paths]
    inventory = dict(status='frozen bounded field evidence, four extraction/eight AC PASS, original context FAIL',
        files=rows, file_count=len(rows), total_bytes=sum(row['bytes'] for row in rows))
    destination = args.output/'commit_inventory.json'
    destination.write_text(json.dumps(inventory, indent=2)+'\n')
    print(json.dumps(dict(path=str(destination.relative_to(REPO)), sha256=sha(destination.read_bytes()),
        file_count=len(rows), total_bytes=inventory['total_bytes']), indent=2))


if __name__ == '__main__': main()
