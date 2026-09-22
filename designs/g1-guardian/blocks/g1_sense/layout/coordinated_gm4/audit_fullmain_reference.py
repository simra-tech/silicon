#!/usr/bin/env python3
"""Independently re-read fullmain polygons and prepare complete exact source CDL."""
import argparse,collections,copy,json,os,re
from pathlib import Path
from build_source_faithful_buffer import pya,snapshot,full_nets,sha
from audit_junction_defaults import default
from spice2cdl import convert

HERE=Path(__file__).resolve().parent

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists() and pya.__version__=='0.30.9' and len(os.sched_getaffinity(0))==1
    source=HERE.parents[1]/'reports/resume-server-20260922/gm4comp3-qualified-source.spice';assert sha(source)=='baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877'
    m=json.loads((a.candidate/'manifest.json').read_text());assert m['status']=='passed fullmain scoped geometry/terminal preparation'
    gds=a.candidate/'g1_ota_main_physical.gds';assert sha(gds)==m['GDS_sha256']
    block=re.search(r'(?ms)^\.subckt g1_ota_main_candidate .*?^\.ends',source.read_text()).group(0)
    lines={line.split()[0]:line for line in block.splitlines() if line.startswith('X')};assert lines==m['source_lines'] and len(lines)==21
    specs={name:line for name,line in lines.items() if 'sg13_hv_' in line};assert len(specs)==19
    a.output.mkdir(parents=True);(a.output/'audit_snapshot.py').write_bytes(Path(__file__).read_bytes())
    result=dict(source_sha256=sha(source),GDS_sha256=sha(gds),manifest_sha256=sha(a.candidate/'manifest.json'),script_sha256=sha(Path(__file__)),source_lines=lines)
    try:
        ly=pya.Layout();ly.read(str(gds));cell=ly.cell('g1_ota_main_physical');active,poly=snapshot(cell,1),snapshot(cell,5)
        probes=copy.deepcopy(m['terminal_audit']['probes']);graph=full_nets(cell,probes);assert graph['status']=='passed'
        gp=[q for q in probes if q['terminal']=='gate'];dp=[q for q in probes if q['layer']==501 and(q['device'] in specs or q['device']=='pair')]
        def hits(box,records):return[q for q in records if box.contains(pya.DPoint(*q['point_um']).to_itype(.001))]
        gates=[];owners=collections.defaultdict(list)
        for polygon in(active&poly).each():
            b=polygon.bbox();assert polygon.area()==b.area();matches=hits(b,gp);assert len(matches)==1
            name=matches[0]['device'];assert name in specs and matches[0]['net']==specs[name].split()[2];gates.append((b,name));owners[name].append(b)
        assert len(gates)==len(gp)==478 and set(owners)==set(specs)
        allocated={name:dict(as_um2=0.,ad_um2=0.,ps_um=0.,pd_um=0.)for name in specs};strips=[]
        for polygon in(active-poly).each():
            b=polygon.bbox();adj=[(g,n)for g,n in gates if g.bottom==b.bottom and g.top==b.top and(g.left==b.right or g.right==b.left)]
            if not adj:continue
            assert 1<=len(adj)<=2 and polygon.area()==b.area();matches=hits(b,dp);assert len(matches)==1;net=matches[0]['net'];weights=collections.Counter(n for g,n in adj)
            for name,count in weights.items():
                words=specs[name].split();fields=[field for field,index in [('s',3),('d',1)]if words[index]==net];assert len(fields)==1;field=fields[0];weight=count/len(adj)
                allocated[name]['a'+field+'_um2']+=weight*polygon.area()*1e-6;allocated[name]['p'+field+'_um']+=weight*polygon.perimeter()*.001
            strips.append(dict(net=net,area_um2=polygon.area()*1e-6,perimeter_um=polygon.perimeter()*.001,adjacent_owners=dict(weights)))
        assert len(strips)==len(dp)==497
        devices=[]
        for name,boxes in owners.items():
            params=dict(re.findall(r'(\w+)=([^\s]+)',specs[name]));nf=int(params['ng']);w=float(params['w'].rstrip('u'));length=float(params['l'].rstrip('u'))
            assert len(boxes)==nf and all(b.width()==round(length*1000)and b.height()==round(w/nf*1000)for b in boxes)
            assert all(abs(allocated[name][key]-value)<1e-8 for key,value in default(w,nf).items())
            center=[sum((b.center().x if axis==0 else b.center().y)*.001 for b in boxes)/nf for axis in(0,1)]
            if name in('XM1','XM2'):assert center==[115.,59.25]
            devices.append(dict(device=name,W_um=w,L_um=length,ng=nf,centroid_um=center,expected_default=default(w,nf)))
        resistor=snapshot(cell,128);cap=snapshot(cell,36);assert resistor.count()==cap.count()==1
        rb,cb=resistor.bbox(),cap.bbox();assert(rb.width(),rb.height(),resistor.area())==(1000,6200,6200000)
        assert(cb.width(),cb.height(),cap.area())==(69000,23000,1587000000)
        b=cell.bbox();assert b.left>=0 and b.bottom>=0 and b.right<=230000 and b.top<=164000
        ports=['inp','inn','vbn','out','vdd','vss'];assert len({q['net']for q in probes})==17
        for li in ly.layer_indexes():
            for polygon in pya.Region(cell.begin_shapes_rec(li)).each():
                for pt in polygon.each_point_hull():assert pt.x%5==pt.y%5==0
                for h in range(polygon.holes()):
                    for pt in polygon.each_point_hole(h):assert pt.x%5==pt.y%5==0
        cdl=a.output/'g1_ota_main_physical.cdl';cdl.write_text('\n'.join(convert(['.subckt g1_ota_main_physical '+' '.join(ports)]+list(lines.values())+['.ends g1_ota_main_physical']))+'\n')
        result.update(status='passed complete saved-polygon and exact source reference gate',CDL_sha256=sha(cdl),devices=devices,terminal_audit=graph,strip_count=len(strips),strips=strips,adjacent_gate_allocation=allocated,
                      RC_geometry='passed RZ1x6.2 and CC69x23',grid_5nm='passed',ports=ports,stock_checks='not run',intrinsic_junction_applicability='not run',full_SENSE='not run',PEX='not run',
                      conversions=['Standard X-to-M/R/C conversion, drops ng/mm_ok only; source parameters unchanged'])
    except Exception as exc:
        result.update(status='failed fullmain independent reference gate',exception_type=type(exc).__name__,detail=str(exc));(a.output/'failure.json').write_text(json.dumps(result,indent=2)+'\n');raise
    (a.output/'manifest.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in('terminal_audit','strips','source_lines')},indent=2))
if __name__=='__main__':main()
