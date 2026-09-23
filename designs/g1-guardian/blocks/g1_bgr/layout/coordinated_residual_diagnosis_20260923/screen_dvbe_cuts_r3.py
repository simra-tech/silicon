#!/usr/bin/env python3
"""Six upper cuts fit the independently observed full-parent fill window."""
import hashlib
import json
import os
from pathlib import Path
import sys


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    base = Path(__file__).resolve().with_name('screen_dvbe_cuts.py')
    assert sha(base) == '399aa14e0b126e9acf8ef2ca0ac1f7c28d98ccf886efe3b379728400ee6bc0de'
    context = Path(os.environ['G1_RESULTS_ROOT'])/'bgr-dvbe-cuts-parent-context-20260923-r1/analysis.json'
    observed = json.loads(context.read_text())
    failed = [r for r in observed['checks'] if not r['passed']]
    assert observed['status'] == 'failed parent-context gate'
    assert {r['layer'] for r in failed} == {30, 50}
    assert all(not r['foreign_overlap'] and not any(r['foreign_capture'].values()) for r in failed)
    context_hash = sha(context)
    text = base.read_text()
    changes = []
    for before, after, count in (
        ('set(os.sched_getaffinity(0)) == {2}', 'set(os.sched_getaffinity(0)) == {48}', 1),
        ('140220', '142430', 3), ('141780', '143570', 4), ('141000', '143000', 2),
        ('(-630, -210, 210, 630)', '(-420, 0, 420)', 1),
        ("'upper_eight_cut'", "'upper_six_cut'", 1)):
        assert text.count(before) == count, (before, text.count(before))
        changes.append(dict(before=before, after=after, occurrences=count))
        text = text.replace(before, after)
    scope = dict(__file__=str(Path(__file__).resolve()), __name__='prepared_r3')
    exec(compile(text, str(base), 'exec'), scope)
    scope['main']()
    assert sha(context) == context_hash
    out = Path(sys.argv[sys.argv.index('--output')+1])
    (out/'derived_screen.py').write_text(text)
    (out/'revision.json').write_text(json.dumps(dict(status='passed exact revision',
        original_sha256=sha(base), derived_sha256=hashlib.sha256(text.encode()).hexdigest(),
        previous_context_sha256=context_hash, substitutions=changes,
        scope='Upper landing1.14um tall, six cuts; lower arrays unchanged. Full-parent context must rerun.',
        old_context='failed preserved', candidate_generation='not run'), indent=2)+'\n')


if __name__ == '__main__':
    main()
