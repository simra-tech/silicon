"""Freeze reviewed OP diagnostic implementation, not launch authority."""
import json
from pathlib import Path
from prepare_586_external_nodeset_controls import HERE,ROOT,sha


def main():
    old=HERE/'t2f586-klu-fast-firstsample-implementation-20260923-a.json'
    prior=json.loads(old.read_text());bindings=dict(prior['bindings_sha256'])
    assert all(sha(ROOT/name)==value for name,value in bindings.items())
    contract=HERE/'t2f586-external-nodeset-op-contract-20260923-a/contract.json'
    packet=json.loads(contract.read_text());assert all(sha(ROOT/name)==value for name,value in packet['bindings_sha256'].items())
    paths=[old,contract,Path(__file__).resolve()]
    paths += [HERE/name for name in ['prepare_586_external_nodeset_controls.py','run_586_external_nodeset_control.py',
        'audit_586_external_nodeset_controls.py','test_586_external_nodeset_controls.py','test_586_external_nodeset_runtime.py']]
    bindings.update({str(path.relative_to(ROOT)):sha(path) for path in paths})
    out=HERE/'t2f586-external-nodeset-implementation-20260923-a.json';assert not out.exists()
    out.write_text(json.dumps(dict(status='source/test frozen; no simulation or solver adoption',contract=str(contract.relative_to(ROOT)),
        contract_sha256=sha(contract),bindings_sha256=bindings,controls=3,maximum_concurrent=1,watchdog_per_arm_s=300),indent=2)+'\n')
    print(sha(out))


if __name__=='__main__':main()
