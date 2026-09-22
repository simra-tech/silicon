#!/usr/bin/env python3
"""Two unchanged stock checks on the frozen399-resistor pilot."""
import collections
import json
from pathlib import Path
import subprocess
import time
import xml.etree.ElementTree as ET
import pya
from run_second_stock import sha, strict


def main():
    root=Path(__file__).resolve().parents[6];pdk=Path('/foss/pdks/ihp-sg13g2')
    base=root/'build/scratch/bgr-resistor-bank-pilot-20260922-r2'
    out=root/'build/scratch/bgr-resistor-bank-stock-20260922-r2'
    assert pya.__version__=='0.30.9' and (pdk/'COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    manifest=json.loads((base/'manifest.json').read_text());assert manifest['status']=='passed scoped geometry/terminal gate'
    gds=base/'bgr_resistor_bank_pilot.gds';cdl=base/'bgr_resistor_bank_pilot.cdl'
    assert sha(gds)==manifest['GDS_sha256']=='4019838faa0efb2b5038e69f9652c6e52eb60ab070ac964f2d39f72af29e0d17'
    assert sha(cdl)==manifest['CDL_sha256']=='8d8952e9a4fe8322f8ced32d3d4502433fdfff1af806acc27e1ecaf931cddb7f'
    source=root/'designs/g1-guardian/blocks/g1_bgr/sim/qualification/candidates/bgr_loop24_qref4_r253p465_hv06/bgr_loop24_qref4_r253p465_hv06.spice'
    assert sha(source)==manifest['source_sha256']
    out.mkdir(parents=True,exist_ok=False)
    decks={str(p.relative_to(pdk)):sha(p) for kind in ['drc','lvs'] for p in (pdk/('libs.tech/klayout/tech/'+kind)).rglob('*')
           if p.is_file() and p.suffix in ['.drc','.lvs','.lylvs','.rb','.json','.py']}
    result=dict(status='running',source_sha256=sha(source),GDS_sha256=sha(gds),CDL_sha256=sha(cdl),
                script_sha256=sha(Path(__file__)),strict_checker_sha256=sha(Path(__file__).with_name('run_second_stock.py')),
                contract_sha256=sha(Path(__file__).with_name('RESISTOR_BANK_STOCK_R2_CONTRACT_20260922.md')),
                stock_deck_hashes=decks,checks=[],density='not run',antenna='not run',PEX='not run',seed='not applicable')
    for kind in ['drc','lvs']:
        run_dir=out/kind
        cmd=['python3',str(pdk/('libs.tech/klayout/tech/'+kind+'/run_'+kind+'.py')),'--run_mode=deep','--topcell=bgr_resistor_bank_pilot','--run_dir='+str(run_dir)]
        cmd+=['--path='+str(gds),'--no_density','--mp=1'] if kind=='drc' else ['--layout='+str(gds),'--netlist='+str(cdl)]
        log=out/(kind+'.log');start=time.monotonic()
        with log.open('x') as handle:proc=subprocess.run(['timeout','--kill-after=5','180']+cmd,stdout=handle,stderr=subprocess.STDOUT)
        row=dict(kind=kind,command=cmd,returncode=proc.returncode,wall_s=time.monotonic()-start,log_sha256=sha(log),status='failed')
        if kind=='drc':
            reports=[]
            for p in sorted(run_dir.rglob('*.lyrdb')):
                counts=collections.Counter(x.findtext('category') for x in ET.parse(p).findall('.//items/item'))
                reports.append(dict(path=str(p.relative_to(out)),sha256=sha(p),markers=sum(counts.values()),categories=dict(counts)))
            row['reports']=reports;passed=bool(reports) and all(r['markers']==0 for r in reports)
        else:
            logs='\n'.join(p.read_text(errors='replace') for p in run_dir.rglob('*.log'))
            row['strict_cross_references']=[strict(p) for p in sorted(run_dir.rglob('*.lvsdb'))]
            row['explicit_match']='Congratulations! Netlists match.' in logs and "Netlists don't match" not in logs
            passed=row['explicit_match'] and bool(row['strict_cross_references']) and all(r['status']=='passed' for r in row['strict_cross_references'])
        row['output_bytes']=sum(p.stat().st_size for p in out.rglob('*') if p.is_file())
        if proc.returncode==0 and passed and row['output_bytes']<.15*2**30:row['status']='passed'
        result['checks'].append(row);(out/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(row),flush=True)
    result['inputs_unchanged']=sha(gds)==manifest['GDS_sha256'] and sha(cdl)==manifest['CDL_sha256'] and sha(source)==manifest['source_sha256']
    result['stock_decks_unchanged']=all(sha(pdk/p)==h for p,h in decks.items())
    result['status']='passed' if result['inputs_unchanged'] and result['stock_decks_unchanged'] and all(r['status']=='passed' for r in result['checks']) else 'failed'
    (out/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(result['status'])


if __name__=='__main__':main()
