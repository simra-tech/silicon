#!/usr/bin/env python3
"""Remove only top-level active/poly dummy-fill polygons crossing native RZ100."""
import argparse
import hashlib
import json
from pathlib import Path
import pya

INPUT_SHA='6b9c5878a81a0ac4d3f68d3d8dbb5fa1927442675606aa6bd46a14d6552def51'
TOP='placed_core_NOT_CONNECTED_FULLCHIP'
LAYERS=((1,22),(5,22))

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def region(cell,li): return pya.Region(cell.begin_shapes_rec(li)).merged()
def overlaps(a,b): return a.left<b.right and b.left<a.right and a.bottom<b.top and b.bottom<a.top

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--input',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--input-record-proof',type=Path);a=ap.parse_args()
    input_sha=sha(a.input)
    if input_sha!=INPUT_SHA:
        assert a.input_record_proof is not None
        proof=json.loads(a.input_record_proof.read_text())
        assert proof['status']=='passed exact GDS record identity except timestamp payloads'
        assert proof['reference_gds_sha256']==INPUT_SHA and proof['reproduced_gds_sha256']==input_sha
        assert proof['all_nondate_records_byte_exact'] and proof['other_record_differences']==0
    assert not a.output.exists()
    a.output.mkdir(parents=True)
    ly=pya.Layout();ly.read(str(a.input));top=ly.cell(TOP);assert top and abs(ly.dbu-.001)<1e-12
    # Native RZ marker: local (124.530,152.200)-(224.530,153.200) um,
    # transformed by the exact assembly R90 at (1031,331) um.
    marker=pya.Trans(pya.Trans.R90,1031000,331000)*pya.Box(124530,152200,224530,153200)
    window=pya.Trans(pya.Trans.R90,1031000,331000)*pya.Box(123000,151000,226000,155000)
    assert window.left<=marker.left and marker.right<=window.right
    assert window.bottom<=marker.bottom and marker.top<=window.top
    rows={}
    for pair in LAYERS:
        li=ly.layer(*pair)
        direct=pya.Region(top.shapes(li)) & pya.Region(window)
        hierarchy=region(top,li) & pya.Region(window)
        assert (direct^hierarchy).is_empty(),('non-root fill in RZ window',pair)
        victims=[s for s in top.shapes(li).each() if overlaps(s.bbox(),window)]
        assert victims,('no crossing filler',pair)
        removed=pya.Region()
        details=[]
        for s in victims:
            assert s.is_box() or s.is_simple_polygon() or s.is_polygon(),('nonpolygon filler',pair,s.to_s())
            polygon=s.box if s.is_box() else s.polygon
            removed.insert(polygon)
            details.append(str(s.bbox()))
            s.delete()
        assert (region(top,li)&pya.Region(window)).is_empty(),('remaining fill in keepout',pair)
        rows[str(pair)]=dict(removed_shapes=len(victims),removed_area_dbu2=removed.merged().area(),
                             removed_boxes=details,pre_window_area_dbu2=hierarchy.area())
    assert rows[str((1,22))]['removed_shapes']==20
    assert rows[str((5,22))]['removed_shapes']==19
    candidate=a.output/'rz_fill_keepout.gds';ly.write(str(candidate))
    result=dict(status='passed narrowly scoped native RZ100 filler keepout; extraction not run',
                input_gds_sha256=input_sha,output_gds_sha256=sha(candidate),
                top=TOP,marker_dbu=str(marker),keepout_dbu=str(window),removed=rows,
                modified_layers=list(map(str,LAYERS)),source_deck_models_untouched=True)
    (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('status','output_gds_sha256','removed')}))
if __name__=='__main__':main()
