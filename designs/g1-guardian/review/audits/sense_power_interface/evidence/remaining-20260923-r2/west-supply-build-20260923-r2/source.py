#!/usr/bin/env python3
"""Build only an accepted frozen supply recipe, preserving its native core parent."""
import argparse
import json
import os
from pathlib import Path
import pya
from build_ls_interface import flat_physical, region, text_records, sha, METALS, CUTS, identity


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in('screen','parent','ls','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();assert not a.output.exists()and len(os.sched_getaffinity(0))==1 and pya.__version__=='0.30.9'
    screen=json.loads((a.screen/'analysis.json').read_text());assert screen['status']=='passed proposed geometry screen'
    assert screen['mode']=='west'
    assert sha(a.parent/'power_connected_native.gds')==screen['source_GDS_sha256']
    assert sha(a.ls/'power_overlay.gds')==screen['LS_overlay_sha256']
    source=a.ls/'candidate_core.gds';meta=json.loads((a.ls/'analysis.json').read_text())
    assert sha(source)==meta['GDS_sha256']=='d2d401965f876042d8b4a1e5622e3996233065a984b78295ad22ea18b2c84ea6'
    assert sha(a.screen/'recipe.json')==screen['recipe_sha256']
    recipe=json.loads((a.screen/'recipe.json').read_text())
    assert all(not polys for n,layers in recipe.items()if n!='VDDA'for polys in layers.values())
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    (a.output/'screen.json').write_bytes((a.screen/'analysis.json').read_bytes())
    (a.output/'recipe.json').write_bytes((a.screen/'recipe.json').read_bytes())
    result=dict(status='running',macro='west_vdda',source_GDS_sha256=sha(source),
                actual_fullnative_screen_sha256=sha(a.screen/'analysis.json'),
                actual_fullnative_context_GDS_sha256=screen['source_GDS_sha256'],
                script_sha256=sha(Path(__file__)),arrays=screen['arrays'],
                exploratory_targets_mA=screen['exploratory_targets_mA'],
                not_run=['actual full-native saved merge and pad join','stock/cut-open/final signal context',
                         'fullchip source LVS/PEX/current distribution/PVT/IR/EM','adoption'])
    try:
        ly=pya.Layout();ly.read(str(source));top=ly.top_cell()
        old={str(i):region(ly,top,i)for i in ly.layer_infos()};texts=text_records(ly,top)
        flat,bn,bm=flat_physical(ly,top)
        before={n:identity(bn,bm[l],pt)for n,l,pt in
                [('LS',30,[783000,501400]),('GATE',30,[734000,600000]),
                 ('VDD',134,[395000,354660]),('VSS',134,[507000,334660])]}
        assert None not in before.values()and len(set(before.values()))==4
        overlay=pya.Layout();overlay.dbu=.001;oc=overlay.create_cell('west_vdda_power_interface_NOT_ADOPTED')
        added={l:pya.Region()for l in METALS+tuple(CUTS)}
        for layers in recipe.values():
            for layer,polys in layers.items():
                layer=int(layer)
                for data in polys:
                    poly=pya.Polygon([pya.Point(*v)for v in data['hull']])
                    for hole in data['holes']:poly.insert_hole([pya.Point(*v)for v in hole])
                    added[layer].insert(poly);top.shapes(ly.layer(layer,0)).insert(poly)
                    oc.shapes(overlay.layer(layer,0)).insert(poly)
        out=a.output/'candidate_core.gds';ly.write(str(out));overlay.write(str(a.output/'power_overlay.gds'))
        saved=pya.Layout();saved.read(str(out));st=saved.top_cell();assert text_records(saved,st)==texts
        for info in saved.layer_infos():
            expected=old.get(str(info),pya.Region())
            if info.datatype==0 and info.layer in added:expected+=added[info.layer]
            assert(region(saved,st,info)^expected).is_empty(),str(info)
        flat,an,am=flat_physical(saved,st)
        after={n:identity(an,am[l],pt)for n,l,pt in
               [('LS',30,[783000,501400]),('GATE',30,[734000,600000]),('handoff',134,[1060000,726000]),
                ('VDD',134,[395000,354660]),('VSS',134,[507000,334660])]}
        assert None not in after.values()and after['LS']==after['GATE']==after['handoff']
        assert len({after['LS'],after['VDD'],after['VSS']})==3
        result.update(status='passed source-held west VDDA overlay and saved flat graph',GDS_sha256=sha(out),
                      overlay_sha256=sha(a.output/'power_overlay.gds'),flat_before=before,flat_after=after,
                      native_additive_polygon_text_roundtrip='passed')
    except Exception as exc:
        result.update(status='failed west VDDA build',error=repr(exc));raise
    finally:
        (a.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({k:v for k,v in result.items()if k!='arrays'},indent=2))


if __name__=='__main__':main()
