#!/usr/bin/env python3
"""Map direct-active hierarchy control without adopting its area accounting."""
import hashlib
from pathlib import Path

original = Path(__file__).resolve().with_name('audit_ownership.py')
assert hashlib.sha256(original.read_bytes()).hexdigest() == 'b315a8942f1560722732ca88f0b4589202f69f6cf57065406c77f27b1d3f242e'
code = original.read_text()
assert code.count('io-tap-physical-dimensions-20260923-r2/analysis.json') == 1
code = code.replace('io-tap-physical-dimensions-20260923-r2/analysis.json',
                    'io-direct-active-20260923-r1/analysis.json')
exec(compile(code,str(original),'exec'),globals())
