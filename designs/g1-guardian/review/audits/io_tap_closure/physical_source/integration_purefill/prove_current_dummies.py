#!/usr/bin/env python3
"""Rebind native dummy terminals to current pure-fill GDS and current source."""
import hashlib
from pathlib import Path

wrapper=Path(__file__).resolve()
base=wrapper.parent.parent/'prove_current_dummies.py'
assert hashlib.sha256(base.read_bytes()).hexdigest()=='24f4fb47bd603802dcb93d47f04dfdb7cd3b706128ef946b650b6be77c3273fb'
code=base.read_text()
edits=[
 ('gshared-fill-20260923-r4/route_fill_pruned.gds','current-purefill-flat-20260923-r1/pure_fill_flattened.gds'),
 ('4cffddc5ae8369c9fd5c574cb9571b4641cdee26876370c93bfbe042c4049df2','6b9c5878a81a0ac4d3f68d3d8dbb5fa1927442675606aa6bd46a14d6552def51'),
 ('io-physical-ap-source-20260923-r2/physical_taps.cdl','trip-hard-full-reference-20260923-r1/physical_taps.cdl'),
 ('796a724df08e1da81bbb43e6b54399e6ac338ff33db6a56535f8a89f91f24abf','be00e66f12309bb26f16165860271936ee3f8eb74bc84c3fa56e1ee3295ccd90')]
for old,new in edits:
    assert code.count(old)==1,(old,code.count(old))
    code=code.replace(old,new)
exec(compile(code,str(base),'exec'),{'__file__':str(base),'__name__':'__main__'})
