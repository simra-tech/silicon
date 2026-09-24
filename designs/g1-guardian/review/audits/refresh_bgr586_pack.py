#!/usr/bin/env python3
"""Refresh only two source-bound native rectangles in frozen r4; no design GDS."""
import argparse,copy,hashlib,json
from pathlib import Path

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def overlap(a,b):return min(a[2],b[2])-max(a[0],b[0])>1e-8 and min(a[3],b[3])-max(a[1],b[1])>1e-8
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--pack',type=Path,required=True);p.add_argument('--source',type=Path,required=True);p.add_argument('--diffusion-proof',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists() and sha(a.source)=='586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b'
    old=json.loads(a.pack.read_text());result=copy.deepcopy(old);proof=json.loads(a.diffusion_proof.read_text())
    assert old['BGR_source_sha256']=='53513ab43c62ead3a4c171f5a026b165e2a0bfda2b5b0cb5b104a30aae33a4e2'
    assert proof['normalized_source_and_drain_geometry_identical'] and not proof['errors']
    lines={r.split()[0]:r for r in a.source.read_text().splitlines() if r.startswith(('XM','XR','XQ'))}
    assert len(lines)==len(result['BGR_devices'])==1036
    changes=[]
    for row in result['BGR_devices']:
        new=lines[row['name']]
        if new==row['source_line']:continue
        assert row['name'] in ('XM31','XM33') and new==row['source_line'].replace('l=0.5u','l=0.6u')
        assert row['width_um']==1.72 and row['height_um']==2.04
        before=copy.deepcopy(row);row['source_line']=new;row['width_um']=1.82;row['bbox_um'][2]+=.1;row['reservation_um'][2]+=.1
        changes.append(dict(name=row['name'],before=before,after=copy.deepcopy(row),native_area_delta_um2=.204))
    assert len(changes)==2
    boxes=result['BGR_devices']
    assert all(not overlap(r['bbox_um'],s['bbox_um']) for i,r in enumerate(boxes) for s in boxes[i+1:])
    assert all(all(abs(v/.005-round(v/.005))<1e-7 for v in r['bbox_um']) for r in boxes)
    assert all(r['reservation_um'][0]>=0 and r['reservation_um'][1]>=0 and r['reservation_um'][2]<=420 and r['reservation_um'][3]<=354 for r in boxes)
    result['BGR_source_sha256']=sha(a.source)
    result['refresh_586']={'status':'passed scoped native bbox/source refresh','script_sha256':sha(Path(__file__)),
        'parent_pack_sha256':sha(a.pack),'diffusion_proof_sha256':sha(a.diffusion_proof),'changes':changes,'native_area_delta_um2':.408,
        'placement_policy':'Preserve native bbox lower-left and Activ origin; extend right edge and right engineering reservation0.1um. All other native placements and entire floorplan/decap assignment unchanged.',
        'unchanged_fields':[k for k in old if k not in ('BGR_devices','BGR_source_sha256')],
        'scope':'Source535-to586 only. Does not repair failed SENSE inherited buffer fidelity or establish legal wells/guards/feed routing/retained-PDN fit. Root isolated BGR prototype checks remain separate. No GDS saved.'}
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['refresh_586'],indent=2))
if __name__=='__main__':main()
