#!/usr/bin/env python3
"""Export the actual retained TRIP subtree with an exact three-way source binding."""
import argparse
import json
import os
from pathlib import Path
import pya
from build_ls_interface import region,text_records,sha


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in('parent','diagnosis','reference','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0))==1 and pya.__version__=='0.30.9'
    parent_hash='9940011f4061ec17815ff65f86c2448ad07145cf6a1d87645f4ab80bbb815669'
    canonical='c99f3ae11b4501610939aa09b4581535a42d257f76951a25b4c84dd72a3afb90'
    baseline='38c1d6d13bbfee4ed0e3c01477742c3d2d28317d9215d9e5bd9a35551285ae59'
    assert sha(a.parent)==parent_hash
    assert sha(a.reference)=='60a9ad6e3744ff0b3dcd407a78febcb49315840a65fdf8ef851032d6e88bfd76'
    diagnosis=json.loads(a.diagnosis.read_text())
    sources={r['name']:r['GDS_sha256']for r in diagnosis['sources']}
    assert sources==dict(parent=parent_hash,standalone=canonical,baseline=baseline)
    pairs={(r['left'],r['right']):r for r in diagnosis['pairs']}
    held=pairs['baseline','parent'];delta=pairs['standalone','parent']
    assert held['texts_exact'] and not held['differences'] and delta['texts_exact']
    assert sorted(r['layer']for r in delta['differences'])==[[50,22],[67,22]]
    assert all(r['right_area_um2']==0 and r['added_area_um2']==0 for r in delta['differences'])
    ly=pya.Layout();ly.read(str(a.parent));original=ly.cell('retained_g1_trip')
    assert original is not None and ly.dbu==.001
    out=pya.Layout();out.dbu=ly.dbu;top=out.create_cell('g1_trip');top.copy_tree(original)
    a.output.mkdir(parents=True)
    dest=a.output/'g1_trip.gds';out.write(str(dest))
    saved=pya.Layout();saved.read(str(dest));st=saved.cell('g1_trip')
    infos={(i.layer,i.datatype)for i in ly.layer_infos()}|{(i.layer,i.datatype)for i in saved.layer_infos()}
    for key in infos:
        info=pya.LayerInfo(*key)
        assert(region(ly,original,info)^region(saved,st,info)).is_empty(),str(info)
    assert text_records(ly,original)==text_records(saved,st)
    (a.output/'g1_trip_lvs.cdl').write_bytes(a.reference.read_bytes())
    (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    result=dict(status='passed actual parent-native source view',GDS_sha256=sha(dest),
        actual_parent_GDS_sha256=parent_hash,canonical_functional_source_GDS_sha256=canonical,
        baseline_source_GDS_sha256=baseline,source_reference_sha256=sha(a.reference),
        diagnosis_sha256=sha(a.diagnosis),script_sha256=sha(Path(__file__)),
        exact_parent_roundtrip_all_layers_and_text=True,canonical_non22_and_lower_fill_exact=True,
        canonical_difference_layers=[[50,22],[67,22]],
        not_run=['actual-source remedy build/stock/LVS','pruning or integration','density/refill/PEX','adoption'])
    (a.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
