#!/usr/bin/env python3
"""Source-probe connectivity after every added TRIP via cut is unavailable."""
import argparse
import json
import os
from pathlib import Path
import networkx as nx
import pya
from build_ls_interface import region,sha,CUTS
from audit_overlay_graph import metal_graph,mincut


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert not a.output.exists()and len(os.sched_getaffinity(0))==1 and pya.__version__=='0.30.9'
    meta=json.loads((a.candidate/'analysis.json').read_text());assert meta['status'].startswith('passed')
    gds=a.candidate/'g1_trip.gds';addition=a.candidate/'internal_overlay_local.gds'
    assert sha(gds)==meta['GDS_sha256']and sha(addition)==meta['overlay_sha256']
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    result=dict(status='running',GDS_sha256=sha(gds),local_overlay_sha256=sha(addition),script_sha256=sha(Path(__file__)),
                not_run=['native Contact/diffusion single-open','all original via single-open','wire current crowding/EM',
                         'per-device current allocation/PVT/IR','comparator/VSS access remedy','adoption'])
    try:
        ly=pya.Layout();ly.read(str(gds));graph,components,cuts,hit=metal_graph(ly.cell('g1_trip'))
        ol=pya.Layout();ol.read(str(addition));wanted=set()
        for layer in CUTS:
            for poly in region(ol,ol.top_cell(),pya.LayerInfo(layer,0)).each():
                point=poly.bbox().center();wanted.add((layer,point.x,point.y))
        selected={node for node,row in cuts.items()if(row['layer'],round(row['center_um'][0]*1000),round(row['center_um'][1]*1000))in wanted}
        assert len(wanted)==len(selected)==meta['new_cut_count']==464
        roots={n:hit(30,pya.DPoint(21,y).to_itype(.001))[0]for n,y in[('VDD',206),('VDDA',202.75)]}
        probes=[];members={}
        for row in meta['source_access']:
            point=row.get('M1_source_probe_um',row.get('native_M1_rail_probe_um'))
            nodes=hit(8,pya.DPoint(*point).to_itype(.001));assert len(nodes)==1
            probes.append(dict(source_record=row,node=nodes[0]));members.setdefault(row['net'],set()).add(nodes[0])
        losses=[];capacities=[]
        for name,root in roots.items():
            owned=nx.node_connected_component(graph,root);assert members[name]<=owned
            sub=graph.subgraph(owned).copy()
            for node in sorted(selected&owned):
                trial=sub.copy();trial.remove_node(node);retained=nx.node_connected_component(trial,root)
                lost=members[name]-retained
                losses.append(dict(net=name,cut=node,layer=cuts[node]['layer'],center_um=cuts[node]['center_um'],
                                   lost_probe_nodes=sorted(lost),connected=not lost))
            for dac,shift in [('soft',3),('hard',118)]:
                point=(shift+20,21.55 if name=='VDDA' else 12.8)
                start=hit(30,pya.DPoint(*point).to_itype(.001));assert len(start)==1 and start[0]!=root
                capacity=.5*mincut(sub,cuts,start[0],root)
                target=4 if name=='VDDA' else 1
                capacities.append(dict(dac=dac,net=name,collector_point_um=point,half_table_via_only_mA=capacity,
                                       exploratory_geometry_target_mA=target,passed=capacity>=target-1e-10))
        assert len(losses)==464 and all(r['connected']for r in losses)
        assert all(r['passed']for r in capacities)
        result.update(status='passed added-cut-open source-probe connectivity and baseline via-only collector targets',
                      added_cuts=464,source_probes=len(probes),probes=probes,cut_loss_cases=losses,collectors=capacities,
                      scope='Actual native-plus-addition metal topology; ideal metal islands, engineering50% table arithmetic at105C/11years. Not current sharing, wire/contact capacity or lifetime qualification.')
    except Exception as exc:
        result.update(status='failed internal cut audit',error=repr(exc));raise
    finally:
        (a.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({k:v for k,v in result.items()if k not in('probes','cut_loss_cases')},indent=2))


if __name__=='__main__':main()
