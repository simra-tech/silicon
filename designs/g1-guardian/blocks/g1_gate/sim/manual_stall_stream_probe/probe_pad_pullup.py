#!/usr/bin/env python3
"""Isolated output-pad diagnostic with a declared 47 kOhm board pull-up."""
import argparse
import hashlib
from pathlib import Path
import sys

p = argparse.ArgumentParser(add_help=False)
p.add_argument('--pad', choices=['4mA', '30mA'], required=True)
a, rest = p.parse_known_args()
sys.argv = [sys.argv[0]] + rest
parent = Path(__file__).with_name('probe_first_order.py')
original = parent.read_text()
assert hashlib.sha256(original.encode()).hexdigest() == '0c91d48855048e87d4d6fe5e367c2caebe96edcb83a0715e17f264f0e4658aa5'
fixture = r"""old = original
    prefixes = ('.param ', '.lib ', '.include ', '.incpslt ', '.temp ',
                '.global ', '.option ', 'Vsub ', 'Rsa ', 'Cda ', 'Rsd ',
                'Cdd ', 'Vdda ', 'Vdd ')
    retained = [line for line in original.splitlines() if line.startswith(prefixes)]
    assert sum(line.startswith('Vdda ') for line in retained) == 1
    assert sum(line.startswith('Vdd ') for line in retained) == 1
    new = ('* DIAGNOSTIC: one output pad with declared 47k pull-up\n'
           + '\n'.join(retained) + '\nVINPUT pad_core 0 0\n'
           + 'XPAD pad_out pad_core vdd 0 vdda 0 0 G1_VSS_DERIVATIVE__sg13g2_IOPadOutPADTYPE\n'
           + 'COUT pad_out 0 20p\nRLOAD pad_out vdda 47k\n'
           + '.save all\n.tran 1n 16u 0 1n\n.end\n')""".replace('PADTYPE', a.pad)
changes = [
    ("old = '.option method=gear reltol=0.005'\n    new = '.option method=gear maxord=1 reltol=0.005'", fixture),
    ('Bounded integration-order diagnostic; never electrical qualification.',
     'Declared-board-pull-up diagnostic; never electrical qualification.'),
    ("'integration_order_convergence': 'not run'", "'loaded_board_qualification': 'not run'"),
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
exec(compile(derived, str(parent) + '[pad-pullup-' + a.pad + ']', 'exec'),
     dict(__name__='__main__', __file__=str(parent)))
