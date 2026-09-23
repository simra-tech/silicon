#!/usr/bin/env python3
"""Pinned r8 native passive correspondence and candidate footprint screen only."""
import argparse,copy,json,os,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'coordinated_gm4'))
from build_native_prototypes import lib,pya,sha
from build_power_revision import snapshot,full_nets_upper

PARENT='8060e30ac14a1c4aeb1cf62204c9e95d9a68dbad3d73412fbb34c6a33be8b4f7'
SOURCE='b8912a862b61554266239634dd388ed0ffad229c0b0e48819ad129d589352e97'

def regions(cell):
    result={}
    for li in cell.layout().layer_indexes():
        info=cell.layout().get_info(li)
        r=snapshot(cell,info.layer,info.datatype)
        if not r.is_empty():result[(info.layer,info.datatype)]=r
    return result

def native(kind,params):
    ly=pya.Layout();ly.dbu=.001
    index=lib.LIB.layout().add_pcell_variant(lib.LIB.layout().pcell_id(kind),params)
    cell=ly.cell(ly.add_lib_cell(lib.LIB,index))
    return ly,cell

def box(r):
    b=r.bbox();return [b.left*.001,b.bottom*.001,b.right*.001,b.top*.001]

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['parent','source','output']:p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--cpu',type=int,required=True);a=p.parse_args()
    assert os.sched_getaffinity(0)=={a.cpu} and a.cpu==1 and pya.__version__=='0.30.9'
    assert not a.output.exists() and sha(a.parent)==PARENT and sha(a.source)==SOURCE
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    ly=pya.Layout();ly.read(str(a.parent));cell=ly.cell('g1_sense_physical');assert cell
    frozen=regions(cell);rows=[]
    recipes=[('XCC','cmim',dict(Calculate='C',w='69u',l='23u'),dict(Calculate='C',w='45u',l='23u'),[60.46,122.,130.66,146.2],False),
             ('XRZ','rppd',dict(Calculate='R',w='1u',l='6.2u'),dict(Calculate='R',w='1u',l='62u'),[123.92,152.,125.32,159.42],True)]
    for name,kind,oldpars,newpars,target,rotate in recipes:
        oldly,old=native(kind,oldpars);oldregs=regions(old);b=old.bbox()
        assert abs(b.width()*.001-(target[2]-target[0]))<1e-8 and abs(b.height()*.001-(target[3]-target[1]))<1e-8
        transform=pya.Trans(round(target[0]*1000)-b.left,round(target[1]*1000)-b.bottom)
        oldregs={k:r.transformed(transform) for k,r in oldregs.items()}
        missing={str(k):(r-frozen.get(k,pya.Region())).area()*1e-6 for k,r in oldregs.items()}
        assert not any(missing.values()),(name,missing)
        newly,new=native(kind,newpars);newregs=regions(new)
        rotation=pya.Trans(pya.Trans.R90 if rotate else pya.Trans.R0)
        b=pya.Region(new.bbox()).transformed(rotation).bbox()
        # Preserve lower-left bbox, rotate only isolated RZ. No geometry saved.
        trans=pya.Trans(rotation.rot,False,round(target[0]*1000)-b.left,round(target[1]*1000)-b.bottom)
        newregs={k:r.transformed(trans) for k,r in newregs.items()}
        merged=pya.Region()
        for r in newregs.values():merged+=r
        obstacles={}
        for k,r in newregs.items():
            if k[1] or k[0] in [160,189]:continue
            other=frozen.get(k,pya.Region())-oldregs.get(k,pya.Region())
            hit=r&other
            if not hit.is_empty():obstacles[str(k)]=dict(area_um2=hit.area()*1e-6,bbox_um=box(hit))
        rows.append(dict(device=name,old_parameters=oldpars,new_parameters=newpars,
            old_native_bbox_um=target,old_subset_missing_um2=missing,
            native_origin_transform=str(transform),candidate_transform=str(trans),
            candidate_bbox_um=box(merged),candidate_same_layer_overlap=obstacles,
            old_layers={str(k):dict(area_um2=r.area()*1e-6,bbox_um=box(r),polygons=r.count()) for k,r in oldregs.items()},
            new_layers={str(k):dict(area_um2=r.area()*1e-6,bbox_um=box(r),polygons=r.count()) for k,r in newregs.items()}))
    after=regions(cell)
    assert set(after)==set(frozen) and all((after[k]^v).is_empty() for k,v in frozen.items())
    result=dict(status='passed native correspondence/read-only footprint inventory',parent_sha256=PARENT,source_sha256=SOURCE,
        native_devices=rows,parent_exact_unchanged=True,geometry_saved=False,
        overlap_scope='Same-layer overlap with parent minus old primitive; includes retained same-net route tabs and taps. Not a foreign-net/spacing acceptance.',
        stock_DRC='not run',source_LVS='not run',physical_adoption='not run')
    (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':main()
