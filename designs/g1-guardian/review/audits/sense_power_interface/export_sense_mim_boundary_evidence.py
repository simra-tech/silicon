#!/usr/bin/env python3
"""Compact portable native MIM boundary failure, without an extraction claim."""
import argparse,ast,getpass,hashlib,json
from pathlib import Path

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[4]
SOURCES=['SENSE_MIM_BOUNDARY_REVIEW_20260923.md','export_sense_mim_boundary_evidence.py']
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
    p=argparse.ArgumentParser()
    for k in ['bulk_root','output','identity_receipt','stage1_receipt','identity_source','identity_tcl']:
        p.add_argument('--'+k.replace('_','-'),type=Path,required=True)
    a=p.parse_args();a.output=a.output.resolve();a.bulk_root=a.bulk_root.resolve()
    assert not a.output.exists() and HERE in a.output.parents
    groups=['sense-magic-identity-20260923-r1','sense-magic-mim-stage1-20260923-r1']
    identity=json.loads((a.bulk_root/groups[0]/'summary.json').read_text())
    stage=json.loads((a.bulk_root/groups[1]/'summary.json').read_text())
    assert identity['status']=='passed binary/version/unchanged technology load only'
    assert stage['status']=='failed required exposed TOP-plate field rule coverage; extraction not run'
    assert stage['native_plate_uncovered_by_TM1_dbu2']==14617600
    pairs=[]
    for group in groups:
        base=a.bulk_root/group
        for q in sorted(base.rglob('*')):
            if q.is_file():pairs.append((q,Path(group)/q.relative_to(base)))
    for name,folder in [('identity',a.identity_receipt),('stage1',a.stage1_receipt)]:
        for filename in ['run.json','tool.log']:pairs.append((folder/filename,Path('receipts')/name/filename))
    pairs.extend([(a.identity_source,Path('sources')/a.identity_source.name),(a.identity_tcl,Path('sources')/a.identity_tcl.name)])
    assert len({str(x[1])for x in pairs})==len(pairs)
    a.output.mkdir(parents=True);rows=[]
    for q,rel in pairs:
        assert q.is_file() and not q.is_symlink()
        assert q.suffix in ('.json','.log','.py','.tcl','.gds','.mag'),str(q)
        raw=q.read_bytes();portable=raw;binary=q.suffix=='.gds'
        if not binary:
            text=raw.decode()
            for old,new in [(str(a.bulk_root),'${BULK}'),(str(REPO),'${REPO}'),('/work/','${REPO}/'),
                            ('.private/research/verification/','${RECEIPTS}/')]:text=text.replace(old,new)
            assert getpass.getuser() not in text and '/home/' not in text and '/opt/sim/' not in text,rel
            if q.suffix=='.json':json.loads(text)
            if q.suffix=='.py':ast.parse(text)
            portable=text.encode()
        destination=a.output/rel;destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(portable)
        rows.append(dict(path=str(destination.relative_to(REPO)),original_sha256=sha(raw),
            exported_sha256=sha(portable),bytes=len(portable),binary_exact=binary,path_only_sanitized=raw!=portable))
    manifest=dict(status='passed compact evidence export; static coverage FAILED; no extraction',
        artifacts=rows,transformation='Path-prefix-only text sanitization; GDS exact')
    (a.output/'export_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    files=[HERE/x for x in SOURCES]+sorted(q for q in a.output.rglob('*')if q.is_file())
    inventory=dict(status='frozen static MIM coverage failure; no extraction claim',
        files=[dict(path=str(q.relative_to(REPO)),sha256=sha(q.read_bytes()),bytes=q.stat().st_size)for q in files])
    inventory['file_count']=len(files);inventory['total_bytes']=sum(x['bytes']for x in inventory['files'])
    target=a.output/'commit_inventory.json';target.write_text(json.dumps(inventory,indent=2)+'\n')
    print(json.dumps(dict(path=str(target.relative_to(REPO)),sha256=sha(target.read_bytes()),
        file_count=inventory['file_count'],bytes=inventory['total_bytes']),indent=2))
if __name__=='__main__':main()
