#!/usr/bin/env python3
"""Isolated native/contact prototypes with independent immutable polygon snapshots."""
import argparse,hashlib,json,os
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
import g1_layout_lib as lib
from audit_junction_defaults import default
pya=lib.pya

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def snapshot(cell,layer):
    result=pya.Region()
    for poly in pya.Region(cell.begin_shapes_rec(cell.layout().layer(layer,0))).each():result.insert(pya.Polygon(poly))
    return result.merged()
def point(box):return [(box[0]+box[2])/2,(box[1]+box[3])/2]
def measure_native(m,before):
    clip=pya.Region(pya.DBox(m.x0,m.y0,m.x1,m.y1).to_itype(.001));active=before[1]&clip;channels=active&before[5]
    boxes=[r.bbox() for r in channels.each()]
    assert len(boxes)==m.nf and all(abs(b.width()*.001-m.l)<1e-9 and abs(b.height()*.001-m.wf)<1e-9 for b in boxes)
    strips=sorted((active-before[5]).each(),key=lambda r:r.bbox().left)
    assert len(strips)==m.nf+1
    junction=dict(as_um2=sum(r.area()*1e-6 for r in strips[::2]),ad_um2=sum(r.area()*1e-6 for r in strips[1::2]),
                  ps_um=sum(r.perimeter()*.001 for r in strips[::2]),pd_um=sum(r.perimeter()*.001 for r in strips[1::2]))
    assert all(abs(junction[k]-default(m.w,m.nf)[k])<1e-8 for k in junction)
    return strips,dict(ng=len(boxes),W_um=sum(b.height()*.001 for b in boxes),L_um=m.l,junction=junction)
def probe_record(rows,name,terminal,net,layer,x,y):rows.append(dict(device=name,terminal=terminal,net=net,layer=layer,point_um=[x,y]))
def pin(D,rows,name,layer,x,y):
    D.pin(layer,x-.2,y-.2,x+.2,y+.2,name)
    probe_record(rows,'pin','anchor',name,lib.LAYERS[layer][0],x,y)

def guards(D,extent,pmos,rows,source_connect=None):
    x1,y1,x2,y2=extent
    if pmos:
        inside=(x1-3,y1-3,x2+3,y2+3)
        D.box('NWell',inside[0]-.6,inside[1]-.6,inside[2]+.6,inside[3]+.6)
        nt=D.tap_ring(*inside,ptype=False)
        pin(D,rows,'vdd','M1',nt[0],(y1+y2)/2)
        st=D.tap_ring(x1-5,y1-5,x2+5,y2+5,ptype=True)
        pin(D,rows,'vss','M1',st[0],(y1+y2)/2)
        tie=nt
    else:
        tie=D.tap_ring(x1-3,y1-3,x2+3,y2+3,ptype=True)
        pin(D,rows,'vss','M1',tie[0],(y1+y2)/2)
    if source_connect:
        x,y=source_connect;D.stack(x,y,'M1','M2');D.stack(tie[0],y,'M1','M2');D.hwire('M2',tie[0],x,y,.4)
    D.boundary(x1-(5.6 if pmos else 3.6),y1-(5.6 if pmos else 3.6),x2+(5.6 if pmos else 3.6),y2+(5.6 if pmos else 3.6))

def nets(cell,probes):
    source=cell.layout();flat=pya.Layout();flat.dbu=.001;top=flat.create_cell('flat')
    regions={layer:snapshot(cell,layer) for layer in (1,5,6,8,10,19,29,30)}
    regions[501]=regions[1]-regions[5]
    for layer,region in regions.items():
        if layer==1:continue
        for poly in region.each():top.shapes(flat.layer(layer,0)).insert(poly)
    network=pya.LayoutToNetlist(pya.RecursiveShapeIterator(flat,top,[]));layers={}
    for layer in (501,5,8,10,30):layers[layer]=network.make_layer(flat.layer(layer,0),'L'+str(layer));network.connect(layers[layer])
    for layer,joins in {6:(501,5,8),19:(8,10),29:(10,30)}.items():
        cut=network.make_layer(flat.layer(layer,0),'V'+str(layer));network.connect(cut)
        for target in joins:network.connect(cut,layers[target])
    network.extract_netlist();expected={};actual={}
    for row in probes:
        n=network.probe_net(layers[row['layer']],pya.DPoint(*row['point_um']).to_itype(.001));identity=None if n is None else n.cluster_id
        row['physical_net']=identity;expected.setdefault(row['net'],set()).add(identity);actual.setdefault(identity,set()).add(row['net'])
    opens={n:sorted(v,key=str) for n,v in expected.items() if None in v or len(v)!=1}
    shorts={str(n):sorted(v) for n,v in actual.items() if len(v)!=1}
    return dict(status='passed' if not opens and not shorts else 'failed',opens=opens,shorts=shorts,probes=probes)

def build_bias(ly,name,kind,w,nf):
    cell=ly.create_cell(name);D=lib.Draw(ly,cell);m=lib.Mos(D,kind,w,1,nf,0,0)
    before={layer:snapshot(cell,layer) for layer in (1,5)};probes=[]
    strips,native_measure=measure_native(m,before)
    m.end_dummies();gate=m.gate_bar('bot');m.rail('bot',m.strips(1));m.rail('top',m.strips(0))
    supply='vdd' if kind=='pmosHV' else 'vss'
    pin(D,probes,'g','M2',m.gx(0),-.33);pin(D,probes,'d','M1',m.sx(1),-1.03)
    guards(D,(0,0,m.x1,m.wf),kind=='pmosHV',probes,(m.sx(0),m.wf+1.03))
    for k in range(nf):probe_record(probes,name,'gate','g',5,m.gx(k),m.wf/2)
    for k in range(nf+1):probe_record(probes,name,'source' if k%2==0 else 'drain',supply if k%2==0 else 'd',501,m.sx(k),m.wf/2)
    active=snapshot(cell,1);poly=snapshot(cell,5);channel_before=before[1]&before[5];channel_after=active&poly
    assert (channel_after^channel_before).is_empty() and (before[1]-active).is_empty()
    data=dict(cell=name,kind=kind,W_um=w,L_um=1,ng=nf,native_channel_XOR_um2=0,native_Activ_removed_um2=0,
              added_body_tap_Activ_um2=(active-before[1]).area()*1e-6,expected_model_junction=default(w,nf),
              native_snapshot_materialized=True,actual_native_measurement=native_measure,terminal_audit=nets(cell,probes))
    return cell,data

def build_pair(ly,name,nf,control):
    cell=ly.create_cell(name);D=lib.Draw(ly,cell);w=nf*6;active_width=nf*2.38+.3
    chain=[lib.Mos(D,'pmosHV',w,2,nf,x,0) for x in (0,active_width+2.4)]
    before={layer:snapshot(cell,layer) for layer in (1,5)};probes=[];gates=[];allocated={n:dict(as_um2=0.,ad_um2=0.,ps_um=0.,pd_um=0.) for n in ('A','B')}
    endpoints={n:[] for n in ('inn','inp','fn','fp','tail')}
    native_measurements=[]
    for j,m in enumerate(chain):
        strips,native_measure=measure_native(m,before);native_measurements.append(native_measure)
        groups=('ABBA' if j==0 else 'BAAB')*(nf//8)
        owners=[('A' if j==0 else 'B') if control else groups[k//2] for k in range(nf)]
        m.end_dummies()
        for owner,side,gate_net,drain_net in (('A','bot','inn','fn'),('B','top','inp','fp')):
            ks=[k for k,n in enumerate(owners) if n==owner]
            if not ks:continue
            for k in ks:m.gate_pad(k,side)
            y=m.yd(side,.33);D.hwire('M2',m.gx(ks[0]),m.gx(ks[-1]),y,.38)
            endpoints[gate_net].append((m.gx(ks[0]),y));endpoints[gate_net].append((m.gx(ks[-1]),y))
            ds=[2*k+1 for k in range(nf//2) if owners[2*k]==owner]
            m.rail(side,ds);x,y=m.sx(ds[0]),m.yd(side,1.03);D.stack(x,y,'M1','M2');endpoints[drain_net].append((x,y))
        for k in range(nf):
            gates.append(dict(chain=j,finger=k,owner=owners[k],center_um=[m.gx(k),3]))
            probe_record(probes,'M1' if owners[k]=='A' else 'M2','gate','inn' if owners[k]=='A' else 'inp',5,m.gx(k),3)
        for k in range(nf+1):
            area=strips[k].area()*1e-6;perimeter=strips[k].perimeter()*.001
            if k%2:
                owner=owners[k];weights={owner:1};signal='fn' if owner=='A' else 'fp';suffix='d'
            else:
                adj=owners[max(0,k-1):min(nf,k+1)];weights={n:adj.count(n)/len(adj) for n in ('A','B') if n in adj};signal='tail';suffix='s'
                x,y=m.strip_pad(k,'top',-.35,hi='M3');D.vwire('M3',x,y,8.8,.3);endpoints['tail'].append((x,8.8))
            for owner,weight in weights.items():allocated[owner]['a'+suffix+'_um2']+=weight*area;allocated[owner]['p'+suffix+'_um']+=weight*perimeter
            probe_record(probes,'pair','source' if k%2==0 else 'drain',signal,501,m.sx(k),3)
    for signal,pts in endpoints.items():
        ys={round(y,8) for x,y in pts};assert len(ys)==1
        xs=[x for x,y in pts];y=pts[0][1];metal='M3' if signal=='tail' else 'M2'
        D.hwire(metal,min(xs),max(xs),y,.4 if signal in ('fn','fp','tail') else .38)
        pin(D,probes,signal,metal,min(xs),y)
    guards(D,(0,0,chain[-1].x1,8.8),True,probes)
    afteractive=snapshot(cell,1);afterpoly=snapshot(cell,5)
    assert ((before[1]&before[5])^(afteractive&afterpoly)).is_empty() and (before[1]-afteractive).is_empty()
    expected=default(w,nf);assert all(abs(allocated[n][key]-expected[key])<1e-8 for n in ('A','B') for key in expected)
    centers={n:[sum(g['center_um'][axis] for g in gates if g['owner']==n)/nf for axis in (0,1)] for n in ('A','B')}
    if not control:assert all(abs(centers['A'][i]-centers['B'][i])<1e-8 for i in (0,1))
    data=dict(cell=name,control=control,native_chain_count=2,logical_W_um=w,L_um=2,logical_ng=nf,
              native_channel_XOR_um2=0,native_Activ_removed_um2=0,added_body_tap_Activ_um2=(afteractive-before[1]).area()*1e-6,
              native_snapshot_materialized=True,actual_native_chain_measurements=native_measurements,logical_gate_centroids_um=centers,expected_model_junction=expected,
              adjacent_gate_junction_allocation=allocated,allocation_scope='Prospective shared-source assignment, not per-device model applicability pass',terminal_audit=nets(cell,probes))
    return cell,data

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--contract',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists() and pya.__version__=='0.30.9' and len(os.sched_getaffinity(0))==1
    contract=json.loads(a.contract.read_text());assert contract['source_sha256']=='baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877'
    source=Path(__file__).resolve().parents[2]/'reports/resume-server-20260922/gm4comp3-qualified-source.spice'
    # coordinated_gm4 -> layout -> g1_sense; retain the exact qualified source.
    assert sha(source)==contract['source_sha256']
    ly=pya.Layout();ly.dbu=.001;top=ly.create_cell('g1_sense_contact_prototypes');rows=[]
    items=[build_bias(ly,'bias_n2','nmosHV',8,2),build_bias(ly,'bias_p4','pmosHV',16,4)]
    items += [build_pair(ly,'pair_'+('control' if control else 'split')+str(nf),nf,control) for nf in (16,64) for control in (False,True)]
    for i,(cell,data) in enumerate(items):
        top.insert(pya.CellInstArray(cell.cell_index(),pya.Trans(0,i*40000)))
        data['bbox_um']=[v*.001 for v in (cell.bbox().left,cell.bbox().bottom,cell.bbox().right,cell.bbox().top)];rows.append(data)
    assert [r['cell'] for r in rows]==contract['cells']
    a.output.mkdir(parents=True);gds=a.output/'native_prototypes.gds';ly.write(str(gds))
    report={'status':'passed scoped native/terminal gate' if all(r['terminal_audit']['status']=='passed' for r in rows) else 'failed physical terminal gate',
            'source_sha256':sha(source),'contract_sha256':sha(a.contract),'generator_sha256':sha(Path(__file__)),'GDS_sha256':sha(gds),'KLayout':pya.__version__,
            'cells':rows,'source_or_model_modified':False,'stock_DRC_LVS':'not run','per_device_shared_junction_model_applicability':'not run',
            'full_macro_or_broad_PEX':'not run','scope':'Isolated candidate only; immutable flattened snapshots, native source dimensions, terminal partition and declared adjacent-gate allocation. No adoption.'}
    (a.output/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='cells'},indent=2))
    print(json.dumps([dict(cell=r['cell'],status=r['terminal_audit']['status'],opens=r['terminal_audit']['opens'],shorts=r['terminal_audit']['shorts'],bbox_um=r['bbox_um']) for r in rows],indent=2))
if __name__=='__main__':main()
