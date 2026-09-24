#!/usr/bin/env python3
"""Single CPU bounded unchanged-deck main/max DRC or strict BGR LVS."""
import argparse
import collections
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
import pya

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'coordinated_full_closure'))
from run_stock import sha,dump,strict
PDK=Path('/foss/pdks/ihp-sg13g2')


def main():
    ap=argparse.ArgumentParser()
    for k in ('candidate','output','resource-gate'):ap.add_argument('--'+k,type=Path,required=True)
    ap.add_argument('--kind',choices=('drc','lvs'),required=True)
    a=ap.parse_args();assert set(os.sched_getaffinity(0))=={0}
    assert pya.__version__=='0.30.9' and (PDK/'COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    gate=json.loads(a.resource_gate.read_text())
    age=(datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(gate['utc'])).total_seconds()
    assert gate['status']=='passed' and 0<=age<1800 and gate['project_cpu_budget']>=43
    assert gate['external_allocation']['expected_growth_gib']>=1 and gate['ram_available_bytes']>=4*2**30
    prep=json.loads((a.candidate/'preparation.json').read_text());assert prep['status']=='passed preparation'
    assert sha(a.candidate/'bank.gds')==prep['gds_sha256']
    assert sha(a.candidate/'bank.cdl')==prep['cdl_sha256']=='7f8e6e8c606b1e04321c5c9b20e94610d34d42055c8818d03d79352b3a4710b2'
    assert all(sha(Path(p))==h for p,h in prep['inputs'].items())
    bindings={str(p):sha(p) for p in list(a.candidate.iterdir())+[Path(__file__),HERE.parent/'coordinated_full_closure/run_stock.py'] if p.is_file()}
    rules={str(p):sha(p) for p in (PDK/'libs.tech/klayout/tech').rglob('*') if p.is_file() and p.suffix in ('.drc','.lvs','.py','.rb','.json')}
    a.output.mkdir(exist_ok=False);(a.output/'worker_snapshot.py').write_bytes(Path(__file__).read_bytes())
    cmd=['python3',str(PDK/('libs.tech/klayout/tech/'+a.kind+'/run_'+a.kind+'.py')),'--run_mode=deep','--topcell=g1_bgr','--run_dir='+str(a.output/'reports')]
    cmd+=['--path='+str(a.candidate/'bank.gds'),'--no_density','--mp=1'] if a.kind=='drc' else ['--layout='+str(a.candidate/'bank.gds'),'--netlist='+str(a.candidate/'bank.cdl'),'--top_lvl_pins','--spice_comments']
    result=dict(status='running',command=cmd,inputs=bindings,stock_rules=rules,
        resource_gate_sha256=sha(a.resource_gate),cpu=0,watchdog_s=180,kill_grace_s=5,
        memory_reservation_gib=4,memory_enforced=False,seed='not applicable',
        density_antenna_electrical_adoption='not run')
    dump(a.output/'summary.json',result);start=time.monotonic()
    with (a.output/'stock.log').open('x') as log:
        run=subprocess.run(['timeout','-k','5','180']+cmd,stdout=log,stderr=subprocess.STDOUT)
    ok=False
    try:
        logs='\n'.join(p.read_text(errors='replace') for p in (a.output/'reports').rglob('*.log'))
        if a.kind=='drc':
            reports=[]
            for p in (a.output/'reports').rglob('*.lyrdb'):
                cats=collections.Counter(i.findtext('category') for i in ET.parse(p).findall('.//items/item'))
                reports.append(dict(file=p.name,sha256=sha(p),markers=sum(cats.values()),categories=dict(cats)))
            result['reports']=reports
            result['main_completed']="DRC run for tables 'main' completed" in logs
            result['maximal_completed']='DRC run for maximum ruleSet completed' in logs
            ok=bool(reports) and all(r['markers']==0 for r in reports) and result['main_completed'] and result['maximal_completed']
        else:
            dbs=list((a.output/'reports').rglob('*.lvsdb'))
            result['strict_lvs']=[strict(p) for p in dbs]
            result['explicit_match']='Congratulations! Netlists match.' in logs and "Netlists don't match" not in logs
            ok=len(dbs)==1 and all(r['status']=='passed' for r in result['strict_lvs']) and result['explicit_match']
    except Exception as e:result['parse_error']=repr(e)
    held=all(sha(Path(p))==h for p,h in {**bindings,**rules,**prep['inputs']}.items())
    growth=sum(p.stat().st_size for p in a.output.rglob('*') if p.is_file())
    result.update(status='passed' if ok and run.returncode==0 and held and growth<2**30 else 'failed',
        returncode=run.returncode,wall_s=time.monotonic()-start,inputs_rules_held=held,output_bytes=growth)
    dump(a.output/'summary.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('inputs','stock_rules')},indent=2))
    return 0 if result['status']=='passed' else 1


if __name__=='__main__':raise SystemExit(main())
