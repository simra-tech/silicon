#!/usr/bin/env python3
"""Isolated complete21-device gm4 OTA; exact native source, no PEX/adoption."""
import argparse,copy,json,os,re
from pathlib import Path
from build_native_prototypes import lib,pya,snapshot,measure_native,probe_record,sha
from build_source_faithful_buffer import full_nets
from build_core8 import source_lines,NAMES,EXTRA_TRUNKS
from build_stacked_pair import TRUNKS

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[5]

def native_origin(D,kind,params,target):
    index=lib.LIB.layout().add_pcell_variant(lib.LIB.layout().pcell_id(kind),params)
    native=D.ly.cell(D.ly.add_lib_cell(lib.LIB,index));box=native.bbox()
    assert abs(box.width()*.001-(target[2]-target[0]))<1e-7 and abs(box.height()*.001-(target[3]-target[1]))<1e-7
    return target[0]-box.left*.001,target[1]-box.bottom*.001

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists() and pya.__version__=='0.30.9' and os.sched_getaffinity(0)=={7}
    source=HERE.parents[1]/'reports/resume-server-20260922/gm4comp3-qualified-source.spice'
    assert sha(source)=='baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877'
    packpath=ROOT/'designs/g1-guardian/review/audits/coordinated-bbox-pack-20260922-r4.json'
    assert sha(packpath)=='d70eeefb4a31de454c785a2f92a2320fc2d457ecf8a5b50f8a27abfb5adb2f56'
    base=ROOT/'build/scratch/sense-core8-20260922-r1';core=base/'g1_main_core8.gds';assert sha(core)=='b7f1e3c68b18e81617c992ee3f1001c309070e5b50fb20c96cd80ce4dc0b90db'
    coremeta=json.loads((base/'manifest.json').read_text());assert json.loads((ROOT/'build/scratch/sense-core8-stock-20260922-r1/summary.json').read_text())['status']=='passed'
    specs=source_lines(source);pack=json.loads(packpath.read_text());boxes={row['name']:row['bbox_um'] for row in pack['main_OTA_devices']}
    a.output.mkdir(parents=True);(a.output/'builder_snapshot.py').write_bytes(Path(__file__).read_bytes())
    result=dict(source_sha256=sha(source),pack_sha256=sha(packpath),core_GDS_sha256=sha(core),builder_sha256=sha(Path(__file__)),stock_checks='not run',PEX='not run',adoption='not run')
    try:
        old=pya.Layout();old.read(str(core));oldtop=old.cell('g1_main_core8');ly=pya.Layout();ly.dbu=.001;cell=ly.create_cell('g1_ota_main_physical');D=lib.Draw(ly,cell)
        for li in old.layer_indexes():
            info=old.get_info(li)
            if info.datatype in (2,25):continue
            for polygon in pya.Region(oldtop.begin_shapes_rec(li)).each():cell.shapes(ly.layer(info)).insert(pya.Polygon(polygon))
        probes=copy.deepcopy(coremeta['terminal_audit']['probes']);rows=[];mos=[]
        for name,line in specs.items():
            if name in NAMES or name in ('XRZ','XCC'):continue
            words=line.split();pars=dict(re.findall(r'(\w+)=([^\s]+)',line));kind='pmosHV' if words[5]=='sg13_hv_pmos' else 'nmosHV'
            w=float(pars['w'].rstrip('u'));length=float(pars['l'].rstrip('u'));nf=int(pars['ng']);assert pars['m']=='1' and not set(pars)&{'as','ad','ps','pd','rfmode'}
            x,y=native_origin(D,kind,dict(w=pars['w'],l=pars['l'],ng=nf),boxes[name]);m=lib.Mos(D,kind,w,length,nf,x,y);mos.append((name,m))
        before={layer:snapshot(cell,layer) for layer in (1,5)};assert (before[1]&before[5]).count()==478
        nets=sorted({n for line in specs.values() for n in line.split()[1:(5 if 'sg13_hv_' in line else 4 if 'rppd' in line else 3)]})
        assert len(nets)==17
        bus={net:128.+index*.8 for index,net in enumerate(nets)}
        for net,y in bus.items():D.hwire('M4',1.5,227.,y,.4)
        for net,x in dict(TRUNKS,**EXTRA_TRUNKS).items():
            # Existing core M3 remains below the new lower-bank M3 columns.
            anchor=next(q['point_um'] for q in probes if q['device']=='pin' and q['net']==net)
            D.vwire('M3',x,anchor[1],114.,.4);D.stack(x,114.,'M3','M5');D.vwire('M5',x,114.,bus[net],.4);D.stack(x,bus[net],'M4','M5')
        def local(net,x,y,start='M2'):
            D.stack(x,y,start,'M3');D.vwire('M3',x,y,bus[net],.4);D.stack(x,bus[net],'M3','M4');D.hwire('M4',min(x,1.5),max(x,227.),bus[net],.4)
        for name,m in mos:
            words=specs[name].split();strips,measure=measure_native(m,before);m.end_dummies();m.gate_bar('bot')
            # Existing parallel rails allow an interior contact choice without
            # changing channels. Keep upper/lower-bank M3 collectors distinct.
            access={'XMT':8,'XM13':4}.get(name,0)
            local(words[2],m.gx(access),m.yd('bot',.33))
            for parity,side,net in [(1,'bot',words[1]),(0,'top',words[3])]:
                m.rail(side,m.strips(parity));local(net,m.sx(access+parity),m.yd(side,1.03),'M1')
            for k in range(m.nf):probe_record(probes,name,'gate',words[2],5,m.gx(k),m.y0+m.wf/2)
            for k in range(m.nf+1):probe_record(probes,name,'drain' if k%2 else 'source',words[1] if k%2 else words[3],501,m.sx(k),m.y0+m.wf/2)
            if m.is_p:
                assert words[3:5]==['vdd','vdd']
                by=m.y1+2.1;D.box('NWell',m.x0-.62,m.y0-.62,m.x1+.62,by+.4);D.tap_strip(m.x0,m.x1,by,ptype=False)
                local('vdd',m.sx(access),by,'M1');probe_record(probes,'body','well_tap','vdd',501,m.sx(access),by)
            rows.append(dict(device=name,source_line=specs[name],native=measure,Activ_origin_um=[m.x0,m.y0]))
        ring=D.tap_ring(1.,115.8,229.,162.2,ptype=True)
        for y in (126.,143.5,160.):D.tap_strip(.7,229.3,y,ptype=True,inset=.6);probe_record(probes,'body','substrate_tap','vss',501,180.,y)
        local('vss',ring[2],120.,'M1');probe_record(probes,'body','substrate_tap','vss',501,ring[2],120.)
        rx,ry=native_origin(D,'rppd',dict(Calculate='R',w='1u',l='6.2u'),boxes['XRZ']);D.pcell('rppd',dict(Calculate='R',w='1u',l='6.2u'),rx,ry)
        for offset,y,net in [(-.32,ry-.28,'out1'),(.32,ry+6.48,'cz')]:
            x=rx+.5+offset;D.sq('M1',x,y,.34);local(net,x,y,'M1');probe_record(probes,'XRZ','end',net,8,x,y)
        cx,cy=native_origin(D,'cmim',dict(Calculate='C',w='69u',l='23u'),boxes['XCC']);D.pcell('cmim',dict(Calculate='C',w='69u',l='23u'),cx,cy)
        # Bottom M5=out, top TM1=cz. Tabs exit right of all native plates.
        outx,czx=132.,136.
        D.box('M5',cx+69+.1,cy+3.4,outx+.6,cy+4.6);D.vwire('M5',outx,cy+4,bus['out'],1.2);D.stack(outx,bus['out'],'M4','M5')
        D.box('TM1',cx+69-.66,cy+8,czx+1.,cy+10)
        # Carry cz on M5 outside the capacitor, joining only its target M4 bus.
        D.stack(czx,cy+9,'M5','TM1');D.vwire('M5',czx,cy+9,bus['cz'],.4);D.stack(czx,bus['cz'],'M4','M5')
        probe_record(probes,'XCC','bottom','out',67,cx+1,cy+1);probe_record(probes,'XCC','top','cz',126,cx+1,cy+1)
        after={layer:snapshot(cell,layer) for layer in (1,5)};delta=(before[1]&before[5])^(after[1]&after[5]);result.update(native_channel_XOR_um2=delta.area()*1e-6,channels=(after[1]&after[5]).count(),added_MOS=rows,bus_M4_y_um=bus)
        (a.output/'preaudit.json').write_text(json.dumps(result,indent=2)+'\n')
        assert delta.is_empty() and (before[1]-after[1]).is_empty()
        graph=full_nets(cell,probes);(a.output/'terminal_audit.json').write_text(json.dumps(graph,indent=2)+'\n');result['terminal_audit']=graph
        assert graph['status']=='passed',dict(opens=graph['opens'],shorts=graph['shorts'])
        for net in ('inp','inn','vbn','out','vdd','vss'):D.pin('M4',226.5,bus[net]-.2,227.,bus[net]+.2,net)
        gds=a.output/'g1_ota_main_physical.gds';ly.write(str(gds));result['GDS_sha256']=sha(gds)
        saved=pya.Layout();saved.read(str(gds));top=saved.cell(cell.name);assert full_nets(top,copy.deepcopy(probes))['status']=='passed'
        bbox=top.bbox();assert bbox.left>=0 and bbox.bottom>=0 and bbox.right<=230000 and bbox.top<=164000
        for li in saved.layer_indexes():
            for poly in pya.Region(top.begin_shapes_rec(li)).each():
                for point in poly.each_point_hull():assert point.x%5==point.y%5==0
                for h in range(poly.holes()):
                    for point in poly.each_point_hole(h):assert point.x%5==point.y%5==0
        result.update(status='passed fullmain scoped geometry/terminal preparation',bbox_um=[v*.001 for v in (bbox.left,bbox.bottom,bbox.right,bbox.top)],source_lines=specs,source_unchanged=sha(source)==result['source_sha256'],intrinsic_shared_junction_applicability='not run',density_antenna='not run')
    except Exception as exc:
        result.update(status='failed fullmain preparation',exception_type=type(exc).__name__,detail=str(exc));(a.output/'failure.json').write_text(json.dumps(result,indent=2)+'\n');raise
    (a.output/'manifest.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('terminal_audit','added_MOS','source_lines')},indent=2))
if __name__=='__main__':main()
