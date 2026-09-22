#!/usr/bin/env python3
"""Actual metal/cut topology and via-only current bottlenecks; not EM signoff."""
import argparse
import collections
import copy
import json
import math
import os
from pathlib import Path

import networkx as nx
from build_native_prototypes import pya,snapshot,sha

METALS=(8,10,30,50,67,126,134)
CUTS={19:(8,10,.4),29:(10,30,.4),49:(30,50,.4),66:(50,67,.4),125:(67,126,1.4),133:(126,134,10.)}


def metal_graph(cell):
    polygons={};bins={};graph=nx.Graph();components={};cuts={}
    for layer in METALS:
        polygons[layer]=list(snapshot(cell,layer).each());bins[layer]=collections.defaultdict(list)
        for index,polygon in enumerate(polygons[layer]):
            node=f'M{layer}:{index}';graph.add_node(node,kind='metal',layer=layer)
            components[node]=polygon
            box=polygon.bbox()
            for x in range(box.left//10000,box.right//10000+1):
                for y in range(box.bottom//10000,box.top//10000+1):bins[layer][(x,y)].append(index)
    def hit(layer,point):
        return [f'M{layer}:{index}'for index in bins[layer].get((point.x//10000,point.y//10000),[])
                if polygons[layer][index].inside(point)]
    for layer,(lower,upper,limit)in CUTS.items():
        for index,polygon in enumerate(snapshot(cell,layer).each()):
            point=polygon.bbox().center();low=hit(lower,point);high=hit(upper,point)
            assert len(low)==len(high)==1,(layer,point,low,high)
            node=f'V{layer}:{index}';graph.add_node(node,kind='cut',capacity_mA=limit,layer=layer)
            graph.add_edge(node,low[0]);graph.add_edge(node,high[0])
            box=polygon.bbox();cuts[node]=dict(layer=layer,center_um=[point.x*.001,point.y*.001],
                bbox_um=[v*.001 for v in(box.left,box.bottom,box.right,box.top)],limit_mA=limit,connected_metals=low+high)
    return graph,components,cuts,hit


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('candidate','reference','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();assert os.sched_getaffinity(0)=={7} and not args.output.exists()
    assert sha(args.candidate)=='6609a77884a0009924422bf9871ea699e2393c8988412e1b000057cf3448beda'
    reference=json.loads(args.reference.read_text());assert reference['source_net_count']==134
    ly=pya.Layout();ly.read(str(args.candidate));cell=ly.cell('g1_sense_physical')
    graph,components,cuts,hit=metal_graph(cell);records=[]
    for net in ('vdd','vss'):
        probes=[copy.deepcopy(row)for row in reference['complete_physical_graph']['probes']if row['net']==net]
        targets={};missing=[]
        for probe in probes:
            layer=8 if probe['layer']==501 else probe['layer']
            if layer not in METALS:continue
            nodes=hit(layer,pya.DPoint(*probe['point_um']).to_itype(.001))
            if len(nodes)!=1:missing.append(probe);continue
            targets.setdefault(nodes[0],[]).append(probe)
        assert not missing,missing
        expected_port=[384.,184. if net=='vdd' else 184.8]
        port=next(row for row in probes if row['device']=='pin' and row['terminal']=='anchor'
                  and row['layer']==50 and all(abs(a-b)<1e-8 for a,b in zip(row['point_um'],expected_port)))
        origin=hit(port['layer'],pya.DPoint(*port['point_um']).to_itype(.001))[0]
        connected=nx.node_connected_component(graph,origin);assert set(targets)<=connected
        sub=graph.subgraph(connected).copy();critical=[]
        for node in nx.articulation_points(sub):
            if node not in cuts:continue
            trial=sub.copy();trial.remove_node(node)
            retained=nx.node_connected_component(trial,origin)
            lost=set(targets)-retained
            if not lost:continue
            labels=sorted({q['device']+'/'+q['terminal']for target in lost for q in targets[target]})
            critical.append(dict(cut=node,**cuts[node],disconnected_source_probe_count=sum(len(targets[target])for target in lost),
                                 disconnected_device_terminals=labels))
        # Node-split via capacities; metal islands are deliberately infinite.
        # This is a via-only upper bound, not a wire/current-sharing proof.
        directed=nx.DiGraph();inf=1e9
        for node,data in sub.nodes(data=True):
            if node in cuts:directed.add_edge(node+':i',node+':o',capacity=cuts[node]['limit_mA'])
        for a,b in sub.edges():
            cut=a if a in cuts else b;metal=b if a in cuts else a
            directed.add_edge(metal,cut+':i',capacity=inf);directed.add_edge(cut+':o',metal,capacity=inf)
        for target in targets:
            if target!=origin:directed.add_edge(target,'sink',capacity=inf)
        capacity,partition=nx.minimum_cut(directed,origin,'sink')
        separating=[node for node in cuts if node+':i' in partition[0] and node+':o' in partition[1]]
        records.append(dict(net=net,external_port=port,source_probe_count=sum(map(len,targets.values())),
                            metal_component_targets=len(targets),critical_single_cuts=critical,
                            via_only_all_load_maxflow_mA=capacity,via_only_50pct_target_mA=capacity*.5,
                            minimum_cut=[dict(cut=node,**cuts[node])for node in separating]))
    result=dict(status='passed actual r5 topology inventory; current margin not qualified',
                GDS_sha256=sha(args.candidate),reference_sha256=sha(args.reference),script_sha256=sha(Path(__file__)),
                rows=records,exploratory_whole_macro_envelope_mA=2.,engineering_utilization=.5,
                native_metal_components=len(components),actual_cut_count=len(cuts),
                bounds='Via-only mincut treats each metal island as ideal and assumes sum of cut capacities. Not wire EM, current crowding, equal-sharing guarantee, current allocation, pulse or125C lifetime signoff.',
                physical_geometry_modified=False,actual_gm4_branch_currents='not yet available')
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({**{k:v for k,v in result.items()if k!='rows'},'nets':[dict(net=row['net'],critical_single_cut_count=len(row['critical_single_cuts']),via_only_all_load_maxflow_mA=row['via_only_all_load_maxflow_mA'],minimum_cut=row['minimum_cut'])for row in records]},indent=2))


if __name__=='__main__':main()
