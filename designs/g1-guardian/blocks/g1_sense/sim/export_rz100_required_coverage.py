#!/usr/bin/env python3
"""Portable completed rejection/DC evidence; no simulation or git mutation."""
import argparse,getpass,gzip,hashlib,io,json
from pathlib import Path
def sha(raw):return hashlib.sha256(raw).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--bulk-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    sim=Path(__file__).resolve().parent;root=sim.parents[4]
    folders=['sense-rz100-rejection-20260923-r1','sense-rz100-dc-grid-preparation-20260923-r1','sense-rz100-dc-grid-20260923-r1','sense-rz100-dc-grid-audit-20260923-r1']
    final=json.loads((a.bulk_root/folders[-1]/'summary.json').read_text());assert final['tuples']==108 and final['all_source_runtime_finite_checks']=='passed'
    assert final['status'] in ['passed full declared standalone grid','failed original gain requirement']
    for mode in ['common','psrr_vdda','psrr_vdd']:
        assert json.loads((a.bulk_root/folders[0]/mode/'summary.json').read_text())['status']=='passed source/OP/finite conditional rejection leaf'
    records=[];a.output.mkdir(parents=True)
    for name in folders:
        sourcebase=a.bulk_root/name;assert sourcebase.is_dir()
        for q in sorted(sourcebase.rglob('*')):
            if not q.is_file():continue
            assert not q.is_symlink();raw=q.read_bytes();portable=raw
            pairs=[(str(a.bulk_root).encode(),b'${RESULTS_ROOT}'),(str(root).encode(),b'${REPOSITORY_ROOT}'),(b'/work/',b'${CONTAINER_REPOSITORY_ROOT}/')]
            for old,new in pairs:portable=portable.replace(old,new)
            inverse=portable
            for old,new in reversed(pairs):inverse=inverse.replace(new,old)
            assert inverse==raw and getpass.getuser().encode() not in portable and str(Path.home()).encode() not in portable
            zipped=q.suffix in ['.json','.jsonl','.dat','.log','.cir'];data=portable
            if zipped:
                buffer=io.BytesIO()
                with gzip.GzipFile(filename='',mode='wb',fileobj=buffer,mtime=0) as stream:stream.write(portable)
                data=buffer.getvalue()
            target=a.output/q.relative_to(a.bulk_root)
            if zipped:target=target.with_name(target.name+'.gz')
            target.parent.mkdir(parents=True,exist_ok=True)
            with target.open('xb') as stream:stream.write(data)
            records.append(dict(path=str(target.relative_to(a.output)),sha256=sha(data),original_sha256=sha(raw),decoded_sha256=sha(portable),bytes=len(data),inverse_exact=True))
    (a.output/'artifact_manifest.json').write_text(json.dumps(dict(status='completed evidence export; all scoped statuses retained',records=records,full_PEX='not qualified',adoption='not run',no_new_simulation=True),indent=2)+'\n')
    helpers=['run_rz100_rejection.py','prepare_rz100_dc_grid.py','run_rz100_dc_grid.py','audit_rz100_dc_grid.py','export_rz100_required_coverage.py']
    paths=sorted(q for q in a.output.rglob('*') if q.is_file())+[sim/n for n in helpers]+[sim.parent/'reports/RZ100_REQUIRED_COVERAGE_20260923.md']
    inventory=[dict(path=str(q.resolve().relative_to(root)),sha256=sha(q.read_bytes()),bytes=q.stat().st_size) for q in paths]
    target=a.output/'commit_inventory.json';target.write_text(json.dumps(dict(status='frozen listed files only',files=inventory,total_bytes=sum(q['bytes'] for q in inventory),self_excluded=True),indent=2)+'\n')
    print(json.dumps(dict(files=len(inventory),bytes=sum(q['bytes'] for q in inventory),inventory_sha256=sha(target.read_bytes()))))
if __name__=='__main__':main()
