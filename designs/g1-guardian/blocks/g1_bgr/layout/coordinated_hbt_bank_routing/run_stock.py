#!/usr/bin/env python3
"""One selected stock check on the frozen 301-HBT bank; no full-BGR claim."""
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
BASE=ROOT/'build/scratch/bgr-hbt-fullbank-20260922-r2'
PDK=Path('/foss/pdks/ihp-sg13g2')
FROZEN={
  "bank.gds": "7a8c57b6a05b0cadd4443bb04a3b629b9da23b3919cf16d723122c12fae34e2c",
  "bank.cdl": "57c27168d72461f1a0def4f0a1d38bac1829462e0a1f76e3829840f0102196e6",
  "placement.json": "2e16c0208e94913b7dbcb061bcae6cfd4edb619e498a45fa6e3e8b71ab6b3621",
  "route_ledger.json": "99a734d096ab00af99d697279066d7383a65a24dfe5df4b4c1f52ba5170ecb02",
  "terminal_graph.json": "b4d875ed503bafff41911f7bb173e1286918752349b23db95e8ddc35d70950a2",
  "all_star_interfaces_cut.json": "87a2dd5d503f3a2679f1d75cee4c4b6296514f1b8979559f05410b5c4ec3a41f",
  "individual_star_cuts.json": "c2c939715aea0a19995829acaef6beedda5a20e4d911a2ecfa56619338d27f3c",
  "local_spacing_ownership.json": "f94856f4d914d937e5b803fc547d89b01d741d70ffe51ebec98319beab20947a",
  "neighbor_obstructions.json": "c33dcfdb2f2c71860880ed1ba285deb443b07efba08c922b16ef8357a96510cc",
  "revision_audit.json": "6bed84066b8ab07e6c0b9ca1215dd76f8910946189bb7840737c6395ed213112",
  "preparation.json": "efd1448404d08281b0cb4c781074f9578d6e088c83a859eb33d5d4e161d4d218",
  "dummy_seed_proof.json": "5b4a87e46a02734860e7f90641e2a8c72efe595d0cd7dd56ccd5b285fbf4c8cf",
  "assignment_review.json": "75de1c4eb3cbc64295ecf68b6bff83e9b80aad7b219be208c987a2bb0104bd4e",
  "derived_builder.py": "c2fbaef7e76f7404b0b9d1d9dc8755ff676f5aeb171f0edf9d5a2c0ce67fc3a0",
  "run.json": "51e98d9a8bb0419de349d9b05b4635c513c8255f355c415b5691d1ccf20f2dea"
}
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
    assert gate['status']=='passed' and 0<=age<1800 and gate['expected_growth_gib']>=.2
    assert gate['project_cpu_budget']>=1 and gate['ram_available_bytes']>=4*2**30
    prep=json.loads((BASE/'preparation.json').read_text());assert prep['status']=='passed preparation'
    assert all(prep['checks'].values()) and prep['source_device_count']==301 and prep['source_net_count']==8
    completed=json.loads((BASE/'run.json').read_text());assert completed['status']=='passed'
    assert all(sha(ROOT/n)==h for n,h in completed['frozen_bindings'].items())
    cards=[line.split() for line in (BASE/'bank.cdl').read_text().splitlines() if line.startswith('Q')]
    assert len(cards)==301 and all(c[5:]==['npn13G2','we=0.07u','le=0.9u','Nx=1','m=1'] for c in cards)
    assert {n for c in cards for n in c[1:5]}=={'vss','b1b','c2','dvbe','vbe','vbe3','vd1','vd2'}
    layout=pya.Layout();layout.read(str(BASE/'bank.gds'))
    assert sum(1 for _ in layout.top_cell().each_inst())==301
    assert len(json.loads((BASE/'placement.json').read_text())['instances'])==301
    for name,h in FROZEN.items():assert sha(BASE/name)==h,name
    for path,h in prep['inputs'].items():assert sha(ROOT/path)==h,path
    out=ROOT/('build/scratch/bgr-hbt-fullbank-stock-20260922-r2-'+a.kind);out.mkdir(exist_ok=False)
    (out/Path(__file__).name).write_bytes(Path(__file__).read_bytes())
    (out/'STOCK_CONTRACT_20260922.md').write_bytes((HERE/'STOCK_CONTRACT_20260922.md').read_bytes())
    decks={str(p.relative_to(PDK)):sha(p) for kind in ['drc','lvs'] for p in (PDK/('libs.tech/klayout/tech/'+kind)).rglob('*') if p.is_file() and p.suffix in ['.drc','.lvs','.lylvs','.rb','.json','.py']}
    cmd=['python3',str(PDK/('libs.tech/klayout/tech/'+a.kind+'/run_'+a.kind+'.py')),'--run_mode=deep','--topcell=bgr_hbt_bank','--run_dir='+str(out/'reports')]
    cmd+=['--path='+str(BASE/'bank.gds'),'--no_density','--mp=1'] if a.kind=='drc' else ['--layout='+str(BASE/'bank.gds'),'--netlist='+str(BASE/'bank.cdl')]
    result=dict(status='running',kind=a.kind,command=cmd,watchdog_s=180,resource_gate_sha256=sha(a.resource_gate),
                frozen=FROZEN,stock_deck_hashes=decks,script_sha256=sha(Path(__file__)),contract_sha256=sha(HERE/'STOCK_CONTRACT_20260922.md'),
                started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),density='not run',antenna='not run',seed='not applicable',fullmacro='not run')
    receipt=out/'summary.json';receipt.write_text(json.dumps(result,indent=2)+'\n');start=time.monotonic()
    with (out/'stock.log').open('x') as log:proc=subprocess.run(['timeout','--kill-after=5','180']+cmd,stdout=log,stderr=subprocess.STDOUT)
    result.update(returncode=proc.returncode,wall_s=time.monotonic()-start,log_sha256=sha(out/'stock.log'))
    passed=False
    try:
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
    except Exception as e:
        result['report_parse_error']=dict(type=type(e).__name__,message=str(e));passed=False
    result['frozen_unchanged']=all(sha(BASE/n)==h for n,h in FROZEN.items()) and all(sha(ROOT/n)==h for n,h in prep['inputs'].items()) and all(sha(ROOT/n)==h for n,h in completed['frozen_bindings'].items())
    result['stock_decks_unchanged']=all(sha(PDK/n)==h for n,h in decks.items())
    result['runner_contract_unchanged']=sha(Path(__file__))==result['script_sha256'] and sha(HERE/'STOCK_CONTRACT_20260922.md')==result['contract_sha256']
    siblings=[ROOT/('build/scratch/bgr-hbt-fullbank-stock-20260922-r2-'+k) for k in ['drc','lvs']]
    result['combined_output_bytes']=sum(p.stat().st_size for d in siblings if d.exists() for p in d.rglob('*') if p.is_file())
    result['status']='passed' if proc.returncode==0 and passed and result['frozen_unchanged'] and result['stock_decks_unchanged'] and result['runner_contract_unchanged'] and result['combined_output_bytes']<.2*2**30 else 'failed'
    result['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();receipt.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2));return 0 if result['status']=='passed' else 1
if __name__=='__main__':raise SystemExit(main())
