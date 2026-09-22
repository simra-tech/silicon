#!/usr/bin/env python3
"""Compact isolated power milestone; explicit portable derivatives, no Git writes."""
import argparse,getpass,hashlib,json,os,re
from pathlib import Path

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[5]
SOURCES='inventory_power_cutpaths.py build_power_revision.py audit_power_reference.py run_power_stock.py audit_power_capacity.py audit_power_contacts.py audit_power_ports_revision.py POWER_STOCK_CONTRACT_20260922.md POWER_ROUTING_REVIEW_20260922.md export_power_evidence.py'.split()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--refreeze',action='store_true');a=p.parse_args()
    a.output=a.output.resolve();assert not a.output.exists()or a.refreeze
    bulk=Path(os.environ['G1_RESULTS_ROOT']).resolve()
    final=json.loads((bulk/'sense-power-stock-20260922-r4/summary.json').read_text());assert final['status']=='passed'
    assert final['GDS_sha256']=='5d640799cb0a4257d34e82a1018237a6bfa0d595bc0d6520522d40125322c170'
    selected=[]
    def add(relative):
        f=bulk/relative;assert f.is_file()and not f.is_symlink(),relative
        selected.append((f,Path(relative),'external-relative:'+relative))
    for i in range(1,5):
        for name in('builder_snapshot.py','manifest.json'):add(f'sense-power-routing-20260922-r{i}/'+name)
        for name in('summary.json','drc.log','drc/g1_sense_physical_g1_sense_physical_full.lyrdb'):
            add(f'sense-power-stock-20260922-r{i}/'+name)
        if i in(2,4):
            for name in('lvs.log','lvs/g1_sense_physical_extracted.cir'):add(f'sense-power-stock-20260922-r{i}/'+name)
    for name in('g1_sense_physical.gds',):add('sense-power-routing-20260922-r4/'+name)
    for name in('manifest.json','g1_sense_physical.cdl','audit_snapshot.py'):add('sense-power-reference-20260922-r4/'+name)
    for name in('sense-r5-power-cutpaths-20260922-r1.json','sense-r5-power-cutpaths-20260922-r3.json',
        'sense-power-capacity-20260922-r1.json','sense-power-capacity-20260922-r3.json','sense-power-capacity-20260922-r4.json',
        'sense-power-contacts-20260922-r2.json','sense-power-contacts-20260922-r3.json','sense-power-junction-20260922-r2.json',
        'sense-power-junction-20260922-r4.json','sense-power-ports-20260922-r4b.json'):add(name)
    for receipt in('sense_power_inventory_20260922_r2','sense_power_ports_20260922_r4'):
        for name in('check.json','check.log'):
            f=ROOT/'.private/research/verification'/receipt/name;assert f.is_file()
            selected.append((f,Path('retained-audit-failures')/receipt/name,'verification-receipt:'+receipt+'/'+name))
    assert sum(f.stat().st_size for f,_,_ in selected)<35*2**20
    def portable(text):
        return text.replace(str(bulk),'${RESULTS_ROOT}').replace(str(ROOT),'${WORKSPACE}')
    def private_check(data):
        text=data.decode();assert getpass.getuser()not in text
        assert not re.search(r'/(?:home|Users|opt/sim)/[^\s"<>]+',text)
        assert ('.private/'+'CONTEXT')not in text
    a.output.mkdir(parents=True,exist_ok=a.refreeze);rows=[]
    for source,relative,origin in selected:
        raw=source.read_bytes();encoded=raw if source.suffix=='.gds'else portable(raw.decode()).encode()
        if source.suffix!='.gds':private_check(encoded)
        dest=a.output/relative
        if a.refreeze:assert dest.read_bytes()==encoded
        else:dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(encoded)
        rows.append(dict(path=str(dest.relative_to(ROOT)),sha256=sha(dest),bytes=len(encoded),source=origin,
            source_sha256=sha(source),transformation='byte-exact'if raw==encoded else'explicit runtime-results/workspace-prefix replacement; original retained'))
    export=a.output/'export_manifest.json'
    export.write_text(json.dumps(dict(status='passed compact power-routing export',files=rows,
        exporter_sha256=sha(Path(__file__)),original_artifacts_retained=True,full_current_margin='not run',complete_PEX='not run',adoption='not run'),indent=2)+'\n')
    frozen=[]
    for f in [HERE/name for name in SOURCES]+[a.output/Path(r['path']).relative_to(a.output.relative_to(ROOT))for r in rows]+[export]:
        assert f.is_file()and not f.is_symlink()
        if f.suffix!='.gds':private_check(f.read_bytes())
        frozen.append(dict(path=str(f.relative_to(ROOT)),sha256=sha(f),bytes=f.stat().st_size))
    inventory=a.output/'commit_inventory.json'
    result=dict(status='frozen isolated power-routing milestone; root owns Git',files=sorted(frozen,key=lambda r:r['path']),
        count=len(frozen),bytes=sum(r['bytes']for r in frozen),excludes=['previously committed r5 assembly and PEX method files',
        'raw binary LVS databases retained externally with hashes in stock reports','new ownership-method investigations'])
    inventory.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],count=result['count'],bytes=result['bytes'],inventory_path=str(inventory.relative_to(ROOT)),inventory_sha256=sha(inventory)),indent=2))

if __name__=='__main__':main()
