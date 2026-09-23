#!/usr/bin/env python3
"""Trapezoidal-method isolated-pad diagnostic; unchanged tolerances and models."""
import hashlib
from pathlib import Path
parent=Path(__file__).with_name('probe_pad_only.py')
original=parent.read_text()
assert hashlib.sha256(original.encode()).hexdigest()=='d46ee770e3f0712a01b1b727bcbf4bec5f37660741a5fb389e0671ede622ed37'
old=r"+ '\n'.join(retained) + '\nVINPUT pad_core 0 0\n'"
new=r"""+ '\n'.join(retained).replace('method=gear', 'method=trap') + '\nVINPUT pad_core 0 0\n'"""
assert original.count(old)==1
derived=original.replace(old,new)
assert derived.replace(new,old)==original
exec(compile(derived,str(parent)+'[trapezoidal-method]','exec'),dict(__name__='__main__',__file__=str(parent)))
