#!/usr/bin/env python3
"""Independent saved six-cut digital-feed removal controls; not EM signoff."""
import argparse
import json
import os
from pathlib import Path
import pya
import networkx as nx
from place_closed_analog import sha
from sense_power_interface.audit_overlay_graph import metal_graph, mincut


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert not a.output.exists() and len(os.sched_getaffinity(0))==1
    assert pya.__version__=='0.30.9'
    source=a.candidate/'power_overlay.gds';meta=json.loads((a.candidate/'analysis.json').read_text())
    assert meta['status'].startswith('passed') and sha(source)==meta['overlay_sha256']
    ly=pya.Layout();ly.read(str(source));graph,components,cuts,hit=metal_graph(ly.top_cell())
    assert len(cuts)==6 and nx.number_connected_components(graph)==2
    rows=[]
    for name,x,y in [('VDD',388760,354660),('VSS',394960,334660)]:
        left,=hit(126,pya.Point(x,376000));right,=hit(134,pya.Point(x,y))
        owned=nx.node_connected_component(graph,left);assert right in owned
        sub=graph.subgraph(owned).copy();losses=[]
        assert len(set(cuts)&owned)==3
        for key in sorted(set(cuts)&owned):
            trial=sub.copy();trial.remove_node(key)
            assert nx.has_path(trial,left,right)
            capacity=.5*mincut(trial,cuts,left,right)
            assert capacity>=8
            losses.append(dict(cut=key,layer=cuts[key]['layer'],center_um=cuts[key]['center_um'],half_table_mA=capacity))
        rows.append(dict(net=name,half_table_via_only_mA=.5*mincut(sub,cuts,left,right),
            worst_one_cut_lost_mA=min(r['half_table_mA'] for r in losses),removed_cuts=losses))
    result=dict(status='passed six digital-feed cut removal controls',overlay_sha256=sha(source),
        metadata_sha256=sha(a.candidate/'analysis.json'),script_sha256=sha(Path(__file__)),
        helper_sha256=sha(Path(__file__).parent/'sense_power_interface/audit_overlay_graph.py'),actual_cuts=len(cuts),nets=rows,
        scope='Ideal equipotential metal components; via-only capacity at50% of105C/11year table. Prospective8mA sizing, not actual current envelope or sharing.',
        not_run=['native wire IR/current sharing','actual-current PVT/EM/hot-lifetime qualification','final routed integration'],
        not_applicable=['physical cut removal in implementation GDS'])
    assert sha(source)==result['overlay_sha256']
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
