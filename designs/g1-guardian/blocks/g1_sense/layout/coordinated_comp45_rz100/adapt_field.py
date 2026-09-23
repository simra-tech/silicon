#!/usr/bin/env python3
"""Exact source/native-bound R100 views and unchanged partial CC engine."""
import argparse,hashlib,json,os,sys
from pathlib import Path
SOURCE='bb933fdabf3fd8a5117bf47f33cd40657caf78ef424e6a9bfddda0f11190d782'
NATIVE='450a49062d17f65be1046736c2ebeff219b4c4d4b22fac0998940c158741a637'
R62_SOURCE='b8912a862b61554266239634dd388ed0ffad229c0b0e48819ad129d589352e97'
R62_NATIVE='cec94187d33b60a654cb12213cfb7e0904fc2a0b5d70a3763fd9d223f44d34f7'
FILES={'prepare':('prepare_affected_field_views.py','1b9fa28fb7b55d026f03aa1960f92ece5c0e9202f7110fcdab9ddb100a6b38ab'),
       'extract':('extract_affected_field_cc.py','12b4a0611b1ea88ae2cf3bdd22bb7701ed4b28c074252f152ee179fb725707d7')}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser(add_help=False);p.add_argument('--stage',choices=FILES,required=True);a,remaining=p.parse_known_args()
    assert os.sched_getaffinity(0)=={0}
    old=Path(__file__).resolve().parent.parent/'coordinated_comp45_rz62'/FILES[a.stage][0]
    assert sha(old)==FILES[a.stage][1];text=old.read_text();original=text
    edits=[('os.sched_getaffinity(0)=={1}','os.sched_getaffinity(0)=={0}')]
    if a.stage=='prepare':edits += [
        ('from inspect_passive_sites import pya,sha,regions,PARENT,SOURCE','from inspect_passive_sites import pya,sha,regions\nPARENT='+repr(R62_NATIVE)+'\nSOURCE='+repr(SOURCE)),
        ("OLD_SOURCE='baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877'",'OLD_SOURCE='+repr(R62_SOURCE)),
        ('NEW_GDS='+repr(R62_NATIVE),'NEW_GDS='+repr(NATIVE))]
    for x,y in edits:assert text.count(x)==1;x_count=text.count(x);text=text.replace(x,y)
    restored=text
    for x,y in reversed(edits):assert restored.count(y)==1;restored=restored.replace(y,x)
    assert restored==original
    out=Path(remaining[remaining.index('--output')+1]);prep=out.with_name(out.name+'-adapter');assert not prep.exists() and not out.exists()
    prep.mkdir(parents=True);derived=prep/'derived.py';derived.write_text(text);(prep/'adapter.py').write_bytes(Path(__file__).read_bytes())
    (prep/'contract.json').write_text(json.dumps(dict(stage=a.stage,old_helper_sha256=sha(old),derived_sha256=sha(derived),edits=edits,exact_inverse=True,
        source_sha256=SOURCE,native_sha256=NATIVE,full_field_coverage='FAILED/unresolved; no method/stack/material/model changes'),indent=2)+'\n')
    sys.path.insert(0,str(old.parent));sys.argv=[str(old)]+remaining
    namespace=dict(__file__=str(old),__name__='rz100_field');exec(compile(text,str(derived),'exec'),namespace);namespace['main']()
if __name__=='__main__':main()
