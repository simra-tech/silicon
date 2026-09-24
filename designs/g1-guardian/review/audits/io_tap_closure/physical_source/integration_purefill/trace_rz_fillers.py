#!/usr/bin/env python3
"""Read-only fullchip-vs-block RZ test for omitted active/poly filler layers."""
import hashlib
from pathlib import Path

base=Path(__file__).with_name('trace_rz_geometry.py')
assert hashlib.sha256(base.read_bytes()).hexdigest()=='903d02fc7cb74586fcdb93a00fcaf07b051fc2f4339ca277c3efda6b9e288dae'
code=base.read_text()
old='layers=[(5,0),(6,0),(8,0),(14,0),(28,0),(52,0),(111,0),(128,0),(8,2)]'
new='layers=[(1,22),(5,22)]'
assert code.count(old)==1
code=code.replace(old,new)
exec(compile(code,str(base),'exec'),{'__file__':str(base),'__name__':'__main__'})
