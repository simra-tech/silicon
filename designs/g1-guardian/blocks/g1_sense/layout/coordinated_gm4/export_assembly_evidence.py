#!/usr/bin/env python3
"""Copy one byte-exact completed assembly milestone; no Git or canonical edits."""
import argparse,getpass,hashlib,json,re,shutil
from pathlib import Path

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[5]
SOURCES='CORE8_ASSEMBLY_CONTRACT_20260922.md CORE8_STOCK_CONTRACT_20260922.md FULLMAIN_CONTRACT_20260922.md RESBANK_CONTRACT_20260922.md FULL_SENSE_CONTRACT_20260922.md build_core8.py audit_core8_reference.py run_core8_stock.py build_full_main.py audit_fullmain_reference.py audit_fullmain_revision.py run_fullmain_stock.py build_sense_resistor_bank.py audit_resbank_reference.py run_resbank_stock.py build_full_sense.py audit_full_sense_reference.py run_full_sense_stock.py audit_full_sense_junctions.py audit_sense_annotation_revision.py export_assembly_evidence.py ASSEMBLY_RESULTS_20260922.md'.split()
SOURCES.append('README.md')
RUNS=['sense-core8-20260922-r1','sense-core8-reference-20260922-r1','sense-core8-stock-20260922-r1']
RUNS += ['sense-fullmain-'+v+'20260922-r'+str(i)for v in('','reference-','stock-')for i in(1,2)]
RUNS += ['sense-resbank-20260922-r1','sense-resbank-20260922-r2','sense-resbank-reference-20260922-r1','sense-resbank-stock-20260922-r1']
RUNS += ['sense-fullassembly-'+v+'20260922-r'+str(i)for v,ns in(('',range(1,6)),('reference-',range(1,6)),('stock-',range(1,5)))for i in ns]
RUNS += ['sense-core8-stock-preparation-20260922-r1','sense-resbank-stock-20260922-r1-preparation']
RUNS += ['sense-fullmain-stock-20260922-r'+str(i)+'-preparation'for i in(1,2)]
RUNS += ['sense-fullassembly-stock-20260922-r'+str(i)+'-preparation'for i in range(1,5)]
EXTRA=['sense-fullmain-r2-revision-audit.json','sense-fullassembly-stock-junctions-20260922-r1.json','sense-fullassembly-stock-junctions-20260922-r2.json','sense-fullassembly-annotation-revision-20260922-r1.json']
SUFFIXES={'.py','.json','.md','.gds','.cdl','.cir','.log','.lyrdb','.lvsdb'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output=a.output.resolve();assert not a.output.exists()
    final=json.loads((ROOT/'build/scratch/sense-fullassembly-stock-20260922-r4/summary.json').read_text());assert final['status']=='passed' and final['checks'][-1]['nine_source_pin_gate']
    selected=[]
    for name in RUNS:
        directory=ROOT/'build/scratch'/name;assert directory.is_dir(),name
        for f in sorted(directory.rglob('*')):
            assert not f.is_symlink(),f
            if f.is_file() and f.suffix in SUFFIXES:selected.append((f,Path(name)/f.relative_to(directory)))
    for name in EXTRA:
        f=ROOT/'build/scratch'/name;assert f.is_file();selected.append((f,Path(name)))
    assert sum(f.stat().st_size for f,_ in selected)<50*2**20
    for f,_ in selected:
        if f.suffix in('.py','.json','.md','.cdl','.cir','.log','.lyrdb'):
            text=f.read_text(errors='replace')
            assert not re.search(r'/home/|/opt/sim/|\.private/CONTEXT',text) and getpass.getuser() not in text,f
    a.output.mkdir(parents=True);rows=[]
    for original,rel in selected:
        target=a.output/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(original,target);assert sha(target)==sha(original)
        rows.append(dict(path=str(target.relative_to(ROOT)),original_path=str(original.relative_to(ROOT)),sha256=sha(target),bytes=target.stat().st_size))
    result=dict(status='passed byte-exact completed assembly export',scope='Core8/fullmain/resbank/full-SENSE successes and retained failures only; previously committed buffer/stacked artifacts are referenced, not recopied. No extraction/adoption claim.',files=rows,bytes=sum(r['bytes']for r in rows),script_sha256=sha(Path(__file__)))
    manifest=a.output/'export_manifest.json';manifest.write_text(json.dumps(result,indent=2)+'\n')
    frozen=[dict(path=r['path'],sha256=r['sha256'],bytes=r['bytes'])for r in rows]
    for name in SOURCES:
        f=HERE/name;assert f.is_file();frozen.append(dict(path=str(f.relative_to(ROOT)),sha256=sha(f),bytes=f.stat().st_size))
    frozen.append(dict(path=str(manifest.relative_to(ROOT)),sha256=sha(manifest),bytes=manifest.stat().st_size))
    inventory=a.output/'commit_inventory.json';inventory.write_text(json.dumps(dict(status='frozen completed assembly milestone; root owns Git',files=sorted(frozen,key=lambda r:r['path']),count=len(frozen),bytes=sum(r['bytes']for r in frozen),excludes=['already committed buffer/stacked artifacts','new active PEX/fill preparations','private context/resource receipts']),indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],exported_files=len(rows),commit_files=len(frozen),bytes=sum(r['bytes']for r in frozen),inventory_path=str(inventory.relative_to(ROOT)),inventory_sha256=sha(inventory)),indent=2))
if __name__=='__main__':main()
