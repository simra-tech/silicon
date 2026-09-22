#!/usr/bin/env python3
"""Isolated95-unit SENSE bank from unchanged original routing section."""
import argparse,hashlib,json,os,re,sys,textwrap
from pathlib import Path
from build_native_prototypes import lib,pya,snapshot,probe_record,sha
from build_source_faithful_buffer import full_nets
from spice2cdl import convert
import g1_sense_layout as baseline

HERE=Path(__file__).resolve().parent
AX0,AY0=248.5,11.43
CH={'vbn':.9,'vn':1.9,'isense':2.9,'vp':3.9,'x2n':4.9,'x2p':5.9,'vped':6.9,'vped_ref':7.9,'vref_buf':8.9,'vref':9.9,'vss':10.9}
CHX={k:236.+v for k,v in CH.items()}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists() and pya.__version__=='0.30.9' and len(os.sched_getaffinity(0))==1
    source=HERE.parents[1]/'reports/resume-server-20260922/gm4comp3-qualified-source.spice';assert sha(source)=='baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877'
    original=HERE.parent/'g1_sense_layout.py';assert sha(original)=='951801e4411006f1a61a21faa6cac919159e74c588daabd96cc3e083094c66e0';text=original.read_text();start=text.index('    # ------------------------------------------------------------------ resistor array');end=text.index('    # ------------------------------------------------------------------ MBI')
    section=textwrap.dedent(text[start:end]);a.output.mkdir(parents=True);(a.output/'builder_snapshot.py').write_bytes(Path(__file__).read_bytes());(a.output/'original_bank_section.py').write_text(section)
    result=dict(source_sha256=sha(source),original_generator_sha256=sha(original),section_sha256=hashlib.sha256(section.encode()).hexdigest(),script_sha256=sha(Path(__file__)),stock_checks='not run',PEX='not run',adoption='not run')
    try:
        ly=pya.Layout();ly.dbu=.001;top=ly.create_cell('g1_sense_resistor_bank');D=lib.Draw(ly,top)
        namespace={key:getattr(baseline,key)for key in('RW','RL','RPITCH','NCOL','HEAD','ROWGAP','TRACK','EXTW','PAD','VIA')}
        namespace.update(D=D,AX0=AX0,AY0=AY0,ROWPITCH=83.92,CH=CH,CHX=CHX,colx=lambda c:AX0+c*2.5,rowy=lambda r:AY0+r*83.92)
        exec(compile(section,str(original),'exec'),namespace)
        chan=namespace['chan_y'];gap=namespace['gap_track'];ax1=namespace['AX1'];reg=namespace['reg'];to_channel=namespace['to_channel'];probes=[]
        ar=D.tap_ring(AX0-1.2,gap(0,2)-1.,ax1+1.2,gap(2,7)+1.,.30,ptype=True)
        for y in(AY0+76.7/2,AY0+83.92+76.7/2):
            D.stack(ar[0],y,'M1','M2');to_channel('vss',ar[0],y);reg('vss',y);probe_record(probes,'guard','body','vss',501,ar[0],y)
        for name,ys in chan.items():
            if not ys:continue
            D.vwire('M3',CHX[name],min(ys),max(ys),.4)
        block=re.search(r'(?ms)^\.subckt g1_sense .*?^\.ends',source.read_text()).group(0)
        specs={line.split()[0]:line for line in block.splitlines()if ' rppd ' in line};assert len(specs)==95 and 'XREF' not in specs
        mapping={}
        def chain(prefix,startnum,cells,first):
            for i,(c,r)in enumerate(cells):mapping[prefix+str(startnum+i)]=(c,r,first if i%2==0 else('bot' if first=='top' else 'top'))
        chain('XR1N',0,[(25,0)],'bot');chain('XR1P',0,[(26,0)],'bot')
        chain('XR2N',0,[(c,0)for c in range(15,25)]+[(c,1)for c in range(27,37)],'top')
        chain('XR2P',0,[(c,0)for c in range(27,37)]+[(c,1)for c in range(15,25)],'top')
        chain('XRD1',0,[(25,1),(26,1)],'top')
        chain('XRD2',0,[(c,0)for c in range(2,15)],'top');chain('XRD2',13,[(c,0)for c in range(49,36,-1)],'bot')
        chain('XRD2',26,[(c,1)for c in range(14,1,-1)],'bot');chain('XRD2',39,[(c,1)for c in range(37,49)],'top')
        assert set(mapping)==set(specs) and len(set((c,r)for c,r,side in mapping.values()))==95
        devices=[]
        for name,line in specs.items():
            words=line.split();pars=dict(re.findall(r'(\w+)=([^\s]+)',line));assert words[3]=='vss' and pars['w']=='2u' and pars['l']=='76.7u' and pars['m']=='1'
            c,r,side=mapping[name];x=AX0+c*2.5+1.;entry=AY0+r*83.92+(76.98 if side=='top' else -.28);exit=AY0+r*83.92+(-.28 if side=='top' else 76.98)
            probe_record(probes,name,'end0',words[1],8,x,entry);probe_record(probes,name,'end1',words[2],8,x,exit)
            devices.append(dict(device=name,source_line=line,column=c,row=r,first_terminal_side=side,head_points_um=[[x,entry],[x,exit]]))
        ports={name:(30,CHX[name],min(chan[name]))for name in('vn','vp','isense','vped','vped_ref','vref_buf','vss')}
        ports.update(sense_n=(10,namespace['xn'],namespace['ytn']),sense_p=(10,namespace['xp'],namespace['ytp']))
        for name,(layer,x,y)in ports.items():D.pin('M3' if layer==30 else'M2',x-.2,y-.2,x+.2,y+.2,name);probe_record(probes,'pin','anchor',name,layer,x,y)
        poly=snapshot(top,128);assert poly.count()==95
        assert all(polygon.bbox().width()==2000 and polygon.bbox().height()==76700 and polygon.area()==153400000 for polygon in poly.each())
        assert(snapshot(top,1)&snapshot(top,5)).is_empty()
        graph=full_nets(top,probes);result['terminal_audit']=graph;(a.output/'terminal_audit.json').write_text(json.dumps(graph,indent=2)+'\n')
        assert graph['status']=='passed',dict(opens=graph['opens'],shorts=graph['shorts'])
        gds=a.output/'g1_sense_resistor_bank.gds';ly.write(str(gds));result['GDS_sha256']=sha(gds)
        cdl=a.output/'g1_sense_resistor_bank.cdl';cdl.write_text('\n'.join(convert(['.subckt g1_sense_resistor_bank '+' '.join(ports)]+list(specs.values())+['.ends g1_sense_resistor_bank']))+'\n')
        result['CDL_sha256']=sha(cdl);bbox=top.bbox();assert bbox.left>=235000 and bbox.right<=385000 and bbox.bottom>=0 and bbox.top<=180000
        result.update(status='passed isolated95R source/geometry/terminal preparation',devices=devices,ports=ports,bbox_um=[v*.001 for v in(bbox.left,bbox.bottom,bbox.right,bbox.top)],native_resistor_count=95,
                      geometry_status='Nine original poly-only dummies retained; complete native/resistor graph, no new well or source change',strict_LVS_requirement='--no_series_res preserves unit-level internal nodes',full_SENSE='not run')
    except Exception as exc:
        result.update(status='failed resistor-bank preparation',exception_type=type(exc).__name__,detail=str(exc));(a.output/'failure.json').write_text(json.dumps(result,indent=2)+'\n');raise
    (a.output/'manifest.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in('terminal_audit','devices')},indent=2))
if __name__=='__main__':main()
