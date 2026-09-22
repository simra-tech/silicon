#!/usr/bin/env python3
"""Fix only the read-only pya terminal lookup; preserve the failed first audit."""
from pathlib import Path
import hashlib
import json

here = Path(__file__).resolve().parent
original = here / 'audit_buffer_stock_junctions.py'
text = original.read_text()
assert text.count('device.net_for_terminal(term.id)') == 1
text = text.replace('device.net_for_terminal(term.id)', 'device.net_for_terminal(term.name)')
assert text.count('source-faithful-buffer-stock-junctions-20260922-r1.json') == 1
text = text.replace('source-faithful-buffer-stock-junctions-20260922-r1.json', 'source-faithful-buffer-stock-junctions-20260922-r2.json')
scope = {'__file__': str(Path(__file__)), '__name__': 'readonly_r2'}
exec(compile(text, str(original), 'exec'), scope)
scope['main']()
out = here / 'source-faithful-buffer-stock-junctions-20260922-r2.json'
result = json.loads(out.read_text())
result.update(original_audit_sha256=hashlib.sha256(original.read_bytes()).hexdigest(),
              declared_change='Use documented terminal-name overload instead of bound id method; no database/source change',
              original_audit_status='failed TypeError before output; retained')
out.write_text(json.dumps(result, indent=2) + '\n')
