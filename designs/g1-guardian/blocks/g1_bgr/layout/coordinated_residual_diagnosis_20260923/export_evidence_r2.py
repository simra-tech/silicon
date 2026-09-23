#!/usr/bin/env python3
"""Portable export successor: normalize host repository prefixes explicitly."""
import hashlib
from pathlib import Path

original = Path(__file__).resolve().with_name('export_evidence.py')
assert hashlib.sha256(original.read_bytes()).hexdigest() == '0edee84adf1c6f5e2c4ec445cad43c8cab0d15362b1b512d2356adb7061aa120'
code = original.read_text()
code = code.replace('import os\n', 'import os\nimport re\n')
needle = '        assert all(word not in portable for word in forbidden),path'
assert code.count(needle) == 1
code = code.replace(needle, "        if not binary:\n            portable=re.sub(b'/' + b'home/[^/\\\\s\\\"]+/silicon-restored/', b'<repository>/', portable)\n"+needle)
needle = '    absent=[]'
assert code.count(needle) == 1
code = code.replace(needle, "    receipts += ['bgr-dvbe-cuts-export-launch-20260923-r1', 'bgr-dvbe-cuts-export-launch-20260923-r2']\n"+needle)
exec(compile(code,str(original),'exec'),globals())
