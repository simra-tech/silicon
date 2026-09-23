#!/usr/bin/env python3
"""In-memory opposite-end gate contact screen; no candidate GDS is saved."""
import argparse
import collections
import copy
import hashlib
import json
import os
from pathlib import Path
import pya

HERE=Path(__file__).resolve().parent
GM4=HERE.parents[2]/'blocks/g1_sense/layout/coordinated_gm4'
METALS=(8,10,30,50,67,126,134)
CUTS={6:(501,5,8),19:(8,10),29:(10,30),49:(30,50),66:(50,67),125:(67,126),133:(126,134)}


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def regions(cell):
    out={}
    for layer in(1,5)+METALS+tuple(CUTS):
        r=pya.Region()
        for poly in pya.Region(cell.begin_shapes_rec(cell.layout().layer(layer,0))).each():r.insert(pya.Polygon(poly))
        out[layer]=r.merged()
    out[501]=out[1]-out[5]
    return out


def graph(regs,probes):
    flat=pya.Layout();flat.dbu=.001;top=flat.create_cell('native_screen')
    for layer,r in regs.items():
        if layer!=1:top.shapes(flat.layer(layer,0)).insert(r)
    net=pya.LayoutToNetlist(pya.RecursiveShapeIterator(flat,top,[]));layers={}
    for layer in(501,5)+METALS:
        layers[layer]=net.make_layer(flat.layer(layer,0),'L'+str(layer));net.connect(layers[layer])
    for layer,joined in CUTS.items():
        cut=net.make_layer(flat.layer(layer,0),'V'+str(layer));net.connect(cut)
        for other in joined:net.connect(cut,layers[other])
    net.extract_netlist();expected=collections.defaultdict(set);actual=collections.defaultdict(set)
    for q in probes:
        found=net.probe_net(layers[q['layer']],pya.DPoint(*q['point_um']).to_itype(.001))
        identity=None if found is None else found.cluster_id
        expected[q['net']].add(identity);actual[identity].add(q['net'])
    result=dict(source_net_count=len(expected),opens={n:sorted(v,key=str)for n,v in expected.items()if None in v or len(v)!=1},
                shorts={str(n):sorted(v)for n,v in actual.items()if len(v)!=1},
                all_physical_nets=sum(1 for c in net.netlist().each_circuit()for n in c.each_net()))
    result['status']='passed'if not result['opens']and not result['shorts']else'failed'
    return flat,net,layers,expected,result


def inside_point(polygon):
    b=polygon.bbox()
    if polygon.inside(b.center()):return b.center()
    for v in polygon.each_point_hull():
        for dx,dy in((1,1),(1,-1),(-1,1),(-1,-1)):
            q=pya.Point(v.x+dx,v.y+dy)
            if polygon.inside(q):return q
    raise AssertionError('No strict interior point for native merged polygon')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--proposal',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert not a.output.exists()and len(os.sched_getaffinity(0))==1 and pya.__version__=='0.30.9'
    plan=json.loads(a.proposal.read_text())
    base=GM4/'ring-r8-evidence-20260922-r1'
    gds=base/'sense-ring-routing-20260922-r8a/g1_sense_physical.gds'
    refpath=base/'sense-ring-reference-20260922-r8a/manifest.json'
    assert sha(gds)==plan['GDS_sha256']and sha(refpath)==plan['reference_sha256']
    ref=json.loads(refpath.read_text());assert ref['source_sha256']==plan['source_sha256']
    source=GM4.parents[1]/'reports/resume-server-20260922/gm4comp3-qualified-source.spice'
    assert sha(source)==plan['source_sha256']
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    result=dict(status='running read-only in-memory screen',GDS_sha256=sha(gds),source_sha256=plan['source_sha256'],
        proposal_sha256=sha(a.proposal),script_sha256=sha(Path(__file__)),new_GDS_saved=False,
        not_run=['Stock DRC/LVS','Electrical or model applicability','Fullchip integration/adoption'])
    try:
        ly=pya.Layout();ly.read(str(gds));top=ly.cell('g1_sense_physical');old=regions(top)
        probes=copy.deepcopy(ref['terminal_audit']['probes'])
        before_flat,before_net,before_layers,expected,before=graph(old,probes)
        assert before['status']=='passed'and before['source_net_count']==134
        result['before_graph']=before
        source_map={(q['device'],tuple(round(v*1000)for v in q['point_um'])):q['net']for q in probes if q['terminal']=='gate'}
        physical_names={next(iter(v)):n for n,v in expected.items()}
        owned={layer:collections.defaultdict(pya.Region)for layer in(5,8)}
        for layer in(5,8):
            for polygon in old[layer].each():
                found=before_net.probe_net(before_layers[layer],inside_point(polygon));assert found is not None
                name=physical_names.get(found.cluster_id,'UNASSIGNED:'+str(found.cluster_id))
                owned[layer][name].insert(polygon)
        additions={layer:collections.defaultdict(pya.Region)for layer in(5,6,8)}
        for row in plan['rows']:
            b=row['channel_bbox_dbu'];point=((b[0]+b[2])//2,(b[1]+b[3])//2)
            name=source_map[row['device'],point];row['source_net']=name
            for rect in row['rectangles']:additions[rect['layer'][0]][name].insert(pya.Box(*rect['bbox_dbu']))
            contact=next(q for q in row['rectangles']if q['layer']==[6,0])['bbox_dbu']
            probes.append(dict(device=row['device'],terminal='opposite_gate_M1',net=name,layer=8,
                point_um=[(contact[0]+contact[2])*.0005,(contact[1]+contact[3])*.0005]))
        violations=[]
        for layer in(5,8):
            for name,new in additions[layer].items():
                foreign=old[layer]-owned[layer].get(name,pya.Region())
                for other,region in additions[layer].items():
                    if other!=name:foreign+=region
                overlap=new&foreign;near=new.sized(179)&foreign
                if not near.is_empty():
                    violations.append(dict(layer=layer,source_net=name,overlap_dbu2=overlap.area(),
                        conservative_180nm_spacing_intersection_dbu2=near.area(),bbox_dbu=str(near.bbox())))
        alladded={layer:pya.Region()for layer in(5,6,8)}
        for layer,groups in additions.items():
            for region in groups.values():alladded[layer]+=region
            alladded[layer].merge()
        assert(alladded[5]&old[1]).is_empty(),'Proposed poly creates new channel area'
        assert(alladded[6]&old[1]).is_empty(),'Proposed gate contact touches Activ'
        assert(alladded[6]-(old[5]+alladded[5])).is_empty()
        assert(alladded[6]-(old[8]+alladded[8])).is_empty()
        closecuts=alladded[6].sized(179)&old[6]
        if not closecuts.is_empty():violations.append(dict(layer=6,source_net='multiple',
            conservative_180nm_spacing_intersection_dbu2=closecuts.area(),bbox_dbu=str(closecuts.bbox())))
        trial={layer:region.dup()for layer,region in old.items()}
        for layer,r in alladded.items():trial[layer]=(trial[layer]+r).merged()
        trial[501]=trial[1]-trial[5]
        assert((trial[1]&trial[5])^(old[1]&old[5])).is_empty()
        assert(trial[501]^old[501]).is_empty()
        after_flat,after_net,after_layers,after_expected,after=graph(trial,probes)
        result.update(after_graph=after,violations=violations,site_count=len(plan['rows']),
            native_channel_diffusion_XOR='passed zero',
            added_area_um2={str(layer):(trial[layer]-old[layer]).area()*1e-6 for layer in alladded},
            geometry_clearance_scope='Conservative 180nm Manhattan foreign-net poly/M1 and old-Cont screening, not stock DRC',
            physical_net_count_held=before['all_physical_nets']==after['all_physical_nets'])
        result['status']='passed in-memory contact/source graph screen only'if not violations and after['status']=='passed'and result['physical_net_count_held']else'failed in-memory proposal screen'
        assert sha(gds)==result['GDS_sha256']and sha(source)==result['source_sha256']
    except Exception as exc:
        result.update(status='failed in-memory screen execution',error=repr(exc));raise
    finally:
        (a.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['status'].startswith('passed')else 1)


if __name__=='__main__':main()
