#!/usr/bin/env python3
"""Save a frozen screened VDDA recipe and independently trace flattened domains."""
import argparse
import json
import os
from pathlib import Path
import sys
import pya

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from place_closed_analog import region,text_records,sha
from audit_placed_decap_domains import physical,identity
from build_interface import METALS,CUTS,box


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--native',type=Path,required=True)
    p.add_argument('--screen',type=Path,required=True)
    p.add_argument('--ladder',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert not a.output.exists()
    assert pya.__version__=='0.30.9'and len(os.sched_getaffinity(0))==1
    source=a.native/'power_connected_native.gds'
    screen=json.loads(a.screen.read_text());ladder=json.loads(a.ladder.read_text())
    assert sha(source)==screen['source_GDS_sha256']=='226c5aad876b9aea1ec2cd5874c828b2ae87ffb80a3efded7f8d9a2389cd8e05'
    selected=[r for r in screen['variants']if r['stack_x_um']==1048 and r['center_y_um']==401.5]
    assert len(selected)==1;recipe=selected[0]
    assert recipe['status'].startswith('passed')and not recipe['failures']
    assert recipe['collector_width_um']==10 and recipe['pad_feed_center_y_um']==392.04
    cases=[r for r in ladder['cases']if r['collector_width_um']==10 and r['chip_feed_center_y_um']==392.04]
    assert len(cases)==3 and all(r['baseline']['status'].startswith('passed')and not r['one_cut_failures']for r in cases)
    assert ladder['target_A']==.010 and ladder['linearity_control']=='passed'
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    result=dict(status='running',source_GDS_sha256=sha(source),screen_sha256=sha(a.screen),
        ladder_sha256=sha(a.ladder),script_sha256=sha(Path(__file__)),macro='shared_vdda',
        exploratory_aggregate_mA=10,current_scope='Conditional head ladder and via arithmetic only; full-pad distribution/current qualification not run')
    try:
        ly=pya.Layout();ly.read(str(source));top=ly.top_cell();assert ly.dbu==.001
        before={str(i):region(ly,top,i)for i in ly.layer_infos()};texts=text_records(ly,top)
        routes={}
        for label,polys in recipe['new_geometry_dbu'].items():
            layer=int(label);r=pya.Region()
            for row in polys:
                poly=pya.Polygon([pya.Point(*xy)for xy in row['hull']])
                for hole in row['holes']:poly.insert_hole([pya.Point(*xy)for xy in hole])
                r.insert(poly)
            routes[layer]=r.merged()
        assert set(routes)==set(METALS+tuple(CUTS))
        assert sum(routes[l].count()for l in CUTS)==148
        overlay=pya.Layout();overlay.dbu=.001;oc=overlay.create_cell('shared_vdda_power_interface_NOT_ADOPTED')
        for layer,r in routes.items():
            for poly in r.each():
                top.shapes(ly.layer(layer,0)).insert(poly)
                oc.shapes(overlay.layer(layer,0)).insert(poly)
        output=a.output/'candidate_native.gds';ly.write(str(output))
        ogds=a.output/'power_overlay.gds';overlay.write(str(ogds))
        saved=pya.Layout();saved.read(str(output));st=saved.top_cell()
        assert text_records(saved,st)==texts
        for i in saved.layer_infos():
            expected=before.get(str(i),pya.Region())
            if i.datatype==0 and i.layer in routes:expected=expected+routes[i.layer]
            assert(region(saved,st,i)^expected).is_empty(),str(i)
        # Repeated local cell names are not global physical identities. Flatten
        # only a disposable metal/cut verification view, never the saved native.
        flat=pya.Layout();flat.dbu=.001;ft=flat.create_cell('flat_physical_verification')
        for layer in METALS+tuple(CUTS):
            for poly in region(saved,st,pya.LayerInfo(layer,0)).each():
                ft.shapes(flat.layer(layer,0)).insert(poly)
        net,metals=physical(flat,ft)
        points={'pad07_bare':(30,[1093145,395000]),'pad07_external':(134,[1271500,395000]),
                'bgr_handoff':(134,[743400,922000]),'bgr_vdd_native':(67,[743400,878000]),
                'sense_vdd':(134,[813000,714000]),'sense_vss':(126,[805000,714000]),
                'core_vdd':(134,[395000,354660]),'core_vss':(134,[507000,334660])}
        probes={name:identity(net,metals[layer],xy)for name,(layer,xy)in points.items()}
        assert all(v is not None for v in probes.values())
        assert len({probes[n]for n in('pad07_bare','pad07_external','bgr_handoff','bgr_vdd_native','sense_vdd')})==1
        assert probes['sense_vss']==probes['core_vss']
        assert len({probes[n]for n in('sense_vdd','core_vdd','core_vss')})==3
        result.update(status='passed source-held shared VDDA geometry and flattened scoped domains',
            GDS_sha256=sha(output),overlay_sha256=sha(ogds),topcell=st.name,arrays=recipe['arrays'],
            probes=probes,source_polygon_text_preservation='passed exact additive saved XOR',
            geometry_recipe=recipe,not_run=['stock DRC','every-new-cut-open check','all native terminal no-merge',
                'final signal routing','native pad lower-stack/2D current distribution','all VDDA consumer branches',
                'full PVT/IR/EM/lifetime/current qualification','adoption'])
    except Exception as exc:
        result.update(status='failed shared VDDA geometry',error=repr(exc));raise
    finally:
        (a.output/'analysis.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
        print(json.dumps({k:v for k,v in result.items()if k not in('geometry_recipe','arrays')},indent=2))


if __name__=='__main__':main()
