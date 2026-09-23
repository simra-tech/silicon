#!/usr/bin/env python3
"""Independent saved BGR/OSC overlay cut-open audit and stock main DRC."""
import argparse
import collections
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace
import xml.etree.ElementTree as ET
import networkx as nx
import pya

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from place_closed_analog import sha
from audit_overlay_graph import metal_graph, mincut
PDK=Path('/foss/pdks/ihp-sg13g2')
DRC=PDK/'libs.tech/klayout/tech/drc'


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--execute',action='store_true')
    a=p.parse_args()
    assert pya.__version__=='0.30.9' and len(os.sched_getaffinity(0))==1
    assert(PDK/'COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    meta=json.loads((a.candidate/'analysis.json').read_text())
    macro=meta.get('macro','bgr');assert macro in('bgr','osc','t2f')
    gds=a.candidate/'power_overlay.gds'
    assert meta['status'].startswith('passed')and sha(gds)==meta['overlay_sha256']
    sys.path.insert(0,str(DRC))
    spec=importlib.util.spec_from_file_location('stock',DRC/'run_drc.py')
    stock=importlib.util.module_from_spec(spec);spec.loader.exec_module(stock)
    args=SimpleNamespace(density_thr=1,drc_json=None,run_mode='deep',precheck_drc=False,
                         disable_extra_rules=False,no_feol=False,no_beol=False,no_offgrid=False,
                         no_angle=False,density_sanity=False,no_density=True,no_recommended=False,
                         table=[],topcell=macro+'_power_interface_NOT_ADOPTED')
    switches=stock.generate_klayout_switches(args,str(gds))
    if a.execute:
        stock.run_check(DRC/'ihp-sg13g2.drc',['main'],str(gds),a.output/'reports',switches)
        return
    assert not a.output.exists();(a.output/'reports').mkdir(parents=True)
    (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    rules={str(q.relative_to(PDK)):sha(q)for q in(PDK/'libs.tech/klayout/tech').rglob('*')if q.is_file()}
    result=dict(status='running',overlay_sha256=sha(gds),candidate_manifest_sha256=sha(a.candidate/'analysis.json'),
                script_sha256=sha(Path(__file__)),rule_hashes=rules,
                not_run=['native-neighbor DRC','fullchip LVS/PEX/current sharing/IR/EM/PVT','adoption']+
                        (['VDDA pad supply connection']if macro in('bgr','t2f')else[]),
                not_applicable=['VDDA pad supply connection']if macro=='osc'else[])
    try:
        ly=pya.Layout();ly.read(str(gds))
        graph,components,cuts,hit=metal_graph(ly.top_cell())
        assert len(cuts)==(10 if macro=='bgr'else 56)and nx.number_connected_components(graph)==2
        rows=[]
        ports=([('VDDA',(67,743400,878000),(134,743400,922000)),
                ('VSS',(67,749650,873000),(126,736800,873000))]if macro=='bgr'else
               [('VDD',(30,772000,1089570),(126,750000,1089570)),
                ('VSS',(30,774000,954000),(126,774000,954000))]if macro=='osc'else
               [('VDD',(30,1044000,1047600),(126,1061920,1047600)),
                ('VSS',(30,1039200,954300),(126,1039200,954300))])
        for net,start,end in ports:
            left=hit(start[0],pya.Point(*start[1:]));right=hit(end[0],pya.Point(*end[1:]))
            assert len(left)==len(right)==1
            left,right=left[0],right[0]
            owned=nx.node_connected_component(graph,left);assert right in owned
            sub=graph.subgraph(owned).copy();losses=[]
            for node in sorted(owned):
                if node not in cuts:continue
                trial=sub.copy();trial.remove_node(node)
                connected=nx.has_path(trial,left,right)
                capacity=.5*mincut(trial,cuts,left,right)if connected else 0
                losses.append(dict(cut=node,layer=cuts[node]['layer'],connected=connected,
                                   center_um=cuts[node]['center_um'],half_table_mA=capacity))
            assert all(r['connected']and r['half_table_mA']>=1-1e-10 for r in losses)
            rows.append(dict(net=net,half_table_via_only_mA=.5*mincut(sub,cuts,left,right),
                             worst_one_cut_lost_mA=min(r['half_table_mA']for r in losses),removed_cuts=losses))
        result.update(saved_graph='passed',actual_cuts=len(cuts),nets=rows,
                      graph_scope='Ideal metal components; additive via capacity at50% engineering target from105C/11year table, not actual sharing or lifetime')
        (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
        command=['timeout','--kill-after=5','90','python3',str(Path(__file__).resolve())]+sys.argv[1:]+['--execute']
        started=time.monotonic()
        with(a.output/'stock.log').open('x')as log:run=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
        reports=[]
        for path in(a.output/'reports').glob('*_main.lyrdb'):
            counts=collections.Counter(i.findtext('category')for i in ET.parse(path).findall('.//items/item'))
            reports.append(dict(path=str(path.relative_to(a.output)),sha256=sha(path),markers=sum(counts.values()),categories=dict(counts)))
        unchanged=sha(gds)==result['overlay_sha256']and all(sha(PDK/q)==h for q,h in rules.items())
        passed=run.returncode==0 and unchanged and len(reports)==1 and reports[0]['markers']==0
        result.update(status='passed isolated '+macro.upper()+' stock and cut-open gates'if passed else'failed isolated '+macro.upper()+' stock gate',
                      reports=reports,returncode=run.returncode,wall_s=time.monotonic()-started,inputs_rules_unchanged=unchanged)
    except Exception as exc:
        result.update(status='failed isolated '+macro.upper()+' check',error=repr(exc))
        raise
    finally:
        (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({k:v for k,v in result.items()if k not in('rule_hashes','nets')},indent=2))
    raise SystemExit(0 if result['status'].startswith('passed')else 1)


if __name__=='__main__':main()
