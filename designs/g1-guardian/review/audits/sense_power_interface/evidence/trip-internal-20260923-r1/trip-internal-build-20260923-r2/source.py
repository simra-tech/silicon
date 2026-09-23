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
    a=p.parse_args();assert not a.output.exists()and len(os.sched_getaffinity(0))==1 and pya.__version__=='0.30.9'
    meta=json.loads((a.screen/'analysis.json').read_text())
    assert meta['status']=='passed native-only source-held internal access screen'
    assert sha(a.gds)==meta['GDS_sha256']=='c99f3ae11b4501610939aa09b4581535a42d257f76951a25b4c84dd72a3afb90'
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
    try:
        ly=pya.Layout();ly.read(str(a.gds));top=ly.cell('g1_trip')
        old={str(i):region(ly,top,i)for i in ly.layer_infos()};texts=text_records(ly,top)
        flat,bn,bm=flat_physical(ly,top)
        circuits=list(bn.netlist().each_circuit());assert len(circuits)==1
        before_count=sum(1 for n in circuits[0].each_net())
        added={l:pya.Region()for l in METALS+tuple(CUTS)}
        overlay=pya.Layout();overlay.dbu=.001;ot=overlay.create_cell('trip_internal_access_NOT_ADOPTED')
        for net,layers in recipe.items():
            for layer,polys in layers.items():
                layer=int(layer)
                for data in polys:
                    poly=pya.Polygon([pya.Point(*v)for v in data['hull']])
                    for hole in data['holes']:poly.insert_hole([pya.Point(*v)for v in hole])
                    added[layer].insert(poly);top.shapes(ly.layer(layer,0)).insert(poly)
                    ot.shapes(overlay.layer(layer,0)).insert(poly)
        out=a.output/'g1_trip.gds';ly.write(str(out));overlay.write(str(a.output/'internal_overlay_local.gds'))
        saved=pya.Layout();saved.read(str(out));st=saved.cell('g1_trip');assert text_records(saved,st)==texts
        for info in saved.layer_infos():
            expected=old.get(str(info),pya.Region())
            if info.datatype==0 and info.layer in added:expected+=added[info.layer]
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
                      primitive_nonmetal_and_all_native_texts_unchanged=True,exact_saved_additive_geometry='passed',
                      source_reference_unchanged=sha(a.output/'g1_trip_lvs.cdl')==sha(a.reference))
    except Exception as exc:
        result.update(status='failed TRIP internal access construction',error=repr(exc));raise
    finally:
        (a.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({k:v for k,v in result.items()if k not in('source_access','arrays')},indent=2))


if __name__=='__main__':main()
