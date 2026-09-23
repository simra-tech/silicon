#!/usr/bin/env python3
"""Read-only exact pad07 conductor polygons and local bare-M3 cross sections."""
import argparse
import json
import os
from pathlib import Path
import sys
import networkx as nx
import pya

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from place_closed_analog import sha
from audit_pad_access import metal_graph


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--native',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert not a.output.exists()
    assert pya.__version__=='0.30.9'and len(os.sched_getaffinity(0))==1
    source=a.native/'fullchip_instances_unrouted.gds'
    assert sha(source)=='8b66a958759478987fa9de59746a0554f9bd065307e730342f10e891082134e6'
    ly=pya.Layout();ly.read(str(source));cell=ly.cell('retained_fullchip_sg13g2_IOPadAnalog')
    graph,components,cuts,hit=metal_graph(cell)
    start=hit(30,pya.Point(40000,179855));end=hit(134,pya.Point(40000,1500))
    assert len(start)==len(end)==1
    owned=nx.node_connected_component(graph,start[0]);assert end[0]in owned
    polygons=[];layers={}
    for node,poly in components.items():
        if node not in owned:continue
        layer=graph.nodes[node]['layer'];layers.setdefault(layer,pya.Region()).insert(poly)
        b=poly.bbox()
        polygons.append(dict(node=node,layer=layer,area_um2=poly.area()*1e-6,
            bbox_um=[v*.001 for v in(b.left,b.bottom,b.right,b.top)],
            hull_um=[[q.x*.001,q.y*.001]for q in poly.each_point_hull()],
            holes_um=[[[q.x*.001,q.y*.001]for q in poly.each_point_hole(h)]for h in range(poly.holes())]))
    vias=[dict(node=n,**cuts[n])for n in sorted(owned)if n in cuts]
    # Local +y points toward the bare pin; global transform is R90+(1273,355).
    # This necessary M3-section screen alone cannot certify the whole stack.
    ys={179854,179855}
    for row in vias:
        if row['layer']in(29,49):ys.add(round(row['center_um'][1]*1000))
    sections=[]
    for y in sorted(ys):
        r=layers[30]&pya.Region(pya.Box(-100000,y,200000,y+1))
        widths=[poly.area()*.001 for poly in r.each()]
        sections.append(dict(local_y_um=y*.001,total_M3_width_um=sum(widths),
                             disconnected_widths_um=widths,
                             half_table_total_mA=sum(widths),
                             scope='Necessary total M3 width only; disconnected pieces or via transfers cannot be assigned equal current'))
    result=dict(status='completed read-only native pad wire inventory; 10mA path qualification not run',
                GDS_sha256=sha(source),script_sha256=sha(Path(__file__)),cell=cell.name,
                points=dict(bare_M3_local_um=[40,179.855],external_TM2_local_um=[40,1.5]),
                chip_transform='R90+(1273,355)um',polygons=polygons,vias=vias,M3_sections=sections,
                exploratory_shared_target_mA=10,geometry_modified=False,
                not_run=['full wire/cut capacity network','actual pad current sharing/current crowding/IR/EM',
                         'shared VDDA geometry','105C lifetime or125C applicability','adoption'])
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    (a.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items()if k not in('polygons','vias')},indent=2))


if __name__=='__main__':main()
