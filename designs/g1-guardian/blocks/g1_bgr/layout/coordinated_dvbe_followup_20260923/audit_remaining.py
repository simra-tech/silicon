#!/usr/bin/env python3
"""Map remaining conditional OP drops back to held native metal endpoints."""
import argparse
import collections
import gzip
import hashlib
import json
import math
import os
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args();assert not a.output.exists() and set(os.sched_getaffinity(0))=={0}
    bulk=Path(os.environ['G1_RESULTS_ROOT'])
    prep=bulk/'bgr-dvbe-fixture-20260923-r1/kpex'
    run=bulk/'bgr-dvbe-kpex-20260923-r1'
    paths=[bulk/'bgr-metal-r-dvbe-kpex-20260923-r1/result/raw_network.json.gz',
           prep/'positive_edges.json',prep/'point_nodes.json',run/'metal_node_voltages.json',
           run/'conditional_analysis.json',Path(__file__)]
    inputs={str(p):sha(p) for p in paths}
    raw=json.loads(gzip.decompress(paths[0].read_bytes()))
    edges,points,voltage,prior=[json.loads(p.read_text()) for p in paths[1:5]]
    assert len(edges)==42615 and len(points)==3355 and len(voltage)==33410
    nodes={n['id']:n for n in raw['nodes']}
    originals={e['id']:e for e in raw['edges'] if e['R_ohm']>0}
    assert {e['raw_edge_id'] for e in edges}==set(originals)
    parent={n:n for n in voltage}
    def find(n):
        while parent[n]!=n:
            parent[n]=parent[parent[n]];n=parent[n]
        return n
    for e in edges:parent[find(e['a'])]=find(e['b'])
    owners=collections.defaultdict(set)
    for p in points:owners[find(p['node'])].add(p['source_net'])
    assert len(owners)==55 and all(len(v)==1 for v in owners.values())
    assert set(owners)=={find(n) for n in voltage}
    rows=collections.defaultdict(list)
    for e in edges:
        orig=originals[e['raw_edge_id']];assert orig['R_ohm']==e['R_ohm']>0
        ends=[nodes[orig[t]] for t in ('a','b')]
        dv=voltage[e['a']]-voltage[e['b']]
        net=next(iter(owners[find(e['a'])]))
        rows[net].append(dict(resistor=e['resistor'],R_ohm=e['R_ohm'],delta_V=dv,
            current_A=dv/e['R_ohm'],power_W=dv*dv/e['R_ohm'],
            endpoint_layers=[n['layer'] for n in ends],
            endpoint_locations_um=[n['location_um'] for n in ends]))
    total=math.fsum(e['power_W'] for r in rows.values() for e in r)
    assert math.isclose(total,prior['total_metal_power_W'],rel_tol=1e-13)
    result=dict(status='passed source-owned saved endpoint attribution',inputs=inputs,
        total_positive_edges=len(edges),nodes=len(voltage),source_nets=55,
        per_net={n:dict(edges=len(r),total_power_W=math.fsum(e['power_W'] for e in r),
            largest_20_edges=sorted(r,key=lambda e:abs(e['delta_V']),reverse=True)[:20]) for n,r in rows.items()},
        limitation='Endpoints do not prove the complete edge support polygon. Geometry clearance and actual nonlinear remedy remain not run.',
        new_simulation='not run',source_model_changes='not applicable')
    assert all(sha(Path(p))==h for p,h in inputs.items())
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    (a.output/'analysis.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({n:result['per_net'][n]['largest_20_edges'][:4] for n in ('dvbe','vdd','vss')},indent=2))


if __name__=='__main__':main()
