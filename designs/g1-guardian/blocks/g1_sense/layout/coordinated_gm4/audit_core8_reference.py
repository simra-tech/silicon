#!/usr/bin/env python3
"""Independent saved-polygon/source attribution for the eight-device assembly."""
import collections
import copy
import json
import os
from pathlib import Path
import re
from build_source_faithful_buffer import pya, snapshot, full_nets, sha
from audit_junction_defaults import default
from spice2cdl import convert

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]


def main():
    base = ROOT / 'build/scratch/sense-core8-20260922-r1'
    out = ROOT / 'build/scratch/sense-core8-reference-20260922-r1'
    assert not out.exists() and pya.__version__ == '0.30.9' and os.sched_getaffinity(0) == {7}
    manifest = json.loads((base/'manifest.json').read_text())
    assert manifest['status'] == 'passed bounded saved core8 preparation'
    gds = base/'g1_main_core8.gds'
    assert sha(gds) == manifest['GDS_sha256'] == 'b7f1e3c68b18e81617c992ee3f1001c309070e5b50fb20c96cd80ce4dc0b90db'
    source = HERE.parents[1]/'reports/resume-server-20260922/gm4comp3-qualified-source.spice'
    assert sha(source) == manifest['source_sha256'] == 'baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877'
    names = {'XM1','XM2','XM3','XM4','XM14','XM11','XM15','XM12'}
    block = re.search(r'(?ms)^\.subckt g1_ota_main_candidate .*?^\.ends',source.read_text()).group(0)
    specs = {line.split()[0]:line for line in block.splitlines() if line.split() and line.split()[0] in names}
    assert specs == manifest['source_lines'] and len(specs) == 8
    ly = pya.Layout(); ly.read(str(gds)); cell = ly.cell('g1_main_core8')
    active, poly = snapshot(cell,1), snapshot(cell,5)
    probes = copy.deepcopy(manifest['terminal_audit']['probes'])
    graph = full_nets(cell,probes)
    assert graph['status'] == 'passed'
    gp = [q for q in probes if q['terminal']=='gate']
    dp = [q for q in probes if q['layer']==501 and (q['device'] in names or q['device']=='pair')]
    gates=[]; owners=collections.defaultdict(list)
    def hits(box, records):
        return [q for q in records if box.contains(pya.DPoint(*q['point_um']).to_itype(.001))]
    for polygon in (active & poly).each():
        box=polygon.bbox(); assert polygon.area()==box.area()
        matches=hits(box,gp); assert len(matches)==1
        name=matches[0]['device']; assert name in specs
        gates.append((box,name)); owners[name].append(box)
    assert len(gates)==len(gp)==400 and set(owners)==names
    allocated={name:dict(as_um2=0.,ad_um2=0.,ps_um=0.,pd_um=0.) for name in specs}
    strips=[]
    for polygon in (active-poly).each():
        box=polygon.bbox()
        adjacent=[(b,n) for b,n in gates if b.bottom==box.bottom and b.top==box.top and (b.left==box.right or b.right==box.left)]
        if not adjacent: continue
        assert 1<=len(adjacent)<=2 and polygon.area()==box.area()
        matches=hits(box,dp); assert len(matches)==1
        net=matches[0]['net']; weights=collections.Counter(n for b,n in adjacent)
        for name,count in weights.items():
            words=specs[name].split()
            fields=[field for field,index in [('s',3),('d',1)] if words[index]==net]
            assert len(fields)==1
            field,weight=fields[0],count/len(adjacent)
            allocated[name]['a'+field+'_um2']+=weight*polygon.area()*1e-6
            allocated[name]['p'+field+'_um']+=weight*polygon.perimeter()*.001
        strips.append(dict(net=net,area_um2=polygon.area()*1e-6,perimeter_um=polygon.perimeter()*.001,adjacent_owners=dict(weights)))
    assert len(strips)==len(dp)==408
    devices=[]
    for name,boxes in owners.items():
        params=dict(re.findall(r'(\w+)=([^\s]+)',specs[name]))
        ng=int(params['ng']); w=float(params['w'].rstrip('u')); l=float(params['l'].rstrip('u'))
        assert len(boxes)==ng and all(b.width()==round(l*1000) and b.height()==round(w/ng*1000) for b in boxes)
        assert all(abs(allocated[name][key]-value)<1e-8 for key,value in default(w,ng).items())
        center=[sum((b.center().x if axis==0 else b.center().y)*.001 for b in boxes)/ng for axis in (0,1)]
        if name in ('XM1','XM2'): assert center==[115.,59.25]
        devices.append(dict(device=name,W_um=w,L_um=l,ng=ng,centroid_um=center,expected_default=default(w,ng)))
    box=cell.bbox(); assert box.left>=0 and box.bottom>=0 and box.right<=230000 and box.top<=164000
    for index in ly.layer_indices():
        for polygon in pya.Region(cell.begin_shapes_rec(index)).each():
            for p in polygon.each_point_hull(): assert p.x%5==0 and p.y%5==0
            for hole in range(polygon.holes()):
                for p in polygon.each_point_hole(hole): assert p.x%5==0 and p.y%5==0
    ports=sorted({n for line in specs.values() for n in line.split()[1:5]})
    assert len(ports)==13 and set(ports)=={q['net'] for q in probes}
    out.mkdir()
    lines=['.subckt g1_main_core8 '+' '.join(ports)]+list(specs.values())+['.ends g1_main_core8']
    cdl=out/'g1_main_core8.cdl'; cdl.write_text('\n'.join(convert(lines))+'\n')
    (out/Path(__file__).name).write_bytes(Path(__file__).read_bytes())
    result=dict(status='passed independent saved-polygon and exact source reference gate',
                source_sha256=sha(source),GDS_sha256=sha(gds),manifest_sha256=sha(base/'manifest.json'),
                script_sha256=sha(Path(__file__)),CDL_sha256=sha(cdl),source_lines=specs,devices=devices,
                terminal_audit=graph,strip_count=len(strips),strips=strips,adjacent_gate_allocation=allocated,
                grid_5nm='passed',ports=ports,stock_DRC_LVS='not run',intrinsic_junction_applicability='not run',
                full_main='not run',seed='not applicable',
                conversions=['Standard X-to-M conversion omits ng/mm_ok; independent native geometry proof retained'])
    (out/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('terminal_audit','strips')},indent=2))


if __name__=='__main__': main()
