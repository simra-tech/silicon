#!/usr/bin/env python3
"""Expand RZ window audit to every stock resistor exclusion and upper-route layer."""
import hashlib
from pathlib import Path

base=Path(__file__).with_name('trace_rz_geometry.py')
assert hashlib.sha256(base.read_bytes()).hexdigest()=='903d02fc7cb74586fcdb93a00fcaf07b051fc2f4339ca277c3efda6b9e288dae'
code=base.read_text()
old='layers=[(5,0),(6,0),(8,0),(14,0),(28,0),(52,0),(111,0),(128,0),(8,2)]'
new='layers=[(1,0),(1,20),(5,0),(6,0),(7,0),(7,21),(8,0),(8,2),(10,0),(14,0),(19,0),(26,0),(27,0),(27,2),(28,0),(29,0),(30,0),(32,0),(33,0),(40,0),(44,0),(46,21),(49,0),(50,0),(52,0),(66,0),(67,0),(99,30),(99,31),(111,0),(125,0),(126,0),(128,0),(133,0),(134,0),(156,0)]'
assert code.count(old)==1
code=code.replace(old,new)
exec(compile(code,str(base),'exec'),{'__file__':str(base),'__name__':'__main__'})
