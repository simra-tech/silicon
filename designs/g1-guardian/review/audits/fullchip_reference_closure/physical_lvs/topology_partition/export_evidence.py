#!/usr/bin/env python3
"""Portable saved-partition evidence with original/exported byte provenance."""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[6]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--inventory', type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists() and not a.inventory.exists()
    bulk = Path(os.environ['G1_RESULTS_ROOT'])
    private = ROOT / '.private'
    receipt = private / 'research/verification/full_io_topology_partition_20260923_r1'
    roots = dict(observation=bulk/'full-io-topology-partition-20260923-r1',
                 accounting=bulk/'full-io-topology-accounting-20260923-r1')
    paths = [(group,q,q.relative_to(base)) for group,base in roots.items()
             for q in sorted(base.rglob('*')) if q.is_file()]
    paths += [('receipt',receipt/name,Path(name)) for name in ('runner.py','run.log','run.json')]
    paths += [('held_scope_control',bulk/'fullchip-substrate-scope-20260923-r2/diagnostic/summary.json',Path('summary.json'))]
    a.output.mkdir(parents=True)
    manifest = []
    forbidden = re.compile(rb'/(?:home|opt[/]sim)/|[.]private/')
    for group,path,relative in paths:
        raw = path.read_bytes()
        text = raw.decode()
        for old,new in ((str(private),'<private-context>'),(str(bulk),'<results>'),(str(ROOT),'<repository>')):
            text = text.replace(old,new)
        data = text.encode()
        assert not forbidden.search(data), path
        if path.suffix == '.json':json.loads(data)
        if path.suffix == '.py':ast.parse(text)
        out = a.output/group/relative
        out.parent.mkdir(parents=True,exist_ok=True)
        out.write_bytes(data)
        manifest.append(dict(path=str(out.relative_to(a.output)),original_sha256=digest(raw),
                             exported_sha256=digest(data),original_bytes=len(raw),exported_bytes=len(data),
                             method='machine path projection only; all numerical and graph records preserved'))
    resource_path = receipt/'resources.json'
    resource = json.loads(resource_path.read_text())
    safe = {k:resource[k] for k in ('status','checks','utc','project_cpu_budget','ram_available_bytes',
                                   'effective_storage_free_bytes','expected_growth_gib','inodes_free')}
    safe['original_sha256'] = digest(resource_path.read_bytes())
    (a.output/'resource_metrics.json').write_text(json.dumps(safe,indent=2)+'\n')
    (a.output/'manifest.json').write_text(json.dumps(dict(status='passed portable evidence export',records=manifest),indent=2)+'\n')
    rows = []
    for path in sorted(q for q in HERE.rglob('*') if q.is_file() and '__pycache__' not in q.parts):
        raw = path.read_bytes()
        assert not forbidden.search(raw),path
        rows.append(dict(path=str(path.relative_to(ROOT)),sha256=digest(raw),bytes=len(raw)))
    result = dict(groups=dict(source_native_substrate_partition=rows),files=len(rows),bytes=sum(r['bytes'] for r in rows))
    a.inventory.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='groups'}))


if __name__ == '__main__':
    main()
