#!/usr/bin/env python3
"""Export completed explicit prototype groups; retain original artifact hashes."""
import argparse
import getpass
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]


def sha(data): return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bulk-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--group', action='append', required=True)
    parser.add_argument('--artifact', action='append', default=[])
    args = parser.parse_args(); args.bulk_root = args.bulk_root.resolve()
    args.output = args.output.resolve()
    assert not args.output.exists() and HERE in args.output.parents
    files = []; groups = []
    for name in args.group:
        assert Path(name).name == name
        base = args.bulk_root/name; assert base.is_dir()
        for path in sorted(base.rglob('*')):
            if not path.is_file(): continue
            if path.suffix in ('.json', '.py', '.log', '.lyrdb', '.gds', '.cdl', '.cir'):
                files.append((path, Path(name)/path.relative_to(base)))
        groups.append(name)
    for item in args.artifact:
        name, value = item.split('=', 1); assert Path(name).name == name
        path = Path(value); assert path.is_file(); files.append((path, Path('observations')/name))
    assert len({str(rel) for _, rel in files}) == len(files)
    args.output.mkdir(parents=True); records = []
    for source, relative in files:
        raw = source.read_bytes(); data = raw
        if source.suffix != '.gds':
            text = raw.decode()
            for old, new in ((str(args.bulk_root), '${BULK}'), (str(REPO), '${REPO}'), ('/work/', '${REPO}/')):
                text = text.replace(old, new)
            # The inspection helpers accept private input paths; export no actual local identity.
            assert getpass.getuser() not in text and '/home/' not in text and '/opt/sim/' not in text, relative
            data = text.encode()
        dest = args.output/relative; dest.parent.mkdir(parents=True, exist_ok=True); dest.write_bytes(data)
        records.append(dict(path=str(dest.relative_to(REPO)), bytes=len(data),
                            original_sha256=sha(raw), exported_sha256=sha(data), path_only_sanitized=raw != data))
    (args.output/'export_manifest.json').write_text(json.dumps(dict(
        status='passed completed isolated dual-gate evidence export; no adoption', groups=groups,
        artifacts=records, omitted='Large LVS database omitted; exact hash, strict xref summary and extracted CDL retained',
        transformation='Only workspace/bulk prefixes replaced in text; original hashes retained'), indent=2)+'\n')
    names = ['prepare_sense_terminal_ledger.py', 'enumerate_sense_metal_contacts.py',
             'inspect_sense_terminal_semantics.py', 'audit_sense_gate_contact_sides.py',
             'prepare_sense_dual_gate_proposal.py', 'screen_sense_dual_gate_proposal.py',
             'distributed_terminal_controls.py', 'build_sense_dual_gate.py',
             'audit_sense_dual_gate_reference.py', 'run_sense_dual_gate_lvs.py',
             'compare_sense_dual_gate_junctions.py', 'SENSE_DISTRIBUTED_TERMINAL_CONTRACT_20260923.md',
             'DUAL_GATE_REVIEW_20260923.md', 'export_sense_dual_gate_evidence.py']
    paths = sorted([HERE/name for name in names]+[q for q in args.output.rglob('*') if q.is_file()])
    rows = [dict(path=str(q.relative_to(REPO)), sha256=sha(q.read_bytes()), bytes=q.stat().st_size) for q in paths]
    inventory = dict(status='frozen isolated dual-gate milestone; applicability failures retained',
                     files=rows, file_count=len(rows), total_bytes=sum(r['bytes'] for r in rows))
    destination = args.output/'commit_inventory.json'; destination.write_text(json.dumps(inventory, indent=2)+'\n')
    print(json.dumps(dict(path=str(destination.relative_to(REPO)), sha256=sha(destination.read_bytes()),
                         file_count=len(rows), total_bytes=inventory['total_bytes']), indent=2))


if __name__ == '__main__': main()
