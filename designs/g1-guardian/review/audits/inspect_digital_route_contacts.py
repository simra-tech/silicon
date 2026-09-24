#!/usr/bin/env python3
"""Locate physical foreign-route contacts to independently extracted macro nets."""
import argparse
import json
import os
from pathlib import Path
import time
import pya
from flat_metal_connectivity import flat_physical
from audit_placed_decap_domains import identity
from place_closed_analog import region, sha

METALS=(8,10,30,50,67,126,134)
CUTS=((19,8,10),(29,10,30),(49,30,50),(66,50,67),(125,67,126),(133,126,134))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('candidate','terminals','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();assert len(os.sched_getaffinity(0))==1 and not a.output.exists()
    m=json.loads((a.candidate/'analysis.json').read_text());g=a.candidate/'digital_replaced_native.gds'
    assert sha(g)==m['GDS_sha256'];start=time.monotonic()
    ly=pya.Layout();ly.read(str(g));top=ly.cell(m['top_cell'])
    mi,=[i for i in top.each_inst() if i.cell.name=='retained_g1_digital']
    ri,=[i for i in top.each_inst() if i.cell.name=='new_signal_routes']
    def isolate(instance):
        l=pya.Layout();l.dbu=ly.dbu;t=l.create_cell('TOP');c=l.create_cell('COPY');c.copy_tree(instance.cell)
        t.insert(pya.CellInstArray(c.cell_index(),instance.cplx_trans))
        n,met,held=flat_physical(l,t)
        rs={x:region(l,t,pya.LayerInfo(x,0)) for x in METALS+tuple(c[0] for c in CUTS)}
        return l,t,n,met,held,rs
    ml,mt,mn,mm,mheld,mr=isolate(mi);rl,rt,rn,rm,rheld,rr=isolate(ri)
    labels={};ports=[]
    for row in json.loads(a.terminals.read_text())['observations']:
        if 'u_digital' not in row['instance']:continue
        for w in row['windows']:
            if w['layer'] not in METALS:continue
            for poly in (mr[w['layer']]&pya.Region(pya.Box(*w['bbox']))).each():
                pt=next(poly.each_point_hull());key=identity(mn,mm[w['layer']],[pt.x,pt.y]);assert key
                labels.setdefault(key,set()).add(row['net']);ports.append(dict(net=row['net'],pin=row['pin'],cluster=list(key),window=w))
    contacts=[]
    tests=[(x,x,x,x) for x in METALS]
    for cut,lo,hi in CUTS:
        tests.extend(((cut,lo,lo,lo),(cut,hi,lo,hi),(lo,cut,lo,lo),(hi,cut,hi,lo)))
    for route_layer,macro_layer,route_probe,macro_probe in tests:
        for poly in (rr[route_layer]&mr[macro_layer]).merged().each():
            pt=next(poly.each_point_hull());xy=[pt.x,pt.y]
            rk=identity(rn,rm[route_probe],xy);mk=identity(mn,mm[macro_probe],xy)
            assert rk and mk,(route_layer,macro_layer,xy)
            contacts.append(dict(route_layer=route_layer,macro_layer=macro_layer,route_cluster=list(rk),macro_cluster=list(mk),
                macro_ports=sorted(labels.get(mk,[])),hull_dbu=[[v.x,v.y] for v in poly.each_point_hull()]))
    # Region boolean intersections omit zero-area edge contact. Extraction
    # treats touching conductors as joined, so inventory those independently.
    boundary=[]
    for layer in METALS:
        for rp in rr[layer].interacting(pya.Region(mi.bbox())).each():
            for mp in mr[layer].interacting(pya.Region(rp)).each():
                if not (pya.Region(rp)&pya.Region(mp)).is_empty():continue
                rpoint=next(rp.each_point_hull());mpoint=next(mp.each_point_hull())
                rk=identity(rn,rm[layer],[rpoint.x,rpoint.y]);mk=identity(mn,mm[layer],[mpoint.x,mpoint.y])
                assert rk and mk
                boundary.append(dict(layer=layer,route_cluster=list(rk),macro_cluster=list(mk),macro_ports=sorted(labels.get(mk,[])),
                    route_hull_dbu=[[v.x,v.y] for v in rp.each_point_hull()],macro_hull_dbu=[[v.x,v.y] for v in mp.each_point_hull()]))
    a.output.mkdir(parents=True)
    (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    result=dict(status='passed read-only contact localization; connectivity acceptance not inferred',GDS_sha256=sha(g),
        terminals_sha256=sha(a.terminals),ports=ports,contacts=contacts,boundary_contacts=boundary,wall_s=time.monotonic()-start,
        not_run=['Routing remedy','Fresh DRC','Full terminal partition','Electrical adoption'])
    (a.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(contacts=len(contacts),ports=len(ports),wall_s=result['wall_s'])))


if __name__=='__main__':main()
