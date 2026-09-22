#!/usr/bin/env python3
"""Saved overlay one-cut-unavailable connectivity and conditional via capacities."""
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


def mincut(graph,cuts,source,target):
    network=nx.DiGraph()
    for node in graph:
        if node in cuts:network.add_edge(node+':i',node+':o',capacity=cuts[node]['limit_mA'])
    for left,right in graph.edges():
        cut=left if left in cuts else right;metal=right if left in cuts else left
        network.add_edge(metal,cut+':i',capacity=1e9);network.add_edge(cut+':o',metal,capacity=1e9)
    return nx.minimum_cut(network,source,target)[0]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert not a.output.exists() and len(os.sched_getaffinity(0))==1 and pya.__version__=='0.30.9'
    source=AUDITS.parents[1]/'blocks/g1_sense/reports/resume-server-20260922/gm4comp3-qualified-source.spice'
    assert sha(source)=='baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877'
    meta=json.loads((a.candidate/'analysis.json').read_text());gds=a.candidate/'power_overlay.gds'
    assert meta['status'].startswith('passed') and sha(gds)==meta['overlay_sha256']=='a16aa0d622329a4d5de51b658a3d57f0e7cf1d1be1cdd4228dfead0856f56ca0'
    layout=pya.Layout();layout.read(str(gds));graph,components,cuts,hit=metal_graph(layout.top_cell())
    assert len(cuts)==38 and nx.number_connected_components(graph)==2
    records=[]
    for net,start,end in [('VDDA',(134,813000,714000),(30,1093145,395000)),('VSS',(126,805000,714000),(126,736800,722000))]:
        left=hit(start[0],pya.Point(*start[1:]));right=hit(end[0],pya.Point(*end[1:]))
        assert len(left)==len(right)==1;left,right=left[0],right[0]
        owned=nx.node_connected_component(graph,left);assert right in owned
        sub=graph.subgraph(owned).copy();capacity=mincut(sub,cuts,left,right)
        losses=[]
        for node in sorted(owned):
            if node not in cuts:continue
            trial=sub.copy();trial.remove_node(node)
            connected=nx.has_path(trial,left,right)
            reduced=mincut(trial,cuts,left,right)if connected else 0
            losses.append(dict(cut=node,layer=cuts[node]['layer'],center_um=cuts[node]['center_um'],
                               connected=connected,half_table_capacity_mA=.5*reduced))
        assert all(r['connected']for r in losses)
        assert min(r['half_table_capacity_mA']for r in losses)>=2-1e-10
        records.append(dict(net=net,half_table_capacity_mA=.5*capacity,
                            one_cut_unavailable_min_half_table_mA=min(r['half_table_capacity_mA']for r in losses),
                            removed_cuts=losses))
    result=dict(status='passed saved overlay one-cut connectivity and conditional via-only target',
                overlay_sha256=sha(gds),canonical_source_sha256=sha(source),script_sha256=sha(Path(__file__)),
                actual_cuts=len(cuts),physical_metal_components=len(components),nets=records,
                exploratory_mA=2,scope='Ideal metal islands, additive via capacity and 50% engineering target against105C/11year table; not measured sharing or lifetime qualification',
                not_run=['wire/contact bottlenecks','aggregate root spine load','125C lifetime/current crowding/IR','fullchip LVS/PEX','adoption'])
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    (a.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({**result,'nets':[{k:v for k,v in row.items()if k!='removed_cuts'}for row in records]},indent=2))


if __name__=='__main__':main()
