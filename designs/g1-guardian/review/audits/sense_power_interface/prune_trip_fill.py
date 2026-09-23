#!/usr/bin/env python3
"""Exact ledger-driven fill-array pruning; no functional hierarchy replacement."""
import json
import pya
from build_ls_interface import region,text_records


def describe(inst):
    child=inst.cell
    assert '_FILL_CELL'in child.name and not list(child.each_inst())and inst.prop_id==0
    ly=child.layout();shapes=[(info,s)for info in ly.layer_infos()for s in child.shapes(ly.layer(info)).each()]
    assert len(shapes)==1
    info,shape=shapes[0];assert info.datatype==22 and info.layer in(10,30,50)and not shape.is_text()
    poly=shape.polygon
    return dict(child_cell=child.name,transform=str(inst.cplx_trans),na=inst.na,nb=inst.nb,
                a=[inst.a.x,inst.a.y],b=[inst.b.x,inst.b.y],property_id=inst.prop_id,
                layer=info.layer,datatype=22,child_hull_dbu=[[p.x,p.y]for p in poly.each_point_hull()],
                child_holes_dbu=[[[p.x,p.y]for p in poly.each_point_hole(i)]for i in range(poly.holes())])


def compatible(actual,expected):
    # Retained source cells may have a namespace prefix/suffix. Shape, layer,
    # array lattice and transform remain exact; ambiguous matches are rejected.
    return expected['child_cell']in actual['child_cell']and all(actual[k]==v for k,v in expected.items()if k!='child_cell')


def prune_from_ledger(layout,top,ledger,bound_source_sha256=None):
    expected=bound_source_sha256 or 'c99f3ae11b4501610939aa09b4581535a42d257f76951a25b4c84dd72a3afb90'
    assert layout.dbu==.001 and ledger['source_GDS_sha256']==expected
    assert ledger['spacing_um']==.42
    before={str(info):region(layout,top,info)for info in layout.layer_infos()}
    texts=text_records(layout,top)
    functional=sorted((c.name,i.cell.name,str(i.cell_inst),i.prop_id)for c in layout.each_cell()
                      for i in c.each_inst()if '_FILL_CELL'not in i.cell.name)
    groups={}
    for row in ledger['rows']:
        assert row['parent_cell']=='g1_trip'and row['datatype']==22 and row['layer']in(10,30,50)
        key=json.dumps(row['array_descriptor'],sort_keys=True)
        groups.setdefault(key,[]).append(row)
    removed={l:pya.Region()for l in(10,30,50)};proof=[]
    for key,rows in groups.items():
        expected=json.loads(key);matches=[]
        for inst in top.each_inst():
            if '_FILL_CELL'not in inst.cell.name:continue
            if expected['child_cell']not in inst.cell.name:continue
            actual=describe(inst)
            if compatible(actual,expected):matches.append(inst)
        assert len(matches)==1,(expected,len(matches))
        inst=matches[0];child=inst.cell;layer=expected['layer'];cia=inst.cell_inst
        shape=next(child.shapes(layout.layer(layer,22)).each());polygon=shape.polygon
        wanted={r['repetition_transform']:r for r in rows};assert len(wanted)==len(rows)
        keep=[];found=[]
        for trans in cia.each_cplx_trans():
            key_=str(trans)
            if key_ not in wanted:keep.append(trans);continue
            poly=polygon.transformed(trans);row=wanted[key_]
            assert [[p.x,p.y]for p in poly.each_point_hull()]==row['local_polygon_hull_dbu']
            assert [[[p.x,p.y]for p in poly.each_point_hole(i)]for i in range(poly.holes())]==row['local_polygon_holes_dbu']
            removed[layer].insert(poly);found.append(key_)
        assert set(found)==set(wanted)
        child_index=child.cell_index();inst.delete()
        for trans in keep:top.insert(pya.CellInstArray(child_index,trans))
        proof.append(dict(original_array=expected,removed_repetitions=len(found),retained_repetitions=len(keep)))
    assert text_records(layout,top)==texts
    assert functional==sorted((c.name,i.cell.name,str(i.cell_inst),i.prop_id)for c in layout.each_cell()
                             for i in c.each_inst()if '_FILL_CELL'not in i.cell.name)
    for info in layout.layer_infos():
        expected=before[str(info)]
        if info.datatype==22 and info.layer in removed:
            assert(removed[info.layer]-expected).is_empty();expected-=removed[info.layer]
        assert(region(layout,top,info)^expected).is_empty(),str(info)
    for layer,r in removed.items():
        record=ledger['per_layer'][str(layer)]
        assert r.count()==record['polygons']and abs(r.area()*1e-6-record['area_um2'])<1e-10
    return dict(status='passed exact scoped fill-array pruning',changed_arrays=proof,
                functional_instances_and_all_non22_texts='passed exact preservation',
                original_minus_declared_fill_polygon_XOR='passed',removed_per_layer=ledger['per_layer'])
