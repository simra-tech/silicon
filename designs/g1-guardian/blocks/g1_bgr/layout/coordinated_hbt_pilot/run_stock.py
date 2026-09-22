#!/usr/bin/env python3
"""One explicitly selected stock check on frozen pilot r1; no rerouting."""
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

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[5]
BASE=ROOT/'build/scratch/bgr-hbt-worstrows-20260922-r1'
PDK=Path('/foss/pdks/ihp-sg13g2')
FROZEN={'pilot.gds':'20990b281b617df935f9fc31071a2369ebdafdc953e5da22a325ddd805ebfc00',
        'pilot.cdl':'8aeac3748ccc6c00a6804bb75e63f07332a67acf64b27daf6cac71f8e3990e72',
        'subset.json':'68ced7b87dd0bf504f5a9c090ec7cd744609515a1ee0a24ba55a4f9298184211',
        'terminal_graph.json':'8efe887b385113ee2d1773280a0bbd39133b0abcbdd9d950d6da24c3b35509e9',
        'neighbor_obstructions.json':'dbde90dcb63d10dd97a7395e7085331cd589a68b078478017b5aeadc731000cd',
        'route_ledger.json':'276ff347fc54469d0bb971a9a23545bbd65396f35e5b6882473e6f5a7d8c28d8'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def strict(path):
    db=pya.LayoutVsSchematic();db.read(str(path));xref=db.xref();X=pya.NetlistCrossReference
    labels={X.Match:'Match',X.MatchWithWarning:'MatchWithWarning',X.Mismatch:'Mismatch',X.NoMatch:'NoMatch',X.Skipped:'Skipped',X.None_:'None'}
    circuits=[]
    for pair in xref.each_circuit_pair():
        row=dict(status=labels[pair.status()],children={})
        for kind,method in [('device',xref.each_device_pair),('net',xref.each_net_pair),('pin',xref.each_pin_pair),('subcircuit',xref.each_subcircuit_pair)]:
            row['children'][kind]=dict(collections.Counter(labels[p.status()] for p in method(pair)))
        circuits.append(row)
    passed=bool(circuits) and all(r['status']=='Match' and all(set(c)<={'Match'} for c in r['children'].values()) for r in circuits)
    return dict(status='passed' if passed else 'failed',circuits=circuits,sha256=sha(path))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--kind',choices=['drc','lvs'],required=True);ap.add_argument('--resource-gate',type=Path,required=True);a=ap.parse_args()
    assert os.sched_getaffinity(0)=={0} and pya.__version__=='0.30.9'
    assert (PDK/'COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    gate=json.loads(a.resource_gate.read_text());stamp=datetime.datetime.fromisoformat(gate['utc'])
    age=(datetime.datetime.now(datetime.timezone.utc)-stamp).total_seconds()
    assert gate['status']=='passed' and 0<=age<1800 and gate['expected_growth_gib']>=.1
    prep=json.loads((BASE/'preparation.json').read_text());assert prep['status']=='passed preparation'
    for name,h in FROZEN.items():assert sha(BASE/name)==h,name
    for path,h in prep['inputs'].items():assert sha(ROOT/path)==h,path
    out=ROOT/('build/scratch/bgr-hbt-worstrows-stock-20260922-r1-'+a.kind);out.mkdir(exist_ok=False)
    (out/Path(__file__).name).write_bytes(Path(__file__).read_bytes())
    (out/'STOCK_CONTRACT_20260922.md').write_bytes((HERE/'STOCK_CONTRACT_20260922.md').read_bytes())
    decks={str(p.relative_to(PDK)):sha(p) for kind in ['drc','lvs'] for p in (PDK/('libs.tech/klayout/tech/'+kind)).rglob('*') if p.is_file() and p.suffix in ['.drc','.lvs','.lylvs','.rb','.json','.py']}
    cmd=['python3',str(PDK/('libs.tech/klayout/tech/'+a.kind+'/run_'+a.kind+'.py')),'--run_mode=deep','--topcell=bgr_hbt_worstrows','--run_dir='+str(out/'reports')]
    cmd+=['--path='+str(BASE/'pilot.gds'),'--no_density','--mp=1'] if a.kind=='drc' else ['--layout='+str(BASE/'pilot.gds'),'--netlist='+str(BASE/'pilot.cdl')]
    result=dict(status='running',kind=a.kind,command=cmd,watchdog_s=180,resource_gate_sha256=sha(a.resource_gate),
                frozen=FROZEN,stock_deck_hashes=decks,script_sha256=sha(Path(__file__)),contract_sha256=sha(HERE/'STOCK_CONTRACT_20260922.md'),
                started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),density='not run',antenna='not run',seed='not applicable',fullmacro='not run')
    receipt=out/'summary.json';receipt.write_text(json.dumps(result,indent=2)+'\n');start=time.monotonic()
    with (out/'stock.log').open('x') as log:proc=subprocess.run(['timeout','--kill-after=5','180']+cmd,stdout=log,stderr=subprocess.STDOUT)
    result.update(returncode=proc.returncode,wall_s=time.monotonic()-start,log_sha256=sha(out/'stock.log'))
    passed=False
    if a.kind=='drc':
        reports=[]
        for p in sorted((out/'reports').rglob('*.lyrdb')):
            categories=collections.Counter(x.findtext('category') for x in ET.parse(p).findall('.//items/item'))
            reports.append(dict(path=str(p.relative_to(out)),sha256=sha(p),markers=sum(categories.values()),categories=dict(categories)))
        result['reports']=reports;passed=bool(reports) and all(r['markers']==0 for r in reports)
    else:
        logs='\n'.join(p.read_text(errors='replace') for p in (out/'reports').rglob('*.log'))
        result['strict_cross_references']=[strict(p) for p in sorted((out/'reports').rglob('*.lvsdb'))]
        result['explicit_match']='Congratulations! Netlists match.' in logs and "Netlists don't match" not in logs
        passed=result['explicit_match'] and bool(result['strict_cross_references']) and all(r['status']=='passed' for r in result['strict_cross_references'])
    result['frozen_unchanged']=all(sha(BASE/n)==h for n,h in FROZEN.items()) and all(sha(ROOT/n)==h for n,h in prep['inputs'].items())
    result['stock_decks_unchanged']=all(sha(PDK/n)==h for n,h in decks.items())
    siblings=[ROOT/('build/scratch/bgr-hbt-worstrows-stock-20260922-r1-'+k) for k in ['drc','lvs']]
    result['combined_output_bytes']=sum(p.stat().st_size for d in siblings if d.exists() for p in d.rglob('*') if p.is_file())
    result['status']='passed' if proc.returncode==0 and passed and result['frozen_unchanged'] and result['stock_decks_unchanged'] and result['combined_output_bytes']<.1*2**30 else 'failed'
    result['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();receipt.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2));return 0 if result['status']=='passed' else 1
if __name__=='__main__':raise SystemExit(main())
