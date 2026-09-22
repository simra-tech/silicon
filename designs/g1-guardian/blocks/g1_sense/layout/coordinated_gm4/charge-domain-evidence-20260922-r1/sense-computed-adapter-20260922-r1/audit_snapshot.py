#!/usr/bin/env python3
"""Audit computed identity/geometry/net properties without mesh, solver or package mutation."""
import argparse
import hashlib
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
from computed_layer_geometry_adapter import ExactComputedLayerBuilder
from export_sense_kpex_api import materialize,sha


def property_snapshot(region):
    if region is None:return []
    it,transform=region.begin_shapes_rec();rows=[]
    while not it.at_end():
        shape=it.shape();polygon=transform*it.trans()*shape.polygon
        rows.append((str(polygon),sorted((str(k),str(v)) for k,v in shape.properties().items())))
        it.next()
    return sorted(rows)


def empty(region):return kdb.Region() if region is None else materialize(region)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('full-lvsdb','full-gds','coupon-lvsdb','coupon-gds','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();assert not a.output.exists() and os.sched_getaffinity(0)=={6} and kdb.__version__=='0.30.9'
    expected=json.loads(Path(__file__).with_name('pex-method-evidence-20260922-r1').joinpath('computed_partition_audit.json').read_text())
    package=Path(klayout_pex.__file__).parent
    assert all(sha(package/n)==v for n,v in expected['installed_source_sha256'].items())
    a.output.mkdir(parents=True);results=[]
    (a.output/'audit_snapshot.py').write_bytes(Path(__file__).read_bytes())
    (a.output/'adapter_snapshot.py').write_bytes(Path(__file__).with_name('computed_layer_geometry_adapter.py').read_bytes())
    for name,database,gds in [('full',a.full_lvsdb,a.full_gds),('coupon',a.coupon_lvsdb,a.coupon_gds)]:
        prior=next(r for r in expected['cases'] if r['case']==name)
        assert sha(database)==prior['LVSDB_sha256'] and sha(gds)==prior['GDS_sha256']
        args=KpexCLI.parse_args(['--pdk','ihp-sg13g2','--threads','1','--2.5D','--mode','CC','--lvsdb',str(database),
                                '--out_dir',str(a.output/name)],Env.from_os_environ())
        KpexCLI.validate_args(args);tech=TechInfo.from_json(args.tech_pbjson_path,dielectric_filter=args.dielectric_filter)
        tech_sha=sha(Path(args.tech_pbjson_path));db=KpexCLI().create_lvsdb(args)
        context=KLayoutExtractionContext.prepare_extraction(db,args.effective_cell_name,tech,False)
        stock=FasterCapInputBuilder(context,tech);fixed=ExactComputedLayerBuilder(context,tech)
        source={s.lvs_layer_name:s.region for layer in context.extracted_layers.values() for s in layer.source_layers}
        original={n:property_snapshot(r) for n,r in source.items()};layer_rows=[]
        for layer in tech.gds_pair_for_computed_layer_name:
            got=fixed.shapes_of_layer(layer);want=source.get(layer)
            assert property_snapshot(got)==property_snapshot(want),layer
            layer_rows.append(dict(name=layer,geometry_and_property_identity='passed',area_um2=empty(got).area()*1e-6))
        canonical=[]
        for layer in tech.gds_pair_for_layer_name:
            if layer in tech.gds_pair_for_computed_layer_name:continue
            assert property_snapshot(fixed.shapes_of_layer(layer))==property_snapshot(stock.shapes_of_layer(layer)),layer
            canonical.append(layer)
        membership=[]
        for layer in ('metal5_cap','metal5_n_cap'):
            region=source[layer];names=sorted({dict(props)['net'] for _,props in property_snapshot(region)})
            union=kdb.Region()
            for net in names:
                queried=fixed.shapes_of_net(layer,net);snapshot=property_snapshot(queried)
                wanted=[r for r in property_snapshot(region) if dict(r[1])['net']==net]
                assert snapshot==wanted,(layer,net)
                flat=empty(queried);assert (union&flat).is_empty();union+=flat
                membership.append(dict(layer=layer,net=net,area_um2=flat.area()*1e-6,property_geometry_identity='passed'))
            assert (empty(region)^union).is_empty()
        cap=empty(fixed.shapes_of_layer('metal5_cap'));noncap=empty(fixed.shapes_of_layer('metal5_n_cap'))
        ly=kdb.Layout();ly.read(str(gds));top=ly.top_cell()
        native=materialize(kdb.Region(top.begin_shapes_rec(ly.layer(67,0))))
        mim=materialize(kdb.Region(top.begin_shapes_rec(ly.layer(36,0))))
        assert (cap&noncap).is_empty() and ((cap+noncap)^native).is_empty() and (cap^(native&mim)).is_empty()
        assert {n:property_snapshot(r) for n,r in source.items()}==original
        assert sha(Path(args.tech_pbjson_path))==tech_sha and sha(database)==prior['LVSDB_sha256'] and sha(gds)==prior['GDS_sha256']
        results.append(dict(case=name,bindings=prior,tech_sha256=tech_sha,computed_layer_controls=layer_rows,
                            canonical_fallback_controls=canonical,computed_M5_net_membership=membership,
                            corrected_M5cap_area_um2=cap.area()*1e-6,corrected_M5noncap_area_um2=noncap.area()*1e-6,
                            overlap_and_native_XOR_um2=0.,source_context_unchanged=True))
    assert all(sha(package/n)==v for n,v in expected['installed_source_sha256'].items())
    result=dict(status='passed isolated computed geometry adapter; field extraction and composition not qualified',cases=results,
                script_sha256=sha(Path(__file__)),adapter_sha256=sha(Path(__file__).with_name('computed_layer_geometry_adapter.py')),
                original_installed_source_sha256=expected['installed_source_sha256'],no_meshing_or_solver=True,
                installed_tool_deck_card_tech_GDS_unchanged=True,intrinsic_extrinsic_decomposition='not implemented',
                later_r8_power_geometry='not evaluated by these saved r5/coupon controls')
    (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
