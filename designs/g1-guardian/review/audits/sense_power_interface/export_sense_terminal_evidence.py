#!/usr/bin/env python3
"""Portable completed terminal-method evidence; original hashes retained."""
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
SOURCES = [
    'prepare_sense_distributed_coupon.py', 'analyze_sense_distributed_coupon.py',
    'run_sense_distributed_coupon.py', 'test_sense_distributed_coupon.py',
    'inspect_sense_gate_boundary.py', 'prepare_sense_contact_footprints.py',
    'extract_sense_contact_topology.py', 'classify_sense_remaining_contacts.py',
    'prepare_sense_all_contact_footprints.py', 'export_sense_terminal_evidence.py',
    'SENSE_METAL_TOPOLOGY_20260923.md', 'SENSE_DISTRIBUTED_TERMINAL_CONTRACT_20260923.md']


def sha(raw): return hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bulk-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--group', action='append', required=True)
    parser.add_argument('--receipt', action='append', default=[])
    parser.add_argument('--artifact', action='append', default=[])
    args = parser.parse_args(); args.output = args.output.resolve()
    assert not args.output.exists() and HERE in args.output.parents
    pairs = []
    for name in args.group:
        assert Path(name).name == name
        base = args.bulk_root/name; assert base.is_dir()
        for path in sorted(base.rglob('*')):
            if path.is_file(): pairs.append((path, Path(name)/path.relative_to(base)))
    for spec in args.receipt:
        name, value = spec.split('=', 1); assert Path(name).name == name
        base = Path(value)
        for filename in ('check.json', 'check.log'):
            pairs.append((base/filename, Path('receipts')/name/filename))
    for spec in args.artifact:
        name, value = spec.split('=', 1); assert Path(name).name == name
        pairs.append((Path(value), Path('observations')/name))
    assert len({str(rel) for _, rel in pairs}) == len(pairs)
    args.output.mkdir(parents=True); records = []
    for source, relative in pairs:
        assert source.is_file() and not source.is_symlink()
        raw = source.read_bytes(); decoded = gzip.decompress(raw) if source.suffix == '.gz' else raw
        text = decoded.decode()
        for old, new in [(str(args.bulk_root.resolve()), '${BULK}'), (str(REPO), '${REPO}'),
                         ('/work/', '${REPO}/'), ('.private/research/verification/', '${RECEIPTS}/')]:
            text = text.replace(old, new)
        assert getpass.getuser() not in text and '/home/' not in text and '/opt/sim/' not in text, relative
        portable = text.encode()
        if source.suffix == '.py': ast.parse(text)
        json_name = source.name[:-3] if source.suffix == '.gz' else source.name
        if json_name.endswith('.json'): json.loads(text)
        compressed = source.suffix == '.gz' or len(portable) > 262144
        if compressed:
            buffer = io.BytesIO()
            with gzip.GzipFile(fileobj=buffer, mode='wb', mtime=0) as stream:
                stream.write(portable)
            data = buffer.getvalue()
            if relative.suffix != '.gz': relative = Path(str(relative)+'.gz')
        else: data = portable
        destination = args.output/relative; destination.parent.mkdir(parents=True, exist_ok=True)
        assert not destination.exists(); destination.write_bytes(data)
        records.append(dict(path=str(destination.relative_to(REPO)), original_sha256=sha(raw),
                            original_decoded_sha256=sha(decoded), portable_decoded_sha256=sha(portable),
                            exported_sha256=sha(data), bytes=len(data), compressed=compressed,
                            path_only_sanitized=decoded != portable))
    manifest = dict(status='passed portable terminal-method export; applicability and exact coupon parity failures retained',
                    artifacts=records, groups=args.group,
                    transformation='Only workspace/bulk/private-receipt prefixes replaced; optional lossless deterministic gzip; original and decoded hashes retained')
    (args.output/'export_manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    paths = sorted([HERE/name for name in SOURCES]+[p for p in args.output.rglob('*') if p.is_file()])
    rows = [dict(path=str(p.relative_to(REPO)), sha256=sha(p.read_bytes()), bytes=p.stat().st_size) for p in paths]
    inventory = dict(status='frozen source-held terminal topology and failed adapter evidence; no adoption',
                     files=rows, file_count=len(rows), total_bytes=sum(r['bytes'] for r in rows))
    destination = args.output/'commit_inventory.json'; destination.write_text(json.dumps(inventory,indent=2)+'\n')
    print(json.dumps(dict(path=str(destination.relative_to(REPO)), sha256=sha(destination.read_bytes()),
                         file_count=len(rows), total_bytes=inventory['total_bytes']),indent=2))


if __name__ == '__main__': main()
