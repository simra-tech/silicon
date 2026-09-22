#!/usr/bin/env python3
"""Source-exact 34-HBT preparation only; never invokes a stock rule or solver."""
import argparse
import collections
import hashlib
import json
import sys
from pathlib import Path
import pya

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
PACK = ROOT/'designs/g1-guardian/review/audits/coordinated-bbox-pack-586-20260922-r1.json'
SOURCE = HERE.parent.parent/'sim/qualification/candidates/bgr_loop24_qref4_r253p465_hv06/bgr_loop24_qref4_r253p465_hv06.spice'
HBT = ROOT/'build/scratch/bgr-hbt-contact-prototypes-20260922-r1'
MOS = ROOT/'build/scratch/bgr-mos-contact-prototypes-20260922-r2'
STOCK = ROOT/'build/scratch/bgr-second-stock-20260922-r1/summary.json'
PDK = Path('/foss/pdks/ihp-sg13g2')
PINNED = {PACK:'2663805a5180a1961850c1068b0c1c3615c010cd2ec47d38a228d65dde4800cb',
          SOURCE:'586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b',
          HBT/'manifest.json':'bcdb1f01f4287db750935896756b5947db22898612a9bb77b229f6f0553d4fc2',
          STOCK:'42d35eaf4daec387389fc0e027e1db271f542536d850f4b01524f5d5a496ae48'}
PORTS = ['c2','dvbe','vbe','vd1','vd2','vss']
LAYERS = {'M1':(8,0),'Via1':(19,0),'M2':(10,0),'Via2':(29,0),'M3':(30,0),
          'M3pin':(30,2),'M3txt':(30,25),'Activ':(1,0),'GatPoly':(5,0)}

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def u(x): return int(round(x*1000))
def box(x1,y1,x2,y2): return pya.Box(u(min(x1,x2)),u(min(y1,y2)),u(max(x1,x2)),u(max(y1,y2)))
def materialized(cell,li):
    r=pya.Region(cell.begin_shapes_rec(li)); r.flatten(); return r
def bounds(b): return [v*.001 for v in (b.left,b.bottom,b.right,b.top)]
def dump(p,v): p.write_text(json.dumps(v,indent=2)+'\n')

class Build:
    def __init__(self,out):
        self.out=out; self.ly=pya.Layout(); self.ly.dbu=.001
        self.top=self.ly.create_cell('bgr_hbt_worstrows')
        self.layers={k:self.ly.layer(*v) for k,v in LAYERS.items()}
        self.routes=[]; self.vias=[]; self.terminals=[]; self.ports=[]; self.cache={}
        self.inputs={str(p.relative_to(ROOT)):sha(p) for p in PINNED}

    def load(self,path):
        if path in self.cache:return self.cache[path]
        ly=pya.Layout();ly.read(str(path));src=ly.top_cell()
        cell=self.ly.create_cell('frozen_'+path.stem);cell.copy_tree(src)
        checks=[]
        for li in ly.layer_indices():
            info=ly.get_info(li);dst=self.ly.layer(info)
            a=materialized(src,li);b=materialized(cell,dst)
            checks.append((a^b).is_empty())
        assert all(checks),'prototype polygon copy parity'
        self.inputs[str(path.relative_to(ROOT))]=sha(path)
        self.cache[path]=cell
        return cell

    def rect(self,layer,net,x1,y1,x2,y2,role):
        b=box(x1,y1,x2,y2);self.top.shapes(self.layers[layer]).insert(b)
        self.routes.append(dict(layer=layer,net=net,bbox_dbu=[b.left,b.bottom,b.right,b.top],role=role))

    def wire(self,layer,net,x1,y1,x2,y2,width=.3,role='wire'):
        assert x1==x2 or y1==y2
        self.rect(layer,net,min(x1,x2)-width/2,min(y1,y2)-width/2,
                  max(x1,x2)+width/2,max(y1,y2)+width/2,role)

    def via(self,kind,net,x,y):
        low,high=('M1','M2') if kind=='Via1' else ('M2','M3')
        for layer in (low,high):self.rect(layer,net,x-.36,y-.15,x+.36,y+.15,'two_cut_landing')
        for dx in (-.21,.21):
            b=box(x+dx-.095,y-.095,x+dx+.095,y+.095)
            self.top.shapes(self.layers[kind]).insert(b)
            self.vias.append(dict(layer=kind,net=net,bbox_dbu=[b.left,b.bottom,b.right,b.top]))

    def run(self):
        for p,h in PINNED.items():assert sha(p)==h,str(p)
        assert pya.__version__=='0.30.9'
        assert (PDK/'COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
        assert json.loads(STOCK.read_text())['status']=='passed'
        pack=json.loads(PACK.read_text()); rows=pack['BGR_devices']
        src={l.split()[0]:l for l in SOURCE.read_text().splitlines() if l.startswith(('XM','XR','XQ'))}
        assert len(src)==1036 and all(src[d['name']]==d['source_line'] for d in rows)
        selected=[d for d in rows if d['zone']=='hbt' and d['slot_index']//17 in (7,11)]
        assert len(selected)==34 and collections.Counter(d['original'] for d in selected)=={'XQ75':24,'XQ76':8,'XQ74':2}
        assert set(n for d in selected for n in d['source_line'].split()[1:5])==set(PORTS)
        hman=json.loads((HBT/'manifest.json').read_text())
        hmap={n:r for r in hman['prototypes'] for n in r['represented_instances']}
        mmap={n:r for r in json.loads((MOS/'manifest.json').read_text())['prototypes'] for n in r['represented_instances']}
        self.inputs[str((MOS/'manifest.json').relative_to(ROOT))]=sha(MOS/'manifest.json')
        self.subset=selected
        # Instance immutable whole contact cells; no modifications inside them.
        for d in selected:
            proto=hmap[d['name']];assert proto['name'] in ('bgr_hbt_proto_03','bgr_hbt_proto_04')
            assert proto['source_line'].split()[1:]==d['source_line'].split()[1:]
            path=HBT/(proto['name']+'.gds');assert sha(path)==proto['gds_sha256']
            cell=self.load(path)
            dx=d['bbox_um'][0]-proto['native_bbox_um'][0];dy=d['bbox_um'][1]-proto['native_bbox_um'][1]
            self.top.insert(pya.CellInstArray(cell.cell_index(),pya.Trans(u(dx),u(dy))))
            x=10+dx;y=10+dy
            d['pcell_origin_um']=[x,y]
            c,b,e,s=d['source_line'].split()[1:5]
            for terminal,net,layer,px,py in [('C',c,'M1',x-.75,y+1.2),('B',b,'M1',x+.6,y-1.5),
                                          ('E',e,'M2',x,y),('S',s,'M1',x+2.9,y+.2)]:
                self.terminals.append(dict(instance=d['name'],terminal=terminal,net=net,layer=layer,point_dbu=[u(px),u(py)]))
        before={k:materialized(self.top,self.layers[k]) for k in ('Activ','GatPoly')}
        track_taps=collections.defaultdict(list)
        for d in selected:
            x,y=d['pcell_origin_um'];c,b,e,s=d['source_line'].split()[1:5]
            row=d['slot_index']//17;bottom=d['bbox_um'][1];top=d['bbox_um'][3]
            tyb=bottom-(.6 if b=='vbe' else 1.2)
            self.via('Via1',b,x+.6,y-1.5)
            self.wire('M2',b,x+.6,y-1.5,x+.6,tyb)
            self.via('Via2',b,x+.6,tyb);track_taps[(row,b,tyb)].append(x+.6)
            tye=top+(.6 if e=='dvbe' else 1.2)
            self.wire('M2',e,x,y+.6,x,tye)
            self.via('Via2',e,x,tye);track_taps[(row,e,tye)].append(x)
            if c!=b:
                # Move the collector column left before it shares an upper
                # channel with the emitter's two-cut Via2 landing.
                tyc=top+1.8
                self.via('Via1',c,x-.6,y+1.5)
                self.wire('M2',c,x-.6,y+1.5,x-1.2,y+1.5)
                self.wire('M2',c,x-1.2,y+1.5,x-1.2,tyc)
                self.via('Via2',c,x-1.2,tyc);track_taps[(row,c,tyc)].append(x-1.2)
            tys=top+2.6
            self.via('Via1',s,x+2.9,y+.2)
            self.wire('M2',s,x+2.9,y+.2,x+2.9,tys)
            self.via('Via2',s,x+2.9,tys);track_taps[(row,s,tys)].append(x+2.9)
        trunk={n:190.8+1.1*i for i,n in enumerate(PORTS)}
        ys=collections.defaultdict(list)
        for (row,n,y),xs in track_taps.items():
            width=.8 if n=='vss' else .3
            self.wire('M3',n,min(xs),y,trunk[n],y,width,'row_collector')
            self.via('Via2',n,trunk[n],y);ys[n].append(y)
        for i,n in enumerate(PORTS):
            py=280+2*i;tx=trunk[n];width=.8 if n=='vss' else .3
            self.wire('M2',n,tx,min(ys[n]),tx,py,width,'bank_trunk')
            self.via('Via2',n,tx,py)
            self.wire('M3',n,tx,py,200.5,py,width,'port_escape')
            self.top.shapes(self.layers['M3pin']).insert(box(200,py-width/2,200.5,py+width/2))
            self.top.shapes(self.layers['M3txt']).insert(pya.Text(n,pya.Trans(u(200.25),u(py))))
            self.ports.append(dict(net=n,layer='M3',point_dbu=[u(200.25),u(py)]))
        native={k:(materialized(self.top,self.layers[k])^r).is_empty() for k,r in before.items()}
        assert all(native.values())
        self.ly.write(str(self.out/'pilot.gds'))
        cdl='.subckt bgr_hbt_worstrows '+' '.join(PORTS)+'\n'
        cdl+='\n'.join('Q'+d['name'][2:]+' '+' '.join(d['source_line'].split()[1:]) for d in selected)+'\n.ends bgr_hbt_worstrows\n'
        (self.out/'pilot.cdl').write_text(cdl)
        dump(self.out/'subset.json',dict(source_sha256=sha(SOURCE),pack_sha256=sha(PACK),ports=PORTS,devices=selected))
        dump(self.out/'route_ledger.json',dict(routes=self.routes,vias=self.vias,terminals=self.terminals,ports=self.ports))
        graph=self.graph()
        dump(self.out/'terminal_graph.json',graph)
        neighbors=self.neighbors(rows,selected,hmap,mmap)
        dump(self.out/'neighbor_obstructions.json',neighbors)
        checks=dict(source_subset=True,prototype_polygon_parity=True,native_Activ_GatPoly=all(native.values()),
                    terminal_graph=graph['status']=='passed',known_neighbor_obstructions=neighbors['status']=='passed')
        result=dict(status='passed preparation' if all(checks.values()) else 'failed preparation',checks=checks,
                    inputs=self.inputs,script_sha256=sha(Path(__file__)),klayout=pya.__version__,
                    pdk_commit=(PDK/'COMMIT').read_text().strip(),device_count=34,terminal_count=len(self.terminals),
                    added_via_counts=dict(collections.Counter(v['layer'] for v in self.vias)),
                    bbox_um=bounds(self.top.bbox()),stock_DRC_LVS='not run',fullmacro_adoption='not run',seed='not applicable')
        result['output_sha256']={p.name:sha(p) for p in self.out.iterdir() if p.name.endswith(('.gds','.cdl','.json'))}
        dump(self.out/'preparation.json',result);print(json.dumps(result,indent=2))
        return 0 if all(checks.values()) else 1

    def graph(self):
        polys={};regions={};parent=[]
        for layer in ('M1','M2','M3'):
            reg=materialized(self.top,self.layers[layer]).merged();regions[layer]=reg;items=[]
            for poly in reg.each():
                i=len(parent);parent.append(i);items.append((i,poly))
            polys[layer]=items
        def find(i):
            while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
            return i
        def union(a,b):parent[find(a)]=find(b)
        errors=[]
        for kind,low,high in [('Via1','M1','M2'),('Via2','M2','M3')]:
            for v in materialized(self.top,self.layers[kind]).each():
                vr=pya.Region(v);hits=[]
                for layer in (low,high):
                    hh=[i for i,p in polys[layer] if not (pya.Region(p)&vr).is_empty()]
                    if len(hh)!=1:errors.append(dict(kind='via_components',via=kind,layer=layer,bbox=bounds(v.bbox()),hits=hh))
                    hits+=hh
                    # Native vias may use a different legal enclosure: test
                    # containment for all,0.055 only for our declared cuts.
                    if not (vr-regions[layer]).is_empty():errors.append(dict(kind='via_unlanded',via=kind,layer=layer))
                for i in hits[1:]:union(hits[0],i)
        for v in self.vias:
            vr=pya.Region(pya.Box(*v['bbox_dbu'])).sized(55)
            for layer in (('M1','M2') if v['layer']=='Via1' else ('M2','M3')):
                if not (vr-regions[layer]).is_empty():errors.append(dict(kind='added_via_enclosure',via=v,layer=layer))
        components=collections.defaultdict(set);observations=[]
        for t in self.terminals+self.ports:
            point=pya.Point(*t['point_dbu']);hits=[i for i,p in polys[t['layer']] if p.inside(point)]
            if len(hits)!=1:errors.append(dict(kind='terminal_missing',terminal=t,hits=hits));continue
            component=find(hits[0]);components[component].add(t['net']);observations.append(dict(t,component=component))
        for comp,nets in components.items():
            if len(nets)!=1:errors.append(dict(kind='cross_net_component',component=comp,nets=sorted(nets)))
        bynet=collections.defaultdict(set)
        for comp,nets in components.items():
            for n in nets:bynet[n].add(comp)
        for n in PORTS:
            if len(bynet[n])!=1:errors.append(dict(kind='open_net',net=n,components=sorted(bynet[n])))
        # Include every added conductor, not only terminal-bearing components.
        for r in self.routes:
            rr=pya.Region(pya.Box(*r['bbox_dbu']))
            hs={find(i) for i,p in polys[r['layer']] if not (pya.Region(p)&rr).is_empty()}
            if len(hs)!=1 or hs!=bynet[r['net']]:errors.append(dict(kind='route_component',route=r,components=sorted(hs)))
        return dict(status='passed' if not errors else 'failed',errors=errors,
                    metal_components_before_vias=sum(map(len,polys.values())),
                    connected_components=len({find(i) for i in range(len(parent))}),observations=observations,
                    nets={n:sorted(cs) for n,cs in bynet.items()},scope='Physical M1/M2/M3 and Via1/Via2 graph; semiconductor terminal identity from frozen prototypes; stock LVS not run')

    def neighbors(self,rows,selected,hmap,mmap):
        for p in [PDK/'libs.tech/klayout/python',PDK/'libs.tech/klayout/python/pycell4klayout-api/source/python']:
            sys.path.insert(0,str(p))
        import sg13g2_pycell_lib  # noqa: F401
        lib=pya.Library.library_by_name('SG13_dev','sg13g2')
        chosen={d['name'] for d in selected};obs={k:pya.Region() for k in ('M1','M2','M3','Via1','Via2')}
        additions={k:pya.Region() for k in obs};nativecells={};counts=collections.Counter()
        for r in self.routes:
            if r['layer'] in additions:additions[r['layer']].insert(pya.Box(*r['bbox_dbu']))
        for r in self.vias:additions[r['layer']].insert(pya.Box(*r['bbox_dbu']))
        for d in rows:
            if d['name'] in chosen:continue
            if d['kind']=='npn13G2' or 'mos' in d['kind']:
                proto=(hmap if d['kind']=='npn13G2' else mmap)[d['name']]
                directory=HBT if d['kind']=='npn13G2' else MOS
                path=directory/(proto['name']+'.gds');assert sha(path)==proto['gds_sha256']
                cell=self.load(path);origin=proto['native_bbox_um'][:2]
            else:
                t=d['source_line'].split();params=dict(x.split('=',1) for x in t[5:])
                key=(d['kind'],params['w'],params['l'])
                if key not in nativecells:
                    variant=lib.layout().add_pcell_variant(lib.layout().pcell_id(d['kind']),dict(w=params['w'],l=params['l'],b=0,Calculate='R'))
                    cell=self.ly.cell(self.ly.add_lib_cell(lib,variant));nativecells[key]=cell
                cell=nativecells[key];origin=bounds(cell.bbox())[:2]
                assert abs(cell.bbox().width()*.001-d['width_um'])<1e-8 and abs(cell.bbox().height()*.001-d['height_um'])<1e-8
            dx=d['bbox_um'][0]-origin[0];dy=d['bbox_um'][1]-origin[1];tr=pya.Trans(u(dx),u(dy))
            for k in obs:
                reg=materialized(cell,self.layers[k]);reg.transform(tr);obs[k]+=reg
            counts[d['kind']]+=1
        findings=[];stats={}
        for k in obs:
            obs[k].merge();additions[k].merge()
            collision=additions[k]&obs[k].sized(300)
            stats[k]=dict(known_neighbor_area_um2=obs[k].area()*1e-6,route_area_um2=additions[k].area()*1e-6,
                          clearance_violation_area_um2=collision.area()*1e-6)
            for poly in collision.each():findings.append(dict(layer=k,bbox_um=bounds(poly.bbox())))
        return dict(status='passed' if not findings else 'failed',screen_clearance_um=.3,
                    neighbor_devices=sum(counts.values()),counts=dict(counts),layers=stats,findings=findings,
                    scope='All1002 non-pilot exact native devices with frozen HBT/MOS contacts; route-to-same-layer known-neighbor screen only',
                    future_guards_feeds_fill='not run',neighbor_to_neighbor_stock_legality='not run')

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert a.output.is_dir() and not (a.output/'pilot.gds').exists()
    try:return Build(a.output).run()
    except Exception as exc:
        dump(a.output/'preparation_exception.json',dict(status='failed',type=type(exc).__name__,message=str(exc)))
        raise

if __name__=='__main__':raise SystemExit(main())
