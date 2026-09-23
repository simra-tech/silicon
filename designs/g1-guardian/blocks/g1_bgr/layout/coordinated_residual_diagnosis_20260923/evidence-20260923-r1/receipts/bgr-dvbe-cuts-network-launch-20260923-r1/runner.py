#!/usr/bin/env python3
"""Prospective observer-only successor; preserve the executed V2 launcher."""
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p/'flow/run.sh').is_file())
PRIVATE = ROOT/'.private'/'research/verification'
EXPECTED = {
    'check_resources_v3.py': '1b89ed72334e2715057ecd2c412b038489c6c556ebfa26cd0735f384f7bd45c7',
    'project_cpu_usage_v3.py': '5829d31ef31948e1a328b0a5de31390dff075d5a1b95636417574354090d6a1f',
    'coordinated_resources_v2.py': 'da4d6c9d96a5fc86ba4fe01455a9dbb9e1f9ae095885ea7de2470008810bf6b9',
    'external_storage.py': '81c65931553cdf495bc4c3cf962bff6a7c624d3593b9fee84b2189a9bcb1b434',
}
BASE = HERE/'run_stage.py'
assert hashlib.sha256(BASE.read_bytes()).hexdigest() == '617a1ef220a7342ea284cf28fad81cfd8d60eaae20bff5a40bceedfb0c7de480'
for name, expected in EXPECTED.items():
    assert hashlib.sha256((PRIVATE/name).read_bytes()).hexdigest() == expected, name
receipt = Path(sys.argv[sys.argv.index('--receipt')+1])
assert not receipt.exists()
code = BASE.read_text()
assert code.count('check_resources_v2.py') == 1
code = code.replace('check_resources_v2.py', 'check_resources_v3.py')
try:
    exec(compile(code, str(BASE), 'exec'), globals())
finally:
    if receipt.is_dir():
        (receipt/'observer_bindings.json').write_text(json.dumps(dict(
            scope='resource observer successor only; CPU48 and combined allocation unchanged',
            base_runner_sha256=hashlib.sha256(BASE.read_bytes()).hexdigest(),
            helpers=EXPECTED,
            helpers_unchanged=all(hashlib.sha256((PRIVATE/n).read_bytes()).hexdigest() == h for n,h in EXPECTED.items()),
        ), indent=2)+'\n')
