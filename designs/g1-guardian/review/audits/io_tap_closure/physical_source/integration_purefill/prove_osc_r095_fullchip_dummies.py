#!/usr/bin/env python3
"""Rebind the frozen native pad-dummy proof to the isolated R0.95 full chip."""
import hashlib
from pathlib import Path

base = Path(__file__).resolve().parent.parent/'prove_current_dummies.py'
assert hashlib.sha256(base.read_bytes()).hexdigest() == \
    '24f4fb47bd603802dcb93d47f04dfdb7cd3b706128ef946b650b6be77c3273fb'
code = base.read_text()
edits = [
    ('gshared-fill-20260923-r4/route_fill_pruned.gds',
     'osc-r095-fullchip-integration-20260924-r1/osc_r095_fullchip.gds'),
    ('4cffddc5ae8369c9fd5c574cb9571b4641cdee26876370c93bfbe042c4049df2',
     '18b897feb06b7a02508ea8734d40845d69bcb515955368daba9dd1938a1949c9'),
    ('io-physical-ap-source-20260923-r2/physical_taps.cdl',
     'osc-r095-physical-20260924-r1/fullchip_r095_candidate.cdl'),
    ('796a724df08e1da81bbb43e6b54399e6ac338ff33db6a56535f8a89f91f24abf',
     '126acd51cae404f55e9a3470d521d0d90f5115e668fbf393ac48c492e4507333'),
]
for old, new in edits:
    assert code.count(old) == 1, (old, code.count(old))
    code = code.replace(old, new)
exec(compile(code, str(base), 'exec'), {'__file__': str(base), '__name__': '__main__'})
