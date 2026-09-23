#!/usr/bin/env python3
"""Exact R100 derivative of completed own-source followthrough/zero-C methods."""
import argparse,hashlib,json,os,sys
from pathlib import Path
from expose_rz100_internal_nodes import SOURCE
PARENT='b8912a862b61554266239634dd388ed0ffad229c0b0e48819ad129d589352e97'
FILES={'followthrough':('run_comp45_followthrough.py','5e733a49ad15e797c410269a144c51ff0c15da91e9f978944a68e79601c08da3'),
       'zero_c':('run_comp45_private_zero_c.py','ea036bd0e17c0604062efd35974d5f350589d43339a4c53a09ddb43e7eec7882')}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def derive(text,stage):
    if stage=='followthrough':edits=[
        ('from compensation_runtime_affinity import verify_cpu','import os\ndef verify_cpu(cpu):\n    assert cpu in (1,7) and os.sched_getaffinity(0)=={cpu}'),
        (PARENT,SOURCE),("candidate=candidate_source(original,'62','45')","candidate=candidate_source(original,'62','45')\n    from prepare_comp45_rz_remedy import change\n    candidate=change(candidate,100)"),
        ('choices=[1,6]','choices=[1,7]'),('C45/R62','C45/R100')]
    else:edits=[('from expose_comp45_internal_nodes import expose,SOURCE','from expose_rz100_internal_nodes import expose,SOURCE'),
        ('from test_expose_comp45_internal_nodes import tests as topology_tests','from expose_rz100_internal_nodes import topology_tests')]
    original=text;ledger=[]
    for x,y in edits:
        count=text.count(x);assert count==(2 if x=='C45/R62' else 1),(x,count)
        text=text.replace(x,y);ledger.append((x,y,count))
    restored=text
    for x,y,count in reversed(ledger):assert restored.count(y)==count;restored=restored.replace(y,x)
    assert restored==original;compile(text,'rz100_followthrough','exec');return text,ledger
def main():
    p=argparse.ArgumentParser(add_help=False);p.add_argument('--stage',choices=FILES,required=True);a,remaining=p.parse_known_args()
    cpu=int(remaining[remaining.index('--cpu')+1]);assert cpu in (1,7) and os.sched_getaffinity(0)=={cpu}
    old=Path(__file__).resolve().parent/FILES[a.stage][0];assert sha(old)==FILES[a.stage][1]
    text,edits=derive(old.read_text(),a.stage)
    out=Path(remaining[remaining.index('--output')+1]);prep=out.with_name(out.name+'-adapter');assert not prep.exists() and not out.exists()
    prep.mkdir(parents=True);derived=prep/'derived.py';derived.write_text(text);(prep/'adapter.py').write_bytes(Path(__file__).read_bytes())
    (prep/'contract.json').write_text(json.dumps(dict(stage=a.stage,original_helper_sha256=sha(old),derived_sha256=sha(derived),edits=edits,exact_inverse=True,
        source_sha256=SOURCE,criteria='Original same-source OP/fullparameters/wave/noise units; no old-source or population inheritance'),indent=2)+'\n')
    sys.argv=[str(old)]+remaining;scope=dict(__file__=str(old),__name__='rz100_followthrough')
    exec(compile(text,str(derived),'exec'),scope);scope['main']()
if __name__=='__main__':main()
