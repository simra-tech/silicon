#!/usr/bin/env python3
"""Compare saved conditional OPs and directly verify whole-mesh extrema."""
import argparse
import collections
import hashlib
import json
import math
from pathlib import Path


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def whole(prepared,run):
    paths=[prepared/'positive_edges.json',prepared/'point_nodes.json',run/'metal_node_voltages.json',run/'conditional_analysis.json',run/'summary.json']
    edges,points,voltage,analysis,summary=[json.loads(p.read_text()) for p in paths]
    assert summary['status']=='passed conditional nonlinear OP completion and source controls'
    assert summary['all2842_parameters_exact'] and not summary['errors']
    assert all(math.isfinite(v) for v in voltage.values())
    parent={n:n for n in voltage}
    def find(n):
        while parent[n]!=n:
            parent[n]=parent[parent[n]];n=parent[n]
        return n
    for e in edges:
        assert math.isfinite(e['R_ohm']) and e['R_ohm']>0
        parent[find(e['a'])]=find(e['b'])
    owners=collections.defaultdict(set);terminal=collections.defaultdict(list)
    for p in points:
        owners[find(p['node'])].add(p['source_net'])
        terminal[p['source_net']].append(voltage[p['node']])
    assert len(points)==3355 and len(owners)==55 and all(len(v)==1 for v in owners.values())
    assert set(owners)=={find(n) for n in voltage}
    values=collections.defaultdict(list)
    for n,v in voltage.items():values[next(iter(owners[find(n)]))].append(v)
    rows={}
    for net,vals in values.items():
        terms=terminal[net]
        excess=max(0.,max(vals)-max(terms),min(terms)-min(vals))
        rows[net]=dict(all_node_count=len(vals),point_count=len(terms),
            all_min_V=min(vals),all_max_V=max(vals),all_span_V=max(vals)-min(vals),
            point_min_V=min(terms),point_max_V=max(terms),point_span_V=max(terms)-min(terms),
            maximum_interior_excursion_outside_points_V=excess,
            exact_extrema_within_points=excess==0)
    return dict(summary=summary,analysis=analysis,ranges=rows,
        exact_discrete_maximum_principle_all55=all(r['exact_extrema_within_points'] for r in rows.values()),
        maximum_interior_excursion_V=max(r['maximum_interior_excursion_outside_points_V'] for r in rows.values()),
        inputs={str(p):sha(p) for p in paths})


def main():
    ap=argparse.ArgumentParser()
    for k in ('baseline-prepared','candidate-prepared','baseline-kpex','baseline-lef','candidate-kpex','candidate-lef','output'):
        ap.add_argument('--'+k,type=Path,required=True)
    a=ap.parse_args();assert not a.output.exists()
    rows=[];inputs={}
    for case in ('kpex','lef'):
        old=whole(a.baseline_prepared/case,getattr(a,'baseline_'+case))
        new=whole(a.candidate_prepared/case,getattr(a,'candidate_'+case))
        assert old['summary']['parameter_before']==new['summary']['parameter_before']
        inputs.update(old['inputs']);inputs.update(new['inputs'])
        op=old['analysis']['actual_macro_ports'];np=new['analysis']['actual_macro_ports']
        reference=new['analysis']['source_net_voltage_ranges']['vref']['zero_R_V']
        rows.append(dict(case=case,old_VREF_V=op['vref']['voltage_V'],new_VREF_V=np['vref']['voltage_V'],
            original_source_VREF_V=reference,delta_VREF_V=np['vref']['voltage_V']-op['vref']['voltage_V'],
            new_error_to_original_V=np['vref']['voltage_V']-reference,
            old_error_to_original_V=op['vref']['voltage_V']-reference,
            full2842_before_exact=True,source_devices=1036,
            original_mesh_positive_edges=old['analysis']['positive_edges'],new_mesh_positive_edges=new['analysis']['positive_edges'],
            old_ranges=old['ranges'],new_ranges=new['ranges'],
            old_exact_maximum_principle=old['exact_discrete_maximum_principle_all55'],
            new_exact_maximum_principle=new['exact_discrete_maximum_principle_all55'],
            old_maximum_interior_excursion_V=old['maximum_interior_excursion_V'],
            new_maximum_interior_excursion_V=new['maximum_interior_excursion_V'],
            old_KCL_interior_A=old['analysis']['metal_interior_KCL_max_A'],
            new_KCL_interior_A=new['analysis']['metal_interior_KCL_max_A'],
            old_supply_A=op['vdd']['current_into_metal_A'],new_supply_A=np['vdd']['current_into_metal_A'],
            warnings=new['summary']['warnings'],runtime_s=new['summary']['runtime']['wall_s']))
    assert all(sha(Path(p))==h for p,h in inputs.items())
    result=dict(status='passed saved conditional comparison; no model qualification or adoption',
        cases=rows,inputs=inputs,worker_sha256=sha(Path(__file__)),
        limitation='Whole-node extrema directly enumerated, not inferred from rounded terminal displays. Exact maximum-principle differences are reported without a tolerance waiver.',
        new_analog='not run; reads completed OPs',canonical_adoption='not run',
        completeness='Metal-only; R BN, substrate, model deembedding and historical C planes remain unqualified')
    a.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps([dict(case=r['case'],old_VREF_V=r['old_VREF_V'],new_VREF_V=r['new_VREF_V'],delta_VREF_V=r['delta_VREF_V'],
        maximum_principle=r['new_exact_maximum_principle'],max_excursion=r['new_maximum_interior_excursion_V']) for r in rows],indent=2))


if __name__=='__main__':main()
