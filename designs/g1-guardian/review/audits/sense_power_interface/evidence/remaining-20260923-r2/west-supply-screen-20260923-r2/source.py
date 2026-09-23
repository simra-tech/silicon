#!/usr/bin/env python3
"""Freeze proposed additive supply geometry against actual flat native ownership."""
import argparse
import json
import os
from pathlib import Path
import time
import pya
from build_ls_interface import flat_physical, region, sha, METALS, CUTS, box


class Routes:
    def __init__(self):
        self.layers={n:{l:pya.Region()for l in METALS+tuple(CUTS)}for n in('VDD','VDDA','VSS')}
        self.arrays=[]

    def wire(self,n,l,x1,y1,x2,y2,w):
        assert x1==x2 or y1==y2
        self.layers[n][l]+=box(min(x1,x2)-w/2,min(y1,y2)-w/2,max(x1,x2)+w/2,max(y1,y2)+w/2)

    def array(self,n,l,x,y,nx,ny):
        lo,hi=CUTS[l]
        size,pitch,enc=(.19,.5,.055)if l<100 else(.42,.84,.12)if l==125 else(.9,1.96,.65)
        for i in range(nx):
            for j in range(ny):
                cx=x+(i-(nx-1)/2)*pitch;cy=y+(j-(ny-1)/2)*pitch
                self.layers[n][l]+=box(cx-size/2,cy-size/2,cx+size/2,cy+size/2)
        for m in(lo,hi):
            e=.45 if l==125 and m==126 else enc
            w=max((nx-1)*pitch+size+2*e,1.64 if m==126 else 2 if m==134 else .2)
            h=max((ny-1)*pitch+size+2*e,1.64 if m==126 else 2 if m==134 else .2)
            self.layers[n][m]+=box(x-w/2,y-h/2,x+w/2,y+h/2)
        self.arrays.append(dict(net=n,layer=l,center_um=[x,y],nx=nx,ny=ny,cuts=nx*ny))


def bounds(r):
    return [[v*.001 for v in(b.left,b.bottom,b.right,b.top)]for b in(q.bbox()for q in r.each())]


def check(routes,native,allowed):
    failures=[]
    for net,layers in routes.layers.items():
        if all(r.is_empty()for r in layers.values()):continue
        for layer in METALS:
            if layers[layer].is_empty():continue
            gap=.4 if layer<100 else 2 if layer==126 else 5
            foreign=native[layer]-allowed[net][layer]
            near=layers[layer]&foreign.sized(round(gap*1000))
            other=pya.Region()
            for n,rr in routes.layers.items():
                if n!=net:other+=layers[layer]&rr[layer].sized(round(gap*1000))
            if not near.is_empty()or not other.is_empty():
                failures.append(dict(net=net,layer=layer,foreign_area_um2=near.area()*1e-6,
                    foreign_bbox_um=bounds(near),other_new_area_um2=other.area()*1e-6,
                    foreign_native_bbox_um=bounds(foreign.interacting(layers[layer].sized(round(gap*1000))))))
        for layer,(lo,hi)in CUTS.items():
            # Empty new conductors cannot capture an old cut. This avoids
            # repeating whole-chip Boolean work for explicitly unchanged layers.
            if layers[lo].is_empty()and layers[hi].is_empty()and layers[layer].is_empty():continue
            own=native[layer]&allowed[net][lo]&allowed[net][hi]
            captured=(layers[lo]+layers[hi])&(native[layer]-own)
            proximity=layers[layer]&native[layer].sized(420 if layer==125 else 1060 if layer==133 else 290)
            assert(layers[layer]-(layers[lo]+allowed[net][lo])).is_empty()
            assert(layers[layer]-(layers[hi]+allowed[net][hi])).is_empty()
            if not captured.is_empty()or not proximity.is_empty():
                failures.append(dict(net=net,cut_layer=layer,foreign_capture_um2=captured.area()*1e-6,
                    foreign_capture_bbox_um=bounds(captured),old_cut_proximity_um2=proximity.area()*1e-6,
                    old_cut_proximity_bbox_um=bounds(proximity)))
    return failures


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in('parent','ls','inventory','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--mode',choices=['west','trip'],required=True)
    a=p.parse_args();assert not a.output.exists()and len(os.sched_getaffinity(0))==1 and pya.__version__=='0.30.9'
    started=time.monotonic()
    source=a.parent/'power_connected_native.gds'
    assert sha(source)=='4e034eda528d4bfa3c00accf1f619fe0569b07471b6bece6697466eb9877a87e'
    ls=a.ls/'power_overlay.gds';assert sha(ls)=='576cdf8f417a52456bdf60fe65c1f2516cab174ad0a449258b6617dbbcc3a60d'
    inv=json.loads(a.inventory.read_text());assert inv['status'].startswith('passed')
    bindings=[r for r in inv['terminals']if r['instance']in('i_core.u_gate','i_core.u_trip','i_core.u_ls_en','i_core.u_ls_r4','i_core.u_ls_mode')]
    assert len(bindings)==15
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    result=dict(status='running',mode=a.mode,source_GDS_sha256=sha(source),LS_overlay_sha256=sha(ls),
                source_inventory_sha256=sha(a.inventory),source_bindings=bindings,script_sha256=sha(Path(__file__)),
                not_run=['saved candidate/stock/cut-loss','actual current division/native source-contact capacity','full PVT/IR/EM','adoption'])
    try:
        ly=pya.Layout();ly.read(str(source));top=ly.top_cell();ll=pya.Layout();ll.read(str(ls))
        for layer in METALS+tuple(CUTS):
            for poly in region(ll,ll.top_cell(),pya.LayerInfo(layer,0)).each():top.shapes(ly.layer(layer,0)).insert(poly)
        flat,net,metals=flat_physical(ly,top)
        print(json.dumps(dict(phase='actual full-native flat extraction complete',wall_s=time.monotonic()-started)),flush=True)
        native={l:region(ly,top,pya.LayerInfo(l,0))for l in METALS+tuple(CUTS)}
        probes={'VDD':[(134,395,354.66)],'VSS':[(134,507,334.66)],'VDDA':[(134,1060,726)]}
        if a.mode=='west':probes['VDDA'] += [(30,783,501.4),(30,734,600)]
        else:
            probes['VDD'] += [(30,792,942)];probes['VSS'] += [(30,792,737)];probes['VDDA'] += [(30,792,938.75)]
        allowed={n:{l:pya.Region()for l in METALS}for n in probes};identities={}
        for n,points in probes.items():
            identities[n]=[]
            for l,x,y in points:
                found=net.probe_net(metals[l],pya.DPoint(x,y).to_itype(.001));assert found is not None,(n,l,x,y)
                identities[n].append(found.cluster_id)
                for layer in METALS:
                    for poly in net.shapes_of_net(found,metals[layer],True).each():allowed[n][layer].insert(poly)
        assert all(not(set(identities[n])&set(identities[m]))for n in identities for m in identities if n!=m)
        print(json.dumps(dict(phase='native source-domain ownership complete',wall_s=time.monotonic()-started)),flush=True)
        routes=Routes()
        if a.mode=='west':
            # LS branch .3mA; GATE branch2mA. No new compact/source change.
            for l in(49,66):routes.array('VDDA',l,783,501.4,3,1)
            routes.array('VDDA',125,783,501.4,2,2);routes.array('VDDA',133,783,501.4,1,2)
            routes.wire('VDDA',134,783,501.4,783,712.5,2.2)
            # Cross below the existing SENSE VSS TM2 flyover, without cuts
            # at the actual crossing. Return to TM2 above its five-um halo.
            routes.array('VDDA',133,783,712.5,1,2)
            routes.wire('VDDA',126,783,712.5,783,731.5,2.2)
            routes.array('VDDA',133,783,731.5,1,2)
            routes.wire('VDDA',134,783,731.5,814,731.5,2.2)
            routes.wire('VDDA',134,814,731.5,814,726,2.2)
            routes.wire('VDDA',134,814,726,1060,726,2.2)
            routes.array('VDDA',49,734,600,4,3)
            routes.wire('VDDA',50,734,600,734,603,2.2)
            routes.wire('VDDA',50,734,603,783,603,2.2)
            routes.array('VDDA',66,783,603,4,3)
            routes.array('VDDA',125,783,603,2,2);routes.array('VDDA',133,783,603,1,2)
            result['exploratory_targets_mA']={'LS_total':.3,'GATE':2,'west_aggregate':2.3,'shared_pad_total':10}
        else:
            # External distributed headers only; independent internal widening
            # cases below do not get silently included in the saved recipe.
            for x in(792,880,968):
                for l in(49,66):routes.array('VDD',l,x,942,4,3)
                routes.array('VDD',125,x,942,2,2);routes.array('VDD',133,x,942,1,2)
            routes.wire('VDD',134,750,942,968,942,2.2);routes.array('VDD',133,750,942,2,2)
            for x in(792,836,880,924,968):
                for l in(49,66):routes.array('VDDA',l,x,938.75,6,3)
                routes.wire('VDDA',67,x,938.75,x,934.5,3.2)
                routes.array('VDDA',125,x,934.5,3,2);routes.array('VDDA',133,x,934.5,1,2)
            routes.wire('VDDA',30,772.6,938.75,998.4,938.75,3.2)
            routes.wire('VDDA',134,792,934.5,1060,934.5,2.2)
            routes.wire('VDDA',134,1060,922,1060,934.5,2.2)
            for x in(792,880,968):
                for l in(49,66):routes.array('VSS',l,x,737,6,3)
                routes.array('VSS',125,x,737,3,2);routes.array('VSS',133,x,737,1,2)
            routes.wire('VSS',30,772.6,737,998.4,737,3.2)
            routes.wire('VSS',134,792,737,1039.2,737,2.2);routes.array('VSS',133,1039.2,737,2,2)
            internal=[]
            for name,x,end in [('VDD',778.5,942),('VDD',893.5,942),('VDDA',840.5,938.75),('VDDA',955.5,938.75)]:
                for width in(1.2,2.2,4.2):
                    r=Routes();r.wire(name,50,x,746.3,x,end,width)
                    internal.append(dict(net=name,x_um=x,width_um=width,failures=check(r,native,allowed)))
            result.update(internal_M4_widening_screens=internal,
                          exploratory_targets_mA={'VDD_external_total':2,'VDDA_external_total':8,'VSS_external_total':9},
                          internal_capacity='not qualified; external headers do not close native lower cuts or source/contact distribution')
        failures=check(routes,native,allowed)
        result.update(status='passed proposed geometry screen'if not failures else'failed proposed geometry screen',
                      flat_initial_cluster_ids=identities,failures=failures,arrays=routes.arrays,
                      new_cut_count=sum(r['cuts']for r in routes.arrays))
        recipe={n:{str(l):[dict(hull=[[v.x,v.y]for v in poly.each_point_hull()],
                  holes=[[[v.x,v.y]for v in poly.each_point_hole(i)]for i in range(poly.holes())])
                  for poly in region_.merged().each()]for l,region_ in layers.items()}for n,layers in routes.layers.items()}
        (a.output/'recipe.json').write_text(json.dumps(recipe,indent=2)+'\n')
        result['recipe_sha256']=sha(a.output/'recipe.json')
    except Exception as exc:
        result.update(status='failed screen method',error=repr(exc));raise
    finally:
        (a.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({k:v for k,v in result.items()if k not in('source_bindings','arrays','internal_M4_widening_screens')},indent=2))
    raise SystemExit(0 if not failures else 1)


if __name__=='__main__':main()
