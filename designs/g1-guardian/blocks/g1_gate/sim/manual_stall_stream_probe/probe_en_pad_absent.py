#!/usr/bin/env python3
"""Ideal EN-core substitution diagnostic; no pad or board qualification."""
import hashlib
from pathlib import Path
parent=Path(__file__).with_name('probe_first_order.py')
original=parent.read_text()
assert hashlib.sha256(original.encode()).hexdigest()=='0c91d48855048e87d4d6fe5e367c2caebe96edcb83a0715e17f264f0e4658aa5'
changes=[
 ('Bounded integration-order diagnostic; never electrical qualification.',
  'Ideal EN-core substitution diagnostic; never electrical qualification.'),
 ("old = '.option method=gear reltol=0.005'",
  "old = 'XPE en_pad en_core vdd 0 vdda 0 0 G1_VSS_DERIVATIVE__sg13g2_IOPadIn'"),
 ("new = '.option method=gear maxord=1 reltol=0.005'",
  "new = 'VEN_DIAGNOSTIC en_core 0 0'"),
 ("'integration_order_convergence': 'not run'", "'physical_pad_equivalence': 'not applicable'"),
]
derived=original
for old,new in changes:
    assert derived.count(old)==1
    derived=derived.replace(old,new)
restored=derived
for old,new in reversed(changes):
    assert restored.count(new)==1
    restored=restored.replace(new,old)
assert restored==original
exec(compile(derived,str(parent)+'[ideal-EN-core]','exec'),dict(__name__='__main__',__file__=str(parent)))
