#!/usr/bin/env python3
"""Saved nine-port annotations and exact r3-to-r4 notch-only geometry control."""
import argparse,json,os
from pathlib import Path
from build_native_prototypes import pya,snapshot,sha

def read(folder):
    manifest=json.loads((folder/'manifest.json').read_text());path=folder/'g1_sense_physical.gds'
    assert sha(path)==manifest['GDS_sha256'];ly=pya.Layout();ly.read(str(path))
    return ly,ly.cell('g1_sense_physical'),manifest

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in('candidate','prior','prior-contacts','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();assert os.sched_getaffinity(0)=={6}and not a.output.exists()
    ly,cell,manifest=read(a.candidate);pl,prior,pm=read(a.prior)
    contact=json.loads(a.prior_contacts.read_text());assert contact['status']=='passed native-contact and section inventory'and contact['GDS_sha256']==pm['GDS_sha256']
    changes=[]
    for info in ly.layer_infos():
        left=pya.Region([pya.Polygon(x)for x in pya.Region(cell.begin_shapes_rec(ly.layer(info))).each()]).merged()
        right=pya.Region([pya.Polygon(x)for x in pya.Region(prior.begin_shapes_rec(pl.layer(info))).each()]).merged()
        delta=left^right
        if not delta.is_empty():
            assert info.datatype==0 and info.layer in(30,50),info.to_s()
            assert(right-left).is_empty(),'No geometry removal allowed'
            changes.append(dict(layer=info.layer,datatype=info.datatype,added_um2=delta.area()*1e-6))
    # M3 gap already lies inside its native 1.2 um trunk; only the two M4
    # 0.20-by-0.15 um notches add physical area.
    assert {r['layer']for r in changes}=={50}and abs(sum(r['added_um2']for r in changes)-.06)<1e-9,changes
    labels=[];pins=[]
    for li in ly.layer_indexes():
        info=ly.get_info(li)
        if info.datatype==25:
            for shape in cell.shapes(li).each():
                if shape.is_text():labels.append(dict(name=shape.text.string,layer=info.layer,point=shape.text.trans.disp))
        if info.datatype==2:
            for shape in cell.shapes(li).each():
                if shape.is_box()or shape.is_polygon():pins.append((info.layer,shape.polygon))
    assert len(labels)==len(pins)==9,(len(labels),len(pins))
    expected={'sense_n':(50,384.,16.),'sense_p':(50,384.,22.),'vref':(50,384.,180.),
              'iptat':(50,384.,180.8),'isense':(50,384.,181.6),'vped':(50,384.,182.4),
              'vref_buf':(50,384.,183.2),'vdd':(134,383.,218.),'vss':(126,383.,226.)}
    assert {q['name']for q in labels}==set(expected);rows=[]
    for label in labels:
        name=label['name'];layer,x,y=expected[name];point=label['point']
        assert label['layer']==layer and point==pya.DPoint(x,y).to_itype(.001)
        hits=[polygon for metal,polygon in pins if metal==layer and polygon.inside(point)]
        assert len(hits)==1;pin=hits[0];b=pin.bbox();assert(pya.Region(pin)-snapshot(cell,layer)).is_empty()
        if name in('vdd','vss'):assert b.width()==b.height()==4000
        rows.append(dict(name=name,layer=layer,pin_datatype=2,text_datatype=25,point_um=[x,y],
                         bbox_um=[v*.001 for v in(b.left,b.bottom,b.right,b.top)]))
    result=dict(status='passed saved annotation and notch-only revision gate',GDS_sha256=manifest['GDS_sha256'],
        prior_GDS_sha256=pm['GDS_sha256'],script_sha256=sha(Path(__file__)),changes=changes,ports=sorted(rows,key=lambda q:q['name']),
        prior_contacts_sha256=sha(a.prior_contacts),inherited_contact_geometry='Exact Activ/GatPoly/Cont XOR zero; same 285 supply diffusion components and minimum four contacts',
        inherited_MIM_geometry='M5/TopMetal1/Vmim unchanged from independently checked r3',
        current_margin='not run',adoption='not run')
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':main()
