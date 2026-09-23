#!/usr/bin/env python3
"""Tighter-tolerance isolated-pad diagnostic; no circuit or model substitution."""
import hashlib
from pathlib import Path
parent=Path(__file__).with_name('probe_pad_only.py')
original=parent.read_text()
assert hashlib.sha256(original.encode()).hexdigest()=='d46ee770e3f0712a01b1b727bcbf4bec5f37660741a5fb389e0671ede622ed37'
old=r"+ '\n'.join(retained) + '\nVINPUT pad_core 0 0\n'"
new=r"""+ '\n'.join(retained).replace('reltol=0.005', 'reltol=0.001').replace('abstol=1e-9', 'abstol=1e-12').replace('vntol=1e-5', 'vntol=1e-6').replace('chgtol=1e-13', 'chgtol=1e-15') + '\nVINPUT pad_core 0 0\n'"""
assert original.count(old)==1
derived=original.replace(old,new)
assert derived.replace(new,old)==original
exec(compile(derived,str(parent)+'[tightened-tolerances]','exec'),dict(__name__='__main__',__file__=str(parent)))
