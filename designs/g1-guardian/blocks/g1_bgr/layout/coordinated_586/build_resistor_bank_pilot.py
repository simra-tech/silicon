#!/usr/bin/env python3
"""Source-faithful fixed resistor-bank placement and isolated routing pilot."""
import ast
import collections
import json
import math
from pathlib import Path
import build_mos_contact_prototypes as base
pya=base.pya


def snapshot(top, layer):
    result=pya.Region(top.begin_shapes_rec(layer)).dup();result.flatten();return result


def main():
    packpath=base.ROOT/'designs/g1-guardian/review/audits/coordinated-bbox-pack-586-20260922-r1.json'
    assert base.sha(packpath)=='2663805a5180a1961850c1068b0c1c3615c010cd2ec47d38a228d65dde4800cb'
    assert base.sha(base.SOURCE)==base.SOURCE_SHA
    pack=json.loads(packpath.read_text());rows=[r for r in pack['BGR_devices'] if r['name'].startswith('XR')]
    lines={l.split()[0]:l for l in base.SOURCE.read_text().splitlines() if l.startswith('XR')}
    assert len(rows)==len(lines)==399 and all(r['source_line']==lines[r['name']] for r in rows)
    out=base.ROOT/'build/scratch/bgr-resistor-bank-pilot-20260922-r1';out.mkdir(parents=True,exist_ok=False)
    ly=pya.Layout();ly.dbu=.001;top=ly.create_cell('bgr_resistor_bank_pilot')
    lib=pya.Library.library_by_name('SG13_dev','sg13g2')
    pairs={'Activ':(1,0),'GatPoly':(5,0),'PolyRes':(128,0),'Cont':(6,0),'pSD':(14,0),'M1':(8,0),
           'M1pin':(8,2),'M1txt':(8,25),'Via1':(19,0),'M2':(10,0),'M2txt':(10,25),'Via2':(29,0),
           'M3':(30,0),'M3pin':(30,2),'M3txt':(30,25),'Via3':(49,0),'M4':(50,0),'prBoundary':(189,4)}
    layers={k:ly.layer(*v) for k,v in pairs.items()}
    env=dict(pya=pya,lib=lib,ly=ly,top=top,L=layers,CONT=.16,CP=.34,VIA=.19,VP=.42,W3=.3,M2_SEGS=[])
    gen=base.HERE.parent/'g1_bgr_layout.py';assert base.sha(gen)==base.GEN_SHA
    nodes=[n for n in ast.parse(gen.read_text()).body if isinstance(n,ast.FunctionDef) and n.name in base.HELPERS]
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(gen),'exec'),env)
    box,label=env['box'],env['label'];native=[];terminals=[]
    for row in rows:
        f=row['source_line'].split();params=dict(p.split('=',1) for p in f[5:])
        assert params['b']=='0' and params['m']=='1' and f[3]=='vss'
        variant=lib.layout().add_pcell_variant(lib.layout().pcell_id(f[4]),dict(w=params['w'],l=params['l'],b=0,Calculate='R'))
        cell=ly.cell(ly.add_lib_cell(lib,variant));bb=cell.bbox();target=[int(round(v*1000)) for v in row['bbox_um']]
        assert (bb.width(),bb.height())==(target[2]-target[0],target[3]-target[1])
        trans=pya.Trans(target[0]-bb.left,target[1]-bb.bottom)
        top.insert(pya.CellInstArray(cell.cell_index(),trans))
        poly=snapshot(cell,layers['PolyRes']);body=list(poly.each_merged())
        assert len(body)==1
        wb,lb=base.number(params['w'])*1e6,base.number(params['l'])*1e6
        assert abs(body[0].bbox().width()*.001-wb)<1e-8 and abs(body[0].bbox().height()*.001-lb)<1e-8
        heads=sorted(snapshot(cell,layers['M1']).each_merged(),key=lambda p:p.bbox().center().y)
        assert len(heads)==2
        rowindex=row['slot_index']//200;assert rowindex in [0,1]
        for end,head in enumerate(heads):
            hb=head.bbox().transformed(trans);cx=hb.center().x*.001;cy=hb.center().y*.001
            net=f[1+end];role='precision_vss' if row['original']=='XR16' and net=='vss' else net
            terminals.append(dict(instance=row['name'],end=end,net=net,role=role,row=rowindex,
                                  head_center_um=[cx,cy],head_bbox_um=[hb.left*.001,hb.bottom*.001,hb.right*.001,hb.top*.001],
                                  column_x_um=cx+(-.3 if end==0 else .3)))
        native.append(dict(name=row['name'],source_line=row['source_line'],bbox_um=row['bbox_um'],origin_dbu=[trans.disp.x,trans.disp.y],
                           PolyRes_W_um=wb,PolyRes_L_um=lb,source_body='vss'))
    before={k:snapshot(top,layers[k]) for k in ['GatPoly','PolyRes']}
    source_nets=sorted(set(t['net'] for t in terminals)|{'vss'});assert len(source_nets)==40
    lower_heads=[t for t in terminals if t['row']==0]
    bottom_max=max(t['head_center_um'][1] for t in lower_heads if t['end']==0)
    top_min=min(t['head_center_um'][1] for t in lower_heads if t['end']==1)
    first=math.ceil((bottom_max+2)*200)/200
    roles=['vss','precision_vss']+[n for n in source_nets if n!='vss']
    tracks={'vss':first,'precision_vss':first+1.2}
    tracks.update({n:first+2.4+i for i,n in enumerate(roles[2:])})
    assert max(tracks.values())<top_min-1
    vias=[]
    def via(which,x,y):
        lo,hi={'Via1':('M1','M2'),'Via2':('M2','M3'),'Via3':('M3','M4')}[which]
        for metal in [lo,hi]:box(metal,x-.15,y-.42,x+.15,y+.42)
        for off in [-.21,.21]:box(which,x-.095,y+off-.095,x+.095,y+off+.095)
        vias.append(dict(layer=which,center_um=[x,y],cuts=2,axis='y',role='terminal or collector'))
    for role,y in tracks.items():
        width=.8 if role in ['vss','precision_vss'] else .3
        box('M3',16,y-width/2,403,y+width/2)
        net='vss' if role=='precision_vss' else role
        label('M3txt',16.6,y,net)
    for t in terminals:
        x=t['column_x_um'];y=t['head_center_um'][1];target=tracks[t['role']]
        via('Via1',x,y)
        if t['row']==0:
            box('M2',x-.15,min(y,target),x+.15,max(y,target));via('Via2',x,target)
        else:
            via('Via2',x,y);via('Via3',x,y)
            box('M4',x-.15,min(y,target),x+.15,max(y,target));via('Via3',x,target)
    guard=env['guard_ring_p'](18,8.5,402,129,net='vss')
    gx=guard[0];gy=tracks['vss'];via('Via1',gx,gy);via('Via2',gx,gy)
    # Explicit one-point precision/general return join. No reference HBT branch yet.
    for y in [tracks['vss'],tracks['precision_vss']]:via('Via2',16,y)
    box('M2',15.85,tracks['vss'],16.15,tracks['precision_vss'])
    probes=[dict(net=t['net'],layer='M1',point_um=t['head_center_um'],instance=t['instance'],terminal=t['end']) for t in terminals]
    for net in source_nets:
        y=tracks[net];box('M3pin',16.2,y-.15,17,y+.15)
        probes.append(dict(net=net,layer='M3',point_um=[16.6,y],instance='port',terminal=net))
    probes.append(dict(net='vss',layer='M1',point_um=[gx,gy],instance='guard',terminal='body'))
    for k,r in before.items():assert (snapshot(top,layers[k])^r).is_empty()
    bounds=pya.Box(0,0,420000,132000);assert (pya.Region(top.bbox())-pya.Region(bounds)).is_empty()
    top.shapes(layers['prBoundary']).insert(bounds)
    offgrid=[];vertex_count=0
    for info in ly.layer_infos():
        for polygon in snapshot(top,ly.layer(info)).each():
            for point in polygon.each_point_hull():
                vertex_count+=1
                if point.x%5 or point.y%5:offgrid.append([info.layer,info.datatype,point.x,point.y])
            for hole in range(polygon.holes()):
                for point in polygon.each_point_hole(hole):
                    vertex_count+=1
                    if point.x%5 or point.y%5:offgrid.append([info.layer,info.datatype,point.x,point.y])
    # Independent actual-metal graph; labels never merge conductors.
    flat=pya.Layout();flat.dbu=.001;ft=flat.create_cell('metal_audit')
    for key in ['M1','M2','M3','M4','Via1','Via2','Via3']:
        for poly in snapshot(top,layers[key]).each():ft.shapes(flat.layer(*pairs[key])).insert(poly)
    netlist=pya.LayoutToNetlist(pya.RecursiveShapeIterator(flat,ft,[]));netlayers={}
    for key in ['M1','M2','M3','M4']:
        netlayers[key]=netlist.make_layer(flat.layer(*pairs[key]),key);netlist.connect(netlayers[key])
    for key,ends in [('Via1',('M1','M2')),('Via2',('M2','M3')),('Via3',('M3','M4'))]:
        cut=netlist.make_layer(flat.layer(*pairs[key]),key);netlist.connect(cut)
        for end in ends:netlist.connect(cut,netlayers[end])
    netlist.extract_netlist();expected=collections.defaultdict(set);actual=collections.defaultdict(set)
    for p in probes:
        n=netlist.probe_net(netlayers[p['layer']],pya.DPoint(*p['point_um']).to_itype(.001));identity=None if n is None else n.cluster_id
        p['physical_component']=identity;expected[p['net']].add(identity);actual[identity].add(p['net'])
    opens={n:sorted(ids,key=str) for n,ids in expected.items() if None in ids or len(ids)!=1}
    shorts={str(i):sorted(ns) for i,ns in actual.items() if len(ns)!=1}
    gds=out/'bgr_resistor_bank_pilot.gds';ly.write(str(gds))
    cdl=out/'bgr_resistor_bank_pilot.cdl'
    cdl.write_text('.subckt bgr_resistor_bank_pilot '+' '.join(source_nets)+'\n'+'\n'.join('R'+r['source_line'][1:] for r in rows)+'\n.ends bgr_resistor_bank_pilot\n')
    report=dict(status='passed scoped geometry/terminal gate' if not opens and not shorts and not offgrid else 'failed geometry/terminal gate',
                source_sha256=base.SOURCE_SHA,pack_sha256=base.sha(packpath),script_sha256=base.sha(Path(__file__)),
                contract_sha256=base.sha(Path(__file__).with_name('RESISTOR_BANK_PILOT_CONTRACT_20260922.md')),
                native_devices=native,source_net_count=40,tracks_um=tracks,terminal_probes=probes,opens=opens,shorts=shorts,
                via_arrays=vias,native_GatPoly_PolyRes_XOR_dbu2=0,bounds_um=[0,0,420,132],
                polygon_vertices=vertex_count,off_5nm_grid=offgrid,
                GDS_sha256=base.sha(gds),CDL_sha256=base.sha(cdl),reference_HBT_star_branch='not run',
                stock_DRC_LVS='not run',PEX_matching_current_margin='not run',seed='not applicable')
    (out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['status','source_net_count','opens','shorts','GDS_sha256','CDL_sha256']},indent=2))


if __name__=='__main__':main()
