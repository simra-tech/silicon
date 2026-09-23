#!/usr/bin/env python3
"""Full raw-matrix comparison, not delta insertion or completeness acceptance."""
import argparse,hashlib,json,math
from pathlib import Path

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def matrix(rows):
    nodes=sorted({r[k] for r in rows for k in ['net1','net2']});index={n:i for i,n in enumerate(nodes)}
    values=[[0. for _ in nodes] for _ in nodes];edges={}
    for row in rows:
        value=row['capacitance_fF'];assert float.fromhex(row['capacitance_fF_hex'])==value and math.isfinite(value) and value>=0
        a,b=row['net1'],row['net2'];assert a!=b
        key=tuple(sorted([a,b]));assert key not in edges;edges[key]=value
        i,j=index[a],index[b];values[i][j]=values[j][i]=-value*1e-15
    for i in range(len(nodes)):values[i][i]=-math.fsum(values[i])
    residual=max(abs(math.fsum(row)) for row in values)
    assert math.isfinite(residual) and residual<=1e-25
    assert all(values[i][j]==values[j][i] for i in range(len(nodes)) for j in range(len(nodes)))
    return dict(nodes=nodes,matrix_F=values,maximum_row_residual_F=residual,
        symmetry_exact=True,positive_semidefinite_basis='Positive-edge incidence Laplacian: energy=sum(Cij*(Vi-Vj)^2)/2>=0'),edges

def tests():
    row=lambda a,b,c:dict(net1=a,net2=b,capacitance_fF=c,capacitance_fF_hex=float(c).hex())
    m,_=matrix([row('a','b',6.),row('b','c',3.5)])
    assert m['matrix_F'][1][1]==math.fsum([6.*1e-15,3.5*1e-15]) and m['matrix_F'][0][1]==-6.*1e-15
    for bad in [[row('a','a',1.)],[row('a','b',-1.)],[row('a','b',1.),row('b','a',1.)]]:
        try:matrix(bad)
        except AssertionError:continue
        raise AssertionError('invalid capacitance graph accepted')
    return 'passed6/3.5fF dimensions, negative/self/duplicate rejection'

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ['before','after','output']:p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();assert not a.output.exists();controls=tests();a.output.mkdir(parents=True)
    views={};edges={}
    for label,folder in [('before',a.before),('after',a.after)]:
        summary=json.loads((folder/'summary.json').read_text())
        assert summary['status']=='passed raw native CC only; completefield FAILED'
        assert summary['exact_source_node_mapping']=='passed' and summary['inputs_tools_cards_unchanged']
        source=folder/'exact_capacitances.json';assert sha(source)==summary['capacitor_sha256']
        rows=json.loads(source.read_text());view,edge=matrix(rows)
        expected=set(summary['expected_source_labels']);assert len(expected)==134
        assert set(view['nodes'])<=expected|{'VSUBS'}
        view.update(capacitance_sha256=sha(source),summary_sha256=sha(folder/'summary.json'),
            source_net_pairs=sum('VSUBS' not in key for key in edge),
            substrate_pairs=sum('VSUBS' in key for key in edge),
            substrate='unbound; excluded pairs are NOT zero or a physical error bound')
        views[label]=view;edges[label]=edge
    assert views['before']['nodes']==views['after']['nodes']
    comparisons=[]
    for key in sorted(set(edges['before'])|set(edges['after'])):
        old=edges['before'].get(key,0.);new=edges['after'].get(key,0.)
        comparisons.append(dict(nodes=list(key),before_fF=old,after_fF=new,delta_fF=new-old))
    comparisons.sort(key=lambda q:abs(q['delta_fF']),reverse=True)
    result=dict(status='passed full raw-matrix mathematical/source comparison; completefield FAILED',
        controls=controls,views=views,all_pair_comparison=comparisons,
        acceptance='No1percent before/after-design acceptance invented. Full partial matrices retained; no delta insertion.',
        excluded_physics=['blackboxed native MIM extrinsic fields','tap-contact fields','unqualified VSUBS reference','wire R and model attachment planes','fullchip/fill context'],
        electrical='not run',full_fast_PM_acceptance='not qualified')
    (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    (a.output/'summary.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(status=result['status'],nodes=len(views['after']['nodes']),largest_change=comparisons[0],
        residuals_F={k:v['maximum_row_residual_F'] for k,v in views.items()}),indent=2))

if __name__=='__main__':main()
