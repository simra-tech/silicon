#!/usr/bin/env python3
"""Conditional actual-pad/new-feed metallic R, with individually bound cut currents."""
import argparse
import collections
import gzip
import json
import math
import os
from pathlib import Path
import time
import klayout.db as kdb
from pad_metal_r_controls import base,BASE,PAIRS,CUTS,IDS,SIZE,scenario


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in('inventory','candidate','controls','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();assert not a.output.exists()and len(os.sched_getaffinity(0))==1 and kdb.__version__=='0.30.9'
    inv=json.loads(a.inventory.read_text());meta=json.loads((a.candidate/'analysis.json').read_text())
    controls=json.loads((a.controls/'summary.json').read_text())
    helper=Path(__file__).with_name('pad_metal_r_controls.py')
    assert controls['status']=='passed twelve analytic native-metal via controls'
    assert controls['script_sha256']==base.sha(helper)and controls['base_helper_sha256']==base.sha(BASE)
    assert inv['GDS_sha256']=='8b66a958759478987fa9de59746a0554f9bd065307e730342f10e891082134e6'
    assert meta['status'].startswith('passed')and meta['source_GDS_sha256']=='226c5aad876b9aea1ec2cd5874c828b2ae87ffb80a3efded7f8d9a2389cd8e05'
    source=a.candidate/'power_overlay.gds';assert base.sha(source)==meta['overlay_sha256']
    a.output.mkdir(parents=True)
    for script in(Path(__file__),helper,BASE):(a.output/script.name).write_bytes(script.read_bytes())
    result=dict(status='running',script_sha256=base.sha(Path(__file__)),inventory_sha256=base.sha(a.inventory),
        candidate_sha256=base.sha(a.candidate/'analysis.json'),overlay_sha256=base.sha(source),
        controls_sha256=base.sha(a.controls/'summary.json'),target_A=.010,
        scope='Pure actual pad metallic net plus new feed only; point-boundary source/sink, no compact devices, no existing parallel SENSE feed.',
        not_run=['wire cross-section current-capacity qualification','mesh/source-boundary convergence','one-cut-loss R redistribution',
                 'actual load partition/ESD leakage/bond/package','temperature/PVT/EM/lifetime','complete pad current qualification','adoption'])
    identity_controls=[]
    for row in controls['controls']:
        control_path=a.controls/(row['cut']+'_'+str(row['count'])+'.json')
        control=json.loads(control_path.read_text());nodes={n['id']:n for n in control['raw']['nodes']}
        cross=[e for e in control['raw']['edges']if nodes[e['a']]['layer']!=nodes[e['b']]['layer']]
        assert len(cross)==row['count']
        assert all(nodes[e['a']]['location_um']==nodes[e['b']]['location_um']for e in cross)
        identity_controls.append(dict(path=control_path.name,sha256=base.sha(control_path),cuts=len(cross)))
    result['raw_cut_identity_controls']=identity_controls
    started=time.monotonic();base.dump(a.output/'summary.json',result)
    try:
        regions={IDS[name]:kdb.Region()for name in PAIRS};name_by_layer={pair[0]:name for name,pair in PAIRS.items()}
        trans=kdb.Trans(1,False,1273000,355000)
        for row in inv['polygons']:
            poly=kdb.Polygon([kdb.Point(round(x*1000),round(y*1000))for x,y in row['hull_um']])
            for hole in row['holes_um']:poly.insert_hole([kdb.Point(round(x*1000),round(y*1000))for x,y in hole])
            assert poly.area()==round(row['area_um2']*1e6)
            regions[IDS[name_by_layer[row['layer']]]].insert(poly.transformed(trans))
        for row in inv['vias']:
            poly=kdb.Polygon(kdb.Box(*[round(v*1000)for v in row['bbox_um']])).transformed(trans)
            regions[IDS[name_by_layer[row['layer']]]].insert(poly)
        ly=kdb.Layout();ly.read(str(source));top=ly.top_cell()
        for name,pair in PAIRS.items():
            regions[IDS[name]]+=kdb.Region(top.begin_shapes_rec(ly.layer(*pair)))
            regions[IDS[name]]=regions[IDS[name]].merged()
        expected={}
        for name in CUTS:
            for poly in regions[IDS[name]].each():
                b=poly.bbox();key=(name,b.left,b.bottom,b.right,b.top)
                assert key not in expected and poly.area()==round(SIZE[name]*1000)**2
                assert poly.area()==b.area()
                expected[key]=None
        model=scenario();assert model==controls['scenario']
        points=[dict(id=0,layer='TM2',point_dbu=[1271500,395000],injection_A=.010,source_net='VDDA',reference_ports=['pad07']),
                dict(id=1,layer='TM2',point_dbu=[1048000,401500],injection_A=-.010,source_net='VDDA',reference_ports=[])]
        raw=base.extract(regions,points,model)
        (a.output/'raw_network.json.gz').write_bytes(gzip.compress(json.dumps(raw,allow_nan=False).encode(),mtime=0))
        solved,voltage=base.solve(raw,points,1)
        base.dump(a.output/'solution.json',solved)
        index={n['id']:i for i,n in enumerate(raw['nodes'])};union=base.Union(len(index))
        for edge in raw['edges']:
            if edge['R_ohm']==0:union.join(index[edge['a']],index[edge['b']])
        roots=sorted({union.find(i)for i in range(len(index))});compact={r:i for i,r in enumerate(roots)}
        reduced={identifier:compact[union.find(i)]for identifier,i in index.items()}
        nodes={n['id']:n for n in raw['nodes']}
        layer_pair={frozenset((IDS[lo],IDS[hi])):name for name,(lo,hi)in CUTS.items()}
        cuts=[];wire=[]
        for edge in raw['edges']:
            left,right=nodes[edge['a']],nodes[edge['b']]
            if edge['R_ohm']==0:continue
            current=float((voltage[reduced[edge['a']]]-voltage[reduced[edge['b']]])/edge['R_ohm'])
            assert math.isfinite(current)
            if left['layer']==right['layer']:
                wire.append(dict(edge=edge['id'],layer=left['layer'],current_A=current,R_ohm=edge['R_ohm']))
                continue
            name=layer_pair[frozenset((left['layer'],right['layer']))]
            bounds=tuple(round(v*1000)for v in left['location_um'])
            assert bounds==tuple(round(v*1000)for v in right['location_um'])
            key=(name,)+bounds;assert key in expected and expected[key]is None
            assert abs(edge['R_ohm']-model['cut_ohm'][name])<=1e-8
            limit=.0007 if name=='TopVia1'else .005 if name=='TopVia2'else .0002
            row=dict(cut=name,bbox_dbu=bounds,current_A=current,half_table_A=limit,utilization=abs(current)/limit)
            expected[key]=row;cuts.append(row)
        assert len(cuts)==len(expected)and all(v is not None for v in expected.values())
        native_counts=collections.Counter(name_by_layer[r['layer']]for r in inv['vias'])
        actual_counts=collections.Counter(r['cut']for r in cuts)
        assert sum(actual_counts.values())==sum(native_counts.values())+148
        failures=[r for r in cuts if r['utilization']>1+1e-8]
        base.dump(a.output/'cut_currents.json',cuts);base.dump(a.output/'wire_edge_currents_NOT_CAPACITY.json',wire)
        result.update(status='completed conditional actual-pad metallic R; full current qualification not run',
            scenario=model,native_cut_counts=dict(native_counts),actual_cut_counts=dict(actual_counts),
            every_cut_geometry_binding='passed',KCL_residual_A=solved['max_free_node_KCL_residual_A'],
            maximum_delta_V=solved['maximum_absolute_delta_V'],effective_R_ohm=abs(solved['points'][1]['delta_V'])/.010,
            conditional_cut_target='failed'if failures else'passed',cut_failures=failures,
            worst_cut=max(cuts,key=lambda r:r['utilization']),nodes=len(raw['nodes']),edges=len(raw['edges']))
    except Exception as exc:
        result.update(status='failed conditional pad-metal method',error=repr(exc));raise
    finally:
        result['wall_s']=time.monotonic()-started;base.dump(a.output/'summary.json',result)
        print(json.dumps(result,indent=2))


if __name__=='__main__':main()
