#!/usr/bin/env python3
"""Repeat the frozen full-context raw junction proof on the analog-pair assembly."""
import hashlib
from pathlib import Path

base=Path(__file__).resolve().parent.parent/'derive_full_context.py'
assert hashlib.sha256(base.read_bytes()).hexdigest()=='a3ff17de3f08f261b99af7b58768285c154ef95e5daf80689282d9775dffe69f'
code=base.read_text()
for old,new in [
    ('gshared-fill-20260923-r4/route_fill_pruned.gds','analog-pair-integration-20260923-r1/analog_pair_native.gds'),
    ('4cffddc5ae8369c9fd5c574cb9571b4641cdee26876370c93bfbe042c4049df2','be54644ebfffdc85bf4ed136966a31e60f374290b9ba7bd179753aa0b038d307')]:
    assert code.count(old)==1
    code=code.replace(old,new)
exec(compile(code,str(base),'exec'),{'__file__':str(base),'__name__':'__main__'})
