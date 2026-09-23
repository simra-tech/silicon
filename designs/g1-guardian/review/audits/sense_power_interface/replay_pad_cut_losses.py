#!/usr/bin/env python3
"""Replay exact saved pad network for418 selected cut losses and straight M2 sections."""
import argparse
import gzip
import json
import os
from pathlib import Path
import time
import numpy as np
import klayout.db as kdb
from pad_metal_r_controls import base,BASE,IDS,CUTS


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in('network','inventory','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();assert not a.output.exists()and len(os.sched_getaffinity(0))==1 and kdb.__version__=='0.30.9'
    meta=json.loads((a.network/'summary.json').read_text())
    assert meta['status'].startswith('completed conditional')and meta['every_cut_geometry_binding']=='passed'
    assert meta['inventory_sha256']==base.sha(a.inventory)and meta['target_A']==.010
    raw_path=a.network/'raw_network.json.gz';raw=json.loads(gzip.decompress(raw_path.read_bytes()))
    raw['point_to_node']={int(k):v for k,v in raw['point_to_node'].items()}
    reference=json.loads((a.network/'solution.json').read_text());points=reference['points']
    solved,voltage=base.solve(raw,points,1)
    assert solved['maximum_absolute_delta_V']==reference['maximum_absolute_delta_V']
    assert [r['delta_V']for r in solved['points']]==[r['delta_V']for r in reference['points']]
    nodes={n['id']:n for n in raw['nodes']};index={n['id']:i for i,n in enumerate(raw['nodes'])}
    union=base.Union(len(index))
    for edge in raw['edges']:
        if edge['R_ohm']==0:union.join(index[edge['a']],index[edge['b']])
    roots=sorted({union.find(i)for i in range(len(index))});compact={r:i for i,r in enumerate(roots)}
    reduced={identifier:compact[union.find(i)]for identifier,i in index.items()}
    pair_names={frozenset((IDS[lo],IDS[hi])):name for name,(lo,hi)in CUTS.items()}
    cuts=[];rail_edges=[]
    for edge in raw['edges']:
        left,right=nodes[edge['a']],nodes[edge['b']]
        if left['layer']!=right['layer']:
            name=pair_names[frozenset((left['layer'],right['layer']))]
            bbox=left['location_um'];assert bbox==right['location_um']
            cuts.append(dict(edge=edge,cut=name,bbox_um=bbox,
                             half_table_A=.0007 if name=='TopVia1'else .005 if name=='TopVia2'else .0002))
        elif left['layer']==IDS['M2']:
            lb,rb=left['location_um'],right['location_um']
            lx=(lb[0]+lb[2])/2;rx=(rb[0]+rb[2])/2
            if min(lx,rx)<1150<max(lx,rx):
                assert (lb[2]<1150 and rb[0]>1150)or(rb[2]<1150 and lb[0]>1150)
                rail_edges.append((edge,left,right))
    assert len(cuts)==2194 and len(rail_edges)==10
    selected=[r for r in cuts if r['cut']in('Via3','Via4','TopVia1','TopVia2')or
              (r['cut']=='Via2'and abs((r['bbox_um'][0]+r['bbox_um'][2])/2-1093.145)<1e-8)]
    assert len(selected)==418
    inv=json.loads(a.inventory.read_text());m2=kdb.Region();trans=kdb.Trans(1,False,1273000,355000)
    for row in inv['polygons']:
        if row['layer']!=10:continue
        poly=kdb.Polygon([kdb.Point(round(x*1000),round(y*1000))for x,y in row['hull_um']])
        for hole in row['holes_um']:poly.insert_hole([kdb.Point(round(x*1000),round(y*1000))for x,y in hole])
        m2.insert(poly.transformed(trans))
    section=m2&kdb.Region(kdb.Box(1150000,0,1150001,2000000))
    bands=sorted((poly.bbox().bottom*.001,poly.bbox().top*.001)for poly in section.each())
    assert len(bands)==10
    rail_rows=[];used=set()
    for edge,left,right in rail_edges:
        yleft=(left['location_um'][1]+left['location_um'][3])/2
        yright=(right['location_um'][1]+right['location_um'][3])/2
        matches=[i for i,(bottom,top)in enumerate(bands)if bottom<=yleft<=top and bottom<=yright<=top]
        assert len(matches)==1 and matches[0]not in used;used.add(matches[0]);i=matches[0]
        rail_rows.append(dict(edge=edge,band_um=bands[i],half_table_A=(bands[i][1]-bands[i][0])*.001))
    cut_a=np.array([reduced[r['edge']['a']]for r in cuts]);cut_b=np.array([reduced[r['edge']['b']]for r in cuts])
    resistances=np.array([r['edge']['R_ohm']for r in cuts]);limits=np.array([r['half_table_A']for r in cuts])
    indices={r['edge']['id']:i for i,r in enumerate(cuts)}
    def evaluate(v,removed=None):
        current=(v[cut_a]-v[cut_b])/resistances;util=np.abs(current)/limits
        if removed is not None:util[indices[removed]]=0
        worst=int(np.argmax(util));rails=[]
        for r in rail_rows:
            edge=r['edge'];value=float((v[reduced[edge['a']]]-v[reduced[edge['b']]])/edge['R_ohm'])
            rails.append(dict(band_um=r['band_um'],current_A=value,half_table_A=r['half_table_A'],utilization=abs(value)/r['half_table_A']))
        assert abs(sum(abs(r['current_A'])for r in rails)-.010)<1e-10
        return dict(max_cut_utilization=float(util[worst]),worst_cut={k:value for k,value in cuts[worst].items()if k!='edge'},
                    worst_cut_current_A=float(current[worst]),long_M2_sections=rails,
                    max_long_M2_utilization=max(r['utilization']for r in rails))
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    result=dict(status='running',network_summary_sha256=base.sha(a.network/'summary.json'),raw_sha256=base.sha(raw_path),
                script_sha256=base.sha(Path(__file__)),base_helper_sha256=base.sha(BASE),
                baseline_exact_replay='passed',baseline=evaluate(voltage),selected_cut_count=418,
                omitted_cut_count=1776,omitted_scope='918 Via1 and858 bottom Via2 losses not run; baseline currents were retained.',
                not_run=['all2194 cut-loss cases','full-metal section current/crowding','source-boundary/mesh/PVT/temperature convergence',
                         'actual load partition/bond/package/ESD','full current-capacity/lifetime qualification','adoption'])
    started=time.monotonic();rows=[];base.dump(a.output/'summary.json',result)
    try:
        for i,cut in enumerate(selected):
            removed=cut['edge']['id'];trial=dict(raw,edges=[e for e in raw['edges']if e['id']!=removed])
            solution,v=base.solve(trial,points,1);values=evaluate(v,removed)
            passed=values['max_cut_utilization']<=1+1e-8 and values['max_long_M2_utilization']<=1+1e-8
            rows.append(dict(removed={k:value for k,value in cut.items()if k!='edge'},status='passed'if passed else'failed',
                             KCL_residual_A=solution['max_free_node_KCL_residual_A'],maximum_delta_V=solution['maximum_absolute_delta_V'],**values))
            if i%25==0:print(json.dumps(dict(completed=i+1,elapsed_s=time.monotonic()-started)),flush=True)
        base.dump(a.output/'cut_loss_results.json',rows)
        result.update(status='passed selected418 cut-loss and ten long-M2 section diagnostic'if all(r['status']=='passed'for r in rows)else'failed selected cut-loss diagnostic',
            completed=len(rows),failures=[r for r in rows if r['status']=='failed'],
            maximum_cut_utilization=max(r['max_cut_utilization']for r in rows),
            maximum_long_M2_utilization=max(r['max_long_M2_utilization']for r in rows),
            maximum_delta_V=max(r['maximum_delta_V']for r in rows))
    except Exception as exc:
        result.update(status='failed cut-loss method',error=repr(exc),completed=len(rows));raise
    finally:
        result['wall_s']=time.monotonic()-started;base.dump(a.output/'summary.json',result)
        print(json.dumps({k:v for k,v in result.items()if k not in('baseline','failures')},indent=2))


if __name__=='__main__':main()
