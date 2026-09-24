#!/usr/bin/env python3
"""Isolated source-held macro feed against the frozen actual decap PDN."""
import argparse
import json
import os
from pathlib import Path
import sys
import pya
import networkx as nx

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from place_closed_analog import region, text_records, sha
from audit_placed_decap_domains import physical, identity
from build_interface import METALS, CUTS, box
sys.path.insert(0,str(HERE.parents[2]/'blocks/g1_sense/layout/coordinated_gm4'))
from inventory_power_cutpaths import metal_graph


def bounds(r):
    return [[v*.001 for v in (b.left,b.bottom,b.right,b.top)]
            for b in (p.bbox() for p in r.each())]


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--pdn',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--macro',choices=['bgr','osc','t2f'],default='bgr')
    a=ap.parse_args()
    assert pya.__version__=='0.30.9' and len(os.sched_getaffinity(0))==1
    assert not a.output.exists()
    source=a.pdn/'decap_pdn_core.gds'
    metadata=json.loads((a.pdn/'analysis.json').read_text())
    assert sha(source)==metadata['GDS_sha256']=='88e5911aeaa4f0ae9c3c4712f4f2430563affa32bae0fe6c6c48c142e9611bdb'
    assert metadata['parent_GDS_sha256']=='a001df1aec9d38d18bbf9649b0944f977eb40cb04a5a23f2f49be4f79d2476c5'
    assert metadata['status'].startswith('passed')
    a.output.mkdir(parents=True)
    (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    result=dict(status='running',source_GDS_sha256=sha(source),script_sha256=sha(Path(__file__)),
                macro=a.macro,exploratory_branch_mA=1,source_and_native_geometry='held',canonical_adoption='not run')
    try:
        layout=pya.Layout();layout.read(str(source));top=layout.top_cell()
        assert layout.dbu==.001
        original={str(i):region(layout,top,i)for i in layout.layer_infos()}
        texts=text_records(layout,top)
        native={l:region(layout,top,pya.LayerInfo(l,0))for l in METALS+tuple(CUTS)}
        supply='VDDA'if a.macro=='bgr'else'VDD'
        routes={n:{l:pya.Region()for l in native}for n in (supply,'VSS')}
        def put(n,l,r):routes[n][l]+=r
        def wire(n,l,x1,y1,x2,y2,w):
            assert x1==x2 or y1==y2
            put(n,l,box(min(x1,x2)-w/2,min(y1,y2)-w/2,max(x1,x2)+w/2,max(y1,y2)+w/2))
        arrays=[]
        def array(n,l,x,y,nx,ny):
            lo,hi=CUTS[l]
            cut,pitch,enc,limit=(.19,.5,.055,.4)if l<100 else((.42,.84,.12,1.4)if l==125 else(.9,1.96,.65,10.))
            sx=(nx-1)*pitch+cut;sy=(ny-1)*pitch+cut
            for i in range(nx):
                for j in range(ny):
                    cx=x+(i-(nx-1)/2)*pitch;cy=y+(j-(ny-1)/2)*pitch
                    put(n,l,box(cx-cut/2,cy-cut/2,cx+cut/2,cy+cut/2))
            landings=[]
            for metal in (lo,hi):
                enclosure=.45 if l==125 and metal==126 else enc
                minimum=1.64 if metal==126 else 2 if metal==134 else .2
                wx=max(sx+2*enclosure,minimum);wy=max(sy+2*enclosure,minimum)
                b=[x-wx/2,y-wy/2,x+wx/2,y+wy/2]
                put(n,metal,box(*b));landings.append(dict(layer=metal,bbox_um=b))
            arrays.append(dict(net=n,layer=l,center_um=[x,y],nx=nx,ny=ny,cuts=nx*ny,
                               landings=landings,half_table_mA=nx*ny*limit*.5,
                               one_cut_lost_half_table_mA=(nx*ny-1)*limit*.5))
        if a.macro=='bgr':
            array(supply,125,743.4,878,2,2)
            array(supply,133,743.4,878,1,2)
            wire(supply,134,743.4,878,743.4,922,2.2)
            wire('VSS',67,749.65,873,749.65,875.975,1.1)
            wire('VSS',67,749.65,875.975,736.8,875.975,1.1)
            wire('VSS',67,736.8,875.975,736.8,873,1.1)
            array('VSS',125,736.8,873,2,2)
            cellname='g1_bgr_candidate'
            native_points=[(supply,67,743.4,878),('VSS',67,749.65,873)]
            root_points=[('VSS',126,736.8,873)]
            handoffs={supply:(134,[743400,922000]),'VSS':(126,[736800,873000])}
        elif a.macro=='osc':
            wire(supply,30,772,1089.57,750,1089.57,1.1)
            for n,x,y in [(supply,750,1089.57),('VSS',774,954)]:
                array(n,49,x,y,4,3);array(n,66,x,y,4,3);array(n,125,x,y,2,2)
            cellname='retained_g1_osc'
            native_points=[(supply,30,772,1089.57),('VSS',30,774,954)]
            root_points=[(supply,126,750,1089.57),('VSS',126,774,954)]
            handoffs={supply:(126,[750000,1089570]),'VSS':(126,[774000,954000])}
        else:
            array(supply,49,1044,1047.6,4,3)
            wire(supply,50,1044,1047.6,1061.92,1047.6,1.1)
            array(supply,66,1061.92,1047.6,4,3)
            array(supply,125,1061.92,1047.6,2,2)
            array('VSS',49,1039.2,954.3,4,3)
            array('VSS',66,1039.2,954.3,4,3)
            array('VSS',125,1039.2,954.3,2,2)
            cellname='retained_g1_t2f'
            native_points=[(supply,30,1044,1047.6),('VSS',30,1039.2,954.3)]
            root_points=[(supply,126,1061.92,1047.6),('VSS',126,1039.2,954.3)]
            handoffs={supply:(126,[1061920,1047600]),'VSS':(126,[1039200,954300])}
        allowed={n:{l:pya.Region()for l in METALS}for n in routes}
        # Trace every actual macro native component, so existing same-net cuts
        # are classified electrically rather than by a same-layer bbox guess.
        placements=[i for i in top.each_inst()if i.cell.name==cellname]
        assert len(placements)==1
        placed=placements[0]
        graph,components,oldcuts,hit=metal_graph(placed.cell)
        owned={}
        for n,l,x,y in native_points:
            point=placed.trans.inverted()*pya.DPoint(x,y).to_itype(.001)
            nodes=hit(l,point);assert len(nodes)==1
            owned[n]=nx.node_connected_component(graph,nodes[0])
            for node,poly in components.items():
                if node in owned[n]:allowed[n][graph.nodes[node]['layer']].insert(poly.transformed(placed.trans))
        assert not(owned[supply]&owned['VSS'])
        for n,l,x,y in root_points:
            at=box(x-.001,y-.001,x+.001,y+.001)
            own=native[l].interacting(at)
            assert not own.is_empty(),(n,l,'missing actual landing')
            allowed[n][l]+=own
        checks=[];failures=[]
        for n,layers in routes.items():
            other='VSS'if n==supply else supply
            for l in METALS:
                margin=.4 if l<100 else 2 if l==126 else 5
                foreign=native[l]-allowed[n][l]
                overlap=layers[l]&foreign
                proximity=layers[l]&foreign.sized(round(margin*1000))
                inter=layers[l]&routes[other][l].sized(round(margin*1000))
                row=dict(net=n,layer=l,margin_um=margin,overlap_um2=overlap.area()*1e-6,
                         proximity_um2=proximity.area()*1e-6,proximity_bbox_um=bounds(proximity),
                         other_route_proximity_um2=inter.area()*1e-6)
                checks.append(row)
                if not overlap.is_empty()or not proximity.is_empty()or not inter.is_empty():failures.append(row)
            for l,(lo,hi)in CUTS.items():
                cuts=layers[l]
                assert(cuts-(layers[lo]+allowed[n][lo])).is_empty()
                assert(cuts-(layers[hi]+allowed[n][hi])).is_empty()
                # No new metal may capture an existing foreign via landing.
                owncuts=native[l]&allowed[n][lo]&allowed[n][hi]
                foreigncuts=native[l]-owncuts
                touch=(layers[lo]+layers[hi])&foreigncuts
                oldnear=cuts&native[l].sized(420 if l==125 else 1060 if l==133 else 290)
                row=dict(net=n,cut_layer=l,old_cut_contact_um2=touch.area()*1e-6,
                         old_cut_proximity_um2=oldnear.area()*1e-6,contact_bbox_um=bounds(touch))
                checks.append(row)
                if not touch.is_empty()or not oldnear.is_empty():failures.append(row)
        result.update(arrays=arrays,checks=checks,failures=failures)
        assert not failures,failures
        overlay=pya.Layout();overlay.dbu=.001;oc=overlay.create_cell(a.macro+'_power_interface_NOT_ADOPTED')
        for n,layers in routes.items():
            for l,r in layers.items():
                for p in r.merged().each():
                    top.shapes(layout.layer(l,0)).insert(p)
                    oc.shapes(overlay.layer(l,0)).insert(p)
        output=a.output/'candidate_core.gds';layout.write(str(output))
        overlay.write(str(a.output/'power_overlay.gds'))
        saved=pya.Layout();saved.read(str(output));st=saved.top_cell()
        assert text_records(saved,st)==texts
        for i in saved.layer_infos():
            expected=original.get(str(i),pya.Region())
            if i.datatype==0 and i.layer in native:expected=expected+routes[supply][i.layer]+routes['VSS'][i.layer]
            assert(region(saved,st,i)^expected).is_empty(),str(i)
        network,metals=physical(saved,st)
        points={'macro_'+n:(l,[round(x*1000),round(y*1000)])for n,l,x,y in native_points}
        points.update({'handoff_'+n:value for n,value in handoffs.items()})
        points.update(core_vdd=(134,[395000,354660]),core_vss=(134,[507000,334660]))
        if a.macro=='t2f':points['isolated_macro_VDDA']=(30,[1044000,1054300])
        probes={n:identity(network,metals[l],xy)for n,(l,xy)in points.items()}
        assert all(v is not None for v in probes.values())
        assert probes['macro_'+supply]==probes['handoff_'+supply]
        assert probes['macro_VSS']==probes['handoff_VSS']==probes['core_vss']
        if a.macro=='bgr':assert len({probes[n]for n in ('macro_VDDA','macro_VSS','core_vdd')})==3
        else:assert probes['macro_VDD']==probes['core_vdd']!=probes['core_vss']
        if a.macro=='t2f':assert probes['isolated_macro_VDDA']not in(probes['core_vdd'],probes['core_vss'])
        result.update(status='passed isolated '+a.macro.upper()+' overlay geometry and scoped physical binding',
                      GDS_sha256=sha(output),overlay_sha256=sha(a.output/'power_overlay.gds'),probes=probes,
                      source_polygon_text_preservation='passed',new_bridge_half_table_mA=1.1,
                      not_run=['stock DRC','native neighbouring stock DRC','one-cut-loss graph',
                               'signal-route context','current sharing/IR/EM/PVT','adoption']+
                              (['VDDA handoff to pad07']if a.macro in('bgr','t2f')else[]),
                      not_applicable=['VDDA handoff to pad07']if a.macro=='osc'else[])
    except Exception as exc:
        result.update(status='failed isolated '+a.macro.upper()+' overlay gate',error=repr(exc))
        raise
    finally:
        (a.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({k:v for k,v in result.items()if k not in ('checks','arrays')},indent=2),flush=True)


if __name__=='__main__':main()
