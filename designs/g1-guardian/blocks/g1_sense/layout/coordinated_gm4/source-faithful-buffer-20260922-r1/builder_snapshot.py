#!/usr/bin/env python3
"""Prepared isolated, hash-locked derivative of the reproduced OTA generator."""
import argparse,hashlib,json,os,re,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
import g1_layout_lib as lib
from build_native_prototypes import snapshot,probe_record
from audit_junction_defaults import default
pya=lib.pya

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def full_nets(cell,probes):
    flat=pya.Layout();flat.dbu=.001;top=flat.create_cell('buffer_network');metals=(8,10,30,50,67,126)
    cuts={6:(501,5,8),19:(8,10),29:(10,30),49:(30,50),66:(50,67),125:(67,126)}
    regions={layer:snapshot(cell,layer) for layer in (1,5)+metals+tuple(cuts)};regions[501]=regions[1]-regions[5]
    for layer,region in regions.items():
        if layer!=1:
            for p in region.each():top.shapes(flat.layer(layer,0)).insert(p)
    network=pya.LayoutToNetlist(pya.RecursiveShapeIterator(flat,top,[]));layers={}
    for layer in (501,5)+metals:layers[layer]=network.make_layer(flat.layer(layer,0),'L'+str(layer));network.connect(layers[layer])
    for layer,joined in cuts.items():
        cut=network.make_layer(flat.layer(layer,0),'V'+str(layer));network.connect(cut)
        for other in joined:network.connect(cut,layers[other])
    network.extract_netlist();expected={};actual={}
    for q in probes:
        n=network.probe_net(layers[q['layer']],pya.DPoint(*q['point_um']).to_itype(.001));identity=None if n is None else n.cluster_id
        q['physical_net']=identity;expected.setdefault(q['net'],set()).add(identity);actual.setdefault(identity,set()).add(q['net'])
    opens={n:sorted(v,key=str) for n,v in expected.items() if None in v or len(v)!=1};shorts={str(n):sorted(v) for n,v in actual.items() if len(v)!=1}
    return dict(status='passed' if not opens and not shorts else 'failed',opens=opens,shorts=shorts,probes=probes)
PATCHES=[
    ("(1.6, 1, 1), (8, 1, 1), (8, 1, 1)","(1.6, 1, 1), (8, 1, 2), (8, 1, 2)"),
    ("(3.2, 1, 1), (16, 1, 2), (16, 1, 2)","(3.2, 1, 1), (16, 1, 4), (16, 1, 4)"),
    ("(32 * 2.38 + 0.30)","(2 * (16 * 2.38 + 0.30) + 2.40)"),
    ("pattern = 'ABBAABBAABBAABBA'","pattern = 'ABBAABBABAABBAAB'"),
    ("tMB2 = MB2.rail('top', [0]); tMB6 = MB6.rail('top', [0])",
     "tMB2 = MB2.rail('top', [0, 2], lo=4 + Mos.RAIL_LO, hi=4 + Mos.RAIL_HI); tMB6 = MB6.rail('top', [0, 2], lo=4 + Mos.RAIL_LO, hi=4 + Mos.RAIL_HI)"),
    ("rMB5 = MB5.rail('bot', [1]); rMB3 = MB3.rail('bot', [1])",
     "rMB5 = MB5.rail('bot', MB5.strips(1)); rMB3 = MB3.rail('bot', MB3.strips(1))"),
    ("tMB5 = MB5.rail('top', [0, 2]); tMB3 = MB3.rail('top', [0, 2])",
     "tMB5 = MB5.rail('top', MB5.strips(0), lo=4 + Mos.RAIL_LO, hi=4 + Mos.RAIL_HI); tMB3 = MB3.rail('top', MB3.strips(0), lo=4 + Mos.RAIL_LO, hi=4 + Mos.RAIL_HI)")]

def build(ly,artifacts=None):
    original=Path(__file__).resolve().parent.parent/'g1_ota_layout.py'
    assert sha(original)=='8dbbf40299c8971d9c3280c1d1dcc38d7318e3750853fb0fd2607ec7c142b92b'
    text=original.read_text()
    for old,new in PATCHES:
        assert text.count(old)==1,old
        text=text.replace(old,new)
    if artifacts is not None:
        (artifacts/'derived_ota_generator.py').write_text(text)
    captured=[];Base=lib.Mos
    class SplitCapture(Base):
        def __init__(self,D,kind,w,l,nf,x0,y0):
            self.split=(kind,w,l,nf)==('pmosHV',192,2,32)
            if not self.split:super().__init__(D,kind,w,l,nf,x0,y0)
            else:
                self.D,self.kind,self.w,self.l,self.nf,self.x0,self.y0=D,kind,w,l,nf,x0,y0
                self.wf=6.;self.pitch=2.38;self.actw=2*(16*2.38+.3)+2.4;self.is_p=self.hv=True
                self.second_x=x0+16*2.38+.3+2.4
                for x in (x0,self.second_x):D.pcell('pmosHV',{'w':'96u','l':'2u','ng':16},x,y0)
            captured.append(self)
        def gx(self,k):
            if not self.split:return super().gx(k)
            return (self.x0 if k<16 else self.second_x)+.34+self.l/2+(k%16)*self.pitch
        def sx(self,k):
            if not self.split:return super().sx(k)
            if k==33:return self.x0+.15+16*self.pitch
            return (self.x0 if k<16 else self.second_x)+.15+(k if k<16 else k-16)*self.pitch
        def strips(self,parity):
            if not self.split:return super().strips(parity)
            return list(range(parity,33,2))+([33] if parity==0 else [])
        def end_dummies(self,clear=.2):
            if not self.split:return super().end_dummies(clear)
            for x in (self.x0-clear-self.l/2,self.second_x-clear-self.l/2,self.x1+clear+self.l/2):self.dummy(x)
    lib.Mos=SplitCapture
    try:
        namespace={'__file__':str(original),'__name__':'isolated_buffer_generator'}
        exec(compile(text,str(original), 'exec'),namespace)
        cell,info=namespace['build_ota'](ly,'g1_ota_source_faithful')
    finally:lib.Mos=Base
    return cell,info,captured,hashlib.sha256(text.encode()).hexdigest()

def audit(cell,mos,source):
    block=re.search(r'(?ms)^\.subckt g1_ota .*?^\.ends',source.read_text()).group(0)
    specs={line.split()[0]:line for line in block.splitlines() if line.startswith('X')}
    names=['XMB4','XMB2','XMB6','XM3','XM13','XM16','XM4','XM21','XM14','XM15','XM12','XM11','PAIR','XMB7','XMB5','XMB3','XMT','XM20']
    assert len(names)==len(mos);active=snapshot(cell,1);poly=snapshot(cell,5);probes=[];records=[]
    for name,m in zip(names,mos):
        chains=[(m.x0,m.nf)] if not m.split else [(m.x0,16),(m.second_x,16)]
        allocations={n:dict(as_um2=0.,ad_um2=0.,ps_um=0.,pd_um=0.) for n in (['XM1','XM2'] if m.split else [name])};logical_gates={n:[] for n in allocations}
        for j,(x,nf) in enumerate(chains):
            clip=pya.Region(pya.DBox(x,m.y0,x+nf*m.pitch+.3,m.y1).to_itype(.001));act=active&clip;channels=act&poly
            boxes=sorted([p.bbox() for p in channels.each()],key=lambda b:b.left)
            assert len(boxes)==nf and all(abs(b.width()*.001-m.l)<1e-8 and abs(b.height()*.001-m.wf)<1e-8 for b in boxes)
            strips=sorted((act-poly).each(),key=lambda p:p.bbox().left);assert len(strips)==nf+1
            groups=('ABBA' if j==0 else 'BAAB')*2
            owners=[('XM1' if groups[k//2]=='A' else 'XM2') if m.split else name for k in range(nf)]
            for k,b in enumerate(boxes):
                owner=owners[k];words=specs[owner].split();logical_gates[owner].append([b.center().x*.001,b.center().y*.001])
                probe_record(probes,owner,'gate',words[2],5,b.center().x*.001,b.center().y*.001)
            for k,p in enumerate(strips):
                b=p.bbox()
                if k%2:weights={owners[k]:1.};terminal='drain';field='d'
                else:
                    adjacent=owners[max(0,k-1):min(nf,k+1)];weights={n:adjacent.count(n)/len(adjacent) for n in allocations if n in adjacent};terminal='source';field='s'
                netnames={specs[n].split()[1 if field=='d' else 3] for n in weights};assert len(netnames)==1
                probe_record(probes,name,terminal,next(iter(netnames)),501,b.center().x*.001,b.center().y*.001)
                for owner,weight in weights.items():allocations[owner]['a'+field+'_um2']+=p.area()*1e-6*weight;allocations[owner]['p'+field+'_um']+=p.perimeter()*.001*weight
        for owner,points in logical_gates.items():
            params=dict(re.findall(r'(\w+)=([^\s]+)',specs[owner]));nf=int(params['ng']);w=float(params['w'].rstrip('u'));l=float(params['l'].rstrip('u'))
            expected=default(w,nf);assert len(points)==nf and abs(nf*m.wf-w)<1e-8 and m.l==l
            assert all(abs(allocations[owner][k]-expected[k])<1e-8 for k in expected)
            records.append(dict(device=owner,source_line=specs[owner],actual_ng=len(points),actual_W_um=nf*m.wf,L_um=l,
                adjacent_gate_junction=allocations[owner],expected_default_junction=expected,gate_centroid_um=[sum(p[i] for p in points)/nf for i in (0,1)],
                allocation_scope='Prospective allocation, not intrinsic shared-source/mismatch applicability' if m.split else 'Independent native device'))
    pair=[r for r in records if r['device'] in ('XM1','XM2')];assert all(abs(pair[0]['gate_centroid_um'][i]-pair[1]['gate_centroid_um'][i])<1e-8 for i in (0,1))
    for metal in (8,10,30,50,67,126):
        it=cell.begin_shapes_rec(cell.layout().layer(metal,25))
        while not it.at_end():
            if it.shape().is_text():
                t=it.shape().text;point=it.trans()*t.trans.disp
                probe_record(probes,'pin','anchor',t.string,metal,point.x*.001,point.y*.001)
            it.next()
    terminal=full_nets(cell,probes);assert terminal['status']=='passed',terminal
    assert len(records)==19
    resistor=snapshot(cell,128);capacitor=snapshot(cell,36)
    assert resistor.count()==1 and capacitor.count()==1
    rb=resistor.bbox();cb=capacitor.bbox()
    assert abs(rb.width()*.001-1)<1e-8 and abs(rb.height()*.001-6.2)<1e-8 and abs(resistor.area()*1e-6-6.2)<1e-8
    assert cb.width()==23000 and cb.height()==23000 and capacitor.area()==23000**2
    return dict(status='passed19MOS scoped source/terminal audit',devices=records,terminal_audit=terminal,
                resistor_capacitor_geometry=dict(status='passed source dimensions',RZ_W_um=1,RZ_L_um=6.2,CC_W_um=23,CC_L_um=23,terminal_LVS='not run'),shared_junction_model_applicability='not run')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists() and pya.__version__=='0.30.9' and os.sched_getaffinity(0)=={7}
    source=Path(__file__).resolve().parents[2]/'reports/resume-server-20260922/gm4comp3-qualified-source.spice';assert sha(source)=='baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877'
    a.output.mkdir(parents=True)
    (a.output/'builder_snapshot.py').write_bytes(Path(__file__).read_bytes())
    try:
        ly=pya.Layout();ly.dbu=.001;cell,info,mos,derived_sha=build(ly,a.output);report=audit(cell,mos,source)
        b=cell.bbox();assert b.width()*.001<=110 and b.height()*.001<=65
    except Exception as exc:
        failure=dict(status='failed initial geometry/audit',exception_type=type(exc).__name__,detail=str(exc),
                     source_sha256=sha(source),script_sha256=sha(Path(__file__)),GDS='not saved',
                     stock_checks='not run',full_SENSE='not run',adoption='not run',
                     artifact_hashes={p.name:sha(p) for p in a.output.iterdir() if p.is_file()})
        (a.output/'failure.json').write_text(json.dumps(failure,indent=2)+'\n')
        print(json.dumps(failure,indent=2));raise
    gds=a.output/'g1_ota_source_faithful.gds';ly.write(str(gds))
    result=dict(status='passed bounded MOS/source/terminal gate; R/C saved-view/stock gates pending',source_sha256=sha(source),GDS_sha256=sha(gds),
                script_sha256=sha(Path(__file__)),derived_generator_sha256=derived_sha,patches=[dict(before=x,after=y,occurrence_count=1) for x,y in PATCHES],
                bbox_um=[q*.001 for q in (b.left,b.bottom,b.right,b.top)],width_um=b.width()*.001,height_um=b.height()*.001,
                independent_audit=report,stock_checks='not run',full_SENSE='not run',adoption='not run')
    (a.output/'manifest.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('independent_audit','patches')},indent=2))
if __name__=='__main__':main()
