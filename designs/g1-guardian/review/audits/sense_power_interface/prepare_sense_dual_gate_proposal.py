#!/usr/bin/env python3
"""Prepare source-bound opposite-end contact rectangles; no geometry is saved."""
import argparse
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
GM4=HERE.parents[2]/'blocks/g1_sense/layout/coordinated_gm4'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--sides',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert not a.output.exists()
    sides=json.loads(a.sides.read_text())
    refpath=GM4/'ring-r8-evidence-20260922-r1/sense-ring-reference-20260922-r8a/manifest.json'
    ref=json.loads(refpath.read_text());assert sha(refpath)==sides['reference_sha256']
    source=GM4.parents[1]/'reports/resume-server-20260922/gm4comp3-qualified-source.spice'
    assert sha(source)==sides['source_sha256']=='baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877'
    specs={d['device']:d for d in ref['devices']};rows=[]
    for index,q in enumerate(sides['channels']):
        d=specs[q['device']];x,y=[round(v*1000)for v in q['gate_witness_um']]
        hw=round(d['W_um']/d['ng']*500);hl=round(d['L_um']*500)
        old=q['contact'];direction=1 if old['side']=='south'else-1
        edge=y+direction*hw;cy=edge+direction*330
        poly_y=sorted((edge+direction*100,edge+direction*480))
        oldbox=old['contact_bbox_dbu'];oldcy=(oldbox[1]+oldbox[3])//2
        rectangles=[dict(layer=[5,0],role='opposite_poly_head',bbox_dbu=[x-max(hl,150),poly_y[0],x+max(hl,150),poly_y[1]]),
                    dict(layer=[6,0],role='opposite_contact',bbox_dbu=[x-80,cy-80,x+80,cy+80]),
                    dict(layer=[8,0],role='opposite_M1_pad',bbox_dbu=[x-150,cy-150,x+150,cy+150]),
                    dict(layer=[8,0],role='gate_center_M1_bridge',bbox_dbu=[x-80,min(oldcy,cy),x+80,max(oldcy,cy)])]
        assert all(v%5==0 for r in rectangles for v in r['bbox_dbu'])
        assert all(r['bbox_dbu'][0]<r['bbox_dbu'][2]and r['bbox_dbu'][1]<r['bbox_dbu'][3]for r in rectangles)
        channel=[x-hl,y-hw,x+hl,y+hw]
        ph=rectangles[0]['bbox_dbu'];assert ph[3]<=channel[1]or ph[1]>=channel[3]
        rows.append(dict(id=index,device=q['device'],source_line=d['source_line'],channel_bbox_dbu=channel,
            existing_gate_contact=old,opposite_contact_side='north'if direction==1 else'south',
            rectangles=rectangles,nominal_neighbor_SD_M1_gap_dbu=hl+30,
            required_actual_clearance_check='not run'))
    assert len(rows)==835 and len({r['device']for r in rows})==58
    result=dict(status='prepared835-site source-held geometry proposal; saved-native legality not run',
        source_sha256=sha(source),GDS_sha256=sides['GDS_sha256'],side_audit_sha256=sha(a.sides),
        reference_sha256=sha(refpath),script_sha256=sha(Path(__file__)),
        source_ngcon_held=2,no_source_or_geometry_modified=True,rows=rows,
        prohibited=['No Via1/M2 additions on opposite complementary gate buses',
                    'No active/channel/implant/well/device/centroid changes','No PDK/model edits or mismatch splits'],
        next_gates=['Exact saved-native M1/Cont/poly foreign-net and existing-via screen',
                    'All active/channel and source-device fingerprints unchanged',
                    'Native source graph134 classes held; all actual pins and both gate contacts audited',
                    'Stock main and strict source LVS; native per-device AP/835channels/48sharedstrips held',
                    'Source-held zeroR full parameter/wave controls before electrical use',
                    'Affected final fullchip fill/DRC/antenna and nearfill extraction after reviewed integration'],
        not_run=['New GDS','Geometry collision/spacing checks','Stock DRC/LVS','Electrical parity','Adoption'])
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items()if k!='rows'},indent=2))


if __name__=='__main__':main()
