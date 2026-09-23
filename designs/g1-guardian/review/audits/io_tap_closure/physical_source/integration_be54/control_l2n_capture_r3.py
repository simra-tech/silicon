#!/usr/bin/env python3
"""Use the explicit L2N writer, not an incomplete pre-comparison LVS report."""
from pathlib import Path

base=Path(__file__).resolve().with_name('control_l2n_capture_r2.py')
code=base.read_text()
needle="code=base.read_text()"
assert code.count(needle)==1
code=code.replace(needle,needle+"\nassert code.count('l2n_data.write(')==1\ncode=code.replace('l2n_data.write(', 'l2n_data.write_l2n(')")
exec(compile(code,str(base),'exec'),globals())
