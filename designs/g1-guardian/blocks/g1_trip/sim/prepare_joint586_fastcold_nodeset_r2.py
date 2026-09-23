#!/usr/bin/env python3
"""Refreeze output-gate repair; preserve every original prepared-a byte."""
import difflib,json
from pathlib import Path
from prepare_joint586_fastcold_nodeset import SIM,ROOT,ORIGINAL,PACKET,sha,transform
from result_directory import allocate_run

def main():
    old=json.loads(PACKET.read_text());output=PACKET.with_name(PACKET.name.replace('-a.json','-b.json'));assert not output.exists()
    cases=[]
    original=(ORIGINAL/'population_transient.cir').read_text()
    for case in old['cases']:
        oldrun=SIM/'qualification'/case['run'];assert not (oldrun/'run.log').exists()
        run=case['run'][:-1]+'b';out=allocate_run(SIM,run)
        for n,v in old['source_hashes'].items():assert sha(oldrun/n)==v;(out/n).write_bytes((oldrun/n).read_bytes())
        deck,audit=transform(original,run,case['label'],old['guesses_original_printed_strings'])
        (out/'op.cir').write_text(deck);(out/'transform_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
        (out/'declared_op_difference.diff').write_text(''.join(difflib.unified_diff(original.splitlines(True),deck.splitlines(True),fromfile='originalFailedFastLowcold',tofile=case['label'])))
        cases.append(dict(case,run=run,deck_sha256=sha(out/'op.cir'),transform_sha256=sha(out/'transform_audit.json')))
    old.update(cases=cases,previous_prepared_contract_sha256=sha(PACKET),output_gate_revision='r2: exact eight header names/order, finite OP and explicit numerical errors, mandatory valid baseline; PASS only after all gates. Old r1 source/contract/prepared inputs remain unlaunched and unchanged.')
    for n in ['run_joint586_fastcold_nodeset_r2.py','prepare_joint586_fastcold_nodeset_r2.py','test_joint586_fastcold_nodeset_r2.py']:
        old['bindings_sha256'][str((SIM/n).relative_to(ROOT))]=sha(SIM/n)
    old['runner']='run_joint586_fastcold_nodeset_r2.py'
    output.write_text(json.dumps(old,indent=2)+'\n');print(output.relative_to(ROOT),sha(output))

if __name__=='__main__':main()
