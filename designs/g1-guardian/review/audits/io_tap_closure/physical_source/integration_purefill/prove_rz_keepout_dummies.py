#!/usr/bin/env python3
"""Independently re-prove exact native dummy terminals on RZ keepout."""
from pathlib import Path

base=Path(__file__).with_name('prove_current_dummies.py')
code=base.read_text()
edits=[
 ('current-purefill-flat-20260923-r1/pure_fill_flattened.gds','current-purefill-rz-keepout-20260923-r2/rz_fill_keepout.gds'),
 ('6b9c5878a81a0ac4d3f68d3d8dbb5fa1927442675606aa6bd46a14d6552def51','5d121548bb9406f8229fdca7e7e26c1c3e6581ad1b0745f8a2cfce4615af8684')]
for old,new in edits:
    assert code.count(old)==1,(old,code.count(old));code=code.replace(old,new)
exec(compile(code,str(base),'exec'),{'__file__':str(base),'__name__':'__main__'})
