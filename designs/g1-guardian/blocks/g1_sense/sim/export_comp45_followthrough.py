#!/usr/bin/env python3
"""Reversible compact export of completed noise/settling and original failures."""
import argparse,getpass,gzip,hashlib,io,json
from pathlib import Path

def sha(raw):return hashlib.sha256(raw).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,required=True)
    p.add_argument('--bulk-root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert not a.output.exists()
    a.input.resolve().relative_to(a.bulk_root.resolve())
    sim=Path(__file__).resolve().parent;root=sim.parents[4]
    leaves=['nominal/noise','nominal/noise-recovery-r2','rise/dc','rise/step',
            'rise/analysis','fall/dc','fall/step','fall/analysis']
    names={'summary.json','contract.json','provenance.json','runner.py','source.py',
           'candidate.spice','probe.cir','run.log','run.json','run.progress.jsonl',
           'noise.dat','ac.dat','phase0.dat'}
    rows=[];states=[];a.output.mkdir(parents=True)
    for leaf in leaves:
        folder=a.input/leaf;assert folder.is_dir()
        states.append(dict(leaf=leaf,status=json.loads((folder/'summary.json').read_text())['status']))
        for source in sorted(folder.iterdir()):
            if source.name not in names:continue
            assert source.is_file() and not source.is_symlink()
            raw=source.read_bytes();portable=raw
            pairs=[(str(a.bulk_root).encode(),b'${RESULTS_ROOT}'),(b'/work/',b'${REPOSITORY_ROOT}/')]
            for old,new in pairs:portable=portable.replace(old,new)
            restored=portable
            for old,new in reversed(pairs):restored=restored.replace(new,old)
            assert restored==raw
            assert b'/home/' not in portable and getpass.getuser().encode() not in portable
            zipped=source.suffix in {'.json','.dat','.log','.cir','.jsonl'}
            data=portable
            if zipped:
                memory=io.BytesIO()
                with gzip.GzipFile(fileobj=memory,mode='wb',filename='',mtime=0) as stream:stream.write(portable)
                data=memory.getvalue()
            target=a.output/leaf/(source.name+('.gz' if zipped else ''))
            target.parent.mkdir(parents=True,exist_ok=True)
            with target.open('xb') as stream:stream.write(data)
            rows.append(dict(path=str(target.relative_to(a.output)),sha256=sha(data),bytes=len(data),
                original_sha256=sha(raw),portable_decoded_sha256=sha(portable),inverse_exact=True))
    (a.output/'artifact_manifest.json').write_text(json.dumps(dict(status='completed export; original failures preserved',
        records=rows,leaves=states,no_simulation=True,normalization='Bulk root and /work prefix only; exact inverse'),indent=2)+'\n')
    paths=sorted(q for q in a.output.rglob('*') if q.is_file())
    paths += [sim/q for q in ['run_comp45_followthrough.py','test_comp45_followthrough.py',
        'recover_comp45_noise.py','analyze_comp45_settling.py','export_comp45_followthrough.py']]
    paths.append(sim.parent/'reports/COMP45_FOLLOWTHROUGH_20260923.md')
    inventory=[dict(path=str(q.resolve().relative_to(root)),sha256=sha(q.read_bytes()),bytes=q.stat().st_size) for q in paths]
    target=a.output/'commit_inventory.json'
    target.write_text(json.dumps(dict(status='frozen listed files only',files=inventory,
        total_bytes=sum(q['bytes'] for q in inventory),self_excluded=True),indent=2)+'\n')
    print(json.dumps(dict(files=len(inventory),bytes=sum(q['bytes'] for q in inventory),sha256=sha(target.read_bytes()))))

if __name__=='__main__':main()
