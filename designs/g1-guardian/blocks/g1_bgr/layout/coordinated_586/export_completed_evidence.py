#!/usr/bin/env python3
"""Exact portable copies of completed geometry controls, including failures."""
import hashlib
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
RUNS = [
    'bgr-original-generator-20260922-r1',
    'bgr-mos-contact-prototypes-20260922-r1',
    'bgr-mos-contact-prototypes-20260922-r2',
    'bgr-mos-stock-20260922-r1',
    'bgr-hbt-contact-prototypes-20260922-r1',
    'bgr-second-stock-20260922-r1',
    'bgr-resistor-bank-pilot-20260922-r1',
    'bgr-resistor-bank-stock-20260922-r1',
    'bgr-resistor-bank-pilot-20260922-r2',
    'bgr-resistor-bank-stock-20260922-r2',
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    out = HERE / 'evidence-20260922-r1'
    assert not out.exists()
    files = []
    for run in RUNS:
        base = ROOT / 'build/scratch' / run
        assert base.is_dir()
        for path in sorted(base.rglob('*')):
            if path.is_dir() or '__pycache__' in path.parts:
                continue
            assert not path.is_symlink()
            data = path.read_bytes()
            assert not re.search(rb'/home/|/opt/sim/|\.private/|BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY', data), str(path)
            files.append((path, Path(run) / path.relative_to(base), data))
    assert sum(len(data) for _, _, data in files) < 30 * 2**20
    out.mkdir()
    rows = []
    for source, relative, data in files:
        target = out / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        assert sha(target.read_bytes()) == sha(data) == sha(source.read_bytes())
        rows.append(dict(source=str(source.relative_to(ROOT)), export=str(relative),
                         sha256=sha(data), bytes=len(data)))
    manifest = dict(status='passed exact completed evidence copy', files=rows,
                    exporter_sha256=sha(Path(__file__).read_bytes()),
                    original_evidence_retained=True, transformation='none',
                    failed_originals_included=True)
    (out / 'export_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(dict(status=manifest['status'], files=len(rows), bytes=sum(r['bytes'] for r in rows))))


if __name__ == '__main__':
    main()
