#!/usr/bin/env python3
"""Bounded immutable-deck checks; strict Match only, never MatchWithWarning."""
import argparse,collections,hashlib,json,os,subprocess,time
from pathlib import Path
import xml.etree.ElementTree as ET
import pya

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def output_bytes(path):return sum(p.stat().st_size for p in path.rglob('*') if p.is_file())
def strict_xref(path):
    db=pya.LayoutVsSchematic();db.read(str(path));xref=db.xref();X=pya.NetlistCrossReference
    names={X.Match:'Match',X.MatchWithWarning:'MatchWithWarning',X.Mismatch:'Mismatch',X.NoMatch:'NoMatch',X.Skipped:'Skipped',X.None_:'None'}
    rows=[]
    for cp in xref.each_circuit_pair():
        row=dict(first=None if cp.first() is None else cp.first().name,second=None if cp.second() is None else cp.second().name,status=names.get(cp.status(),str(cp.status())),children={})
        for kind,iterator in [('device',xref.each_device_pair),('net',xref.each_net_pair),('pin',xref.each_pin_pair),('subcircuit',xref.each_subcircuit_pair)]:
            counts=collections.Counter(names.get(pair.status(),str(pair.status())) for pair in iterator(cp));row['children'][kind]=dict(counts)
        rows.append(row)
    passed=bool(rows) and all(r['status']=='Match' and all(set(counts)<= {'Match'} for counts in r['children'].values()) for r in rows)
    return dict(status='passed' if passed else 'failed',circuits=rows)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--prototype',type=Path,required=True);p.add_argument('--cdl',type=Path,required=True);p.add_argument('--saved-audit',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists() and pya.__version__=='0.30.9' and os.sched_getaffinity(0)=={7}
    base=a.prototype.resolve();cdl=a.cdl.resolve();m=json.loads((base/'manifest.json').read_text());refs=json.loads((cdl/'manifest.json').read_text());audit=json.loads(a.saved_audit.read_text())
    gds=base/'native_prototypes.gds';assert sha(gds)==m['GDS_sha256']==refs['GDS_sha256']==audit['GDS_sha256']=='dfef42cc9384e44c7ad1d8851d0fd4cfa057ee61b700911859252d3557114db4'
    assert audit['status']=='passed saved-GDS native/terminal audit' and m['status']=='passed scoped native/terminal gate'
    assert refs['prototype_manifest_sha256']==sha(base/'manifest.json') and refs['source_sha256']==m['source_sha256']
    live_source=Path(__file__).resolve().parents[2]/'reports/resume-server-20260922/gm4comp3-qualified-source.spice'
    assert sha(live_source)==m['source_sha256']
    cdl_hashes={r['cell']+'.cdl':r['cdl_sha256'] for r in refs['references']}
    assert all(sha(cdl/path)==digest for path,digest in cdl_hashes.items())
    reference_manifest_hash=sha(cdl/'manifest.json')
    pdk=Path('/foss/pdks/ihp-sg13g2');assert (pdk/'COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    deck_files=sorted(p for kind in ('drc','lvs') for p in (pdk/('libs.tech/klayout/tech/'+kind)).rglob('*') if p.is_file() and p.suffix in ('.drc','.lvs','.lylvs','.rb','.json','.py'))
    hashes={str(p.relative_to(pdk)):sha(p) for p in deck_files};a.output.mkdir(parents=True);out=a.output.resolve()
    result=dict(status='running',GDS_sha256=sha(gds),source_sha256=m['source_sha256'],script_sha256=sha(Path(__file__)),
                contract_sha256=sha(Path(__file__).with_name('STOCK_PROTOTYPE_CONTRACT_20260922.md')),stock_hashes=hashes,checks=[],
                density='not run',antenna='not run',full_macro_PEX='not run',shared_junction_model_applicability='not run')
    jobs=[('drc','g1_sense_contact_prototypes',None)]+[('lvs',r['cell'],r) for r in refs['references']]
    stopped=False
    for kind,name,reference in jobs:
        if stopped:
            result['checks'].append(dict(kind=kind,cell=name,status='not run',reason='earlier stock gate failed'));continue
        runner=pdk/('libs.tech/klayout/tech/'+kind+'/run_'+kind+'.py');run_dir=out/(name+'-'+kind)
        cmd=['python3',str(runner),'--run_mode=deep','--topcell='+name,'--run_dir='+str(run_dir)]
        if kind=='drc':cmd+=['--path='+str(gds),'--no_density','--mp=1']
        else:
            path=cdl/(name+'.cdl');assert sha(path)==reference['cdl_sha256'];cmd+=['--layout='+str(gds),'--netlist='+str(path)]
        log=out/(name+'-'+kind+'.log');started=time.monotonic()
        with log.open('x') as stream:proc=subprocess.run(['timeout','--kill-after=5','180']+cmd,stdout=stream,stderr=subprocess.STDOUT)
        row=dict(kind=kind,cell=name,command=cmd,child_limit_s=180,returncode=proc.returncode,wall_s=time.monotonic()-started,log_sha256=sha(log),status='failed')
        if kind=='drc':
            reports=[]
            for path in sorted(run_dir.rglob('*.lyrdb')):
                categories=collections.Counter(item.findtext('category').strip("'") for item in ET.parse(path).findall('.//items/item'))
                reports.append(dict(path=str(path.relative_to(out)),sha256=sha(path),markers=sum(categories.values()),categories=dict(categories)))
            row['reports']=reports
            if proc.returncode==0 and reports and all(r['markers']==0 for r in reports):row['status']='passed'
        else:
            logs='\n'.join(path.read_text(errors='replace') for path in run_dir.rglob('*.log'))+'\n'+log.read_text(errors='replace')
            explicit='Congratulations! Netlists match.' in logs and "Netlists don't match" not in logs
            dbs=sorted(run_dir.rglob('*.lvsdb'));checks=[dict(path=str(path.relative_to(out)),sha256=sha(path),xref=strict_xref(path)) for path in dbs]
            row.update(explicit_comparison_pass=explicit,databases=checks)
            if proc.returncode==0 and explicit and checks and all(r['xref']['status']=='passed' for r in checks):row['status']='passed'
        row['output_bytes']=output_bytes(out)
        if row['output_bytes']>30*2**20:row.update(status='failed',growth_limit_exceeded=True)
        result['checks'].append(row);stopped=row['status']!='passed'
        (out/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(row),flush=True)
    result['stock_decks_unchanged']=all(sha(pdk/path)==digest for path,digest in hashes.items())
    result['live_source_unchanged']=sha(live_source)==m['source_sha256']
    result['source_CDL_bindings_unchanged']=sha(cdl/'manifest.json')==reference_manifest_hash and all(sha(cdl/path)==digest for path,digest in cdl_hashes.items())
    assert sha(gds)==m['GDS_sha256'] and result['stock_decks_unchanged'] and result['live_source_unchanged'] and result['source_CDL_bindings_unchanged']
    result['status']='passed' if all(r['status']=='passed' for r in result['checks']) else 'failed'
    (out/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status']}))
if __name__=='__main__':main()
