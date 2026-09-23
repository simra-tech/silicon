#!/usr/bin/env python3
"""Preserve exact identity failure and expose its complete saved-data delta."""
from pathlib import Path

base=Path(__file__).resolve().with_name('audit_pre_purge.py');code=base.read_text()
needle='    assert set(actual)==set(expected)\n'
assert code.count(needle)==1
code=code.replace(needle,"    (a.output/'identity_delta.json').write_text(json.dumps(dict(\n"
    "        status='identity mismatch' if set(actual)!=set(expected) else 'exact identity',\n"
    "        actual_count=len(actual),expected_count=len(expected),\n"
    "        actual_only=sorted(set(actual)-set(expected)),expected_only=sorted(set(expected)-set(actual)),\n"
    "        actual_all=[list(key)+[struct.pack('>d',value).hex()] for key,value in actual.items()],\n"
    "        expected_all=rows),indent=2)+'\\n')\n"+needle)
exec(compile(code,str(base),'exec'),globals())
