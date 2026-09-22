#!/usr/bin/env python3
"""Source586 assembly from three immutable stock-qualified component banks."""
import argparse,collections,hashlib,json,os
from pathlib import Path
import pya
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[5]
BULK=Path(os.environ['G1_RESULTS_ROOT'])
SOURCE=HERE.parent.parent/'sim/qualification/candidates/bgr_loop24_qref4_r253p465_hv06/bgr_loop24_qref4_r253p465_hv06.spice'
R=ROOT/'build/scratch/bgr-resistor-bank-pilot-20260922-r2'
H=ROOT/'build/scratch/bgr-hbt-fullbank-20260922-r2'
M=BULK/'bgr-mos-full-20260922-r2'
PAIRS={'M1':(8,0),'M2':(10,0),'M3':(30,0),'M4':(50,0),'M5':(67,0),
       'Via1':(19,0),'Via2':(29,0),'Via3':(49,0),'Via4':(66,0)}
METALS=['M1','M2','M3','M4','M5'];CUTS={'Via1':('M1','M2'),'Via2':('M2','M3'),'Via3':('M3','M4'),'Via4':('M4','M5')}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def u(x):return round(x*1000)
def box(x1,y1,x2,y2):return pya.Box(u(min(x1,x2)),u(min(y1,y2)),u(max(x1,x2)),u(max(y1,y2)))
def bb(b):return[b.left,b.bottom,b.right,b.top]
def region(c,l):
 r=pya.Region(c.begin_shapes_rec(l));r.flatten();return r
def native_texts(c):
 ly=c.layout();rows=[]
 for li in ly.layer_indices():
  info=ly.get_info(li)
  if info.layer in(8,10,30,50,67) and info.datatype in(2,25):continue
  it=c.begin_shapes_rec(li)
  while not it.at_end():
   if it.shape().is_text():
    t=it.shape().text;rows.append((info.layer,info.datatype,t.string,str(it.trans()*t.trans)))
   it.next()
 return sorted(rows)
class Assembly:
 def __init__(self,out):
  self.out=out;self.ly=pya.Layout();self.ly.dbu=.001;self.top=self.ly.create_cell('g1_bgr')
  self.layers={k:self.ly.layer(*p) for k,p in PAIRS.items()};self.routes=[];self.vias=[];self.probes=[];self.inputs={};self.copy_audits=[]
 def bind(self,p,expected=None):
  h=sha(p)
  if expected:assert h==expected,(p,h)
  self.inputs[str(p)]=h;return p
 def rect(self,k,n,x1,y1,x2,y2,why):
  b=box(x1,y1,x2,y2);self.top.shapes(self.layers[k]).insert(b);self.routes.append(dict(layer=k,net=n,bbox=bb(b),purpose=why))
 def wire(self,k,n,x1,y1,x2,y2,why):
  assert x1==x2 or y1==y2
  self.rect(k,n,min(x1,x2)-.15,min(y1,y2)-.15,max(x1,x2)+.15,max(y1,y2)+.15,why)
 def via(self,k,n,x,y,axis='x'):
  dx,dy=(.36,.15) if axis=='x' else(.15,.36)
  for m in CUTS[k]:self.rect(m,n,x-dx,y-dy,x+dx,y+dy,'via_landing')
  for d in(-.21,.21):
   cx=x+(d if axis=='x' else 0);cy=y+(d if axis=='y' else 0);b=box(cx-.095,cy-.095,cx+.095,cy+.095)
   self.top.shapes(self.layers[k]).insert(b);self.vias.append(dict(layer=k,net=n,bbox=bb(b)))
 def stack(self,n,x,y,axis='x'):
  self.via('Via3',n,x,y,axis);self.via('Via4',n,x,y,axis)
 def copy(self,name,path,h):
  ly=pya.Layout();ly.read(str(self.bind(path,h)));old=ly.top_cell();cell=self.ly.create_cell(name);cell.copy_tree(old)
  # Remove only metal bank labels/pins, never native device recognition text.
  expected_texts=native_texts(old)
  drawing={tuple((ly.get_info(i).layer,ly.get_info(i).datatype)):region(old,i) for i in ly.layer_indices()
           if not(ly.get_info(i).layer in(8,10,30,50,67) and ly.get_info(i).datatype in(2,25))}
  removed=collections.Counter()
  for c in self.ly.each_cell():
   for li in self.ly.layer_indices():
    for s in list(c.shapes(li).each()):
     info=self.ly.get_info(li)
     if info.layer in(8,10,30,50,67) and info.datatype in(2,25):removed[str(info)]+=1;s.delete()
  assert all((r^region(cell,self.ly.layer(*pair))).is_empty() for pair,r in drawing.items())
  assert native_texts(cell)==expected_texts
  self.top.insert(pya.CellInstArray(cell.cell_index(),pya.Trans()))
  self.copy_audits.append(dict(bank=name,drawing_XOR=0,native_text_parity=True,native_text_count=len(expected_texts),removed_bank_annotations=dict(removed)))
 def graph(self,top,removed=(),precision=False):
  ly=top.layout();flat=pya.Layout();flat.dbu=.001;ft=flat.create_cell('audit')
  for k,pair in PAIRS.items():
   r=region(top,ly.layer(*pair))
   if k=='Via3':
    for role in removed:
     for b in self.star[role]:r-=pya.Region(pya.Box(*b))
   if k=='M2' and precision:r-=pya.Region(box(15.5,15.50,16.5,15.82))
   for poly in r.each():ft.shapes(flat.layer(*pair)).insert(poly)
  ltn=pya.LayoutToNetlist(pya.RecursiveShapeIterator(flat,ft,[]));layers={}
  for k in METALS:layers[k]=ltn.make_layer(flat.layer(*PAIRS[k]),k);ltn.connect(layers[k])
  for k,ends in CUTS.items():
   cut=ltn.make_layer(flat.layer(*PAIRS[k]),k);ltn.connect(cut)
   for end in ends:ltn.connect(cut,layers[end])
  ltn.extract_netlist();expected=collections.defaultdict(set);actual=collections.defaultdict(set);observations=[]
  for p in self.probes:
   role=p.get('role',p['net']);want=role if role in removed else p['net']
   if precision and role in('return_XQ56','precision_XR16'):want='precision_XR16_XQ56'
   node=ltn.probe_net(layers[p['layer']],pya.Point(*p['point']));i=None if node is None else node.cluster_id
   expected[want].add(i);actual[i].add(want);observations.append(dict(p,expected=want,component=i))
  opens={n:sorted(v,key=str) for n,v in expected.items() if None in v or len(v)!=1};shorts={str(i):sorted(v) for i,v in actual.items() if len(v)>1}
  return dict(status='passed' if not opens and not shorts else'failed',removed_star_interfaces=list(removed),precision_stem_cut=precision,
              expected_net_count=len(expected),physical_net_count=len(actual),opens=opens,shorts=shorts,observations=observations)
 def prepare(self):
  assert pya.__version__=='0.30.9'
  assert Path('/foss/pdks/ihp-sg13g2/COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
  self.bind(SOURCE,'586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b')
  rp=json.loads(self.bind(R/'manifest.json').read_text());hp=json.loads(self.bind(H/'preparation.json').read_text());mp=json.loads(self.bind(M/'preparation.json').read_text())
  for path in (BULK/'bgr-mos-full-20260922-r2-drc/summary.json',BULK/'bgr-mos-full-20260922-r2-lvs/summary.json',
               ROOT/'build/scratch/bgr-resistor-bank-stock-20260922-r2/summary.json',
               ROOT/'build/scratch/bgr-hbt-fullbank-stock-20260922-r2-drc/summary.json',
               ROOT/'build/scratch/bgr-hbt-fullbank-stock-20260922-r2-lvs/summary.json'):
   assert json.loads(self.bind(path).read_text())['status']=='passed'
  self.copy('resistor_bank',R/'bgr_resistor_bank_pilot.gds','4019838faa0efb2b5038e69f9652c6e52eb60ab070ac964f2d39f72af29e0d17')
  self.copy('hbt_bank',H/'bank.gds','7a8c57b6a05b0cadd4443bb04a3b629b9da23b3919cf16d723122c12fae34e2c')
  self.copy('mos_bank',M/'bank.gds',mp['gds_sha256'])
  initial={tuple((self.ly.get_info(i).layer,self.ly.get_info(i).datatype)):region(self.top,i) for i in self.ly.layer_indices() if self.ly.get_info(i).datatype==0}
  for p in rp['terminal_probes']:
   role='precision_XR16' if p['instance'].split('_u')[0]=='XR16' and p['net']=='vss' else p['net']
   self.probes.append(dict(instance=p['instance'],terminal=p['terminal'],net=p['net'],role=role,layer=p['layer'],point=[u(x) for x in p['point_um']]))
  hl=json.loads(self.bind(H/'route_ledger.json').read_text());self.star=hl['star_interfaces']
  for p in hl['probes']:self.probes.append(dict(p,point=p['point_dbu']))
  ml=json.loads(self.bind(M/'route_ledger.json').read_text());self.probes+=ml['probes']
  mnets=mp['source_nets'];trunks={n:403.7+.75*i for i,n in enumerate(mnets)};ports={n:132+.6*i for i,n in enumerate(mnets)}
  tracks=rp['tracks_um'];shared=sorted(set(mnets)&set(tracks));assert shared==['det','pbias','pcasc','vb2','vref','vss']
  def mos_link(n,y):
   x=trunks[n];self.stack(n,x,ports[n]);self.wire('M5',n,x,y,x,ports[n],'MOS_bank_connector')
  for n in shared:
   x=trunks[n];y=tracks[n];self.wire('M3',n,403,y,x,y,'resistor_collector_extension');self.stack(n,x,y);mos_link(n,y)
  hm4=region(self.top,self.layers['M4']);chosen=[];assign=[]
  horder=['b1b','c2','dvbe','vbe','vbe3','vd1','vd2'];cross={'b1b':129.8,'c2':130.6,'vbe':131.4}
  for n in horder[:-1]:
   py=136+.6*horder.index(n);target=cross[n] if n in cross else tracks[n]
   candidates=[200.8+.005*i for i in range(2600)]
   good=[]
   for x in candidates:
    if all(abs(x-v)>=1.1-1e-9 for v in chosen) and (pya.Region(box(x-.15,target-.36,x+.15,target+.36)).sized(210)&hm4).is_empty():good.append(x);break
   assert good,('no HBT landing escape',n)
   x=good[0];chosen.append(x);assign.append(dict(net=n,x_um=x,port_y_um=py,target_y_um=target,M4_obstacle_gap_dbu=210))
   self.wire('M3',n,200.5,py,x,py,'HBT_port_extension');self.stack(n,x,py)
   self.wire('M5',n,x,target,x,py,'HBT_bank_connector')
   if n in cross:
    self.via('Via4',n,x,target,axis='y');self.wire('M4',n,x,target,trunks[n],target,'interbank_crossing')
    self.via('Via4',n,trunks[n],target,axis='y');mos_link(n,target)
   else:self.stack(n,x,target,axis='y')
  source_lines=SOURCE.read_text().splitlines();ports_source=next(l.split()[2:] for l in source_lines if l.lower().startswith('.subckt'))
  assert len(ports_source)==9
  for n in ports_source:
   y=ports[n] if n in ports else tracks[n]
   if n not in ports:self.wire('M3',n,403,y,419,y,'external_port_extension')
   self.top.shapes(self.ly.layer(30,2)).insert(box(418.5,y-.15,419,y+.15));self.top.shapes(self.ly.layer(30,25)).insert(pya.Text(n,pya.Trans(u(418.75),u(y))))
   self.probes.append(dict(instance='full_port',terminal=n,net=n,layer='M3',point=[u(418.75),u(y)]))
  devices=[l for l in source_lines if l.startswith(('XM','XR','XQ'))];assert len(devices)==1036
  cdl=[]
  for l in devices:
   cdl.append(('M'+l[2:]) if l.startswith('XM') else l[1:])
  (self.out/'bank.cdl').write_text('.subckt g1_bgr '+' '.join(ports_source)+'\n'+'\n'.join(cdl)+'\n.ends g1_bgr\n')
  native_pairs=[p for p in initial if p not in set(PAIRS.values())]
  assert all((initial[p]^region(self.top,self.ly.layer(*p))).is_empty() for p in native_pairs)
  self.ly.write(str(self.out/'bank.gds'));savedly=pya.Layout();savedly.read(str(self.out/'bank.gds'));saved=savedly.top_cell()
  assert all((region(self.top,i)^region(saved,savedly.layer(self.ly.get_info(i)))).is_empty() for i in self.ly.layer_indices())
  previous=BULK/'bgr-assembly-20260922-r2'
  if self.out!=previous and previous.is_dir():
   prior=pya.Layout();prior.read(str(self.bind(previous/'bank.gds')))
   changed=[]
   for i in savedly.layer_indices():
    info=savedly.get_info(i);delta=region(saved,i)^region(prior.top_cell(),prior.layer(info))
    if not delta.is_empty():changed.append(dict(layer=info.to_s(),area_dbu2=delta.area(),polygons=delta.count()));assert(info.layer,info.datatype) in(PAIRS['M4'],PAIRS['M5'],PAIRS['Via4'],(5,2),(63,0))
   assert (self.out/'bank.cdl').read_bytes()==self.bind(previous/'bank.cdl').read_bytes()
   dump(self.out/'revision_audit.json',dict(status='passed',unchanged_layers_except_M4_M5_Via4_and_native_annotation_restoration=True,changed_layer_ledger=changed,CDL_byte_identical=True,
        change='Restore native device recognition annotations; change two interbank bridge heights for stock M4 spacing.',
        precision_resistor_probe_count=sum(p.get('role')=='precision_XR16' for p in self.probes)))
  dump(self.out/'routing.json',dict(routes=self.routes,vias=self.vias,HBT_column_assignment=assign,source_probes=self.probes,copy_audits=self.copy_audits))
  graph=self.graph(saved);dump(self.out/'terminal_graph.json',graph)
  cuts=[]
  if graph['status']=='passed':
   for role in self.star:cuts.append(self.graph(saved,(role,)))
   cuts.append(self.graph(saved,tuple(self.star)));cuts.append(self.graph(saved,precision=True))
  dump(self.out/'star_cuts.json',cuts)
  metal={k:region(saved,savedly.layer(*PAIRS[k])) for k in METALS};enclosure=[]
  for v in self.vias:
   for k in CUTS[v['layer']]:
    if not(pya.Region(pya.Box(*v['bbox'])).sized(55)-metal[k]).is_empty():enclosure.append(dict(via=v,layer=k))
  off=[]
  for li in savedly.layer_indices():
   for p in region(saved,li).each():
    for pt in p.each_point_hull():
     if pt.x%5 or pt.y%5:off.append([pt.x,pt.y])
  checks=dict(source1036=True,bank_native_drawing_XOR=True,saved_parity=True,terminal_graph=graph['status']=='passed',
              seven_star_cuts=len(cuts)==7 and all(c['status']=='passed' for c in cuts),via_enclosures=not enclosure,
              grid=not off,bounds=(pya.Region(saved.bbox())-pya.Region(box(0,0,420,354))).is_empty())
  result=dict(status='passed preparation' if all(checks.values()) else'failed preparation',checks=checks,inputs=self.inputs,
              source_count=1036,source_ports=ports_source,source_nets=sorted({p['net'] for p in self.probes}),source_terminal_probes=len(self.probes),
              enclosure_errors=enclosure,offgrid=off,gds_sha256=sha(self.out/'bank.gds'),cdl_sha256=sha(self.out/'bank.cdl'),
              script_sha256=sha(Path(__file__)),stock_PEX_electrical='not run',seed='not applicable')
  dump(self.out/'preparation.json',result);print(json.dumps(result,indent=2));return 0 if all(checks.values()) else 1
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert a.output.is_dir() and not(a.output/'bank.gds').exists()
 try:return Assembly(a.output).prepare()
 except Exception as e:dump(a.output/'exception.json',dict(status='failed',type=type(e).__name__,message=str(e)));raise
if __name__=='__main__':raise SystemExit(main())
