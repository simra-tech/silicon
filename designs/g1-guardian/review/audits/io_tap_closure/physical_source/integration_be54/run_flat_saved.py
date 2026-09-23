#!/usr/bin/env python3
"""Input-only saved-data control successors for the exact overlay-flattened view."""
import hashlib
import json
from pathlib import Path
import sys

successor=Path(__file__).resolve()
index=sys.argv.index('--stage');stage=sys.argv[index+1];del sys.argv[index:index+2]
choices={
 'diagnostics':('prepare_diagnostics.py','094a89f8ef9e96542877bf95d320401e2b2e2f3dbc8b027a35d9e3a65acaa9cb'),
 'dummy':('prove_dummies.py','557e86cdf5bac5f18e92bdee76bf12079a89328c542f3acb0fe47be29d919e84'),
 'comparison':('run_comparison.py','bb7ac611cae3789484ea1edc3182e22148b698186bdece725e9ccdb46c92468b')}
filename,expected=choices[stage];base=successor.with_name(filename)
assert hashlib.sha256(base.read_bytes()).hexdigest()==expected
output=Path(sys.argv[sys.argv.index('--output')+1])
code=base.read_text();edits=[]
for old,new in [
 ('wrapper=Path(__file__).resolve()','wrapper=SUCCESSOR_WRAPPER'),
 ('analog-pair-integration-20260923-r1','analog-pair-overlay-flat-20260923-r1'),
 ('analog_pair_native.gds','overlay_flattened.gds'),
 ('be54644ebfffdc85bf4ed136966a31e60f374290b9ba7bd179753aa0b038d307','dcca5f47f6d397e8c6811116f092ac0f9adbbe761617a87ba69cec8216417333'),
 ('analog-pair-native-lvs-20260923-r1/reports/analog_pair_native.lvsdb','analog-pair-flat-native-lvs-20260923-r1/reports/overlay_flattened.lvsdb'),
 ('analog-pair-diagnostics-20260923-r1','analog-pair-flat-diagnostics-20260923-r1'),
 ('analog-pair-dummy-proof-20260923-r1','analog-pair-flat-dummy-proof-20260923-r1')]:
    count=code.count(old)
    if count:
        edits.append(dict(old=old,new=new,count=count));code=code.replace(old,new)
assert len(edits)>=2
exec(compile(code,str(base),'exec'),{'__file__':str(base),'__name__':'__main__','SUCCESSOR_WRAPPER':successor})
(output/'flat_successor_binding.json').write_text(json.dumps(dict(stage=stage,base_sha256=expected,
    wrapper_sha256=hashlib.sha256(successor.read_bytes()).hexdigest(),edits=edits),indent=2)+'\n')
