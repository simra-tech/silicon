#!/usr/bin/env python3
"""One declared substrate-ring change; preserve failed r1 source and geometry."""
import hashlib
import json
from pathlib import Path
import sys


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    here = Path(__file__).resolve().parent
    original = here / 'build_stacked_pair.py'
    assert sha(original) == 'edc0919bdbf991f5191764936bbf741f25d2a4fb0613333659714830395fd289'
    diagnostic = here / 'stacked-pair-channel-diagnostic-20260922-r1/diagnostic.json'
    report = json.loads(diagnostic.read_text())
    assert report['original_builder_sha256'] == sha(original)
    assert report['differences']['added_channels']['area_um2'] == 7.632
    assert report['differences']['removed_channels']['area_um2'] == 0
    assert report['differences']['removed_native_Activ']['area_um2'] == 0
    before = 'ring=D.tap_ring(m.x0-1.45,m.y0-3.05,m.x1+1.45,m.y0+9.05,ptype=True)'
    after = 'ring=D.tap_ring(m.x0-2.50,m.y0-3.05,m.x1+2.50,m.y0+9.05,ptype=True)'
    source = original.read_text()
    assert source.count(before) == 1
    derived = source.replace(before, after)
    out = Path(sys.argv[sys.argv.index('--output') + 1])
    assert out.name == 'stacked-pair-20260922-r2' and not out.exists()
    scope = {'__file__': str(Path(__file__)), '__name__': 'isolated_r2'}
    exec(compile(derived, str(original), 'exec'), scope)
    try:
        scope['main']()
    finally:
        if out.exists():
            (out / 'derived_builder.py').write_text(derived)
            receipt = dict(original_builder_sha256=sha(original), derived_builder_sha256=sha(out / 'derived_builder.py'),
                           diagnostic_sha256=sha(diagnostic), only_geometry_replacement=[before, after],
                           contract_sha256=sha(here / 'STACKED_GUARD_R2_CONTRACT_20260922.md'))
            (out / 'revision.json').write_text(json.dumps(receipt, indent=2) + '\n')


if __name__ == '__main__':
    main()
