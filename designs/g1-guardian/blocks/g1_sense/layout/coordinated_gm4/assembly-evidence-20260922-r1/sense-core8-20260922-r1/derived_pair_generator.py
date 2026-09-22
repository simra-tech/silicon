#!/usr/bin/env python3
"""Prepared isolated stacked64 pair; not a routed full gm4 OTA or fit adoption."""
import argparse,hashlib,json,os,re
from pathlib import Path
from build_native_prototypes import lib,pya,snapshot,measure_native,probe_record,pin,sha
from build_source_faithful_buffer import full_nets
from audit_junction_defaults import default

TRUNKS={'inn':2.,'inp':3.2,'fn':4.4,'fp':5.6,'tail':224.,'vdd':225.2,'vss':226.4}

def native_obstructions(ly,pair,pack,source):
    """Other19 full native cells only in memory; not added to saved pair GDS."""
    block=re.search(r'(?ms)^\.subckt g1_ota_main_candidate .*?^\.ends',source.read_text()).group(0)
    lines={line.split()[0]:line for line in block.splitlines() if line.startswith('X')}
    library=lib.LIB;rows=[];native_layout=pya.Layout();native_layout.dbu=.001
    for row in pack['main_OTA_devices']:
        name=row['name']
        if name in ('XM1', 'XM2', 'XM3', 'XM4', 'XM14', 'XM11', 'XM15', 'XM12'):continue
        line=lines[name];words=line.split();mapping={'sg13_hv_pmos':'pmosHV','sg13_hv_nmos':'nmosHV','rppd':'rppd','cap_cmim':'cmim'}
        kind=next(mapping[w] for w in words if w in mapping);params=dict(re.findall(r'\b(w|l|ng)=([^\s]+)',line))
        if 'ng' in params:params['ng']=int(params['ng'])
        if kind=='rppd':params.update(Calculate='R',b=0)
        if kind=='cmim':params.update(Calculate='C')
        index=library.layout().add_pcell_variant(library.layout().pcell_id(kind),params)
        cell=native_layout.cell(native_layout.add_lib_cell(library,index));bbox=cell.bbox();wanted=row['bbox_um']
        assert abs(bbox.width()*.001-(wanted[2]-wanted[0]))<1e-7 and abs(bbox.height()*.001-(wanted[3]-wanted[1]))<1e-7
        trans=pya.Trans(round(wanted[0]*1000)-bbox.left,round(wanted[1]*1000)-bbox.bottom);layers=[]
        for layer in (1,5,6,7,8,10,14,19,28,29,30,31,36,44,49,50,66,67,125,126,128,129):
            native=snapshot(cell,layer).transformed(trans);candidate=snapshot(pair,layer);overlap=candidate&native
            layers.append(dict(layer=layer,overlap_um2=overlap.area()*1e-6,within_200nm=(candidate.sized(200)&native).area()*1e-6))
        assert all(item['overlap_um2']==0 for item in layers),(name,layers)
        rows.append(dict(device=name,source_line=line,bbox_um=wanted,layers=layers))
    assert len(rows)==13
    return dict(status='passed same-layer zero-overlap with13 excluded native cells',devices=rows,
                scope='200nm proximity reported, not a universal clearance rule; native-only context has no future contacts/guards/routes. Stock full-context legality not run.')

def build(ly,source,pack):
    block=re.search(r'(?ms)^\.subckt g1_ota_main_candidate .*?^\.ends',source.read_text()).group(0)
    pair_source={line.split()[0]:line for line in block.splitlines() if line.split() and line.split()[0] in ('XM1','XM2')}
    assert len(pair_source)==2
    for name,line in pair_source.items():
        words=line.split();params=dict(re.findall(r'(\w+)=([^\s]+)',line))
        assert words[1:6]==(['fn','inn','tail','vdd','sg13_hv_pmos'] if name=='XM1' else ['fp','inp','tail','vdd','sg13_hv_pmos'])
        assert params['w']=='384u' and params['l']=='2u' and params['ng']=='64' and params['m']=='1'
        assert not set(params)&{'as','ad','ps','pd','rfmode'}
    cell=ly.create_cell('g1_main_pair_stacked64');D=lib.Draw(ly,cell)
    chains=[lib.Mos(D,'pmosHV',384,2,64,38.69,y) for y in (9.,103.5)]
    before={layer:snapshot(cell,layer) for layer in (1,5)};probes=[];gates=[];rows=[]
    allocated={name:dict(as_um2=0.,ad_um2=0.,ps_um=0.,pd_um=0.) for name in ('XM1','XM2')};points={net:[] for net in TRUNKS}
    def exit_m2(net,x,y):
        tx=TRUNKS[net];D.hwire('M2',x,tx,y,.4);D.stack(tx,y,'M2','M3');points[net].append((tx,y))
    for index,m in enumerate(chains):
        strips,measure=measure_native(m,before);groups=('ABBA' if index==0 else 'BAAB')*8;owners=['XM1' if groups[k//2]=='A' else 'XM2' for k in range(64)]
        m.end_dummies()
        for name,side,gate_net,drain_net in [('XM1','bot','inn','fn'),('XM2','top','inp','fp')]:
            fingers=[k for k,n in enumerate(owners) if n==name]
            for k in fingers:m.gate_pad(k,side)
            gy=m.yd(side,.33);D.hwire('M2',m.gx(fingers[0]),m.gx(fingers[-1]),gy,.38);exit_m2(gate_net,m.gx(fingers[0]),gy)
            drains=[k for k in range(1,64,2) if owners[k]==name];m.rail(side,drains);dx=m.sx(drains[0]);dy=m.yd(side,1.03);D.stack(dx,dy,'M1','M2');exit_m2(drain_net,dx,dy)
        tail_y=m.y0+8.4
        for k in range(64):
            name=owners[k];gates.append(dict(device=name,center_um=[m.gx(k),m.y0+3]))
            probe_record(probes,name,'gate','inn' if name=='XM1' else 'inp',5,m.gx(k),m.y0+3)
        for k,polygon in enumerate(strips):
            if k%2:
                weights={owners[k]:1.};field='d';net='fn' if owners[k]=='XM1' else 'fp'
            else:
                adjacent=owners[max(0,k-1):min(64,k+1)];weights={name:adjacent.count(name)/len(adjacent) for name in allocated if name in adjacent};field='s';net='tail'
                x,y=m.strip_pad(k,'top',-.35,hi='M3');D.vwire('M3',x,y,tail_y,.3)
            for name,weight in weights.items():
                allocated[name]['a'+field+'_um2']+=weight*polygon.area()*1e-6;allocated[name]['p'+field+'_um']+=weight*polygon.perimeter()*.001
            probe_record(probes,'pair',field,net,501,m.sx(k),m.y0+3)
        D.hwire('M3',m.sx(0),TRUNKS['tail'],tail_y,.4);points['tail'].append((TRUNKS['tail'],tail_y))
        D.box('NWell',m.x0-.62,m.y0-2.25,m.x1+.62,m.y0+8.25)
        for by in (m.y0-1.8,m.y0+7.8):
            D.tap_strip(m.x0,m.x1,by,ptype=False);x=m.gx(0);D.stack(x,by,'M1','M2');exit_m2('vdd',x,by)
            probe_record(probes,'body','well_tap','vdd',501,m.x0+1,by)
        rows.append(dict(Activ_origin_um=[m.x0,m.y0],native_measurement=measure))
    ring=D.tap_ring(1.,4.5,229.,114.5,ptype=True)
    for sy in (18.5,32.5,86.,99.5):
        D.tap_strip(.7,229.3,sy,ptype=True,inset=.6)
        probe_record(probes,'body','substrate_tap','vss',501,100.,sy)
    D.stack(ring[2],12.,'M1','M2');exit_m2('vss',ring[2],12.)
    probe_record(probes,'body','substrate_tap','vss',501,ring[2],12.)
    for net,x in TRUNKS.items():
        ys=[point[1] for point in points[net]];D.vwire('M3',x,min(ys),max(ys),.4);pin(D,probes,net,'M3',x,min(ys))
    after={layer:snapshot(cell,layer) for layer in (1,5)}
    assert ((before[1]&before[5])^(after[1]&after[5])).is_empty() and (before[1]-after[1]).is_empty()
    expected=default(384,64);assert all(abs(allocated[name][key]-expected[key])<1e-8 for name in allocated for key in expected)
    centers={name:[sum(g['center_um'][axis] for g in gates if g['device']==name)/64 for axis in (0,1)] for name in allocated}
    assert all(abs(centers[name][axis]-[115.,59.25][axis])<1e-8 for name in centers for axis in (0,1))
    terminal=full_nets(cell,probes);assert terminal['status']=='passed',terminal
    box=cell.bbox();assert box.left>=0 and box.bottom>=0 and box.right<=230000 and box.top<=164000
    obstructions=native_obstructions(ly,cell,pack,source)
    return cell,dict(status='passed isolated stacked pair native/terminal/obstruction scope',source_lines=pair_source,native_rows=rows,adjacent_gate_allocation=allocated,
                     expected_default=expected,gate_centroids_um=centers,native_channel_XOR_um2=0,native_Activ_removed_um2=0,
                     added_body_tap_Activ_um2=(after[1]-before[1]).area()*1e-6,terminal_audit=terminal,native_obstruction_screen=obstructions,
                     bbox_um=[value*.001 for value in (box.left,box.bottom,box.right,box.top)],
                     shared_junction_model_applicability='not run',stock_checks='not run',full_main_OTA='not run',PEX='not run',adoption='not run')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--pack',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists() and pya.__version__=='0.30.9' and os.sched_getaffinity(0)=={7}
    assert sha(a.pack)=='d70eeefb4a31de454c785a2f92a2320fc2d457ecf8a5b50f8a27abfb5adb2f56'
    source=Path(__file__).resolve().parents[2]/'reports/resume-server-20260922/gm4comp3-qualified-source.spice';assert sha(source)=='baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877'
    a.output.mkdir(parents=True);(a.output/'builder_snapshot.py').write_bytes(Path(__file__).read_bytes())
    result=dict(source_sha256=sha(source),pack_sha256=sha(a.pack),script_sha256=sha(Path(__file__)))
    try:
        ly=pya.Layout();ly.dbu=.001;cell,report=build(ly,source,json.loads(a.pack.read_text()));result.update(report)
        gds=a.output/'g1_main_pair_stacked64.gds';ly.write(str(gds));result['GDS_sha256']=sha(gds)
    except Exception as exc:
        result.update(status='failed isolated stacked-pair gate',exception_type=type(exc).__name__,detail=str(exc),GDS='not saved',stock_checks='not run')
        (a.output/'failure.json').write_text(json.dumps(result,indent=2)+'\n');raise
    (a.output/'manifest.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('terminal_audit','native_obstruction_screen')},indent=2))
if __name__=='__main__':main()
