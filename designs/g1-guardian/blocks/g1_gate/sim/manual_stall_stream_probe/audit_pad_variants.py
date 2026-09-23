#!/usr/bin/env python3
"""Independent emitted-deck inverse checks; no numerical or physical acceptance."""
import argparse
import hashlib
import json
from pathlib import Path

def audit(base, candidate, edits):
    restored=candidate
    for old,new in edits:
        assert base.count(old)==1 and restored.count(new)==1
        restored=restored.replace(new,old)
    assert restored==base

p=argparse.ArgumentParser()
p.add_argument('--baseline',type=Path,required=True)
p.add_argument('--tight',type=Path,required=True)
p.add_argument('--trap',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
assert not a.output.exists()
base=a.baseline.read_text()
assert base.count('XPAD ')==1 and 'sg13g2_IOPadOut4mA' in base
assert '\nCOUT pad_out 0 20p\n' in base and '\n.tran 1n 16u 0 1n\n' in base
result={'checks':{},'deck_sha256':{},'electrical_acceptance':'not run'}
variants=[
 ('tight',a.tight,[('reltol=0.005','reltol=0.001'),('abstol=1e-9','abstol=1e-12'),
                  ('vntol=1e-5','vntol=1e-6'),('chgtol=1e-13','chgtol=1e-15')]),
 ('trap',a.trap,[('method=gear','method=trap')]),
]
result['deck_sha256']['baseline']=hashlib.sha256(a.baseline.read_bytes()).hexdigest()
for label,path,edits in variants:
    candidate=path.read_text()
    audit(base,candidate,edits)
    result['checks'][label+'_exact_inverse']='passed'
    try:
        audit(base,candidate.replace('COUT pad_out 0 20p','COUT pad_out 0 21p'),edits)
    except AssertionError:
        result['checks'][label+'_changed_load_rejected']='passed'
    else:
        raise AssertionError('unexpected circuit change was accepted')
    result['deck_sha256'][label]=hashlib.sha256(path.read_bytes()).hexdigest()
a.output.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
