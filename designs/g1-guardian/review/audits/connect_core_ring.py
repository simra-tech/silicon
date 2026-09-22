#!/usr/bin/env python3
"""Restore source-native corner via arrays in expanded core supply rings."""
import argparse
import collections
import json
import os
from pathlib import Path
import pya
from audit_placed_decap_domains import physical,identity,sha,DESIGN,HERE
from place_closed_analog import region,text_records


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--placement',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    assert not args.output.exists() and len(os.sched_getaffinity(0))==1 and pya.__version__=='0.30.9'
    baseline=DESIGN/'blocks/g1_padring/layout/g1_chip_top.gds'
    assert sha(baseline)=='38c1d6d13bbfee4ed0e3c01477742c3d2d28317d9215d9e5bd9a35551285ae59'
    parent=json.loads((args.placement/'analysis.json').read_text())
    parent_gds=args.placement/'placed_core.gds'
    assert sha(parent_gds)==parent['GDS_sha256'] and parent['status']=='passed source-preserving core placement'
    old=pya.Layout();old.read(str(baseline));ot=old.cell('g1_chip_top')
    new=pya.Layout();new.read(str(parent_gds));nt=new.top_cell()
    assert old.dbu==new.dbu==.001
    oldnet,oldlayers=physical(old,ot)
    anchors={'VDD':identity(oldnet,oldlayers[134],[395000,354660]),
             'VSS':identity(oldnet,oldlayers[134],[507000,334660])}
    assert None not in anchors.values() and len(set(anchors.values()))==2
    by_net={v:k for k,v in anchors.items()}
    inventory_path=HERE/'fit-ring-layer-screen-20260922-r2.json'
    inventory=json.loads(inventory_path.read_text())['actual_core_ring_conductors']
    rings=[]
    before={str(info):region(new,nt,info) for info in new.layer_infos()}
    before_text=text_records(new,nt)
    for row in inventory:
        layer=row['layer'];box=pya.DBox(*row['bbox_um']).to_itype(.001)
        netid=identity(oldnet,oldlayers[layer],[box.center().x,box.center().y])
        assert netid in by_net
        east=layer==126 and box.left>986000
        north=layer==134 and box.bottom>986000
        expanded=pya.Box(box.left+(64000 if east else 0),box.bottom+(64000 if north else 0),
                         box.right+(64000 if layer==134 or east else 0),box.top+(64000 if layer==126 or north else 0))
        assert (pya.Region(expanded)-region(new,nt,pya.LayerInfo(layer,0))).is_empty()
        rings.append(dict(layer=layer,box=box,expanded=expanded,net=by_net[netid],east=east,north=north))
    source_cuts=region(old,ot,pya.LayerInfo(133,0))
    additions=pya.Region();corners=[]
    for vertical in [r for r in rings if r['layer']==126]:
        for horizontal in [r for r in rings if r['layer']==134]:
            overlap=pya.Region(vertical['box'])&pya.Region(horizontal['box'])
            if overlap.is_empty():
                continue
            assert vertical['net']==horizontal['net']
            transform=pya.Trans(64000 if vertical['east'] else 0,64000 if horizontal['north'] else 0)
            expected=overlap.transformed(transform)
            assert (expected^(pya.Region(vertical['expanded'])&pya.Region(horizontal['expanded']))).is_empty()
            selected=pya.Region()
            for polygon in source_cuts.each():
                r=pya.Region(polygon)
                if not (r&overlap).is_empty():
                    assert (r-overlap).is_empty(), 'Never clip a source-native cut'
                    selected.insert(polygon)
            assert not selected.is_empty()
            moved=selected.transformed(transform)
            assert (moved&region(new,nt,pya.LayerInfo(133,0))).is_empty()
            additions+=moved
            corners.append(dict(net=vertical['net'],corner=('east'if vertical['east']else'west')+'_'+('north'if horizontal['north']else'south'),
                                cuts=selected.count(),source_area_um2=selected.area()*1e-6,transform=str(transform),
                                source_cut_polygon_strings=[str(p) for p in selected.each()]))
    assert len(corners)==8 and collections.Counter(r['net']for r in corners)=={'VDD':4,'VSS':4}
    for polygon in additions.each():
        nt.shapes(new.layer(133,0)).insert(polygon)
    for info in new.layer_infos():
        actual=region(new,nt,info)
        expected=before[str(info)]+additions if info==pya.LayerInfo(133,0) else before[str(info)]
        assert (actual^expected).is_empty()
    assert text_records(new,nt)==before_text
    newnet,newlayers=physical(new,nt)
    groups=collections.defaultdict(set)
    for row in rings:
        point=row['expanded'].center()
        found=identity(newnet,newlayers[row['layer']],[point.x,point.y])
        assert found is not None
        groups[row['net']].add(found)
    assert all(len(group)==1 for group in groups.values()) and groups['VDD']!=groups['VSS']
    args.output.mkdir(parents=True)
    output=args.output/'ring_connected_core.gds'
    new.write(str(output))
    saved=pya.Layout();saved.read(str(output))
    assert text_records(saved,saved.top_cell())==before_text
    for info in new.layer_infos():
        assert (region(new,nt,info)^region(saved,saved.top_cell(),info)).is_empty()
    result=dict(status='passed exact-native corner arrays and two-ring connectivity',
                GDS_sha256=sha(output),parent_GDS_sha256=sha(parent_gds),baseline_sha256=sha(baseline),
                script_sha256=sha(Path(__file__)),ring_inventory_sha256=sha(inventory_path),KLayout=pya.__version__,
                corners=corners,added_TopVia2_cuts=sum(r['cuts']for r in corners),
                native_geometry_and_texts_unchanged_except_copied_cuts='passed',saved_roundtrip='passed',
                physical_ring_components={k:[list(n)for n in v]for k,v in groups.items()},
                not_run=['stock DRC of added arrays in new context','decap row and macro feeds','padframe/sealring',
                         'fullchip LVS/PEX/currentIR/EM','electrical adoption'])
    (args.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='corners'},indent=2))


if __name__=='__main__':
    main()
