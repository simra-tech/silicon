#!/usr/bin/env python3
"""Native supply contacts, actual feed sections and MIM drawing invariance."""
import argparse,collections,json,os
from pathlib import Path
from build_native_prototypes import pya,snapshot,sha

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in('candidate','baseline','output'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();assert os.sched_getaffinity(0)=={6} and not a.output.exists()
    manifest=json.loads((a.candidate/'manifest.json').read_text());gds=a.candidate/'g1_sense_physical.gds'
    assert sha(gds)==manifest['GDS_sha256'] and sha(a.baseline)==manifest['baseline_GDS_sha256']
    ly=pya.Layout();ly.read(str(gds));cell=ly.cell('g1_sense_physical')
    old=pya.Layout();old.read(str(a.baseline));base=old.cell('g1_sense_physical')
    mask=snapshot(base,36).sized(1000);mim=[]
    for layer in(67,126,129):
        delta=(snapshot(cell,layer)^snapshot(base,layer))&mask
        mim.append(dict(layer=layer,native_MIM_context_XOR_um2=delta.area()*1e-6));assert delta.is_empty()
    diffusion=snapshot(cell,1)-snapshot(cell,5);contacts=list(snapshot(cell,6).each());bins=collections.defaultdict(list)
    for index,polygon in enumerate(diffusion.each()):
        b=polygon.bbox()
        for x in range(b.left//10000,b.right//10000+1):
            for y in range(b.bottom//10000,b.top//10000+1):bins[x,y].append((index,polygon))
    rows=[];cache={}
    for probe in manifest['terminal_audit']['probes']:
        if probe['net']not in('vdd','vss')or probe['layer']!=501:continue
        point=pya.DPoint(*probe['point_um']).to_itype(.001)
        hits=[(i,r)for i,r in bins[point.x//10000,point.y//10000]if r.inside(point)];assert len(hits)==1
        index,polygon=hits[0]
        if index not in cache:
            region=pya.Region(polygon);inside=[c for c in contacts if not(region&pya.Region(c)).is_empty()]
            assert inside and all((pya.Region(c)-region).is_empty()for c in inside)
            cache[index]=len(inside)
        count=cache[index]
        rows.append(dict(net=probe['net'],device=probe['device'],terminal=probe['terminal'],point_um=probe['point_um'],
            diffusion_component=index,physical_contacts=count,tabulated_total_mA=.3*count,
            engineering_50pct_mA=.15*count,one_contact_lost_50pct_mA=.15*max(0,count-1)))
    # Exact one-dbu transverse polygon sections, no source-generator width assumption.
    specs=[]
    for dx,prefix in((0.,'XBUF'),(120.,'XREF')):
        specs.extend([(prefix+'/VDD_M3',30,7.3+dx,215.,'horizontal'),(prefix+'/VSS_M3',30,9.1+dx,215.,'horizontal'),
                      (prefix+'/VDD_M4_bar',50,35.+dx,230.13,'vertical'),(prefix+'/VSS_M4_bar',50,35.+dx,195.08,'vertical')])
    specs.extend([('XOTA/VDD_M4_leftcollector',50,120.,145.,'vertical'),('XOTA/VSS_M4_leftcollector',50,120.,145.8,'vertical'),
                  ('XOTA/VDD_M3_core',30,230.2,90.,'horizontal'),('XOTA/VSS_M3_core',30,231.4,90.,'horizontal'),
                  ('global/VDD_TopMetal2',134,300.,172.,'vertical'),('global/VSS_TopMetal1',126,300.,178.,'vertical')])
    widths=[]
    for name,layer,x,y,direction in specs:
        point=pya.DPoint(x,y).to_itype(.001);region=snapshot(cell,layer)
        clip=pya.Box(-1000000,point.y,1000000,point.y+1)if direction=='horizontal'else pya.Box(point.x,-1000000,point.x+1,1000000)
        sections=[q for q in(region&pya.Region(clip)).each()if q.bbox().contains(point)]
        if len(sections)!=1:
            widths.append(dict(name=name,layer=layer,point_um=[x,y],status='failed section target',matches=len(sections)));continue
        b=sections[0].bbox();width=(b.width()if direction=='horizontal'else b.height())*.001
        limit=width*(15 if layer==126 else 16 if layer==134 else 2)
        widths.append(dict(name=name,layer=layer,point_um=[x,y],width_um=width,tabulated_mA=limit,engineering_50pct_mA=limit*.5,
                          status='passed geometric section only',branch_envelope='not yet qualified'))
    result=dict(status='passed native-contact and section inventory'if all(r['status'].startswith('passed')for r in widths)else'failed section target',
        GDS_sha256=sha(gds),baseline_GDS_sha256=sha(a.baseline),script_sha256=sha(Path(__file__)),MIM_metal_context=mim,
        supply_diffusion_probes=rows,unique_supply_diffusion_components=len(cache),
        any_single_contact_components=sorted(i for i,count in cache.items()if count==1),metal_sections=widths,
        scope='Contact totals assume summed capacity, not guaranteed equal sharing. Contacts counted on actual MOS/tap diffusion only; resistor terminal contacts not covered. No branch-current, crowding, EM pulse or 125C lifetime qualification.',
        full_power_margin='not run',source_junction_applicability='not run')
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='supply_diffusion_probes'},indent=2))

if __name__=='__main__':main()
