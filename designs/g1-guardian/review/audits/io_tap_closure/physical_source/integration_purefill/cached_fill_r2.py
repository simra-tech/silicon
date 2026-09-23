"""Preserve the saved fill template's Box/SimplePolygon/Polygon representation."""
import hashlib
from pathlib import Path

base=Path(__file__).resolve().with_name('cached_fill.py')
assert hashlib.sha256(base.read_bytes()).hexdigest()=='e9542578433e02839054710c6d80c1e5898379bc347ee9372564ba2783904c06'
code=base.read_text()
old='s.box.dup() if s.is_box() else s.polygon.dup()'
new='s.box.dup() if s.is_box() else (s.simple_polygon.dup() if s.is_simple_polygon() else s.polygon.dup())'
assert code.count(old)==1;code=code.replace(old,new)
exec(compile(code,str(base),'exec'),globals())
