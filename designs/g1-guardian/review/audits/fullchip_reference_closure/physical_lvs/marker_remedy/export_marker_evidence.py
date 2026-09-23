#!/usr/bin/env python3
"""Portable source/hash-bound isolated marker and dummy proof evidence."""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import re
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[6]


def digest(b):return hashlib.sha256(b).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--inventory',type=Path,required=True)
    a=ap.parse_args();a.output=a.output.resolve();a.inventory=a.inventory.resolve()
    assert not a.output.exists() and not a.inventory.exists()
    bulk=Path(os.environ['G1_RESULTS_ROOT'])
    folders={
        'preparation':'io-marker-candidate-20260923-r1',
        'secondary_drc':'io-marker-secondary-drc-20260923-r1',
        'rc_drc':'io-marker-rc-drc-20260923-r1',
        'secondary_original_lvs_failed':'io-marker-secondary-lvs-20260923-r1',
        'rc_lvs':'io-marker-rc-lvs-20260923-r1',
        'secondary_prefix_preparation':'io-marker-secondary-prefix-20260923-r1',
        'secondary_prefix_lvs_failed':'io-marker-secondary-prefix-lvs-20260923-r1',
        'dummy_proof_failed':'io-three-dummy-proof-20260923-r1',
        'dummy_proof':'io-three-dummy-proof-20260923-r2',
        'resistor_graph':'io-marker-series-graph-20260923-r1',
        'dummy_extraction_reference':'io-three-dummy-reference-20260923-r1'}
    forbidden=re.compile(rb'/(?:home|opt[/]sim)/|[.]private/')
    a.output.mkdir(parents=True);rows=[]
    for group,folder in folders.items():
        base=bulk/folder;summary=json.loads((base/'summary.json').read_text())
        assert not summary['status'].startswith('running')
        for p in sorted(base.rglob('*')):
            if not p.is_file() or p.name.endswith('.progress.jsonl'):continue
            raw=p.read_bytes();data=raw
            method='byte-identical binary geometry' if p.suffix=='.gds' else 'portable path projection only'
            if p.suffix!='.gds':
                text=raw.decode()
                for old,new in [(str(bulk),'<results>'),(str(ROOT),'<repository>'),
                                ('/work/'+'.'+'private/','<private-context>/'),
                                ('<repository>/'+'.'+'private/','<private-context>/'),
                                ('.'+'private/','<private-context>/')]:text=text.replace(old,new)
                data=text.encode()
                if p.suffix=='.json':json.loads(text)
                if p.suffix=='.py':ast.parse(text)
            assert not forbidden.search(data),str(p)
            dest=a.output/group/p.relative_to(base);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
            rows.append(dict(path=str(dest.relative_to(a.output)),original_sha256=digest(raw),
                             exported_sha256=digest(data),original_bytes=len(raw),exported_bytes=len(data),projection=method))
    (a.output/'manifest.json').write_text(json.dumps(dict(status='passed portable export; original failed checks retained',records=rows),indent=2)+'\n')
    paths=sorted([p for p in HERE.iterdir() if p.is_file() and p.suffix in ('.py','.md')]+[p for p in a.output.rglob('*') if p.is_file()])
    inventory=[]
    for p in paths:
        raw=p.read_bytes();assert not forbidden.search(raw),str(p)
        inventory.append(dict(path=str(p.relative_to(ROOT)),sha256=digest(raw),bytes=len(raw)))
    result=dict(groups={'isolated_IO_marker_and_dummy_boundary':inventory},files=len(inventory),bytes=sum(p['bytes'] for p in inventory))
    a.inventory.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='groups'}))


if __name__=='__main__':main()
