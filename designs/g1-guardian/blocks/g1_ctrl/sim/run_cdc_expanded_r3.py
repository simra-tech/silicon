#!/usr/bin/env python3
"""Retain all4410 checks; budget the expanded fixture's calculated119ms duration."""
import hashlib
from pathlib import Path

path=Path(__file__).with_name('run_cdc_expanded.py')
assert hashlib.sha256(path.read_bytes()).hexdigest()=='7ffbbd0e7192bb0b4fc3673ba3dd50a70acb71563cf81e60ded399a960b3cd40'
text=path.read_text()
assert text.count('real data_delay=2., output_delay=0.;')==1
text=text.replace('real data_delay=2., output_delay=0.;','real data_delay=2.0, output_delay=0.0;')
# Per45 configurations the procedural serial/reset schedule is approximately
# 119ms, exceeding the inherited294-check fixture's100ms timeout. 200ms changes
# only the testbench fail-safe, not stimulus timing, acceptance, RTL or120s wall cap.
needle="text=bench.read_text()"
assert text.count(needle)==1
text=text.replace(needle,needle+"\n    assert text.count('#100000000;')==1\n    text=text.replace('#100000000;','#200000000;')")
ns=dict(__file__=__file__,__name__='cdc_expanded_r3')
exec(compile(text,str(path),'exec'),ns)
ns['main']()
