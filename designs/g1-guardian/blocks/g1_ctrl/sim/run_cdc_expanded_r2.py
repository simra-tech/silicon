#!/usr/bin/env python3
"""Only repair invalid Verilog real literal spelling in the retained r1 harness."""
import hashlib
from pathlib import Path

path=Path(__file__).with_name('run_cdc_expanded.py')
assert hashlib.sha256(path.read_bytes()).hexdigest()=='7ffbbd0e7192bb0b4fc3673ba3dd50a70acb71563cf81e60ded399a960b3cd40'
text=path.read_text()
old='real data_delay=2., output_delay=0.;'
assert text.count(old)==1
text=text.replace(old,'real data_delay=2.0, output_delay=0.0;')
ns=dict(__file__=__file__,__name__='cdc_expanded_r2')
exec(compile(text,str(path),'exec'),ns)
ns['main']()
