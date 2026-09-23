#!/usr/bin/env python3
"""Fail-closed abort inventory adapter; unchanged prepared transient semantics."""
import re
import run_joint586_fastcold_nodeset_transients as original

original_error_lines = original.error_lines


def error_lines(log):
    errors = original_error_lines(log)
    errors.extend(line for line in log.splitlines()
        if re.search(r'analysis aborted', line, re.I) and line not in errors)
    return errors


if __name__ == '__main__':
    # The original implementation is immutable and hash-bound alongside this
    # adapter. Its source remains runner.py; the executed wrapper is additionally
    # saved and bound so provenance does not misidentify the effective code.
    import argparse
    import json
    from pathlib import Path
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument('--contract', type=Path, required=True)
    p.add_argument('--contract-sha256', required=True)
    p.add_argument('--solver', required=True)
    a, _ = p.parse_known_args()
    assert original.sha(a.contract) == a.contract_sha256
    packet = json.loads(a.contract.read_text())
    assert packet['adapter_sha256'] == original.sha(Path(__file__))
    assert all(original.sha(original.ROOT/n) == v for n,v in packet['bindings_sha256'].items())
    case, = [c for c in packet['cases'] if c['solver'] == a.solver]
    out = original.SIM/'qualification'/case['run']
    assert not (out/'run.log').exists() and not (out/'error_inventory_adapter.py').exists()
    (out/'error_inventory_adapter.py').write_text(Path(__file__).read_text())
    original.error_lines = error_lines
    original.main()
