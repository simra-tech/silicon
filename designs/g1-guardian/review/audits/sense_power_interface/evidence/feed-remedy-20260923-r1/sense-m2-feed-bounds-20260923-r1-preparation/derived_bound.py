#!/usr/bin/env python3
"""Source-held graph coefficients only; no physical current or attachment chosen."""
import argparse
import collections
from fractions import Fraction
import gzip
import hashlib
import json
import os
from pathlib import Path
import time
from rail_resistance_bound_math import graph_bounds

HERE=Path(__file__).resolve().parent


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def dump(path,value):path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
def rational(value):
    return dict(numerator=str(value.numerator),denominator=str(value.denominator),display_ohm=float(value))


class Union:
    def __init__(self,n):self.parent=list(range(n))
    def find(self,a):
        while self.parent[a]!=a:
            self.parent[a]=self.parent[self.parent[a]];a=self.parent[a]
        return a
    def join(self,a,b):self.parent[self.find(a)]=self.find(b)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('topology','support','output'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();assert not args.output.exists() and len(os.sched_getaffinity(0))==1
    manifest=args.topology/'summary.json'
    assert sha(manifest)=='e6789336f014a8f623dabadd1e4d2cdbc323210b19e17dd26261137b7f1a087d'
    m=json.loads(manifest.read_text());assert m['status']=='passed geometry-only all-contact metal-R topology'
    assert sha(args.topology/'topology.json')==m['topology_sha256']
    assert sha(args.topology/'raw_network.json.gz')==m['raw_network_sha256']
    assert sha(args.topology/'positive_edges.json.gz')=='1e53c318b8d10649833bdddb41960ea4fd84b2c964da91dcfdf6961aca10adfe'
    support=json.loads((args.support/'summary.json').read_text())
    assert support['status']=='passed 171-slot native support inventory; all model attachments unqualified'
    assert sha(args.support/'support_sets.json')==support['support_sets_sha256']
    source=HERE.parents[2]/'blocks/g1_sense/reports/resume-server-20260922/gm4comp3-qualified-source.spice'
    baseline=HERE.parents[2]/'blocks/g1_sense/layout/coordinated_gm4/ring-r8-evidence-20260922-r1/sense-ring-routing-20260922-r8a/g1_sense_physical.gds'
    gds=Path('${BULK}/sense-m2-feed-build-20260923-r1/g1_sense_physical.gds')
    assert sha(source)==m['source_sha256']==support['source_sha256']
    assert sha(baseline)==support['GDS_sha256']=='8060e30ac14a1c4aeb1cf62204c9e95d9a68dbad3d73412fbb34c6a33be8b4f7'
    assert sha(gds)==m['GDS_sha256']=='4b8a82d4a19127e5975d558381cd0f1057235cf51dfbbc58e2219b0f0c4a8bd1'
    args.output.mkdir(parents=True)
    for name,path in [('source.py',Path(__file__)),('math.py',HERE/'rail_resistance_bound_math.py')]:
        (args.output/name).write_bytes(path.read_bytes())
    result=dict(status='running conditional fixed-metal-graph bounds',source_sha256=sha(source),GDS_sha256=sha(gds),
                topology_summary_sha256=sha(manifest),support_summary_sha256=sha(args.support/'summary.json'),
                script_sha256=sha(Path(__file__)),math_sha256=sha(HERE/'rail_resistance_bound_math.py'),
                physical_current_budget='unknown; none selected',model_attachment='not qualified',physical_IR='not run',adoption='not run')
    start=time.monotonic()
    try:
        raw=json.loads(gzip.decompress((args.topology/'raw_network.json.gz').read_bytes()))
        positive=json.loads(gzip.decompress((args.topology/'positive_edges.json.gz').read_bytes()))
        audit=json.loads((args.topology/'topology.json').read_text())
        index={row['id']:i for i,row in enumerate(raw['nodes'])};zero=Union(len(index))
        for edge in raw['edges']:
            if edge['R_ohm']==0:zero.join(index[edge['a']],index[edge['b']])
        roots=sorted({zero.find(i) for i in range(len(index))});compact={root:i for i,root in enumerate(roots)}
        reduced={key:compact[zero.find(value)] for key,value in index.items()}
        reconstructed=[];native_groups=collections.defaultdict(list);raw_nodes={r['id']:r for r in raw['nodes']}
        for edge in raw['edges']:
            a,b=reduced[edge['a']],reduced[edge['b']]
            if edge['R_ohm']==0 or a==b:continue
            reconstructed.append(dict(a=a,b=b,R_ohm=edge['R_ohm']))
            native_groups[tuple(sorted((a,b)))].append(dict(raw_edge_id=edge['id'],R_ohm=edge['R_ohm'],
                endpoints=[raw_nodes[edge['a']],raw_nodes[edge['b']]]))
        assert reconstructed==positive,'Exact native positive graph reconstruction failed'
        connected=Union(len(roots))
        for edge in positive:connected.join(edge['a'],edge['b'])
        names=collections.defaultdict(set);observations=collections.defaultdict(list)
        for obs in audit['observations']:
            assert reduced[obs['raw_node']]==obs['reduced_node']
            component=connected.find(obs['reduced_node']);assert component==obs['R_component']
            names[component].add(obs['source_net']);observations[component].append(obs)
        assert len(names)==134 and all(len(value)==1 and None not in value for value in names.values())
        summaries={}
        for rail in ('vdd','vss'):
            found=[c for c,n in names.items() if n=={rail}];assert len(found)==1;component=found[0]
            nodes=[n for n in range(len(roots)) if connected.find(n)==component]
            edges=[(e['a'],e['b'],e['R_ohm']) for e in positive if connected.find(e['a'])==component]
            bounded=graph_bounds(nodes,edges);leading=[]
            for bridge in sorted(bounded['bridges'],key=lambda r:r['resistance'],reverse=True)[:20]:
                first,last=bridge['descendant_discovery_interval'];counts=collections.Counter();owners=collections.Counter();ports=[]
                for obs in observations[component]:
                    inside=first<=bounded['node_discovery'][obs['reduced_node']]<=last
                    side='partition' if inside else 'complement';counts[side+'/'+obs['kind']]+=1
                    for owner in obs.get('owners',[]):owners[side+'/'+owner['device']+'/'+owner['terminal']]+=1
                    if obs.get('device')=='PORT':ports.append(dict(terminal=obs['terminal'],side=side,
                        scope='single existing source witness only; not full equipotential pin'))
                leading.append(dict(nodes=bridge['nodes'],cut_resistance_ohm=rational(bridge['resistance']),
                    native_edges=native_groups[bridge['nodes']],observation_counts=dict(counts),
                    owner_footprint_counts=dict(owners),port_witnesses=ports))
            summary=dict(nodes=bounded['nodes'],edges=bounded['native_edges'],bridge_count=len(bounded['bridges']),
                tree_diameter_upper_ohm=rational(bounded['tree_diameter_upper_ohm']),
                bridge_diameter_lower_ohm=rational(bounded['bridge_diameter_lower_ohm']),
                computational_tree_endpoints=bounded['tree_endpoint_pair'],
                complete_positive_current_budget_A='unknown',voltage_oscillation_formula='D_tree * I_positive_complete',
                display_mV_per_mA_complete_positive_budget=float(bounded['tree_diameter_upper_ohm']),
                leading_bridges=leading)
            dump(args.output/(rail+'_bounds.json'),summary);summaries[rail]={k:v for k,v in summary.items() if k!='leading_bridges'}
        assert sha(source)==result['source_sha256'] and sha(gds)==result['GDS_sha256']
        result.update(status='passed conditional positive-metal-graph coefficients; no physical IR acceptance',rails=summaries,
                      not_run=['Complete current budget and external-feed attachment','Continuum/intrinsic/substrate resistance',
                               'Compact-model contact weights','Electrical/IR/EM acceptance','Fullchip adoption'])
    except Exception as exc:
        result.update(status='failed metal-graph bound audit',error=repr(exc));raise
    finally:
        result['wall_s']=time.monotonic()-start;dump(args.output/'summary.json',result);print(json.dumps(result,indent=2))


if __name__=='__main__':main()
