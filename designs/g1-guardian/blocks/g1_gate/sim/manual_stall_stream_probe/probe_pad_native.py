#!/usr/bin/env python3
"""Native six-pin pad source control; preserve explicit global substrate tie."""
import hashlib
from pathlib import Path
parent=Path(__file__).with_name('probe_pad_only.py')
original=parent.read_text()
assert hashlib.sha256(original.encode()).hexdigest()=='d46ee770e3f0712a01b1b727bcbf4bec5f37660741a5fb389e0671ede622ed37'
old='XPAD pad_out pad_core vdd 0 vdda 0 0 G1_VSS_DERIVATIVE__sg13g2_IOPadOutPADTYPE'
new='XPAD pad_out pad_core vdd 0 vdda 0 sg13g2_IOPadOutPADTYPE'
assert original.count(old)==1
derived=original.replace(old,new)
assert derived.replace(new,old)==original
exec(compile(derived,str(parent)+'[native-source-control]','exec'),dict(__name__='__main__',__file__=str(parent)))
