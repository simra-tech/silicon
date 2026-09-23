#!/usr/bin/env python3
"""Freeze prospective fast pilot method; no analog run or population release."""
import argparse
import difflib
import json
from pathlib import Path
from run_joint586_fast_nodeset_staged import SIM,ROOT,sha,qualification,NODESET_PACKET,NODESET_PACKET_SHA,NODESET_AUDIT_SHA


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--campaign-id',required=True);a=p.parse_args()
    assert Path(a.campaign_id).name==a.campaign_id
    old=SIM/'qualification/joint586-adverse30-contract-20260923-b/contract.json'
    assert sha(old)=='2bff2817772337148c16d3c4d7d7ed432a41715cd69d8eb0bff3c4e35202438c'
    contract=json.loads(old.read_text());assert all(sha(ROOT/n)==v for n,v in contract['live_bindings_sha256'].items())
    audit=SIM/'qualification/joint586-fast-nodeset-rescue-audit-20260923-b.json'
    qualification(audit,audit,'fast')
    out=SIM/'qualification'/a.campaign_id;out.mkdir()
    pairs=[('run_joint586_adverse_staged.py','run_joint586_fast_nodeset_staged.py'),
           ('audit_joint586_adverse_calibration.py','audit_joint586_fast_nodeset_calibration.py'),
           ('audit_joint586_adverse_staged.py','audit_joint586_fast_nodeset_staged.py')]
    for index,(before,after) in enumerate(pairs):
        diff=''.join(difflib.unified_diff((SIM/before).read_text().splitlines(True),(SIM/after).read_text().splitlines(True),fromfile=before,tofile=after))
        (out/('declared_source_difference_%d.diff'%index)).write_text(diff)
    files=[old,NODESET_PACKET,audit,Path(__file__).absolute(),SIM/'test_joint586_fast_nodeset_staged.py']
    files += [SIM/n for pair in pairs for n in pair]
    files += [SIM/'prepare_joint586_fastcold_nodeset.py',SIM/'audit_joint586_fast_nodeset_rescue_r2.py']
    contract['live_bindings_sha256'].update({str(q.relative_to(ROOT)):sha(q) for q in files})
    contract['staged_execution'].update(runner_sha256=sha(SIM/'run_joint586_fast_nodeset_staged.py'),
        auditor_sha256=sha(SIM/'audit_joint586_fast_nodeset_staged.py'),
        prior_original_staged_contract_sha256=sha(old),
        qualification='63 fast generated inputs (60heldouts plus3calibration code pairs) restore original bytes after removing the identical fixed8nodeset line. Original probe numerical/analysis AST unchanged; same60 ordering and JSON value/order roundtrip tested. These software checks do not establish an analog calibration result.',
        source_differences_sha256={q.name:sha(q) for q in out.glob('*.diff')})
    contract.update(status='prepared fast fixed-nodeset firstsample only; NOTRUN pending review/resource/lease',
        fixed_nodeset_contract_sha256=NODESET_PACKET_SHA,fixed_nodeset_qualification_sha256=NODESET_AUDIT_SHA,
        fixed_nodeset_guesses=json.loads(NODESET_PACKET.read_text())['fixed_guesses'],
        initial_allowed_seed=78101,subsequent29_status='not run; separate firstsample audit and disposition required',
        method_scope='Only fast model-level population. Original independent binary calibration/tenconditions/40guards20residuals/full11512+27 and1200s held. Same fixed8 canonical78001 external-node guesses for every seed/code/condition. New14 exact consistency gate, original cross-method exactwave failures retained separately. JSON condition tuple/list representation normalized prospectively. No IC/UIC/tolerance/card/sourcegeometry/acceptance change.',
        previous_method_failures='Original fast lowcoldSPARSEtimeout/KLUinitialOPfailure and originalreturn-a preflight/a-audit failure remain archived; no original sample overwrite or success-denominator rewrite.')
    (out/'contract.json').write_text(json.dumps(contract,indent=2)+'\n');print(out.name,sha(out/'contract.json'))


if __name__=='__main__':main()
