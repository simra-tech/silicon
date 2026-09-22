#!/usr/bin/env python3
"""Remaining source-bound isolated checks, strict stock cross-reference status."""
import collections
import hashlib
import json
from pathlib import Path
import subprocess
import time
import xml.etree.ElementTree as ET
import pya


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def strict(path):
    db = pya.LayoutVsSchematic(); db.read(str(path)); x = db.xref(); X = pya.NetlistCrossReference
    statuses = {X.Match:'Match', X.MatchWithWarning:'MatchWithWarning', X.Mismatch:'Mismatch',
                X.NoMatch:'NoMatch', X.Skipped:'Skipped', X.None_:'None'}
    rows=[]
    for pair in x.each_circuit_pair():
        row=dict(status=statuses[pair.status()],children={})
        for kind, iterator in [('device',x.each_device_pair),('net',x.each_net_pair),('pin',x.each_pin_pair),('subcircuit',x.each_subcircuit_pair)]:
            row['children'][kind]=dict(collections.Counter(statuses[p.status()] for p in iterator(pair)))
        rows.append(row)
    passed=bool(rows) and all(r['status']=='Match' and all(set(c)<= {'Match'} for c in r['children'].values()) for r in rows)
    return dict(status='passed' if passed else 'failed',circuits=rows,sha256=sha(path))


def main():
    root=Path(__file__).resolve().parents[6]; pdk=Path('/foss/pdks/ihp-sg13g2')
    assert pya.__version__=='0.30.9' and (pdk/'COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    mos=root/'build/scratch/bgr-mos-contact-prototypes-20260922-r2'
    hbt=root/'build/scratch/bgr-hbt-contact-prototypes-20260922-r1'
    first=root/'build/scratch/bgr-mos-stock-20260922-r1'
    assert json.loads((first/'summary.json').read_text())['status']=='passed'
    out=root/'build/scratch/bgr-second-stock-20260922-r1';out.mkdir(parents=True,exist_ok=False)
    decks={str(p.relative_to(pdk)):sha(p) for kind in ['drc','lvs'] for p in (pdk/('libs.tech/klayout/tech/'+kind)).rglob('*')
           if p.is_file() and p.suffix in ['.drc','.lvs','.lylvs','.rb','.json','.py']}
    result=dict(status='running',script_sha256=sha(Path(__file__)),contract_sha256=sha(Path(__file__).with_name('SECOND_STOCK_CONTRACT_20260922.md')),
                stock_deck_hashes=decks,checks=[],previous_MOS_strict=[strict(p) for p in sorted(first.rglob('*.lvsdb'))],
                density='not run',antenna='not run',seed='not applicable',full_macro='not run')
    jobs=[]
    for base in [hbt,mos]:
        manifest=json.loads((base/'manifest.json').read_text())
        assert manifest['source_sha256']=='586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b'
        for item in manifest['prototypes']:
            name=item['name']
            if base==mos and name in ['bgr_mos_proto_00','bgr_mos_proto_03']:continue
            assert sha(base/(name+'.gds'))==item['gds_sha256'] and sha(base/(name+'.cdl'))==item['cdl_sha256']
            for kind in (['drc','lvs'] if base==hbt else ['lvs']): jobs.append((base,item,kind))
    assert len(jobs)==16
    for base,item,kind in jobs:
        name=item['name'];run_dir=out/(name+'-'+kind)
        cmd=['python3',str(pdk/('libs.tech/klayout/tech/'+kind+'/run_'+kind+'.py')),'--run_mode=deep','--topcell='+name,'--run_dir='+str(run_dir)]
        cmd+=['--path='+str(base/(name+'.gds')),'--no_density','--mp=1'] if kind=='drc' else ['--layout='+str(base/(name+'.gds')),'--netlist='+str(base/(name+'.cdl'))]
        log=out/(name+'-'+kind+'.log');start=time.monotonic()
        with log.open('x') as handle: proc=subprocess.run(['timeout','--kill-after=5','180']+cmd,stdout=handle,stderr=subprocess.STDOUT)
        row=dict(name=name,kind=kind,command=cmd,returncode=proc.returncode,wall_s=time.monotonic()-start,log_sha256=sha(log),status='failed')
        if kind=='drc':
            reports=[]
            for p in sorted(run_dir.rglob('*.lyrdb')):
                counts=collections.Counter(x.findtext('category') for x in ET.parse(p).findall('.//items/item'))
                reports.append(dict(path=str(p.relative_to(out)),sha256=sha(p),markers=sum(counts.values()),categories=dict(counts)))
            row['reports']=reports
            passed=bool(reports) and all(r['markers']==0 for r in reports)
        else:
            logs='\n'.join(p.read_text(errors='replace') for p in run_dir.rglob('*.log'))
            dbs=[strict(p) for p in sorted(run_dir.rglob('*.lvsdb'))]
            row['strict_cross_references']=dbs
            row['explicit_match']='Congratulations! Netlists match.' in logs and "Netlists don't match" not in logs
            passed=row['explicit_match'] and bool(dbs) and all(r['status']=='passed' for r in dbs)
        if proc.returncode==0 and passed: row['status']='passed'
        result['checks'].append(row);(out/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(row),flush=True)
    result['stock_decks_unchanged']=all(sha(pdk/p)==digest for p,digest in decks.items())
    result['status']='passed' if result['stock_decks_unchanged'] and all(r['status']=='passed' for r in result['checks']+result['previous_MOS_strict']) else 'failed'
    (out/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(result['status'])


if __name__=='__main__':main()
