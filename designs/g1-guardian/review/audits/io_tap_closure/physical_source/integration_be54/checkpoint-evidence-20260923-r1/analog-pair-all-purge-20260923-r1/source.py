#!/usr/bin/env python3
"""Independent native-token binding plus bit-exact diagnostic restoration."""
import hashlib
from pathlib import Path

base=Path(__file__).resolve().with_name('audit_pre_purge_r2.py')
assert hashlib.sha256(base.read_bytes()).hexdigest()=='8776e28840a4259d2e38c73ebe18a871f86075472239f2a713675ea7d7958dc1'
code=base.read_text();needle='from l2n_device_bijection import bind'
assert code.count(needle)==1
code=code.replace(needle,'from l2n_device_bijection_r2 import bind')
exec(compile(code,str(base),'exec'),globals())
