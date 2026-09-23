#!/usr/bin/env python3
"""Export conservative top-level conductor blockages for isolated signal routing.

Macro interiors use their native-bound LEFs. This adds the chip rings and new
decap row-access metal which are absent from standard-cell LEFs. It neither
draws power feeds nor claims PDN connectivity/current qualification.
"""
import argparse
import json
import os
from pathlib import Path
import pya
from place_closed_analog import sha,region

LAYERS={8:'Metal1',10:'Metal2',30:'Metal3',50:'Metal4',67:'Metal5',126:'TopMetal1',134:'TopMetal2'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--core',type=Path,required=True)
    p.add_argument('--core-gds-name',default='refreshed_core.gds')
    p.add_argument('--power-overlay',type=Path,action='append',default=[])
    p.add_argument('--m5-halo-dbu',type=int,choices=[0,20,40],default=0,
                   help='Optional conservative M5 obstacle reservation; no source geometry change')
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    assert not a.output.exists() and pya.__version__=='0.30.9' and len(os.sched_getaffinity(0))==1
    meta=json.loads((a.core/'analysis.json').read_text())
    assert Path(a.core_gds_name).name==a.core_gds_name
    source=a.core/a.core_gds_name
    assert meta['status'].startswith('passed') and sha(source)==meta['GDS_sha256']
    ly=pya.Layout();ly.read(str(source));top=ly.top_cell()
    assert ly.dbu==.001
    overlays=[]
    for folder in a.power_overlay:
        metadata=json.loads((folder/'analysis.json').read_text())
        gds=folder/'power_overlay.gds'
        assert metadata['status'].startswith('passed') and sha(gds)==metadata['overlay_sha256']
        ol=pya.Layout();ol.read(str(gds));assert ol.dbu==.001
        overlays.append((ol,ol.top_cell(),gds,metadata))
    rows=[];coverage=[]
    for number,name in LAYERS.items():
        native=pya.Region(top.shapes(ly.layer(number,0))).merged()
        for ol,ot,gds,metadata in overlays:
            native+=region(ol,ot,pya.LayerInfo(number,0))
        native.merge()
        reserved=native.sized(a.m5_halo_dbu) if number==67 and a.m5_halo_dbu else native
        assert (native-reserved).is_empty()
        conservative=pya.Region()
        # Orthogonal PDN rings/feeders must not become a whole-core bbox.
        # Exact decomposition is audited before exporting rectangles.
        pieces=reserved.decompose_trapezoids_to_region()
        assert (pieces^reserved).is_empty()
        for polygon in pieces.each():
            box=polygon.bbox();conservative.insert(box)
            assert polygon.area()==box.area(), 'Nonrectangular decomposition requires explicit routing policy'
            rows.append(dict(layer=name,bbox_dbu=[box.left,box.bottom,box.right,box.top]))
        assert (reserved^conservative).is_empty()
        coverage.append(dict(layer=name,native_area_um2=native.area()*1e-6,
                             conservative_area_um2=conservative.merged().area()*1e-6,
                             spacing_reservation_dbu=a.m5_halo_dbu if number==67 else 0,
                             no_conductor_omitted='passed',rectangles=conservative.count()))
    assert rows and {'Metal2','TopMetal1','TopMetal2'}<={r['layer']for r in rows}<=set(LAYERS.values())
    a.output.mkdir(parents=True)
    (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    lines=['# Conservative native chip-ring and decap-access obstacles.',
           'set core_obs_block [ord::get_db_block]',
           'set core_obs_tech [ord::get_db_tech]']
    for row in rows:
        lines.append('odb::dbObstruction_create $core_obs_block [$core_obs_tech findLayer '+row['layer']+'] '+' '.join(map(str,row['bbox_dbu'])))
    script=a.output/'core_obstacles.tcl';script.write_text('\n'.join(lines)+'\n')
    result=dict(status='passed conservative native top-conductor obstacle export',GDS_sha256=sha(source),
                M5_clearance_halo_dbu=a.m5_halo_dbu,
                routing_policy='Exact native/overlay rectangles plus optional M5 reservation.20nm retained230nm stock M5.e failures;40nm tests additional routing clearance. No rule or source geometry changes',
                power_overlays=[dict(path=str(gds),sha256=sha(gds),metadata_sha256=sha(gds.parent/'analysis.json'))
                                for ol,ot,gds,metadata in overlays],
                script_sha256=sha(Path(__file__)),Tcl_sha256=sha(script),obstacles=rows,layer_coverage=coverage,
                not_run=['OpenDB import and rectangle roundtrip','signal global/detailed routing',
                         'PDN feeds and connections','stock wholechip checks','electrical adoption'])
    (a.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items()if k!='obstacles'},indent=2))


if __name__=='__main__':
    main()
