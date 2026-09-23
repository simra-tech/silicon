#!/usr/bin/env python3
"""One isolated unchanged-stock-deck 180-second IO marker check."""
import argparse
from collections import Counter
import datetime
import hashlib
import json
import os
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
import pya
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[6]
sys.path.insert(0,str(HERE.parent))
from inspect_stock_result_r4 import analyze,device
sys.path.insert(0,str(ROOT/'designs/g1-guardian/blocks/g1_top/sim'))
from run_bounded import run_bounded
PDK=Path('/foss/pdks/ihp-sg13g2')


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for k in ('gate','candidate','output'):ap.add_argument('--'+k,type=Path,required=True)
    ap.add_argument('--cell',choices=('secondary','rc'),required=True)
    ap.add_argument('--kind',choices=('drc','lvs'),required=True)
    a=ap.parse_args()
    assert not a.output.exists() and set(os.sched_getaffinity(0))=={1}
    gate=json.loads(a.gate.read_text())
    age=(datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(gate['utc'])).total_seconds()
    assert gate['status']=='passed' and gate['project_cpu_budget']>=44 and 0<=age<1800
    assert gate['ram_available_bytes']>4*2**30
    meta=json.loads((a.candidate/'summary.json').read_text())
    assert meta['status']=='passed isolated preparation'
    cell=next(c for c in meta['cells'] if c['kind']==a.cell)
    gds,cdl=Path(cell['gds']),Path(cell['reference'])
    assert sha(gds)==cell['GDS_sha256'] and sha(cdl)==cell['CDL_sha256']
    bindings={str(p):sha(p) for p in (gds,cdl,a.candidate/'summary.json',Path(__file__),HERE.parent/'inspect_stock_result_r4.py')}
    rules={str(p):sha(p) for p in (PDK/'libs.tech/klayout/tech').rglob('*') if p.is_file() and p.suffix in ('.drc','.lvs','.py','.rb','.json')}
    a.output.mkdir(parents=True)
    (a.output/'runner_snapshot.py').write_bytes(Path(__file__).read_bytes())
    command=['python3',str(PDK/('libs.tech/klayout/tech/'+a.kind+'/run_'+a.kind+'.py')),
             '--run_mode=deep','--topcell='+cell['top'],'--run_dir='+str(a.output/'reports')]
    command+=['--path='+str(gds),'--no_density','--mp=1'] if a.kind=='drc' else ['--layout='+str(gds),'--netlist='+str(cdl),'--top_lvl_pins','--spice_comments']
    result=dict(status='running',inputs=bindings,rules=rules,resource_gate_sha256=sha(a.gate),
                CPU=1,memory_reservation_GiB=4,memory_enforced=False,watchdog_s=180,
                not_run=['fullchip adoption','electrical/ESD qualification'])
    (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    with (a.output/'console.log').open('x') as log:
        run=run_bounded(command,log,a.output/'run.json',180,cwd=ROOT,interval_s=2)
    ok=False
    try:
        if a.kind=='drc':
            logs='\n'.join(p.read_text(errors='replace') for p in (a.output/'reports').rglob('*.log'))
            reports=[]
            for path in (a.output/'reports').rglob('*.lyrdb'):
                categories=Counter(i.findtext('category') for i in ET.parse(path).findall('.//items/item'))
                reports.append(dict(file=path.name,sha256=sha(path),markers=sum(categories.values()),categories=dict(categories)))
            result.update(reports=reports,main_completed="DRC run for tables 'main' completed" in logs,
                          maximal_completed='DRC run for maximum ruleSet completed' in logs)
            ok=bool(reports) and all(r['markers']==0 for r in reports) and result['main_completed'] and result['maximal_completed']
        else:
            strict=analyze(a.output/'reports',run['returncode'],cell['top'],True,None,'deep')
            result['strict_analysis']=strict
            dbs=list((a.output/'reports').rglob('*.lvsdb'))
            assert len(dbs)==1
            db=pya.LayoutVsSchematic();db.read(str(dbs[0]))
            paired=[]
            for cp in db.xref().each_circuit_pair():
                for pair in db.xref().each_pin_pair(cp):
                    paired.append(dict(layout=pair.first().name() if pair.first() else None,
                                       reference=pair.second().name() if pair.second() else None))
            exact=bool(paired) and all(p['layout'] is not None and p['reference'] is not None and p['layout'].casefold()==p['reference'].casefold() for p in paired)
            expected=sorted(p.casefold() for p in cell['expected_pins'])
            pinsets={side:sorted(p.name().casefold() for p in next(c for c in nl.each_circuit() if c.name.casefold()==cell['top'].casefold()).each_pin())
                     for side,nl in [('layout',db.netlist()),('reference',db.reference)]}
            exact=exact and all(p==expected for p in pinsets.values())
            result.update(actual_paired_pins=paired,actual_paired_pin_identity=exact)
            result['source_pin_set_casefold_check']=dict(expected=expected,actual=pinsets)
            result['device_graphs']={side:{c.name:[device(d) for d in c.each_device()] for c in nl.each_circuit()}
                                     for side,nl in [('layout',db.netlist()),('reference',db.reference)]}
            ok=strict['status'].startswith('passed') and exact
    except BaseException as exc:result['parse_error']=repr(exc)
    held=all(sha(Path(p))==h for p,h in dict(bindings,**rules).items())
    result.update(status='passed' if ok and held and run['status']=='completed' and run['returncode']==0 else 'failed',
                  run=run,inputs_rules_held=held,output_bytes=sum(p.stat().st_size for p in a.output.rglob('*') if p.is_file()))
    (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('inputs','rules','device_graphs','strict_analysis')},indent=2))
    raise SystemExit(0 if result['status']=='passed' else 1)


if __name__=='__main__':main()
