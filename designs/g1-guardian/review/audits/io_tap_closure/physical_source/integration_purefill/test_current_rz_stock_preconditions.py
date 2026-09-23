#!/usr/bin/env python3
"""Pure negative controls; never starts an EDA engine or edits a rule deck."""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import tempfile
import current_rz_stock_preconditions as p

def rejected(fn):
    try:fn()
    except AssertionError:return True
    return False
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    assert not a.output.exists()
    expected={'libs.tech/klayout/tech/lvs/sg13g2.lvs':'0'*64}
    assert p.require_rules(expected,dict(expected))
    altered={'libs.tech/klayout/tech/lvs/sg13g2.lvs':'1'*64}
    altered_rule_rejected=rejected(lambda:p.require_rules(expected,altered))
    cache=dict(expected);cache['libs.tech/klayout/tech/drc/__pycache__/run_drc.cpython-312.pyc']='2'*64
    assert p.require_rules(p.rule_files(expected),p.rule_files(cache))
    now=datetime(2026,9,23,18,0,0,tzinfo=timezone.utc)
    gate=dict(status='passed',checks={key:True for key in p.REQUIRED_CHECKS},
              utc=now.isoformat(),sample_seconds=30.1,reserve_gib=16,
              external_allocation={'reserve_gib':2},coordinated_allocation={'cpus':[0,2]})
    assert p.require_affinity(gate,{0},0,now)
    multi_cpu_rejected=rejected(lambda:p.require_affinity(gate,{0,2},0,now))
    wrong_cpu_rejected=rejected(lambda:p.require_affinity(gate,{2},0,now))
    missing_ledger_cpu_rejected=rejected(lambda:p.require_affinity(gate,{3},3,now))
    missing_check=dict(gate,checks={})
    missing_gate_check_rejected=rejected(lambda:p.require_affinity(missing_check,{0},0,now))
    with tempfile.TemporaryDirectory() as temp:
        item=Path(temp)/'bound.txt';item.write_text('original')
        digest=p.digest(item);assert p.require_bound_hashes({item:digest})
        item.write_text('mutated')
        midrun_mutation_rejected=rejected(lambda:p.require_bound_hashes({item:digest}))
    assert all((altered_rule_rejected,multi_cpu_rejected,wrong_cpu_rejected,
                missing_ledger_cpu_rejected,missing_gate_check_rejected,midrun_mutation_rejected))
    result=dict(status='passed pure stock precondition negative controls',
                altered_rule_hash_rejected=altered_rule_rejected,
                generated_bytecode_ignored_only=True,
                multiple_cpu_affinity_rejected=multi_cpu_rejected,
                wrong_cpu_affinity_rejected=wrong_cpu_rejected,
                missing_ledger_cpu_rejected=missing_ledger_cpu_rejected,
                missing_gate_check_rejected=missing_gate_check_rejected,
                midrun_bound_input_mutation_rejected=midrun_mutation_rejected,
                eda_engine='not run',rule_deck_changes='not applicable')
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
if __name__=='__main__':main()
