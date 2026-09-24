#!/usr/bin/env python3
"""Correct probe frame on both block and assembled snapshots."""
import hashlib
from pathlib import Path
import pya

base=Path(__file__).with_name('trace_rz_upper_graph.py')
assert hashlib.sha256(base.read_bytes()).hexdigest()=='faeebb2c25801cee67f49c793732fafae26e2981179ad1c01a6b4844375a1c0c'
code=base.read_text();old='point=tr*local';new='point=PROBE_TRANSFORM*local'
assert code.count(old)==1
code=code.replace(old,new)
exec(compile(code,str(base),'exec'),{'__file__':str(base),'__name__':'__main__',
    'PROBE_TRANSFORM':pya.Trans(pya.Trans.R90,1031000,331000)})
