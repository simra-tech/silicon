#!/usr/bin/env python3
"""Full exact proof using qualified saved-template type-preserving batching."""
import hashlib
from pathlib import Path

base=Path(__file__).resolve().with_name('flatten_pure_fill_r3.py')
assert hashlib.sha256(base.read_bytes()).hexdigest()=='71ef13331d2cfc5c8b0b24b301ae81d7e8952843266ec32800c090d93241dbbd'
code=base.read_text()
edits=[('from cached_fill import relocate','from cached_fill_r2 import relocate'),
    ("expected[CACHED_PATH]=sha(CACHED_PATH);expected[BASE_PATH]=sha(BASE_PATH)",
     "expected[CACHED_PATH]=sha(CACHED_PATH);expected[BASE_PATH]=sha(BASE_PATH);expected[CACHED_PATH.with_name('cached_fill.py')]=sha(CACHED_PATH.with_name('cached_fill.py'))"),
    ("'CACHED_PATH':HERE/'cached_fill.py'","'CACHED_PATH':HERE/'cached_fill_r2.py'")]
for old,new in edits:
    assert code.count(old)==1,(old,code.count(old));code=code.replace(old,new)
exec(compile(code,str(base),'exec'),{'__file__':str(Path(__file__).resolve()),'__name__':'__main__'})
