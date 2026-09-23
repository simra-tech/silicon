#!/usr/bin/env python3
"""Source-bound mechanical R100 derivative of the qualified R62 native flow."""
import argparse,hashlib,json,os,sys
from pathlib import Path

SOURCE='bb933fdabf3fd8a5117bf47f33cd40657caf78ef424e6a9bfddda0f11190d782'
FILES={
    'build':('build_candidate.py','2600bbb9ccd550082f7b7a154e34ecaf61c904ba025dbba2a4373e86f240bb97'),
    'reference':('audit_candidate.py','b5d9eb5e5db390e4df96362e2189596893d880375d4adea2c66d3ca46e34d730'),
    'stock':('run_stock.py','9c6ba7202209537ad1a7c0014f7a280825e5eabaf3e9dd4f846d7736e8659924')}
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def derive(text,stage):
    if stage=='build':
        edits=[('from inspect_passive_sites import lib,pya,sha,regions,native,box,PARENT,SOURCE',
                'from inspect_passive_sites import lib,pya,sha,regions,native,box,PARENT\nSOURCE='+repr(SOURCE),1),
               ('a.cpu==1','a.cpu==0',1),('C45/R62','C45/R100',1),
               ("l='62u'","l='100u'",1),('186.81','224.81',4)]
    else:
        edits=[('from inspect_passive_sites import sha,SOURCE','from inspect_passive_sites import sha\nSOURCE='+repr(SOURCE),1)]
        if stage=='reference':edits += [('(62000,1000,62000000):1','(100000,1000,100000000):1',1)]
        else:edits += [('C45/R62','C45/R100',1),('os.sched_getaffinity(0)=={1}','os.sched_getaffinity(0)=={0}',1),('os.sched_getaffinity(0) == {1}','os.sched_getaffinity(0) == {0}',1)]
    original=text
    for old,new,count in edits:
        assert text.count(old)==count,(stage,old,text.count(old),count)
        text=text.replace(old,new)
    recovered=text
    for old,new,count in reversed(edits):
        assert recovered.count(new)==count,(stage,new)
        recovered=recovered.replace(new,old)
    assert recovered==original
    compile(text,'derived_native_'+stage,'exec')
    return text,edits

def main():
    p=argparse.ArgumentParser(add_help=False);p.add_argument('--stage',choices=FILES,required=True)
    args,remaining=p.parse_known_args();assert os.sched_getaffinity(0)=={0}
    old=Path(__file__).resolve().parent.parent/'coordinated_comp45_rz62'/FILES[args.stage][0]
    assert sha(old)==FILES[args.stage][1]
    output=Path(remaining[remaining.index('--output')+1]);prep=output.with_name(output.name+'-rz100-adapter')
    assert not output.exists() and not prep.exists()
    source=Path(remaining[remaining.index('--source')+1]);assert sha(source)==SOURCE
    text,edits=derive(old.read_text(),args.stage)
    prep.mkdir(parents=True);derived=prep/'derived.py';derived.write_text(text)
    (prep/'adapter.py').write_bytes(Path(__file__).read_bytes())
    (prep/'contract.json').write_text(json.dumps(dict(stage=args.stage,source_sha256=SOURCE,
        parent_helper_sha256=sha(old),derived_helper_sha256=sha(derived),adapter_sha256=sha(Path(__file__)),
        edits=edits,exact_inverse=True,cpu=0,
        geometry_scope='Only main native R62->R100 plus same-net CZ feed shift186.81->224.81um; main C45 and nine external ports held',
        acceptance='All inherited native/channel/source134/geometry-save/strictstock gates unchanged; no source/card/rule changes beyond declared R geometry',
        full_field_model_acceptance='unresolved; no adoption'),indent=2)+'\n')
    sys.path.insert(0,str(old.parent));sys.argv=[str(old)]+remaining
    # Preserve original relative helper lookup. The executed derived text and
    # inverse are separately bound above, not mislabeled as the old source.
    namespace=dict(__file__=str(old),__name__='isolated_rz100_native')
    exec(compile(text,str(derived),'exec'),namespace);namespace['main']()
if __name__=='__main__':main()
