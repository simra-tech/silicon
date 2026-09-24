#!/usr/bin/env python3
"""Output-pad-only numerical diagnostic with manual-documented voltage LTE."""
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
    new = ('* DIAGNOSTIC: one output pad with ideal core drive and 20pF load\n'
           + '\n'.join(retained) + '\nVINPUT pad_core 0 0\n'
           + 'XPAD pad_out pad_core vdd 0 vdda 0 0 G1_VSS_DERIVATIVE__sg13g2_IOPadOutPADTYPE\n'
           + 'COUT pad_out 0 20p\n.save all\n.tran 1n 16u 0 1n\n.end\n')""".replace('PADTYPE', a.pad)
init_old = "(a.output / '.spiceinit').write_bytes((a.baseline / '.spiceinit').read_bytes())"
init_new = "(a.output / '.spiceinit').write_bytes((a.baseline / '.spiceinit').read_bytes() + b'\\noption newtrunc\\noption ltetrtol=1\\noption ltereltol=0.001\\noption lteabstol=1e-6\\n')"
changes = [
    ("old = '.option method=gear reltol=0.005'\n    new = '.option method=gear maxord=1 reltol=0.005'", fixture),
    ('Bounded integration-order diagnostic; never electrical qualification.',
     'Voltage-LTE output-pad diagnostic; never electrical qualification.'),
    ("'integration_order_convergence': 'not run'", "'voltage_LTE_diagnostic': 'not run'"),
    (init_old, init_new),
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
exec(compile(derived, str(parent) + '[pad-newtrunc-' + a.pad + ']', 'exec'),
     dict(__name__='__main__', __file__=str(parent)))
