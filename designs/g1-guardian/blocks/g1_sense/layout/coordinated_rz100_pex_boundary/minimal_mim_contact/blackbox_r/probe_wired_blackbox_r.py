#!/usr/bin/env python3
"""Run stock blackboxed R extraction on the DRC/LVS-controlled wired coupon."""
import hashlib
from pathlib import Path

parent = Path(__file__).resolve().parents[1] / 'probe_coupon.py'
original = parent.read_text()
assert hashlib.sha256(original.encode()).hexdigest() == 'c54fdb2c345bff605e430bb951affc27a3dea0048621e2ac2e7b59f5c547bb36'
changes = [
    ("manifest['status'] == 'passed native coupon geometry preparation'",
     "manifest['status'] == 'prepared native CMIM plus external access-metal diagnostic'"),
    ("sha(gds) == manifest['GDS_sha256'] == '546c3e33d3894fb4c0d54c623a0cd2ac261cbf074a44d210240921c86194fd20'",
     "sha(gds) == manifest['GDS_sha256'] and manifest['source_GDS_sha256'] == '546c3e33d3894fb4c0d54c623a0cd2ac261cbf074a44d210240921c86194fd20'"),
    ("'--mode', args.mode, '--blackbox', 'false'",
     "'--mode', args.mode, '--blackbox', 'true'"),
    ("context = KLayoutExtractionContext.prepare_extraction(db, 'sense_mim_method_control', tech, False)",
     "context = KLayoutExtractionContext.prepare_extraction(db, 'sense_mim_method_control', tech, True)"),
    ("source_changes='none', model_deck_changes='none',",
     "source_changes='access-metal stubs only', model_deck_changes='none', blackbox_devices=True,"),
]
derived = original
for old, new in changes:
    assert derived.count(old) == 1
    derived = derived.replace(old, new)
restored = derived
for old, new in reversed(changes):
    assert restored.count(new) == 1
    restored = restored.replace(new, old)
assert restored == original
exec(compile(derived, str(parent) + '[wired-blackbox-R]', 'exec'),
     dict(__name__='__main__', __file__=str(parent)))
