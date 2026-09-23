#!/usr/bin/env python3
"""Move only the failed upper landing above source-bound VBE/VD2 collectors."""
import hashlib
import json
from pathlib import Path
import sys


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    base = Path(__file__).resolve().with_name('screen_dvbe_cuts.py')
    data = base.read_bytes()
    assert sha(data) == '399aa14e0b126e9acf8ef2ca0ac1f7c28d98ccf886efe3b379728400ee6bc0de'
    root = next(p for p in base.parents if (p / 'flow/run.sh').is_file())
    ledger = root / 'build/scratch/bgr-hbt-fullbank-20260922-r2/route_ledger.json'
    ledger_hash = sha(ledger.read_bytes())
    assert ledger_hash == '99a734d096ab00af99d697279066d7383a65a24dfe5df4b4c1f52ba5170ecb02'
    obstacles = [r for r in json.loads(ledger.read_text())['routes'] if r['layer'] == 'M3'
                 and r['purpose'] == 'row_collector' and r['bbox_dbu'][0] < 204000
                 and r['bbox_dbu'][2] > 192000 and r['bbox_dbu'][1] < 143780
                 and r['bbox_dbu'][3] > 140000]
    assert {(r['net'], tuple(r['bbox_dbu'])) for r in obstacles} == {
        ('vbe', (13800, 141500, 194250, 141800)),
        ('vd2', (142200, 140900, 197550, 141200))}
    text = data.decode()
    changes = []
    for before, after, count in (('set(os.sched_getaffinity(0)) == {2}', 'set(os.sched_getaffinity(0)) == {0}', 1),
                                 ('140220', '142220', 3),
                                 ('141780', '143780', 4),
                                 ('141000', '143000', 2)):
        assert text.count(before) == count, (before, text.count(before))
        changes.append(dict(before=before, after=after, occurrences=count))
        text = text.replace(before, after)
    scope = dict(__file__=str(Path(__file__).resolve()), __name__='prepared_r2')
    exec(compile(text, str(base), 'exec'), scope)
    scope['main']()
    assert sha(base.read_bytes()) == sha(data) and sha(ledger.read_bytes()) == ledger_hash
    out = Path(sys.argv[sys.argv.index('--output')+1])
    (out / 'derived_screen.py').write_text(text)
    (out / 'revision.json').write_text(json.dumps(dict(
        status='passed exact source revision', original_sha256=sha(data),
        source_route_ledger_sha256=ledger_hash, held_source_obstacles=obstacles,
        derived_sha256=sha(text.encode()), substitutions=changes,
        scope='Only upper landing/cut y coordinates move from141 to143um; M5 starts at136.9um and all lower shapes are unchanged. Exclusive coordinator CPU0 loan replaces returned CPU2 lease.',
        reason='Source-bound native VBE M3 spans y141.5..141.8 and VD2 spans140.9..141.2; candidate lower boundary142.22 gives420nm to VBE.',
        previous_screen='failed preserved', candidate_generation='not run'), indent=2)+'\n')


if __name__ == '__main__':
    main()
