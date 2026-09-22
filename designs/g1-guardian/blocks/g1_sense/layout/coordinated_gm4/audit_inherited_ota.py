#!/usr/bin/env python3
"""Source/finger and polygon reproduction controls; no design GDS is saved."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
LAYOUT = HERE.parent
DESIGN = LAYOUT.parents[2]
sys.path.insert(0, str(LAYOUT))
import g1_layout_lib as lib
import g1_ota_layout as gen
pya = lib.pya

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def block(text, name):
    return re.search(r'(?ms)^\.subckt '+name+r' .*?^\.ends', text).group(0)

def specs(text):
    result = {}
    for line in text.splitlines():
        if not line.startswith('X'):
            continue
        words = line.split()
        params = dict(re.findall(r'\b(\w+)=([^\s]+)', line))
        result[words[0]] = {'line': line, 'params': params}
    return result

def region(cell, layer):
    return pya.Region(cell.begin_shapes_rec(cell.layout().layer(*layer))).merged()

def geometry(active, gates):
    channels = active & gates
    diffusion = active - gates
    rows = sorted([p.bbox() for p in channels.each()], key=lambda b:b.left)
    assert all(p.is_box() for p in channels.each())
    strips = sorted([p for p in diffusion.each()], key=lambda p:p.bbox().left)
    return {'ng': len(rows), 'W_um': sum(b.height() for b in rows)*.001,
            'L_um': sorted(set(b.width()*.001 for b in rows)),
            'finger_W_um': sorted(set(b.height()*.001 for b in rows)),
            'diffusion_strips': [{'bbox_um':[p.bbox().left*.001,p.bbox().bottom*.001,p.bbox().right*.001,p.bbox().top*.001],
                                  'area_um2':p.area()*1e-6,'full_polygon_perimeter_um':p.perimeter()*.001} for p in strips],
            'junction_scope':'Polygon perimeter includes channel-facing edges; not asserted identical to model PS/PD.'}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args()
    assert not args.output.exists() and pya.__version__=='0.30.9' and len(os.sched_getaffinity(0))==1
    source=DESIGN/'blocks/g1_sense/reports/resume-server-20260922/gm4comp3-qualified-source.spice'
    delivered=DESIGN/'blocks/g1_padring/layout/g1_chip_top.gds'
    assert sha(source)=='baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877'
    assert sha(delivered)=='38c1d6d13bbfee4ed0e3c01477742c3d2d28317d9215d9e5bd9a35551285ae59'
    sources={name:specs(block(source.read_text(),name)) for name in ('g1_ota','g1_ota_main_candidate')}
    # Capture constructor locations only. Every physical channel is counted from delivered polygons.
    captured=[]
    original=lib.Mos
    class Capture(original):
        def __init__(self,*a,**k):
            super().__init__(*a,**k)
            captured.append(self)
    lib.Mos=gen.Mos=Capture
    generated=pya.Layout(); generated.dbu=.001
    fresh,info=gen.build_ota(generated)
    lib.Mos=gen.Mos=original
    physical=pya.Layout();physical.read(str(delivered))
    old=physical.cell('g1_ota');assert old is not None
    keys=set((i.layer,i.datatype) for i in generated.layer_infos())|set((i.layer,i.datatype) for i in physical.layer_infos())
    xor=[]
    for key in sorted(keys):
        delta=region(fresh,key)^region(old,key)
        if not delta.is_empty():xor.append({'layer':list(key),'area_um2':delta.area()*1e-6,'polygons':delta.count()})
    active=region(old,(1,0));gates=region(old,(5,0))
    names=['XMB4','XMB2','XMB6','XM3','XM13','XM16','XM4','XM21','XM14','XM15','XM12','XM11','PAIR','XMB7','XMB5','XMB3','XMT','XM20']
    assert len(captured)==len(names)
    rows=[]
    for name,m in zip(names,captured):
        clip=pya.Region(pya.Box(lib.um(m.x0),lib.um(m.y0),lib.um(m.x1),lib.um(m.y1)))
        actual=geometry(active&clip,gates&clip)
        assert actual['ng']==m.nf and abs(actual['W_um']-m.w)<1e-8
        logical=[name] if name!='PAIR' else ['XM1','XM2']
        for logical_name in logical:
            row={'device':logical_name,'native_group':name,'physical':actual,'constructor_origin_um':[m.x0,m.y0],
                 'physical_logical_ng':actual['ng'] if name!='PAIR' else actual['ng']//2,
                 'physical_logical_W_um':actual['W_um'] if name!='PAIR' else actual['W_um']/2,
                 'pair_assignment_scope':'Generator ABBA map; independent gate-net ownership not run' if name=='PAIR' else 'single logical device'}
            views={}
            for view,spec in sources.items():
                params=spec[logical_name]['params']; w=float(params['w'].rstrip('u')); l=float(params['l'].rstrip('u')); ng=int(params['ng'])
                matching=(row['physical_logical_ng']==ng and abs(row['physical_logical_W_um']-w)<1e-8 and actual['L_um']==[l])
                native=generated.create_cell('expected_'+view+'_'+logical_name)
                D=lib.Draw(generated,native);D.pcell(m.kind,{'w':params['w'],'l':params['l'],'ng':ng},0,0)
                expected=geometry(region(native,(1,0)),region(native,(5,0)))
                views[view]={'source':spec[logical_name], 'geometry_matches':matching,'expected_native':expected,
                             'explicit_junction_parameters':{key:params.get(key) for key in ('as','ad','ps','pd')},
                             'junction_model_applicability':'not run; all four omitted in source, stock subcircuit defaults require separate audit'}
            row['source_comparisons']=views;rows.append(row)
    hierarchy=[]
    for line in block(source.read_text(),'g1_sense').splitlines():
        if line.startswith(('XOTA ','XBUF ','XREF ')):
            w=line.split();sub=w[-1]
            failures=[r['device'] for r in rows if not r['source_comparisons'][sub]['geometry_matches']]
            hierarchy.append({'instance':w[0],'source_line':line,'expected_subcircuit':sub,'inherited_cell':'g1_ota',
                              'inherited_geometry_fidelity':'failed' if failures else 'passed scoped W/L/ng', 'mismatched_devices':failures})
    result={'status':'failed inherited source-to-physical finger fidelity','KLayout':pya.__version__,
            'source_sha256':sha(source),'delivered_sha256':sha(delivered),'script_sha256':sha(Path(__file__)),
            'generator_sha256':sha(LAYOUT/'g1_ota_layout.py'),'library_sha256':sha(LAYOUT/'g1_layout_lib.py'),
            'spice2cdl_sha256':sha(LAYOUT/'spice2cdl.py'),
            'generator_polygon_reproduction':{'status':'passed' if not xor else 'failed','nontext_layer_differences':xor,'boundary_um':info['bbox']},
            'hierarchy':hierarchy,'devices':rows,
            'not_run':['independent gate-net ownership for shared pair','model default AS/AD/PS/PD applicability','new source-faithful routed geometry','new stock DRC/LVS/PEX'],
            'GDS_saved':False,'scope':'Nontext polygons counted from delivered cell. Constructor locations are independently bounded against actual channel W/L/ng. Stock LVS drops ng and therefore cannot substitute for this audit.'}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='devices'},indent=2))

if __name__=='__main__':main()
