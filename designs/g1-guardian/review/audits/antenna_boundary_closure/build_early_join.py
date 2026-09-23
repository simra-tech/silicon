#!/usr/bin/env python3
"""One additive M3 join on the held sealed R5 diagnostic parent."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time
import traceback
import pya


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def cell_records(layout,cell,excluded=None):
    shapes=[]
    for index in layout.layer_indexes():
        info=str(layout.get_info(index))
        for shape in cell.shapes(index).each():
            shapes.append((info,str(shape),repr(shape.properties())))
    inst=[]
    for i in cell.each_inst():
        if i.cell.name==excluded:continue
        c=i.cell_inst
        inst.append((i.cell.name,str(c.cplx_trans),str(c.a),str(c.b),c.na,c.nb,repr(i.properties())))
    payload=json.dumps([sorted(shapes),sorted(inst)],separators=(',',':')).encode()
    return dict(sha256=hashlib.sha256(payload).hexdigest(),shapes=len(shapes),instances=len(inst))


def main():
    p=argparse.ArgumentParser();p.add_argument('--parent',type=Path,required=True)
    p.add_argument('--proof',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists();a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    result=dict(status='running');start=time.monotonic()
    try:
        assert pya.__version__=='0.30.9' and len(os.sched_getaffinity(0))==1
        source=a.parent/'sealed_native.gds';meta=json.loads((a.parent/'analysis.json').read_text())
        assert sha(source)==meta['GDS_sha256']=='393b485183dc7d7624365a2119590ed1babdf945ce298f848a0b1c228da736c7'
        proof=json.loads(a.proof.read_text());assert proof['status'].startswith('passed') and proof['source_GDS_sha256']==sha(source)
        assert proof['bridge_M3_box_dbu']==[358400,318000,359200,328180]
        assert not proof['observations'][0]['foreign_M3_clearance_findings'] and not any(proof['observations'][0]['new_cut_exposures'].values())
        ly=pya.Layout();ly.read(str(source));top=ly.top_cell();assert ly.dbu==.001
        assert top.name=='placed_core_NOT_CONNECTED_FULLCHIP'
        name='EARLY_VDD_M3_ANTENNA_JOIN_NOT_ADOPTED';assert ly.cell(name) is None
        before={c.name:cell_records(ly,c)for c in ly.each_cell()}
        child=ly.create_cell(name);child.shapes(ly.layer(30,0)).insert(pya.Box(*proof['bridge_M3_box_dbu']))
        top.insert(pya.CellInstArray(child.cell_index(),pya.Trans()))
        out=a.output/'sealed_native.gds';ly.write(str(out))
        overlay=pya.Layout();overlay.dbu=.001;ot=overlay.create_cell(name)
        ot.shapes(overlay.layer(30,0)).insert(pya.Box(*proof['bridge_M3_box_dbu']));overlay.write(str(a.output/'antenna_join_overlay.gds'))
        saved=pya.Layout();saved.read(str(out));st=saved.top_cell()
        after={c.name:cell_records(saved,c,name if c.name==st.name else None)for c in saved.each_cell()if c.name!=name}
        assert before==after
        ci=saved.cell(name);assert ci is not None and ci.child_instances()==0
        shapes=[(str(saved.get_info(i)),str(s))for i in saved.layer_indexes()for s in ci.shapes(i).each()]
        assert len(shapes)==1 and shapes[0][0]=='30/0'
        region=pya.Region(st.begin_shapes_rec(saved.layer(39,4)))
        assert region.count()==1 and (region^pya.Region(pya.Box(0,0,1414000,1414000))).is_empty()
        assert pya.Region(st.begin_shapes_rec(saved.layer(189,0))).is_empty()
        result.update(status='passed single additive M3 early VDD join; diagnostic R5 parent',
            GDS_sha256=sha(out),source_GDS_sha256=sha(source),source_metadata_sha256=sha(a.parent/'analysis.json'),
            proof_sha256=sha(a.proof),script_sha256=sha(Path(__file__)),overlay_sha256=sha(a.output/'antenna_join_overlay.gds'),
            native_cell_shape_text_property_instance_exact='passed',original_cells=len(before),native_cell_inventory=before,
            native_top_instances=len(list(ly.cell(top.name).each_inst()))-1,
            added_only=dict(layer='Metal3 30/0',box_dbu=proof['bridge_M3_box_dbu'],new_union_area_um2=proof['bridge_added_area_um2']),
            actual_39_4_boundary_um2=1999396, elapsed_seconds=time.monotonic()-start,
            not_run=['stock antenna','stock main/maximal','R6 and all-feed context','electrical-current or reliability qualification'],
            not_applicable=['device/source/card/deck or port changes'])
    except BaseException as exc:
        result.update(status='failed',error=repr(exc),traceback=traceback.format_exc());raise
    finally:
        (a.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({k:v for k,v in result.items()if k!='native_cell_inventory'},indent=2))


if __name__=='__main__':main()
