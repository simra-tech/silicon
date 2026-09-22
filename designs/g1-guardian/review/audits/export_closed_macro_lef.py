#!/usr/bin/env python3
"""Build source-bound conservative macro abstracts without changing native GDS."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import pya
from place_closed_analog import region, text_records

METALS={8:'Metal1',10:'Metal2',30:'Metal3',50:'Metal4',67:'Metal5',126:'TopMetal1',134:'TopMetal2'}


def subtract_rectangle(box,cut):
    """Disjoint rectangular decomposition; no LEF polygon-hole ambiguity."""
    l,b,r,t=box;cl,cb,cr,ct=cut
    il,ib,ir,it=max(l,cl),max(b,cb),min(r,cr),min(t,ct)
    if il>=ir or ib>=it:
        return [box]
    return [v for v in [(l,b,il,t),(ir,b,r,t),(il,b,ir,ib),(il,it,ir,t)]if v[0]<v[2]and v[1]<v[3]]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--gds',type=Path,required=True)
    p.add_argument('--sha256',required=True)
    p.add_argument('--cell',required=True)
    p.add_argument('--reference-lef',type=Path,required=True)
    p.add_argument('--macro',choices=['g1_bgr','g1_sense'],required=True)
    p.add_argument('--size',nargs=2,type=float,required=True)
    p.add_argument('--pin-egress',action='store_true',help='Open only empty same-layer access corridors to nearest macro edge')
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    assert not a.output.exists() and pya.__version__=='0.30.9' and len(os.sched_getaffinity(0))==1
    assert sha(a.gds)==a.sha256
    a.output.mkdir(parents=True)
    (a.output/'exporter_snapshot.py').write_bytes(Path(__file__).read_bytes())
    original=a.reference_lef.read_text()
    assert re.search(r'^MACRO '+a.macro+r'\s*$',original,re.M)
    directions={name:re.search(r'DIRECTION (\w+) ;',body)[1]
                for name,body in re.findall(r'^  PIN (\w+)\n(.*?)^  END \1$',original,re.M|re.S)}
    assert len(directions)==9
    ly=pya.Layout();ly.read(str(a.gds));top=ly.cell(a.cell)
    assert top is not None and ly.dbu==.001
    extent=pya.Box(0,0,*[round(v*1000)for v in a.size])
    assert (pya.Region(top.bbox())-pya.Region(extent)).is_empty()
    native={layer:region(ly,top,pya.LayerInfo(layer,0))for layer in METALS}
    pins={};windows={layer:[]for layer in METALS}
    for layer in METALS:
        labels=[s.text for s in top.shapes(ly.layer(layer,25)).each()if s.is_text()]
        annotation=[s for s in top.shapes(ly.layer(layer,2)).each()if s.is_box()or s.is_polygon()]
        for label in labels:
            name=label.string;point=pya.Point(label.trans.disp.x,label.trans.disp.y)
            assert name in directions and name not in pins,(layer,name)
            containing=[s for s in annotation if not(pya.Region(s.polygon)&pya.Region(pya.Box(point.x,point.y,point.x+1,point.y+1))).is_empty()]
            assert len(containing)==1,(name,len(containing))
            shape=containing[0];poly=shape.polygon;box=poly.bbox()
            assert (pya.Region(poly)^pya.Region(box)).is_empty(), 'Explicit rectangular macro port required'
            assert (pya.Region(box)-native[layer]).is_empty(), 'Pin must be backed by actual native metal'
            coords=[box.left,box.bottom,box.right,box.top]
            assert all(v%5==0 for v in coords)
            windows[layer].append(coords)
            pins[name]=dict(layer=layer,bbox_dbu=coords,label_dbu=[point.x,point.y],direction=directions[name],
                            use='POWER'if name=='vdd'else'GROUND'if name=='vss'else'SIGNAL')
    assert set(pins)==set(directions)
    def corridor_for(pin):
        l,b,r,t=pin['bbox_dbu'];margin=500
        side=min([(l,'west'),(b,'south'),(extent.right-r,'east'),(extent.top-t,'north')])[1]
        corridor=dict(west=[0,b-margin,r,t+margin],east=[l,b-margin,extent.right,t+margin],
                      south=[l-margin,0,r+margin,t],north=[l-margin,b,r+margin,extent.top])[side]
        return side,corridor
    if a.pin_egress:
        for pin in pins.values():
            layer=pin['layer'];old_box=list(pin['bbox_dbu']);port=pya.Region(pya.Box(*old_box))
            side,corridor=corridor_for(pin)
            connected=[poly for poly in native[layer].each()if not(pya.Region(poly)&port).is_empty()]
            assert len(connected)==1, 'Pin must belong to one continuous native same-layer conductor'
            extension=pya.Region(connected[0])&pya.Region(pya.Box(*corridor))&pya.Region(extent)
            pin['annotation_bbox_dbu']=old_box
            pin['same_layer_native_extension']='not applicable: nonrectangular or unchanged local conductor'
            box=extension.bbox()
            if not extension.is_empty() and (extension^pya.Region(box)).is_empty():
                assert (port-extension).is_empty() and (extension-native[layer]).is_empty()
                coords=[box.left,box.bottom,box.right,box.top]
                assert all(v%5==0 for v in coords)
                pin['bbox_dbu']=coords
                pin['same_layer_native_extension']='passed exact rectangular portion of original pin conductor'
        windows={layer:[pin['bbox_dbu']for pin in pins.values()if pin['layer']==layer]for layer in METALS}
    lines=['VERSION 5.8 ;','BUSBITCHARS "[]" ;','DIVIDERCHAR "/" ;',
           'MACRO '+a.macro,'  CLASS BLOCK ;','  ORIGIN 0 0 ;','  FOREIGN '+a.macro+' 0 0 ;',
           '  SIZE %.3f BY %.3f ;'%tuple(a.size),'  SYMMETRY X Y R90 ;']
    def rectangle(coords):
        return '      RECT '+' '.join('%.3f'%(v*.001)for v in coords)+' ;'
    for name,pin in sorted(pins.items()):
        lines+=['  PIN '+name,'    DIRECTION '+pin['direction']+' ;','    USE '+pin['use']+' ;',
                '    PORT','      LAYER '+METALS[pin['layer']]+' ;',rectangle(pin['bbox_dbu']),
                '    END','  END '+name]
    lines+=['  OBS'];audit=[];egress=[]
    for layer in METALS:
        # Block low layers over the whole reservation; upper native polygon
        # bboxes conservatively permit only genuinely empty over-macro routing.
        boxes=[[extent.left,extent.bottom,extent.right,extent.top]]if layer<=67 else[
            [q.bbox().left,q.bbox().bottom,q.bbox().right,q.bbox().top]for q in native[layer].each()]
        for cut in windows[layer]:
            boxes=[part for box in boxes for part in subtract_rectangle(box,cut)]
        obs=pya.Region()
        for box in boxes:
            obs.insert(pya.Box(*box))
        port=pya.Region()
        for box in windows[layer]:
            port.insert(pya.Box(*box))
        if a.pin_egress and windows[layer]:
            nonpin=native[layer]-port
            for name,pin in sorted(pins.items()):
                if pin['layer']!=layer:
                    continue
                side,corridor=corridor_for(pin)
                candidate=pya.Region(pya.Box(*corridor))&pya.Region(extent)
                # Native non-pin geometry is never declared routable. Only
                # conservative blanket space, not real metal, is opened.
                opened=candidate-nonpin
                obs-=opened
                egress.append(dict(pin=name,layer=layer,side=side,corridor_dbu=corridor,
                                   empty_or_pin_access_area_um2=opened.area()*1e-6,
                                   native_nonpin_area_in_corridor_um2=(candidate&nonpin).area()*1e-6))
            boxes=[]
            for polygon in obs.merged().each():
                for part in polygon.decompose_trapezoids():
                    box=part.bbox()
                    assert (pya.Region(part)^pya.Region(box)).is_empty()
                    boxes.append([box.left,box.bottom,box.right,box.top])
        assert (native[layer]-port-obs).is_empty()
        assert (obs&port).is_empty()
        if boxes:
            lines+=['    LAYER '+METALS[layer]+' ;']+[rectangle(box)for box in boxes]
        audit.append(dict(layer=layer,rectangles=len(boxes),native_area_um2=native[layer].area()*1e-6,
                          obstacle_area_um2=obs.area()*1e-6,pin_area_um2=port.area()*1e-6,
                          native_nonpin_coverage='passed',pin_obstacle_nonoverlap='passed'))
    lines+=['  END','END '+a.macro,'END LIBRARY']
    output=a.output/(a.macro+'.lef');output.write_text('\n'.join(lines)+'\n')
    # Router logical top name and disjoint subcell namespace only. Never remove
    # fill, pins, layers, devices or native hierarchical text during this copy.
    copied=pya.Layout();copied.dbu=ly.dbu
    ct=copied.create_cell(a.macro);ct.copy_tree(top)
    used={a.macro}
    for cell in copied.each_cell():
        if cell.cell_index()==ct.cell_index():
            continue
        name=a.macro+'__'+hashlib.sha256(cell.name.encode()).hexdigest()[:12]
        assert name not in used
        used.add(name);cell.name=name
    assert text_records(ly,top)==text_records(copied,ct)
    for info in ly.layer_infos():
        assert (region(ly,top,info)^region(copied,ct,info)).is_empty()
    gds=a.output/(a.macro+'.gds');copied.write(str(gds))
    saved=pya.Layout();saved.read(str(gds));st=saved.cell(a.macro)
    assert st is not None and len(saved.top_cells())==1
    assert text_records(ly,top)==text_records(saved,st)
    for info in ly.layer_infos():
        assert (region(ly,top,info)^region(saved,st,info)).is_empty()
    result=dict(status='passed conservative native-metal LEF abstraction',GDS_sha256=sha(a.gds),cell=a.cell,
                reference_LEF_sha256=sha(a.reference_lef),LEF_sha256=sha(output),macro=a.macro,size_um=a.size,
                abstract_GDS_sha256=sha(gds),namespace_geometry_text_and_saved_roundtrip='passed',
                script_sha256=sha(Path(__file__)),pins=pins,layer_audits=audit,
                same_layer_empty_space_pin_egress=egress,
                native_GDS_unchanged=sha(a.gds)==a.sha256,
                not_run=['OpenROAD LEF parse/roundtrip','PDN/global/detailed routing','fullchip DRC/LVS/PEX',
                         'current/IR/EM','canonical adoption'])
    (a.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
