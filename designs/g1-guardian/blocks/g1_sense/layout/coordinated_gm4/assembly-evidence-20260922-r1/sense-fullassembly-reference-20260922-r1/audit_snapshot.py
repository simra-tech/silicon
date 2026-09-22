#!/usr/bin/env python3
"""Independent saved full-SENSE geometry, source identities and exact CDL."""
import argparse,collections,copy,json,os,re
from pathlib import Path
from build_native_prototypes import pya,snapshot,sha
from build_source_faithful_buffer import full_nets
from audit_junction_defaults import default
from spice2cdl import convert

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[5]
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0))==1 and pya.__version__=='0.30.9'
    source=HERE.parents[1]/'reports/resume-server-20260922/gm4comp3-qualified-source.spice';assert sha(source)=='baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877'
    m=json.loads((a.candidate/'manifest.json').read_text());assert m['status']=='passed complete SENSE scoped preparation'
    gds=a.candidate/'g1_sense_physical.gds';assert sha(gds)==m['GDS_sha256']
    blocks={s.split()[1]:s for s in re.findall(r'(?ms)^\.subckt .*?^\.ends[^\n]*',source.read_text())};assert set(blocks)=={'g1_sense','g1_ota','g1_ota_main_candidate'}
    specs={};source_lines={};ports=blocks['g1_sense'].splitlines()[0].split()[2:];assert len(ports)==9
    def collect(name,block,pmap):
        for line in blocks[block].splitlines():
            if not line.startswith('X'):continue
            words=line.split();device=name+words[0]
            if words[-1]in blocks:continue
            model=next((q for q in words if q in('sg13_hv_nmos','sg13_hv_pmos','rppd','cap_cmim')),None);assert model
            nn=4 if 'mos'in model else(3 if model=='rppd'else 2)
            for i in range(1,nn+1):words[i]=pmap.get(words[i],name+words[i])
            source_lines[device]=line
            if 'mos'in model:specs[device]=words
    collect('','g1_sense',{})
    for name,block,pmap in [('XOTA/','g1_ota_main_candidate',dict(inp='vp',inn='vn',vbn='iptat',out='isense',vdd='vdd',vss='vss')),('XBUF/','g1_ota',dict(inp='vped_ref',inn='vped',vbn='iptat',out='vped',vdd='vdd',vss='vss')),('XREF/','g1_ota',dict(inp='vref',inn='vref_buf',vbn='iptat',out='vref_buf',vdd='vdd',vss='vss'))]:collect(name,block,pmap)
    assert len(specs)==58 and len(source_lines)==159
    a.output.mkdir(parents=True);(a.output/'audit_snapshot.py').write_bytes(Path(__file__).read_bytes());result=dict(source_sha256=sha(source),GDS_sha256=sha(gds),manifest_sha256=sha(a.candidate/'manifest.json'),script_sha256=sha(Path(__file__)))
    try:
        ly=pya.Layout();ly.read(str(gds));cell=ly.cell('g1_sense_physical');probes=copy.deepcopy(m['terminal_audit']['probes']);graph=full_nets(cell,probes);assert graph['status']=='passed'
        active,poly=snapshot(cell,1),snapshot(cell,5);gp=[q for q in probes if q['terminal']=='gate'];dp=[q for q in probes if q['layer']==501 and q['terminal']in('source','drain')]
        def hits(b,qs):return[q for q in qs if b.contains(pya.DPoint(*q['point_um']).to_itype(.001))]
        gates=[];owners=collections.defaultdict(list)
        for polygon in(active&poly).each():
            b=polygon.bbox();assert polygon.area()==b.area();qs=hits(b,gp);assert len(qs)==1;name=qs[0]['device'];assert name in specs and qs[0]['net']==specs[name][2];gates.append((b,name));owners[name].append(b)
        assert len(gates)==len(gp)==835 and set(owners)==set(specs)
        allocated={name:dict(as_um2=0.,ad_um2=0.,ps_um=0.,pd_um=0.)for name in specs};strips=[]
        for polygon in(active-poly).each():
            b=polygon.bbox();adj=[(g,n)for g,n in gates if g.bottom==b.bottom and g.top==b.top and(g.left==b.right or g.right==b.left)]
            if not adj:continue
            assert 1<=len(adj)<=2 and polygon.area()==b.area();qs=hits(b,dp);assert len(qs)==1;net=qs[0]['net'];weights=collections.Counter(n for g,n in adj)
            for name,count in weights.items():
                fields=[f for f,index in [('s',3),('d',1)]if specs[name][index]==net];assert len(fields)==1;field=fields[0];weight=count/len(adj)
                allocated[name]['a'+field+'_um2']+=weight*polygon.area()*1e-6;allocated[name]['p'+field+'_um']+=weight*polygon.perimeter()*.001
            strips.append(dict(net=net,area_um2=polygon.area()*1e-6,perimeter_um=polygon.perimeter()*.001,adjacent_owners=dict(weights)))
        assert len(strips)==len(dp)==893
        devices=[]
        for name,boxes in owners.items():
            params=dict(re.findall(r'(\w+)=([^\s]+)',source_lines[name]));nf=int(params['ng']);w=float(params['w'].rstrip('u'));length=float(params['l'].rstrip('u'))
            assert len(boxes)==nf and all(b.width()==round(length*1000)and b.height()==round(w/nf*1000)for b in boxes)
            assert all(abs(allocated[name][key]-value)<1e-8 for key,value in default(w,nf).items())
            center=[sum((b.center().x if i==0 else b.center().y)*.001 for b in boxes)/nf for i in(0,1)]
            devices.append(dict(device=name,source_line=source_lines[name],W_um=w,L_um=length,ng=nf,centroid_um=center,expected_default=default(w,nf)))
        for prefix in('XOTA/','XBUF/','XREF/'):
            centers=[r['centroid_um']for r in devices if r['device']in(prefix+'XM1',prefix+'XM2')];assert len(centers)==2 and all(abs(centers[0][i]-centers[1][i])<1e-8 for i in(0,1))
        r=snapshot(cell,128);c=snapshot(cell,36);assert r.count()==98 and c.count()==3
        assert collections.Counter((p.bbox().width(),p.bbox().height(),p.area())for p in r.each())==collections.Counter({(2000,76700,153400000):95,(1000,6200,6200000):3})
        assert collections.Counter((p.bbox().width(),p.bbox().height(),p.area())for p in c.each())==collections.Counter({(69000,23000,1587000000):1,(23000,23000,529000000):2})
        for li in ly.layer_indexes():
            for polygon in pya.Region(cell.begin_shapes_rec(li)).each():
                for pt in polygon.each_point_hull():assert pt.x%5==pt.y%5==0
                for h in range(polygon.holes()):
                    for pt in polygon.each_point_hole(h):assert pt.x%5==pt.y%5==0
        b=cell.bbox();assert b.left>=0 and b.bottom>=0 and b.right<=385000 and b.top<=240000
        cdl=a.output/'g1_sense_physical.cdl';text=source.read_text();assert text.count('.subckt g1_sense ')==1;text=text.replace('.subckt g1_sense ','.subckt g1_sense_physical ')
        cdl.write_text('\n'.join(convert(text.splitlines()))+'\n')
        result.update(status='passed saved-polygon and exact source reference gate',CDL_sha256=sha(cdl),devices=devices,source_lines=source_lines,terminal_audit=graph,strips=strips,adjacent_gate_allocation=allocated,channels=835,strip_count=893,resistor_count=98,capacitor_count=3,ports=ports,grid_5nm='passed',stock_checks='not run',intrinsic_junction_applicability='not run',PEX='not run',fullchip_fit='not run',adoption='not run',conversions=['Exact original hierarchy; top name only changed; standard X-to-M/R/C conversion drops ng/mm_ok without changing source parameters'])
    except Exception as exc:
        result.update(status='failed full-SENSE independent reference',exception_type=type(exc).__name__,detail=str(exc));(a.output/'failure.json').write_text(json.dumps(result,indent=2)+'\n');raise
    (a.output/'manifest.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in('terminal_audit','strips','devices','source_lines','adjacent_gate_allocation')},indent=2))
if __name__=='__main__':main()
