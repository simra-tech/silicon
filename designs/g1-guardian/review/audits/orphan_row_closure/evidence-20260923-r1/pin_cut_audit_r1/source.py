#!/usr/bin/env python3
"""All 53 source-selected row pins plus ten physical one-cut-open controls."""
import argparse
import json
import os
from pathlib import Path
import sys
import time
import traceback
import pya

HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent))
from flat_metal_connectivity import flat_physical
from audit_placed_decap_domains import identity,physical
from place_closed_analog import region,sha


def main():
    p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True)
    p.add_argument('--observations',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists();a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    result=dict(status='running');start=time.monotonic()
    try:
        assert len(os.sched_getaffinity(0))==1 and pya.__version__=='0.30.9'
        meta=json.loads((a.candidate/'analysis.json').read_text());gds=a.candidate/'power_connected_native.gds'
        assert meta['status'].startswith('passed') and sha(gds)==meta['GDS_sha256']=='4acb5b3b91881423d72d3c071a7790d1e05edfa164e20b92e6441b0135fb0192'
        assert sha(a.observations)=='5b07203bfb5c81274312f566ee73b6da9e5d3c3dd317ef4de3c83035a222e722'
        rows=[r for r in json.loads(a.observations.read_text())['observations'] if r['net']=='VDD' and r['clusters']==[['instance_resolved_metal_graph',23471]]]
        assert len(rows)==53 and sum(r['instance']=='i_core.u_digital_1'for r in rows)==1
        ly=pya.Layout();ly.read(str(gds));top=ly.top_cell()
        net,ml,held=flat_physical(ly,top)
        root=identity(net,ml[134],[395000,354660]);vss=identity(net,ml[134],[507000,334660])
        assert root is not None and vss is not None and root!=vss
        probes=[]
        for row in rows:
            for window in row['windows']:
                layer=window['layer'];box=pya.Box(*window['bbox'])
                actual=pya.Region(top.begin_shapes_rec_overlapping(ly.layer(layer,0),box))&pya.Region(box)
                assert abs(actual.area()*1e-6-window['native_area_um2'])<1e-10
                for poly in actual.each():
                    point=next(poly.each_point_hull());found=identity(net,ml[layer],[point.x,point.y])
                    assert found==root,(row['instance'],found,root)
                    probes.append(dict(instance=row['instance'],pin=row['pin'],layer=layer,window=window['bbox'],point=[point.x,point.y],root_match=True))
        numbers=(8,10,30,50,67,126,134,19,29,49,66,125,133)
        roi=pya.Box(1058000,892000,1066000,898000)
        raw={n:(pya.Region(top.begin_shapes_rec_overlapping(ly.layer(n,0),roi))&pya.Region(roi)).merged()for n in numbers}
        cases=[]
        for array in meta['arrays']:
            cut=array['cut_layer']
            for box in array['cut_boxes']:
                flat=pya.Layout();flat.dbu=.001;cell=flat.create_cell('one_cut_open_actual_native_ROI')
                removal=pya.Region(pya.Box(*box));assert (removal-raw[cut]).is_empty()
                for n,shapes in raw.items():cell.shapes(flat.layer(n,0)).insert(shapes-removal if n==cut else shapes)
                graph,layers=physical(flat,cell)
                a1=identity(graph,layers[8],[1061920,894780]);a2=identity(graph,layers[126],[1061920,894780])
                assert a1==a2 and a1 is not None
                cases.append(dict(cut_layer=cut,removed_box=box,row_to_root_M1_TM1_connected=True))
        assert len(cases)==10
        result.update(status='passed all 53 source-row pins and ten local cut-open controls',
            GDS_sha256=sha(gds),candidate_metadata_sha256=sha(a.candidate/'analysis.json'),source_observation_sha256=sha(a.observations),
            source_observation_scope='R6 historical selection by its cluster key only; every actual window is freshly probed in the current candidate graph, not numeric-ID equality across runs.',
            terminals=len(rows),window_probes=probes,cut_open_cases=cases,script_sha256=sha(Path(__file__)),elapsed_seconds=time.monotonic()-start,
            nominal_half_table_lower_cut_capacity_mA=.4,one_cut_removed_lower_cut_capacity_mA=.2,
            scope='Ideal-metal connectivity and cut arithmetic only. Local 8x6 um clipped graph provides positive surviving-path witnesses; global unchanged native path was separately proved.',
            not_run=['actual current envelope','native-wire IR/EM/hot lifetime','stock DRC in this audit','final signal-routed context'])
    except BaseException as exc:
        result.update(status='failed',error=repr(exc),traceback=traceback.format_exc());raise
    finally:
        (a.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({k:v for k,v in result.items()if k!='window_probes'},indent=2))


if __name__=='__main__':main()
