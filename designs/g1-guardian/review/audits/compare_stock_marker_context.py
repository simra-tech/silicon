#!/usr/bin/env python3
"""Compare unchanged stock-main marker multisets without waiving any marker."""
import argparse
import json
from pathlib import Path
from sense_power_interface.compare_native_markers import load,rows,sha


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('baseline','candidate','output'):p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--baseline-gds-sha',required=True);p.add_argument('--candidate-gds-sha',required=True)
    a=p.parse_args();assert not a.output.exists()
    before,old=load(a.baseline);after,new=load(a.candidate)
    assert before['GDS_sha256']==a.baseline_gds_sha and after['GDS_sha256']==a.candidate_gds_sha
    assert before['stock_rule_hashes']==after['stock_rule_hashes']
    added=new-old;removed=old-new
    result=dict(status='passed exact marker preservation'if not added and not removed else'failed exact marker preservation',
        baseline_summary_sha256=sha(a.baseline/'summary.json'),candidate_summary_sha256=sha(a.candidate/'summary.json'),
        baseline_GDS_sha256=a.baseline_gds_sha,candidate_GDS_sha256=a.candidate_gds_sha,
        script_sha256=sha(Path(__file__)),helper_sha256=sha(Path(__file__).parent/'sense_power_interface/compare_native_markers.py'),
        baseline_markers=sum(old.values()),candidate_markers=sum(new.values()),added=rows(added),removed=rows(removed),
        absolute_stock_acceptance='failed'if new else'passed',
        scope='Exact category/cell/value multiset equality; no inherited-rule waiver',
        not_run=['other decks','device-aware fullchip LVS','full PDN/currentIR/EM','electrical adoption'])
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2));raise SystemExit(0 if not added and not removed else 1)


if __name__=='__main__':main()
