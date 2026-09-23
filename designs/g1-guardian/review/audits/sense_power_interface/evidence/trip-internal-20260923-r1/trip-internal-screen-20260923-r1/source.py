#!/usr/bin/env python3
"""Bounded native-only DAC supply bypass screen; no primitive or GDS mutation."""
import argparse
import json
import os
from pathlib import Path
import pya
from build_ls_interface import flat_physical, region, sha, METALS, CUTS, box
from screen_supply_extensions import Routes, check


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--gds',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert not a.output.exists()and len(os.sched_getaffinity(0))==1 and pya.__version__=='0.30.9'
    assert sha(a.gds)=='c99f3ae11b4501610939aa09b4581535a42d257f76951a25b4c84dd72a3afb90'
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    result=dict(status='running',GDS_sha256=sha(a.gds),script_sha256=sha(Path(__file__)),
                coordinate_frame='original g1_trip local micrometers; chip translation(+771,+736)',
                not_run=['saved geometry','actual fullnative PDN/other feed context','stock/source LVS',
                         'comparator VDD and all VSS access remedies','per-DAC/per-device currents/contact capacity',
                         'complete PEX/PVT/IR/EM','adoption'])
    try:
        ly=pya.Layout();ly.read(str(a.gds));top=ly.cell('g1_trip');assert top is not None
        flat,net,metals=flat_physical(ly,top)
        native={l:region(ly,top,pya.LayerInfo(l,0))for l in METALS+tuple(CUTS)}
        allowed={n:{l:pya.Region()for l in METALS}for n in('VDD','VDDA','VSS')}
        for n,y in [('VDD',206),('VDDA',202.75),('VSS',1)]:
            found=net.probe_net(metals[30],pya.DPoint(21,y).to_itype(.001));assert found is not None
            for l in METALS:
                for poly in net.shapes_of_net(found,metals[l],True).each():allowed[n][l].insert(poly)
        routes=Routes();access=[]
        for dac,shift in [('soft',3.),('hard',118.)]:
            # Source geometry is derived from the held generator: DAC bank bx9.5,
            # four HV PMOS per bit, unmirrored source strip center ox+.15.
            for bit in range(8):
                x0=shift+9.5+7*bit
                for index in range(4):
                    x=x0+.5+1.5*index+.15;y=21.85
                    probe=pya.DPoint(x,y).to_itype(.001)
                    assert not (allowed['VDDA'][8]&box(x-.001,y-.001,x+.001,y+.001)).is_empty()
                    actual=net.probe_net(metals[8],probe);assert actual is not None
                    root=net.probe_net(metals[30],pya.DPoint(21,202.75).to_itype(.001))
                    assert actual.cluster_id==root.cluster_id
                    # M1 only, no new Contact/Activ/GatPoly/NWell geometry.
                    routes.layers['VDDA'][8]+=box(x-.3,18.6,x+.3,23.4)
                    routes.array('VDDA',19,x,y,1,2);routes.array('VDDA',29,x,y,1,2)
                    access.append(dict(dac=dac,bit=bit,HV_PMOS_index=index,net='VDDA',M1_source_probe_um=[x,y]))
                x=x0+3.85;y=12.8
                assert not(allowed['VDD'][8]&box(x-.001,y-.001,x+.001,y+.001)).is_empty()
                routes.array('VDD',19,x,y,2,1);routes.array('VDD',29,x,y,2,1)
                access.append(dict(dac=dac,bit=bit,net='VDD',native_M1_rail_probe_um=[x,y]))
            ax=shift+66.5;dx=shift+4.5
            routes.wire('VDDA',30,shift+10.15,21.85,ax,21.85,4.2)
            routes.array('VDDA',49,ax,21.85,8,3)
            routes.wire('VDDA',50,ax,21.85,ax,202.75,4.2)
            routes.wire('VDD',30,dx,12.8,shift+62.35,12.8,1.2)
            routes.array('VDD',49,dx,12.8,4,2)
            routes.wire('VDD',50,dx,12.8,dx,206,1.2)
        failures=check(routes,native,allowed)
        result.update(status='passed native-only source-held internal access screen'if not failures else'failed native-only internal access screen',
                      failures=failures,arrays=routes.arrays,source_access=access,
                      new_cut_count=sum(r['cuts']for r in routes.arrays),
                      exploratory_DAC_branch_targets_mA={'each_DAC_VDDA':4,'each_DAC_VDD':1},
                      current_scope='Geometry assumptions only; source-contact and per-device current allocation not qualified')
        recipe={n:{str(l):[dict(hull=[[v.x,v.y]for v in poly.each_point_hull()],
                holes=[[[v.x,v.y]for v in poly.each_point_hole(i)]for i in range(poly.holes())])
                for poly in r.merged().each()]for l,r in layers.items()}for n,layers in routes.layers.items()}
        (a.output/'recipe.json').write_text(json.dumps(recipe,indent=2)+'\n');result['recipe_sha256']=sha(a.output/'recipe.json')
    except Exception as exc:
        result.update(status='failed internal-access method',error=repr(exc));raise
    finally:
        (a.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({k:v for k,v in result.items()if k not in('arrays','source_access')},indent=2))
    raise SystemExit(0 if not failures else 1)


if __name__=='__main__':main()
