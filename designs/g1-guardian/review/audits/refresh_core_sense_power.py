#!/usr/bin/env python3
"""Bind source-faithful SENSE power revision into the diagnostic placed core."""
import argparse
import collections
import json
import os
from pathlib import Path
import pya
from place_closed_analog import region, text_records, sha
from audit_placed_decap_domains import physical, identity


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--core',type=Path,required=True)
    p.add_argument('--placement',type=Path,required=True)
    p.add_argument('--sense',type=Path,required=True)
    p.add_argument('--sense-source-sha256',default='5d640799cb0a4257d34e82a1018237a6bfa0d595bc0d6520522d40125322c170')
    p.add_argument('--sense-namespace-sha256',default='9ea581e6d0af129cafce646127922410e8eae9b6ba84c3542d108123638eadc8')
    p.add_argument('--bgr',type=Path)
    p.add_argument('--bgr-source-sha256')
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0))==1 and pya.__version__=='0.30.9'
    a.output.mkdir(parents=True)
    (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    parent=json.loads((a.core/'analysis.json').read_text())
    metadata=json.loads((a.sense/'analysis.json').read_text())
    source=a.core/'decap_access_core.gds';sense=a.sense/'g1_sense.gds'
    assert sha(source)==parent['GDS_sha256']=='ad15826889e747908ec03cddf0eb2d3ba6931c816352a5366c5d402e430af5d3'
    assert sha(sense)==metadata['abstract_GDS_sha256']==a.sense_namespace_sha256
    assert metadata['GDS_sha256']==a.sense_source_sha256
    decaps=json.loads((a.placement/'analysis.json').read_text())['decaps']
    old=pya.Layout();old.read(str(source));ot=old.top_cell()
    sl=pya.Layout();sl.read(str(sense));st=sl.cell('g1_sense')
    bgrmeta=None;bt=None;bl=None
    if a.bgr:
        bgrmeta=json.loads((a.bgr/'analysis.json').read_text())
        assert a.bgr_source_sha256 and bgrmeta['GDS_sha256']==a.bgr_source_sha256
        assert sha(a.bgr/'g1_bgr.gds')==bgrmeta['abstract_GDS_sha256']
        bl=pya.Layout();bl.read(str(a.bgr/'g1_bgr.gds'));bt=bl.cell('g1_bgr')
        assert bt is not None and bl.dbu==.001
    new=pya.Layout();new.dbu=old.dbu;nt=new.create_cell(ot.name)
    assert old.dbu==sl.dbu==new.dbu==.001
    # Every direct top-level route, row access, cut and text is retained.
    for info in old.layer_infos():
        for shape in ot.shapes(old.layer(info)).each():
            nt.shapes(new.layer(info)).insert(shape)
    cache={};copies=[];replaced=[];bgr_replaced=[];instances=0
    for instance in ot.each_inst():
        previous=instance.cell
        kind=('sense'if previous.name=='g1_sense_candidate'else
              'bgr'if bt is not None and previous.name=='g1_bgr_candidate'else None)
        replace=kind is not None
        selected=st if kind=='sense'else bt if kind=='bgr'else previous
        owner=sl if kind=='sense'else bl if kind=='bgr'else old
        key=(kind,selected.cell_index())
        if key not in cache:
            cell=new.create_cell(previous.name);cell.copy_tree(selected)
            assert text_records(owner,selected)==text_records(new,cell)
            for info in owner.layer_infos():
                assert (region(owner,selected,info)^region(new,cell,info)).is_empty()
            cache[key]=cell
            copies.append(dict(name=previous.name,replacement=replace,source_cell=selected.name,
                               polygons_texts='passed'))
        assert not instance.is_regular_array()
        nt.insert(pya.CellInstArray(cache[key].cell_index(),instance.cplx_trans))
        instances+=1
        if kind=='sense':
            assert str(instance.trans)=='r90 1031000,331000'
            replaced.append(instance.trans)
        if kind=='bgr':
            assert str(instance.trans)=='r0 331000,732000'
            bgr_replaced.append(instance.trans)
    assert instances==4674 and len(replaced)==1
    assert len(bgr_replaced)==(1 if bt is not None else 0)
    # Preserve an explicitly unqualified debug view even if connectivity fails.
    debug=a.output/'unqualified_debug.gds';new.write(str(debug))
    direct=[]
    for info in old.layer_infos():
        xor=pya.Region(ot.shapes(old.layer(info)))^pya.Region(nt.shapes(new.layer(info)))
        assert xor.is_empty(),str(info)
        direct.append(str(info))
    net,layers=physical(new,nt)
    groups=collections.defaultdict(set)
    for row in decaps:
        for name,pin in row['pins'].items():
            lo=identity(net,layers[8],pin['placed_dbu'])
            hi=identity(net,layers[10],pin['placed_dbu'])
            assert lo is not None and lo==hi
            groups[lo].add(name)
    assert len(groups)==464 and all(len(names)==1 for names in groups.values())
    ring={name:identity(net,layers[134],xy)for name,xy in [('VDD',[395000,354660]),('VSS',[507000,334660])]}
    (a.output/'ring_diagnostic.json').write_text(json.dumps(dict(ring=ring,direct_top_layers_unchanged=direct,
        debug_GDS_sha256=sha(debug),status='diagnostic only; acceptance pending'),indent=2)+'\n')
    assert None not in ring.values() and ring['VDD']!=ring['VSS']
    ports={};transform=replaced[0]
    for name,port in metadata['pins'].items():
        point=transform*pya.Point(*port['label_dbu'])
        found=identity(net,layers[port['layer']],[point.x,point.y])
        assert found is not None and found not in groups and found not in ring.values()
        ports[name]=dict(layer=port['layer'],point_dbu=[point.x,point.y],physical_net=list(found))
    assert len({tuple(p['physical_net'])for p in ports.values()})==9
    bgrports={}
    if bgrmeta:
        forbidden=set(groups)|set(ring.values())|{tuple(p['physical_net'])for p in ports.values()}
        for name,port in bgrmeta['pins'].items():
            point=bgr_replaced[0]*pya.Point(*port['label_dbu'])
            found=identity(net,layers[port['layer']],[point.x,point.y])
            assert found is not None and found not in forbidden
            bgrports[name]=dict(layer=port['layer'],point_dbu=[point.x,point.y],physical_net=list(found))
        assert len(bgrports)==9 and len({tuple(p['physical_net'])for p in bgrports.values()})==9
    output=a.output/'refreshed_core.gds';new.write(str(output))
    saved=pya.Layout();saved.read(str(output))
    assert len(saved.top_cells())==1 and text_records(saved,saved.top_cell())==text_records(new,nt)
    for info in new.layer_infos():
        assert (region(new,nt,info)^region(saved,saved.top_cell(),info)).is_empty()
    result=dict(status='passed scoped source-faithful SENSE power placement refresh',GDS_sha256=sha(output),
                parent_GDS_sha256=sha(source),SENSE_source_GDS_sha256=metadata['GDS_sha256'],
                SENSE_namespaced_GDS_sha256=sha(sense),script_sha256=sha(Path(__file__)),
                instance_count=instances,copied_native_cells=copies,SENSE_chip_ports=ports,
                BGR_source_GDS_sha256=bgrmeta['GDS_sha256']if bgrmeta else None,
                BGR_namespaced_GDS_sha256=bgrmeta['abstract_GDS_sha256']if bgrmeta else None,
                BGR_chip_ports=bgrports,
                retained_decap_M1_M2_pairs=9324,retained_decap_components=464,
                supply_rings_distinct='passed',SENSE_external_nets_distinct_from_rings_decaps='passed',
                native_geometry_texts_and_saved_roundtrip='passed',
                not_run=['refreshed fullcore DRC','all macro inter-net proof','row/macro supply feeds and signal routes',
                         'fullchip LVS/PEX/currentIR/EM','density/antenna','electrical adoption'])
    (a.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
