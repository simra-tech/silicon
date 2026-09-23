#!/usr/bin/env python3
"""Exact paired native-context stock marker comparison; no inherited waiver."""
import argparse
import json
from pathlib import Path
from compare_native_markers import load,rows,sha


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline',type=Path,required=True)
    p.add_argument('--candidate',type=Path,required=True)
    p.add_argument('--build',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert not a.output.exists()
    original,old=load(a.baseline);changed,new=load(a.candidate)
    build=json.loads((a.build/'analysis.json').read_text())
    assert build['status'].startswith('passed')
    assert original['GDS_sha256']==build['source_GDS_sha256']=='226c5aad876b9aea1ec2cd5874c828b2ae87ffb80a3efded7f8d9a2389cd8e05'
    assert changed['GDS_sha256']==build['GDS_sha256']==sha(a.build/'candidate_native.gds')
    assert original['stock_rule_hashes']==changed['stock_rule_hashes']
    added=new-old;removed=old-new
    result=dict(status='passed exact native-neighbor marker preservation'if not added and not removed else'failed native-neighbor marker preservation',
        baseline_summary_sha256=sha(a.baseline/'summary.json'),candidate_summary_sha256=sha(a.candidate/'summary.json'),
        build_sha256=sha(a.build/'analysis.json'),script_sha256=sha(Path(__file__)),
        baseline_markers=sum(old.values()),candidate_markers=sum(new.values()),
        added=rows(added),removed=rows(removed),inherited_failures=rows(old&new),
        absolute_stock_acceptance='failed'if new else'passed',
        scope='Exact category/cell/value multiset; no category exclusions, coordinate tolerance or rule waiver.',
        not_run=['final full-assembly stock checks','density/antenna/fullchip LVS/PEX/current qualification','adoption'])
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items()if k!='inherited_failures'},indent=2))
    raise SystemExit(bool(added or removed))


if __name__=='__main__':main()
