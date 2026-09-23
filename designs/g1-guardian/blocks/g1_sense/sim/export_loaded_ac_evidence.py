#!/usr/bin/env python3
"""Compact, reversible path-only export of loaded AC leaves and failed controls."""
import argparse
import getpass
import gzip
import hashlib
import io
import json
from pathlib import Path


def sha(b):return hashlib.sha256(b).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['bulk-root','receipt-root','suite','analysis','output']:
        p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--inventory-only',action='store_true');a=p.parse_args()
    sim=Path(__file__).resolve().parent;root=sim.parents[4]
    if a.inventory_only:
        paths=sorted(f for f in a.output.rglob('*') if f.is_file())
        paths += [sim/n for n in ['run_loaded_ac_audit.py','test_loaded_ac_audit.py','analyze_loaded_ac_audit.py','export_loaded_ac_evidence.py']]
        paths += [sim.parent/'reports/LOADED_AC_20260923.md']
        destination=a.output/'commit_inventory.json';assert not destination.exists()
        rows=[dict(path=str(f.resolve().relative_to(root)),sha256=sha(f.read_bytes()),bytes=f.stat().st_size) for f in paths]
        destination.write_text(json.dumps(dict(status='frozen exact listed files only',files=rows,total_bytes=sum(r['bytes'] for r in rows),self_excluded=True),indent=2)+'\n')
        print(json.dumps(dict(files=len(rows),bytes=sum(r['bytes'] for r in rows),sha256=sha(destination.read_bytes()))));return
    assert not a.output.exists();a.output.mkdir(parents=True);records=[]
    def add(source,rel):
        raw=source.read_bytes()
        substitutions=[(str(a.bulk_root).encode(),b'${RESULTS_ROOT}'),(b'/work/',b'${REPOSITORY_ROOT}/')]
        cooked=raw
        for old,new in substitutions:cooked=cooked.replace(old,new)
        restored=cooked
        for old,new in reversed(substitutions):restored=restored.replace(new,old)
        assert restored==raw
        assert getpass.getuser().encode() not in cooked and b'/home/' not in cooked
        target=a.output/rel;target.parent.mkdir(parents=True,exist_ok=True)
        payload=cooked
        if target.suffix=='.gz':
            stream=io.BytesIO()
            with gzip.GzipFile(fileobj=stream,mode='wb',filename='',mtime=0) as zipped:zipped.write(cooked)
            payload=stream.getvalue()
        target.write_bytes(payload)
        records.append(dict(path=str(target.relative_to(a.output)),sha256=sha(payload),bytes=len(payload),original_sha256=sha(raw),decoded_portable_sha256=sha(cooked),path_normalization_applied=raw!=cooked,inverse_exact=True))
    folders=[('baseline-r1',a.bulk_root/'sense-loaded-ac-baseline-20260923-r1'),('baseline-r2',a.bulk_root/'sense-loaded-ac-baseline-20260923-r2')]
    folders += [(mode,a.suite/mode) for mode in ['differential','common','psrr_vdda','psrr_vdd','tian_voltage','tian_current']]
    for label,folder in folders:
        names=['summary.json','contract.json','provenance.json','runner.py','probe.cir','run.log','ac.dat']
        if label.startswith('tian_'):names.append('probe.spice')
        if label in ['differential','common']:names.append('input_basis.dat')
        for name in names:
            add(folder/name,Path(label)/(name+('.gz' if name in ['probe.cir','probe.spice','run.log'] else '')))
        receipt='sense_loaded_ac_'+label.replace('-r','_20260923_r') if label.startswith('baseline-') else 'sense_loaded_ac_'+label+'_20260923_r1'
        add(a.receipt_root/receipt/'tool.log',Path(label)/'bounded_tool.log.gz')
    for name in ['summary.json','return_ratio.json']:add(a.analysis/name,Path('analysis')/name)
    (a.output/'artifact_manifest.json').write_text(json.dumps(dict(status='passed compact export; evidence dispositions unchanged',records=records,normalization='Configured results root and fixed /work prefix only; exact inverse. gzip mtime0.',no_simulation=True),indent=2)+'\n')
    print(json.dumps(dict(files=len(records),bytes=sum(r['bytes'] for r in records))))


if __name__=='__main__':main()
