#!/usr/bin/env python3
"""Fresh native-terminal proof for the unchanged three dummies in the analog-pair assembly."""
import hashlib
from pathlib import Path

base=Path(__file__).resolve().parent.parent/'prove_current_dummies.py'
assert hashlib.sha256(base.read_bytes()).hexdigest()=='24f4fb47bd603802dcb93d47f04dfdb7cd3b706128ef946b650b6be77c3273fb'
code=base.read_text()
for old,new in [
 ('gshared-fill-20260923-r4/route_fill_pruned.gds','analog-pair-integration-20260923-r1/analog_pair_native.gds'),
 ('4cffddc5ae8369c9fd5c574cb9571b4641cdee26876370c93bfbe042c4049df2','be54644ebfffdc85bf4ed136966a31e60f374290b9ba7bd179753aa0b038d307'),
 ('io-physical-ap-source-20260923-r2/physical_taps.cdl','analog-pair-reference-20260923-r1/physical_taps.cdl'),
 ('796a724df08e1da81bbb43e6b54399e6ac338ff33db6a56535f8a89f91f24abf','ac740690d87f2c1b27ecfa803aba8b11541da617e39e2e7f131aa90fa930fb2e')]:
    assert code.count(old)==1;code=code.replace(old,new)
exec(compile(code,str(base),'exec'),{'__file__':str(base),'__name__':'__main__'})
