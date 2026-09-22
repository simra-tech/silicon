#!/usr/bin/env python3
"""Add diagnostic M2 row access above intact native decap M1 supply rails."""
import argparse
import collections
import faulthandler
import json
import os
from pathlib import Path
import pya
from audit_placed_decap_domains import physical, identity, sha
from place_closed_analog import region, text_records


def main():
    faulthandler.dump_traceback_later(60,repeat=True)
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--placement',type=Path,required=True)
    p.add_argument('--ring',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0))==1 and pya.__version__=='0.30.9'
    placement=json.loads((a.placement/'analysis.json').read_text())
    ring=json.loads((a.ring/'analysis.json').read_text())
    source=a.ring/'ring_connected_core.gds'
    assert sha(source)==ring['GDS_sha256'] and ring['parent_GDS_sha256']==placement['GDS_sha256']
    assert len(placement['decaps'])==4662
    a.output.mkdir(parents=True)
    (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    ly=pya.Layout();ly.read(str(source));top=ly.top_cell()
    assert ly.dbu==.001
    oldnet,oldlayers=physical(ly,top)
    before={str(i):region(ly,top,i) for i in ly.layer_infos()}
    texts=text_records(ly,top)
    metals={n:pya.Region() for n in ('VDD','VSS')}
    cuts=pya.Region();centers={};buckets=collections.defaultdict(list)
    groups=collections.defaultdict(set);probes=[];rejected=0
    for row in placement['decaps']:
        x0,y0,x1,y1=[round(x*1000)for x in row['intended_LEF_bbox_um']]
        for name,pin in row['pins'].items():
            x,y=pin['placed_dbu'];net=identity(oldnet,oldlayers[8],[x,y])
            assert net is not None
            groups[net].add(name)
            probes.append(dict(index=row['index'],net=name,point=[x,y],before=list(net)))
            metals[name].insert(pya.Box(x0,y-400,x1,y+400))
            # Conservative square spacing >=0.29 um between 0.19 um cuts,
            # including cuts requested by staggered cells in shared rails.
            for cx in (x-250,x+250):
                key=(cx//500,y//500)
                nearby=[v for dx in (-1,0,1)for dy in (-1,0,1)
                        for v in buckets[(key[0]+dx,key[1]+dy)]]
                if any(abs(cx-px)<480 and abs(y-py)<480 for px,py in nearby):
                    rejected+=1
                    continue
                box=pya.Box(cx-95,y-95,cx+95,y+95)
                centers[(cx,y)]=dict(net=name,original=list(net))
                buckets[key].append((cx,y));cuts.insert(box)
    assert all(len(v)==1 for v in groups.values())
    assert (metals['VDD'].sized(210)&metals['VSS']).is_empty()
    m2=metals['VDD']+metals['VSS'];m2.merge()
    assert (m2.sized(210)&before['10/0']).is_empty(), 'No contact or spacing conflict with retained M2'
    assert (cuts.sized(290)&before['19/0']).is_empty(), 'No conflict with retained Via1'
    # One exact union test avoids thousands of repeated whole-core booleans.
    assert (cuts.sized(50)-before['8/0']).is_empty()
    assert (cuts.sized(50)-m2).is_empty()
    for layer,addition in ((10,m2),(19,cuts)):
        for polygon in addition.each():
            top.shapes(ly.layer(layer,0)).insert(polygon)
    newnet,newlayers=physical(ly,top)
    mapping=collections.defaultdict(set);pin_errors=[]
    for probe in probes:
        m1=identity(newnet,newlayers[8],probe['point'])
        upper=identity(newnet,newlayers[10],probe['point'])
        if m1 is None or m1!=upper:
            pin_errors.append(dict(probe=probe,m1=m1,m2=upper))
        mapping[m1].add(tuple(probe['before']))
    # Row additions may only connect native portions already joined in M1.
    merges=[dict(after=k,before=sorted(v))for k,v in mapping.items()if len(v)>1]
    counts=collections.Counter(tuple(v['original'])for v in centers.values())
    insufficient=[dict(net=k,cuts=counts[k])for k in groups if counts[k]<2]
    assert not pin_errors and not merges and not insufficient,(pin_errors[:3],merges[:3],insufficient[:3])
    for info in ly.layer_infos():
        addition=m2 if info==pya.LayerInfo(10,0) else cuts if info==pya.LayerInfo(19,0) else pya.Region()
        assert (region(ly,top,info)^(before[str(info)]+addition)).is_empty()
    assert text_records(ly,top)==texts
    output=a.output/'decap_access_core.gds';ly.write(str(output))
    saved=pya.Layout();saved.read(str(output))
    assert text_records(saved,saved.top_cell())==texts
    for info in ly.layer_infos():
        assert (region(ly,top,info)^region(saved,saved.top_cell(),info)).is_empty()
    result=dict(status='passed scoped native decap row access',GDS_sha256=sha(output),
                parent_GDS_sha256=sha(source),placement_sha256=sha(a.placement/'analysis.json'),
                script_sha256=sha(Path(__file__)),KLayout=pya.__version__,
                decaps=4662,metal_backed_M1_M2_pin_pairs=len(probes),
                original_M1_components=len(groups),minimum_cuts_per_original_component=min(counts.values()),
                added_Via1_cuts=len(centers),spacing_rejected_requests=rejected,
                M2_area_um2=m2.area()*1e-6,Via1_area_um2=cuts.area()*1e-6,
                errors=pin_errors,distinct_original_net_merges=merges,
                unchanged_native_geometry_texts_and_saved_roundtrip='passed',
                not_run=['stock DRC in new context','row to ring feeds','power current distribution/IR/EM',
                         'fullchip LVS/PEX','electrical adoption'],not_applicable=['qualified connected chip from row access alone'])
    (a.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    faulthandler.cancel_dump_traceback_later()


if __name__=='__main__':
    main()
