#!/usr/bin/env python3
"""Recover only unfinished maximal DRC via unchanged stock run_check API."""
import argparse
import collections
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace
import xml.etree.ElementTree as ET
import pya

PDK=Path('/foss/pdks/ihp-sg13g2')
DRC=PDK/'libs.tech/klayout/tech/drc'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def switches(module,gds,topcell='placed_core_NOT_CONNECTED_FULLCHIP'):
    args=SimpleNamespace(density_thr=1,drc_json=None,run_mode='deep',precheck_drc=False,
                         disable_extra_rules=False,no_feol=False,no_beol=False,no_offgrid=False,
                         no_angle=False,density_sanity=False,no_density=True,no_recommended=False,
                         table=[],topcell=topcell)
    return module.generate_klayout_switches(args,str(gds))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parent-drc',type=Path,required=True)
    parser.add_argument('--placement',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--execute',action='store_true')
    args=parser.parse_args()
    assert len(os.sched_getaffinity(0))==1 and pya.__version__=='0.30.9'
    assert (PDK/'COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    gds=args.placement/'placed_core.gds'
    parent=json.loads((args.parent_drc/'summary.json').read_text())
    assert parent['returncode']==124 and parent['source_rules_unchanged'] and sha(gds)==parent['GDS_sha256']
    assert len(parent['reports'])==1 and parent['reports'][0]['markers']==0
    main_report=args.parent_drc/parent['reports'][0]['path']
    assert main_report.name.endswith('_main.lyrdb') and sha(main_report)==parent['reports'][0]['sha256']
    assert "tables 'main' completed in 101.57 seconds" in (args.parent_drc/'stock.log').read_text()
    assert all(sha(PDK/p)==h for p,h in parent['stock_rule_hashes'].items())
    sys.path.insert(0,str(DRC))
    spec=importlib.util.spec_from_file_location('pinned_stock_drc',DRC/'run_drc.py')
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sw=switches(module,gds)
    if args.execute:
        module.run_check(DRC/'rule_decks/sg13g2_maximal.drc',['sg13g2_maximal'],str(gds),args.output/'reports',sw)
        return
    assert not args.output.exists()
    (args.output/'reports').mkdir(parents=True)
    receipt=dict(status='running',parent_summary_sha256=sha(args.parent_drc/'summary.json'),
                 GDS_sha256=sha(gds),stock_rule_hashes=parent['stock_rule_hashes'],script_sha256=sha(Path(__file__)),
                 reused_main=dict(status='passed',report_sha256=sha(main_report),markers=0,wall_s=101.57),
                 switches={k:str(v) for k,v in sw.items()},watchdog_s=900,
                 thread_policy='Explicit1 instead of implicit128 on sameoneCPUaffinity; no rule/options/input geometry changes.',
                 not_run=['density','antenna','connected fullchip LVS','PEX/IR/EM/electrical adoption'])
    (args.output/'summary.json').write_text(json.dumps(receipt,indent=2)+'\n')
    command=['timeout','--kill-after=5','900','python3',str(Path(__file__).resolve())]+sys.argv[1:]+['--execute']
    start=time.monotonic()
    with (args.output/'stock.log').open('x') as log:
        result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
    reports=[]
    for path in (args.output/'reports').glob('*.lyrdb'):
        categories=collections.Counter(item.findtext('category') for item in ET.parse(path).findall('.//items/item'))
        reports.append(dict(path=str(path.relative_to(args.output)),sha256=sha(path),markers=sum(categories.values()),categories=dict(categories)))
    unchanged=sha(gds)==parent['GDS_sha256'] and all(sha(PDK/p)==h for p,h in parent['stock_rule_hashes'].items())
    passed=result.returncode==0 and unchanged and len(reports)==1 and reports[0]['markers']==0
    receipt.update(status='passed scoped main plus maximal DRC' if passed else 'failed maximal DRC recovery',
                   returncode=result.returncode,wall_s=time.monotonic()-start,reports=reports,inputs_rules_unchanged=unchanged)
    (args.output/'summary.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({k:v for k,v in receipt.items() if k!='stock_rule_hashes'},indent=2))
    raise SystemExit(0 if passed else 1)


if __name__=='__main__':
    main()
