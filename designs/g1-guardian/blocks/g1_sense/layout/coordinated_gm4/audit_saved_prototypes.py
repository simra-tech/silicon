#!/usr/bin/env python3
"""Re-read saved prototype polygons and independently repeat native/terminal gates."""
import argparse,hashlib,json,os
from pathlib import Path
from build_native_prototypes import nets,snapshot,pya

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--prototype',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0))==1
    m=json.loads((a.prototype/'manifest.json').read_text());gds=a.prototype/'native_prototypes.gds';assert sha(gds)==m['GDS_sha256']
    ly=pya.Layout();ly.read(str(gds));rows=[]
    for record in m['cells']:
        cell=ly.cell(record['cell']);channels=snapshot(cell,1)&snapshot(cell,5);boxes=[p.bbox() for p in channels.each()]
        expected=record.get('ng',2*record.get('logical_ng',0));actual_w=sum(b.height()*.001 for b in boxes)
        expected_w=record.get('W_um',2*record.get('logical_W_um',0));lengths=sorted(set(b.width()*.001 for b in boxes))
        assert len(boxes)==expected and abs(actual_w-expected_w)<1e-8 and lengths==[record['L_um']]
        terminal=nets(cell,record['terminal_audit']['probes']);assert terminal['status']=='passed'
        rows.append(dict(cell=cell.name,actual_gate_count=len(boxes),actual_total_W_um=actual_w,L_um=lengths,terminal_audit=terminal))
    result={'status':'passed saved-GDS native/terminal audit','GDS_sha256':sha(gds),'manifest_sha256':sha(a.prototype/'manifest.json'),
            'script_sha256':sha(Path(__file__)),'cells':rows,'new_GDS_saved':False,'stock_checks':'not run'}
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'cells':len(rows)},indent=2))
if __name__=='__main__':main()
