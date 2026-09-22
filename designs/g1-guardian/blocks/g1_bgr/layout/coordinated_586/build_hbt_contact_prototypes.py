#!/usr/bin/env python3
"""Five actual source HBT terminal patterns, unchanged native emitter geometry."""
import ast
import json
from pathlib import Path
import build_mos_contact_prototypes as base

pya = base.pya


def main():
    assert base.sha(base.SOURCE) == base.SOURCE_SHA
    gen = base.HERE.parent/'g1_bgr_layout.py'
    assert base.sha(gen) == base.GEN_SHA
    selected = [x for x in ast.parse(gen.read_text()).body if isinstance(x, ast.FunctionDef) and x.name in base.HELPERS]
    code = compile(ast.Module(body=selected, type_ignores=[]), str(gen), 'exec')
    lib = pya.Library.library_by_name('SG13_dev', 'sg13g2')
    out = base.ROOT/'build/scratch/bgr-hbt-contact-prototypes-20260922-r1'
    out.mkdir(parents=True, exist_ok=False)
    groups = {}
    for line in base.SOURCE.read_text().splitlines():
        if not line.startswith('XQ'):
            continue
        f = line.split(); nodes = f[1:5]
        assert f[5:] == ['npn13G2','we=0.07u','le=0.9u','Nx=1','m=1']
        groups.setdefault(tuple(nodes.index(n) for n in nodes), []).append(line)
    assert len(groups) == 5 and sum(map(len,groups.values())) == 301
    layers = {'Activ':(1,0),'GatPoly':(5,0),'Cont':(6,0),'pSD':(14,0),'NWell':(31,0),'TGO':(44,0),
              'M1':(8,0),'M1pin':(8,2),'M1txt':(8,25),'Via1':(19,0),'M2':(10,0),'M2pin':(10,2),
              'M2txt':(10,25),'Via2':(29,0),'M3':(30,0),'M3txt':(30,25),'prBoundary':(189,4)}
    rows = []
    for index, (pattern, lines) in enumerate(groups.items()):
        name = 'bgr_hbt_proto_%02d' % index
        ly = pya.Layout(); ly.dbu = .001; top = ly.create_cell(name)
        env = dict(pya=pya,lib=lib,ly=ly,top=top,L={k:ly.layer(*v) for k,v in layers.items()},
                   CONT=.16,CP=.34,VIA=.19,VP=.42,W3=.3,M2_SEGS=[])
        exec(code,env)
        x = y = 10
        env['pcell']('npn13G2',{'Nx':1},x,y)
        native_bbox = top.bbox()
        # The entire native PCell geometry remains in its unchanged child cell.
        native = {k:pya.Region(top.begin_shapes_rec(env['L'][k])).dup() for k in ['Activ','GatPoly']}
        for r in native.values(): r.flatten()
        box, label = env['box'], env['label']
        cnet,bnet,enet,substrate = lines[0].split()[1:5]
        xl,xr,yb,yt = x-2.90,x+2.90,y-2.88,y+3.33
        env['cont_row'](x-2.75,x+2.75,yb); env['cont_row'](x-2.75,x+2.75,yt)
        env['cont_col'](y-2.60,y+3.05,xl); env['cont_col'](y-2.60,y+3.05,xr)
        env['ring']('M1',xl+.13,yb+.13,xr-.13,yt-.13,.26)
        label('M1txt',xr,y+.2,substrate)
        box('M1pin',xr-.13,y,xr+.13,y+.4)
        if len(set(pattern)) == 1:
            box('M1',x-.15,yb,x+.15,yt)
        else:
            # Original base/collector contact extensions, without global routing.
            box('M1',x-.975,y-1.75,x+.975,y-1.02)
            label('M1txt',x+.6,y-1.5,bnet)
            box('M1pin',x+.4,y-1.65,x+.8,y-1.35)
            if cnet == bnet:
                box('M1',x-.92,y-1.26,x-.62,y+1.25)
            else:
                box('M1',x-.925,y+1.01,x+.925,y+1.75)
                label('M1txt',x-.6,y+1.5,cnet)
                box('M1pin',x-.8,y+1.35,x-.4,y+1.65)
            label('M2txt',x,y,enet)
            box('M2pin',x-.4,y-.4,x+.4,y+.4)
            if enet == substrate:
                # Two contact cuts at the substrate return, not a single-cut tie.
                box('M1',x-.42,yb-.15,x+.42,yb+.15)
                env['via1'](x,yb,2,'x',net=substrate)
                env['m2_v'](x,y-.6,yb,w=.72,net=substrate)
        for k,r in native.items():
            assert (pya.Region(top.begin_shapes_rec(env['L'][k]))^r).is_empty()
        bbox = top.bbox(); reservation = native_bbox.enlarged(2000)
        assert (pya.Region(bbox)-pya.Region(reservation)).is_empty()
        top.shapes(env['L']['prBoundary']).insert(reservation)
        gds = out/(name+'.gds'); ly.write(str(gds))
        f = lines[0].split(); ports=list(dict.fromkeys(f[1:5]))
        cdl = out/(name+'.cdl')
        cdl.write_text('.subckt '+name+' '+' '.join(ports)+'\nQUNIT '+' '.join(f[1:])+'\n.ends '+name+'\n')
        rows.append(dict(name=name,source_line=lines[0],represented_instances=[l.split()[0] for l in lines],
                         terminal_pattern=pattern,native_Activ_GatPoly_XOR_dbu2=0,
                         native_bbox_um=[v*.001 for v in [native_bbox.left,native_bbox.bottom,native_bbox.right,native_bbox.top]],
                         contact_bbox_um=[v*.001 for v in [bbox.left,bbox.bottom,bbox.right,bbox.top]],
                         reservation_passed=True,gds_sha256=base.sha(gds),cdl_sha256=base.sha(cdl),
                         stock_DRC_LVS='not run',terminal_net_partition='not run'))
    result=dict(status='passed scoped generation and native preservation',source_sha256=base.SOURCE_SHA,
                generator_sha256=base.sha(Path(__file__)),original_helpers_sha256=base.GEN_SHA,
                pdk_commit=(base.PDK/'COMMIT').read_text().strip(),klayout=pya.__version__,prototypes=rows,
                seed='not applicable',full_macro_guards_routing_fit='not run')
    (out/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__': main()
