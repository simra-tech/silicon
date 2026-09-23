#!/usr/bin/env python3
"""Reuse the held upper VDD stack; add only the two missing Via1 cuts."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import traceback
import pya

HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent));sys.path.insert(0,str(HERE.parent/'antenna_boundary_closure'))
from flat_metal_connectivity import flat_physical
from audit_placed_decap_domains import identity
from place_closed_analog import region,sha
from build_early_join import cell_records


def main():
    p=argparse.ArgumentParser();p.add_argument('--parent',type=Path,required=True)
    p.add_argument('--previous',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists();a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    result=dict(status='running');start=time.monotonic()
    try:
        assert pya.__version__=='0.30.9' and len(os.sched_getaffinity(0))==1
        source=a.parent/'power_connected_native.gds';parent=json.loads((a.parent/'analysis.json').read_text())
        assert sha(source)==parent['GDS_sha256']=='9940011f4061ec17815ff65f86c2448ad07145cf6a1d87645f4ab80bbb815669'
        previous=json.loads((a.previous/'analysis.json').read_text());gate=json.loads((a.previous/'contact_gate.json').read_text())
        assert previous['status'].startswith('passed') and previous['source_GDS_sha256']==sha(source)
        assert gate['status']=='passed' and not gate['errors']
        assert gate['source_probes']==previous['before']
        source_owners={8:previous['before']['row'],10:previous['before']['VDD_root']}
        old_witnesses={layer:[r['point']for r in gate['touches']if r['layer']==layer and r['why']=='new cut contacts old metal' and r['found']==owner]for layer,owner in source_owners.items()}
        assert all(old_witnesses.values())
        ly=pya.Layout();ly.read(str(source));top=ly.top_cell();assert ly.dbu==.001
        before={c.name:cell_records(ly,c)for c in ly.each_cell()}
        boxes=[[1061575,894685,1061765,894875],[1062075,894685,1062265,894875]]
        cuts=pya.Region();[cuts.insert(pya.Box(*box))for box in boxes]
        raw={n:region(ly,top,pya.LayerInfo(n,0))for n in (8,10,19)}
        witnesses=[]
        for layer in (8,10):
            assert (cuts-raw[layer]).is_empty()
            touched=raw[layer].interacting(cuts)
            assert touched.count()==1
            poly=next(touched.each())
            assert any(poly.inside(pya.Point(*xy))for xy in old_witnesses[layer]),(layer,old_witnesses[layer])
            witnesses.append(dict(layer=layer,source_net=source_owners[layer],old_graph_witnesses=old_witnesses[layer],polygon_bbox=str(poly.bbox())))
        assert raw[19].interacting(cuts.sized(190)).is_empty()
        name='ORPHAN_VDD_VIA1_REUSE_UPPER_NOT_ADOPTED';assert ly.cell(name)is None
        child=ly.create_cell(name);child.shapes(ly.layer(19,0)).insert(cuts);top.insert(pya.CellInstArray(child.cell_index(),pya.Trans()))
        out=a.output/'power_connected_native.gds';ly.write(str(out))
        ov=pya.Layout();ov.dbu=.001;oc=ov.create_cell(name);oc.shapes(ov.layer(19,0)).insert(cuts);ov.write(str(a.output/'row_feed_overlay.gds'))
        saved=pya.Layout();saved.read(str(out));st=saved.top_cell()
        after={c.name:cell_records(saved,c,name if c.name==st.name else None)for c in saved.each_cell()if c.name!=name}
        assert before==after
        assert (region(saved,st,pya.LayerInfo(19,0))^(raw[19]|cuts)).is_empty()
        net,ml,held=flat_physical(saved,st)
        points={'row':(8,[1043040,894780]),'tiehi':(8,[1085000,894780]),'M2_landing':(10,[1061920,894780]),
                'TM1_landing':(126,[1061920,894780]),'VDD_root':(134,[395000,354660]),'VSS_root':(134,[507000,334660])}
        probes={n:identity(net,ml[layer],xy)for n,(layer,xy)in points.items()}
        assert None not in probes.values()
        assert len({v for k,v in probes.items()if k!='VSS_root'})==1 and probes['VSS_root']!=probes['row']
        result.update(status='passed source-held two-Via1-only orphan VDD repair',source_GDS_sha256=sha(source),GDS_sha256=sha(out),
            source_metadata_sha256=sha(a.parent/'analysis.json'),previous_precontact_gate_sha256=sha(a.previous/'contact_gate.json'),
            previous_geometry_metadata_sha256=sha(a.previous/'analysis.json'),script_sha256=sha(Path(__file__)),overlay_sha256=sha(a.output/'row_feed_overlay.gds'),
            old_polygon_ownership_witnesses=witnesses,arrays=[dict(cut_layer=19,cut_boxes=boxes,cut_count=2)],
            added_only='Two Via1 cuts; no metal, Via2/3/4, TopVia1/2, cell, text, property or source changes',
            native_cell_shape_text_property_instance_exact='passed',old_cells=len(before),probes=probes,elapsed_seconds=time.monotonic()-start,
            original_r1_stock='failed 26 added upper-cut markers; unchanged original artifacts retained',
            not_run=['all 53 current row windows and every-cut-open','stock DRC on r2','final routed context','current IR EM lifetime qualification'])
    except BaseException as exc:
        result.update(status='failed',error=repr(exc),traceback=traceback.format_exc());raise
    finally:
        (a.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
