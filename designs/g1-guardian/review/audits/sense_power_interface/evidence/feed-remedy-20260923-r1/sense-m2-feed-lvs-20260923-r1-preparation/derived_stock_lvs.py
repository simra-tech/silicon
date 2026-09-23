#!/usr/bin/env python3
"""Strict stock LVS of the isolated dual-gate candidate, with unchanged source."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import pya
from screen_sense_dual_gate_proposal import GM4, sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('candidate', 'reference', 'drc', 'output'):
        parser.add_argument('--'+key, type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists() and len(os.sched_getaffinity(0)) == 1
    assert pya.__version__ == '0.30.9'
    sys.path.insert(0, str(GM4))
    from run_stock_native_prototypes import strict_xref
    source = GM4.parents[1]/'reports/resume-server-20260922/gm4comp3-qualified-source.spice'
    gds = args.candidate/'g1_sense_physical.gds'
    cdl = args.reference/'g1_sense_physical.cdl'
    ref = json.loads((args.reference/'manifest.json').read_text())
    drc = json.loads((args.drc/'summary.json').read_text())
    candidate = json.loads((args.candidate/'analysis.json').read_text())
    assert candidate['status'] == 'passed source-held M2 feeder geometry; stock checks not run'
    assert drc['status'] == 'passed scoped main and maximal DRC'
    assert ref['status'] == 'passed saved-polygon and exact source reference gate'
    assert sha(gds) == ref['GDS_sha256'] == drc['GDS_sha256'] == candidate['GDS_sha256']
    assert sha(source) == ref['source_sha256'] == candidate['source_sha256']
    assert sha(cdl) == ref['CDL_sha256'] == 'e3e3c22fa0e59c61f5acc79f3733833ec2a144fe3f133ed09f7922a395deec20'
    pdk = Path('/foss/pdks/ihp-sg13g2')
    assert (pdk/'COMMIT').read_text().strip() == '84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    hashes = {str(p.relative_to(pdk)): sha(p) for p in (pdk/'libs.tech/klayout/tech/lvs').rglob('*') if p.is_file()}
    args.output.mkdir(parents=True)
    (args.output/'source.py').write_bytes(Path(__file__).read_bytes())
    command = ['timeout', '--kill-after=5', '120', 'python3',
               str(pdk/'libs.tech/klayout/tech/lvs/run_lvs.py'), '--run_mode=deep',
               '--topcell=g1_sense_physical', '--run_dir='+str(args.output/'lvs'),
               '--layout='+str(gds), '--netlist='+str(cdl), '--no_series_res']
    result = dict(status='running', GDS_sha256=sha(gds), source_sha256=sha(source),
                  CDL_sha256=sha(cdl), reference_manifest_sha256=sha(args.reference/'manifest.json'),
                  DRC_summary_sha256=sha(args.drc/'summary.json'), script_sha256=sha(Path(__file__)),
                  stock_rule_hashes=hashes, command=command, child_limit_s=120,
                  not_run=['Intrinsic A/P and gate resistance applicability',
                           'Zero-R/electrical parity', 'PEX', 'Fullchip adoption'])
    (args.output/'summary.json').write_text(json.dumps(result, indent=2)+'\n')
    start = time.monotonic()
    with (args.output/'lvs.log').open('x') as log:
        run = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
    text = (args.output/'lvs.log').read_text(errors='replace')
    text += '\n'.join(p.read_text(errors='replace') for p in (args.output/'lvs').rglob('*.log'))
    databases = list((args.output/'lvs').glob('*.lvsdb'))
    explicit = 'Congratulations! Netlists match.' in text and "Netlists don't match" not in text
    checks = [dict(path=str(p.relative_to(args.output)), sha256=sha(p), xref=strict_xref(p)) for p in databases]
    top = [r for check in checks for r in check['xref']['circuits'] if r['second'].lower() == 'g1_sense_physical']
    ports = len(top) == 1 and top[0]['children']['pin'] == {'Match': 9}
    unchanged = (sha(gds) == result['GDS_sha256'] and sha(source) == result['source_sha256']
                 and sha(cdl) == result['CDL_sha256'] and all(sha(pdk/p) == h for p, h in hashes.items()))
    passed = run.returncode == 0 and explicit and len(checks) == 1 and ports and unchanged
    passed = passed and all(c['xref']['status'] == 'passed' for c in checks)
    result.update(status='passed' if passed else 'failed', returncode=run.returncode,
                  wall_s=time.monotonic()-start, explicit_comparison_pass=explicit,
                  databases=checks, nine_top_pins_match=ports, source_rules_unchanged=unchanged)
    (args.output/'summary.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'stock_rule_hashes'}, indent=2))
    raise SystemExit(0 if passed else 1)


if __name__ == '__main__': main()
