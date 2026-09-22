#!/usr/bin/env python3
"""Build isolated source-held SENSE power overlay; no canonical adoption."""
import argparse
import json
import os
from pathlib import Path
import sys
import pya

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from place_closed_analog import region, text_records, sha
from audit_placed_decap_domains import physical, identity

METALS=(8,10,30,50,67,126,134)
CUTS={19:(8,10),29:(10,30),49:(30,50),66:(50,67),125:(67,126),133:(126,134)}


def box(x1,y1,x2,y2):
    return pya.Region(pya.DBox(x1,y1,x2,y2).to_itype(.001))


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--native',type=Path,required=True)
    ap.add_argument('--spines',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args()
    assert not a.output.exists() and pya.__version__=='0.30.9' and len(os.sched_getaffinity(0))==1
    source=a.native/'fullchip_instances_unrouted.gds'
    assert sha(source)=='8b66a958759478987fa9de59746a0554f9bd065307e730342f10e891082134e6'
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    result=dict(status='running',source_GDS_sha256=sha(source),script_sha256=sha(Path(__file__)),
                source_primitives_and_macro_ports='held',canonical_adoption='not run')
    try:
        layout=pya.Layout();layout.read(str(source));top=layout.top_cell();assert layout.dbu==.001
        original={str(info):region(layout,top,info) for info in layout.layer_infos()}
        texts=text_records(layout,top)
        native={l:region(layout,top,pya.LayerInfo(l,0)) for l in METALS+tuple(CUTS)}
        routes={n:{l:pya.Region() for l in METALS+tuple(CUTS)} for n in ('VDDA','VSS')}
        def put(net,layer,r):routes[net][layer]+=r
        def wire(net,layer,points,width):
            for (x1,y1),(x2,y2) in zip(points,points[1:]):
                assert x1==x2 or y1==y2
                put(net,layer,box(min(x1,x2)-width/2,min(y1,y2)-width/2,
                                  max(x1,x2)+width/2,max(y1,y2)+width/2))
        arrays=[]
        def array(net,layer,x,y,nx,ny):
            lower,upper=CUTS[layer]
            cut,pitch,enc,limit=(.19,.5,.055,.4) if layer<100 else ((.42,.84,.12,1.4) if layer==125 else (.9,1.96,.65,10.))
            sx=(nx-1)*pitch+cut;sy=(ny-1)*pitch+cut
            for i in range(nx):
                for j in range(ny):
                    cx=x+(i-(nx-1)/2)*pitch;cy=y+(j-(ny-1)/2)*pitch
                    put(net,layer,box(cx-cut/2,cy-cut/2,cx+cut/2,cy+cut/2))
            landing=[]
            for metal in (lower,upper):
                extra=.45 if layer==125 and metal==126 else enc
                minimum=1.64 if metal==126 else 2. if metal==134 else .2
                wx=max(sx+2*extra,minimum);wy=max(sy+2*extra,minimum)
                bounds=[x-wx/2,y-wy/2,x+wx/2,y+wy/2]
                put(net,metal,box(*bounds));landing.append(dict(layer=metal,bbox_um=bounds))
            arrays.append(dict(net=net,layer=layer,center_um=[x,y],nx=nx,ny=ny,cuts=nx*ny,
                               landings=landing,limit_mA_per_cut=limit,
                               half_limit_equal_sharing_mA=.5*nx*ny*limit,
                               one_cut_unavailable_half_limit_mA=.5*(nx*ny-1)*limit,
                               worst_single_cut_utilization_at_2mA=2/limit))
        wire('VDDA',134,[(813,714),(813,726),(1048,726),(1048,395)],2.2)
        wire('VDDA',30,[(1048,395),(1093.145,395)],2.2)
        array('VDDA',49,1048,395,4,3)
        array('VDDA',66,1048,395,4,3)
        array('VDDA',125,1048,395,2,2)
        array('VDDA',133,1048,395,2,1)
        wire('VSS',126,[(805,714),(803.8,714),(803.8,722)],2.2)
        array('VSS',133,803.8,722,2,2)
        wire('VSS',134,[(803.8,722),(736.8,722)],2.2)
        array('VSS',133,736.8,722,2,2)
        allowed={n:{l:pya.Region() for l in METALS} for n in routes}
        for net,layer,window in [('VDDA',134,[811,712,815,716]),('VDDA',30,[1093,381.105,1093.290,405.875]),
                                 ('VSS',126,[803,712,807,716])]:
            assert (box(*window)-native[layer]).is_empty()
            allowed[net][layer]+=native[layer].interacting(box(*window))
        checks=[];failures=[]
        for net,layers in routes.items():
            other='VSS' if net=='VDDA' else 'VDDA'
            for layer in METALS:
                clearance=.4 if layer<100 else 2 if layer==126 else 5
                forbidden=native[layer]-allowed[net][layer]
                overlap=layers[layer]&forbidden
                nearby=layers[layer]&forbidden.sized(round(clearance*1000))
                inter=layers[layer]&routes[other][layer].sized(round(clearance*1000))
                row=dict(net=net,layer=layer,overlap_um2=overlap.area()*1e-6,
                         conservative_proximity_um2=nearby.area()*1e-6,other_route_proximity_um2=inter.area()*1e-6)
                checks.append(row)
                if not overlap.is_empty() or not nearby.is_empty() or not inter.is_empty():failures.append(row)
            for layer,(lo,hi) in CUTS.items():
                cuts=layers[layer]
                assert (cuts-(layers[lo]+allowed[net][lo])).is_empty()
                assert (cuts-(layers[hi]+allowed[net][hi])).is_empty()
                gap=.29 if layer<100 else .42 if layer==125 else 1.06
                assert (cuts&native[layer].sized(round(gap*1000))).is_empty(),(net,layer,'old cut proximity')
        result.update(arrays=arrays,native_clearance_checks=checks,clearance_failures=failures)
        assert not failures, failures
        # No root spine is modified or copied into the implementation overlay.
        spines=json.loads((a.spines/'analysis.json').read_text())['spines']
        spines += [dict(net='VDD',lane='reserved_r5_750',bbox=[747000,321000,753000,1093000]),
                   dict(net='VSS',lane='reserved_r5_774',bbox=[771000,321000,777000,1093000])]
        for row in spines:
            r=pya.Region(pya.Box(*row['bbox']))
            for net in routes:
                if net=='VSS' and row['net']=='VSS':continue
                assert (routes[net][126]&r.sized(2000)).is_empty(),(net,'root spine',row['lane'])
        overlay=pya.Layout();overlay.dbu=.001;oc=overlay.create_cell('sense_power_interface_NOT_ADOPTED')
        for net,layers in routes.items():
            for layer,r in layers.items():
                for polygon in r.merged().each():
                    top.shapes(layout.layer(layer,0)).insert(polygon)
                    oc.shapes(overlay.layer(layer,0)).insert(polygon)
        output=a.output/'candidate_unrouted.gds';layout.write(str(output))
        overlay.write(str(a.output/'power_overlay.gds'))
        saved=pya.Layout();saved.read(str(output));st=saved.top_cell()
        assert text_records(saved,st)==texts
        for info in saved.layer_infos():
            expected=original.get(str(info),pya.Region())
            if info.datatype==0 and info.layer in routes['VDDA']:
                expected=expected+routes['VDDA'][info.layer]+routes['VSS'][info.layer]
            assert (region(saved,st,info)^expected).is_empty(),str(info)
        network,metals=physical(saved,st)
        points={'sense_vdda':(134,[813000,714000]),'pad07_bare':(30,[1093145,395000]),
                'pad07_external':(134,[1271500,395000]),'sense_vss':(126,[805000,714000]),
                'vss_handoff':(126,[736800,722000]),'core_vdd':(134,[395000,354660]),
                'core_vss':(134,[507000,334660])}
        probes={n:identity(network,metals[l],xy) for n,(l,xy) in points.items()}
        assert all(v is not None for v in probes.values())
        assert probes['sense_vdda']==probes['pad07_bare']==probes['pad07_external']
        assert probes['sense_vss']==probes['vss_handoff']
        assert len({probes[n] for n in ('sense_vdda','sense_vss','core_vdd','core_vss')})==4
        result.update(status='passed isolated overlay geometry and scoped physical binding; stock not run',
                      GDS_sha256=sha(output),overlay_sha256=sha(a.output/'power_overlay.gds'),
                      probes=probes,unchanged_source_geometry_and_texts='passed',
                      root_spine_handoff=dict(net='VSS',layer=126,center_um=[736.8,722],
                          footprint_um=[734.72,719.92,738.88,724.08],spine_implementation='root owned; not included'),
                      exploratory_current_mA=2,metal_bridge_half_limit_mA=2.2,
                      current_scope='105C/11year table, 50% engineering target; aggregate/equal-sharing and one-cut-unavailable diagnostics, not actual current-sharing or hot lifetime qualification',
                      not_run=['stock DRC','routed signal overlay and all other macro interfaces',
                               'actual root VSS spine connection','native pad07 internal current capacity',
                               'field parasitics/IR/EM/full corner current envelope','electrical adoption'])
    except Exception as exc:
        result.update(status='failed isolated overlay gate',error=repr(exc))
        raise
    finally:
        (a.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':main()
