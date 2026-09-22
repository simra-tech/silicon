#!/usr/bin/env python3
"""Frozen-contact MOS routing, exact source placement and physical graph gates."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import pya

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[5]
PACK=ROOT/'designs/g1-guardian/review/audits/coordinated-bbox-pack-586-20260922-r1.json'
SOURCE=HERE.parent.parent/'sim/qualification/candidates/bgr_loop24_qref4_r253p465_hv06/bgr_loop24_qref4_r253p465_hv06.spice'
MOS=ROOT/'build/scratch/bgr-mos-contact-prototypes-20260922-r2'
PINNED={PACK:'2663805a5180a1961850c1068b0c1c3615c010cd2ec47d38a228d65dde4800cb',
SOURCE:'586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b',
MOS/'manifest.json':'0d2e3e723a07d1474180ab4691ee0f1244884bb62b6583bebb7bf7fa300f0fc7'}
PAIRS={'M1':(8,0),'M2':(10,0),'M3':(30,0),'M4':(50,0),'Via1':(19,0),'Via2':(29,0),'Via3':(49,0),
'M3pin':(30,2),'M3txt':(30,25),'NWell':(31,0),'Activ':(1,0),'GatPoly':(5,0)}
METALS=['M1','M2','M3','M4'];CUTS={'Via1':('M1','M2'),'Via2':('M2','M3'),'Via3':('M3','M4')}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def u(x):return int(round(x*1000))
def box(x1,y1,x2,y2):return pya.Box(u(min(x1,x2)),u(min(y1,y2)),u(max(x1,x2)),u(max(y1,y2)))
def bb(b):return[b.left,b.bottom,b.right,b.top]
def region(c,li):
 r=pya.Region(c.begin_shapes_rec(li));r.flatten();return r

class Build:
 def __init__(self,out,subset):
  self.out=out;self.subset=subset;self.ly=pya.Layout();self.ly.dbu=.001;self.top=self.ly.create_cell('bgr_mos_bank')
  self.layers={k:self.ly.layer(*v) for k,v in PAIRS.items()};self.routes=[];self.vias=[];self.probes=[];self.wells=[]
  self.placed=[];self.copies=[];self.inputs={str(p.relative_to(ROOT)):sha(p) for p in PINNED};self.cache={}
 def rect(self,k,n,x1,y1,x2,y2,purpose):
  b=box(x1,y1,x2,y2);self.top.shapes(self.layers[k]).insert(b);self.routes.append(dict(layer=k,net=n,bbox=bb(b),purpose=purpose))
 def wire(self,k,n,x1,y1,x2,y2,w=.3,purpose='wire'):
  assert abs(x1-x2)<1e-8 or abs(y1-y2)<1e-8
  self.rect(k,n,min(x1,x2)-w/2,min(y1,y2)-w/2,max(x1,x2)+w/2,max(y1,y2)+w/2,purpose)
 def via(self,k,n,x,y,axis='y'):
  dx,dy=(.15,.36) if axis=='y' else(.36,.15)
  for layer in CUTS[k]:self.rect(layer,n,x-dx,y-dy,x+dx,y+dy,'via_landing')
  for off in(-.21,.21):
   cx=x+(off if axis=='x' else 0);cy=y+(off if axis=='y' else 0);b=box(cx-.095,cy-.095,cx+.095,cy+.095)
   self.top.shapes(self.layers[k]).insert(b);self.vias.append(dict(layer=k,net=n,bbox=bb(b)))
 def load(self,proto,nodes):
  key=(proto['name'],tuple(nodes))
  if key in self.cache:return self.cache[key]
  path=MOS/(proto['name']+'.gds');assert sha(path)==proto['gds_sha256'];self.inputs[str(path.relative_to(ROOT))]=sha(path)
  ly=pya.Layout();ly.read(str(path));old=ly.top_cell();cell=self.ly.create_cell('contact_%03d'%len(self.cache));cell.copy_tree(old)
  oldnodes=proto['source_line'].split()[1:5];mapping=dict(zip(oldnodes,nodes));assert all(mapping[a]==b for a,b in zip(oldnodes,nodes))
  texts=[]
  for li in ly.layer_indices():
   info=ly.get_info(li);dest=self.ly.layer(info)
   assert(region(old,li)^region(cell,dest)).is_empty()
   for s in list(cell.shapes(dest).each()):
    if s.is_text() and s.text.string in mapping:
     t=s.text;oldtext=t.string;t.string=mapping[t.string];s.text=t
     if oldtext!=t.string:texts.append(dict(layer=info.layer,old=oldtext,new=t.string))
   assert(region(old,li)^region(cell,dest)).is_empty()
  self.copies.append(dict(prototype=proto['name'],nodes=nodes,polygon_XOR=0,text_remap=texts))
  self.cache[key]=cell;return cell
 def prepare(self):
  for p,h in PINNED.items():assert sha(p)==h
  assert pya.__version__=='0.30.9'
  assert Path('/foss/pdks/ihp-sg13g2/COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
  pack=json.loads(PACK.read_text())['BGR_devices'];src={l.split()[0]:l for l in SOURCE.read_text().splitlines() if l.startswith('XM')}
  allmos=[d for d in pack if 'mos' in d['kind']];assert len(allmos)==len(src)==336
  rows=[d for d in allmos if self.subset=='full' or(d['zone']=='nmos10' and d['slot_index']//33==1)]
  assert len(rows)==(336 if self.subset=='full' else 30)
  prototypes=json.loads((MOS/'manifest.json').read_text())['prototypes'];pmap={n:p for p in prototypes for n in p['represented_instances']}
  self.allmos=allmos;self.pmap=pmap
  for d in rows:
   assert src[d['name']]==d['source_line'];f=d['source_line'].split();nodes=f[1:5];params=dict(s.split('=') for s in f[6:])
   w=float(params['w'][:-1]);length=float(params['l'][:-1]);proto=pmap[d['name']];cell=self.load(proto,nodes)
   dx=d['bbox_um'][0]-proto['native_bbox_um'][0];dy=d['bbox_um'][1]-proto['native_bbox_um'][1];x,y=10+dx,10+dy
   self.top.insert(pya.CellInstArray(cell.cell_index(),pya.Trans(u(dx),u(dy))))
   lf=length+.68;gx=x+.34+length/2;drain=x+lf+.15;source=x-.15 if nodes[2]!=nodes[3] else x+.15
   if f[5].endswith('pmos'):
    assert nodes[2]==nodes[3];bulk=x+.35;by=y+w+1.4
    self.wells.append(dict(net=nodes[3],point=[u(x+.35),u(y+w+1.4)],instance=d['name']))
   else:bulk=x-1.93;by=y+.15
   pins=[('D',nodes[0],drain,y+w/2),('G',nodes[1],gx,y-.7),('S',nodes[2],source,y+w/2),('B',nodes[3],bulk,by)]
   if d['zone']=='startup':group=('pmos10',int(round((d['bbox_um'][1]-142)/15.24)))
   else:group=(d['zone'],d['slot_index']//{'pmos10':21,'pmos5':20,'nmos10':33}[d['zone']])
   self.placed.append(dict(d,origin=[x,y],pins=pins,row_group=group))
   for name,net,px,py in pins:self.probes.append(dict(instance=d['name'],terminal=name,net=net,layer='M1',point=[u(px),u(py)]))
  baseline={k:region(self.top,self.layers[k]) for k in ('Activ','GatPoly','NWell')}
  groups=collections.defaultdict(list)
  for d in self.placed:groups[tuple(d['row_group'])].append(d)
  rails={};taps=collections.defaultdict(list)
  for group,ds in groups.items():
   nets=sorted({n for d in ds for _,n,_,_ in d['pins']})
   if group[0]=='pmos10':start=146+15.24*group[1]
   elif group[0]=='pmos5':start=222.6+10.24*group[1]
   else:start=309+15.04*group[1]
   rails[group]={n:start+.8*i for i,n in enumerate(nets)}
   for d in ds:
    for terminal,net,x,y in d['pins']:
     if terminal=='B' and d['source_line'].split()[5].endswith('pmos'):continue
     if terminal=='S' and d['source_line'].split()[3]==d['source_line'].split()[4] and d['kind']=='nmosHV':continue
     self.via('Via1',net,x,y);ty=rails[group][net]
     self.wire('M2',net,x,y,x,ty);self.via('Via2',net,x,ty,axis='x');taps[(group,net,ty)].append(x)
  nets=sorted({p['net'] for p in self.probes});trunks={n:270+i for i,n in enumerate(nets)};ys=collections.defaultdict(list)
  for(group,n,y),xs in taps.items():
   tx=trunks[n];self.wire('M3',n,min(xs+[tx]),y,max(xs+[tx]),y,purpose='row_collector')
   self.via('Via3',n,tx,y,axis='x');ys[n].append(y)
  for i,n in enumerate(nets):
   tx=trunks[n];py=132+.6*i
   self.wire('M4',n,tx,min(ys[n]+[py]),tx,max(ys[n]+[py]),purpose='global_trunk');self.via('Via3',n,tx,py,axis='x')
   self.wire('M3',n,tx,py,419,py,purpose='port_escape')
   self.top.shapes(self.layers['M3pin']).insert(box(418.5,py-.15,419,py+.15))
   self.top.shapes(self.layers['M3txt']).insert(pya.Text(n,pya.Trans(u(418.75),u(py))))
   self.probes.append(dict(instance='port',terminal=n,net=n,layer='M3',point=[u(418.75),u(py)]))
  assert all((region(self.top,self.layers[k])^r).is_empty() for k,r in baseline.items())
  self.ly.write(str(self.out/'bank.gds'))
  (self.out/'bank.cdl').write_text('.subckt bgr_mos_bank '+' '.join(nets)+'\n'+'\n'.join('M'+d['source_line'][2:] for d in rows)+'\n.ends bgr_mos_bank\n')
  dump(self.out/'placement.json',dict(devices=self.placed,copies=self.copies))
  dump(self.out/'route_ledger.json',dict(routes=self.routes,vias=self.vias,probes=self.probes,rails=[dict(group=g,nets=v) for g,v in rails.items()]))
  ly=pya.Layout();ly.read(str(self.out/'bank.gds'));saved=ly.top_cell()
  assert all((region(self.top,li)^region(saved,ly.layer(self.ly.get_info(li)))).is_empty() for li in self.ly.layer_indices())
  graph=self.graph(saved);dump(self.out/'terminal_graph.json',graph)
  nw=region(saved,ly.layer(31,0)).merged();components=collections.defaultdict(set);missing=[]
  for probe in self.wells:
   hits=[i for i,p in enumerate(nw.each()) if p.inside(pya.Point(*probe['point']))]
   if len(hits)!=1:missing.append(probe)
   else:components[hits[0]].add(probe['net'])
  wrong={str(i):sorted(v) for i,v in components.items() if len(v)>1}
  enclosures=[]
  for v in self.vias:
   for k in CUTS[v['layer']]:
    if not(pya.Region(pya.Box(*v['bbox'])).sized(55)-region(saved,ly.layer(*PAIRS[k]))).is_empty():enclosures.append(dict(via=v,layer=k))
  off=[]
  for li in ly.layer_indices():
   for p in region(saved,li).each():
    for pt in p.each_point_hull():
     if pt.x%5 or pt.y%5:off.append([pt.x,pt.y])
  bounds=(pya.Region(saved.bbox())-pya.Region(box(0,0,420,354))).is_empty()
  checks=dict(source_exact=True,native_copy_XOR_zero=True,saved_parity=True,terminal_graph=graph['status']=='passed',
              PMOS_well_domains=not wrong and not missing,via_enclosure=not enclosures,grid=not off,bounds=bounds)
  result=dict(status='passed preparation' if all(checks.values()) else'failed preparation',checks=checks,subset=self.subset,
   device_count=len(rows),terminal_incidence_count=4*len(rows),source_nets=nets,inputs=self.inputs,script_sha256=sha(Path(__file__)),
   gds_sha256=sha(self.out/'bank.gds'),cdl_sha256=sha(self.out/'bank.cdl'),well_domain_shorts=wrong,missing_well_probes=missing,
   enclosure_errors=enclosures,offgrid=off,stock_DRC_LVS='not run',PEX_analog='not run',seed='not applicable')
  dump(self.out/'preparation.json',result);print(json.dumps(result,indent=2));return 0 if all(checks.values()) else 1
 def graph(self,top):
  ly=top.layout();flat=pya.Layout();flat.dbu=.001;ft=flat.create_cell('audit')
  for k in METALS+list(CUTS):
   for p in region(top,ly.layer(*PAIRS[k])).each():ft.shapes(flat.layer(*PAIRS[k])).insert(p)
  ltn=pya.LayoutToNetlist(pya.RecursiveShapeIterator(flat,ft,[]));layers={}
  for k in METALS:layers[k]=ltn.make_layer(flat.layer(*PAIRS[k]),k);ltn.connect(layers[k])
  for k,ends in CUTS.items():
   layer=ltn.make_layer(flat.layer(*PAIRS[k]),k);ltn.connect(layer)
   for end in ends:ltn.connect(layer,layers[end])
  ltn.extract_netlist();expected=collections.defaultdict(set);actual=collections.defaultdict(set);probes=[]
  for p in self.probes:
   node=ltn.probe_net(layers[p['layer']],pya.Point(*p['point']));identity=None if node is None else node.cluster_id
   expected[p['net']].add(identity);actual[identity].add(p['net']);probes.append(dict(p,component=identity))
  opens={n:sorted(v,key=str) for n,v in expected.items() if None in v or len(v)!=1};shorts={str(i):sorted(v) for i,v in actual.items() if len(v)>1}
  return dict(status='passed' if not opens and not shorts else'failed',opens=opens,shorts=shorts,probes=probes)

def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--subset',choices=['nmos30','full'],required=True);a=p.parse_args()
 assert a.output.is_dir() and not(a.output/'bank.gds').exists()
 try:return Build(a.output,a.subset).prepare()
 except Exception as e:dump(a.output/'exception.json',dict(status='failed',type=type(e).__name__,message=str(e)));raise
if __name__=='__main__':raise SystemExit(main())
