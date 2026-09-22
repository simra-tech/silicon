#!/usr/bin/env python3
"""One fixed-position HBT bank; geometry/graph audits only, no stock tool."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import pya

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
LAYOUT = HERE.parent
SOURCE = LAYOUT.parent/'sim/qualification/candidates/bgr_loop24_qref4_r253p465_hv06/bgr_loop24_qref4_r253p465_hv06.spice'
PACK = ROOT/'designs/g1-guardian/review/audits/coordinated-bbox-pack-586-20260922-r1.json'
HBT = ROOT/'build/scratch/bgr-hbt-contact-prototypes-20260922-r1'
MOS = ROOT/'build/scratch/bgr-mos-contact-prototypes-20260922-r2'
CONTROL = ROOT/'build/scratch/bgr-hbt-return-controls-20260922-r2'
RBANK = ROOT/'build/scratch/bgr-resistor-bank-pilot-20260922-r2'
PDK = Path('/foss/pdks/ihp-sg13g2')
PINNED = {
    SOURCE:'586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b',
    PACK:'2663805a5180a1961850c1068b0c1c3615c010cd2ec47d38a228d65dde4800cb',
    HBT/'manifest.json':'bcdb1f01f4287db750935896756b5947db22898612a9bb77b229f6f0553d4fc2',
    MOS/'manifest.json':'0d2e3e723a07d1474180ab4691ee0f1244884bb62b6583bebb7bf7fa300f0fc7',
    CONTROL/'controls.json':'9ab1a1f51551c8969a589c62a9b187258fbb2e6adabc3c5a3ce206d1751721da',
    CONTROL/'bank_source_placement_ledger.json':'3f3782081e28daa32f70dffe07d4ab921fac662df25cd565e11194d1248c7ea8',
    RBANK/'bgr_resistor_bank_pilot.gds':'4019838faa0efb2b5038e69f9652c6e52eb60ab070ac964f2d39f72af29e0d17',
    RBANK/'manifest.json':'58b2f809e73e4359ec5adfb78a49840e817c49e38c70db977a5eb3b7f43a95c9',
}
PAIRS = {'M1':(8,0),'Via1':(19,0),'M2':(10,0),'Via2':(29,0),'M3':(30,0),'Via3':(49,0),'M4':(50,0),
         'M3pin':(30,2),'M3txt':(30,25),'prBoundary':(189,4)}
METALS = ('M1','M2','M3','M4')
CUTS = {'Via1':('M1','M2'),'Via2':('M2','M3'),'Via3':('M3','M4')}
SIGNALS = ['b1b','c2','dvbe','vbe','vbe3','vd1','vd2']
RETURNS = ['return_XQ56','return_XQ60','return_XQ67','return_XQ62']
GUARD = 'guard_vss'
STAR = 'star_vss'


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p, v): p.write_text(json.dumps(v, indent=2)+'\n')
def u(v): return int(round(v*1000))
def box(x1,y1,x2,y2): return pya.Box(u(min(x1,x2)),u(min(y1,y2)),u(max(x1,x2)),u(max(y1,y2)))
def bb(b): return [b.left,b.bottom,b.right,b.top]
def reg(cell, li):
    r=pya.Region(cell.begin_shapes_rec(li));r.flatten();return r
def source_net(role): return 'vss' if role in RETURNS+[GUARD,STAR] else role


class Bank:
    def __init__(self,out):
        self.out=out;self.ly=pya.Layout();self.ly.dbu=.001;self.top=self.ly.create_cell('bgr_hbt_bank')
        self.layers={n:self.ly.layer(*p) for n,p in PAIRS.items()}
        self.routes=[];self.vias=[];self.probes=[];self.instances=[];self.copy_audits=[];self.interfaces={}
        self.inputs={p:sha(p) for p in PINNED};self.cache={}

    def rect(self, layer, role, x1,y1,x2,y2, purpose):
        b=box(x1,y1,x2,y2);self.top.shapes(self.layers[layer]).insert(b)
        self.routes.append(dict(layer=layer,role=role,net=source_net(role),bbox_dbu=bb(b),purpose=purpose))

    def wire(self, layer, role, x1,y1,x2,y2, width=.3, purpose='wire'):
        assert abs(x1-x2)<1e-9 or abs(y1-y2)<1e-9
        self.rect(layer,role,min(x1,x2)-width/2,min(y1,y2)-width/2,max(x1,x2)+width/2,max(y1,y2)+width/2,purpose)

    def via(self, kind, role, x,y, axis='x', interface=None):
        lo,hi=CUTS[kind];dx,dy=(.36,.15) if axis=='x' else (.15,.36)
        self.rect(lo,STAR if interface else role,x-dx,y-dy,x+dx,y+dy,'via_landing')
        self.rect(hi,role,x-dx,y-dy,x+dx,y+dy,'via_landing')
        boxes=[]
        for offset in (-.21,.21):
            cx=x+(offset if axis=='x' else 0);cy=y+(offset if axis=='y' else 0)
            b=box(cx-.095,cy-.095,cx+.095,cy+.095)
            self.top.shapes(self.layers[kind]).insert(b);boxes.append(bb(b))
            self.vias.append(dict(layer=kind,role=role,net=source_net(role),bbox_dbu=bb(b),interface=interface))
        if interface:
            assert kind=='Via3' and interface==role and interface not in self.interfaces
            self.interfaces[interface]=boxes

    def contact(self, path, original_nodes, actual_nodes):
        mapping=dict(zip(original_nodes,actual_nodes))
        assert all(mapping[a]==b for a,b in zip(original_nodes,actual_nodes))
        key=(path,tuple(actual_nodes))
        if key in self.cache:return self.cache[key]
        src=pya.Layout();src.read(str(path));old=src.top_cell()
        cell=self.ly.create_cell('contact_%02d'%len(self.cache));cell.copy_tree(old)
        self.inputs[path]=sha(path);changes=[];native_inst_count=sum(1 for _ in cell.each_inst())
        assert native_inst_count==1
        for li in src.layer_indices():
            info=src.get_info(li);target=self.ly.layer(info)
            assert (reg(old,li)^reg(cell,target)).is_empty()
            for shape in list(cell.shapes(target).each()):
                if not shape.is_text():continue
                text=shape.text
                if text.string in mapping and mapping[text.string]!=text.string:
                    previous=text.string;text.string=mapping[previous];shape.text=text
                    changes.append(dict(layer=info.layer,datatype=info.datatype,old=previous,new=text.string))
            assert (reg(old,li)^reg(cell,target)).is_empty()
        # Only the source-required diode label map is permitted.
        assert not changes or all(c['old']=='vbe' and c['new'] in ('vbe3','vd2') for c in changes)
        self.copy_audits.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path),actual_nodes=actual_nodes,
                                     all_polygon_layers_xor_zero=True,native_instances_unchanged=True,text_changes=changes))
        self.cache[key]=cell;return cell

    def place(self, rows, hman, controls):
        hmap={n:p for p in hman['prototypes'] for n in p['represented_instances']}
        variants={v['name'].replace('return_control','proto'):v for v in controls['variants']}
        for d in rows:
            proto=hmap[d['name']];nodes=d['source_line'].split()[1:5]
            if proto['name'] in variants:
                variant=variants[proto['name']];path=CONTROL/(variant['name']+'.gds')
                assert sha(path)==variant['gds_sha256']
            else:path=HBT/(proto['name']+'.gds');assert sha(path)==proto['gds_sha256']
            cell=self.contact(path,proto['source_line'].split()[1:5],nodes)
            dx=d['bbox_um'][0]-proto['native_bbox_um'][0];dy=d['bbox_um'][1]-proto['native_bbox_um'][1]
            self.top.insert(pya.CellInstArray(cell.cell_index(),pya.Trans(u(dx),u(dy))))
            x,y=10+dx,10+dy
            dummy=len(set(nodes))==1
            erole=GUARD if dummy else ('return_'+d['original'] if nodes[2]=='vss' else nodes[2])
            assert erole in RETURNS+[GUARD]+SIGNALS
            data=dict(d,origin_um=[x,y],emitter_role=erole,dummy=dummy)
            self.instances.append(data)
            for t,n,layer,px,py,role in [('C',nodes[0],'M1',x-.75,y+1.2,GUARD if dummy else nodes[0]),
                   ('B',nodes[1],'M1',x if dummy else x+.6,y-1.14 if dummy else y-1.5,GUARD if dummy else nodes[1]),
                   ('E',nodes[2],'M2',x,y,erole),('S',nodes[3],'M1',x+2.9,y+.2,GUARD)]:
                self.probes.append(dict(instance=d['name'],terminal=t,net=n,role=role,layer=layer,point_dbu=[u(px),u(py)]))
        assert len(self.instances)==301 and len(self.probes)==1204

    def route(self):
        bases=collections.defaultdict(set);upper=collections.defaultdict(set)
        for d in self.instances:
            if d['dummy']:continue
            row=d['slot_index']//17;c,b,e,s=d['source_line'].split()[1:5]
            bases[row].add(b)
            if c!=b:upper[row].add(c)
            if e!='vss':upper[row].add(e)
        assert max(map(len,bases.values()))<=2 and max(map(len,upper.values()))<=3
        taps=collections.defaultdict(list);return_taps=collections.defaultdict(list)
        for d in self.instances:
            x,y=d['origin_um'];row=d['slot_index']//17;bottom,top=d['bbox_um'][1],d['bbox_um'][3]
            c,b,e,s=d['source_line'].split()[1:5]
            if not d['dummy']:
                by=bottom-.35-.6*sorted(bases[row]).index(b)
                self.via('Via1',b,x+.6,y-1.5)
                self.wire('M2',b,x+.6,y-1.5,x+.6,by)
                self.via('Via2',b,x+.6,by);taps[(row,b,by)].append(x+.6)
                if c!=b:
                    cy=top+.15+.6*sorted(upper[row]).index(c)
                    self.via('Via1',c,x-.6,y+1.5,axis='y')
                    self.wire('M2',c,x-.6,y+1.5,x-1.2,y+1.5)
                    self.wire('M2',c,x-1.2,y+1.5,x-1.2,cy)
                    self.via('Via2',c,x-1.2,cy);taps[(row,c,cy)].append(x-1.2)
                if e!='vss':
                    ey=top+.15+.6*sorted(upper[row]).index(e)
                    self.wire('M2',e,x,y+.6,x,ey)
                    self.via('Via2',e,x,ey);taps[(row,e,ey)].append(x)
                else:
                    role=d['emitter_role'];ey=y+(1.2 if d['original']=='XQ62' else 0)
                    self.wire('M2',role,x,y,x,ey)
                    self.via('Via2',role,x,ey);self.via('Via3',role,x,ey)
                    return_taps[(row,role,ey)].append(x)
            gy=top+2.2
            self.via('Via1',GUARD,x+2.9,y+.2)
            self.wire('M2',GUARD,x+2.9,y+.2,x+2.9,gy)
            self.via('Via2',GUARD,x+2.9,gy);taps[(row,GUARD,gy)].append(x+2.9)
        trunk={n:190.8+1.1*i for i,n in enumerate(SIGNALS)};trunk[GUARD]=198.5
        ys=collections.defaultdict(list)
        for (row,role,y),xs in taps.items():
            width=.8 if role==GUARD else .3
            self.wire('M3',role,min(xs),y,trunk[role],y,width,'row_collector')
            self.via('Via2',role,trunk[role],y);ys[role].append(y)
        for i,role in enumerate(SIGNALS):
            py=136+.6*i;tx=trunk[role]
            self.wire('M2',role,tx,min(min(ys[role]),py),tx,max(max(ys[role]),py),purpose='source_trunk')
            self.via('Via2',role,tx,py)
            self.wire('M3',role,tx,py,200.5,py,purpose='port_escape')
            self.top.shapes(self.layers['M3pin']).insert(box(200,py-.15,200.5,py+.15))
            self.top.shapes(self.layers['M3txt']).insert(pya.Text(role,pya.Trans(u(200.25),u(py))))
            self.probes.append(dict(instance='port',terminal=role,net=role,role=role,layer='M3',point_dbu=[u(200.25),u(py)]))
        self.wire('M2',GUARD,198.5,134,198.5,max(ys[GUARD]),.8,'general_source_trunk')
        self.via('Via2',GUARD,198.5,134)
        self.wire('M3',GUARD,7.2,134,198.5,134,.8,'general_left_escape')
        self.via('Via2',GUARD,7.2,134)
        return_x=dict(zip(RETURNS,[1.2,2.6,4.0,5.4]));return_ys=collections.defaultdict(list)
        for (row,role,y),xs in return_taps.items():
            tx=return_x[role]
            self.wire('M4',role,tx,y,max(xs),y,.8,'functional_return_row')
            self.via('Via2',role,tx,y);self.via('Via3',role,tx,y);return_ys[role].append(y)
        turn_y=dict(zip(RETURNS,[16.26,15.06,13.86,12.66]))
        for role,tx in return_x.items():
            self.wire('M2',role,tx,turn_y[role],tx,max(return_ys[role]),.8,'return_trunk')
        self.wire('M2',GUARD,7.2,11.46,7.2,134,.8,'general_return_trunk')
        targets={'return_XQ56':(1.2,16.26,16,16.26),'return_XQ60':(2.6,15.06,13.6,15.06),
                 'return_XQ67':(4.0,13.86,14.8,15.06),'return_XQ62':(5.4,12.66,16,15.06),
                 GUARD:(7.2,11.46,17.2,15.06)}
        for role,(x,y,tx,ty) in targets.items():
            self.via('Via2',role,x,y);self.via('Via3',role,x,y)
            self.wire('M4',role,x,y,tx,y,.8,'star_branch')
            if y!=ty:self.wire('M4',role,tx,y,tx,ty,.8,'star_branch')
            self.via('Via3',role,tx,ty,interface=role)
        self.rect('M3',STAR,13.2,14.66,17.6,15.46,'declared_general_star_hub')
        self.rect('M3',STAR,15.6,15.86,16.4,16.66,'declared_precision_point')
        for y in (15.06,16.26):self.via('Via2',STAR,16,y,axis='y')
        self.rect('M2',STAR,15.85,15.06,16.15,16.26,'declared_precision_general_join')
        self.top.shapes(self.layers['M3pin']).insert(box(16.2,14.91,17,15.21))
        self.top.shapes(self.layers['M3txt']).insert(pya.Text('vss',pya.Trans(16600,15060)))
        self.probes.append(dict(instance='port',terminal='vss',net='vss',role=STAR,layer='M3',point_dbu=[16600,15060]))
        self.channels=[dict(row=row,base_roles=sorted(bases[row]),upper_roles=sorted(upper[row])) for row in range(19)]

    def graph(self, top, removed=(), byrole=False, get_geometry=False):
        ly=top.layout();flat=pya.Layout();flat.dbu=.001;ft=flat.create_cell('physical_graph')
        removed_region=pya.Region()
        for role in removed:
            for b in self.interfaces[role]:removed_region.insert(pya.Box(*b))
        regions={}
        for k in list(METALS)+list(CUTS):
            r=reg(top,ly.layer(*PAIRS[k]))
            if k=='Via3':r-=removed_region
            regions[k]=r.merged()
            for polygon in regions[k].each():ft.shapes(flat.layer(*PAIRS[k])).insert(polygon)
        n=pya.LayoutToNetlist(pya.RecursiveShapeIterator(flat,ft,[]));nl={}
        for k in METALS:nl[k]=n.make_layer(flat.layer(*PAIRS[k]),k);n.connect(nl[k])
        for k,ends in CUTS.items():
            cut=n.make_layer(flat.layer(*PAIRS[k]),k);n.connect(cut)
            for end in ends:n.connect(cut,nl[end])
        n.extract_netlist();expected=collections.defaultdict(set);actual=collections.defaultdict(set);obs=[]
        for p in self.probes:
            node=n.probe_net(nl[p['layer']],pya.Point(*p['point_dbu']))
            identity=None if node is None else node.cluster_id
            group=p['role'] if byrole or p['role'] in removed else p['net']
            expected[group].add(identity);actual[identity].add(group);obs.append(dict(p,physical_component=identity,expected_group=group))
        opens={k:sorted(v,key=str) for k,v in expected.items() if None in v or len(v)!=1}
        shorts={str(k):sorted(v) for k,v in actual.items() if len(v)!=1}
        result=dict(status='passed' if not opens and not shorts else 'failed',removed_star_interfaces=list(removed),
                    physical_component_count=len(actual),opens=opens,shorts=shorts,observations=obs,
                    text_labels_merge_components=False)
        geometry={}
        if get_geometry and result['status']=='passed':
            component_role={k:next(iter(v)) for k,v in actual.items()}
            for layer in METALS:
                for polygon in regions[layer].each():
                    vertex=next(polygon.each_point_hull());point=None
                    for dx,dy in [(1,1),(1,-1),(-1,1),(-1,-1),(2,1),(1,2),(-2,-1),(-1,-2)]:
                        candidate=pya.Point(vertex.x+dx,vertex.y+dy)
                        if polygon.inside(candidate):point=candidate;break
                    assert point is not None,'interior polygon probe'
                    node=n.probe_net(nl[layer],point);identity=None if node is None else node.cluster_id
                    assert identity in component_role,('unobserved conductor',layer,bb(polygon.bbox()),identity)
                    role=component_role[identity]
                    geometry.setdefault(role,{k:pya.Region() for k in METALS})[layer].insert(polygon)
        return result,geometry

    def local_audit(self, geometry):
        additions={role:{k:pya.Region() for k in METALS} for role in geometry}
        errors=[];spacing=[]
        for r in self.routes:
            rr=pya.Region(pya.Box(*r['bbox_dbu']));role=r['role'];layer=r['layer']
            if not (rr-geometry[role][layer]).is_empty():errors.append(dict(check='route_ownership',route=r))
            additions[role][layer]+=rr
        for role, layers in additions.items():
            for other,regions in geometry.items():
                if role==other:continue
                for layer in METALS:
                    hit=layers[layer]&regions[layer].sized(300)
                    for p in hit.each():spacing.append(dict(route_role=role,neighbor_role=other,layer=layer,bbox_dbu=bb(p.bbox()),area_dbu2=p.area()))
        all_regions={k:reg(self.top,self.layers[k]) for k in METALS}
        for v in self.vias:
            shape=pya.Region(pya.Box(*v['bbox_dbu'])).sized(55)
            for layer in CUTS[v['layer']]:
                if not (shape-all_regions[layer]).is_empty():errors.append(dict(check='via_55nm_enclosure',via=v,layer=layer))
        return dict(status='passed' if not errors and not spacing else 'failed',ownership_enclosure_errors=errors,
                    added_route_to_other_role_spacing_um=.3,spacing_findings=spacing,
                    scope='Added route/landing polygons versus actual all-cut physical-role native/route metal, not stock DRC')

    def neighbors(self, pack):
        obs={k:pya.Region() for k in list(METALS)+list(CUTS)};reservations=pya.Region();count=0
        mm=json.loads((MOS/'manifest.json').read_text());mmap={n:p for p in mm['prototypes'] for n in p['represented_instances']}
        cache={}
        for d in pack:
            if 'mos' not in d['kind']:continue
            proto=mmap[d['name']];path=MOS/(proto['name']+'.gds')
            assert sha(path)==proto['gds_sha256'];self.inputs[path]=sha(path)
            if path not in cache:
                ly=pya.Layout();ly.read(str(path));cache[path]=(ly,{k:reg(ly.top_cell(),ly.layer(*PAIRS[k])) for k in obs})
            dx=d['bbox_um'][0]-proto['native_bbox_um'][0];dy=d['bbox_um'][1]-proto['native_bbox_um'][1]
            tr=pya.Trans(u(dx),u(dy))
            for k,r in cache[path][1].items():obs[k]+=r.transformed(tr)
            reservations.insert(box(*d['reservation_um']));count+=1
        assert count==336
        rly=pya.Layout();rly.read(str(RBANK/'bgr_resistor_bank_pilot.gds'))
        resistor={k:reg(rly.top_cell(),rly.layer(*PAIRS[k])) for k in obs}
        additions={k:pya.Region() for k in obs}
        for r in self.routes+self.vias:additions[r['layer']].insert(pya.Box(*r['bbox_dbu']))
        allowed=pya.Region(box(13,14.4,18.2,16.8));findings=[];star_hits=[]
        for k,r in additions.items():
            cases={'MOS_contacts':r&obs[k].sized(300),'MOS_reserved_rectangles':r&reservations.sized(300),
                   'routed_resistor_bank':(r&resistor[k].sized(300))-allowed}
            for kind,hit in cases.items():
                for p in hit.each():findings.append(dict(kind=kind,layer=k,bbox_dbu=bb(p.bbox()),area_dbu2=p.area()))
            for p in (r&resistor[k]&allowed).each():star_hits.append(dict(layer=k,bbox_dbu=bb(p.bbox()),area_dbu2=p.area()))
        return dict(status='passed' if not findings else 'failed',MOS_count=count,resistor_count=399,
                    findings=findings,intentional_resistor_star_intersections=star_hits,
                    future_MOS_routing_and_ring_geometry='not run')

    def run(self):
        for p,h in PINNED.items():assert sha(p)==h,str(p)
        assert pya.__version__=='0.30.9' and (PDK/'COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
        controls=json.loads((CONTROL/'controls.json').read_text());assert controls['status']=='passed two contact and source-placement controls'
        ledger=json.loads((CONTROL/'bank_source_placement_ledger.json').read_text())
        pack=json.loads(PACK.read_text())['BGR_devices'];rows=[d for d in pack if d['kind']=='npn13G2']
        assert rows==ledger['fixed_devices'];assert len(ledger['all_50_macro_replication_centroids'])==50
        hman=json.loads((HBT/'manifest.json').read_text())
        for p in hman['prototypes']:
            path=HBT/(p['name']+'.gds');assert sha(path)==p['gds_sha256'];self.inputs[path]=sha(path)
        self.place(rows,hman,controls)
        before={li:reg(self.top,li) for li in self.ly.layer_indices()}
        self.route()
        unchanged=[]
        routing_pairs=set(PAIRS[k] for k in list(METALS)+list(CUTS)+['M3pin','M3txt','prBoundary'])
        for li,r in before.items():
            info=self.ly.get_info(li)
            if (info.layer,info.datatype) not in routing_pairs:
                same=(reg(self.top,li)^r).is_empty();unchanged.append(same);assert same,str(info)
        gds=self.out/'bank.gds';self.ly.write(str(gds))
        cdl=self.out/'bank.cdl';cdl.write_text('.subckt bgr_hbt_bank '+' '.join(SIGNALS+['vss'])+'\n'+
             '\n'.join('Q'+d['source_line'][2:] for d in rows)+'\n.ends bgr_hbt_bank\n')
        dump(self.out/'route_ledger.json',dict(routes=self.routes,vias=self.vias,probes=self.probes,star_interfaces=self.interfaces))
        dump(self.out/'placement.json',dict(instances=self.instances,copy_audits=self.copy_audits,all_50_centroids=ledger['all_50_macro_replication_centroids'],channels=self.channels))
        saved=pya.Layout();saved.read(str(gds));top=saved.top_cell()
        assert all((reg(top,saved.layer(self.ly.get_info(li)))^reg(self.top,li)).is_empty() for li in self.ly.layer_indices())
        full,_=self.graph(top);dump(self.out/'terminal_graph.json',full)
        cut_all,geometry=self.graph(top,RETURNS+[GUARD],byrole=True,get_geometry=True)
        dump(self.out/'all_star_interfaces_cut.json',cut_all)
        cuts=[]
        for role in RETURNS+[GUARD]:
            report,_=self.graph(top,[role]);cuts.append(report)
        dump(self.out/'individual_star_cuts.json',cuts)
        local=self.local_audit(geometry) if cut_all['status']=='passed' else dict(status='not run; all-cut graph failed')
        dump(self.out/'local_spacing_ownership.json',local)
        neighbors=self.neighbors(pack);dump(self.out/'neighbor_obstructions.json',neighbors)
        offgrid=[];vertices=0
        for li in saved.layer_indices():
            for polygon in reg(top,li).each():
                points=list(polygon.each_point_hull())
                for h in range(polygon.holes()):points+=list(polygon.each_point_hole(h))
                for p in points:
                    vertices+=1
                    if p.x%5 or p.y%5:offgrid.append([saved.get_info(li).to_s(),p.x,p.y])
        bounds_ok=(pya.Region(top.bbox())-pya.Region(box(0,0,420,354))).is_empty()
        for p,h in self.inputs.items():assert sha(p)==h,str(p)
        checks=dict(source_fixed_positions=True,native_polygon_copy=True,native_nonrouting_layers_unchanged=all(unchanged),
                    serialized_polygon_parity=True,source_terminal_graph=full['status']=='passed',
                    all_star_interfaces_separate=cut_all['status']=='passed',individual_star_cuts=all(c['status']=='passed' for c in cuts),
                    local_spacing_ownership=local['status']=='passed',known_neighbors=neighbors['status']=='passed',
                    on_5nm_grid=not offgrid,macro_bounds=bounds_ok)
        result=dict(status='passed preparation' if all(checks.values()) else 'failed preparation',checks=checks,
                    source_device_count=301,source_terminal_count=1204,source_net_count=8,star_interface_count=5,
                    inputs={str(p.relative_to(ROOT)):h for p,h in self.inputs.items()},script_sha256=sha(Path(__file__)),
                    GDS_sha256=sha(gds),CDL_sha256=sha(cdl),klayout=pya.__version__,pdk_commit=(PDK/'COMMIT').read_text().strip(),
                    bounds_dbu=bb(top.bbox()),polygon_vertices=vertices,off_grid=offgrid,
                    stock_DRC_LVS_density_antenna='not run',PEX_analog_matching_IR_noise='not run',
                    full_macro_ring_adoption='not run',seed='not applicable')
        dump(self.out/'preparation.json',result);print(json.dumps(result,indent=2))
        return 0 if all(checks.values()) else 1


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    assert a.output.is_dir() and not (a.output/'bank.gds').exists()
    try:return Bank(a.output).run()
    except Exception as e:
        dump(a.output/'preparation_exception.json',dict(status='failed',exception=type(e).__name__,message=str(e)));raise


if __name__=='__main__':raise SystemExit(main())
