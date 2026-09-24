#!/usr/bin/env python3
"""Add source-bound three-instance LS feeds; flattened physical identities only."""
import argparse
import json
import os
from pathlib import Path
import sys
import networkx as nx
import pya

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from place_closed_analog import region,text_records,sha
from audit_placed_decap_domains import physical,identity
from build_interface import METALS,CUTS,box
sys.path.insert(0,str(HERE.parents[2]/'blocks/g1_sense/layout/coordinated_gm4'))
from inventory_power_cutpaths import metal_graph


def flat_physical(layout,top):
    flat=pya.Layout();flat.dbu=.001;cell=flat.create_cell('flat_ls_interface_verification')
    for layer in METALS+tuple(CUTS):
        for poly in region(layout,top,pya.LayerInfo(layer,0)).each():
            cell.shapes(flat.layer(layer,0)).insert(poly)
    net,metals=physical(flat,cell)
    return flat,net,metals


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in('pdn','inventory','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();assert not a.output.exists()and len(os.sched_getaffinity(0))==1 and pya.__version__=='0.30.9'
    source=a.pdn/'decap_pdn_core.gds';meta=json.loads((a.pdn/'analysis.json').read_text())
    inv=json.loads(a.inventory.read_text());assert inv['status'].startswith('passed')
    assert sha(source)==meta['GDS_sha256']=='88e5911aeaa4f0ae9c3c4712f4f2430563affa32bae0fe6c6c48c142e9611bdb'
    canonical=HERE.parents[2]/'blocks/g1_ctrl/ls/layout/g1_ls_up.gds'
    assert sha(canonical)=='85de277ca1c2de41fa59e577db1d6d7633edddb24abf3b6d57e6787afd335546'
    terminals=[r for r in inv['terminals']if r['instance']in('i_core.u_ls_en','i_core.u_ls_r4','i_core.u_ls_mode')]
    assert len(terminals)==9
    assert all(r['net']=={'vdd':'VDD','vdda':'VDDA','vss':'VSS'}[r['pin']]for r in terminals)
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    result=dict(status='running',macro='ls',source_GDS_sha256=sha(source),source_LS_GDS_sha256=sha(canonical),
                inventory_sha256=sha(a.inventory),script_sha256=sha(Path(__file__)),
                exploratory_branch_mA=.1,exploratory_three_branch_aggregate_mA=.3)
    try:
        ly=pya.Layout();ly.read(str(source));top=ly.top_cell()
        old={str(i):region(ly,top,i)for i in ly.layer_infos()};texts=text_records(ly,top)
        native={l:region(ly,top,pya.LayerInfo(l,0))for l in METALS+tuple(CUTS)}
        routes={n:{l:pya.Region()for l in native}for n in('VDD','VDDA','VSS')}
        allowed={n:{l:pya.Region()for l in METALS}for n in routes}
        arrays=[]
        def array(net,layer,x,y,nx,ny):
            lower,upper=CUTS[layer]
            size,pitch,enclosure=(.19,.42,.055)if layer<100 else(.42,.84,.12)
            for i in range(nx):
                for j in range(ny):
                    cx=x+(i-(nx-1)/2)*pitch;cy=y+(j-(ny-1)/2)*pitch
                    routes[net][layer]+=box(cx-size/2,cy-size/2,cx+size/2,cy+size/2)
            for metal in(lower,upper):
                enc=.45 if metal==126 else enclosure
                width=max((nx-1)*pitch+size+2*enc,1.64 if metal==126 else .2)
                height=max((ny-1)*pitch+size+2*enc,1.64 if metal==126 else .2)
                routes[net][metal]+=box(x-width/2,y-height/2,x+width/2,y+height/2)
            arrays.append(dict(net=net,layer=layer,center_um=[x,y],nx=nx,ny=ny,cuts=nx*ny))
        def wire(net,x1,x2,y):routes[net][30]+=box(x1-.4,y-.4,x2+.4,y+.4)
        instance_records=[];pins={}
        placements=[i for i in top.each_inst()if i.cell.name=='retained_g1_ls_up']
        assert len(placements)==3
        graph,components,cuts,hit=metal_graph(placements[0].cell)
        for terminal in terminals:
            assert len(terminal['windows'])==1
            window=terminal['windows'][0];assert window['layer']==8
            pinbox=pya.Box(*window['bbox']);point=pinbox.center()
            matches=[]
            for inst in placements:
                nodes=hit(8,inst.trans.inverted()*point)
                if len(nodes)==1:matches.append((inst,nodes[0]))
            assert len(matches)==1,(terminal['instance'],terminal['pin'],matches)
            inst,node=matches[0];net=terminal['net'];owned=nx.node_connected_component(graph,node)
            for identifier,poly in components.items():
                if identifier in owned:allowed[net][graph.nodes[identifier]['layer']].insert(poly.transformed(inst.trans))
            # Deliberate access points stay inside the actual source pin window.
            x=(734 if terminal['pin']!='vdda' else 739.3)+({'i_core.u_ls_en':0,'i_core.u_ls_r4':20,'i_core.u_ls_mode':40}[terminal['instance']])
            y={'vdd':500.,'vdda':501.4,'vss':490.575}[terminal['pin']]
            access=pya.DPoint(x,y).to_itype(.001);assert pinbox.contains(access)
            found=hit(8,inst.trans.inverted()*access);assert len(found)==1 and found[0]in owned
            for layer in(19,29):array(net,layer,x,y,3,1)
            key=terminal['instance']+'.'+terminal['pin'];pins[key]=(net,[access.x,access.y])
            instance_records.append(dict(instance=terminal['instance'],pin=terminal['pin'],net=net,transform=str(inst.trans),access_dbu=[access.x,access.y]))
        wire('VDD',734,774,500);wire('VSS',734,774,490.575);wire('VDDA',739.3,783,501.4)
        for net,x,y in [('VDD',750,500),('VSS',774,490.575)]:
            array(net,49,x,y,3,1);array(net,66,x,y,3,1);array(net,125,x,y,2,2)
            landing=native[126].interacting(box(x-.001,y-.001,x+.001,y+.001));assert not landing.is_empty()
            allowed[net][126]+=landing
        assert sum(r['cuts']for r in arrays)==74
        checks=[];failures=[]
        for net,layers in routes.items():
            for layer in METALS:
                gap=.4 if layer<100 else 2 if layer==126 else 5
                foreign=native[layer]-allowed[net][layer]
                near=layers[layer]&foreign.sized(round(gap*1000))
                inter=pya.Region()
                for other in routes:
                    if other!=net:inter+=layers[layer]&routes[other][layer].sized(round(gap*1000))
                row=dict(net=net,layer=layer,foreign_proximity_um2=near.area()*1e-6,other_route_proximity_um2=inter.area()*1e-6,
                         bboxes_um=[[v*.001 for v in(b.left,b.bottom,b.right,b.top)]for b in(q.bbox()for q in near.each())])
                checks.append(row)
                if not near.is_empty()or not inter.is_empty():failures.append(row)
            for layer,(lower,upper)in CUTS.items():
                owncuts=native[layer]&allowed[net][lower]&allowed[net][upper]
                touch=(layers[lower]+layers[upper])&(native[layer]-owncuts)
                near=layers[layer]&native[layer].sized(420 if layer==125 else 1060 if layer==133 else 290)
                assert(layers[layer]-(layers[lower]+allowed[net][lower])).is_empty()
                assert(layers[layer]-(layers[upper]+allowed[net][upper])).is_empty()
                row=dict(net=net,cut_layer=layer,foreign_cut_capture_um2=touch.area()*1e-6,existing_cut_proximity_um2=near.area()*1e-6)
                checks.append(row)
                if not touch.is_empty()or not near.is_empty():failures.append(row)
        result.update(checks=checks,failures=failures,arrays=arrays,source_terminals=instance_records)
        assert not failures,failures
        flat,before_net,before_metals=flat_physical(ly,top)
        before={key:identity(before_net,before_metals[8],point)for key,(net,point)in pins.items()}
        assert None not in before.values()and len(set(before.values()))==9
        overlay=pya.Layout();overlay.dbu=.001;oc=overlay.create_cell('ls_power_interface_NOT_ADOPTED')
        for layers in routes.values():
            for layer,r in layers.items():
                for poly in r.merged().each():
                    top.shapes(ly.layer(layer,0)).insert(poly);oc.shapes(overlay.layer(layer,0)).insert(poly)
        out=a.output/'candidate_core.gds';ly.write(str(out));overlay.write(str(a.output/'power_overlay.gds'))
        saved=pya.Layout();saved.read(str(out));st=saved.top_cell();assert text_records(saved,st)==texts
        for info in saved.layer_infos():
            expected=old.get(str(info),pya.Region())
            if info.datatype==0 and info.layer in native:
                for layers in routes.values():expected+=layers[info.layer]
            assert(region(saved,st,info)^expected).is_empty()
        flat,after_net,after_metals=flat_physical(saved,st)
        after={key:identity(after_net,after_metals[8],point)for key,(net,point)in pins.items()}
        roots={'VDD':identity(after_net,after_metals[134],[395000,354660]),
               'VSS':identity(after_net,after_metals[134],[507000,334660]),
               'VDDA':identity(after_net,after_metals[30],[783000,501400])}
        assert None not in roots.values()and len(set(roots.values()))==3
        assert all(after[key]==roots[net]for key,(net,point)in pins.items())
        result.update(status='passed source-held three-instance LS feeds and flat pin binding',GDS_sha256=sha(out),
            overlay_sha256=sha(a.output/'power_overlay.gds'),flat_before=before,flat_after=after,root_probes=roots,
            not_run=['VDDA handoff to pad','stock/cut-open/context checks','actual transient/source-neck/return-current qualification',
                     'fullchip LVS/PEX/PVT/IR/EM','adoption'])
    except Exception as exc:
        result.update(status='failed LS feed geometry',error=repr(exc));raise
    finally:
        (a.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({k:v for k,v in result.items()if k not in('checks','arrays')},indent=2))


if __name__=='__main__':main()
