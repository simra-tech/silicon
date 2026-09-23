#!/usr/bin/env python3
"""Portable orphan-row engineering evidence with original/exported hashes."""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    p=argparse.ArgumentParser();p.add_argument('--bulk',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists();a.output.mkdir(parents=True)
    root=Path(__file__).resolve().parents[5];manifest=[]
    groups={'candidate_r1':'orphan-vdd-row-feed-20260923-r1','pin_cut_audit_r1':'orphan-vdd-row-audit-20260923-r1',
            'stock_main_r1':'orphan-vdd-row-main-20260923-r1','baseline_main':'core-io-power-stock-20260923-r1',
            'candidate_r2':'orphan-vdd-row-feed-20260923-r2','pin_cut_audit_r2':'orphan-vdd-row-audit-20260923-r2',
            'stock_main_r2':'orphan-vdd-row-main-20260923-r2','stock_maximal_r2':'orphan-vdd-row-maximal-20260923-r2',
            'baseline_maximal':'core-io-power-maximal-20260923-r1'}
    for group,folder in groups.items():
        source=a.bulk/folder
        assert source.is_dir()
        for path in sorted(source.rglob('*')):
            if not path.is_file() or path.name=='power_connected_native.gds':continue
            assert path.stat().st_size<8_000_000,path.name
            original=path.read_bytes()
            if path.suffix=='.gds':exported=original
            else:
                exported=original.decode().replace(str(a.bulk),'<results-root>').replace(str(root),'<repo-root>').encode()
                for token in (b'/'+b'home/',b'/'+b'opt/sim/',b'.'+b'private/',a.bulk.name.encode()):assert token not in exported,(path.name,token)
            rel=Path(group)/path.relative_to(source);target=a.output/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(exported)
            manifest.append(dict(path=str(rel),source_run=folder,source_relative=str(path.relative_to(source)),source_sha256=hashlib.sha256(original).hexdigest(),
                source_bytes=len(original),exported_sha256=hashlib.sha256(exported).hexdigest(),exported_bytes=len(exported),byte_identical=original==exported))
    (a.output/'manifest.json').write_text(json.dumps(dict(status='passed compact normalized export',files=manifest,
        normalization='Only results-root and repository-root prefixes; binary GDS unchanged.',omitted='Full candidate GDS retained by hash and reconstruction builder.'),indent=2)+'\n')
    print(json.dumps(dict(files=len(manifest),bytes=sum(r['exported_bytes']for r in manifest))))


if __name__=='__main__':main()
