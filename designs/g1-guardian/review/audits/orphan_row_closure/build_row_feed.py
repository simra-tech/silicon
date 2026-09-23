#!/usr/bin/env python3
"""Add one redundant source-bound orphan VDD row access stack, no native edits."""
import argparse
import faulthandler
import json
import os
from pathlib import Path
import sys
import time
import traceback
import pya

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
sys.path.insert(0,str(HERE.parent/'antenna_boundary_closure'))
from flat_metal_connectivity import flat_physical
from audit_placed_decap_domains import identity
from place_closed_analog import region,sha
from build_early_join import cell_records

METALS=(8,10,30,50,67,126,134)
CUTS=((19,8,10),(29,10,30),(49,30,50),(66,50,67),(125,67,126),(133,126,134))


def main():
    p=argparse.ArgumentParser();p.add_argument('--parent',type=Path,required=True)
    p.add_argument('--roundtrip',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists();a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    result=dict(status='running');receipt=a.output/'analysis.json';start=time.monotonic()
    def save():receipt.write_text(json.dumps(result,indent=2)+'\n')
    faulthandler.dump_traceback_later(60,repeat=True)
    try:
        assert pya.__version__=='0.30.9' and len(os.sched_getaffinity(0))==1
        source=a.parent/'power_connected_native.gds';meta=json.loads((a.parent/'analysis.json').read_text())
        assert sha(source)==meta['GDS_sha256']=='9940011f4061ec17815ff65f86c2448ad07145cf6a1d87645f4ab80bbb815669'
        assert sha(a.roundtrip)=='43be000677b631983ae7f159d988cc6d1654679caa436e6ab3da62b1df2452fd'
        lines=a.roundtrip.read_text().splitlines()
        assert 'INST\ti_core.u_digital_1\tsg13g2_tiehi\tR0\t1084320\t891000\t1086240\t894780' in lines
        assert 'CONN\tVDD\ti_core.u_digital_1\tVDD' in lines
        assert 'CONN\tVSS\ti_core.u_digital_1\tVSS' in lines
        assert 'CONN\tnet\ti_core.u_digital_1\tL_HI' in lines
        ly=pya.Layout();ly.read(str(source));top=ly.top_cell();assert ly.dbu==.001
        old={n:region(ly,top,pya.LayerInfo(n,0))for n in METALS+tuple(c[0]for c in CUTS)}
        before={c.name:cell_records(ly,c)for c in ly.each_cell()}
        result.update(source_GDS_sha256=sha(source),source_metadata_sha256=sha(a.parent/'analysis.json'),
            source_roundtrip_sha256=sha(a.roundtrip),script_sha256=sha(Path(__file__)),phase='extracting old flat metal graph');save()
        net,ml,held=flat_physical(ly,top)
        points={'row':(8,[1043040,894780]),'tiehi':(8,[1085000,894780]),
                'landing':(126,[1061920,894780]),'VDD_root':(134,[395000,354660]),'VSS_root':(134,[507000,334660])}
        probes={n:identity(net,ml[layer],point)for n,(layer,point)in points.items()}
        assert None not in probes.values(),probes
        assert probes['row']==probes['tiehi'] and probes['landing']==probes['VDD_root']
        assert len(set(probes.values()))==3,probes
        allowed={probes['row'],probes['VDD_root']}
        added={n:pya.Region()for n in old};arrays=[];x=1061920;y=894780
        for cut,lo,hi in CUTS[:5]:
            width,pitch,enc=(190,500,55)if cut<100 else(420,840,120)
            boxes=[]
            for dx in (-pitch//2,pitch//2):
                box=[x+dx-width//2,y-width//2,x+dx+width//2,y+width//2]
                added[cut].insert(pya.Box(*box));boxes.append(box)
            for layer in (lo,hi):
                extra=450 if layer==126 else enc
                wx=pitch+width+2*extra;wy=width+2*extra
                if layer==126:wy=max(wy,1640)
                added[layer].insert(pya.Box(x-wx//2,y-wy//2,x+wx//2,y+wy//2))
            arrays.append(dict(cut_layer=cut,cut_boxes=boxes,cut_count=2))
        errors=[];touches=[]
        def inspect(layer,polys,why):
            for poly in polys.each():
                p=next(poly.each_point_hull());found=identity(net,ml[layer],[p.x,p.y])
                row=dict(layer=layer,point=[p.x,p.y],found=found,why=why);touches.append(row)
                if found not in allowed:errors.append(row)
        for layer in METALS:inspect(layer,old[layer].interacting(added[layer]),'new metal touches existing metal')
        for cut,lo,hi in CUTS:
            for layer,other in ((lo,hi),(hi,lo)):
                inspect(other,old[other].interacting(old[cut].interacting(added[layer])),'new metal contacts old cut')
                inspect(layer,old[layer].interacting(added[cut]),'new cut contacts old metal')
                assert (added[cut]-(old[layer]+added[layer])).is_empty()
        gate=dict(status='failed'if errors else'passed',errors=errors,touches=touches,source_probes=probes,arrays=arrays)
        (a.output/'contact_gate.json').write_text(json.dumps(gate,indent=2)+'\n');assert not errors,errors[:10]
        name='ORPHAN_VDD_ROW_FEED_NOT_ADOPTED';assert ly.cell(name)is None
        child=ly.create_cell(name)
        for layer,r in added.items():child.shapes(ly.layer(layer,0)).insert(r)
        top.insert(pya.CellInstArray(child.cell_index(),pya.Trans()))
        output=a.output/'power_connected_native.gds';ly.write(str(output))
        overlay=pya.Layout();overlay.dbu=.001;ot=overlay.create_cell(name)
        for layer,r in added.items():ot.shapes(overlay.layer(layer,0)).insert(r)
        overlay.write(str(a.output/'row_feed_overlay.gds'))
        saved=pya.Layout();saved.read(str(output));st=saved.top_cell()
        after={c.name:cell_records(saved,c,name if c.name==st.name else None)for c in saved.each_cell()if c.name!=name}
        assert before==after
        result['phase']='extracting saved flat metal graph';save()
        new,nm,nh=flat_physical(saved,st)
        final={n:identity(new,nm[l],pt)for n,(l,pt)in points.items()}
        assert final['row']==final['tiehi']==final['landing']==final['VDD_root'] and final['row']!=final['VSS_root']
        result.update(status='passed source-held orphan VDD row feed geometry',GDS_sha256=sha(output),overlay_sha256=sha(a.output/'row_feed_overlay.gds'),
            source_cell='i_core.u_digital_1 / sg13g2_tiehi / L_HI -> net',arrays=arrays,before=probes,after=final,
            native_cell_shape_text_property_instance_exact='passed',old_cells=len(before),elapsed_seconds=time.monotonic()-start,
            capacity_scope='Two cuts per Via1..Via4 and TopVia1. No actual load, wire IR, current sharing, EM or lifetime qualification.',
            not_run=['stock main/maximal','independent every-cut-open','all 53 row terminals','final R6 routing context','electrical qualification'])
        save();print(json.dumps(result,indent=2))
    except BaseException as exc:
        result.update(status='failed',error=repr(exc),traceback=traceback.format_exc(),elapsed_seconds=time.monotonic()-start);save();raise
    finally:faulthandler.cancel_dump_traceback_later()


if __name__=='__main__':main()
