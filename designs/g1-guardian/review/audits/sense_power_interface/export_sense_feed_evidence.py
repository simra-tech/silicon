#!/usr/bin/env python3
"""Portable source-held terminal-support and isolated feeder-remedy evidence."""
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
SOURCES = ['inspect_sense_remaining_terminal_support.py', 'SENSE_REMAINING_TERMINALS_CONTRACT_20260923.md',
    'rail_resistance_bound_math.py', 'test_rail_resistance_bound_math.py', 'bound_sense_metal_rails.py',
    'SENSE_RAIL_RESISTANCE_BOUND_PROPOSAL_20260923.md', 'build_sense_m2_feed_remedy.py',
    'audit_sense_m2_feed_reference.py', 'run_sense_m2_feed_drc.py', 'run_sense_m2_feed_lvs.py',
    'extract_sense_m2_feed_topology.py', 'bound_sense_m2_feed_rails.py', 'compare_sense_feed_bridge_cuts.py',
    'test_sense_feed_bridge_cuts.py',
    'SENSE_M2_FEED_REMEDY_CONTRACT_20260923.md', 'SENSE_M2_FEED_REVIEW_20260923.md',
    'export_sense_feed_evidence.py']


def sha(data): return hashlib.sha256(data).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bulk-root', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--group', action='append', required=True)
    p.add_argument('--receipt', action='append', default=[])
    p.add_argument('--artifact', action='append', default=[])
    a = p.parse_args(); a.output = a.output.resolve(); a.bulk_root = a.bulk_root.resolve()
    assert not a.output.exists() and HERE in a.output.parents
    pairs = []
    for name in a.group:
        assert Path(name).name == name
        base = a.bulk_root/name; assert base.is_dir()
        for path in sorted(base.rglob('*')):
            if path.is_file() and path.suffix in ('.json', '.py', '.log', '.lyrdb', '.gds', '.cdl', '.cir', '.txt', '.gz'):
                pairs.append((path, Path(name)/path.relative_to(base)))
    for spec in a.receipt:
        name, value = spec.split('=', 1); assert Path(name).name == name
        for filename in ('check.json', 'check.log'):
            pairs.append((Path(value)/filename, Path('receipts')/name/filename))
    for spec in a.artifact:
        name, value = spec.split('=', 1); assert Path(name).name == name
        pairs.append((Path(value), Path('observations')/name))
    assert len({str(rel) for _, rel in pairs}) == len(pairs)
    a.output.mkdir(parents=True); records = []
    for source, relative in pairs:
        assert source.is_file() and not source.is_symlink()
        raw = source.read_bytes(); decoded = gzip.decompress(raw) if source.suffix == '.gz' else raw
        binary = source.suffix == '.gds'
        portable = decoded
        if not binary:
            text = decoded.decode()
            for old, new in [(str(a.bulk_root), '${BULK}'), (str(REPO), '${REPO}'),
                             ('/work/', '${REPO}/'), ('.private/research/verification/', '${RECEIPTS}/')]:
                text = text.replace(old, new)
            assert getpass.getuser() not in text and '/home/' not in text and '/opt/sim/' not in text, relative
            portable = text.encode()
            if source.suffix == '.py': ast.parse(text)
            json_name = source.name[:-3] if source.suffix == '.gz' else source.name
            if json_name.endswith('.json'): json.loads(text)
        compressed = not binary and (source.suffix == '.gz' or len(portable) > 262144)
        if compressed:
            buffer = io.BytesIO()
            with gzip.GzipFile(fileobj=buffer, mode='wb', mtime=0) as stream: stream.write(portable)
            data = buffer.getvalue()
            if relative.suffix != '.gz': relative = Path(str(relative)+'.gz')
        else: data = portable
        destination = a.output/relative; destination.parent.mkdir(parents=True, exist_ok=True)
        assert not destination.exists(); destination.write_bytes(data)
        records.append(dict(path=str(destination.relative_to(REPO)), original_sha256=sha(raw),
            original_decoded_sha256=sha(decoded), portable_decoded_sha256=sha(portable),
            exported_sha256=sha(data), bytes=len(data), compressed=compressed, binary_exact=binary,
            path_only_sanitized=decoded != portable))
    manifest = dict(status='passed portable source-held feed evidence; intrinsic/current/adoption limitations retained',
        artifacts=records, groups=a.group,
        omitted='Large LVS database; exact stock hash, strict xref and extracted CDL are retained',
        transformation='Path-prefix sanitization in text only; optional deterministic lossless gzip; binary GDS byte-exact')
    (a.output/'export_manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    paths = sorted([HERE/name for name in SOURCES]+[f for f in a.output.rglob('*') if f.is_file()])
    rows = [dict(path=str(f.relative_to(REPO)), sha256=sha(f.read_bytes()), bytes=f.stat().st_size) for f in paths]
    inventory = dict(status='frozen isolated feeder and terminal-support milestone; no adoption',
        files=rows, file_count=len(rows), total_bytes=sum(r['bytes'] for r in rows))
    dest = a.output/'commit_inventory.json'; dest.write_text(json.dumps(inventory, indent=2)+'\n')
    print(json.dumps(dict(path=str(dest.relative_to(REPO)), sha256=sha(dest.read_bytes()),
        file_count=len(rows), total_bytes=inventory['total_bytes']), indent=2))


if __name__ == '__main__': main()
