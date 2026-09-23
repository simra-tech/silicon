#!/usr/bin/env python3
"""Conditional nine-rail/60-cut pad-head ladder; not a full-pad EM model."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def solve(xs,rails,vias,width,center,rsh,rvia,removed=None,target=.010):
    count=len(xs);index={x:i for i,x in enumerate(xs)};edges=[]
    for offset,w,label,limit in[(0,1.,'M2_header',.001),(count,width,'M3_collector',.0003 if width<=.3 else width*.001)]:
        for i,(left,right)in enumerate(zip(xs,xs[1:])):
            edges.append((offset+i,offset+i+1,rsh*(right-left)/w,label,limit))
    for k,x in enumerate(vias):
        if k!=removed:edges.append((index[x],count+index[x],rvia,'Via2',.0002))
    for left,right in rails:
        x=round((left+right)/2,6);w=right-left
        edges.append((index[x],2*count,rsh*176/w,'M2_long_rail',w*.001))
    fixed={2*count:0.}
    fixed.update({count+i:1. for i,x in enumerate(xs)if abs(x-center)<=5.1+1e-9})
    unknown=[n for n in range(2*count+1)if n not in fixed];lookup={n:i for i,n in enumerate(unknown)}
    rr=[];cc=[];vv=[];rhs=np.zeros(len(unknown))
    for a,b,r,label,limit in edges:
        g=1/r
        for n,other in[(a,b),(b,a)]:
            if n not in lookup:continue
            row=lookup[n];rr.append(row);cc.append(row);vv.append(g)
            if other in lookup:rr.append(row);cc.append(lookup[other]);vv.append(-g)
            else:rhs[row]+=g*fixed[other]
    result=spsolve(coo_matrix((vv,(rr,cc)),shape=(len(unknown),len(unknown))).tocsr(),rhs)
    voltage={**fixed,**{n:float(result[i])for n,i in lookup.items()}}
    assert all(math.isfinite(v)for v in voltage.values())
    injected=sum((voltage[a]-voltage[b])/r if a in fixed and fixed[a]==1 else
                 (voltage[b]-voltage[a])/r if b in fixed and fixed[b]==1 else 0
                 for a,b,r,label,limit in edges if not(a in fixed and b in fixed))
    assert injected>0;scale=target/injected
    kcl={n:0. for n in range(2*count+1)};records=[]
    for a,b,r,label,limit in edges:
        current=(voltage[a]-voltage[b])/r*scale;kcl[a]+=current;kcl[b]-=current
        records.append(dict(kind=label,a=a,b=b,R_ohm=r,current_A=current,half_table_A=limit,utilization=abs(current)/limit))
    residual=max(abs(kcl[n])for n in unknown)
    assert residual<1e-12 and abs(kcl[2*count]+target)<1e-12
    worst=max(records,key=lambda row:row['utilization'])
    return dict(status='passed conditional head target'if worst['utilization']<=1+1e-10 else'failed conditional head target',
                removed_Via2=removed,required_source_V=scale,KCL_residual_A=residual,worst=worst,
                rail_currents_A=[r['current_A']for r in records if r['kind']=='M2_long_rail'],
                maximum_by_kind={kind:max(abs(r['current_A'])for r in records if r['kind']==kind)
                                 for kind in('M2_header','M3_collector','Via2','M2_long_rail')})


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--inventory',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--collector-widths',type=float,nargs='+',default=[.29,6.])
    p.add_argument('--feed-centers',type=float,nargs='+',default=[387.3,393.49])
    a=p.parse_args();assert not a.output.exists()and len(os.sched_getaffinity(0))==1
    inv=json.loads(a.inventory.read_text())
    assert inv['GDS_sha256']=='8b66a958759478987fa9de59746a0554f9bd065307e730342f10e891082134e6'
    m2=[r for r in inv['polygons']if r['layer']==10];assert len(m2)==1
    holes=sorted((min(p[0]for p in h),max(p[0]for p in h),min(p[1]for p in h),max(p[1]for p in h))for h in m2[0]['holes_um'])
    assert len(holes)==8 and all(abs(y1-3)<1e-9 and abs(y2-179)<1e-9 for x1,x2,y1,y2 in holes)
    rails=[];left=26.105
    for x1,x2,y1,y2 in holes:rails.append((left,x1));left=x2
    rails.append((left,50.875))
    assert len(rails)==9 and abs(sum(b-a for a,b in rails)-13.57)<1e-9
    vias=sorted(round(r['center_um'][0],6)for r in inv['vias']if r['layer']==29 and abs(r['center_um'][1]-179.855)<1e-9)
    assert len(vias)==60 and len(set(vias))==60
    cases=[]
    assert all(w>=.29 for w in a.collector_widths)
    for width in a.collector_widths:
        for chip_center in a.feed_centers:
            center=chip_center-355
            xs=sorted(set(vias+[round((a+b)/2,6)for a,b in rails]+[26.105,50.875,round(center-5.1,6),round(center+5.1,6)]))
            assert min(xs)>=26.105 and max(xs)<=50.875
            for rsh,rvia,label in[(.073,5.,'tabulated_min'),(.088,9.,'tabulated_target'),(.103,20.,'tabulated_max_LEF')]:
                baseline=solve(xs,rails,vias,width,center,rsh,rvia)
                losses=[solve(xs,rails,vias,width,center,rsh,rvia,k)for k in range(60)]
                cases.append(dict(collector_width_um=width,chip_feed_center_y_um=chip_center,
                    resistance_scenario=label,sheet_ohm_per_square=rsh,Via2_ohm=rvia,baseline=baseline,
                    one_cut_failures=sum(r['status'].startswith('failed')for r in losses),one_cut_results=losses))
    # Linearity is a method control, not a current-model acceptance waiver.
    full=solve(xs,rails,vias,width,center,.103,20.,target=.010)
    half=solve(xs,rails,vias,width,center,.103,20.,target=.005)
    assert abs(full['required_source_V']-2*half['required_source_V'])<1e-14
    result=dict(status='completed conditional native pad-head ladder; full-pad current qualification not run',
        inventory_sha256=sha(a.inventory),script_sha256=sha(Path(__file__)),rails_um=rails,Via2_x_um=vias,
        target_A=.010,cases=cases,linearity_control='passed',
        assumptions=['One-dimensional ohmic M2 header width1um, nine exact176um rails, 60individual Via2 and M3 collector.',
                     'Finite lateral header/collector resistances determine unequal rail/cut currents; no equal rail-current assumption.',
                     '10.2um feed window is an ideal voltage boundary; lower ends of all nine rails share an ideal reference.',
                     'Three paired tabulated resistance scenarios are diagnostic, not all independent extrema or temperature corners.',
                     '50% engineering target against105C/11year current table, not foundry derating.'],
        not_run=['actual2D spreading/crowding','native lower-stack/collector distribution','feed-window voltage gradient',
                 'full-chip load partition/IR/EM/PVT','collector geometry clearance/stock','adoption'])
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    (a.output/'analysis.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({**{k:v for k,v in result.items()if k not in('cases','Via2_x_um')},
        'cases':[{k:v for k,v in row.items()if k!='one_cut_results'}for row in cases]},indent=2))


if __name__=='__main__':main()
