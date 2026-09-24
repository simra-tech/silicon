#!/usr/bin/env python3
"""Fresh raw-junction context on current qualified pure-fill geometry."""
import hashlib
from pathlib import Path
import current_bindings as binding

binding.validate_inputs()
base=Path(__file__).resolve().parent.parent/'integration_be54/derive_context.py'
assert hashlib.sha256(base.read_bytes()).hexdigest()=='f1d0c6fde58042e1f8e2710cdb12af741130b499a1f6fb52f2b2355c7136b5cb'
code=base.read_text()
for old,new in [('analog-pair-integration-20260923-r1/analog_pair_native.gds',binding.GDS_RELATIVE),
    ('be54644ebfffdc85bf4ed136966a31e60f374290b9ba7bd179753aa0b038d307',binding.GDS_SHA)]:
    assert code.count(old)==1;code=code.replace(old,new)
exec(compile(code,str(base),'exec'),{'__file__':str(base),'__name__':'__main__'})
