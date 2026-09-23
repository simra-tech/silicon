#!/usr/bin/env python3
"""Translate a stock/LVS-qualified additive TRIP overlay, keeping native source held."""
import argparse
import json
import os
from pathlib import Path
import pya
from build_ls_interface import region, sha, METALS, CUTS
from prune_trip_fill import describe,prune_from_ledger


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in('candidate','drc','lvs','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--native-source',type=Path)
    a=p.parse_args();assert not a.output.exists()and len(os.sched_getaffinity(0))==1 and pya.__version__=='0.30.9'
    meta=json.loads((a.candidate/'analysis.json').read_text())
    assert meta['status'].startswith('passed')
    gds=a.candidate/'g1_trip.gds';local=a.candidate/'internal_overlay_local.gds'
    assert sha(gds)==meta['GDS_sha256']and sha(local)==meta['overlay_sha256']
    drc=json.loads((a.drc/'summary.json').read_text());lvs=json.loads((a.lvs/'summary.json').read_text())
    assert drc['status']=='passed scoped main and maximal DRC'and lvs['status']=='passed strict source LVS'
    assert drc['GDS_sha256']==lvs['GDS_sha256']==sha(gds)
    assert lvs['reference_sha256']==meta['source_reference_sha256']
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    source=pya.Layout();source.read(str(local));top=source.top_cell();assert source.dbu==.001
    assert not list(top.each_inst())
    ly=pya.Layout();ly.dbu=.001;out=ly.create_cell('trip_internal_access_global_NOT_ADOPTED')
    transform=pya.Trans(771000,736000);counts={}
    for info in source.layer_infos():
        assert info.datatype==0 and info.layer in METALS+tuple(CUTS)
        assert not any(shape.is_text()for shape in top.shapes(source.layer(info)).each())
        r=region(source,top,info)
        for poly in r.each():out.shapes(ly.layer(info)).insert(poly.transformed(transform))
        counts[str(info)]=dict(polygons=r.count(),area_dbu2=r.area())
    dest=a.output/'power_overlay.gds';ly.write(str(dest))
    saved=pya.Layout();saved.read(str(dest))
    for info in source.layer_infos():
        assert(region(source,top,info)^region(saved,saved.top_cell(),info).transformed(transform.inverted())).is_empty()
    probes=[]
    for row in meta['source_access']:
        point=row.get('M1_source_probe_um',row.get('native_M1_rail_probe_um'))
        probes.append(dict(net=row['net'],layer=8,global_dbu=[round(point[0]*1000)+771000,round(point[1]*1000)+736000],source_record=row))
    fill={}
    if 'fill_removal_sha256'in meta:
        local_fill=a.candidate/'fill_removal_local.gds';ledger_path=a.candidate/'fill_removal.json'
        assert sha(local_fill)==meta['fill_removal_sha256']and sha(ledger_path)==meta['fill_removal_ledger_sha256']
        fl=pya.Layout();fl.read(str(local_fill));glob=pya.Layout();glob.dbu=.001
        gc=glob.create_cell('trip_fill_removal_global_NOT_ADOPTED')
        for info in fl.layer_infos():
            assert info.datatype==22 and info.layer in(10,30,50)
            for poly in region(fl,fl.top_cell(),info).each():gc.shapes(glob.layer(info)).insert(poly.transformed(transform))
        fill_path=a.output/'fill_removal_global.gds';glob.write(str(fill_path))
        saved_fill=pya.Layout();saved_fill.read(str(fill_path))
        for info in fl.layer_infos():
            assert(region(fl,fl.top_cell(),info)^region(saved_fill,saved_fill.top_cell(),info).transformed(transform.inverted())).is_empty()
        ledger=json.loads(ledger_path.read_text())
        original_path=a.native_source or Path(__file__).resolve().parent.parents[2]/'blocks/g1_trip/layout/g1_trip.gds'
        assert sha(original_path)==ledger['source_GDS_sha256']
        original=pya.Layout();original.read(str(original_path));original_top=original.cell('g1_trip')
        for row in ledger['rows']:
            instances=[inst for inst in original_top.each_inst()if inst.cell.name==row['child_cell']and str(inst.cell_inst)==row['original_array']]
            assert len(instances)==1
            row['array_descriptor']=describe(instances[0])
            row['global_polygon_hull_dbu']=[[x+771000,y+736000]for x,y in row['local_polygon_hull_dbu']]
            row['global_polygon_holes_dbu']=[[[x+771000,y+736000]for x,y in hole]for hole in row['local_polygon_holes_dbu']]
        ledger.update(translation_dbu=[771000,736000],local_ledger_sha256=sha(ledger_path))
        original_top.name='retained_g1_trip'
        for cell in original.each_cell():
            if '_FILL_CELL'in cell.name:cell.name='retained_'+cell.name
        prune_proof=prune_from_ledger(original,original_top,ledger,bound_source_sha256=sha(original_path))
        candidate=pya.Layout();candidate.read(str(gds));ct=candidate.cell('g1_trip')
        for layer in(10,30,50):
            assert(region(original,original_top,pya.LayerInfo(layer,22))^region(candidate,ct,pya.LayerInfo(layer,22))).is_empty()
        (a.output/'prune_helper_control.json').write_text(json.dumps(prune_proof,indent=2)+'\n')
        (a.output/'fill_removal.json').write_text(json.dumps(ledger,indent=2)+'\n')
        fill=dict(fill_removal_overlay_sha256=sha(fill_path),fill_removal_ledger_sha256=sha(a.output/'fill_removal.json'),
                  local_fill_removal_overlay_sha256=sha(local_fill),fill_removal=meta['fill_removal'],
                  prune_helper_sha256=sha(Path(__file__).with_name('prune_trip_fill.py')),
                  prune_helper_namespaced_control_sha256=sha(a.output/'prune_helper_control.json'),
                  fill_inverse_translation_XOR='passed',fill_scope='Exact selected datatype22 repetitions only; functional native geometry and instances held')
    report=dict(status='passed exact source-held overlay translation; final combined-native context not run',
                overlay_sha256=sha(dest),local_overlay_sha256=sha(local),candidate_GDS_sha256=sha(gds),
                native_source_GDS_sha256=meta['source_GDS_sha256'],reference_sha256=lvs['reference_sha256'],
                drc_summary_sha256=sha(a.drc/'summary.json'),lvs_summary_sha256=sha(a.lvs/'summary.json'),
                script_sha256=sha(Path(__file__)),translation_dbu=[771000,736000],dbu_um=.001,
                exact_inverse_translation_polygon_XOR='passed',layers=counts,new_cut_count=meta['new_cut_count'],
                native_header_probes=[dict(net=n,layer=30,global_dbu=[792000,y])for n,y in[('VDD',942000),('VDDA',938750),('VSS',737000)]],
                source_access=probes,not_run=['combined-native foreign contact and final signal context','combined density/refill and near-fill PEX',
                    'per-device source/contact current capacity','comparator/VSS access remedy','PEX/PVT/IR/EM','adoption'])
    report.update(fill)
    if 'actual_native_source_binding'in meta:report['actual_native_source_binding']=meta['actual_native_source_binding']
    (a.output/'analysis.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items()if k not in('source_access','layers')},indent=2))


if __name__=='__main__':main()
