#!/usr/bin/env python3
"""Reversible three-dummy comparison-only source after new native proof."""
from pathlib import Path

base=Path(__file__).with_name('project_current_dummies.py')
code=base.read_text()
old='6b9c5878a81a0ac4d3f68d3d8dbb5fa1927442675606aa6bd46a14d6552def51'
new='5d121548bb9406f8229fdca7e7e26c1c3e6581ad1b0745f8a2cfce4615af8684'
assert code.count(old)==1;code=code.replace(old,new)
exec(compile(code,str(base),'exec'),{'__file__':str(base),'__name__':'__main__'})
