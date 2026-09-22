#!/usr/bin/env python3
"""Screen frozen power overlay against exact separately exported signal routes."""
import argparse
import json
import os
from pathlib import Path
import sys
import pya

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from place_closed_analog import region,sha


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--power',type=Path,required=True)
    p.add_argument('--signals',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert not a.output.exists() and pya.__version__=='0.30.9' and len(os.sched_getaffinity(0))==1
    pm=json.loads((a.power/'analysis.json').read_text());sm=json.loads((a.signals/'analysis.json').read_text())
    power=a.power/'power_overlay.gds';signals=a.signals/'signal_routes_only.gds'
    assert pm['status'].startswith('passed') and sm['status'].startswith('passed')
    assert sha(power)==pm['overlay_sha256']=='a16aa0d622329a4d5de51b658a3d57f0e7cf1d1be1cdd4228dfead0856f56ca0'
    assert sha(signals)==sm['route_only_GDS_sha256']=='03473e0dd19b9d69be9faa5e7b9edb4254c7aabab354b8899d18b0bba586703b'
    assert pm['source_GDS_sha256']==sm['native_GDS_sha256']=='8b66a958759478987fa9de59746a0554f9bd065307e730342f10e891082134e6'
    pl=pya.Layout();pl.read(str(power));sl=pya.Layout();sl.read(str(signals))
    pt,st=pl.top_cell(),sl.top_cell();assert pl.dbu==sl.dbu==.001
    rows=[]
    for layer,gap in ((8,.4),(10,.4),(30,.4),(50,.4),(67,.4),(126,2),(134,5),
                      (19,.29),(29,.29),(49,.29),(66,.29),(125,.42),(133,1.06)):
        pr=region(pl,pt,pya.LayerInfo(layer,0));sr=region(sl,st,pya.LayerInfo(layer,0))
        collision=pr&sr;near=pr&sr.sized(round(gap*1000))
        rows.append(dict(layer=layer,clearance_um=gap,overlap_um2=collision.area()*1e-6,
                         proximity_um2=near.area()*1e-6,
                         proximity_bboxes_um=[[x*.001 for x in (b.left,b.bottom,b.right,b.top)]for b in (q.bbox()for q in near.each())]))
    passed=all(r['proximity_um2']==0 for r in rows)
    result=dict(status='passed frozen signal-route overlay clearance'if passed else'failed frozen signal-route overlay clearance',
                overlay_sha256=sha(power),signal_route_only_sha256=sha(signals),signal_full_GDS_sha256=sm['GDS_sha256'],
                script_sha256=sha(Path(__file__)),native_source_sha256=sm['native_GDS_sha256'],layers=rows,
                geometry_mutated=False,not_run=['combined routed+power stock DRC','root final PDN interactions',
                                               'coupling/IR/EM/fullchip LVS','adoption'])
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    (a.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
    raise SystemExit(0 if passed else 1)


if __name__=='__main__':main()
