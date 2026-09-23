#!/usr/bin/env python3
"""Scoped actual-geometry early VDD landing probe, never fullchip signoff."""
import argparse
import faulthandler
import hashlib
import json
import os
from pathlib import Path
import time
import traceback
import pya


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser();p.add_argument('--gds',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists();a.output.mkdir(parents=True)
    (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    result=dict(status='running',source_GDS_sha256=sha(a.gds),script_sha256=sha(Path(__file__)))
    receipt=a.output/'analysis.json';start=time.monotonic()
    def save(): receipt.write_text(json.dumps(result,indent=2)+'\n')
    faulthandler.dump_traceback_later(30,repeat=True)
    try:
        assert len(os.sched_getaffinity(0))==1 and pya.__version__=='0.30.9'
        ly=pya.Layout();ly.read(str(a.gds));top=ly.top_cell();assert ly.dbu==.001
        roi=pya.Box(350000,300000,510000,333000)
        layers=(1,5,6,7,8,10,14,19,29,30,49,50,66,67)
        raw={n:(pya.Region(top.begin_shapes_rec_overlapping(ly.layer(n,0),roi))&pya.Region(roi)).merged() for n in layers}
        nsd=(pya.Region(top.begin_shapes_rec_overlapping(ly.layer(7,21),roi))&pya.Region(roi)).merged()
        raw['gate']=(raw[1]&raw[5]).merged();raw['field']=(raw[5]-raw[1]).merged()
        raw['diode']=(((raw[1]-raw[5])-(raw[14]|nsd))|((raw[1]-raw[5])&raw[14])).merged()
        result.update(ROI_dbu=[roi.left,roi.bottom,roi.right,roi.top],raw_shapes={str(k):v.count()for k,v in raw.items()},phase='ROI prepared');save()
        bridge=pya.Region(pya.Box(358400,318000,359200,328180))
        target=pya.Point(358800,327780);header=pya.Point(358800,310000)
        observations=[]
        for added in (False,True):
            flat=pya.Layout();flat.dbu=.001;cell=flat.create_cell('actual_native_ROI')
            keys=['gate','field','diode',6,8,19,10,29,30]
            for i,key in enumerate(keys): cell.shapes(flat.layer(i+1,0)).insert(raw[key]+(bridge if key==30 and added else pya.Region()))
            net=pya.LayoutToNetlist(pya.RecursiveShapeIterator(flat,cell,[]))
            ml={key:net.make_layer(flat.layer(i+1,0),str(key))for i,key in enumerate(keys)}
            for r in ml.values():net.connect(r)
            for lo,hi in [('gate','field'),('gate',6),('field',6),('diode',6),(6,8),(8,19),(19,10),(10,29),(29,30)]:net.connect(ml[lo],ml[hi])
            result['phase']='extracting '+str(added);save();net.extract_netlist()
            probes={name:net.probe_net(ml[30],point)for name,point in [('header',header),('target',target)]}
            assert all(n is not None for n in probes.values())
            result['phase']='areas '+str(added);save()
            obs=dict(bridge_added=added,probes={name:n.cluster_id for name,n in probes.items()},areas={})
            for name,n in probes.items():
                obs['areas'][name]={str(k):net.shapes_of_net(n,ml[k],True).area()*1e-6 for k in ('gate',8,10,30)}
            if not added:
                assert probes['header'].cluster_id != probes['target'].cluster_id
                allowed={n.cluster_id for n in probes.values()}
                touches=[]
                for poly in raw[30].interacting(bridge.sized(240)).each():
                    pt=next(poly.each_point_hull());n=net.probe_net(ml[30],pt)
                    touches.append(dict(bbox=str(poly.bbox()),cluster=None if n is None else n.cluster_id,
                                        same_allowed=n is not None and n.cluster_id in allowed,
                                        direct_contact=not pya.Region(poly).interacting(bridge).is_empty()))
                obs['M3_within_240nm']=touches
                obs['foreign_M3_clearance_findings']=[row for row in touches if not row['same_allowed']]
                # No new cuts are added. Any old Via2/3 touched by the new M3
                # must already overlap native M3; otherwise its opposite layer
                # is an additional ownership question, not assumed safe.
                obs['new_cut_exposures']={str(cut):(raw[cut].interacting(bridge)-raw[30]).area()*1e-6 for cut in (29,49)}
            else: assert probes['header'].cluster_id==probes['target'].cluster_id
            observations.append(obs);result['observations']=observations;save()
        result.update(status='passed scoped early landing geometry and gate connectivity',elapsed_seconds=time.monotonic()-start,
            bridge_M3_box_dbu=[358400,318000,359200,328180],bridge_added_area_um2=(bridge-raw[30]).area()*1e-6,
            not_run=['fullchip connected-net area','fullchip stock antenna or DRC','root geometry adoption','outside-ROI foreign connectivity'],
            boundary='Actual clipped ROI. Gate area is a scoped lower-bound witness only if its same-node connection is confirmed in unmodified native geometry; metal areas are not fullchip ratios.')
        assert not observations[0]['foreign_M3_clearance_findings']
        assert not any(observations[0]['new_cut_exposures'].values())
        save();print(json.dumps(result,indent=2))
    except BaseException as exc:
        result.update(status='failed',error=repr(exc),traceback=traceback.format_exc(),elapsed_seconds=time.monotonic()-start);save();raise
    finally:faulthandler.cancel_dump_traceback_later()


if __name__=='__main__':main()
