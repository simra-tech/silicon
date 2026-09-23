#!/usr/bin/env python3
"""Compact reversible export; failed original and separate analysis stay separate."""
import argparse
import getpass
import gzip
import hashlib
import io
import json
from pathlib import Path


def digest(raw):return hashlib.sha256(raw).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bulk-root',type=Path,required=True)
    p.add_argument('--candidate',action='append',required=True,help='label=folder')
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert not a.output.exists()
    sim=Path(__file__).resolve().parent;root=sim.parents[4]
    candidates=[]
    for entry in a.candidate:
        label,folder=entry.split('=',1)
        assert label.replace('-','').isalnum()
        folder=Path(folder).resolve();folder.relative_to(a.bulk_root.resolve())
        candidates.append((label,folder))
    assert len({n for n,_ in candidates})==len(candidates)
    a.output.mkdir(parents=True);records=[];leaves=[]
    names=['summary.json','contract.json','provenance.json','runner.py','source.py',
           'candidate.spice','probe.spice','probe.cir','run.log','run.json','ac.dat',
           'input_basis.dat','return_ratio.json']
    for label,folder in candidates:
        for case in ['nominal','slow','fast']:
            for mode in ['differential','tian_voltage','tian_current',
                         'differential-recovery-r2','differential-bounded-dc-r2','differential-own-source-r2',
                         'analysis-differential','analysis-loop','analysis-saved-state']:
                leaf=folder/case/mode;summary=leaf/'summary.json'
                state=json.loads(summary.read_text()) if summary.exists() else {}
                leaves.append(dict(candidate=label,case=case,mode=mode,
                    status=state.get('status','not run' if not leaf.exists() else 'failed missing summary'),
                    original_failure_status=state.get('original_failure_status'),
                    conditional_PM_status=state.get('conditional_PM_status'),
                    conditional_GM_status=state.get('conditional_GM_status')))
                for name in names:
                    source=leaf/name
                    if not source.exists():continue
                    raw=source.read_bytes();portable=raw
                    pairs=[(str(a.bulk_root).encode(),b'${RESULTS_ROOT}'),(b'/work/',b'${REPOSITORY_ROOT}/')]
                    for old,new in pairs:portable=portable.replace(old,new)
                    restored=portable
                    for old,new in reversed(pairs):restored=restored.replace(new,old)
                    assert restored==raw
                    assert b'/home/' not in portable and getpass.getuser().encode() not in portable
                    payload=portable;suffix=''
                    if name in ['summary.json','probe.cir','probe.spice','run.log','return_ratio.json']:
                        suffix='.gz';buffer=io.BytesIO()
                        with gzip.GzipFile(fileobj=buffer,mode='wb',filename='',mtime=0) as stream:stream.write(portable)
                        payload=buffer.getvalue()
                    target=a.output/label/case/mode/(name+suffix)
                    target.parent.mkdir(parents=True,exist_ok=True)
                    with target.open('xb') as stream:stream.write(payload)
                    records.append(dict(path=str(target.relative_to(a.output)),sha256=digest(payload),
                        bytes=len(payload),original_sha256=digest(raw),
                        decoded_portable_sha256=digest(portable),inverse_exact=True))
    manifest=a.output/'artifact_manifest.json'
    manifest.write_text(json.dumps(dict(status='completed export; no status promotion',
        records=records,leaves=leaves,no_simulation=True,
        normalization='Configured bulk root and /work prefix only; exact inverse'),indent=2)+'\n')
    sources=['run_loaded_compensation_candidate.py','test_loaded_compensation_candidate.py',
             'analyze_loaded_compensation_candidate.py','recover_compensation_scale_audit.py',
             'qualify_compensation_dc_candidate.py','test_compensation_dc_candidate.py',
             'analyze_compensation_saved_state.py',
             'compensation_runtime_affinity.py','test_compensation_runtime_affinity.py',
             'export_compensation_candidates.py']
    paths=sorted(p for p in a.output.rglob('*') if p.is_file())+[sim/n for n in sources]
    paths.append(sim.parent/'reports/COMPENSATION_CANDIDATES_20260923.md')
    rows=[dict(path=str(p.resolve().relative_to(root)),sha256=digest(p.read_bytes()),bytes=p.stat().st_size) for p in paths]
    inventory=a.output/'commit_inventory.json'
    inventory.write_text(json.dumps(dict(status='frozen exact listed files only',files=rows,
        total_bytes=sum(r['bytes'] for r in rows),self_excluded=True),indent=2)+'\n')
    print(json.dumps(dict(files=len(rows),bytes=sum(r['bytes'] for r in rows),sha256=digest(inventory.read_bytes()))))


if __name__=='__main__':main()
