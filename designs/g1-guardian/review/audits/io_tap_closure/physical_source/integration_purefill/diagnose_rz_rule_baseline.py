#!/usr/bin/env python3
"""Read-only exact rule-tree baseline delta, for wrapper diagnostics."""
import argparse
import json
import os
from pathlib import Path
import current_rz_bindings as b
import current_rz_stock_preconditions as p
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    assert not a.output.exists()
    root=Path(os.environ['PDK_ROOT'])/os.environ['PDK']
    cases={
      'lvs':(json.loads(b.bound(b.STOCK_LVS_RULE_BASELINE).read_text())['stock_rule_hashes'],'libs.tech/klayout/tech/lvs'),
      'tech':(json.loads(b.bound(b.PHYSICAL['main']).read_text())['stock_rule_hashes'],'libs.tech/klayout/tech')}
    report={}
    for name,(expected,relative) in cases.items():
        actual=p.rule_tree(root,relative)
        report[name]=dict(expected_count=len(expected),actual_count=len(actual),
                          expected_only=sorted(set(expected)-set(actual))[:10],
                          actual_only=sorted(set(actual)-set(expected))[:10],
                          changed=[dict(path=k,expected=expected[k],actual=actual[k])
                                   for k in sorted(set(expected)&set(actual)) if expected[k]!=actual[k]][:10])
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))
if __name__=='__main__':main()
