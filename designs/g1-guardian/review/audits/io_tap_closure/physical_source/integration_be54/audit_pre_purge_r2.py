#!/usr/bin/env python3
"""Use proved document/reader ID bijection before exact sidecar recovery."""
import hashlib
from pathlib import Path
import sys

here=Path(__file__).resolve().parent;sys.path.insert(0,str(here))
from l2n_device_bijection import bind
base=here/'audit_pre_purge.py'
assert hashlib.sha256(base.read_bytes()).hexdigest()=='6bc27cf9a8a597d5a4f0af932e4a925222608ad1012154604ec3beb420174029'
code=base.read_text();old='rows=json.loads(a.sidecar.read_text());expected='
assert code.count(old)==1
code=code.replace(old,'rows=bind(a.snapshot,nl,json.loads(a.sidecar.read_text()),a.output);expected=')
exec(compile(code,str(base),'exec'),globals())
