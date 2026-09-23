#!/usr/bin/env python3
"""Read-only own-pad collector/shared VDDA geometry variants; no GDS save."""
import argparse
import json
import os
from pathlib import Path
import sys
import pya

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from place_closed_analog import region,sha
from build_interface import METALS,CUTS,box


def bounds(r):return [[v*.001 for v in(b.left,b.bottom,b.right,b.top)]for b in(p.bbox()for p in r.each())]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--native',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert not a.output.exists()
    assert pya.__version__=='0.30.9'and len(os.sched_getaffinity(0))==1
    source=a.native/'power_connected_native.gds';meta=json.loads((a.native/'analysis.json').read_text())
    assert sha(source)==meta['GDS_sha256']=='226c5aad876b9aea1ec2cd5874c828b2ae87ffb80a3efded7f8d9a2389cd8e05'
    assert meta['status'].startswith('passed')
    ly=pya.Layout();ly.read(str(source));top=ly.top_cell()
    actual={l:region(ly,top,pya.LayerInfo(l,0))for l in METALS+tuple(CUTS)}
    own={l:pya.Region()for l in METALS}
    for l,x,y in[(10,1093.145,395),(30,1093.145,395),(134,743.4,922)]:
        own[l]=actual[l].interacting(box(x-.001,y-.001,x+.001,y+.001))
        assert not own[l].is_empty(),(l,x,y)
    variants=[]
    for stack_x,center in((1080,393.49),(1086,393.49),(1090,393.49),(1096,393.49),(1100,393.49)):
        new={l:pya.Region()for l in actual}
        new[30]+=box(1087.29,381.105,1093.29,405.875)
        new[30]+=box(min(stack_x-5.1,1087.29),center-5.1,max(stack_x+5.1,1093.29),center+5.1)
        new[134]+=box(1058.9,center-1.1,1061.1,923.1)
        new[134]+=box(1058.9,center-1.1,stack_x+1.1,center+1.1)
        new[134]+=box(742.3,920.9,1061.1,923.1)
        arrays=[]
        for l,nx,ny in[(49,8,8),(66,8,8),(125,4,4),(133,2,2)]:
            lo,hi=CUTS[l]
            cut,pitch,enc,limit=(.19,.5,.055,.4)if l<100 else((.42,.84,.12,1.4)if l==125 else(.9,1.96,.65,10))
            for i in range(nx):
                for j in range(ny):
                    x=stack_x+(i-(nx-1)/2)*pitch;y=center+(j-(ny-1)/2)*pitch
                    new[l]+=box(x-cut/2,y-cut/2,x+cut/2,y+cut/2)
            for layer in(lo,hi):
                enclosure=.45 if l==125 and layer==126 else enc
                wx=(nx-1)*pitch+cut+2*enclosure;wy=(ny-1)*pitch+cut+2*enclosure
                new[layer]+=box(stack_x-wx/2,center-wy/2,stack_x+wx/2,center+wy/2)
            arrays.append(dict(layer=l,cuts=nx*ny,half_table_mA=nx*ny*limit*.5,
                               one_cut_lost_half_table_mA=(nx*ny-1)*limit*.5))
        checks=[]
        for l in METALS:
            gap=.4 if l<100 else 2 if l==126 else 5
            foreign=actual[l]-own[l];overlap=new[l]&foreign;near=new[l]&foreign.sized(round(gap*1000))
            checks.append(dict(layer=l,overlap_um2=overlap.area()*1e-6,proximity_um2=near.area()*1e-6,
                               proximity_bboxes_um=bounds(near),
                               foreign_polygon_bboxes_um=bounds(foreign.interacting(new[l].sized(round(gap*1000))))))
        for l,(lo,hi)in CUTS.items():
            allowedcuts=actual[l]&own[lo]&own[hi]
            capture=(new[lo]+new[hi])&(actual[l]-allowedcuts)
            gap=.29 if l<100 else .42 if l==125 else 1.06
            near=new[l]&actual[l].sized(round(gap*1000))
            assert(new[l]-(new[lo]+own[lo])).is_empty()and(new[l]-(new[hi]+own[hi])).is_empty()
            checks.append(dict(cut_layer=l,foreign_cut_capture_um2=capture.area()*1e-6,
                               existing_cut_proximity_um2=near.area()*1e-6,capture_bboxes_um=bounds(capture)))
        failed=[r for r in checks if any(v!=0 for k,v in r.items()if k.endswith('_um2'))]
        variants.append(dict(stack_x_um=stack_x,center_y_um=center,status='passed native-only conservative screen'if not failed else'failed native-only conservative screen',
                             arrays=arrays,checks=checks,failures=failed))
    result=dict(status='completed shared VDDA variant screen; no adoption',source_GDS_sha256=sha(source),
                script_sha256=sha(Path(__file__)),variants=variants,geometry_saved=False,
                exploratory_aggregate_mA=10,scope='10mA total pad geometry assumption includes SENSE; SENSE remains its own <=2mA leaf, not a series aggregate path.',
                not_run=['pad full wire/cut distribution qualification','new stock DRC','final signal reroute',
                         'all VDDA consumer feeds/actual current partition/IR/EM/PVT','adoption'])
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    (a.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({**{k:v for k,v in result.items()if k!='variants'},
                     'variants':[{k:v for k,v in r.items()if k!='checks'}for r in variants]},indent=2))


if __name__=='__main__':main()
