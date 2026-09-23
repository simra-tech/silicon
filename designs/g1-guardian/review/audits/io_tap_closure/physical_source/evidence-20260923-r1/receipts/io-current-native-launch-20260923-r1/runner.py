#!/usr/bin/env python3
"""Prospective fixed 30-second resource observation; no policy/lease change."""
import hashlib
from pathlib import Path

predecessor = Path(__file__).resolve().with_name('run_stage_v3.py')
assert hashlib.sha256(predecessor.read_bytes()).hexdigest() == '7db646c1cf517e70f78d4a30d1a4e7841985ed846ef730508015dd4ce23c8d8c'
text = predecessor.read_text()
needle = "code = code.replace('check_resources_v2.py', 'check_resources_v3.py')"
assert text.count(needle) == 1
text = text.replace(needle, needle+"\nassert code.count(\"'--output', str(gate)\") == 1\n"
    "code = code.replace(\"'--output', str(gate)\", \"'--seconds', '30', '--output', str(gate)\")")
exec(compile(text, str(predecessor), 'exec'), globals())
