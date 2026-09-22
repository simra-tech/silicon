#!/usr/bin/env python3
"""Read-only computed-layer partition and stock builder-query audit; no meshing."""
import argparse
import json
import os
from pathlib import Path

import klayout.db as kdb
import klayout_pex
from klayout_pex.env import Env
from klayout_pex.kpex_cli import KpexCLI
from klayout_pex.klayout.lvsdb_extractor import KLayoutExtractionContext
from klayout_pex.fastercap.fastercap_input_builder import FasterCapInputBuilder
from klayout_pex.tech_info import TechInfo
from export_sense_kpex_api import materialize, sha


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('full-lvsdb','full-gds','coupon-lvsdb','coupon-gds','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();assert os.sched_getaffinity(0)=={6} and kdb.__version__=='0.30.9'
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/'script_snapshot.py').write_bytes(Path(__file__).read_bytes())
    results=[]
    for name,database,gds,cap_area in [('full',args.full_lvsdb,args.full_gds,2645.),('coupon',args.coupon_lvsdb,args.coupon_gds,49.)]:
        binds={path:sha(path)for path in(database,gds)}
        cli_args=KpexCLI.parse_args(['--pdk','ihp-sg13g2','--threads','1','--2.5D','--mode','CC','--lvsdb',str(database),
                                    '--out_dir',str(args.output/name)],Env.from_os_environ())
        KpexCLI.validate_args(cli_args);cli=KpexCLI();tech=TechInfo.from_json(cli_args.tech_pbjson_path,dielectric_filter=cli_args.dielectric_filter)
        db=cli.create_lvsdb(cli_args);context=KLayoutExtractionContext.prepare_extraction(db,cli_args.effective_cell_name,tech,False)
        builder=FasterCapInputBuilder(context,tech)
        selected={layer.lvs_layer_name:layer for layer in context.extracted_layers[(67,0)].source_layers}
        assert set(selected)=={'metal5_cap','metal5_n_cap'}
        cap=materialize(selected['metal5_cap'].region);noncap=materialize(selected['metal5_n_cap'].region)
        ly=kdb.Layout();ly.read(str(gds));native=materialize(kdb.Region(ly.top_cell().begin_shapes_rec(ly.layer(67,0))))
        mim=materialize(kdb.Region(ly.top_cell().begin_shapes_rec(ly.layer(36,0))))
        assert materialize(cap&noncap).is_empty() and materialize((cap+noncap)^native).is_empty()
        assert materialize(cap^(native&mim)).is_empty() and abs(cap.area()*1e-6-cap_area)<1e-8
        queries={key:materialize(builder.shapes_of_layer(key)) for key in ('metal5_cap','metal5_n_cap')}
        assert all(materialize(region^native).is_empty()for region in queries.values())
        unnamed=[]
        for net in db.netlist().circuit_by_name(cli_args.effective_cell_name).each_net():
            if net.name or not net.expanded_name().startswith('$'):continue
            by_object=builder.shapes_of_net('TopMetal1',net)
            by_expanded=context.shapes_of_net((126,0),net.expanded_name())
            unnamed.append(dict(expanded_name=net.expanded_name(),literal_name=net.name,
                                stock_object_query_area_um2=0. if by_object is None else materialize(by_object).area()*1e-6,
                                expanded_string_query_area_um2=0. if by_expanded is None else materialize(by_expanded).area()*1e-6))
        assert all(sha(path)==value for path,value in binds.items())
        results.append(dict(case=name,LVSDB_sha256=sha(database),GDS_sha256=sha(gds),
                            native_M5_um2=native.area()*1e-6,computed_M5cap_um2=cap.area()*1e-6,
                            computed_M5noncap_um2=noncap.area()*1e-6,partition_overlap_um2=0.,partition_native_XOR_um2=0.,
                            native_MIM_intersection_XOR_um2=0.,
                            stock_builder_query_um2={key:region.area()*1e-6 for key,region in queries.items()},
                            unnamed_net_queries=unnamed))
    package=Path(klayout_pex.__file__).parent
    sources=['klayout/lvsdb_extractor.py','fastercap/fastercap_input_builder.py','fastercap/fastercap_model_generator.py',
             'fastercap/fastercap_runner.py','klayout/netlist_expander.py','tech_info.py']
    result=dict(status='passed independent partition diagnostic; stock computed-name query aliases demonstrated',
                script_sha256=sha(Path(__file__)),cases=results,installed_source_sha256={name:sha(package/name)for name in sources},
                no_geometry_mutation=True,no_meshing_or_solver=True,no_tool_deck_model_changes=True,
                repair_feasibility='Existing KLayoutExtractedLayerInfo.source_layers retains exact computed names and net properties. A future generic adapter could select exact computed identity before any canonical GDS-pair fallback; not implemented here.',
                intrinsic_extrinsic_decomposition='not provided by this geometry partition audit',full_macro_3D='not run')
    (args.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
