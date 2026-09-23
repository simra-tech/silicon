#!/usr/bin/env python3
"""Preserve exact pinned tap definitions and a requested metal-rule lookup."""
import argparse
import hashlib
import json
import os
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', type=Path, required=True)
    a = ap.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0)) == 1
    pdk = Path('/foss/pdks/ihp-sg13g2')
    assert (pdk/'COMMIT').read_text().strip() == '84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    paths = [pdk/'libs.tech/klayout/tech/lvs/rule_decks'/name for name in
             ('general_derivations.lvs', 'tap_derivations.lvs', 'tap_extraction.lvs', 'layers_definitions.lvs')]
    rows = []
    for path in sorted((pdk/'libs.tech/klayout/tech/drc').rglob('*')):
        if not path.is_file():
            continue
        try:
            lines = path.read_text().splitlines()
        except UnicodeError:
            continue
        hits = [i for i, line in enumerate(lines) if 'M3.f' in line]
        if hits:
            paths.append(path)
            rows.append(dict(path=str(path.relative_to(pdk)), hits=[dict(line=i+1,
                context='\n'.join(lines[max(0,i-8):i+12])) for i in hits]))
    a.output.mkdir(parents=True)
    artifacts = []
    for path in paths:
        rel = path.relative_to(pdk)
        dest = a.output/rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(path.read_bytes())
        artifacts.append(dict(path=str(rel), sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    assert rows
    (a.output/'summary.json').write_text(json.dumps(dict(status='passed pinned read-only definition capture',
        artifacts=artifacts, M3_f=rows), indent=2)+'\n')


if __name__ == '__main__':
    main()
