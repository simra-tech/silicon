#!/usr/bin/env python3
"""Bind qualified saved-graph diagnostics to the current stock database."""
import hashlib
import json
from pathlib import Path
import sys

wrapper=Path(__file__).resolve()
base=wrapper.parent.parent/'prepare_current_diagnostics.py'
assert hashlib.sha256(base.read_bytes()).hexdigest()=='43a15aa05133d6bf2edb3abae318a7adff050f778c04698354e07bcdde98068a'
output=Path(sys.argv[sys.argv.index('--output')+1])
code=base.read_text()
edits=[
 ('4cffddc5ae8369c9fd5c574cb9571b4641cdee26876370c93bfbe042c4049df2','6b9c5878a81a0ac4d3f68d3d8dbb5fa1927442675606aa6bd46a14d6552def51'),
 ('1b2156355d671e31970482eb3ec8f47b5e4b7bb25d7b111155bfb0ea7306460f','7efa28056f533df4fec8b585654e5445e8d932d4a775747ee5813ae65660cf85'),
 ('gshared-fill-20260923-r4','current-purefill-flat-20260923-r1'),
 ('io-physical-ap-native-lvs-20260923-r1/reports/route_fill_pruned.lvsdb','current-purefill-native-lvs-20260923-r1/reports/pure_fill_flattened.lvsdb'),
 ('route_fill_pruned.gds','pure_fill_flattened.gds'),
 ('io-physical-ap-source-20260923-r2','trip-hard-full-reference-20260923-r1'),
 ('d39ce8512f167545ab2818582bd1e51e88f6402ff810dcf3368cd7d277ddb4d4','94e50a2a7f0646282f4499831bcfe03a2cf8871fbc33a7549b6e8f94fded207b')]
for old,new in edits:
    assert code.count(old)>0,(old,code.count(old))
    code=code.replace(old,new)
exec(compile(code,str(base),'exec'),{'__file__':str(base),'__name__':'__main__'})
(output/'current_binding.json').write_text(json.dumps(dict(base_sha256=hashlib.sha256(base.read_bytes()).hexdigest(),
    wrapper_sha256=hashlib.sha256(wrapper.read_bytes()).hexdigest(),
    effective_source_sha256=hashlib.sha256(code.encode()).hexdigest(),edits=edits),indent=2)+'\n')
