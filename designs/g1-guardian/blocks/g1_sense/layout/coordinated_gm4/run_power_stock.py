#!/usr/bin/env python3
"""Power supplement to the unchanged bounded full-SENSE stock runner."""
import json,sys
from pathlib import Path
from build_native_prototypes import sha
import run_full_sense_stock

HERE=Path(__file__).resolve().parent

def main():
    output=Path(sys.argv[sys.argv.index('--output')+1]);candidate=Path(sys.argv[sys.argv.index('--candidate')+1])
    manifest=json.loads((candidate/'manifest.json').read_text())
    assert manifest['status']=='passed isolated power routing geometry gate'
    assert manifest['terminal_audit']['status']=='passed'and manifest['terminal_audit']['source_net_count']==134
    supplement=output.with_name(output.name+'-power-contract');assert not supplement.exists();supplement.mkdir(parents=True)
    for name in('POWER_STOCK_CONTRACT_20260922.md','run_power_stock.py'):
        (supplement/name).write_bytes((HERE/name).read_bytes())
    (supplement/'bindings.json').write_text(json.dumps(dict(candidate_GDS_sha256=manifest['GDS_sha256'],
        candidate_manifest_sha256=sha(candidate/'manifest.json'),supplement_sha256=sha(HERE/'POWER_STOCK_CONTRACT_20260922.md'),
        base_runner_sha256=sha(HERE/'run_full_sense_stock.py')),indent=2)+'\n')
    run_full_sense_stock.main()

if __name__=='__main__':main()
