#!/usr/bin/env python3
"""Unchanged stock main DRC for the isolated power-routing overlay only."""
import argparse
import collections
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
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from place_closed_analog import sha


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--execute',action='store_true')
    a=p.parse_args()
    assert pya.__version__=='0.30.9' and len(os.sched_getaffinity(0))==1
    assert (PDK/'COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    metadata=json.loads((a.candidate/'analysis.json').read_text())
    gds=a.candidate/'power_overlay.gds'
    assert metadata['status'].startswith('passed') and sha(gds)==metadata['overlay_sha256']
    sys.path.insert(0,str(DRC))
    spec=importlib.util.spec_from_file_location('stock',DRC/'run_drc.py')
    stock=importlib.util.module_from_spec(spec);spec.loader.exec_module(stock)
    args=SimpleNamespace(density_thr=1,drc_json=None,run_mode='deep',precheck_drc=False,
                         disable_extra_rules=False,no_feol=False,no_beol=False,no_offgrid=False,
                         no_angle=False,density_sanity=False,no_density=True,no_recommended=False,
                         table=[],topcell='sense_power_interface_NOT_ADOPTED')
    switches=stock.generate_klayout_switches(args,str(gds))
    if a.execute:
        stock.run_check(DRC/'ihp-sg13g2.drc',['main'],str(gds),a.output/'reports',switches)
        return
    assert not a.output.exists();(a.output/'reports').mkdir(parents=True)
    (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    rules={str(q.relative_to(PDK)):sha(q)for q in (PDK/'libs.tech/klayout/tech').rglob('*')if q.is_file()}
    result=dict(status='running',overlay_sha256=sha(gds),script_sha256=sha(Path(__file__)),
                stock_rule_hashes=rules,switches={k:str(v)for k,v in switches.items()},
                not_run=['native neighbouring geometry DRC','maximal DRC','density/antenna','full-chip LVS/PEX/IR/EM','adoption'])
    receipt=a.output/'summary.json';receipt.write_text(json.dumps(result,indent=2)+'\n')
    command=['timeout','--kill-after=5','90','python3',str(Path(__file__).resolve())]+sys.argv[1:]+['--execute']
    started=time.monotonic()
    with (a.output/'stock.log').open('x')as log:
        run=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
    reports=[]
    for path in (a.output/'reports').glob('*_main.lyrdb'):
        counts=collections.Counter(i.findtext('category')for i in ET.parse(path).findall('.//items/item'))
        reports.append(dict(path=str(path.relative_to(a.output)),sha256=sha(path),markers=sum(counts.values()),categories=dict(counts)))
    unchanged=sha(gds)==result['overlay_sha256'] and all(sha(PDK/q)==h for q,h in rules.items())
    passed=run.returncode==0 and unchanged and len(reports)==1 and reports[0]['markers']==0
    result.update(status='passed isolated overlay main DRC'if passed else'failed isolated overlay main DRC',
                  reports=reports,returncode=run.returncode,wall_s=time.monotonic()-started,inputs_rules_unchanged=unchanged)
    receipt.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='stock_rule_hashes'},indent=2))
    raise SystemExit(0 if passed else 1)


if __name__=='__main__':main()
