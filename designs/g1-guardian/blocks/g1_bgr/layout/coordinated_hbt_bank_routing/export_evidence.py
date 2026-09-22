#!/usr/bin/env python3
"""Exact completed evidence export; retain failures, never stage or overwrite."""
import argparse
import datetime
import getpass
import hashlib
import json
from pathlib import Path
import re

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[5]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--resource-gate',required=True,type=Path);a=ap.parse_args()
    gate=json.loads(a.resource_gate.read_text())
    stamp=datetime.datetime.strptime(gate['utc'].replace('+00:00',''),'%Y-%m-%dT%H:%M:%S.%f').replace(tzinfo=datetime.timezone.utc)
    assert gate['status']=='passed' and gate['expected_growth_gib']>=.2
    assert 0<=(datetime.datetime.now(datetime.timezone.utc)-stamp).total_seconds()<1800
    scratch=ROOT/'build/scratch'
    common=['bank.gds','bank.cdl','placement.json','route_ledger.json','terminal_graph.json',
            'all_star_interfaces_cut.json','individual_star_cuts.json','local_spacing_ownership.json',
            'neighbor_obstructions.json','preparation.json','assignment_review.json','run.json','prepare.log']
    groups={
      'return_controls/r1':(scratch/'bgr-hbt-return-controls-20260922-r1',
          ['run.json','prepare_return_controls.py','run_return_controls.py','PREPARATION_CONTRACT_20260922.md','run.sh']),
      'return_controls/r2':(scratch/'bgr-hbt-return-controls-20260922-r2',
          ['controls.json','bank_source_placement_ledger.json','bgr_hbt_return_control_01.gds',
           'bgr_hbt_return_control_02.gds','bgr_hbt_return_control_01.cdl','bgr_hbt_return_control_02.cdl','run.json','prepare.log']),
      'fullbank/r1':(scratch/'bgr-hbt-fullbank-20260922-r1',common),
      'fullbank/r2':(scratch/'bgr-hbt-fullbank-20260922-r2',common+['dummy_seed_proof.json','derived_builder.py','revision_audit.json']),
    }
    statuses={}
    for kind in ('drc','lvs'):
        base=scratch/('bgr-hbt-fullbank-stock-20260922-r2-'+kind)
        status=json.loads((base/'summary.json').read_text())['status']
        assert status in ('passed','failed'), 'completed stock receipt required, not necessarily passed'
        statuses[kind]=status
        names=['summary.json','stock.log']+[str(p.relative_to(base)) for p in sorted((base/'reports').rglob('*'))
                if p.is_file() and p.suffix in ('.lyrdb','.lvsdb','.log','.cir')]
        groups['stock/'+kind]=(base,names)
    assert json.loads((groups['return_controls/r1'][0]/'run.json').read_text())['status']=='failed before geometry launch'
    assert json.loads((groups['return_controls/r2'][0]/'run.json').read_text())['status']=='passed'
    assert json.loads((groups['fullbank/r1'][0]/'preparation.json').read_text())['status']=='failed preparation'
    assert json.loads((groups['fullbank/r2'][0]/'preparation.json').read_text())['status']=='passed preparation'
    rows=[];total=0
    forbidden=re.compile(rb'/home/|/opt/sim|\.private')
    local_user=getpass.getuser().encode()
    for group,(base,names) in groups.items():
        for name in names:
            p=base/name;assert p.is_file() and not p.is_symlink()
            data=p.read_bytes();assert not forbidden.search(data) and local_user not in data,str(p)
            if p.suffix=='.json':json.loads(data.decode())
            rows.append(dict(source=str(p.relative_to(ROOT)),export=group+'/'+name,sha256=sha(p),bytes=len(data)))
            total+=len(data)
    assert total<.2*2**30 and gate['effective_storage_free_bytes']>total+8*2**30
    out=HERE/'evidence/20260922-r1';out.mkdir(parents=True,exist_ok=False)
    for row in rows:
        source=ROOT/row['source'];target=out/row['export'];target.parent.mkdir(parents=True,exist_ok=True)
        assert sha(source)==row['sha256']
        target.write_bytes(source.read_bytes())
        assert sha(target)==row['sha256'] and target.stat().st_size==row['bytes']
    result=dict(status='passed exact export and privacy/JSON checks',artifacts=rows,
                artifact_count=len(rows),artifact_bytes=total,stock_statuses=statuses,
                preserved_failures=['return control r1 prelaunch error','fullbank r1 real port short and nine absent dummy-B probes'],
                full_BGR_PEX_analog_density_antenna='not run',resource_gate_sha256=sha(a.resource_gate),
                script_sha256=sha(Path(__file__)))
    (out/'export_manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('status','artifact_count','artifact_bytes','stock_statuses')},indent=2))

if __name__=='__main__':main()
