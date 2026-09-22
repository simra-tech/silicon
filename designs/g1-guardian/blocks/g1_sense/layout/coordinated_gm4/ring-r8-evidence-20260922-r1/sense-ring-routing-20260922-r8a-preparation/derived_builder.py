#!/usr/bin/env python3
"""Isolated native-preserving SENSE power routing; all signoff remains explicit."""
import argparse,copy,json,os
from pathlib import Path
import networkx as nx
from build_native_prototypes import pya,snapshot as native_snapshot,sha
from inventory_power_cutpaths import metal_graph,METALS,CUTS

HERE=Path(__file__).resolve().parent
SOURCE_SHA='baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877'
R5_SHA='6609a77884a0009924422bf9871ea699e2393c8988412e1b000057cf3448beda'
PORTS={'vdd':(134,383.,218.),'vss':(126,383.,226.)}

def snapshot(cell,layer,datatype=0):
    if datatype==0:return native_snapshot(cell,layer)
    iterator=cell.begin_shapes_rec(cell.layout().layer(layer,datatype))
    return pya.Region([pya.Polygon(p)for p in pya.Region(iterator).each()]).merged()

def full_nets_upper(cell,probes):
    # Independent extension of the frozen connectivity algorithm, not a deck edit.
    flat=pya.Layout();flat.dbu=.001;top=flat.create_cell('power_network')
    metals=(8,10,30,50,67,126,134)
    cuts={6:(501,5,8),19:(8,10),29:(10,30),49:(30,50),66:(50,67),125:(67,126),133:(126,134)}
    regions={layer:snapshot(cell,layer) for layer in (1,5)+metals+tuple(cuts)};regions[501]=regions[1]-regions[5]
    for layer,region in regions.items():
        if layer!=1:
            for polygon in region.each():top.shapes(flat.layer(layer,0)).insert(polygon)
    network=pya.LayoutToNetlist(pya.RecursiveShapeIterator(flat,top,[]));layers={}
    for layer in (501,5)+metals:
        layers[layer]=network.make_layer(flat.layer(layer,0),'L'+str(layer));network.connect(layers[layer])
    for layer,joined in cuts.items():
        cut=network.make_layer(flat.layer(layer,0),'V'+str(layer));network.connect(cut)
        for other in joined:network.connect(cut,layers[other])
    network.extract_netlist();expected={};actual={}
    for q in probes:
        net=network.probe_net(layers[q['layer']],pya.DPoint(*q['point_um']).to_itype(.001))
        identity=None if net is None else net.cluster_id;q['physical_net']=identity
        expected.setdefault(q['net'],set()).add(identity);actual.setdefault(identity,set()).add(q['net'])
    opens={n:sorted(v,key=str)for n,v in expected.items()if None in v or len(v)!=1}
    shorts={str(n):sorted(v)for n,v in actual.items()if len(v)!=1}
    return dict(status='passed'if not opens and not shorts else'failed',opens=opens,shorts=shorts,probes=probes,source_net_count=len(expected))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in('candidate','coverage','inventory','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();assert os.sched_getaffinity(0)=={7} and not a.output.exists() and pya.__version__=='0.30.9'
    source=HERE.parents[1]/'reports/resume-server-20260922/gm4comp3-qualified-source.spice'
    assert sha(source)==SOURCE_SHA and sha(a.candidate)==R5_SHA
    coverage=json.loads(a.coverage.read_text());assert coverage['source_net_count']==134
    inventory=json.loads(a.inventory.read_text());assert inventory['GDS_sha256']==R5_SHA
    a.output.mkdir(parents=True);(a.output/'builder_snapshot.py').write_bytes(Path(__file__).read_bytes())
    result=dict(status='running isolated power revision',source_sha256=SOURCE_SHA,baseline_GDS_sha256=R5_SHA,
                script_sha256=sha(Path(__file__)),coverage_sha256=sha(a.coverage),inventory_sha256=sha(a.inventory),
                exploratory_envelope_mA=2.,engineering_utilization=.5,stock_checks='not run',PEX='not run',adoption='not run',
                current_scope='105C / 11 years tabulated limits only; actual branch allocation, 125C and pulse qualification not run')
    try:
        ly=pya.Layout();ly.read(str(a.candidate));cell=ly.cell('g1_sense_physical')
        frozen={ly.get_info(li).to_s():snapshot(cell,ly.get_info(li).layer,ly.get_info(li).datatype)
                for li in ly.layer_indexes()}
        graph,components,cuts,hit=metal_graph(cell)
        owned={};added={net:{layer:pya.Region()for layer in METALS}for net in PORTS}
        for net in PORTS:
            origin=hit(50,pya.Point(384000,184000 if net=='vdd'else 184800))[0]
            own=nx.node_connected_component(graph,origin)
            owned[net]={layer:pya.Region([polygon for node,polygon in components.items()if node in own and graph.nodes[node]['layer']==layer]) for layer in METALS}
        foreign={net:{layer:snapshot(cell,layer)-owned[net][layer] for layer in METALS}for net in PORTS}
        spacing={8:180,10:240,30:240,50:240,67:240,126:1640,134:2000}
        def region_box(x1,y1,x2,y2):return pya.Region(pya.DBox(min(x1,x2),min(y1,y2),max(x1,x2),max(y1,y2)).to_itype(.001))
        def put(layer,region,net=None):
            for polygon in region.each():cell.shapes(ly.layer(layer,0)).insert(polygon)
            if net is not None:added[net][layer]+=region
        def box(layer,x1,y1,x2,y2,net=None):put(layer,region_box(x1,y1,x2,y2),net)
        def wire(layer,points,width,net):
            if layer==134:width=max(width,2.2)
            for (x1,y1),(x2,y2)in zip(points,points[1:]):
                assert x1==x2 or y1==y2
                box(layer,min(x1,x2)-width/2,min(y1,y2)-width/2,max(x1,x2)+width/2,max(y1,y2)+width/2,net)
        arrays=[]
        def array(layer,x,y,nx_,ny_,net):
            lower,upper,limit=CUTS[layer];cut=.19 if layer<100 else(.42 if layer==125 else .9)
            pitch=.5 if layer<100 else(.84 if layer==125 else 1.96)
            # Minimum end enclosure plus manufacturing-grid margin; upper metals retain width rules.
            enc=.055 if layer<100 else(.12 if layer==125 else .65)
            sx=(nx_-1)*pitch+cut;sy=(ny_-1)*pitch+cut
            for i in range(nx_):
                for j in range(ny_):
                    cx=x+(i-(nx_-1)/2)*pitch;cy=y+(j-(ny_-1)/2)*pitch
                    box(layer,cx-cut/2,cy-cut/2,cx+cut/2,cy+cut/2)
            for metal in(lower,upper):
                extra=.45 if layer==125 and metal==126 else enc
                wx=max(sx+2*extra,1.64 if metal==126 else(2. if metal==134 else .2))
                wy=max(sy+2*extra,1.64 if metal==126 else(2. if metal==134 else .2))
                box(metal,x-wx/2,y-wy/2,x+wx/2,y+wy/2,net)
            arrays.append(dict(net=net,cut_layer=layer,center_um=[x,y],nx=nx_,ny=ny_,cuts=nx_*ny_,tabulated_mA=nx_*ny_*limit))
        # Separate-layer backbones avoid a VDD/VSS flyover crossing at buffer escapes.
        wire(134,[(40,172),(383,172),(383,218)],2.,'vdd')
        wire(126,[(14,178),(378,178),(378,226),(383,226)],2.,'vss')
        def upper_pod(x,y,net):
            array(125,x,y,2,2,net)
            if net=='vdd':array(133,x,y,2,1,net)
        # Distributed main M4 collectors: ten parallel Via4 cuts per access, narrow Y footprint.
        for net,xs,y in [('vdd',(40.,54.,180.,200.,220.),145.),('vss',(150.,190.,210.),145.8)]:
            for x in xs:
                array(66,x,y,10,1,net);wire(67,[(x,y),(x,149.)],2.,net);upper_pod(x,149.,net)
                wire(134 if net=='vdd'else 126,[(x,149.),(x,172. if net=='vdd'else 178.)],2.,net)
        # Independent core feeds bypass all three legacy single-cut common stages.
        for net,x,y,escape in [('vdd',230.2,110.,225.),('vss',231.4,100.,215.)]:
            array(49,x,y,1,12,net);wire(50,[(x,y),(escape,y)],2.,net)
            array(66,escape,y,4,3,net);upper_pod(escape,y,net)
            wire(134 if net=='vdd'else 126,[(escape,y),(escape,172. if net=='vdd'else 178.)],2.,net)
        # Both buffers receive direct native M3 feeds below the old single-cut edge escapes.
        for dx in(0.,120.):
            for net,x,y in [('vdd',7.3+dx,220.),('vss',9.1+dx,225.)]:
                array(49,x,y,4,3,net)
                escape=40. if net=='vdd' and dx==0. else x
                if escape!=x:
                    bridge=region_box(x-1,y-1,escape+1,y+1)
                    assert (bridge.sized(239)&foreign[net][50]).is_empty(), 'M4 bridge foreign-net clearance'
                    wire(50,[(x,y),(escape,y)],2.,net)
                array(66,escape,y,4,3,net)
                upper_pod(escape,y,net)
                if net=='vdd':
                    stem=40. if dx==0. else 3.+dx
                    wire(134,[(escape,y),(stem,y),(stem,172.)],2.,net)
                else:wire(126,[(x,y),(14.+dx,y),(14.+dx,178.)],2.,net)
        # Join the same-net 220 um collector landing to the 225 um core stem;
        # their prior 1.92 um notch failed the unchanged 2 um TM2 spacing rule.
        box(134,217.92,147.9,226.1,150.1,'vdd')
        # Additional row at each left buffer VDD bar/trunk crossing. Existing
        # two Via3 cuts plus a body-tap alternate were a 0.6 mA via-only
        # engineering bottleneck; do not rely on the body-tap route for load.
        for dx in(0.,120.):
            for x in(7.05+dx,7.55+dx):
                box(49,x-.095,230.38-.095,x+.095,230.38+.095)
            for layer in(30,50):box(layer,6.9+dx,229.73,7.7+dx,230.53,'vdd')
            arrays.append(dict(net='vdd',cut_layer=49,center_um=[7.3+dx,230.38],nx=2,ny=1,cuts=2,
                tabulated_mA=.8,role='additional buffer bar row, existing row retained'))
        # Add a second local cut only when both metal landings and neighboring cuts clear.
        redundancies=[];deferred=[]
        for row in inventory['rows']:
            net=row['net']
            for old in row['critical_single_cuts']:
                layer=old['layer'];lower,upper,_=CUTS[layer];x,y=old['center_um'];selected=None
                if layer>=100:continue
                for dx,dy in((.5,0),(-.5,0),(0,.5),(0,-.5),(.5,.5),(-.5,.5),(.5,-.5),(-.5,-.5)):
                    nx_,ny_=round(x+dx,3),round(y+dy,3)
                    cut=region_box(nx_-.095,ny_-.095,nx_+.095,ny_+.095)
                    if not(snapshot(cell,layer)&cut.sized(295)).is_empty():continue
                    landing=region_box(min(x,nx_)-.15,min(y,ny_)-.15,max(x,nx_)+.15,max(y,ny_)+.15)
                    if any(not((foreign[net][metal]+added['vss'if net=='vdd'else'vdd'][metal])&landing.sized(spacing[metal]-1)).is_empty()for metal in(lower,upper)):continue
                    put(layer,cut)
                    for metal in(lower,upper):put(metal,landing,net)
                    selected=dict(original=old,new_center_um=[nx_,ny_]);redundancies.append(selected);break
                if selected is None:deferred.append(old)
        # Only external supply annotations move; source ports and all signal pins remain exact.
        erased=[]
        for shape in list(cell.shapes(ly.layer(50,25)).each()):
            if shape.is_text()and shape.text.string in PORTS:erased.append(shape.text.string);shape.delete()
        assert sorted(erased)==['vdd','vss']
        for shape in list(cell.shapes(ly.layer(50,2)).each()):
            if shape.is_box()and shape.box in(pya.Box(383000,183800,385000,184200),pya.Box(383000,184600,385000,185000)):shape.delete()
        port_map=[]
        probes=copy.deepcopy(coverage['complete_physical_graph']['probes'])
        for net,(layer,x,y)in PORTS.items():
            box(layer,x-2,y-2,x+2,y+2,net);cell.shapes(ly.layer(layer,2)).insert(pya.DBox(x-2,y-2,x+2,y+2).to_itype(.001))
            cell.shapes(ly.layer(layer,25)).insert(pya.Text(net,pya.Trans(pya.Point(round(x*1000),round(y*1000)))))
            old_y=184. if net=='vdd'else 184.8
            matching=[q for q in probes if q['device']=='pin'and q['terminal']=='anchor'and q['layer']==50 and q['net']==net and abs(q['point_um'][0]-384)<1e-8 and abs(q['point_um'][1]-old_y)<1e-8]
            assert len(matching)==1;matching[0].update(layer=layer,point_um=[x,y])
            port_map.append(dict(net=net,old=dict(layer=50,point_um=[384,old_y]),new=dict(layer=layer,point_um=[x,y],bbox_um=[x-2,y-2,x+2,y+2])))
        gds=a.output/'g1_sense_physical.gds';ly.write(str(gds))
        saved=pya.Layout();saved.read(str(gds));saved_cell=saved.cell('g1_sense_physical')
        tm2=snapshot(saved_cell,134);tv2=snapshot(saved_cell,133)
        assert not tm2.is_empty() and tm2.bbox().left>=36160
        assert not tv2.is_empty() and tv2.bbox().left>=36160
        result['ring_keepout']=dict(status='passed',required_min_local_x_um=36.16,
            actual_TM2_min_local_x_um=tm2.bbox().left*.001,
            actual_TopVia2_min_local_x_um=tv2.bbox().left*.001,
            R90_translation_um=[1031,331],global_TM2_min_y_um=331+tm2.bbox().left*.001,
            nearest_ring_top_y_um=362.16,spacing_um=331+tm2.bbox().left*.001-362.16,
            scope='All saved TM2 and TopVia2 geometry; parent full-core check remains separate')
        allowed=set(METALS)|set(CUTS);native=[]
        for li in ly.layer_indexes():
            info=ly.get_info(li)
            if info.layer in allowed and info.datatype in(0,2,25):continue
            original=frozen.get(info.to_s(),pya.Region());delta=original^snapshot(cell,info.layer,info.datatype)
            native.append(dict(layer=info.to_s(),XOR_um2=delta.area()*1e-6));assert delta.is_empty(),info.to_s()
        network=full_nets_upper(cell,probes);result.update(GDS_sha256=sha(gds),native_nondrawing_XOR=native,terminal_audit=network,
            arrays=arrays,local_redundancies=redundancies,local_deferred=deferred,external_port_map=port_map)
        (a.output/'preaudit.json').write_text(json.dumps(result,indent=2)+'\n')
        assert network['status']=='passed'and network['source_net_count']==134,dict(opens=network['opens'],shorts=network['shorts'])
        b=cell.bbox();assert b.left>=0 and b.bottom>=0 and b.right<=385000 and b.top<=240000,str(b)
        for li in ly.layer_indexes():
            for polygon in snapshot(cell,ly.get_info(li).layer,ly.get_info(li).datatype).each():
                for point in polygon.each_point_hull():assert point.x%5==point.y%5==0
        result.update(status='passed isolated power routing geometry gate',bbox_um=[v*.001 for v in(b.left,b.bottom,b.right,b.top)],source_unchanged=sha(source)==SOURCE_SHA)
    except Exception as exc:
        result.update(status='failed isolated power routing geometry gate',exception_type=type(exc).__name__,detail=str(exc))
        (a.output/'failure.json').write_text(json.dumps(result,indent=2)+'\n');raise
    (a.output/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items()if k not in('terminal_audit','local_redundancies','local_deferred','native_nondrawing_XOR','arrays')},indent=2))

if __name__=='__main__':main()
