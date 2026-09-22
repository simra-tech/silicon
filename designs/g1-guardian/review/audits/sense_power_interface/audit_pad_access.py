#!/usr/bin/env python3
"""Read-only native pad07 bare-to-pad via capacity, not metal/current signoff."""
import argparse
import json
import os
from pathlib import Path
import sys
import networkx as nx
import pya

AUDITS=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(AUDITS))
from place_closed_analog import sha
HELPERS=AUDITS.parents[1]/'blocks/g1_sense/layout/coordinated_gm4'
sys.path.insert(0,str(HELPERS))
from inventory_power_cutpaths import metal_graph


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--native',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    assert pya.__version__=='0.30.9' and len(os.sched_getaffinity(0))==1 and not a.output.exists()
    source=a.native/'fullchip_instances_unrouted.gds'
    assert sha(source)=='8b66a958759478987fa9de59746a0554f9bd065307e730342f10e891082134e6'
    layout=pya.Layout();layout.read(str(source))
    cell=layout.cell('retained_fullchip_sg13g2_IOPadAnalog');assert cell is not None
    graph,components,cuts,hit=metal_graph(cell)
    origin=hit(30,pya.Point(40000,179855));target=hit(134,pya.Point(40000,1500))
    assert len(origin)==len(target)==1;origin,target=origin[0],target[0]
    owned=nx.node_connected_component(graph,origin);assert target in owned
    sub=graph.subgraph(owned).copy();critical=[]
    for node in nx.articulation_points(sub):
        if node not in cuts:continue
        trial=sub.copy();trial.remove_node(node)
        if not nx.has_path(trial,origin,target):critical.append(dict(cut=node,**cuts[node]))
    directed=nx.DiGraph()
    for node in owned:
        if node in cuts:directed.add_edge(node+':i',node+':o',capacity=cuts[node]['limit_mA'])
    for left,right in sub.edges():
        cut=left if left in cuts else right;metal=right if left in cuts else left
        directed.add_edge(metal,cut+':i',capacity=1e9);directed.add_edge(cut+':o',metal,capacity=1e9)
    capacity,partition=nx.minimum_cut(directed,origin,target)
    separating=[dict(cut=n,**cuts[n])for n in owned if n in cuts and n+':i'in partition[0]and n+':o'in partition[1]]
    result=dict(status='passed native via-path inventory; actual current qualification not run',
                GDS_sha256=sha(source),script_sha256=sha(Path(__file__)),helper_sha256=sha(HELPERS/'inventory_power_cutpaths.py'),
                cell=cell.name,origin=dict(layer=30,local_um=[40,179.855]),target=dict(layer=134,local_um=[40,1.5]),
                via_only_capacity_mA=capacity,half_table_target_mA=.5*capacity,
                critical_single_cuts=critical,minimum_cut=separating,native_modified=False,
                limits='11years/105C only; ideal metal islands and additive via capacities, no actual sharing proof',
                not_run=['wire bottlenecks/IR/current crowding','all VDDA consumers aggregate current','125C lifetime','pad ESD/bond current capability'])
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    (a.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items()if k!='minimum_cut'},indent=2))


if __name__=='__main__':main()
