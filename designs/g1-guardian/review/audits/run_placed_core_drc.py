#!/usr/bin/env python3
"""Unmodified stock local-geometry DRC of placed core; density/signoff separate."""
import argparse
import collections
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import xml.etree.ElementTree as ET
import pya

PDK=Path('/foss/pdks/ihp-sg13g2')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--placement',type=Path,required=True)
    parser.add_argument('--resource-gate',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    assert not args.output.exists() and len(os.sched_getaffinity(0))==1 and pya.__version__=='0.30.9'
    assert (PDK/'COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    gate=json.loads(args.resource_gate.read_text())
    age=(datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(gate['utc'])).total_seconds()
    assert gate['status']=='passed' and 0<=age<1800 and gate['external_allocation']['expected_growth_gib']>=2
    summary=json.loads((args.placement/'analysis.json').read_text())
    gds=args.placement/'placed_core.gds'
    assert summary['status']=='passed source-preserving core placement' and sha(gds)==summary['GDS_sha256']
    assert json.loads((args.placement/'decap_domains.json').read_text())['status']=='passed scoped decap domain no-merge'
    rules={str(p.relative_to(PDK)):sha(p) for p in (PDK/'libs.tech/klayout/tech').rglob('*') if p.is_file()}
    args.output.mkdir(parents=True)
    command=['python3',str(PDK/'libs.tech/klayout/tech/drc/run_drc.py'),
             '--run_mode=deep','--topcell=placed_core_NOT_CONNECTED_FULLCHIP',
             '--run_dir='+str(args.output/'reports'),'--path='+str(gds),'--no_density','--mp=1']
    receipt=dict(status='running',command=command,stock_rule_hashes=rules,
                 GDS_sha256=sha(gds),placement_manifest_sha256=sha(args.placement/'analysis.json'),
                 resource_gate_sha256=sha(args.resource_gate),script_sha256=sha(Path(__file__)),
                 watchdog_s=300,kill_grace_s=5,seed='not applicable',
                 scope='Local geometry DRC only. Placed core has no connected fullchip ring/pads/feeds; density disabled explicitly, not a signoff claim.',
                 not_run=['density','antenna','fullchip connectivity/LVS','PEX','IR/EM','electrical adoption'])
    (args.output/'summary.json').write_text(json.dumps(receipt,indent=2)+'\n')
    start=time.monotonic()
    with (args.output/'stock.log').open('x') as log:
        result=subprocess.run(['timeout','--kill-after=5','300']+command,stdout=log,stderr=subprocess.STDOUT)
    reports=[]
    for path in (args.output/'reports').rglob('*.lyrdb'):
        categories=collections.Counter(item.findtext('category') for item in ET.parse(path).findall('.//items/item'))
        reports.append(dict(path=str(path.relative_to(args.output)),sha256=sha(path),markers=sum(categories.values()),categories=dict(categories)))
    unchanged=sha(gds)==receipt['GDS_sha256'] and all(sha(PDK/p)==h for p,h in rules.items())
    passed=result.returncode==0 and unchanged and reports and all(r['markers']==0 for r in reports)
    receipt.update(status='passed scoped geometry DRC' if passed else 'failed scoped geometry DRC',
                   returncode=result.returncode,wall_s=time.monotonic()-start,reports=reports,
                   source_rules_unchanged=unchanged,output_bytes=sum(p.stat().st_size for p in args.output.rglob('*') if p.is_file()))
    (args.output/'summary.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({k:v for k,v in receipt.items() if k!='stock_rule_hashes'},indent=2))
    raise SystemExit(0 if passed else 1)


if __name__=='__main__':
    main()
