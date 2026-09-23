#!/usr/bin/env python3
"""Copy compact source-audit evidence with original/exported hash provenance."""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bulk', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists()
    a.output.mkdir(parents=True)
    manifest = []
    for rev in ('r1', 'r2'):
        run = 'io-tap-upstream-alternatives-20260923-' + rev
        source = a.bulk / run
        for path in sorted(source.iterdir()):
            assert path.is_file() and path.suffix in ('.py', '.json')
            data = path.read_bytes()
            for token in (b'/' + b'home/', b'/' + b'opt/sim/', b'.' + b'private/', a.bulk.name.encode()):
                assert token not in data
            relative = Path(rev) / path.name
            target = a.output / relative
            target.parent.mkdir(exist_ok=True)
            target.write_bytes(data)
            digest = hashlib.sha256(data).hexdigest()
            manifest.append(dict(path=str(relative), source_run=run, source_relative=path.name,
                                 source_sha256=digest, exported_sha256=digest,
                                 source_bytes=len(data), exported_bytes=len(data), byte_identical=True))
    (a.output / 'manifest.json').write_text(json.dumps(dict(status='passed exact export', files=manifest), indent=2) + '\n')
    print(json.dumps(dict(files=len(manifest), bytes=sum(row['source_bytes'] for row in manifest))))


if __name__ == '__main__':
    main()
