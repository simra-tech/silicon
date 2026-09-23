#!/usr/bin/env python3
"""Fresh raw-junction context proof on the exact overlay-flattened view."""
import hashlib
from pathlib import Path

base=Path(__file__).resolve().with_name('derive_context.py')
assert hashlib.sha256(base.read_bytes()).hexdigest()=='f1d0c6fde58042e1f8e2710cdb12af741130b499a1f6fb52f2b2355c7136b5cb'
code=base.read_text()
for old,new in [
 ('analog-pair-integration-20260923-r1/analog_pair_native.gds','analog-pair-overlay-flat-20260923-r1/overlay_flattened.gds'),
 ('be54644ebfffdc85bf4ed136966a31e60f374290b9ba7bd179753aa0b038d307','dcca5f47f6d397e8c6811116f092ac0f9adbbe761617a87ba69cec8216417333')]:
    assert code.count(old)==1;code=code.replace(old,new)
exec(compile(code,str(base),'exec'),{'__file__':str(base),'__name__':'__main__'})
