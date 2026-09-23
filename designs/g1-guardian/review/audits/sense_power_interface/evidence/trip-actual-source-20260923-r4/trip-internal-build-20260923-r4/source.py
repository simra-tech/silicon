#!/usr/bin/env python3
"""Save a passed source-held DAC access recipe, without changing native devices."""
import argparse
import json
import os
from pathlib import Path
import pya
from build_ls_interface import flat_physical, region, text_records, sha, METALS, CUTS, identity


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in('screen','gds','reference','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--remove-conflicting-fill',action='store_true')
    p.add_argument('--source-binding',type=Path)
    a=p.parse_args();assert not a.output.exists()and len(os.sched_getaffinity(0))==1 and pya.__version__=='0.30.9'
    meta=json.loads((a.screen/'analysis.json').read_text())
    assert meta['status']=='passed native-only source-held internal access screen'
    canonical='c99f3ae11b4501610939aa09b4581535a42d257f76951a25b4c84dd72a3afb90'
    assert meta['GDS_sha256']==canonical
    binding=None
    if a.source_binding:
        binding=json.loads(a.source_binding.read_text())
        assert binding['status']=='passed actual parent-native source view'
        assert sha(a.gds)==binding['GDS_sha256']
        assert binding['canonical_functional_source_GDS_sha256']==canonical
        assert binding['canonical_non22_and_lower_fill_exact'] is True
    else:assert sha(a.gds)==canonical
    assert sha(a.reference)=='60a9ad6e3744ff0b3dcd407a78febcb49315840a65fdf8ef851032d6e88bfd76'
    assert sha(a.screen/'recipe.json')==meta['recipe_sha256']
    recipe=json.loads((a.screen/'recipe.json').read_text())
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    (a.output/'recipe.json').write_bytes((a.screen/'recipe.json').read_bytes())
    (a.output/'g1_trip_lvs.cdl').write_bytes(a.reference.read_bytes())
    result=dict(status='running',source_GDS_sha256=sha(a.gds),source_reference_sha256=sha(a.reference),
                screen_sha256=sha(a.screen/'analysis.json'),script_sha256=sha(Path(__file__)),
                source_access=meta['source_access'],arrays=meta['arrays'],new_cut_count=meta['new_cut_count'],
                not_run=['stock main/maximal/strict source LVS','full-native placement/PDN/final signal context',
                         'comparator VDD and VSS access remedy','per-device contact-current allocation/IR/EM/PVT','adoption'])
    if binding:result.update(actual_native_source_binding=binding,source_binding_sha256=sha(a.source_binding))
    try:
        ly=pya.Layout();ly.read(str(a.gds));top=ly.cell('g1_trip')
        old={str(i):region(ly,top,i)for i in ly.layer_infos()};texts=text_records(ly,top)
        flat,bn,bm=flat_physical(ly,top)
        circuits=list(bn.netlist().each_circuit());assert len(circuits)==1
        before_count=sum(1 for n in circuits[0].each_net())
        added={l:pya.Region()for l in METALS+tuple(CUTS)}
        removed={l:pya.Region()for l in(10,30,50)};removal_rows=[]
        functional_before=sorted((c.name,i.cell.name,str(i.cell_inst),i.prop_id)for c in ly.each_cell()
                                 for i in c.each_inst()if '_FILL_CELL'not in i.cell.name)
        overlay=pya.Layout();overlay.dbu=.001;ot=overlay.create_cell('trip_internal_access_NOT_ADOPTED')
        for net,layers in recipe.items():
            for layer,polys in layers.items():
                layer=int(layer)
                for data in polys:
                    poly=pya.Polygon([pya.Point(*v)for v in data['hull']])
                    for hole in data['holes']:poly.insert_hole([pya.Point(*v)for v in hole])
                    added[layer].insert(poly);top.shapes(ly.layer(layer,0)).insert(poly)
                    ot.shapes(overlay.layer(layer,0)).insert(poly)
        if a.remove_conflicting_fill:
            card=Path('/foss/pdks/ihp-sg13g2/libs.tech/klayout/tech/drc/rule_decks/sg13g2_tech_default.json')
            def walk(value):
                if isinstance(value,dict):
                    if 'MFil_c'in value:yield value['MFil_c']
                    for item in value.values():yield from walk(item)
                elif isinstance(value,list):
                    for item in value:yield from walk(item)
            assert list(walk(json.loads(card.read_text())))==[.42]
            expected_removal={l:region(ly,top,pya.LayerInfo(l,22)).interacting(added[l].sized(420))for l in removed}
            for inst in list(top.each_inst()):
                child=inst.cell
                if not any(name in child.name for name in tuple('Met%d_%s_FILL_CELL'%(m,size)for m in(2,3,4)for size in('M','S'))):continue
                assert inst.prop_id==0 and not list(child.each_inst())
                shapes=[(info,s.polygon)for info in ly.layer_infos()for s in child.shapes(ly.layer(info)).each()]
                assert len(shapes)==1
                info,polygon=shapes[0];assert info.datatype==22 and info.layer in removed
                cia=inst.cell_inst;keep=[];cut=[]
                for trans in cia.each_cplx_trans():
                    moved=polygon.transformed(trans)
                    if not(pya.Region(moved)&added[info.layer].sized(420)).is_empty():
                        removed[info.layer].insert(moved);cut.append(trans)
                        removal_rows.append(dict(parent_cell=top.name,child_cell=child.name,original_array=str(cia),
                            repetition_transform=str(trans),layer=info.layer,datatype=22,
                            child_polygon_hull_dbu=[[v.x,v.y]for v in polygon.each_point_hull()],
                            local_polygon_hull_dbu=[[v.x,v.y]for v in moved.each_point_hull()],
                            local_polygon_holes_dbu=[[[v.x,v.y]for v in moved.each_point_hole(i)]for i in range(moved.holes())]))
                    else:keep.append(trans)
                if cut:
                    child_index=child.cell_index();inst.delete()
                    for trans in keep:top.insert(pya.CellInstArray(child_index,trans))
            for layer in removed:
                # Pure boundary touches need not be removed; every actual
                # positive-area intersection with the .42um halo is removed.
                actual_original=old.get(str(pya.LayerInfo(layer,22)),pya.Region())
                assert(removed[layer]-actual_original).is_empty()
                assert(removed[layer]-expected_removal[layer]).is_empty()
                remaining=region(ly,top,pya.LayerInfo(layer,22))
                assert(actual_original-remaining-removed[layer]).is_empty()
                assert(remaining-(actual_original-removed[layer])).is_empty()
                assert(remaining&added[layer].sized(420)).is_empty()
            removal_layout=pya.Layout();removal_layout.dbu=.001;rc=removal_layout.create_cell('trip_fill_removal_local_NOT_ADOPTED')
            for layer,r in removed.items():
                for poly in r.each():rc.shapes(removal_layout.layer(layer,22)).insert(poly)
            removal_layout.write(str(a.output/'fill_removal_local.gds'))
            ledger=dict(source_GDS_sha256=sha(a.gds),spacing_card_sha256=sha(card),spacing_um=.42,
                        selection='Original M2/M3/M4 datatype22 polygons intersecting positive area of new-metal .42um sized halo',
                        rows=removal_rows,per_layer={str(l):dict(polygons=r.count(),area_um2=r.area()*1e-6)for l,r in removed.items()})
            (a.output/'fill_removal.json').write_text(json.dumps(ledger,indent=2)+'\n')
            result.update(fill_removal_sha256=sha(a.output/'fill_removal_local.gds'),fill_removal_ledger_sha256=sha(a.output/'fill_removal.json'),
                          fill_removal=ledger['per_layer'],fill_scope='Only affected fill repetitions removed/split; all functional instances and child definitions held')
        functional_after=sorted((c.name,i.cell.name,str(i.cell_inst),i.prop_id)for c in ly.each_cell()
                                for i in c.each_inst()if '_FILL_CELL'not in i.cell.name)
        assert functional_after==functional_before
        out=a.output/'g1_trip.gds';ly.write(str(out));overlay.write(str(a.output/'internal_overlay_local.gds'))
        saved=pya.Layout();saved.read(str(out));st=saved.cell('g1_trip');assert text_records(saved,st)==texts
        for info in saved.layer_infos():
            expected=old.get(str(info),pya.Region())
            if info.datatype==0 and info.layer in added:expected+=added[info.layer]
            if info.datatype==22 and info.layer in removed:expected-=removed[info.layer]
            assert(region(saved,st,info)^expected).is_empty(),str(info)
        flat,an,am=flat_physical(saved,st)
        circuits=list(an.netlist().each_circuit());assert len(circuits)==1
        after_count=sum(1 for n in circuits[0].each_net());assert after_count==before_count
        roots={n:identity(an,am[30],[21000,int(y*1000)])for n,y in [('VDD',206),('VDDA',202.75),('VSS',1)]}
        assert None not in roots.values()and len(set(roots.values()))==3
        probes=[]
        for row in meta['source_access']:
            point=row.get('M1_source_probe_um',row.get('native_M1_rail_probe_um'))
            found=identity(an,am[8],[round(v*1000)for v in point]);assert found==roots[row['net']]
            probes.append(dict(**row,flat_identity=found))
        result.update(status='passed source-held native TRIP internal DAC access construction',GDS_sha256=sha(out),
                      overlay_sha256=sha(a.output/'internal_overlay_local.gds'),source_access=probes,
                      flat_metal_net_count_before=before_count,flat_metal_net_count_after=after_count,
                      primitive_nonmetal_and_all_native_texts_unchanged=True,functional_instance_hierarchy_unchanged=True,
                      exact_saved_additive_geometry='passed with exact scoped datatype22 removal'if a.remove_conflicting_fill else'passed',
                      source_reference_unchanged=sha(a.output/'g1_trip_lvs.cdl')==sha(a.reference))
    except Exception as exc:
        result.update(status='failed TRIP internal access construction',error=repr(exc));raise
    finally:
        (a.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({k:v for k,v in result.items()if k not in('source_access','arrays')},indent=2))


if __name__=='__main__':main()
