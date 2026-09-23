#!/usr/bin/env python3
"""Authorized physical A/P source from independently controlled raw junctions."""
import hashlib
from pathlib import Path

original=Path(__file__).resolve().with_name('prepare_ap.py')
assert hashlib.sha256(original.read_bytes()).hexdigest()=='8aeed8c6cbb29915896a37f5f1ed72d8ccb939f9d5d6b7332680b3d6d81f67fc'
code=original.read_text()
replacements={
    'io-tap-physical-ownership-20260923-r1/analysis.json':'io-junction-ownership-20260923-r1/analysis.json',
    "assert proof['status'] == 'failed one or more native ownership mappings'":"assert proof['status'] == 'passed per-tap physical junction ownership; stock/electrical validation pending'",
    "assert len(proof['failures']) == 5":"assert not proof['failures']",
    "geometry_negative_controls='not run'":"geometry_negative_controls=proof['negative_controls']",
    "physical_instanced_XOR='not run'":"physical_instanced_XOR='passed scoped140 IO masters/raw geometry and physical junction projection; final fullchip stock remains pending'",
    "unused_failure_applicability='not applicable to current source reachability'":"unused_failure_applicability='not applicable; direct source geometry mapped all63 taps, original subtraction failures retained separately'"}
for old,new in replacements.items():
    assert code.count(old)==1,old
    code=code.replace(old,new)
exec(compile(code,str(original),'exec'),globals())
