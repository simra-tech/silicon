#!/usr/bin/env python3
"""Input-only successor of the exact saved-graph and physical-port controls."""
import hashlib
import json
import sys
from pathlib import Path

wrapper=Path(__file__).resolve()
base=wrapper.parent.parent/'prepare_current_diagnostics.py'
assert hashlib.sha256(base.read_bytes()).hexdigest()=='43a15aa05133d6bf2edb3abae318a7adff050f778c04698354e07bcdde98068a'
index=sys.argv.index('--database-sha256');dbhash=sys.argv[index+1]
assert len(dbhash)==64 and all(c in '0123456789abcdef' for c in dbhash)
del sys.argv[index:index+2]
output=Path(sys.argv[sys.argv.index('--output')+1])
code=base.read_text()
edits=[
 ('4cffddc5ae8369c9fd5c574cb9571b4641cdee26876370c93bfbe042c4049df2','be54644ebfffdc85bf4ed136966a31e60f374290b9ba7bd179753aa0b038d307'),
 ('1b2156355d671e31970482eb3ec8f47b5e4b7bb25d7b111155bfb0ea7306460f',dbhash),
 ('gshared-fill-20260923-r4','analog-pair-integration-20260923-r1'),
 ('io-physical-ap-native-lvs-20260923-r1/reports/route_fill_pruned.lvsdb','analog-pair-native-lvs-20260923-r1/reports/analog_pair_native.lvsdb'),
 ('route_fill_pruned.gds','analog_pair_native.gds'),
 ('io-physical-ap-source-20260923-r2','analog-pair-reference-20260923-r1'),
 ('d39ce8512f167545ab2818582bd1e51e88f6402ff810dcf3368cd7d277ddb4d4','35b4b45b11427e327bc8a2cd145c27c70c102d00dd388a0199a0d19a96695f51')]
ledger=[]
for old,new in edits:
    count=code.count(old);assert count>0,(old,count)
    ledger.append(dict(old=old,new=new,count=count));code=code.replace(old,new)
exec(compile(code,str(base),'exec'),{'__file__':str(base),'__name__':'__main__'})
(output/'successor_binding.json').write_text(json.dumps(dict(base_sha256=hashlib.sha256(base.read_bytes()).hexdigest(),
    wrapper_sha256=hashlib.sha256(wrapper.read_bytes()).hexdigest(),edits=ledger,
    effective_source_sha256=hashlib.sha256(code.encode()).hexdigest()),indent=2)+'\n')
(output/'successor_source.py').write_text(code)
