#!/usr/bin/env python3
"""Only the independently re-proved three source dummies, comparison only."""
import hashlib
from pathlib import Path

wrapper=Path(__file__).resolve()
base=wrapper.parent.parent/'prepare_current_dummy_reference.py'
assert hashlib.sha256(base.read_bytes()).hexdigest()=='39b7d84bb57864ee96124b08e5e50ea890cd83cf4c90dade0be2748aaccaccd3'
code=base.read_text()
edits=[
 ('4cffddc5ae8369c9fd5c574cb9571b4641cdee26876370c93bfbe042c4049df2','6b9c5878a81a0ac4d3f68d3d8dbb5fa1927442675606aa6bd46a14d6552def51'),
 ('796a724df08e1da81bbb43e6b54399e6ac338ff33db6a56535f8a89f91f24abf','be00e66f12309bb26f16165860271936ee3f8eb74bc84c3fa56e1ee3295ccd90'),
 ('io-physical-ap-source-20260923-r2/physical_taps_reader.cdl','trip-hard-full-reference-20260923-r1/physical_taps_reader.cdl'),
 ('d39ce8512f167545ab2818582bd1e51e88f6402ff810dcf3368cd7d277ddb4d4','94e50a2a7f0646282f4499831bcfe03a2cf8871fbc33a7549b6e8f94fded207b')]
for old,new in edits:
    assert code.count(old)==1,(old,code.count(old))
    code=code.replace(old,new)
exec(compile(code,str(base),'exec'),{'__file__':str(base),'__name__':'__main__'})
