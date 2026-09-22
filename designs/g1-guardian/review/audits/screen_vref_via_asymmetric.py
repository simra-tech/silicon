#!/usr/bin/env python3
"""One constrained VREF site: asymmetric enclosure, not a modified foundry rule."""
import argparse,hashlib,json,os
from pathlib import Path
import pya
from sense_route_manifest import load_candidate_resistances
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
assert not a.output.exists() and len(os.sched_getaffinity(0))==1 and pya.__version__=='0.30.9'
m,_=load_candidate_resistances(a.manifest);ly=pya.Layout();ly.read(str(a.manifest.parent/'g1_chip_top.gds'));top=ly.cell('g1_chip_top');dbu=ly.dbu
old=pya.DBox(644.065,774.385,644.255,774.575).to_itype(dbu);new=old.moved(410,0);array=old+new
def coords(box):return [value*dbu for value in (box.left,box.bottom,box.right,box.top)]
def local(layer,datatype,window):return (pya.Region(top.begin_shapes_rec_overlapping(ly.layer(layer,datatype),window)) & pya.Region(window)).merged()
rows=[]
for layer in (10,30):
    landing=array.enlarged(50)
    if layer==30:landing=pya.Box(landing.left,array.bottom-10,landing.right,landing.top)
    window=landing.enlarged(350);actual=local(layer,0,window);own=[shape for shape in actual.each() if shape.inside(old.center())];assert len(own)==1
    others=actual-pya.Region(own[0]);conflicts=others & pya.Region(landing).sized(210);fill=local(layer,22,window)&pya.Region(landing).sized(300)
    rows.append({'layer':layer,'landing_bbox_um':coords(landing),'actual_added_area_um2':(pya.Region(landing)-actual).area()*dbu**2,
        'distinct_metal_conflicts':[coords(shape.bbox()) for shape in conflicts.each()], 'fill_keepout_area_um2':fill.area()*dbu**2,
        'minimum_drawn_enclosure_um':.01 if layer==30 else .05})
window=new.enlarged(300);othercuts=local(29,0,window)-pya.Region(old);cutclear=(othercuts&pya.Region(new).sized(220)).is_empty()
result={'candidate_sha256':m['candidate_sha256'],'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'net':'i_core.vref','point_um':[644.16,774.48],'cut_layer':29,'old_cut_bbox_um':coords(old),'added_cut_bbox_um':coords(new),'metals':rows,'cut_spacing_clear':cutclear,
    'status':'passed local geometric feasibility' if cutclear and all(not row['distinct_metal_conflicts'] and row['fill_keepout_area_um2']==0 for row in rows) else 'failed local geometric feasibility',
    'justification':'Standard symmetric.05um enclosure widens the existingM3 south edge into its neighbor spacing. Keep.05um elsewhere and use.01um south enclosure (twice stockVn.c minimum.005um), leaving.215um gap to the neighbor above stockMn.b .21um. Existing cut retained, one cut added at.41um pitch. This is a design geometry choice, not a deck change or rule waiver.',
    'stock_DRC_LVS_antenna_density':'not run','current_RC_fullpath_open_qualification':'not run'}
a.output.write_text(json.dumps(result,indent=2)+'\n');print(result['status'])
