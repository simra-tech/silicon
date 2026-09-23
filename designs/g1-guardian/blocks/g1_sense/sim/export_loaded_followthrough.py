#!/usr/bin/env python3
"""Reversible compact export of completed/failed loaded follow-through attempts."""
import argparse
import getpass
import gzip
import hashlib
import io
import json
from pathlib import Path


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bulk-root', type=Path, required=True)
    parser.add_argument('--attempt', action='append', default=[],
                        help='Portable label=absolute attempt folder; repeatable')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--inventory-only', action='store_true')
    args = parser.parse_args()
    sim = Path(__file__).resolve().parent
    root = sim.parents[4]
    if args.inventory_only:
        paths = sorted(p for p in args.output.rglob('*') if p.is_file())
        paths += [sim / name for name in ['run_loaded_followthrough.py',
            'test_loaded_followthrough.py', 'analyze_loaded_followthrough.py',
            'export_loaded_followthrough.py', 'analyze_loaded_differential.py']]
        paths.append(sim.parent / 'reports/LOADED_FOLLOWTHROUGH_20260923.md')
        rows = [dict(path=str(p.resolve().relative_to(root)),
                     sha256=sha(p.read_bytes()), bytes=p.stat().st_size) for p in paths]
        assert len({r['path'] for r in rows}) == len(rows)
        target = args.output / 'commit_inventory.json'
        with target.open('x') as stream:
            json.dump(dict(status='frozen exact listed files only', files=rows,
                           total_bytes=sum(r['bytes'] for r in rows),
                           self_excluded=True), stream, indent=2)
            stream.write('\n')
        print(json.dumps(dict(files=len(rows), sha256=sha(target.read_bytes()))))
        return
    assert args.attempt and not args.output.exists()
    args.output.mkdir(parents=True)
    records = []
    dispositions = []
    labels = set()

    def export(source, relative):
        raw = source.read_bytes()
        pairs = [(str(args.bulk_root).encode(), b'${RESULTS_ROOT}'),
                 (b'/work/', b'${REPOSITORY_ROOT}/')]
        portable = raw
        for old, new in pairs:
            portable = portable.replace(old, new)
        restored = portable
        for old, new in reversed(pairs):
            restored = restored.replace(new, old)
        assert restored == raw
        assert b'/home/' not in portable and getpass.getuser().encode() not in portable
        target = args.output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = portable
        if target.suffix == '.gz':
            buf = io.BytesIO()
            with gzip.GzipFile(fileobj=buf, mode='wb', filename='', mtime=0) as zipped:
                zipped.write(portable)
            payload = buf.getvalue()
        with target.open('xb') as stream:
            stream.write(payload)
        records.append(dict(path=str(relative), sha256=sha(payload), bytes=len(payload),
                            original_sha256=sha(raw), decoded_portable_sha256=sha(portable),
                            inverse_exact=True, path_normalized=portable != raw))

    for item in args.attempt:
        label, folder = item.split('=', 1)
        assert label and label.replace('-', '').replace('_', '').isalnum()
        assert label not in labels
        labels.add(label)
        folder = Path(folder)
        folder.resolve().relative_to(args.bulk_root.resolve())
        for case in ['slow', 'fast', 'rise', 'fall']:
            base = folder / case
            if not base.exists():
                continue
            modes = (['differential', 'tian_voltage', 'tian_current']
                     if case in ['slow', 'fast'] else ['dc', 'step'])
            for mode in modes:
                leaf = base / mode
                summary = leaf / 'summary.json'
                status = (json.loads(summary.read_text())['status'] if summary.exists()
                          else 'not run' if not leaf.exists() else 'failed missing summary')
                dispositions.append(dict(attempt=label, case=case, mode=mode, status=status))
                for name in ['summary.json', 'contract.json', 'provenance.json', 'runner.py',
                             'probe.cir', 'probe.spice', 'run.json', 'run.log', 'ac.dat',
                             'input_basis.dat', 'phase0.dat']:
                    source = leaf / name
                    if source.exists():
                        suffix = '.gz' if name in ['probe.cir', 'probe.spice', 'run.log', 'phase0.dat'] else ''
                        export(source, Path(label) / case / mode / (name + suffix))
            for name in ['summary.json', 'return_ratio.json']:
                source = base / 'analysis' / name
                if source.exists():
                    export(source, Path(label) / case / 'analysis' / name)
    with (args.output / 'artifact_manifest.json').open('x') as stream:
        required = []
        for case in ['slow', 'fast', 'rise', 'fall']:
            modes = (['differential', 'tian_voltage', 'tian_current']
                     if case in ['slow', 'fast'] else ['dc', 'step'])
            for mode in modes:
                attempts = [r for r in dispositions if r['case'] == case and r['mode'] == mode]
                required.append(dict(case=case, mode=mode, attempts=attempts,
                                     coverage='recorded' if attempts else 'not run'))
        json.dump(dict(status='completed export; electrical dispositions unchanged',
                       records=records, leaves=dispositions, required_coverage=required,
                       normalization='Configured bulk root and /work prefix only; exact inverse',
                       no_simulation=True), stream, indent=2)
        stream.write('\n')
    print(json.dumps(dict(files=len(records), bytes=sum(r['bytes'] for r in records))))


if __name__ == '__main__':
    main()
