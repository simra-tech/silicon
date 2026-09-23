#!/usr/bin/env python3
"""Single-instance deletion diagnostic, not a usable board or safety model."""
import hashlib
from pathlib import Path

parent = Path(__file__).with_name('probe_first_order.py')
original = parent.read_text()
assert hashlib.sha256(original.encode()).hexdigest() == '0c91d48855048e87d4d6fe5e367c2caebe96edcb83a0715e17f264f0e4658aa5'
changes = [
    ('Bounded integration-order diagnostic; never electrical qualification.',
     'Single external-FET deletion diagnostic; never electrical qualification.'),
    ("old = '.option method=gear reltol=0.005'", "old = 'XFET dfet gfet source CSD16340Q3'"),
    ("new = '.option method=gear maxord=1 reltol=0.005'", "new = '* DIAGNOSTIC ONLY: external XFET instance absent'"),
    ("'integration_order_convergence': 'not run'", "'physical_board_equivalence': 'not applicable'"),
]
derived = original
for old, new in changes:
    assert derived.count(old) == 1
    derived = derived.replace(old, new)
restored = derived
for old, new in reversed(changes):
    assert restored.count(new) == 1
    restored = restored.replace(new, old)
assert restored == original
exec(compile(derived, str(parent)+'[single-XFET-removal]', 'exec'),
     dict(__name__='__main__', __file__=str(parent)))
