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
from place_closed_analog import sha

LAYERS={8:'Metal1',10:'Metal2',30:'Metal3',50:'Metal4',67:'Metal5',126:'TopMetal1',134:'TopMetal2'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--core',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    assert not a.output.exists() and pya.__version__=='0.30.9' and len(os.sched_getaffinity(0))==1
    meta=json.loads((a.core/'analysis.json').read_text())
    source=a.core/'refreshed_core.gds'
    assert meta['status'].startswith('passed') and sha(source)==meta['GDS_sha256']
    ly=pya.Layout();ly.read(str(source));top=ly.top_cell()
    assert ly.dbu==.001
    rows=[];coverage=[]
    for number,name in LAYERS.items():
        native=pya.Region(top.shapes(ly.layer(number,0))).merged()
        conservative=pya.Region()
        for polygon in native.each():
            box=polygon.bbox();conservative.insert(box)
            rows.append(dict(layer=name,bbox_dbu=[box.left,box.bottom,box.right,box.top]))
        assert (native-conservative).is_empty()
        coverage.append(dict(layer=name,native_area_um2=native.area()*1e-6,
                             conservative_area_um2=conservative.merged().area()*1e-6,
                             no_conductor_omitted='passed',rectangles=conservative.count()))
    assert rows and {r['layer']for r in rows}=={'Metal2','TopMetal1','TopMetal2'}
    a.output.mkdir(parents=True)
    (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    lines=['# Conservative native chip-ring and decap-access obstacles.',
           'set core_obs_block [ord::get_db_block]',
           'set core_obs_tech [ord::get_db_tech]']
    for row in rows:
        lines.append('odb::dbObstruction_create $core_obs_block [$core_obs_tech findLayer '+row['layer']+'] '+' '.join(map(str,row['bbox_dbu'])))
    script=a.output/'core_obstacles.tcl';script.write_text('\n'.join(lines)+'\n')
    result=dict(status='passed conservative native top-conductor obstacle export',GDS_sha256=sha(source),
                script_sha256=sha(Path(__file__)),Tcl_sha256=sha(script),obstacles=rows,layer_coverage=coverage,
                not_run=['OpenDB import and rectangle roundtrip','signal global/detailed routing',
                         'PDN feeds and connections','stock wholechip checks','electrical adoption'])
    (a.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items()if k!='obstacles'},indent=2))


if __name__=='__main__':
    main()
