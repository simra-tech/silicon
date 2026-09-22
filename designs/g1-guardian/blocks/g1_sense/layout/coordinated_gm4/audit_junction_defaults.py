#!/usr/bin/env python3
"""Evaluate pinned unchanged HV default junction equations against inventoried polygons."""
import argparse,hashlib,json
from pathlib import Path

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def default(w,ng):
    f=max(w/ng,.15);z1=.34;z2=.38
    if ng%2:
        area=f*(z1+(ng-1)/2*z2);perim=2*(f*((ng-1)/2+1)+z1+(ng-1)/2*z2)
        return dict(as_um2=area,ad_um2=area,ps_um=perim,pd_um=perim)
    return dict(as_um2=f*(2*z1+max(0,(ng-2)/2)*z2),ad_um2=f*z2/2*ng,
                ps_um=2*(f*(2+max(ng-2,0)/2)+2*z1+max(ng-2,0)/2*z2),pd_um=(f+z2)*ng)
def geom(strips):
    return dict(as_um2=sum(x['area_um2'] for x in strips[::2]),ad_um2=sum(x['area_um2'] for x in strips[1::2]),
                ps_um=sum(x['full_polygon_perimeter_um'] for x in strips[::2]),pd_um=sum(x['full_polygon_perimeter_um'] for x in strips[1::2]))
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--inventory',type=Path,required=True);p.add_argument('--model',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists()
    assert sha(a.model)=='58ce3084c253f2d3753c3b95386e8f4b81dcadfed4f4503dce56862a556c3328'
    inv=json.loads(a.inventory.read_text());rows=[]
    for row in inv['devices']:
        for view,record in row['source_comparisons'].items():
            q=record['source']['params'];assert all(k not in q for k in ('as','ad','ps','pd','rfmode','z1','z2','wmin'))
            w=float(q['w'].rstrip('u'));ng=int(q['ng']);expected=default(w,ng);native=geom(record['expected_native']['diffusion_strips'])
            assert all(abs(expected[k]-native[k])<1e-8 for k in expected)
            actual=geom(row['physical']['diffusion_strips']) if row['native_group']!='PAIR' else None
            rows.append({'device':row['device'],'source_view':view,'default_junction':expected,'source_native_junction':native,
                         'source_native_default_matches':True,'delivered_junction':actual,
                         'delivered_matches_source_default':None if actual is None else all(abs(expected[k]-actual[k])<1e-8 for k in expected),
                         'delta_delivered_minus_default':None if actual is None else {k:actual[k]-expected[k] for k in expected},
                         'terminal_scope':'Even strips source, odd drain from generator topology; independent physical net mapping is a separate gate.'})
    pair=next(r for r in inv['devices'] if r['device']=='XM1');actual=geom(pair['physical']['diffusion_strips'])
    expected={k:sum(r['default_junction'][k] for r in rows if r['source_view']=='g1_ota' and r['device'] in ('XM1','XM2')) for k in actual}
    paired={'scope':'Aggregate two logical input MOS junctions; shared-source partition must not double-count common physical strips.',
            'delivered_shared_PAIR':actual,'sum_two_source_default_M1_M2':expected,'delta':{k:actual[k]-expected[k] for k in actual},
            'status':'failed aggregate default-junction geometry fidelity'}
    assert abs(paired['delta']['as_um2']+1.8)<1e-8 and abs(paired['delta']['ps_um']+12.6)<1e-8
    result={'status':'failed inherited junction/default geometry fidelity','model_sha256':sha(a.model),'inventory_sha256':sha(a.inventory),
            'script_sha256':sha(Path(__file__)),'rows':rows,'shared_input_pair':paired,
            'equation_scope':'Unchanged stock HV subcircuits, rfmode default0, as default0 selects automatic equations; z1=.34um/z2=.38um. Source native full rectangular diffusion perimeter agrees with these equations. These are geometric/default-parameter comparisons, not new electrical simulation or extracted PSP parameter acceptance.',
            'not_run':['effect on simulated OTA performance','corrected routed physical buffer','independent gate/drain/source net ownership','body/well isolation']}
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(paired,indent=2))
if __name__=='__main__':main()
