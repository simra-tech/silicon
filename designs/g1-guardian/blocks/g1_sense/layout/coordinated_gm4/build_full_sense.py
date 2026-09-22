#!/usr/bin/env python3
"""Isolated full SENSE from source-faithful checked macro parts; no adoption."""
import argparse,copy,json,os,re
from pathlib import Path
from build_native_prototypes import lib,pya,snapshot,probe_record,measure_native,sha
from build_source_faithful_buffer import full_nets
from spice2cdl import convert

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[5]
CENTRAL={net:235.6+i for i,net in enumerate(('iptat','vn','isense','vp','vped','vped_ref','vref_buf','vref','vdd','vss'))}
CENTRAL['vss']=244.65

def copy_cell(layout,path,oldname,newname):
    old=pya.Layout();old.read(str(path));source=old.cell(oldname);cell=layout.create_cell(newname)
    for li in old.layer_indexes():
        info=old.get_info(li);target=layout.layer(info)
        for polygon in pya.Region(source.begin_shapes_rec(li)).each():cell.shapes(target).insert(pya.Polygon(polygon))
        it=source.begin_shapes_rec(li)
        while not it.at_end():
            if it.shape().is_text():cell.shapes(target).insert(it.shape().text.transformed(it.trans()))
            it.next()
    return cell

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists() and pya.__version__=='0.30.9' and os.sched_getaffinity(0)=={7}
    source=HERE.parents[1]/'reports/resume-server-20260922/gm4comp3-qualified-source.spice';assert sha(source)=='baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877'
    mainbase=ROOT/'build/scratch/sense-fullmain-20260922-r2';bufbase=HERE/'source-faithful-buffer-20260922-r2';resbase=ROOT/'build/scratch/sense-resbank-20260922-r2'
    mg=mainbase/'g1_ota_main_physical.gds';bg=bufbase/'g1_ota_source_faithful.gds';rg=resbase/'g1_sense_resistor_bank.gds'
    assert sha(mg)=='970b6b572f8637a5e56ad2d695e925f7e938ae28136a0e0015b256b77f6ae701' and sha(bg)=='320df90ee046c73b628005da9384c80fbd21a715a39b0e8b96b10923726fc500' and sha(rg)=='cb8cdbcfdab98a9b3a3e3fe2925ebaff2c7cd768ec9befeddea8bd8310d4c87a'
    for path in(ROOT/'build/scratch/sense-fullmain-stock-20260922-r2/summary.json',HERE/'source-faithful-buffer-stock-20260922-r1/summary.json',ROOT/'build/scratch/sense-resbank-stock-20260922-r1/summary.json'):assert json.loads(path.read_text())['status']=='passed'
    mm=json.loads((mainbase/'manifest.json').read_text());bm=json.loads((bufbase/'manifest.json').read_text());rm=json.loads((resbase/'manifest.json').read_text())
    a.output.mkdir(parents=True);(a.output/'builder_snapshot.py').write_bytes(Path(__file__).read_bytes());result=dict(source_sha256=sha(source),script_sha256=sha(Path(__file__)),input_GDS_hashes=dict(main=sha(mg),buffer=sha(bg),resistor=sha(rg)),stock_checks='not run',PEX='not run',adoption='not run')
    try:
        ly=pya.Layout();ly.dbu=.001;top=ly.create_cell('g1_sense_physical');D=lib.Draw(ly,top)
        maincell=copy_cell(ly,mg,'g1_ota_main_physical','g1_ota_main_candidate');bufcell=copy_cell(ly,bg,'g1_ota_source_faithful','g1_ota');rescell=copy_cell(ly,rg,'g1_sense_resistor_bank','resistor_bank_view')
        # Resistors remain top-level as in the schematic, not a new source subcircuit.
        for li in ly.layer_indexes():
            if ly.get_info(li).datatype in(2,25):continue
            for polygon in pya.Region(rescell.begin_shapes_rec(li)).each():top.shapes(li).insert(pya.Polygon(polygon))
        D.inst(maincell,5.,5.);D.inst(bufcell,15.5,185.8);D.inst(bufcell,135.5,185.8)
        portmaps={'XOTA':dict(inp='vp',inn='vn',vbn='iptat',out='isense',vdd='vdd',vss='vss'),
                  'XBUF':dict(inp='vped_ref',inn='vped',vbn='iptat',out='vped',vdd='vdd',vss='vss'),
                  'XREF':dict(inp='vref',inn='vref_buf',vbn='iptat',out='vref_buf',vdd='vdd',vss='vss')}
        probes=copy.deepcopy(rm['terminal_audit']['probes']);points={net:[] for net in CENTRAL};instances=[]
        def instance_probes(name,original,dx,dy):
            translated=[]
            for q in original:
                q=copy.deepcopy(q);net=q['net'];q['net']=portmaps[name].get(net,name+'/'+net);q['device']=name+'/'+q['device'];q['point_um']=[q['point_um'][0]+dx,q['point_um'][1]+dy];translated.append(q)
            probes.extend(translated);return translated
        instance_probes('XOTA',mm['terminal_audit']['probes'],5,5)
        for name,dx in(('XBUF',15.5),('XREF',135.5)):instance_probes(name,bm['independent_audit']['terminal_audit']['probes'],dx,185.8)
        def central(net,x,y,low):
            if low!='M4':D.stack(x,y,low,'M4')
            D.hwire('M4',x,CENTRAL[net],y,.4);D.stack(CENTRAL[net],y,'M4','M5');points[net].append(y)
        for pin,net in portmaps['XOTA'].items():
            x,y=231.75,mm['bus_M4_y_um'][pin]+5.;central(net,x,y,'M4');probe_record(probes,'XOTA','port',net,50,x,y)
        for pin,(layer,x,y)in rm['ports'].items():
            if pin in('sense_n','sense_p'):continue
            access_y=y+.04 if pin=='vref_buf'else y
            if access_y!=y:D.vwire('M3',x,y,access_y,.4)
            central(pin,x,access_y,'M3');probe_record(probes,'Rbank','port',pin,layer,x,y)
        for index,(name,dx)in enumerate((('XBUF',15.5),('XREF',135.5))):
            anchors={q['net']:q for q in bm['independent_audit']['terminal_audit']['probes']if q['device']=='pin'}
            for j,pin in enumerate(('vbn','out','inn','inp')):
                q=anchors[pin];x,y=q['point_um'][0]+dx,q['point_um'][1]+185.8;escape=106.+120*index+j;track=232.7+.64*(4*index+j);net=portmaps[name][pin]
                D.stack(x,y,'M2','M4');D.hwire('M4',x,escape,y,.4);D.stack(escape,y,'M4','M5');D.vwire('M5',escape,y,track,.4);D.stack(escape,track,'M4','M5');central(net,escape,track,'M4')
            for pin,track in(('vdd',238.),('vss',239.)):
                q=anchors[pin];x=q['point_um'][0]+dx;y=232.;net=portmaps[name][pin];D.stack(x,y,'M3','M5');D.vwire('M5',x,y,track,.8);D.stack(x,track,'M4','M5');central(net,x,track,'M4')
            instances.append(dict(instance=name,origin_um=[dx,185.8],bbox_um=[dx-10.5,181.,dx+90.11,232.2],source_subcircuit='g1_ota'))
        # Exact top-level source diode MBI, separate from all three OTA devices.
        m=lib.Mos(D,'nmosHV',3.3,1,1,237.,184.);before={layer:snapshot(top,layer)for layer in(1,5)};assert(before[1]&before[5]).count()==835
        strips,measure=measure_native(m,before);m.end_dummies();m.gate_bar('bot');m.rail('bot',[1]);m.rail('top',[0])
        for x,y in((m.gx(0),m.yd('bot',.33)),(m.sx(1),m.yd('bot',1.03))):
            D.stack(x,y,'M1'if x==m.sx(1)else'M2','M3');D.vwire('M3',x,y,177.8,.4);D.stack(x,177.8,'M3','M4')
        D.hwire('M4',m.gx(0),m.sx(1),177.8,.4);central('iptat',m.gx(0),177.8,'M4')
        x,y=m.sx(0),m.yd('top',1.03);central('vss',x,y,'M1')
        for k in range(1):probe_record(probes,'XMBI','gate','iptat',5,m.gx(k),m.y0+m.wf/2)
        for k in range(2):probe_record(probes,'XMBI','drain'if k else'source','iptat'if k else'vss',501,m.sx(k),m.y0+m.wf/2)
        gr=D.tap_ring(234.5,180.5,242.,191.,ptype=True);central('vss',gr[2],189.,'M1');probe_record(probes,'XMBI','body','vss',501,gr[2],189.)
        outer=D.tap_ring(1.,1.,384.,239.,ptype=True);central('vss',outer[2],179.,'M1');probe_record(probes,'macro','body','vss',501,outer[2],179.)
        for net,ys in points.items():assert ys,net;D.vwire('M5',CENTRAL[net],min(ys),max(ys),.8 if net in('vdd','vss')else .4)
        for pin,xout,ypin in(('sense_n',381.,16.),('sense_p',382.2,22.)):
            layer,x,y=rm['ports'][pin];D.hwire('M2',x,xout,y,.3);D.stack(xout,y,'M2','M5');D.vwire('M5',xout,y,ypin,.4);D.stack(xout,ypin,'M4','M5');D.pin('M4',383.,ypin-.5,385.,ypin+.5,pin);D.hwire('M4',xout,384.,ypin,.4);probe_record(probes,'pin','anchor',pin,50,384.,ypin)
        for j,net in enumerate(('vref','iptat','isense','vped','vref_buf','vdd','vss')):
            y=180.+j*.8;x=CENTRAL[net];D.vwire('M5',x,min(min(points[net]),y),max(max(points[net]),y),.8 if net in('vdd','vss')else .4);D.stack(x,y,'M4','M5');D.hwire('M4',x,384.,y,.4);D.pin('M4',383.,y-.2,385.,y+.2,net);probe_record(probes,'pin','anchor',net,50,384.,y)
        # Pin sense_p/sense_n plus seven listed ports comprise nine external ports;
        # source also exposes vped and vref_buf already included, total nine.
        external_labels=[s.text.string for li in ly.layer_indexes()if ly.get_info(li).datatype==25 for s in top.shapes(li).each()if s.is_text()]
        assert sorted(external_labels)==sorted(('sense_p','sense_n','vref','iptat','isense','vped','vref_buf','vdd','vss'))
        after={layer:snapshot(top,layer)for layer in(1,5)};delta=(before[1]&before[5])^(after[1]&after[5]);result.update(channels=(after[1]&after[5]).count(),native_channel_XOR_um2=delta.area()*1e-6,MBI_native=measure)
        gds=a.output/'g1_sense_physical.gds';ly.write(str(gds));result['GDS_sha256']=sha(gds);(a.output/'preaudit.json').write_text(json.dumps(result,indent=2)+'\n');assert delta.is_empty()
        graph=full_nets(top,probes);(a.output/'terminal_audit.json').write_text(json.dumps(graph,indent=2)+'\n');result['terminal_audit']=graph;assert graph['status']=='passed',dict(opens=graph['opens'],shorts=graph['shorts'])
        bbox=top.bbox();assert bbox.left>=0 and bbox.bottom>=0 and bbox.right<=385000 and bbox.top<=240000
        assert snapshot(top,128).count()==98 and snapshot(top,36).count()==3
        for li in ly.layer_indexes():
            for polygon in pya.Region(top.begin_shapes_rec(li)).each():
                for pt in polygon.each_point_hull():assert pt.x%5==pt.y%5==0
                for h in range(polygon.holes()):
                    for pt in polygon.each_point_hole(h):assert pt.x%5==pt.y%5==0
        result.update(status='passed complete SENSE scoped preparation',instances=instances,external_pin_labels=external_labels,central_M5_x_um=CENTRAL,bbox_um=[v*.001 for v in(bbox.left,bbox.bottom,bbox.right,bbox.top)],resistor_count=98,capacitor_count=3,MOS_logical_count=58,source_unchanged=sha(source)==result['source_sha256'],fullchip_fit='not run',intrinsic_junction_applicability='not run',density_antenna='not run')
    except Exception as exc:
        result.update(status='failed complete SENSE preparation',exception_type=type(exc).__name__,detail=str(exc));(a.output/'failure.json').write_text(json.dumps(result,indent=2)+'\n');raise
    (a.output/'manifest.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='terminal_audit'},indent=2))
if __name__=='__main__':main()
