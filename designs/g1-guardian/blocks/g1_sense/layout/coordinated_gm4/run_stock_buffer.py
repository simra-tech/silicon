#!/usr/bin/env python3
"""Two bounded frozen stock checks; original failures and source remain untouched."""
import argparse,collections,json,os,subprocess,time
from pathlib import Path
import xml.etree.ElementTree as ET
import pya
from run_stock_native_prototypes import sha,output_bytes,strict_xref

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--buffer',type=Path,required=True);p.add_argument('--saved-audit',type=Path,required=True);p.add_argument('--cdl',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists() and pya.__version__=='0.30.9' and os.sched_getaffinity(0)=={7}
    gds=(a.buffer/'g1_ota_source_faithful.gds').resolve();cdl=(a.cdl/'g1_ota_source_faithful.cdl').resolve();m=json.loads((a.buffer/'manifest.json').read_text());audit=json.loads(a.saved_audit.read_text());ref=json.loads((a.cdl/'manifest.json').read_text())
    source=Path(__file__).resolve().parents[2]/'reports/resume-server-20260922/gm4comp3-qualified-source.spice'
    assert sha(source)==m['source_sha256']==ref['source_sha256']=='baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877'
    assert sha(gds)==m['GDS_sha256']==audit['GDS_sha256']==ref['GDS_sha256']=='320df90ee046c73b628005da9384c80fbd21a715a39b0e8b96b10923726fc500'
    assert audit['status']=='passed saved-buffer source/native/terminal audit' and sha(a.saved_audit)==ref['saved_audit_sha256'] and sha(cdl)==ref['CDL_sha256']
    assert sha(a.buffer/'manifest.json')==ref['manifest_sha256'] and sha(a.cdl/'source_reference.spice')==ref['source_view_sha256']
    bindings={path:sha(path) for path in (source,gds,cdl,a.cdl/'manifest.json',a.cdl/'source_reference.spice',a.saved_audit,a.buffer/'manifest.json')}
    pdk=Path('/foss/pdks/ihp-sg13g2');assert (pdk/'COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    decks={str(path.relative_to(pdk)):sha(path) for kind in ('drc','lvs') for path in (pdk/('libs.tech/klayout/tech/'+kind)).rglob('*') if path.is_file() and path.suffix in ('.drc','.lvs','.lylvs','.rb','.json','.py')}
    a.output.mkdir(parents=True);out=a.output.resolve();top='g1_ota_source_faithful'
    result=dict(status='running',GDS_sha256=sha(gds),source_sha256=sha(source),CDL_sha256=sha(cdl),saved_audit_sha256=sha(a.saved_audit),
                script_sha256=sha(Path(__file__)),contract_sha256=sha(Path(__file__).with_name('STOCK_BUFFER_CONTRACT_20260922.md')),
                stock_deck_hashes=decks,checks=[],density='not run',antenna='not run',PEX='not run',full_SENSE='not run',
                stock_written_junction_applicability='not run; earlier prototype annotation failures retained',shared_source_model_applicability='not run',adoption='not run')
    stopped=False
    for kind in ('drc','lvs'):
        if stopped:result['checks'].append(dict(kind=kind,status='not run',reason='earlier check failed'));continue
        run_dir=out/kind;runner=pdk/('libs.tech/klayout/tech/'+kind+'/run_'+kind+'.py')
        cmd=['python3',str(runner),'--run_mode=deep','--topcell='+top,'--run_dir='+str(run_dir)]
        cmd+=['--path='+str(gds),'--no_density','--mp=1'] if kind=='drc' else ['--layout='+str(gds),'--netlist='+str(cdl)]
        log=out/(kind+'.log');started=time.monotonic()
        with log.open('x') as stream:proc=subprocess.run(['timeout','--kill-after=5','180']+cmd,stdout=stream,stderr=subprocess.STDOUT)
        row=dict(kind=kind,status='failed',command=cmd,child_limit_s=180,returncode=proc.returncode,wall_s=time.monotonic()-started,log_sha256=sha(log))
        if kind=='drc':
            reports=[]
            for path in sorted(run_dir.rglob('*.lyrdb')):
                categories=collections.Counter(item.findtext('category').strip("'") for item in ET.parse(path).findall('.//items/item'))
                reports.append(dict(path=str(path.relative_to(out)),sha256=sha(path),markers=sum(categories.values()),categories=dict(categories)))
            row['reports']=reports
            if proc.returncode==0 and reports and all(r['markers']==0 for r in reports):row['status']='passed'
        else:
            text=log.read_text(errors='replace')+'\n'+'\n'.join(path.read_text(errors='replace') for path in run_dir.rglob('*.log'))
            explicit='Congratulations! Netlists match.' in text and "Netlists don't match" not in text
            dbs=[dict(path=str(path.relative_to(out)),sha256=sha(path),xref=strict_xref(path)) for path in sorted(run_dir.rglob('*.lvsdb'))]
            row.update(explicit_comparison_pass=explicit,databases=dbs)
            if proc.returncode==0 and explicit and dbs and all(r['xref']['status']=='passed' for r in dbs):row['status']='passed'
        row['output_bytes']=output_bytes(out)
        if row['output_bytes']>50*2**20:row.update(status='failed',phase_growth_exceeded=True)
        result['checks'].append(row);stopped=row['status']!='passed';(out/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(row),flush=True)
    result['all_live_input_bindings_unchanged']=all(sha(path)==digest for path,digest in bindings.items())
    result['all_stock_decks_unchanged']=all(sha(pdk/path)==digest for path,digest in decks.items())
    result['status']='passed' if result['all_live_input_bindings_unchanged'] and result['all_stock_decks_unchanged'] and all(r['status']=='passed' for r in result['checks']) else 'failed'
    (out/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status']}))
if __name__=='__main__':main()
