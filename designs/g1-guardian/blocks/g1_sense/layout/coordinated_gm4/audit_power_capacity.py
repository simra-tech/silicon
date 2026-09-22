#!/usr/bin/env python3
"""Saved power revision: physical cut articulation and per-target via-only capacity."""
import argparse,collections,json,os
from pathlib import Path
import networkx as nx
from build_native_prototypes import pya,snapshot,sha
from inventory_power_cutpaths import metal_graph,METALS

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in('candidate','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();assert os.sched_getaffinity(0)=={6} and not a.output.exists()
    manifest=json.loads((a.candidate/'manifest.json').read_text());gds=a.candidate/'g1_sense_physical.gds'
    assert sha(gds)==manifest['GDS_sha256']
    ly=pya.Layout();ly.read(str(gds));cell=ly.cell('g1_sense_physical')
    graph,polygons,cuts,hit=metal_graph(cell);rows=[]
    for mapping in manifest['external_port_map']:
        net=mapping['net'];port=mapping['new'];origin=hit(port['layer'],pya.DPoint(*port['point_um']).to_itype(.001))[0]
        connected=nx.node_connected_component(graph,origin);sub=graph.subgraph(connected).copy();targets=collections.defaultdict(list)
        for q in manifest['terminal_audit']['probes']:
            if q['net']!=net:continue
            layer=8 if q['layer']==501 else q['layer']
            if layer not in METALS:continue
            hits=hit(layer,pya.DPoint(*q['point_um']).to_itype(.001));assert len(hits)==1 and hits[0]in connected
            targets[hits[0]].append(q)
        critical=[]
        for node in nx.articulation_points(sub):
            if node not in cuts:continue
            trial=sub.copy();trial.remove_node(node);retained=nx.node_connected_component(trial,origin)
            lost=set(targets)-retained
            if lost:critical.append(dict(cut=node,**cuts[node],lost_terminals=sorted({q['device']+'/'+q['terminal']for target in lost for q in targets[target]})))
        directed=nx.DiGraph();inf=1e9
        for node in sub:
            if node in cuts:directed.add_edge(node+':i',node+':o',capacity=cuts[node]['limit_mA'])
        for x,y in sub.edges():
            cut=x if x in cuts else y;metal=y if x in cuts else x
            directed.add_edge(metal,cut+':i',capacity=inf);directed.add_edge(cut+':o',metal,capacity=inf)
        terminal_capacities=[]
        for target,probes in targets.items():
            if target==origin:continue
            capacity,partition=nx.minimum_cut(directed,origin,target)
            separating=[dict(cut=node,**cuts[node])for node in cuts if node+':i'in partition[0]and node+':o'in partition[1]]
            terminal_capacities.append(dict(metal_component=target,source_probe_count=len(probes),
                terminals=sorted({q['device']+'/'+q['terminal']for q in probes}),via_only_capacity_mA=capacity,
                engineering_50pct_capacity_mA=.5*capacity,minimum_cut=separating))
        lower=[r for r in terminal_capacities if r['engineering_50pct_capacity_mA']<2.-1e-9]
        rows.append(dict(net=net,external_port=port,source_probe_count=sum(map(len,targets.values())),
            single_cut_articulations=critical,per_target_via_only=terminal_capacities,
            below_whole_macro_2mA_if_entire_load_assigned=lower,
            actual_branch_current_margin='not run; requires actual branch currents, metal widths and contact capacity'))
    result=dict(status='passed topology inventory'if all(not r['single_cut_articulations']for r in rows)else'failed single-cut-open screen',
        GDS_sha256=sha(gds),manifest_sha256=sha(a.candidate/'manifest.json'),script_sha256=sha(Path(__file__)),
        rows=rows,actual_cut_count=len(cuts),scope='Ideal metal islands, via capacities only. Not current-sharing, wire/contact capacity, complete EM or per-branch electrical qualification.',
        current_applicability='Published 105C / 11-year limits, engineering 50% target. Hot 125C and pulses not qualified.',
        native_contact_capacity='not run',full_power_margin='not run')
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],GDS_sha256=result['GDS_sha256'],rows=[dict(net=r['net'],critical_cuts=len(r['single_cut_articulations']),
        target_components=len(r['per_target_via_only']),minimum_target_50pct_mA=min(t['engineering_50pct_capacity_mA']for t in r['per_target_via_only']),
        below_2mA_target_components=len(r['below_whole_macro_2mA_if_entire_load_assigned']))for r in rows]),indent=2))

if __name__=='__main__':main()
