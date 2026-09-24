"""Freeze approved finite-anchor DC qualification; never authorizes all-code scaling."""
import json
from pathlib import Path
from prepare_dac586_dc_controls import ROOT,SIM,sha


def main():
    proposal=SIM/'qualification/dac586-dc-proposal-20260923-a.json'
    assert sha(proposal)=='6363bda288613247e70a55553ab8f0139688b56c001d1a9458d5bc14ce99d5ed'
    data=json.loads(proposal.read_text());bindings=dict(data['bindings_sha256'])
    names=['prepare_dac586_dc_controls.py','run_dac586_dc_control.py','audit_dac586_dc_controls.py',
           'dac586_dc_metrics.py','test_dac586_dc_controls.py','test_dac586_dc_metrics.py',
           'test_dac586_dc_runtime.py','freeze_dac586_dc_execution.py']
    bindings.update({str((SIM/name).relative_to(ROOT)):sha(SIM/name) for name in names})
    assert all(sha(ROOT/name)==value for name,value in bindings.items())
    for row in data['controls']:
        out=SIM/'qualification'/row['run']
        assert sha(out/'preparation.json')==row['preparation_sha256']
        assert not (out/'run.json').exists()
    output=SIM/'qualification/dac586-dc-execution-20260923-a.json';assert not output.exists()
    result=dict(status='approved bounded14 controls; not run',proposal=str(proposal.relative_to(ROOT)),
        proposal_sha256=sha(proposal),source_bindings_sha256=bindings,numerical_comparison_approved=True,
        required_static_method_audit=str((SIM/'qualification/dac586-dc-static-method-audit-20260923-a.json').relative_to(ROOT)),
        scope='100nV/1nA prospective finite-anchor method consistency only; strict exact failures separate. No uniform solver-error proof or256/population release.',
        authority='ROOT bounded11staticB+3two-point DC approval20260923; original11512+27/repeat/return requirements unchanged.')
    output.write_text(json.dumps(result,indent=2)+'\n');print(sha(output))


if __name__=='__main__':main()
