#!/usr/bin/env python3
"""Retain failed preflight a; fresh same-input return b and explicit mixed receipts."""
import copy
import difflib
import json
from pathlib import Path
from prepare_joint586_fast_nodeset_rescue import SIM,ROOT,PACKET,sha,transform
from result_directory import allocate_run


def main():
    target=SIM/'qualification/joint586-fast-nodeset-rescue-contract-20260923-b.json'
    assert not target.exists() and sha(PACKET)=='2787b5179069e559ee4b056ca378c1e8a3e79f82cee74a599d5a0085925890f4'
    packet=json.loads(PACKET.read_text());case,=[c for c in packet['cases'] if c['kind']=='own' and c['label']=='return']
    old_case=copy.deepcopy(case);failed=SIM/'qualification'/case['run']
    assert not any((failed/n).exists() for n in ['run.log','run.json','provenance.json','summary.json'])
    old=SIM/'qualification'/case['original_run']
    case['run']=case['run'][:-1]+'b'
    out=allocate_run(SIM,case['run'])
    for n in ['sense.spice','trip.spice','bgr.spice','population_inventory.json']:
        (out/n).write_bytes((failed/n).read_bytes())
    body=(old/'population_transient.cir').read_text()
    deck,audit=transform(body,case['original_run'],case['run'],packet['fixed_guesses'])
    (out/'population_transient.cir').write_text(deck)
    case.update(deck_sha256=sha(out/'population_transient.cir'),transform=audit,
        validation_adapter_sha256=sha(SIM/'run_joint586_fast_nodeset_return_r2.py'))
    (out/'preparation.json').write_text(json.dumps(case,indent=2)+'\n')
    (out/'transform_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    (out/'declared_initialization_difference.diff').write_text(''.join(difflib.unified_diff(body.splitlines(True),deck.splitlines(True),fromfile=case['original_run'],tofile=case['run'])))
    for p in [PACKET,Path(__file__).resolve(),SIM/'run_joint586_fast_nodeset_return_r2.py',
            SIM/'test_joint586_fast_nodeset_return_r2.py',SIM/'audit_joint586_fast_nodeset_rescue_r2.py']:
        packet['bindings_sha256'][str(p.relative_to(ROOT))]=sha(p)
    packet['inherited_execution_contract_sha256']={c['run']:sha(PACKET) for c in packet['cases'] if c is not case and not c['reuse_receipts_sha256']}
    packet['preserved_preflight_failure']=dict(run=old_case['run'],status='failed hierarchy preflight; ngspice not run',
        original_packet_sha256=sha(PACKET),cause='Single-output hierarchy validator rejected four wrdata commands before run/provenance creation.',
        original_deck_sha256=old_case['deck_sha256'],repair='Validation-only view tests each of four output commands; actual deck remains original bound4phase transient except fresh output paths.')
    packet['status']='prepared return preflight correction; original a cohort and failure retained'
    target.write_text(json.dumps(packet,indent=2)+'\n');print(target.relative_to(ROOT),sha(target))


if __name__=='__main__':main()
