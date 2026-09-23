#!/usr/bin/env python3
"""Export compact exact-or-normalized engineering evidence, retaining failures."""
import argparse
import hashlib
import json
from pathlib import Path


def digest(b):return hashlib.sha256(b).hexdigest()


def main():
    p=argparse.ArgumentParser();p.add_argument('--bulk',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--include-main',action='store_true');a=p.parse_args()
    assert not a.output.exists();a.output.mkdir(parents=True)
    groups={
        'native_failed':'antenna-native-supply-audit-20260923-r1',
        'native_passed':'antenna-native-supply-audit-20260923-r2',
        'flat_timeout':'antenna-sealed-supply-audit-20260923-r1',
        'ring_timeout':'antenna-ring-supply-audit-20260923-r1',
        'API_control':'antenna-evaluate-control-20260923-r1',
        'source_binding':'antenna-source-binding-20260923-r1',
        'landing_failed':'antenna-early-landing-20260923-r1',
        'landing_passed':'antenna-early-landing-20260923-r2',
        'additive_candidate':'antenna-early-join-20260923-r1',
        'stock_antenna':'antenna-early-join-stock-20260923-r1',
        'original_stock_failed':'native-sealed-antenna-20260923-r1'}
    if a.include_main:groups['stock_main']='antenna-early-join-main-20260923-r1'
    manifest=[]
    root=Path(__file__).resolve().parents[5]
    for name,folder in groups.items():
        source=a.bulk/folder;assert source.is_dir()
        for path in sorted(source.rglob('*')):
            if not path.is_file():continue
            if path.name in ('sealed_native.gds',):continue
            if path.stat().st_size>8_000_000:continue
            relative=Path(name)/path.relative_to(source)
            original=path.read_bytes()
            if path.suffix=='.gds':exported=original
            else:
                text=original.decode()
                text=text.replace(str(a.bulk),'<results-root>').replace(str(root),'<repo-root>')
                exported=text.encode()
                for token in (b'/'+b'home/',b'/'+b'opt/sim/',b'.'+b'private/',a.bulk.name.encode()):
                    assert token not in exported,(relative,token)
            target=a.output/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(exported)
            manifest.append(dict(path=str(relative),source_run=folder,source_relative=str(path.relative_to(source)),
                source_sha256=digest(original),source_bytes=len(original),exported_sha256=digest(exported),
                exported_bytes=len(exported),byte_identical=original==exported))
    (a.output/'manifest.json').write_text(json.dumps(dict(status='passed compact evidence export',
        files=manifest,normalization='Only results-root and repository-root path prefixes; binary GDS bytes held.',
        omitted='Large full GDS retained by hash and reproducible additive builder; no raw result pruning.'),indent=2)+'\n')
    print(json.dumps(dict(files=len(manifest),bytes=sum(r['exported_bytes']for r in manifest)),indent=2))


if __name__=='__main__':main()
